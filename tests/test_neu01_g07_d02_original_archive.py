"""Verify original G07-D02 first source metadata and preserve its exact bytes."""
from hashlib import sha256
import json
from pathlib import Path

AUDIT = Path("docs/results/NEU-01-G07-D02-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G07-D02-first-run/archive-index.json")
FROZEN = "5bf3dd61678b267c4997ed56328ae1c8183389d44e1c21910b315d59f8e7cef9"


def test_original_d02_bytes_sha256():
    data = AUDIT.read_bytes()
    assert len(data) == 4008
    assert sha256(data).hexdigest() == FROZEN
    assert data.endswith(b"\n")


def test_original_source_run_chronology_not_renamed():
    i = json.loads(INDEX.read_text())
    assert i["post_result_protocol_commit"] == "7bc2b1e73032a290748fdb38326974771a6f8244"
    assert i["first_implementation_commit"] == "49cb81125a212da5a6a01f482e7707ea1ae6d8fd"
    assert i["first_source_workflow_run_id"] == 43333636930
    assert i["pre_source_synthetic_tests_passed"] == 6
    assert i["original_artifact"]["id"] == 13996481794
    assert i["first_aggregate_json"]["sha256"] == FROZEN
    assert i["source_attempt_number"] == 1


def test_original_d02_metadata_without_amplitudes():
    d = json.loads(AUDIT.read_text())
    assert d["status"] == "TOPLEVEL_EEGLAB_FIELD_LAYOUT_RESOLVED"
    assert d["retrospective_post_g07_missing_EEG_variable"] is True
    assert d["original_derivative_full_body_authenticated"] is True
    assert d["original_derivative_identity"]["original_bytes"] == 73824136
    assert d["original_derivative_identity"]["observed_sha256"] == "2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359"
    meta = d["top_level_metadata"]
    assert (meta["nbchan"], meta["pnts"], meta["trials"], meta["srate_hz"]) == (61, 150000, 1, 500)
    assert meta["reference_label"] == "common"
    assert meta["safe_known_top_level_fields"]["data"] == {"dimensions": [61,150000],"matlab_class":"double"}
    assert meta["safe_known_top_level_fields"]["history"]["dimensions"] == [0]
    assert meta["total_matlab_variables"] == 42
    assert meta["other_unpublished_variable_names_count"] == 22
    assert meta["missing_required_metadata"] == []
    assert meta["raw_eeg_values_loaded_by_investigation"] is False
    assert meta["source_derivative_sample_alignment_verified"] is False
    assert d["other_five_derivative_bodies_authenticated"] is False
    assert d["sample_alignment_verified"] is False
    assert d["causal_processing_stage_identified"] is False
    assert d["original_eeg_binary_uploaded"] is False


def test_tampered_archive_changes_hash():
    b = AUDIT.read_bytes()
    changed = b.replace(b"TOPLEVEL_EEGLAB_FIELD_LAYOUT_RESOLVED", b"TOPLEVEL_EEGLAB_FIELD_LAYOUT_UNKNOWN", 1)
    assert changed != b
    assert sha256(changed).hexdigest() != FROZEN
