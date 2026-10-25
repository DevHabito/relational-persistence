"""Synthetic/adversarial-only tests for the frozen RP-E011-D03 diagnostic.

No original JSSPP bytes are downloaded or opened by this test module.
Fixture-only patches cannot affect the production CLI constants in Git.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from experiments import rp_e011_d03_anomaly as study
from experiments.rp_e011_jsspp_source import SourceBlocked


def row(job_id: str | int, queue: str = "short", requested: int = 1) -> str:
    standard = [
        str(job_id), "0", "0", "1", "1", "-1", "-1",
        str(requested), "3600", "-1", "1", "-1", "-1",
        "-1", "1", "-1", "-1", "-1",
    ]
    return " ".join(standard) + f' node-a {queue} "quoted qsub parameters" 0'


def fixture(*rows: str) -> bytes:
    return ("; synthetic fixture only\n\n" + "\n".join(rows) + "\n").encode()


def pin_fixture(monkeypatch, raw: bytes, eligible: int, queues: int) -> None:
    # This unit-test-only calibration does not change the frozen executable.
    monkeypatch.setattr(study, "EXPECTED_SOURCE_BYTES", len(raw))
    monkeypatch.setattr(study, "EXPECTED_SOURCE_SHA256", sha256(raw).hexdigest())
    monkeypatch.setattr(study, "EXPECTED_DATA_ROWS", len(raw.decode().splitlines()) - 2)
    monkeypatch.setattr(study, "EXPECTED_ELIGIBLE_ROWS", eligible)
    monkeypatch.setattr(study, "EXPECTED_QUEUE_COUNT", queues)


def test_frozen_provider_identity_matches_permanent_d02_archive():
    archive = Path(__file__).resolve().parents[1] / (
        "docs/results/RP-E011-D02-first-run/audit.json"
    )
    original = archive.read_bytes()
    data = json.loads(original)
    assert sha256(original).hexdigest() == study.FROZEN_D02_AUDIT_SHA256
    assert data["decision"] == study.FROZEN_D02_RESULT
    assert data["source"]["original_bytes"] == study.EXPECTED_SOURCE_BYTES
    assert data["source"]["sha256"] == study.EXPECTED_SOURCE_SHA256
    assert data["schema"]["counts"]["invalid_job_id"] == 1


def test_both_readers_localize_zero_without_copying_source_content():
    raw = fixture(row(1, "short"), row(0, "long"), row(3, "short"))
    result = study.inspect_id_rows(raw)
    assert result["data_rows"] == 3
    assert result["nonpositive_job_id_count"] == 1
    bad = result["nonpositive_job_ids"][0]
    assert bad["physical_line"] == 4
    assert bad["data_record_ordinal"] == 2
    assert bad["integer_job_id"] == 0
    assert bad["original_line_without_newline_sha256"] == sha256(
        row(0, "long").encode()
    ).hexdigest()
    assert "qsub" not in str(bad)


def test_negative_id_and_duplicate_are_both_counted():
    result = study.inspect_id_rows(fixture(row(-6), row(2), row(2)))
    assert result["nonpositive_job_ids"][0]["integer_job_id"] == -6
    assert result["duplicate_job_id_count"] == 1


def test_quoted_id_causes_diagnostic_disagreement():
    with pytest.raises(study.ParserDisagreement, match="ID token readers"):
        study.inspect_id_rows(fixture(row('"2"')))


def test_noninteger_id_rejected_without_guessing():
    with pytest.raises(study.InvalidSourceText, match="Non-integer"):
        study.inspect_id_rows(fixture(row("job-x")))


def test_unbalanced_qsub_quote_is_an_invalid_source_text():
    with pytest.raises(study.InvalidSourceText, match="Unbalanced"):
        study.inspect_id_rows(fixture(row(2) + ' "unterminated'))


def test_non_22_field_extension_triggers_stop():
    with pytest.raises(study.ParserDisagreement, match="width"):
        study.inspect_id_rows(fixture(row(2).replace(" 0", "", 1)))


def test_invalid_utf8_rejected_before_per_row_analysis():
    with pytest.raises(study.InvalidSourceText, match="UTF-8"):
        study.inspect_id_rows(b"\xff\xfe")


def test_source_sha_mismatch_stops_before_any_row_parser(monkeypatch):
    def forbidden(_):
        raise AssertionError("No source bytes may be parsed on SHA mismatch")

    monkeypatch.setattr(study, "parse_original", forbidden)
    result = study.audit_bytes(fixture(row(1)))
    assert result["decision"] == "SOURCE_SHA_MISMATCH"
    assert result["diagnostic"] is None
    assert result["d02_first_verdict_unchanged"] == "DATASET_SCHEMA_REJECTED"


def test_synthetic_localization_success_preserves_d02_rejection(monkeypatch):
    raw = fixture(row(1, "short"), row(0, "long"), row(3, "long"))
    pin_fixture(monkeypatch, raw, eligible=2, queues=2)
    result = study.audit_bytes(raw)
    assert result["decision"] == "ANOMALY_LOCALIZED"
    assert result["diagnostic"]["nonpositive_job_id_count"] == 1
    assert result["diagnostic"]["d02_extended_queue_count"] == 2
    assert result["d02_first_verdict_unchanged"] == "DATASET_SCHEMA_REJECTED"
    assert result["predictive_scores_computed"] is False


def test_a_second_invalid_id_never_localizes_as_the_original(monkeypatch):
    raw = fixture(row(1, "short"), row(0, "long"), row(-5, "long"))
    pin_fixture(monkeypatch, raw, eligible=1, queues=1)
    result = study.audit_bytes(raw)
    assert result["decision"] == "ANOMALY_NOT_REPRODUCED"
    assert result["diagnostic"]["nonpositive_job_id_count"] == 2


def test_mismatched_eligible_count_never_pretends_profile_verified(monkeypatch):
    raw = fixture(row(1, "short", requested=-1), row(0, "long"), row(3, "long"))
    pin_fixture(monkeypatch, raw, eligible=2, queues=1)
    result = study.audit_bytes(raw)
    assert result["decision"] == "PARSER_DISAGREEMENT"
    assert result["diagnostic"]["d02_standard_eligible_rows"] == 1


def test_first_source_archives_access_block_instead_of_retry(monkeypatch, tmp_path):
    def blocked():
        raise SourceBlocked("fixture simulated official source blocked")

    monkeypatch.setattr(study, "download_exact", blocked)
    folder = tmp_path / "original"
    report = study.first_source(folder)
    assert report["decision"] == "SOURCE_ACCESS_BLOCKED"
    assert report["errors"][0]["stage"] == "original-provider-access"
    assert json.loads((folder / "RP-E011-D03.json").read_text()) == report
    with pytest.raises(ValueError, match="overwrite"):
        study.first_source(folder)
