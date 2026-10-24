"""RP-E008-S01: independently audited discrete-event queue transfer stress test.

This is deterministic mathematical software simulation, never a physical
observation. The complete model and its outcome gate were registered in
docs/preregistration/RP-E008-S01.md before writing this source.
"""

from __future__ import annotations

import argparse
from collections import deque
from fractions import Fraction
import hashlib
import heapq
import json
from pathlib import Path
import random

ORIGIN_MS = 1000
SAMPLE_STEP_MS = 25
DWELL_MS = 500
PREVIOUS_SAMPLE_MS = 925
LATEST_SAMPLE_MS = 975
PROFILES = ("uniform", "early_burst", "late_burst")
SERVICE_VARIANTS = {
    "constant": (18,),
    "mixed": (12, 18, 24),
    "high_variance": (6, 18, 30),
}
TRAIN_REPETITIONS = tuple(range(4))
HELDOUT_REPETITIONS = tuple(range(4, 8))
BASELINE_CALIBRATION_COUNT = 120
FROZEN_THRESHOLD = Fraction(9, 10)
PROTOCOL = "RP-E008-S01"


def fraction_text(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}"


def source_digest(obj: object) -> str:
    content = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(content).hexdigest()


def design() -> list[dict]:
    return [
        {
            "trial_id": f"{arrival}-{service}-r{rep}",
            "arrival_profile": arrival,
            "service_variant": service,
            "replicate": rep,
            "split": "train" if rep in TRAIN_REPETITIONS else "heldout",
            "arrival_seed": 808000 + 10000 * i + 100 * j + rep,
            "service_seed": 909000 + 10000 * i + 100 * j + rep,
        }
        for i, arrival in enumerate(PROFILES)
        for j, service in enumerate(SERVICE_VARIANTS)
        for rep in range(8)
    ]


def arrivals_for(spec: dict) -> list[int]:
    rng = random.Random(spec["arrival_seed"])
    planned = []
    for window in range(0, ORIGIN_MS, 200):
        if spec["arrival_profile"] == "uniform":
            planned.extend(range(window, window + 200, 5))
        else:
            first_spacing, second_spacing = (
                (3, 12) if spec["arrival_profile"] == "early_burst"
                else (12, 3)
            )
            planned.extend(range(window, window + 100, first_spacing))
            planned.extend(range(window + 100, window + 200, second_spacing))
    return sorted(
        max(0, min(ORIGIN_MS - 1, t + rng.choice((-1, 0, 1))))
        for t in planned
    )


def duration_sources(spec: dict, jobs: int) -> tuple[list[int], list[int]]:
    pattern = SERVICE_VARIANTS[spec["service_variant"]]
    calibration = [
        pattern[k % len(pattern)] for k in range(BASELINE_CALIBRATION_COUNT)
    ]
    assert sum(calibration) == 18 * BASELINE_CALIBRATION_COUNT
    rng = random.Random(spec["service_seed"])
    prechange = []
    while len(prechange) < jobs:
        group = list(pattern)
        rng.shuffle(group)
        prechange.extend(group)
    prechange = prechange[:jobs]
    # Every prechange duration is even: the postchange worker halves it.
    assert all(v % 2 == 0 for v in prechange)
    return calibration, [x // 2 for x in prechange]


def source_for(spec: dict) -> dict:
    arrivals = arrivals_for(spec)
    calibration, duration = duration_sources(spec, len(arrivals))
    return {
        "spec": spec,
        "arrival_ms": arrivals,
        "postchange_service_ms": duration,
        "prechange_calibration_ms": calibration,
        "all_jobs_accepted": True,
        "no_physical_service_or_network_measured": True,
    }


def completion_recursion(source: dict) -> tuple[list[int], list[dict]]:
    """Oracle A: FCFS recursion, independent of the event calendar."""
    arrivals = source["arrival_ms"]
    service = source["postchange_service_ms"]
    if not arrivals or len(arrivals) != len(service):
        raise ValueError("Empty or mismatched job inputs")
    completions = []
    prior_finish = 0
    for arrival, duration in zip(arrivals, service):
        if type(arrival) is not int or not 0 <= arrival < ORIGIN_MS:
            raise ValueError("Invalid arrival timestamp")
        if type(duration) is not int or duration <= 0:
            raise ValueError("Invalid service duration")
        finished = max(arrival, prior_finish) + duration
        completions.append(finished)
        prior_finish = finished
    return completions, sampled_by_counts(arrivals, completions)


def sampled_by_counts(arrivals: list[int], completions: list[int]) -> list[dict]:
    """Generate complete 25-ms statuses from the Lindley-completion oracle."""
    until = max(ORIGIN_MS, completions[-1]) + DWELL_MS + SAMPLE_STEP_MS
    samples = []
    arrival_cursor = 0
    completion_cursor = 0
    for t in range(0, until + 1, SAMPLE_STEP_MS):
        while arrival_cursor < len(arrivals) and arrivals[arrival_cursor] <= t:
            arrival_cursor += 1
        while (completion_cursor < len(completions)
               and completions[completion_cursor] <= t):
            completion_cursor += 1
        backlog = arrival_cursor - completion_cursor
        if backlog < 0:
            raise AssertionError("Impossible negative backlog in recursion")
        samples.append({"time_ms": t, "backlog": backlog,
                        "arrived": arrival_cursor, "completed": completion_cursor})
    return samples


def event_calendar(source: dict) -> tuple[list[int], list[dict], list[dict]]:
    """Oracle B: independent event heap, one active job and explicit FIFO.

    Event priority: completion before arrival at equal timestamps.
    """
    arrivals = source["arrival_ms"]
    service = source["postchange_service_ms"]
    event_heap = [(t, 1, idx) for idx, t in enumerate(arrivals)]
    heapq.heapify(event_heap)
    waiting: deque[int] = deque()
    active: int | None = None
    completed = {}
    trace = []
    while event_heap:
        t, kind, idx = heapq.heappop(event_heap)
        if kind == 1:
            waiting.append(idx)
            trace.append({"time_ms": t, "kind": "arrival", "job": idx})
        else:
            if active != idx:
                raise AssertionError("Calendar completed the wrong active job")
            if idx in completed:
                raise AssertionError("A job completed twice")
            completed[idx] = t
            active = None
            trace.append({"time_ms": t, "kind": "completion", "job": idx})
        if active is None and waiting:
            active = waiting.popleft()
            start = t
            if start < arrivals[active]:
                raise AssertionError("FCFS job started before arrival")
            heapq.heappush(event_heap, (start + service[active], 0, active))
    if len(completed) != len(arrivals):
        raise AssertionError("Not all simulated jobs completed")
    # Separate independent event-sweep derivation of q at sample times.
    until = max(ORIGIN_MS, max(completed.values())) + DWELL_MS + SAMPLE_STEP_MS
    ordered = sorted(trace, key=lambda r: (r["time_ms"],
                                           0 if r["kind"] == "completion" else 1,
                                           r["job"]))
    samples = []
    arrived = 0
    finished = 0
    event_index = 0
    for t in range(0, until + 1, SAMPLE_STEP_MS):
        while event_index < len(ordered) and ordered[event_index]["time_ms"] <= t:
            if ordered[event_index]["kind"] == "arrival":
                arrived += 1
            else:
                finished += 1
            event_index += 1
        samples.append({"time_ms": t, "backlog": arrived - finished,
                        "arrived": arrived, "completed": finished})
    return [completed[k] for k in range(len(arrivals))], samples, trace


def sampled_recovery(samples: list[dict]) -> int:
    """First sampled idle at/after origin with 500 ms sampled confirmation."""
    lookup = {row["time_ms"]: row["backlog"] for row in samples}
    for row in samples:
        t = row["time_ms"]
        if t < ORIGIN_MS or row["backlog"] != 0:
            continue
        if all(lookup.get(candidate) == 0
               for candidate in range(t, t + DWELL_MS + 1, SAMPLE_STEP_MS)):
            return t - ORIGIN_MS
    raise ValueError("No sampled 500-ms sustained idle confirmation")


def predict(samples: list[dict], calibration: list[int]) -> dict:
    if len(calibration) != BASELINE_CALIBRATION_COUNT:
        raise ValueError("Wrong calibration sample count")
    if sum(calibration) != 18 * BASELINE_CALIBRATION_COUNT:
        raise ValueError("Calibration not the frozen prechange capacity")
    lookup = {s["time_ms"]: s["backlog"] for s in samples}
    q0 = lookup[PREVIOUS_SAMPLE_MS]
    q1 = lookup[LATEST_SAMPLE_MS]
    if min(q0, q1) < 0:
        raise ValueError("Negative queue source")
    # Prechange B=1000/18 work/s, postchange 2B=1000/9 work/s.
    b = Fraction(BASELINE_CALIBRATION_COUNT * 1000, sum(calibration))
    static = Fraction(q1, 1) / (2 * b)
    estimated = max(Fraction(0), Fraction(q1) + Fraction(q1 - q0, 2))
    trend = estimated / (2 * b)
    return {
        "sample_prev_ms": PREVIOUS_SAMPLE_MS,
        "sample_last_ms": LATEST_SAMPLE_MS,
        "forecast_origin_ms": ORIGIN_MS,
        "q_prev": q0,
        "q_last": q1,
        "B_work_per_second": fraction_text(b),
        "predicted_backlog_at_origin": fraction_text(estimated),
        "prediction_static_seconds": fraction_text(static),
        "prediction_trend_seconds": fraction_text(trend),
    }


def evaluate_case(source: dict) -> dict:
    a_finish, a_samples = completion_recursion(source)
    b_finish, b_samples, trace = event_calendar(source)
    if a_finish != b_finish or a_samples != b_samples:
        raise ValueError("The two independent FCFS engines disagree")
    if len(trace) != 2 * len(source["arrival_ms"]):
        raise ValueError("Missing arrival/completion trace records")
    if any(s["backlog"] < 0 for s in b_samples):
        raise ValueError("Negative event-calendar backlog")
    observed_ms = sampled_recovery(a_samples)
    if observed_ms != sampled_recovery(b_samples):
        raise ValueError("Sampled recovery differs across independent engines")
    true_ms = max(0, a_finish[-1] - ORIGIN_MS)
    if not 0 <= observed_ms - true_ms < SAMPLE_STEP_MS:
        raise ValueError("Sampled drain disagrees with exact service endpoint")
    prediction = predict(a_samples, source["prechange_calibration_ms"])
    actual = Fraction(observed_ms, 1000)
    baseline = Fraction(prediction["prediction_static_seconds"])
    trend = Fraction(prediction["prediction_trend_seconds"])
    return {
        "trial_id": source["spec"]["trial_id"],
        "arrival_profile": source["spec"]["arrival_profile"],
        "service_variant": source["spec"]["service_variant"],
        "split": source["spec"]["split"],
        "source_sha256": source_digest(source),
        "arrivals": len(source["arrival_ms"]),
        "calendar_event_sha256": source_digest(trace),
        "sampled_status_sha256": source_digest(a_samples),
        "completion_trace_sha256": source_digest(a_finish),
        "oracle_A_B_equal": True,
        "original_source": source,
        "original_completion_times_ms": a_finish,
        "original_event_calendar": trace,
        "original_sampled_status": a_samples,
        "actual_last_completion_ms": a_finish[-1],
        "true_drain_after_origin_ms": true_ms,
        "first_sampled_idle_after_origin_ms": observed_ms,
        "observed_recovery_seconds": fraction_text(actual),
        "predictions": prediction,
        "absolute_errors_seconds": {
            "static": fraction_text(abs(actual - baseline)),
            "trend": fraction_text(abs(actual - trend)),
        },
        "not_physical_measurement": True,
    }


def mean_fraction(values: list[Fraction]) -> Fraction:
    if not values:
        raise ValueError("Empty scoring set")
    return sum(values, Fraction(0)) / len(values)


def summarize(cases: list[dict]) -> dict:
    if len(cases) != 72 or len({c["trial_id"] for c in cases}) != 72:
        raise ValueError("Incomplete 72-case preregistered grid")
    expected = {spec["trial_id"] for spec in design()}
    if {c["trial_id"] for c in cases} != expected:
        raise ValueError("Unexpected or substituted case")
    subsets = {name: [c for c in cases if c["split"] == name]
               for name in ("train", "heldout")}
    if any(len(rows) != 36 for rows in subsets.values()):
        raise ValueError("Train and heldout blocks must each have 36")
    def two_maes(rows: list[dict]) -> dict:
        return {
            model: mean_fraction([
                Fraction(c["absolute_errors_seconds"][model])
                for c in rows
            ])
            for model in ("static", "trend")
        }
    train = two_maes(subsets["train"])
    test = two_maes(subsets["heldout"])
    passed = test["static"] > 0 and test["trend"] <= FROZEN_THRESHOLD * test["static"]
    regime = {}
    for key in (*PROFILES, *SERVICE_VARIANTS):
        matched = [
            c for c in subsets["heldout"]
            if c["arrival_profile"] == key or c["service_variant"] == key
        ]
        regime[key] = {name: fraction_text(value)
                       for name, value in two_maes(matched).items()}
    wins = ties = losses = 0
    for c in subsets["heldout"]:
        e = c["absolute_errors_seconds"]
        a, b = Fraction(e["static"]), Fraction(e["trend"])
        if b < a:
            wins += 1
        elif b == a:
            ties += 1
        else:
            losses += 1
    return {
        "decision": "PASS_SIMULATED_TRANSFER" if passed
        else "NO_REGISTERED_SIMULATED_TRANSFER",
        "preregistered_threshold": fraction_text(FROZEN_THRESHOLD),
        "diagnostic_mae_seconds": {k: fraction_text(v) for k, v in train.items()},
        "heldout_mae_seconds": {k: fraction_text(v) for k, v in test.items()},
        "heldout_mae_approx_seconds": {k: float(v) for k, v in test.items()},
        "heldout_profile_mae_seconds": regime,
        "heldout_trial_wins_ties_losses": {"wins": wins, "ties": ties, "losses": losses},
        "complete_trials": len(cases), "heldout_trials": len(subsets["heldout"]),
        "mathematical_model_only": True,
        "independent_physical_replication": "NOT_PERFORMED",
        "RP_E007_observations_reused": False,
        "lean_formalization": "NO_NEW_THEOREM",
    }


def run_all() -> tuple[list[dict], dict]:
    cases = [evaluate_case(source_for(spec)) for spec in design()]
    summary = summarize(cases)
    return cases, summary


def write_first_run(root: Path) -> dict:
    if root.exists() and any(root.iterdir()):
        raise ValueError("The original simulation output may never be overwritten")
    root.mkdir(parents=True, exist_ok=True)
    complete, result = run_all()
    for case in complete:
        (root / f'{case["trial_id"]}.json').write_text(
            json.dumps(case, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    (root / "summary.json").write_text(
        json.dumps({"protocol": PROTOCOL, **result}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    hashes = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.iterdir()) if p.is_file()
    }
    (root / "source-manifest.json").write_text(
        json.dumps({"sha256": hashes, "count": len(hashes),
                    "archive_semantics": "first run; no replacement"},
                   sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = write_first_run(args.output)
    except Exception as error:
        args.output.mkdir(parents=True, exist_ok=True)
        path = args.output / "error.json"
        path.write_text(json.dumps({
            "protocol": PROTOCOL,
            "decision": "STOP_SIMULATOR_INVARIANT",
            "error": f"{type(error).__name__}: {error}",
        }, indent=2) + "\n", encoding="utf-8")
        raise
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
