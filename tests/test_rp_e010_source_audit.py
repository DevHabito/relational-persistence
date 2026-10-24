"""Adversarial SWF and frozen provenance tests for RP-E010-D01.

Tiny synthetic rows in this module are parser fixtures ONLY, not
production traces or outcome labels. No prediction model appears.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from experiments.rp_e010_source_audit import (
    EXPECTED_BLOB, EXPECTED_BYTES, REVISION, FILEPATH, SOURCE_URL,
    classify, git_blob_sha1, inspect_bytes, parse_swf_independent,
    parse_swf_primary, sha256,
)


def swf_row(job: int, submit: str = "0", wait: str = "5",
            runtime: str = "9", processors: str = "2",
            status: str = "1", queue: str = "1") -> str:
    row = ["-1"] * 18
    row[0] = str(job)
    row[1] = submit
    row[2] = wait
    row[3] = runtime
    row[4] = processors
    row[10] = status
    row[14] = queue
    return " ".join(row)


def fixture(*rows: str) -> bytes:
    return ("; Format: SWF 2.2\n\n"
            + "\n".join(rows) + "\n").encode("utf-8")


def read_both(data: bytes) -> dict:
    result_a = parse_swf_primary(data)
    result_b = parse_swf_independent(data)
    assert result_a == result_b
    return result_a


def test_provenance_is_pinned_and_not_a_latest_branch():
    assert REVISION == "f349db7f7783333f668e79618da62f8714fd7f2c"
    assert EXPECTED_BLOB == "6d3cf513d74f6b839dc8425dd30bc889e15dc3be"
    assert FILEPATH == "workloads/hpc2n.swf"
    assert EXPECTED_BYTES == 19_242_100
    assert f"/{REVISION}/" in SOURCE_URL
    assert SOURCE_URL.startswith("https://raw.githubusercontent.com/")


def test_git_blob_hash_uses_canonical_size_prefixed_git_framing():
    payload = b"hello\n"
    import hashlib
    assert git_blob_sha1(payload) == hashlib.sha1(b"blob 6\0hello\n").hexdigest()
    assert len(sha256(payload)) == 64


def test_all_18_fields_and_two_oracles_agree_on_valid_fixture():
    stats = read_both(fixture(
        swf_row(1, "0"), swf_row(2, "2.5"), swf_row(3, "2.5")
    ))
    assert stats["header_lines"] == 1
    assert stats["data_lines"] == 3
    assert stats["eligible_completed"] == 3
    assert stats["bad_width"] == stats["invalid_numeric"] == 0
    assert stats["duplicate_job_ids"] == stats["unsorted_submit"] == 0


def test_duplicate_id_is_detected_and_cannot_be_discarded():
    stats = read_both(fixture(swf_row(1), swf_row(1, "3")))
    assert stats["duplicate_job_ids"] == 1
    assert classify(stats, identity_verified=True) == "DATASET_SCHEMA_REJECTED"


def test_timestamp_regression_is_not_silently_sorted_by_parser():
    stats = read_both(fixture(swf_row(1, "9"), swf_row(2, "8")))
    assert stats["unsorted_submit"] == 1
    assert classify(stats, identity_verified=True) == "DATASET_SCHEMA_REJECTED"


def test_wrong_width_and_non_numeric_job_ids_reject_source():
    stats = read_both(fixture(
        swf_row(1), "1 2 3", swf_row(2).replace("2 ", "not-an-id ", 1)
    ))
    assert stats["bad_width"] == 1
    assert stats["invalid_numeric"] == 1
    assert len(stats["first_bad_lines"]) == 2
    assert classify(stats, identity_verified=True) == "DATASET_SCHEMA_REJECTED"


def test_negatives_are_counted_without_inventing_timestamps():
    rows = [
        swf_row(1, submit="-1"),
        swf_row(2, wait="-1"),
        swf_row(3, runtime="-1"),
        swf_row(4, processors="-1"),
        swf_row(5, status="-1"),
        swf_row(6, queue="-1"),
    ]
    stats = read_both(fixture(*rows))
    assert stats["missing_submit"] == 1
    assert stats["missing_wait"] == 1
    assert stats["missing_runtime"] == 1
    assert stats["missing_processors"] == 1
    assert stats["missing_status"] == 1
    assert stats["missing_queue"] == 1
    assert stats["eligible_completed"] == 1


@pytest.mark.parametrize("bad_field", ("NaN", "Infinity", "not-a-number"))
def test_nonfinite_and_invalid_values_are_rejected(bad_field):
    stats = read_both(fixture(swf_row(1, runtime=bad_field)))
    assert stats["invalid_numeric"] == 1
    assert stats["eligible_completed"] == 0


def test_nonintegral_processor_cannot_be_a_valid_job():
    stats = read_both(fixture(swf_row(1, processors="1.5")))
    assert stats["invalid_numeric"] == 1


def test_missing_data_is_not_automatically_filled():
    stat = read_both(fixture(swf_row(1, wait="-1")))
    assert stat["missing_wait"] == 1
    assert stat["eligible_completed"] == 0


def test_source_byte_tampering_cannot_pass_pinned_identity():
    data = fixture(swf_row(1))
    outcome = inspect_bytes(data)
    assert outcome["identity_verified"] is False
    assert outcome["decision"] == "DATASET_SCHEMA_REJECTED"
    assert outcome["actual_git_blob_sha1"] != EXPECTED_BLOB
    assert outcome["independent_parser_agreement"] is True


def test_corrupt_unicode_is_not_silently_replaced():
    with pytest.raises(UnicodeDecodeError):
        parse_swf_primary(b"\xff\xfe")


def test_only_thousand_eligible_observations_can_pass_schema_gate():
    stat = read_both(fixture(*(
        swf_row(i + 1, submit=str(i)) for i in range(1000)
    )))
    assert stat["eligible_completed"] == 1000
    assert classify(stat, identity_verified=True) == "DATASET_SCHEMA_VERIFIED"


def test_blank_lines_keep_same_original_line_number_in_both_oracles():
    stats = read_both(b"; A\n\n\n1 2 3\n")
    assert stats["first_bad_lines"][0]["line_number"] == 4


def test_first_bad_lines_are_bounded_and_do_not_copy_user_job_fields():
    stats = read_both(fixture(*(["not an SWF row"] * 20)))
    assert stats["bad_width"] == 20
    assert len(stats["first_bad_lines"]) == 8
    assert all(set(item) == {"line_number", "reason"}
               for item in stats["first_bad_lines"])
