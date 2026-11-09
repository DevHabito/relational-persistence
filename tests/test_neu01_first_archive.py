"""NEU-01-G00: first hosted sidecar outcome is checksum-pinned, not EEG data."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest

from experiments import neu01_source_metadata_gate as gate

ORIGINAL = Path("docs/results/NEU-01-G00-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G00-first-run/archive-index.json")
FIXED_DIGEST = "cec3cd2e71c70740ed272cc383ceca53f1ebdf3a854d86932ef50702338b21d6"


def original(first=ORIGINAL, provenance=INDEX):
    raw=first.read_bytes()
    index=json.loads(provenance.read_text(encoding="utf-8"))
    if sha256(raw).hexdigest()!=FIXED_DIGEST:
        raise ValueError("NEU-01 original first metadata result SHA changed")
    if index["first_original_json_sha256"]!=FIXED_DIGEST:
        raise ValueError("NEU-01 archive index differs from original first SHA")
    return json.loads(raw),index


def test_original_runner_identity_source_scope_and_metadata_decision():
    result, index=original()
    assert index["first_hosted_run_id"]=="42613113888"
    assert index["first_code_and_workflow_head"]=="87b6d04f35d37dad1e8b83449ec6242afa0f7f6d"
    assert index["protocol_only_commit"]==gate.PROTOCOL_SHA
    assert index["original_git_dataset_commit"]==gate.DATASET_SHA
    assert index["first_preflight_tests_passed"]==19
    assert result["decision"]=="SOURCE_SIDECAR_DISAGREEMENT_PRESENT"
    assert result["source_scope"]=="five BIDS JSON/TSV sidecar pairs from sub-01 session1"
    assert result["number_of_disagreeing_task_sidecars"]==1
    assert result["lz_complexity_computed_on_original_eeg"] is False
    assert result["raw_eeg_binary_values_downloaded"] is False
    assert result["subject_diagnosis_or_self_continuity_inferred"] is False


def test_independent_manifest_replay_agrees_with_original():
    result,_=original()
    current=json.loads(gate.MANIFEST.read_text(encoding="utf-8"))
    assert result==gate.evaluate(current)
    details=result["sidecar_channel_count_disagreements"][0]
    assert details["task"]=="eyesclosed"
    assert details["declared_eeg_channels"]==64
    assert details["companion_tsv_rows"]==61


def test_original_json_tampering_rejected_even_if_index_modified(tmp_path):
    fake=tmp_path/"audit.json"
    idx=tmp_path/"index.json"
    copyfile(ORIGINAL,fake)
    copyfile(INDEX,idx)
    fake.write_bytes(fake.read_bytes()+b" ")
    manifest=json.loads(idx.read_text(encoding="utf-8"))
    manifest["first_original_json_sha256"]=sha256(fake.read_bytes()).hexdigest()
    idx.write_text(json.dumps(manifest),encoding="utf-8")
    with pytest.raises(ValueError,match="first metadata result SHA changed"):
        original(fake,idx)


def test_manifest_unverified_source_cannot_be_called_processed_data():
    result,index=original()
    assert index["whole_source_eeg_binary_loaded"] is False
    assert index["source_eeg_content_sha256_checked"] is False
    assert index["all_published_recording_metadata_checked"] is False
    assert result["all_900_eeg_recordings_audited"] is False
    assert result["same_subject_channel_harmonization_verified"] is False
