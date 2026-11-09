"""NEU-01-G00: bounded, provenance-pinned EEG BIDS *metadata* audit.

This code validates a previously inspected five-sidecar summary. It neither
downloads EEG recordings nor computes Lempel–Ziv complexity, clinical
biomarkers, or neural/thermodynamic interpretations. Raw file sidecars must be
checked against the independent original BrainVision signal in a later gate.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

PROTOCOL_SHA = "b0267de1c20362dc38bda0ef32d09f3d97f240a9"
DATASET_SHA = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
MANIFEST = Path("docs/research/NEU-01-G00-FIVE-SIDECAR-MANIFEST.json")
OUTPUT = Path("docs/results/NEU-01-G00-first-run/audit.json")
TASKS = ("eyesclosed", "eyesopen", "mathematic", "memory", "music")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
PATH_PREFIX = "sub-01/ses-session1/eeg/"
CHECK_FIELDS = ("declared_eeg_channels", "channel_rows_in_companion_tsv",
                "sampling_frequency_hz", "declared_duration_seconds")


class MetadataGateError(ValueError):
    pass


def validate_manifest(data: dict) -> None:
    if not isinstance(data, dict):
        raise MetadataGateError("MANIFEST_NOT_OBJECT")
    expected = {
        "study": "NEU-01-G00",
        "source_kind": "SOURCE_METADATA_ONLY",
        "protocol_only_commit": PROTOCOL_SHA,
        "source_repository": "OpenNeuroDatasets/ds004148",
        "source_git_commit": DATASET_SHA,
        "dataset_doi": "10.18112/openneuro.ds004148.v1.0.0",
        "original_dataset_publication_doi": "10.1038/s41597-022-01607-9",
        "nemar_catalog_doi": "10.82901/nemar.on004148",
        "published_cohort_participants": 60,
        "published_session_count": 3,
        "published_task_count": 5,
        "catalog_recordings_reported": 900,
        "full_catalog_recording_count_independently_verified": False,
        "raw_eeg_bodies_downloaded_or_verified": False,
        "original_eeg_signal_lzc_evaluated": False,
    }
    for field, value in expected.items():
        if data.get(field) != value or type(data.get(field)) is not type(value):
            raise MetadataGateError("FROZEN_SOURCE_OR_CLAIM_CHANGED_" + field)
    rows = data.get("records")
    if not isinstance(rows, list) or len(rows) != len(TASKS):
        raise MetadataGateError("EXACT_FIVE_TASK_SOURCE_SET_REQUIRED")
    seen = set()
    for item in rows:
        if not isinstance(item, dict) or item.get("task") not in TASKS:
            raise MetadataGateError("UNREGISTERED_TASK")
        task = item["task"]
        if task in seen:
            raise MetadataGateError("DUPLICATED_TASK")
        seen.add(task)
        stem = PATH_PREFIX + f"sub-01_ses-session1_task-{task}"
        if item.get("eeg_sidecar_path") != stem + "_eeg.json":
            raise MetadataGateError("UNEXPECTED_EEG_SIDECAR_PATH")
        if item.get("channels_tsv_path") != stem + "_channels.tsv":
            raise MetadataGateError("UNEXPECTED_COMPANION_CHANNELS_PATH")
        for field in ("eeg_sidecar_git_blob_sha", "channels_tsv_git_blob_sha"):
            sha = item.get(field)
            if not isinstance(sha, str) or HEX40.fullmatch(sha) is None:
                raise MetadataGateError("SOURCE_BLOB_HASH_MISSING")
        for field in CHECK_FIELDS:
            val = item.get(field)
            if type(val) is not int or val <= 0:
                raise MetadataGateError("MALFORMED_NUMERIC_SIDECAR_FIELD")
        if not 100 <= item["sampling_frequency_hz"] <= 20000:
            raise MetadataGateError("IMPOSSIBLE_OR_UNREGISTERED_SAMPLE_RATE")
        if item["declared_duration_seconds"] != 300:
            raise MetadataGateError("SOURCE_DURATION_DIFFERS_FROM_PUBLISHER")
        if item["sampling_frequency_hz"] != 500:
            raise MetadataGateError("SOURCE_SAMPLE_RATE_DIFFERS_FROM_PUBLISHER")
        if item.get("eeg_reference") != "FCz":
            raise MetadataGateError("SOURCE_REFERENCE_DIFFERENT")
    if seen != set(TASKS):
        raise MetadataGateError("EXACT_FIVE_TASK_SOURCE_SET_REQUIRED")


def evaluate(data: dict) -> dict:
    validate_manifest(data)
    discrepancies = []
    for item in data["records"]:
        if item["declared_eeg_channels"] != item["channel_rows_in_companion_tsv"]:
            discrepancies.append({
                "task": item["task"],
                "declared_eeg_channels": item["declared_eeg_channels"],
                "companion_tsv_rows": item["channel_rows_in_companion_tsv"],
                "source_eeg_sidecar_blob_sha": item["eeg_sidecar_git_blob_sha"],
                "source_channels_tsv_blob_sha": item["channels_tsv_git_blob_sha"],
            })
    return {
        "study": "NEU-01-G00",
        "protocol_only_commit": PROTOCOL_SHA,
        "source_git_commit": DATASET_SHA,
        "source_scope": "five BIDS JSON/TSV sidecar pairs from sub-01 session1",
        "five_task_metadata_pairs": len(data["records"]),
        "sampling_rate_metadata_hz": 500,
        "recording_duration_metadata_seconds_each": 300,
        "sidecar_channel_count_disagreements": discrepancies,
        "number_of_disagreeing_task_sidecars": len(discrepancies),
        "decision": ("SOURCE_SIDECAR_DISAGREEMENT_PRESENT" if discrepancies
                     else "FIVE_SIDECARS_SELF_CONSISTENT"),
        "raw_eeg_binary_values_downloaded": False,
        "all_900_eeg_recordings_audited": False,
        "lz_complexity_computed_on_original_eeg": False,
        "subject_diagnosis_or_self_continuity_inferred": False,
        "same_subject_channel_harmonization_verified": False,
        "physical_entropy_or_mental_health_claimed": False,
    }


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = evaluate(data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
