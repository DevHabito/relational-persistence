"""Synthetic-only regression of separately registered RP-E011-D02 source gate.

These fixtures are NOT source observations and cannot validate any
scheduler, forecast, cross-site generalization or physical theory.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from experiments.rp_e011_jsspp_source import (
    DOCUMENTED_QUEUE_INDEX, MAX_ORIGINAL_BYTES, MIN_ELIGIBLE,
    PROTOCOL, SOURCE_URL, SourceBlocked, classify, first_source,
    official_origin, parse_original, standard_swf_fields,
)


def base(job_id: int, *, submit=100, wait=15, runtime=200,
         allocated=2, requested=4, status=1, queue_number=-1) -> list[str]:
    values = ["-1"] * 18
    values[0] = str(job_id)
    values[1] = str(submit)
    values[2] = str(wait)
    values[3] = str(runtime)
    values[4] = str(allocated)
    values[7] = str(requested)
    values[10] = str(status)
    values[14] = str(queue_number)
    return values


def row(job_id: int, queue="short", **kwargs) -> str:
    return (
        " ".join(base(job_id, **kwargs)) +
        f' nodeA {queue} "--walltime 20m --cores 4" 0'
    )


def source(*lines: str) -> bytes:
    return ("; JSSPP extended SWF\n\n" + "\n".join(lines) + "\n").encode("utf-8")


def test_separate_source_url_frozen_not_retry_of_alcf():
    assert PROTOCOL == "RP-E011-D02"
    assert SOURCE_URL.endswith("/2017/cerit/grid-jobs.swf")
    assert DOCUMENTED_QUEUE_INDEX == 19
    assert MIN_ELIGIBLE == 1000
    assert MAX_ORIGINAL_BYTES == 150_000_000


def test_enforce_original_archive_https_same_origin():
    assert official_origin(SOURCE_URL) is True
    assert official_origin("http://jsspp.org/workload/grid-jobs.swf") is False
    assert official_origin("https://mirror.invalid/workload/grid-jobs.swf") is False
    assert official_origin("https://malicious@jsspp.org/grid-jobs.swf") is False


def test_unquoted_standard_prefix_and_quoted_extensions_have_same_prefix():
    line = row(1, queue="short")
    result = parse_original(source(line, row(2, queue="long")))
    assert result["counts"]["data_rows"] == 2
    assert result["counts"]["valid_numeric_prefix_rows"] == 2
    assert result["counts"]["standard_eligible_rows"] == 2
    assert result["independent_standard_prefix_readers_agree"] is True
    assert result["distinct_documented_extended_queue_names_on_eligible_jobs"] == 2
    assert result["parsed_record_widths"]["22"] == 2


def test_status_is_source_metadata_not_hindsight_waittime_filter():
    data = parse_original(source(row(1, status=-1, queue="long")))
    assert data["counts"]["unknown_status"] == 1
    assert data["counts"]["standard_eligible_rows"] == 1


def test_unavailable_original_wait_and_requested_resources_counted_no_imputation():
    data = parse_original(source(
        row(1, wait=-1),
        row(2, requested=-1),
        row(3, allocated=0),
        row(4, submit=-1),
    ))
    stat = data["counts"]
    assert stat["missing_wait"] == 1
    assert stat["missing_submit"] == 1
    assert stat["nonpositive_requested_processors"] == 1
    assert stat["nonpositive_allocated_processors"] == 1
    assert stat.get("standard_eligible_rows", 0) == 0


def test_missing_extended_queue_name_cannot_be_replaced_by_numeric_swf_queue():
    base_record = base(1, queue_number=12)
    original = source(" ".join(base_record))
    result = parse_original(original)
    assert result["counts"]["missing_documented_extended_queue_column"] == 1
    assert result["distinct_documented_extended_queue_names_on_eligible_jobs"] == 0


def test_duplicated_job_id_is_fatal_even_if_queue_is_available():
    data = parse_original(source(row(1, "a"), row(1, "b")))
    assert data["counts"]["duplicate_job_id"] == 1
    assert classify(data) == "DATASET_SCHEMA_REJECTED"


def test_negative_or_zero_job_id_is_rejected():
    data = parse_original(source(row(-1, "a"), row(0, "b")))
    assert data["counts"]["invalid_job_id"] == 2
    assert classify(data) == "DATASET_SCHEMA_REJECTED"


def test_bad_numeric_standard_prefix_not_force_interpreted():
    broken = base(1)
    broken[2] = "not-a-time"
    data = parse_original(source(" ".join(broken) + ' nodeA queueX "args" 0'))
    assert data["counts"]["bad_18_field_swf_prefixes"] == 1
    assert classify(data) == "DATASET_SCHEMA_REJECTED"


def test_unterminated_quoted_qsub_arguments_are_preserved_as_failure():
    malformed = " ".join(base(1)) + ' nodeA short "unterminated'
    data = parse_original(source(malformed))
    assert data["counts"]["quote_parse_failures"] == 1
    assert data["first_10_source_structure_problems"][0]["line"] == 3
    assert classify(data) == "DATASET_SCHEMA_REJECTED"


def test_wrong_type_binary_file_is_rejected_no_ocr_or_false_swf():
    with pytest.raises(ValueError, match="binary"):
        parse_original(b"FWS\x00binaryadobeSWF")
    with pytest.raises(ValueError, match="UTF-8"):
        parse_original(b"\xff\xfe\xfa")


def test_provenance_source_has_no_upstream_sha_pretence(tmp_path):
    result = first_source(
        tmp_path / "fixture", byte_override=source(row(1, "a"))
    )
    assert result["source"]["fixture_only"] is True
    assert result["decision"] == "DATASET_SCHEMA_REJECTED"
    assert result["source_unmodified"] is True
    assert result["retrospective_forecast_evaluated"] is False
    assert result["scalar_C_law_tested"] is False


def test_999_valid_jobs_do_not_pass_pre_registered_1000_gate():
    rows = [row(i + 1, queue=("a" if i % 2 else "b"))
            for i in range(999)]
    result = parse_original(source(*rows))
    assert result["counts"]["standard_eligible_rows"] == 999
    assert classify(result) == "DATASET_SCHEMA_REJECTED"


def test_1000_independent_queue_labeled_source_fixture_can_pass():
    rows = [row(i + 1, queue=("a" if i % 2 else "b"))
            for i in range(1000)]
    result = parse_original(source(*rows))
    assert result["counts"]["standard_eligible_rows"] == 1000
    assert result["distinct_documented_extended_queue_names_on_eligible_jobs"] == 2
    assert result["independent_standard_prefix_readers_agree"] is True
    assert classify(result) == "DATASET_SCHEMA_VERIFIED"


def test_single_real_extended_queue_never_passes():
    rows = [row(i + 1, queue="one") for i in range(1001)]
    result = parse_original(source(*rows))
    assert result["counts"]["standard_eligible_rows"] == 1001
    assert result["distinct_documented_extended_queue_names_on_eligible_jobs"] == 1
    assert classify(result) == "DATASET_SCHEMA_REJECTED"


def test_missing_or_garbled_extended_queue_value_must_not_count():
    data = parse_original(source(row(1, "-1"), row(2, "null")))
    assert data["counts"]["missing_documented_extended_queue_name"] == 2
    assert data["distinct_documented_extended_queue_names_on_eligible_jobs"] == 0


def test_first_run_file_is_immutable_even_when_original_outcome_negative(tmp_path):
    folder = tmp_path / "original"
    folder.mkdir()
    (folder / "RP-E011-D02.json").write_text("frozen record")
    with pytest.raises(ValueError, match="replace first"):
        first_source(folder, byte_override=source(row(1)))


def test_swf_parser_never_returns_wait_forecast_or_holdout_loss():
    data = parse_original(source(row(1)))
    assert data["queue_wait_predictions_computed"] is False
    assert "MAE" not in str(data)
    assert "heldout_prediction" not in str(data)


def test_invalid_quote_cannot_hide_first_source_error_line_number():
    original = source(*(' '.join(base(i))+' name queue "unterminated' for i in range(20)))
    result = parse_original(original)
    assert len(result["first_10_source_structure_problems"]) == 10
    assert all(set(x) == {"line", "issue"}
               for x in result["first_10_source_structure_problems"])
