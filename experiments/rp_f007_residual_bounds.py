"""RP-F007-A01 — exact conditional residual service bounds (SYNTHETIC ONLY).

Frozen protocol: main commit 93d5dc4. A hard, ENFORCED runtime bound
and an advertised/requested walltime are different propositions.
The latter does not justify a maximum residual-service guarantee.
No external HPC observations, statistics or physical law are inferred.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import argparse
import json
from pathlib import Path

from experiments.rp_f006_queue_observability import (
    Job, World, binary_waiting_count, causal_observation,
    construct_world, replay_registered_dispatch, swept_waiting_counts,
)

PROTOCOL = "RP-F007-A01"
PREREG_SHA = "93d5dc4f2c99b663bfede40d515c2dc37bc14e14"
RUNNING_AGE = 30
CAP_BROAD = 500
CAP_NARROW = 90
SNAPSHOTS = (Fraction(-120), Fraction(-60), Fraction(0))


class WitnessInvalid(ValueError):
    """A fixed preregistered world violates a causal/model audit gate."""


def make_world(cap: int, remaining: int) -> World:
    """Build independent registered family; never hide actual R duration."""
    world = construct_world(Fraction(remaining))
    old, running, target = world.jobs
    return replace(
        world,
        jobs=(
            old,
            replace(running, requested_walltime=Fraction(cap)),
            target,
        ),
    )


def directly_count_waiting(world: World, t: Fraction) -> int:
    """Third direct-predicate oracle not calling either F006 counter."""
    return sum(1 for job in world.jobs if job.submit < t <= job.start)


def checked_world(world: World, cap: int, *, enforced: bool = True) -> dict:
    """Check every assumption including public cap and dispatch replay."""
    if len(world.jobs) != 3 or tuple(j.name for j in world.jobs) != (
        "H", "R", "T"
    ):
        raise WitnessInvalid("Unknown/hidden arrival or changed population")
    h, running, target = world.jobs
    if not (
        h.submit == -201 and h.start == -200 and h.end == -190
        and h.requested_walltime == 500
        and running.submit == -31 and running.start == -30
        and running.requested_walltime == cap
        and target.submit == 0 and target.service == 1
        and target.requested_walltime == 500
        and all(job.requested_processors == 1 for job in world.jobs)
        and len({job.queue for job in world.jobs}) == 1
    ):
        raise WitnessInvalid("Known source timing/requests/age/cap changed")
    if any(job.start < job.submit or job.end <= job.start for job in world.jobs):
        raise WitnessInvalid("Invalid start, submission, or service duration")
    if any(first.end > second.start or first.start >= second.start
           for first, second in zip(world.jobs, world.jobs[1:])):
        raise WitnessInvalid("FCFS order or service overlap")
    if running.end <= 0:
        raise WitnessInvalid("Running job must still be active at origin")
    if target.start != running.end:
        raise WitnessInvalid("Target did not start at running completion")
    remaining = running.end
    if remaining != target.wait or remaining <= 0:
        raise WitnessInvalid("Remaining-service/time-to-start identity invalid")
    if enforced and running.service > cap:
        raise WitnessInvalid("Hard cap violated by observed service duration")
    # Do not claim physical policy evidence merely from requested time.
    try:
        replay = replay_registered_dispatch(world)
    except ValueError as exc:
        raise WitnessInvalid("Independent dispatch replay disagrees") from exc
    oracle = swept_waiting_counts(world, SNAPSHOTS)
    for instant in SNAPSHOTS:
        direct = directly_count_waiting(world, instant)
        binary = binary_waiting_count(world, instant)
        if direct != binary or binary != oracle[instant]:
            raise WitnessInvalid("Three independently implemented queue oracles disagree")
    if [oracle[t] for t in SNAPSHOTS] != [0, 0, 0]:
        raise WitnessInvalid("Registered queue snapshot changed")
    return {
        "actual_future_remaining_s": int(remaining),
        "running_runtime_s": int(running.service),
        "target_wait_s": int(target.wait),
        "independent_dispatch_replayed": replay["independent_dispatch_replay_agrees"],
        "three_queue_state_oracles_agreed": True,
    }


def public_observation(world: World, *, enforced: bool) -> dict:
    """The only input available to a bound-valued predictor."""
    data = causal_observation(world)
    data["running_walltime_limit_is_enforced"] = enforced
    data["known_running_age_s"] = str(RUNNING_AGE)
    # Future end, future actual runtime and target wait MUST NOT be features.
    return data


def exact_midpoint(min_wait: int, max_wait: int) -> Fraction:
    return Fraction(min_wait + max_wait, 2)


def analytic_minimax(min_wait: int, max_wait: int) -> Fraction:
    if min_wait < 0 or min_wait > max_wait:
        raise WitnessInvalid("Invalid admissible waiting-time set")
    return Fraction(max_wait - min_wait, 2)


def exhaustive_family(cap: int) -> dict:
    if cap not in (CAP_BROAD, CAP_NARROW):
        raise WitnessInvalid("Cap was not one of two registered interventions")
    maximum = cap - RUNNING_AGE
    observation = None
    witnessed = []
    for remaining in range(1, maximum + 1):
        world = make_world(cap, remaining)
        verified = checked_world(world, cap, enforced=True)
        current = public_observation(world, enforced=True)
        if observation is None:
            observation = current
        if observation != current:
            raise WitnessInvalid("Public pre-origin inputs varied within family")
        witnessed.append(verified["target_wait_s"])
    expected = list(range(1, maximum + 1))
    if witnessed != expected or observation is None:
        raise WitnessInvalid("Residual-wait family not fully enumerated")
    if not observation["running_walltime_limit_is_enforced"]:
        raise WitnessInvalid("Required enforceability flag not public")
    if observation["all_public_requests"][1][1] != str(cap):
        raise WitnessInvalid("Declared running hard cap missing from observation")
    midpoint = exact_midpoint(1, maximum)
    analytic = analytic_minimax(1, maximum)
    exhaustive = max(abs(midpoint - Fraction(wait)) for wait in witnessed)
    if exhaustive != analytic:
        raise WitnessInvalid("Independent finite enumerator disagrees with endpoint formula")
    return {
        "public_hard_cap_seconds": cap,
        "running_elapsed_seconds_at_origin": RUNNING_AGE,
        "public_hard_cap_enforced": True,
        "admissible_world_count": len(witnessed),
        "admissible_wait_min_seconds": 1,
        "admissible_wait_max_seconds": maximum,
        "public_observations_identical_in_family": True,
        "independent_fcfs_dispatch_replay_for_every_world": True,
        "three_queue_state_oracles_for_every_world": True,
        "public_observation": observation,
        "minimax_midpoint_prediction_s": str(midpoint),
        "sharp_minimax_worst_case_error_s": str(exhaustive),
        "independent_analytic_error_bound_s": str(analytic),
        "zero_prediction_worst_case_error_s": str(max(witnessed)),
    }


def adversarial_controls() -> dict:
    bad = make_world(CAP_BROAD, 471)
    try:
        checked_world(bad, CAP_BROAD, enforced=True)
    except WitnessInvalid as exc:
        cap_detected = "Hard cap violated" in str(exc)
    else:
        cap_detected = False
    if not cap_detected:
        raise WitnessInvalid("Overrun unexpectedly accepted as hard-capped")

    # The exact same trace is feasible if the 500s number is *only
    # advertised*, so treating it as a guaranteed cap would be unsound.
    unbounded_request = checked_world(bad, CAP_BROAD, enforced=False)
    if unbounded_request["target_wait_s"] != 471:
        raise WitnessInvalid("Advertised-only control did not exceed putative 470s cap")
    wrong_oracle = (
        bad.named("R").end == bad.named("T").start
        and bad.named("R").end > 0
    )
    if not wrong_oracle:
        raise WitnessInvalid("Illicit future completion oracle control failed")

    baseline = make_world(CAP_BROAD, 1)
    altered = replace(baseline, jobs=baseline.jobs + (
        Job("UNREGISTERED", Fraction(-1), Fraction(-1), Fraction(1)),))
    try:
        checked_world(altered, CAP_BROAD)
    except WitnessInvalid as exc:
        extra_rejected = "hidden arrival" in str(exc)
    else:
        extra_rejected = False
    altered_dispatch = replace(
        baseline, jobs=(
            baseline.named("H"),
            replace(baseline.named("R"), start=Fraction(-29)),
            baseline.named("T"),
        )
    )
    try:
        checked_world(altered_dispatch, CAP_BROAD)
    except WitnessInvalid:
        dispatch_rejected = True
    else:
        dispatch_rejected = False
    if not extra_rejected or not dispatch_rejected:
        raise WitnessInvalid("Unknown arrivals or dispatch mutation not rejected")

    return {
        "hard_cap_overrun_rejected": cap_detected,
        "advertised_only_500_not_a_guarantee": (
            unbounded_request["target_wait_s"] > CAP_BROAD - RUNNING_AGE
        ),
        "future_running_completion_oracle_is_not_public": wrong_oracle,
        "unregistered_future_arrival_rejected": extra_rejected,
        "changed_dispatch_rejected": dispatch_rejected,
    }


def audit() -> dict:
    broad = exhaustive_family(CAP_BROAD)
    narrow = exhaustive_family(CAP_NARROW)
    controls = adversarial_controls()
    large_err = Fraction(broad["sharp_minimax_worst_case_error_s"])
    small_err = Fraction(narrow["sharp_minimax_worst_case_error_s"])
    if (large_err != Fraction(469, 2) or small_err != Fraction(59, 2)
            or large_err - small_err != 205
            or small_err / large_err != Fraction(59, 469)
            or broad["minimax_midpoint_prediction_s"] != "471/2"
            or narrow["minimax_midpoint_prediction_s"] != "61/2"
            or not all(controls.values())):
        raise WitnessInvalid("Original preregistered numerical gates not satisfied")
    return {
        "protocol": PROTOCOL,
        "frozen_preregistration_commit": PREREG_SHA,
        "decision": "BOUNDED_STATE_MINIMAX_VERIFIED",
        "source": "SYNTHETIC_ONLY",
        "broad_family": broad,
        "narrow_family": narrow,
        "registered_controls": controls,
        "minimax_error_decrease_s": str(large_err - small_err),
        "narrow_over_broad_minimax_error_ratio": str(small_err / large_err),
        "public_cap_change_means_public_observation_changes": True,
        "no_external_prediction_data_used": True,
        "no_original_rp_e010_or_rp_e011_result_changed": True,
        "novel_queuing_theorem_claimed": False,
        "physical_law_or_scalar_C_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Cannot overwrite original RP-F007-A01 report")
    try:
        result = audit()
    except (WitnessInvalid, ValueError, AssertionError) as exc:
        result = {
            "protocol": PROTOCOL,
            "frozen_preregistration_commit": PREREG_SHA,
            "decision": "BOUND_WITNESS_INVALID",
            "source": "SYNTHETIC_ONLY",
            "error": f"{type(exc).__name__}: {str(exc)[:400]}",
            "novel_queuing_theorem_claimed": False,
            "physical_law_or_scalar_C_claimed": False,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "protocol": PROTOCOL,
        "decision": result["decision"],
        "broad_error": (result.get("broad_family") or {}).get(
            "sharp_minimax_worst_case_error_s"),
        "narrow_error": (result.get("narrow_family") or {}).get(
            "sharp_minimax_worst_case_error_s"),
    }, sort_keys=True))
    if result["decision"] != "BOUNDED_STATE_MINIMAX_VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
