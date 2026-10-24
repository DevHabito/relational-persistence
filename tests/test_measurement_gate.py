"""Adversarial synthetic fixtures for the RP-E003 measurement gate.

No instrument measurements or physical validation are claimed by these tests.
All timestamps and records below are intentionally manufactured fixtures.
"""

from dataclasses import replace

import pytest

from relational_persistence.measurement_gate import (
    CapacityCalibration,
    ControllerResponse,
    ExternalDisturbance,
    IndependentRecovery,
    MeasurementGateError,
    TrialEvidence,
    validate_evidence,
)


def fixture() -> TrialEvidence:
    return TrialEvidence(
        system_id="synthetic-test-system",
        trial_id="synthetic-test-trial-001",
        clock_domain="common_monotonic_ns",
        clock_resolution_ns=1_000,
        work_unit="request",
        calibration=CapacityCalibration(
            start_ns=1_000_000_000,
            end_ns=3_000_000_000,
            completed_work_units=400,
            saturated_calibration_evidence="calibration-saturated-run-01",
            logger_id="calibration-logger",
        ),
        disturbance=ExternalDisturbance(
            onset_ns=4_000_000_000,
            end_ns=6_000_000_000,
            delivered_excess_work_units=500,
            logger_id="independent-injector",
        ),
        controller=ControllerResponse(
            action_ns=4_250_000_000,
            logger_id="controller-action-logger",
        ),
        recovery=IndependentRecovery(
            observation_end_ns=10_000_000_000,
            recovered_at_ns=8_000_000_000,
            sustained_window_ns=1_000_000_000,
            frozen_criterion_sha256="a" * 64,
            logger_id="independent-recovery-probe",
        ),
    )


def test_structure_gives_typed_non_circular_quantities():
    result = validate_evidence(fixture())
    assert result["capacity_calibration_units_per_second"] == 200
    assert result["external_excess_intensity_units_per_second"] == 250
    assert result["measured_response_latency_seconds"] == 0.25
    assert result["independently_observed_recovery_seconds"] == 2
    assert result["candidate_index_inverse_seconds"] == 3.2
    assert result["measurement_dimensions"]["candidate_index"] == "1/s"
    assert result["causal_identification"] == "NOT_ESTABLISHED"


def test_common_clock_translation_is_invariant():
    original = fixture()
    shift = 123_456_789_000
    shifted = replace(
        original,
        calibration=replace(
            original.calibration,
            start_ns=original.calibration.start_ns + shift,
            end_ns=original.calibration.end_ns + shift,
        ),
        disturbance=replace(
            original.disturbance,
            onset_ns=original.disturbance.onset_ns + shift,
            end_ns=original.disturbance.end_ns + shift,
        ),
        controller=replace(
            original.controller,
            action_ns=original.controller.action_ns + shift,
        ),
        recovery=replace(
            original.recovery,
            observation_end_ns=original.recovery.observation_end_ns + shift,
            recovered_at_ns=original.recovery.recovered_at_ns + shift,
        ),
    )
    assert validate_evidence(shifted) == validate_evidence(original)


def test_consistent_work_unit_rescaling_does_not_create_effect():
    original = fixture()
    transformed = replace(
        original,
        work_unit="half_request",
        calibration=replace(original.calibration, completed_work_units=800),
        disturbance=replace(original.disturbance, delivered_excess_work_units=1000),
    )
    a, b = validate_evidence(original), validate_evidence(transformed)
    assert a["candidate_index_inverse_seconds"] == b["candidate_index_inverse_seconds"]
    assert a["independently_observed_recovery_seconds"] == b["independently_observed_recovery_seconds"]


def test_capacity_estimated_during_intervention_is_rejected():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="calibrated strictly before"):
        validate_evidence(replace(
            data,
            calibration=replace(data.calibration, end_ns=data.disturbance.onset_ns),
        ))


def test_zero_or_subresolution_latency_is_rejected():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="latency"):
        validate_evidence(replace(
            data, controller=replace(data.controller, action_ns=data.disturbance.onset_ns),
        ))
    with pytest.raises(MeasurementGateError, match="latency"):
        validate_evidence(replace(
            data, controller=replace(
                data.controller,
                action_ns=data.disturbance.onset_ns + data.clock_resolution_ns - 1,
            ),
        ))


def test_calibration_work_cannot_be_zero_or_boolean():
    data = fixture()
    for value in [0, True, -1]:
        with pytest.raises(MeasurementGateError, match="completed calibration work"):
            validate_evidence(replace(
                data, calibration=replace(data.calibration, completed_work_units=value),
            ))


def test_external_intensity_cannot_be_zero_or_redefined_post_hoc():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="excess work"):
        validate_evidence(replace(
            data, disturbance=replace(data.disturbance, delivered_excess_work_units=0),
        ))
    with pytest.raises(MeasurementGateError, match="intensity convention"):
        validate_evidence(replace(
            data, disturbance=replace(data.disturbance, intensity_convention="outcome_variance"),
        ))


def test_reusing_evidence_logger_invalidates_independence_gate():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="distinct loggers"):
        validate_evidence(replace(
            data, recovery=replace(data.recovery, logger_id=data.controller.logger_id),
        ))


def test_wall_clock_and_unsynchronized_channels_are_forbidden():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="Cross-clock"):
        validate_evidence(replace(data, clock_domain="wall_clock_utc"))


def test_outcome_criterion_must_be_precommitted():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="SHA-256"):
        validate_evidence(replace(
            data, recovery=replace(data.recovery, frozen_criterion_sha256="just some words"),
        ))


def test_recovery_before_intervention_end_is_rejected():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="after the disturbance ends"):
        validate_evidence(replace(
            data,
            recovery=replace(data.recovery, recovered_at_ns=data.disturbance.end_ns - 1),
        ))


def test_incomplete_sustained_window_is_rejected():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="full window"):
        validate_evidence(replace(
            data,
            recovery=replace(data.recovery, recovered_at_ns=9_500_000_000),
        ))


def test_non_recovery_is_right_censored_not_discarded():
    data = fixture()
    result = validate_evidence(replace(
        data, recovery=replace(data.recovery, recovered_at_ns=None),
    ))
    assert result["recovery_right_censored"] is True
    assert result["independently_observed_recovery_seconds"] is None
    assert result["recovery_lower_bound_seconds"] == 4


def test_missing_saturation_evidence_is_rejected():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="saturation evidence"):
        validate_evidence(replace(
            data,
            calibration=replace(data.calibration, saturated_calibration_evidence=""),
        ))


def test_controller_action_after_monitoring_ends_is_rejected():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="outside"):
        validate_evidence(replace(
            data, controller=replace(data.controller, action_ns=20_000_000_000),
        ))


def test_not_enough_followup_is_rejected_even_when_censored():
    data = fixture()
    with pytest.raises(MeasurementGateError, match="Follow-up"):
        validate_evidence(replace(
            data,
            recovery=replace(
                data.recovery, recovered_at_ns=None,
                observation_end_ns=data.disturbance.end_ns,
            ),
        ))


def test_record_does_not_assert_experimental_confirmation():
    result = validate_evidence(fixture())
    assert "STRUCTURAL_GATE_ONLY" in result["evidence_status"]
    assert result["causal_identification"] == "NOT_ESTABLISHED"
    assert "validated" not in result.get("trial_id", "").lower()
