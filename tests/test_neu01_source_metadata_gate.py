"""NEU-01-G00 tests: five original metadata summaries, no EEG amplitudes."""
from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from experiments import neu01_source_metadata_gate as gate


def source_data():
    return json.loads(gate.MANIFEST.read_text(encoding="utf-8"))


def test_original_five_tasks_have_one_sidecar_count_disagreement():
    summary = gate.evaluate(source_data())
    assert summary["decision"] == "SOURCE_SIDECAR_DISAGREEMENT_PRESENT"
    assert summary["five_task_metadata_pairs"] == 5
    assert summary["number_of_disagreeing_task_sidecars"] == 1
    assert summary["sidecar_channel_count_disagreements"][0]["task"] == "eyesclosed"
    assert summary["sidecar_channel_count_disagreements"][0]["declared_eeg_channels"] == 64
    assert summary["sidecar_channel_count_disagreements"][0]["companion_tsv_rows"] == 61
    assert summary["raw_eeg_binary_values_downloaded"] is False
    assert summary["all_900_eeg_recordings_audited"] is False
    assert summary["lz_complexity_computed_on_original_eeg"] is False
    assert summary["subject_diagnosis_or_self_continuity_inferred"] is False


def test_other_four_sidecars_are_consistent_only_as_metadata():
    data = source_data()
    items = {x["task"]:x for x in data["records"]}
    for name in ("eyesopen", "mathematic", "memory", "music"):
        assert items[name]["declared_eeg_channels"] == 61
        assert items[name]["channel_rows_in_companion_tsv"] == 61
        assert items[name]["sampling_frequency_hz"] == 500
        assert items[name]["declared_duration_seconds"] == 300
        assert items[name]["eeg_reference"] == "FCz"


def test_counterfactual_corrected_source_metadata_would_be_consistent():
    data = source_data()
    first = next(x for x in data["records"] if x["task"] == "eyesclosed")
    # This is ONLY a synthetic test case, not a claim the source has changed.
    first["declared_eeg_channels"] = 61
    result = gate.evaluate(data)
    assert result["decision"] == "FIVE_SIDECARS_SELF_CONSISTENT"
    assert result["number_of_disagreeing_task_sidecars"] == 0
    assert result["same_subject_channel_harmonization_verified"] is False


@pytest.mark.parametrize("modifier,expected",[
    (lambda d: d["records"].pop(), "EXACT_FIVE_TASK_SOURCE_SET_REQUIRED"),
    (lambda d: d["records"].append(deepcopy(d["records"][0])), "EXACT_FIVE_TASK_SOURCE_SET_REQUIRED"),
    (lambda d: d["records"][0].update(task="eyesopen"), "UNEXPECTED_EEG_SIDECAR_PATH"),
    (lambda d: d["records"][0].update(sampling_frequency_hz=0), "MALFORMED_NUMERIC_SIDECAR_FIELD"),
    (lambda d: d["records"][0].update(sampling_frequency_hz=40), "IMPOSSIBLE_OR_UNREGISTERED_SAMPLE_RATE"),
    (lambda d: d["records"][0].update(sampling_frequency_hz=1000), "SOURCE_SAMPLE_RATE_DIFFERS_FROM_PUBLISHER"),
    (lambda d: d["records"][0].update(declared_duration_seconds=301), "SOURCE_DURATION_DIFFERS_FROM_PUBLISHER"),
    (lambda d: d["records"][0].update(eeg_reference="unknown"), "SOURCE_REFERENCE_DIFFERENT"),
    (lambda d: d["records"][0].update(eeg_sidecar_git_blob_sha="0"*39), "SOURCE_BLOB_HASH_MISSING"),
    (lambda d: d["records"][0].update(eeg_sidecar_path="sub-99/other/eeg.json"), "UNEXPECTED_EEG_SIDECAR_PATH"),
    (lambda d: d.update(source_git_commit="0"*40), "FROZEN_SOURCE_OR_CLAIM_CHANGED_source_git_commit"),
    (lambda d: d.update(raw_eeg_bodies_downloaded_or_verified=True), "FROZEN_SOURCE_OR_CLAIM_CHANGED_raw_eeg_bodies_downloaded_or_verified"),
    (lambda d: d.update(original_eeg_signal_lzc_evaluated=True), "FROZEN_SOURCE_OR_CLAIM_CHANGED_original_eeg_signal_lzc_evaluated"),
    (lambda d: d.update(full_catalog_recording_count_independently_verified=True), "FROZEN_SOURCE_OR_CLAIM_CHANGED_full_catalog_recording_count_independently_verified"),
])
def test_metadata_corruption_or_overclaim_rejected(modifier,expected):
    data=source_data()
    modifier(data)
    with pytest.raises(gate.MetadataGateError,match=expected):
        gate.evaluate(data)


def test_cli_output_is_identical_to_verified_aggregated_summary():
    p = subprocess.run(
        [sys.executable, "-m", "experiments.neu01_source_metadata_gate"],
        text=True, capture_output=True, check=False, timeout=30,
    )
    assert p.returncode==0,p.stderr
    expected=gate.evaluate(source_data())
    assert json.loads(p.stdout)==expected
    assert json.loads(gate.OUTPUT.read_text(encoding="utf-8"))==expected


def test_python_optimized_mode_cannot_bypass_source_integrity_checks():
    expr=(
        "from experiments import neu01_source_metadata_gate as g;"
        "import json;data=json.loads(g.MANIFEST.read_text());"
        "data['source_git_commit']='0'*40;"
        "\ntry:\n g.evaluate(data);print('BROKEN')"
        "\nexcept g.MetadataGateError:\n print('GUARD_ACTIVE')"
    )
    p=subprocess.run([sys.executable,"-O","-c",expr],
                     text=True,capture_output=True,timeout=30,check=False)
    assert p.returncode==0,p.stderr
    assert p.stdout.strip()=="GUARD_ACTIVE"
