"""Audit the first RP-E004-P01 run without refitting or rerunning it.

These are real monotonic-clock measurements from one controlled hosted
software system. They do not validate a physical persistence law.
"""

import hashlib
import json
import math
from pathlib import Path

from relational_persistence.measurement_gate import (
    CapacityCalibration,
    ControllerResponse,
    ExternalDisturbance,
    IndependentRecovery,
    TrialEvidence,
    validate_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E004-P01-first-run"


def read_json(name):
    return json.loads((ARCHIVE / name).read_text(encoding="utf-8"))


def test_immutable_registration_checksum():
    index = read_json("index.json")
    prereg = ROOT / "docs/preregistration/RP-E004-P01.md"
    assert hashlib.sha256(prereg.read_bytes()).hexdigest() == index["registration_sha256"]
    assert index["protocol"] == "RP-E004-P01"
    assert index["decision"] == "PROCEED_TO_SEPARATE_STUDY_DESIGN"
    assert index["physical_law_test"] == "NOT_PERFORMED"
    assert index["causal_identification"] == "NOT_ESTABLISHED"


def test_all_twelve_original_log_byte_hashes_match():
    index = read_json("index.json")
    for trial, expected in index["source_event_log_hashes"].items():
        for role, sha in expected.items():
            path = ARCHIVE / trial / f"{role}.json"
            assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, (trial, role)


def test_recorded_measures_reproduce_independent_gate():
    index = read_json("index.json")
    for row in index["positive_results"]:
        trial = row["trial_id"]
        calibration = read_json(f"{trial}/calibration.json")
        injection = read_json(f"{trial}/injector.json")
        controller = read_json(f"{trial}/controller.json")
        monitor = read_json(f"{trial}/monitor.json")
        evidence = TrialEvidence(
            system_id="github-actions-single-runner-queue",
            trial_id=trial,
            clock_domain="common_monotonic_ns",
            clock_resolution_ns=index["monotonic_resolution_ns"],
            work_unit="HTTP_work_unit",
            calibration=CapacityCalibration(
                calibration["start_ns"], calibration["end_ns"],
                calibration["completed_work_units"],
                calibration["saturation_evidence"], calibration["logger_id"],
            ),
            disturbance=ExternalDisturbance(
                injection["onset_ns"], injection["end_ns"],
                injection["successfully_delivered_work_units"],
                injection["logger_id"],
            ),
            controller=ControllerResponse(
                controller["action_ns"], controller["logger_id"],
            ),
            recovery=IndependentRecovery(
                monitor["observation_end_ns"], monitor["recovered_at_ns"],
                monitor["sustained_window_ns"], index["registration_sha256"],
                monitor["logger_id"],
            ),
        )
        measured = validate_evidence(evidence)
        for expected, actual in (
            ("B_work_units_per_second", "capacity_calibration_units_per_second"),
            ("I_work_units_per_second", "external_excess_intensity_units_per_second"),
            ("tau_seconds", "measured_response_latency_seconds"),
            ("Y_seconds", "independently_observed_recovery_seconds"),
            ("candidate_index_inverse_seconds", "candidate_index_inverse_seconds"),
        ):
            assert math.isclose(row[expected], measured[actual], rel_tol=1e-12)
        assert measured["causal_identification"] == "NOT_ESTABLISHED"
        assert 0 < measured["measured_response_latency_seconds"]


def test_sham_is_not_assigned_a_fabricated_index():
    index = read_json("index.json")
    row = index["sham"]
    injector = read_json("sham-01/injector.json")
    controller = read_json("sham-01/controller.json")
    assert injector["successfully_delivered_work_units"] == 0
    assert controller["action_ns"] is None
    assert row["candidate_index_inverse_seconds"] is None
    assert row["schema_verdict"] == "SHAM_UNDEFINED_INDEX"
