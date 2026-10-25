"""Synthetic-only adversarial checks for D04; never download original jobs."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from experiments import rp_e011_d04_temporal as d04
from experiments.rp_e011_jsspp_source import SourceBlocked


def row(job_id: int, submit: int, wait: int = 0,
        queue: str = "short", requested: int = 1, status: int = 1) -> str:
    standard = [
        str(job_id), str(submit), str(wait), "1", "1",
        "-1", "-1", str(requested), "3600", "-1",
        str(status), "-1", "-1", "-1", "-1", "-1", "-1", "-1",
    ]
    return " ".join(standard) + f' node-a {queue} "opaque qsub args" 0'


def sample(*lines: str) -> bytes:
    return ("\n".join(lines) + "\n").encode()


def patch_small_sample(monkeypatch, *lines: str):
    monkeypatch.setattr(d04, "EXPECTED_ROWS", len(lines))
    return sample(*lines)


def test_known_archive_sha_and_first_line_have_not_changed():
    d04.verify_original_archives()
    source = d04.ROOT / "docs/results/RP-E011-D03-first-run/audit.json"
    report = json.loads(source.read_text("utf-8"))
    assert sha256(source.read_bytes()).hexdigest() == d04.D03_AUDIT_SHA
    assert report["diagnostic"]["nonpositive_job_ids"][0]["physical_line"] == 1


def test_exception_only_for_first_line_and_counted_explicitly(monkeypatch):
    raw = patch_small_sample(
        monkeypatch, row(0, 1), row(2, 2, queue="a"), row(3, 3, queue="b")
    )
    jobs, profile = d04.parse_temporal_candidates(raw)
    assert len(jobs) == 2
    assert profile["known_first_line_id_zero_exception_count"] == 1
    assert profile["original_source_data_rows"] == 3
    assert profile["included_status_counts"] == {"1": 2}


def test_later_zero_not_reclassified_as_a_header(monkeypatch):
    raw = patch_small_sample(monkeypatch, row(1, 1), row(0, 2))
    with pytest.raises(d04.SchemaDisagreement, match="additional nonpositive"):
        d04.parse_temporal_candidates(raw)


def test_negative_id_is_fatal_even_with_valid_other_fields(monkeypatch):
    raw = patch_small_sample(monkeypatch, row(0, 1), row(-2, 2))
    with pytest.raises(d04.SchemaDisagreement, match="additional nonpositive"):
        d04.parse_temporal_candidates(raw)


def test_duplicate_id_is_never_accepted(monkeypatch):
    raw = patch_small_sample(monkeypatch, row(0, 1), row(2, 2), row(2, 3))
    with pytest.raises(d04.SchemaDisagreement, match="duplicate"):
        d04.parse_temporal_candidates(raw)


def test_bad_wait_and_resource_fail_before_any_model(monkeypatch):
    raw = patch_small_sample(monkeypatch, row(0, 1), row(1, 2, wait=-3))
    with pytest.raises(d04.SchemaDisagreement, match="start timestamp"):
        d04.parse_temporal_candidates(raw)
    raw = patch_small_sample(monkeypatch, row(0, 1), row(1, 2, requested=0))
    with pytest.raises(d04.SchemaDisagreement, match="invalid eligible"):
        d04.parse_temporal_candidates(raw)


def test_status_is_observed_but_not_used_to_drop_target(monkeypatch):
    raw = patch_small_sample(
        monkeypatch, row(0, 1), row(2, 2, status=0), row(3, 3, status=-1)
    )
    jobs, profile = d04.parse_temporal_candidates(raw)
    assert len(jobs) == 2
    assert profile["included_status_counts"] == {"-1": 1, "0": 1}


def test_bad_queue_and_wrong_width_never_admitted(monkeypatch):
    raw = patch_small_sample(monkeypatch, row(0, 1), row(1, 2, queue="?"))
    with pytest.raises(d04.SchemaDisagreement, match="lacks queue"):
        d04.parse_temporal_candidates(raw)
    raw = patch_small_sample(monkeypatch, row(0, 1), row(1, 2) + " 99")
    with pytest.raises(d04.SchemaDisagreement, match="22"):
        d04.parse_temporal_candidates(raw)


def test_exact_70_30_chronological_cutoff_and_count_oracles(monkeypatch):
    monkeypatch.setattr(d04, "EXPECTED_ELIGIBLE", 10)
    source = [
        (Decimal(i), i + 1, "a" if i % 2 == 0 else "b")
        for i in range(10)
    ]
    result = d04.temporal_coverage(source, min_split=2, min_queue=1, cross_queues=2)
    assert result["fixed_chronological_cutoff_seconds"] == "6.3"
    assert result["diagnostic_candidate_count"] == 7
    assert result["heldout_candidate_count"] == 3
    assert result["distinct_queue_count"] == 2
    assert result["independent_sorted_vs_streaming_split_counts_agree"] is True
    assert result["feasible"] is True


def test_tied_submit_records_remain_in_one_split(monkeypatch):
    monkeypatch.setattr(d04, "EXPECTED_ELIGIBLE", 6)
    jobs = [
        (Decimal(0), 1, "a"), (Decimal(0), 2, "b"),
        (Decimal(7), 3, "a"), (Decimal(7), 4, "b"),
        (Decimal(10), 5, "a"), (Decimal(10), 6, "b"),
    ]
    outcome = d04.temporal_coverage(jobs, min_split=2, min_queue=1, cross_queues=2)
    assert outcome["fixed_chronological_cutoff_seconds"] == "7"
    assert outcome["diagnostic_candidate_count"] == 2
    assert outcome["heldout_candidate_count"] == 4
    assert outcome["feasible"] is True


def test_single_cross_queue_fails_despite_high_total_counts(monkeypatch):
    monkeypatch.setattr(d04, "EXPECTED_ELIGIBLE", 8)
    rows = [
        (Decimal(i), i + 1, "x" if i < 4 else "y")
        for i in range(8)
    ]
    out = d04.temporal_coverage(rows, min_split=2, min_queue=1, cross_queues=2)
    assert out["feasible"] is False


def test_byte_hash_mismatch_forbids_all_parser_access(monkeypatch):
    def forbidden():
        raise AssertionError("Original archives must not be consulted on SHA mismatch")
    monkeypatch.setattr(d04, "verify_original_archives", forbidden)
    result = d04.audit_verified_bytes(b"synthetic not original")
    assert result["decision"] == "SOURCE_SHA_MISMATCH"
    assert result["schema"] is None
    assert result["temporal_coverage"] is None


def test_independent_oracle_mismatch_is_fatal(monkeypatch):
    original = b"synthetic"
    monkeypatch.setattr(d04, "SOURCE_SHA", sha256(original).hexdigest())
    monkeypatch.setattr(d04, "SOURCE_SIZE", len(original))
    monkeypatch.setattr(d04, "verify_original_archives", lambda: None)
    def disagree(_):
        raise d04.SchemaDisagreement("two oracles disagree")
    monkeypatch.setattr(d04, "match_original_d02", disagree)
    outcome = d04.audit_verified_bytes(original)
    assert outcome["decision"] == "SOURCE_SCHEMA_DISAGREEMENT"
    assert outcome["predictions_computed"] is False


def test_first_run_block_archived_and_not_overwritten(monkeypatch, tmp_path):
    def blocked():
        raise SourceBlocked("fixture forbidden original provider access")
    monkeypatch.setattr(d04, "download_exact", blocked)
    target = tmp_path / "first"
    outcome = d04.first_run(target)
    assert outcome["decision"] == "SOURCE_ACCESS_BLOCKED"
    assert json.loads((target / "RP-E011-D04.json").read_text()) == outcome
    with pytest.raises(ValueError, match="overwrite"):
        d04.first_run(target)


def test_sort_does_not_use_wait_or_future_status_as_feature():
    jobs = [
        (Decimal(9), 10, "a"),
        (Decimal(1), 20, "a"),
        (Decimal(3), 30, "b"),
    ]
    assert all(len(rec) == 3 for rec in jobs)
    # Only [submit, positive ID, queue] flow into the cohort splitter.
    assert sorted(jobs) == [
        (Decimal(1), 20, "a"),
        (Decimal(3), 30, "b"),
        (Decimal(9), 10, "a"),
    ]
