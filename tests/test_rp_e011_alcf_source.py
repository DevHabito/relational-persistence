"""Adversarial preregistered RP-E011-D01 official-source audit tests.

All CSV fixtures are artificial; there is NO official Polaris download,
no predictive scoring, and no observational scientific measurement in CI.
"""

from __future__ import annotations

from copy import deepcopy
import csv
from io import StringIO

import pytest

from experiments.rp_e011_alcf_source import (
    CATALOG_COMPRESSED_BYTES, EXPECTED_CSV_BYTES, FILENAME, ORIGIN,
    PAGE, PROTOCOL, REQUIRED_COLUMNS, SourceBlocked,
    decode_response, first_audit, official_url,
    resolve_download, safe_decimal, safe_time, source_gate,
    structural_audit,
)


def csv_fixture(records: list[dict]) -> bytes:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS)
    writer.writeheader()
    for record in records:
        writer.writerow(record)
    return output.getvalue().encode("utf-8")


def row(identifier: str, queue: str = "debug",
        queued: str = "2022-08-09 08:00:00",
        started: str = "2022-08-09 08:10:00") -> dict:
    return {
        "COBALT_JOBID": identifier,
        "MACHINE_NAME": "polaris",
        "QUEUED_TIMESTAMP": queued,
        "START_TIMESTAMP": started,
        "END_TIMESTAMP": "2022-08-09 08:20:00",
        "QUEUE_NAME": queue,
        "NODES_REQUESTED": "4",
        "NODES_USED": "4",
        "WALLTIME_SECONDS": "1800",
        "QUEUED_WAIT_SECONDS": "600",
        "ELIGIBLE_WAIT_SECONDS": "600",
        "DATA_LOAD_STATUS": "complete",
    }


def fixture_page(path: str = f"/data/{FILENAME}") -> str:
    return f'<html><a href="{path}">Download</a></html>'


def test_canonical_source_metadata_not_changed():
    assert PROTOCOL == "RP-E011-D01"
    assert EXPECTED_CSV_BYTES == 27_825_794
    assert CATALOG_COMPRESSED_BYTES == 2_261_468
    assert PAGE.startswith("https://reports.alcf.anl.gov/data/")
    assert "20220809_20221231" in PAGE
    assert len(REQUIRED_COLUMNS) == 12


def test_explicit_single_same_origin_link_is_accepted():
    url, detail = resolve_download(fixture_page())
    assert url == f"https://{ORIGIN}/data/{FILENAME}"
    assert detail["trusted_matching_direct_downloads"] == 1
    assert detail["matching_resolution_methods"] == ["a.href"]


def test_no_link_is_blocked_instead_of_guessing_url():
    with pytest.raises(SourceBlocked, match="does not expose exactly one"):
        resolve_download("<html><button>Download</button></html>")


def test_unrelated_file_and_wrong_annual_period_do_not_substitute():
    with pytest.raises(SourceBlocked):
        resolve_download(fixture_page("/data/ANL-ALCF-DJC-POLARIS_20230101_20231231.csv"))


def test_multiple_matching_downloads_are_ambiguity_not_fallback():
    page = (
        fixture_page()
        + f'<a href="/api/download/{FILENAME}">another source</a>'
    )
    with pytest.raises(SourceBlocked, match="matched=2"):
        resolve_download(page)


def test_off_origin_http_javascript_and_credentials_blocked():
    assert official_url(f"http://{ORIGIN}/data/{FILENAME}") is False
    assert official_url(f"https://example.org/{FILENAME}") is False
    assert official_url(f"https://attacker@{ORIGIN}/{FILENAME}") is False
    assert official_url(f"https://{ORIGIN}:444/{FILENAME}") is False
    with pytest.raises(SourceBlocked):
        resolve_download(fixture_page(f"https://evil.example/{FILENAME}"))


def test_gzip_fixture_decodes_without_guessing_size():
    import gzip
    payload = b"COL1,COL2\none,two\n"
    compressed = gzip.compress(payload)
    original, encoding = decode_response(compressed)
    assert encoding == "gzip"
    assert original == payload


def test_fabricated_html_response_cannot_be_accepted_as_csv():
    with pytest.raises(SourceBlocked, match="HTML"):
        decode_response(b"<html><body>No dataset</body></html>")


def test_separate_readers_agree_on_genuine_csv_fixture_counts():
    record = structural_audit(csv_fixture([row("1"), row("2", queue="regular")]))
    assert record["data_rows"] == 2
    assert record["independent_csv_reader_rows"] == 2
    assert record["independent_csv_readers_agree"] is True
    assert record["wrong_width_rows"] == 0
    assert record["distinct_nonempty_queue_name_count"] == 2
    assert record["missing_required_columns"] == []


def test_only_two_queues_and_complete_timestamps_generate_eligible_rows():
    result = structural_audit(csv_fixture([
        row("1"), row("2", queue="production"),
        row("3", queue="", started=""),
    ]))
    assert result["missing_and_invalid_counts"][
        "structurally_usable_queued_and_started_rows"
    ] == 2
    assert result["missing_and_invalid_counts"]["missing_queue_name"] == 1
    assert result["missing_and_invalid_counts"][
        "missing_or_invalid_start_timestamp"
    ] == 1


def test_duplicate_and_invalid_ids_remain_visible_even_when_rows_have_valid_width():
    observed = structural_audit(csv_fixture([
        row("1"), row("1"), row("unknown"), row("-3"),
    ]))
    counts = observed["missing_and_invalid_counts"]
    assert counts["duplicate_job_id"] == 1
    assert counts["invalid_job_id"] == 2


def test_both_queued_and_eligible_wait_are_distinct_fields():
    records = [row("1")]
    records[0]["ELIGIBLE_WAIT_SECONDS"] = "0"
    observed = structural_audit(csv_fixture(records))
    assert observed["missing_and_invalid_counts"].get(
        "documented_queued_wait_disagreements_over_1s", 0
    ) == 0


def test_queued_wait_mismatch_is_reported_not_corrected():
    records = [row("1")]
    records[0]["QUEUED_WAIT_SECONDS"] = "8"
    observed = structural_audit(csv_fixture(records))
    assert observed["missing_and_invalid_counts"][
        "documented_queued_wait_disagreements_over_1s"
    ] == 1


def test_nonfinite_nodes_and_timestamp_formats_cannot_be_imputed():
    assert safe_decimal("NaN") is None
    assert safe_decimal("Infinity") is None
    assert safe_decimal("-1") == -1
    assert safe_time("2022-08-09 08:10:00.123456") is not None
    assert safe_time("not-a-timestamp") is None
    assert safe_time("") is None


def test_wrong_width_is_detected_by_both_independent_reader_paths():
    csv_blob = csv_fixture([row("1")])
    csv_blob += b"not,a,full,CSV,row\n"
    result = structural_audit(csv_blob)
    assert result["wrong_width_rows"] == 1
    assert result["independent_csv_reader_wrong_width_rows"] == 1
    assert result["independent_csv_readers_agree"] is True


def test_wrong_width_or_missing_header_prevents_source_pass():
    blob = csv_fixture([row("1"), row("2", queue="production")])
    stats = structural_audit(blob)
    assert source_gate(blob, stats) == "DATASET_SCHEMA_REJECTED"
    altered = deepcopy(stats)
    altered["missing_required_columns"].append("QUEUE_NAME")
    assert source_gate(blob, altered) == "DATASET_SCHEMA_REJECTED"


def test_dont_declare_a_fixture_success_without_original_catalog_size():
    records = [row(str(i), queue="a" if i % 2 else "b")
               for i in range(1200)]
    blob = csv_fixture(records)
    stats = structural_audit(blob)
    assert stats["missing_and_invalid_counts"][
        "structurally_usable_queued_and_started_rows"
    ] == 1200
    assert stats["distinct_nonempty_queue_name_count"] == 2
    assert source_gate(blob, stats) == "DATASET_SCHEMA_REJECTED"


def test_first_official_source_attempt_with_no_link_archives_blocked(tmp_path):
    output = tmp_path / "first"
    result = first_audit(
        output, page_override="<button>Download</button>"
    )
    assert result["decision"] == "SOURCE_ACCESS_BLOCKED"
    assert result["queue_prediction_scored"] is False
    assert (output / "RP-E011-D01.json").exists()


def test_first_download_tiny_fixture_archives_rejected_and_sha(tmp_path):
    original = csv_fixture([row("1")])
    result = first_audit(
        tmp_path / "first", page_override=fixture_page(),
        download_override=original,
    )
    assert result["decision"] == "DATASET_SCHEMA_REJECTED"
    assert result["acquisition"]["uncompressed_csv_bytes"] == len(original)
    assert result["schema"] is None
    assert result["physical_law_validated"] is False


def test_existing_original_run_never_overwritten(tmp_path):
    output = tmp_path / "original"
    output.mkdir()
    (output / "RP-E011-D01.json").write_text("original")
    with pytest.raises(ValueError, match="overwrite"):
        first_audit(output, page_override=fixture_page())


def test_no_leakage_through_future_scheduler_fields_in_schema():
    # D01 can count these columns' presence, never score a wait predictor.
    record = row("1")
    record["END_TIMESTAMP"] = "2022-08-09 09:20:00"
    report = structural_audit(csv_fixture([record]))
    assert report["missing_and_invalid_counts"].get("wait_mae", 0) == 0
    assert report["independent_csv_readers_agree"] is True
