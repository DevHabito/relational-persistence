"""RP-E003 independent measurement evidence gate.

This is a *schema validator*, NOT a detector of causal independence.
Log identifiers and timestamps can be fabricated; hardware calibration,
instrument trust, measurement error and external recovery labels require
separate audits before scientific evaluation.

A candidate result from this module must never be reported as validation
of a physical persistence law or as a preregistered prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


NANOSECONDS_PER_SECOND = 1_000_000_000
REQUIRED_INTENSITY = "excess_work_rate"


class MeasurementGateError(ValueError):
    """An unsupported or incomplete physical-measurement assertion."""


@dataclass(frozen=True)
class CapacityCalibration:
    start_ns: int
    end_ns: int
    completed_work_units: int
    saturated_calibration_evidence: str
    logger_id: str


@dataclass(frozen=True)
class ExternalDisturbance:
    onset_ns: int
    end_ns: int
    delivered_excess_work_units: int
    logger_id: str
    intensity_convention: str = REQUIRED_INTENSITY


@dataclass(frozen=True)
class ControllerResponse:
    action_ns: int
    logger_id: str


@dataclass(frozen=True)
class IndependentRecovery:
    """The monitor's confirmation timestamp, not a model-derived estimate."""

    observation_end_ns: int
    recovered_at_ns: int | None
    sustained_window_ns: int
    frozen_criterion_sha256: str
    logger_id: str


@dataclass(frozen=True)
class TrialEvidence:
    system_id: str
    trial_id: str
    clock_domain: str
    clock_resolution_ns: int
    work_unit: str
    calibration: CapacityCalibration
    disturbance: ExternalDisturbance
    controller: ControllerResponse
    recovery: IndependentRecovery


def _positive_integer(value: object, description: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise MeasurementGateError(f"{description} must be a positive integer")
    return value


def _strict_int(value: object, description: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MeasurementGateError(f"{description} must be an integer nanosecond timestamp")
    return value


def _nonempty(value: str, description: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MeasurementGateError(f"{description} must be nonempty")


def validate_evidence(evidence: TrialEvidence) -> dict:
    """Validate structural independence and typed measurement dimensions.

    An admissible *structure* does not prove instrument calibration,
    treatment exogeneity, clock accuracy or causal identifiability.
    """
    for key in ("system_id", "trial_id", "clock_domain", "work_unit"):
        _nonempty(getattr(evidence, key), key)
    if evidence.clock_domain != "common_monotonic_ns":
        raise MeasurementGateError(
            "Cross-clock timestamps need independent synchronization evidence; unsupported"
        )
    resolution = _positive_integer(evidence.clock_resolution_ns, "clock_resolution_ns")

    calibration = evidence.calibration
    disturbance = evidence.disturbance
    controller = evidence.controller
    recovery = evidence.recovery

    logs = (
        calibration.logger_id,
        disturbance.logger_id,
        controller.logger_id,
        recovery.logger_id,
    )
    for logger in logs:
        _nonempty(logger, "independent_logger_id")
    if len(set(logs)) != 4:
        raise MeasurementGateError("All four evidence streams require distinct loggers")

    _nonempty(calibration.saturated_calibration_evidence, "saturation evidence reference")
    _nonempty(recovery.frozen_criterion_sha256, "frozen recovery criterion reference")
    if len(recovery.frozen_criterion_sha256) != 64 or not all(
        ch in "0123456789abcdef" for ch in recovery.frozen_criterion_sha256
    ):
        raise MeasurementGateError("Recovery criterion reference must be a lowercase SHA-256")

    for name, value in (
        ("calibration start", calibration.start_ns),
        ("calibration end", calibration.end_ns),
        ("disturbance onset", disturbance.onset_ns),
        ("disturbance end", disturbance.end_ns),
        ("controller action", controller.action_ns),
        ("recovery observation end", recovery.observation_end_ns),
    ):
        _strict_int(value, name)

    calibration_duration_ns = calibration.end_ns - calibration.start_ns
    disturbance_duration_ns = disturbance.end_ns - disturbance.onset_ns
    latency_ns = controller.action_ns - disturbance.onset_ns
    if calibration_duration_ns < resolution:
        raise MeasurementGateError("Capacity calibration duration is below clock resolution")
    if calibration.end_ns >= disturbance.onset_ns:
        raise MeasurementGateError("Capacity must be calibrated strictly before the trial")
    if disturbance_duration_ns < resolution:
        raise MeasurementGateError("The intervention duration is below clock resolution")
    if latency_ns < resolution:
        raise MeasurementGateError("Actual controller action latency must exceed clock resolution")
    if controller.action_ns > recovery.observation_end_ns:
        raise MeasurementGateError("Response action lies outside the recorded observation window")
    if recovery.observation_end_ns <= disturbance.end_ns:
        raise MeasurementGateError("Follow-up must extend beyond intervention end")
    _positive_integer(calibration.completed_work_units, "completed calibration work")
    _positive_integer(disturbance.delivered_excess_work_units, "externally delivered excess work")
    if disturbance.intensity_convention != REQUIRED_INTENSITY:
        raise MeasurementGateError("Unregistered disturbance intensity convention")
    dwell_ns = _positive_integer(recovery.sustained_window_ns, "sustained recovery window")
    if dwell_ns < resolution:
        raise MeasurementGateError("Sustained recovery window is below clock resolution")

    censored = recovery.recovered_at_ns is None
    if not censored:
        stamp = _strict_int(recovery.recovered_at_ns, "recovery timestamp")
        if stamp < disturbance.end_ns:
            raise MeasurementGateError("Recovery must be measured after the disturbance ends")
        if stamp + dwell_ns > recovery.observation_end_ns:
            raise MeasurementGateError("Sustained recovery was not observed for its full window")

    b_units_per_s = calibration.completed_work_units * NANOSECONDS_PER_SECOND / calibration_duration_ns
    i_units_per_s = disturbance.delivered_excess_work_units * NANOSECONDS_PER_SECOND / disturbance_duration_ns
    tau_seconds = latency_ns / NANOSECONDS_PER_SECOND
    recovery_seconds = (
        None if censored else (recovery.recovered_at_ns - disturbance.end_ns) / NANOSECONDS_PER_SECOND
    )
    lower_bound_seconds = (
        (recovery.observation_end_ns - disturbance.end_ns) / NANOSECONDS_PER_SECOND
        if censored else None
    )
    return {
        "schema": "RP-E003-S01",
        "trial_id": evidence.trial_id,
        "system_id": evidence.system_id,
        "capacity_calibration_units_per_second": b_units_per_s,
        "external_excess_intensity_units_per_second": i_units_per_s,
        "measured_response_latency_seconds": tau_seconds,
        "independently_observed_recovery_seconds": recovery_seconds,
        "recovery_right_censored": censored,
        "recovery_lower_bound_seconds": lower_bound_seconds,
        "candidate_index_inverse_seconds": b_units_per_s / (i_units_per_s * tau_seconds),
        "measurement_dimensions": {
            "B": evidence.work_unit + "/s",
            "I": evidence.work_unit + "/s",
            "tau": "s",
            "candidate_index": "1/s",
            "Y": "s",
        },
        "evidence_status": "STRUCTURAL_GATE_ONLY_NOT_EMPIRICALLY_VALIDATED",
        "causal_identification": "NOT_ESTABLISHED",
    }
