"""Replay the original P02 observed health traces from permanent byte-preserved logs.

A passing test certifies consistency of recorded bytes with a frozen
software algorithm; it cannot independently calibrate physical instruments
or validate a cross-system persistence law.
"""

import hashlib
import json
from pathlib import Path

import pytest

from experiments.rp_e004_p02 import (
    RECOVERY_DWELL_NS, GAP_LIMIT_NS, audit_trial, read_jsonlines, replay_monitor,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E004-P02-first-run"


def summary():
    return json.loads((ARCHIVE / "summary.json").read_text(encoding="utf-8"))


def test_first_run_protocol_hash_precedes_measurements():
    meta = summary()
    assert meta["protocol"] == "RP-E004-P02"
    assert meta["git_sha"] == "48de8c3e56c2a9ac99331b226b925df8b4099ce9"
    assert meta["decision"] == "PASS_AUDITABLE_INSTRUMENTATION"
    assert meta["physical_law_test"] == "NOT_PERFORMED"
    prereg = ROOT / "docs/preregistration/RP-E004-P02.md"
    assert hashlib.sha256(prereg.read_bytes()).hexdigest() == meta["preregistration_sha256"]


def test_original_24_role_and_trace_byte_hashes_are_preserved():
    for trial in summary()["trials"]:
        location = ARCHIVE / trial["trial_id"]
        assert len(trial["source_log_sha256"]) == 6
        for role, expected in trial["source_log_sha256"].items():
            suffix = ".jsonl" if role in ("monitor-samples", "service-actions") else ".json"
            record = location / f"{role}{suffix}"
            assert record.is_file()
            assert hashlib.sha256(record.read_bytes()).hexdigest() == expected


def test_independent_trace_replay_agrees_with_all_original_trial_decisions():
    meta = summary()
    for observed in meta["trials"]:
        trial_id = observed["trial_id"]
        archived = audit_trial(
            ARCHIVE / trial_id,
            trial_id,
            meta["preregistration_sha256"],
            meta["monotonic_resolution_ns"],
        )
        assert archived["verdict"] == observed["verdict"]
        assert archived["health_replay"] == observed["health_replay"]
        assert archived["calibration"] == observed["calibration"]
        assert archived["source_log_sha256"] == observed["source_log_sha256"]
        assert archived.get("measurement") == observed.get("measurement")
        assert archived.get("action_timing_ns") == observed.get("action_timing_ns")


def test_first_run_recovery_does_not_depend_on_controller_fields():
    trial = ARCHIVE / "positive-controlled-01"
    source = json.loads((trial / "injector.json").read_text())
    samples = read_jsonlines(trial / "monitor-samples.jsonl")
    result = replay_monitor(
        samples, source["end_ns"], RECOVERY_DWELL_NS, GAP_LIMIT_NS
    )
    assert result["recovered_at_ns"] is not None
    assert result["maximum_post_end_gap_ns"] <= GAP_LIMIT_NS


def test_tampered_missing_sample_may_not_be_silently_interpolated():
    trial = ARCHIVE / "positive-controlled-01"
    source = json.loads((trial / "injector.json").read_text())
    samples = read_jsonlines(trial / "monitor-samples.jsonl")
    last = [x for x in samples if x["observed_ns"] >= source["end_ns"]]
    corrupt = samples[:]
    corrupt = [x for x in corrupt if x not in last[7:13]]
    with pytest.raises(ValueError, match="gap"):
        replay_monitor(corrupt, source["end_ns"], RECOVERY_DWELL_NS, GAP_LIMIT_NS)


def test_sham_and_disabled_controller_do_not_gain_an_undefined_index():
    rows = {row["trial_id"]: row for row in summary()["trials"]}
    for name in ("sham-01", "positive-disabled-01"):
        row = rows[name]
        assert row["candidate_index_inverse_seconds"] is None
        assert row["health_replay"]["after_end_samples"] > 0
    assert rows["sham-01"]["delivered_units"] == 0
    assert rows["positive-disabled-01"]["delivered_units"] == 120


def test_short_censored_followup_is_not_accepted(tmp_path):
    import shutil
    original = ARCHIVE / "positive-disabled-01"
    copied = tmp_path / "positive-disabled-01"
    shutil.copytree(original, copied)
    injector = json.loads((copied / "injector.json").read_text())
    samples_path = copied / "monitor-samples.jsonl"
    samples = read_jsonlines(samples_path)
    for sample in samples:
        if sample["observed_ns"] >= injector["end_ns"]:
            sample["queued"] = 1
    samples_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\\n" for row in samples),
        encoding="utf-8",
    )
    monitor_path = copied / "monitor.json"
    monitor = json.loads(monitor_path.read_text())
    monitor["recovered_at_ns"] = None
    monitor["confirmed_at_ns"] = None
    monitor_path.write_text(json.dumps(monitor), encoding="utf-8")
    with pytest.raises(ValueError, match="Censored trial terminated"):
        audit_trial(
            copied, "positive-disabled-01",
            summary()["preregistration_sha256"],
            summary()["monotonic_resolution_ns"],
        )
