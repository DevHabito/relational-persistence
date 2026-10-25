"""RP-F006-A01: exact finite FCFS-compatible partial-state obstruction.

Preregistered at 3670d7d9 before this implementation. Synthetic ONLY.

The two schedules preserve identical observed events up through submission
at t=0, including the running job's age and publicly requested walltime.
Unknown *actual* remaining service differentiates future outcomes. This
is a basic queueing-theory limitation, not a new physical or empirical law.

FCFS here means no service overlap and no passing in submission order.
The preregistered one-second submit-to-start dispatch delays of H and R
are explicit recorded delays, not a claim of work-conserving service
during all idle instants. From the target submission onward, service
is immediately dispatched as soon as the prior job finishes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from hashlib import sha256
import argparse
import json
from pathlib import Path

PROTOCOL = "RP-F006-A01"
ORIGIN = Fraction(0)
PREVIOUS = Fraction(-120)
LATEST = Fraction(-60)
HISTORY_START = Fraction(-3600)
HISTORY_END = LATEST
RATE_SECONDS = Fraction(3540)
WALLTIME_LIMIT = Fraction(500)
REGISTERED_SHORT_END = Fraction(1)
REGISTERED_LONG_END = Fraction(100)


@dataclass(frozen=True, slots=True)
class Job:
    name: str
    submit: Fraction
    start: Fraction
    end: Fraction
    requested_walltime: Fraction = WALLTIME_LIMIT
    requested_processors: int = 1
    queue: str = "synthetic-single-queue"

    @property
    def wait(self) -> Fraction:
        return self.start - self.submit

    @property
    def service(self) -> Fraction:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class World:
    jobs: tuple[Job, ...]

    def named(self, name: str) -> Job:
        return next(job for job in self.jobs if job.name == name)


def construct_world(running_completion: Fraction,
                    target_service: Fraction = Fraction(1)) -> World:
    """Exact registered worlds; parameters enable negative controls only."""
    h = Job("H", Fraction(-201), Fraction(-200), Fraction(-190))
    running = Job("R", Fraction(-31), Fraction(-30), running_completion)
    target = Job(
        "T", ORIGIN, running_completion, running_completion + target_service
    )
    return World((h, running, target))


def validate_fcfs_compatible(world: World) -> dict:
    """Independent schedule feasibility: FCFS order and no service overlap.

    Nonpreemptive FCFS does not by itself assert that all idle servers
    dispatch instantaneously. That additional work-conservation axiom
    would reject the one-second registered H/R dispatch delays.
    """
    if tuple(job.name for job in world.jobs) != ("H", "R", "T"):
        raise ValueError("The registered job ordering or identities changed")
    if any(job.submit > job.start or job.start >= job.end
           for job in world.jobs):
        raise ValueError("Invalid submission, start, or completion ordering")
    if any(job.requested_walltime != WALLTIME_LIMIT
           or job.service > job.requested_walltime
           or job.requested_processors != 1
           or job.queue != world.jobs[0].queue
           for job in world.jobs):
        raise ValueError("Public request or actual service exceeded fixed contract")
    if any(first.submit >= second.submit or first.start >= second.start
           or first.end > second.start
           for first, second in zip(world.jobs, world.jobs[1:])):
        raise ValueError("Nonpreemptive FCFS order/overlap failure")
    if world.named("T").start != world.named("R").end:
        raise ValueError("Target did not start immediately when server was released")
    if (world.named("H").submit != -201 or world.named("H").start != -200
            or world.named("H").end != -190
            or world.named("R").submit != -31
            or world.named("R").start != -30
            or world.named("T").submit != 0
            or world.named("T").service != 1):
        raise ValueError("Frozen witness's nonvarying times changed")
    return {
        "fcfs_arrival_and_start_order": True,
        "no_overlapping_service": True,
        "target_starts_at_running_completion": True,
        "work_conservation_before_origin_asserted": False,
    }


def visible_event_history(world: World) -> tuple[tuple[str, str, str], ...]:
    """All completed events before t=0; the current target submits at 0.

    A start event reveals wait for that already-started job, but a future
    completion is deliberately not visible. Runtime is never an input.
    """
    items = []
    for job in world.jobs:
        for event_name, stamp in (
            ("submit", job.submit), ("start", job.start), ("end", job.end)
        ):
            if stamp < ORIGIN:
                items.append((str(stamp), event_name, job.name))
    return tuple(sorted(items, key=lambda row: (Fraction(row[0]), row[1], row[2])))


def public_requests(world: World) -> tuple[tuple[str, str, int, str], ...]:
    return tuple((
        job.name, str(job.requested_walltime),
        job.requested_processors, job.queue
    ) for job in world.jobs)


def binary_waiting_count(world: World, instant: Fraction) -> int:
    """Independent sorted-arrivals minus sorted-starts oracle."""
    from bisect import bisect_left
    submits = sorted(job.submit for job in world.jobs)
    starts = sorted(job.start for job in world.jobs)
    return bisect_left(submits, instant) - bisect_left(starts, instant)


def swept_waiting_counts(world: World,
                         instants: tuple[Fraction, ...]) -> dict[Fraction, int]:
    """Separate event sweep, never calls the binary method or its arrays."""
    events = []
    for job in world.jobs:
        events.append((job.submit, +1))
        events.append((job.start, -1))
    events.sort()
    result: dict[Fraction, int] = {}
    active = index = 0
    for instant in sorted(set(instants)):
        while index < len(events) and events[index][0] < instant:
            active += events[index][1]
            index += 1
        if active < 0:
            raise ValueError("Negative queued count in independent sweep")
        result[instant] = active
    return result


def causal_observation(world: World) -> dict:
    """Same content for both worlds; only already-started waits are read."""
    instants = (PREVIOUS, LATEST, ORIGIN)
    sweep = swept_waiting_counts(world, instants)
    binary = {stamp: binary_waiting_count(world, stamp) for stamp in instants}
    if sweep != binary:
        raise ValueError("Binary count disagrees with independent event sweep")
    previously_started = tuple(
        job for job in world.jobs
        if HISTORY_START <= job.start < HISTORY_END
    )
    if not previously_started:
        raise ValueError("No past started-job observation in witness")
    if len(previously_started) != 1 or previously_started[0].name != "H":
        raise ValueError("Known historical started cohort changed")
    if world.named("R").start >= ORIGIN or world.named("R").end <= ORIGIN:
        raise ValueError("R must be currently running in both worlds")
    return {
        "all_pre_origin_events": [
            list(event) for event in visible_event_history(world)
        ],
        "all_public_requests": [
            list(request) for request in public_requests(world)
        ],
        "target_submission_s": str(ORIGIN),
        "running_job_start_s": str(world.named("R").start),
        "running_job_age_s": str(ORIGIN - world.named("R").start),
        "running_job_observed_busy": True,
        "q_minus_120": sweep[PREVIOUS],
        "q_minus_60": sweep[LATEST],
        "q_pre_target": sweep[ORIGIN],
        "past_started_count": len(previously_started),
        "historical_wait_median_s": str(previously_started[0].wait),
        "historical_start_rate_per_s": str(Fraction(len(previously_started), 1) / RATE_SECONDS),
        "source": "synthetic deterministic FCFS-compatible three-job schedule",
    }


def frozen_p01_predictions(observation: dict) -> dict[str, Fraction]:
    """The unfitted RP-E011-P01 queue-state and median heuristics."""
    q_previous = observation["q_minus_120"]
    q_latest = observation["q_minus_60"]
    past_started = observation["past_started_count"]
    history = Fraction(observation["historical_wait_median_s"])
    if past_started <= 0:
        return {"history": history, "static": history, "trend": history}
    return {
        "history": history,
        "static": Fraction(q_latest * RATE_SECONDS, past_started),
        "trend": Fraction(max(0, 2 * q_latest - q_previous) * RATE_SECONDS,
                          past_started),
    }


def exact_minimax(short: Fraction, long: Fraction) -> dict:
    if not short <= long:
        raise ValueError("Expected nondecreasing registered target labels")
    midpoint = (short + long) / 2
    worst = max(abs(midpoint - short), abs(midpoint - long))
    assert worst == (long - short) / 2
    return {
        "label_separation_s": str(long - short),
        "equal_weighted_minimax_prediction_s": str(midpoint),
        "unavoidable_maximum_absolute_error_s": str(worst),
        "equally_weighted_two_world_expected_mae_lower_bound_s": str(worst),
        "equal_weighting_is_synthetic_assumption_only": True,
    }


def audit_witness() -> dict:
    short = construct_world(REGISTERED_SHORT_END)
    long = construct_world(REGISTERED_LONG_END)
    short_valid = validate_fcfs_compatible(short)
    long_valid = validate_fcfs_compatible(long)
    short_observed = causal_observation(short)
    long_observed = causal_observation(long)
    if short_observed != long_observed:
        raise ValueError("Known pre-origin observations differ")
    if short.named("T").wait != 1 or long.named("T").wait != 100:
        raise ValueError("Registered target wait contrast is invalid")
    prediction = frozen_p01_predictions(short_observed)
    if prediction != {"history": Fraction(1), "static": Fraction(0),
                      "trend": Fraction(0)}:
        raise ValueError("Known P01-style frozen predictors unexpectedly changed")

    same_world = construct_world(REGISTERED_SHORT_END)
    same_contrast = same_world.named("T").wait - short.named("T").wait
    # Invalid future oracle: actual R completion would distinguish worlds.
    post_origin_oracle_distinct = short.named("R").end != long.named("R").end
    target_longer = replace(
        long.named("T"), end=long.named("T").end + Fraction(17)
    )
    runtime_change_wait_invariant = (
        replace(long, jobs=(long.named("H"), long.named("R"), target_longer))
        .named("T").wait == long.named("T").wait
    )
    if same_contrast != 0 or not post_origin_oracle_distinct or not runtime_change_wait_invariant:
        raise ValueError("One of the prespecified negative controls failed")

    # Independent exact-rational computation of outcomes is separated
    # from the algebraic Lean 4 certificate.
    comparison = {
        name: {
            "prediction_s": str(value),
            "short_abs_error_s": str(abs(value - short.named("T").wait)),
            "long_abs_error_s": str(abs(value - long.named("T").wait)),
            "worst_case_abs_error_s": str(
                max(abs(value - short.named("T").wait),
                    abs(value - long.named("T").wait))
            ),
        } for name, value in prediction.items()
    }
    return {
        "protocol": PROTOCOL,
        "decision": "FINITE_NONIDENTIFIABILITY_VERIFIED",
        "source": "SYNTHETIC_ONLY",
        "first_preregistered_code": "3670d7d9bb15e69c6d354f056ecc4de87b27d55c",
        "world_short": short_valid,
        "world_long": long_valid,
        "full_pre_origin_observations_identical": True,
        "registered_common_observation": short_observed,
        "short_target_wait_s": str(short.named("T").wait),
        "long_target_wait_s": str(long.named("T").wait),
        "frozen_candidate_and_baseline_predictions": comparison,
        "exact_rational_obstruction": exact_minimax(
            short.named("T").wait, long.named("T").wait
        ),
        "registered_negative_controls": {
            "identical_running_completion_gives_no_wait_contrast": same_contrast == 0,
            "illicit_future_completion_oracle_distinguishes_worlds": post_origin_oracle_distinct,
            "changing_target_service_does_not_change_wait": runtime_change_wait_invariant,
        },
        "new_queuing_theorem_claimed": False,
        "empirical_external_validation_claimed": False,
        "scalar_C_validated": False,
        "physical_law_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite an existing RP-F006 original report")
    try:
        result = audit_witness()
    except (ValueError, AssertionError) as exc:
        # Frozen registered invalid case; preserve the first attempt,
        # rather than replace an adverse witness with a convenient one.
        result = {
            "protocol": PROTOCOL,
            "decision": "WITNESS_INVALID",
            "source": "SYNTHETIC_ONLY",
            "error": f"{type(exc).__name__}: {str(exc)[:300]}",
            "new_queuing_theorem_claimed": False,
            "empirical_external_validation_claimed": False,
            "scalar_C_validated": False,
            "physical_law_claimed": False,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "protocol": PROTOCOL,
        "decision": result["decision"],
        "waits_s": [
            result.get("short_target_wait_s"), result.get("long_target_wait_s")
        ],
        "lower_bound_s": (result.get("exact_rational_obstruction") or {}).get(
            "unavoidable_maximum_absolute_error_s"
        ),
    }, sort_keys=True))
    if result["decision"] != "FINITE_NONIDENTIFIABILITY_VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
