"""RP-E010-P01: frozen external HPC2N observational wait-time evaluation.

The source and prediction protocol were registered separately on main
before this implementation. No model coefficients, lag choices, outcome
trimming or source filters are selected from held-out wait errors.

This is a historical PARALLEL scheduler with upstream-cleaned job records,
not an observed physical FIFO, new stability theorem or scalar C test.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import urllib.error

from experiments.rp_e010_source_audit import (
    EXPECTED_BLOB, EXPECTED_BYTES, SOURCE_URL,
    fetch_exact_pinned_source, inspect_bytes, git_blob_sha1,
)

PROTOCOL = "RP-E010-P01"
SOURCE_SHA256 = "77b8993c73ae438385f6c0015708251f52dc316267b03ac19a406fbea2802afa"
EXPECTED_RECORDS = 202_871
EXPECTED_TARGET_ELIGIBLE = 201_992
PRIOR_SECONDS = Decimal(120)
LATEST_SECONDS = Decimal(60)
HISTORY_SECONDS = Decimal(3600)
START_WINDOW_SECONDS = Decimal(3540)
THRESHOLD_RATIO = Decimal("0.90")
MIN_CASES = 1000


@dataclass(frozen=True)
class Job:
    job_id: int
    submit: Decimal
    wait: Decimal
    runtime: Decimal
    processors: int
    status: int

    @property
    def start(self) -> Decimal:
        return self.submit + self.wait

    @property
    def eligible_target(self) -> bool:
        return (self.submit >= 0 and self.wait >= 0
                and self.runtime >= 0 and self.processors > 0
                and self.status == 1)


def parse_verified_jobs(raw: bytes) -> tuple[list[Job], dict]:
    """Refuse bytes before reading records; double-check D01's fixed counts."""
    if (len(raw) != EXPECTED_BYTES or git_blob_sha1(raw) != EXPECTED_BLOB
            or sha256(raw).hexdigest() != SOURCE_SHA256):
        raise ValueError("Pinned external source bytes do not match RP-E010-D01")
    verified = inspect_bytes(raw)
    stats = verified["counters"]
    if (verified["decision"] != "DATASET_SCHEMA_VERIFIED"
            or verified["independent_parser_agreement"] is not True
            or stats["data_lines"] != EXPECTED_RECORDS
            or stats["eligible_completed"] != EXPECTED_TARGET_ELIGIBLE
            or stats["missing_queue"] != EXPECTED_RECORDS):
        raise ValueError("Source structural audit disagrees with original D01")
    jobs = []
    for line in raw.decode("utf-8", errors="strict").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        tokens = line.split()
        if len(tokens) != 18:
            raise ValueError("Observed SWF row has changed width")
        try:
            job = Job(
                int(tokens[0]), Decimal(tokens[1]), Decimal(tokens[2]),
                Decimal(tokens[3]), int(Decimal(tokens[4])), int(tokens[10])
            )
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Unparseable verified workload") from error
        if not all(x.is_finite() for x in (
            job.submit, job.wait, job.runtime
        )):
            raise ValueError("Nonfinite original workload")
        jobs.append(job)
    if (len(jobs) != EXPECTED_RECORDS or
            sum(job.eligible_target for job in jobs) != EXPECTED_TARGET_ELIGIBLE):
        raise ValueError("Reparsed job count differs from double-oracle source audit")
    return jobs, {
        "actual_external_bytes": len(raw),
        "actual_external_sha256": sha256(raw).hexdigest(),
        "actual_external_git_blob_sha1": git_blob_sha1(raw),
        "source_url": SOURCE_URL,
        "source_record_count": stats["data_lines"],
        "schema_eligible_target_count": stats["eligible_completed"],
        "unavailable_queue_id_count": stats["missing_queue"],
        "missing_status_count": stats["missing_status"],
        "missing_wait_count": stats["missing_wait"],
    }


class RecordedEvents:
    """Derived recorded global waiting-count proxy; never call it physical q."""

    def __init__(self, jobs: list[Job]) -> None:
        self.stamps = sorted(
            (job.submit, job.start, job.wait)
            for job in jobs if job.submit >= 0 and job.wait >= 0
        )
        if not self.stamps:
            raise ValueError("No observed submission/start pairs")
        self.arrivals = sorted(a for a, _, _ in self.stamps)
        self.starts = sorted(s for _, s, _ in self.stamps)
        self.started_with_wait = sorted((s, w) for _, s, w in self.stamps)
        self.history_times = [s for s, _ in self.started_with_wait]
        self.history_cumulative_wait = [Decimal(0)]
        for _, wait in self.started_with_wait:
            self.history_cumulative_wait.append(
                self.history_cumulative_wait[-1] + wait
            )

    def binary_backlog(self, snapshot: Decimal) -> int:
        """a < snapshot <= s; strict event ordering is preregistered."""
        return (bisect_left(self.arrivals, snapshot)
                - bisect_left(self.starts, snapshot))

    def history(self, origin: Decimal) -> tuple[int, Decimal]:
        """Only jobs ALREADY STARTED in [t-3600,t-60)."""
        first = bisect_left(self.history_times, origin - HISTORY_SECONDS)
        last = bisect_left(self.history_times, origin - LATEST_SECONDS)
        if first > last:
            raise AssertionError("Impossible inverted historical interval")
        count = last - first
        return count, (
            self.history_cumulative_wait[last] -
            self.history_cumulative_wait[first]
        )

    def swept_backlog(self, instants: list[Decimal]) -> dict[Decimal, int]:
        """Separate two-pointer event sweep of original accepted/start clocks.

        This independent method does not call the binary-search q oracle.
        Both process events with timestamp strictly less than snapshot.
        """
        arrivals = self.arrivals
        starts = self.starts
        arrived = started = 0
        result = {}
        for snapshot in sorted(set(instants)):
            while arrived < len(arrivals) and arrivals[arrived] < snapshot:
                arrived += 1
            while started < len(starts) and starts[started] < snapshot:
                started += 1
            queue_proxy = arrived - started
            if queue_proxy < 0:
                raise ValueError("Negative reconstructed aggregate wait count")
            result[snapshot] = queue_proxy
        return result


def cohort(jobs: list[Job]) -> tuple[list[Job], list[Job], dict]:
    submitted = [j.submit for j in jobs if j.submit >= 0]
    if not submitted:
        raise ValueError("No real nonnegative recorded submissions")
    minimum, maximum = min(submitted), max(submitted)
    cutoff = minimum + (Decimal(7) * (maximum - minimum) // Decimal(10))
    candidates = [
        job for job in jobs
        if job.eligible_target and job.submit >= minimum + HISTORY_SECONDS
    ]
    # Feature-eligibility |W_t| is checked independently afterwards.
    diagnostics = [j for j in candidates if j.submit < cutoff]
    heldout = [j for j in candidates if j.submit >= cutoff]
    return diagnostics, heldout, {
        "earliest_submit_seconds": str(minimum),
        "latest_submit_seconds": str(maximum),
        "chronological_cutoff_seconds": str(cutoff),
        "feature_age_floor_seconds": str(minimum + HISTORY_SECONDS),
        "candidate_diagnostic_targets_before_past-start-eligibility": len(diagnostics),
        "candidate_heldout_targets_before_past-start-eligibility": len(heldout),
    }


def feature_at_origin(origin: Decimal, events: RecordedEvents,
                      swept: dict[Decimal, int]) -> dict | None:
    count, historical_wait_sum = events.history(origin)
    if count == 0:
        return None
    older, latest = origin - PRIOR_SECONDS, origin - LATEST_SECONDS
    old_binary = events.binary_backlog(older)
    last_binary = events.binary_backlog(latest)
    if (older not in swept or latest not in swept
            or old_binary != swept[older] or last_binary != swept[latest]):
        raise ValueError("Independent binary/event-sweep backlog oracles disagree")
    if min(old_binary, last_binary) < 0:
        raise ValueError("Negative archive-derived waiting proxy")
    b = Decimal(count) / START_WINDOW_SECONDS
    if b <= 0:
        raise ValueError("Invalid historical start-rate denominator")
    correction = max(0, last_binary + (last_binary - old_binary))
    # Calculate count/rate directly, avoiding a second rounding of B.
    preds = {
        "static": Decimal(last_binary) * START_WINDOW_SECONDS / Decimal(count),
        "trend": Decimal(correction) * START_WINDOW_SECONDS / Decimal(count),
        "history": historical_wait_sum / Decimal(count),
    }
    if any(not value.is_finite() or value < 0 for value in preds.values()):
        raise ValueError("Nonfinite or negative frozen forecast")
    return {
        "snapshot_previous_s": older,
        "snapshot_latest_s": latest,
        "q_previous": old_binary,
        "q_latest": last_binary,
        "predicted_queue_at_submission": correction,
        "historical_starts": count,
        "history_window_lower_inclusive_s": origin - HISTORY_SECONDS,
        "history_window_upper_exclusive_s": latest,
        "observed_B_starts_per_second": b,
        "model_predictions": preds,
    }


def processor_group(processors: int) -> str:
    if 1 <= processors <= 2:
        return "1..2"
    if 3 <= processors <= 16:
        return "3..16"
    if processors > 16:
        return ">16"
    raise ValueError("Invalid eligible processor group")


def stringify_row(job: Job, split: str, feature: dict,
                  diagnostic_mean: Decimal | None) -> dict:
    estimates = dict(feature["model_predictions"])
    if diagnostic_mean is not None:
        estimates["diagnostic_constant"] = diagnostic_mean
    # The returned record is emitted as original-machine forecast evidence.
    # Labels enter only into error computation, never feature extraction.
    error = {name: abs(value - job.wait) for name, value in estimates.items()}
    if any(not value.is_finite() for value in error.values()):
        raise ValueError("Nonfinite original untrimmed outcome error")
    return {
        "job_id": job.job_id,
        "split": split,
        "origin_submit_seconds": str(job.submit),
        "observed_wait_seconds": str(job.wait),
        "recorded_allocated_processors": job.processors,
        "processor_group": processor_group(job.processors),
        "causal_snapshot_previous_seconds": str(feature["snapshot_previous_s"]),
        "causal_snapshot_latest_seconds": str(feature["snapshot_latest_s"]),
        "recorded_waiting_proxy_previous": feature["q_previous"],
        "recorded_waiting_proxy_latest": feature["q_latest"],
        "predicted_waiting_proxy_at_origin": feature["predicted_queue_at_submission"],
        "past_started_job_count": feature["historical_starts"],
        "observed_B_started_jobs_per_second": str(feature["observed_B_starts_per_second"]),
        "predictions_seconds": {k: str(v) for k, v in estimates.items()},
        "absolute_errors_seconds": {k: str(v) for k, v in error.items()},
        "signed_errors_seconds": {k: str(v - job.wait)
                                  for k, v in estimates.items()},
        "causal_pre_origin_feature_verified": True,
    }


def frozen_gate(maes: dict[str, Decimal]) -> str:
    """Two-comparator 10% gate fixed before the HPC first run."""
    if any(name not in maes for name in ("static", "trend", "history")):
        raise ValueError("A preregistered comparator is missing")
    if any(not value.is_finite() or value < 0 for value in maes.values()):
        raise ValueError("Invalid observational forecast score")
    if (
        maes["static"] > 0 and maes["history"] > 0
        and maes["trend"] <= THRESHOLD_RATIO * maes["static"]
        and maes["trend"] <= THRESHOLD_RATIO * maes["history"]
    ):
        return "PASS_OBSERVATIONAL_INCREMENT"
    return "NO_REGISTERED_OBSERVATIONAL_GAIN"


class DecimalMetrics:
    def __init__(self, models: tuple[str, ...]) -> None:
        self.models = models
        self.count = 0
        self.errors = {name: Decimal(0) for name in models}
        self.bias = {name: Decimal(0) for name in models}
        self.zero_waits = 0

    def append(self, original: dict) -> None:
        self.count += 1
        self.zero_waits += int(Decimal(original["observed_wait_seconds"]) == 0)
        for model in self.models:
            self.errors[model] += Decimal(original["absolute_errors_seconds"][model])
            self.bias[model] += Decimal(original["signed_errors_seconds"][model])

    def summary(self) -> dict:
        if self.count == 0:
            return {"jobs": 0, "mae_seconds": None, "bias_seconds": None}
        return {
            "jobs": self.count, "zero_wait_jobs": self.zero_waits,
            "mae_seconds": {k: str(v / self.count)
                            for k, v in self.errors.items()},
            "bias_seconds": {k: str(v / self.count)
                             for k, v in self.bias.items()},
        }


def evaluate_data(jobs: list[Job], provenance: dict, output: Path) -> dict:
    events = RecordedEvents(jobs)
    diagnostics, holdout, times = cohort(jobs)
    if not diagnostics or not holdout:
        raise ValueError("No chronological source target in one split")
    all_targets = diagnostics + holdout
    snapshots = [
        s for job in all_targets
        for s in (job.submit - PRIOR_SECONDS, job.submit - LATEST_SECONDS)
    ]
    swept = events.swept_backlog(snapshots)
    origins = sorted(set(j.submit for j in all_targets))
    # Feature cache is constructed without reading ANY target wait label
    # of jobs in the held-out set. Past-start history is causally prior.
    cache = {t: feature_at_origin(t, events, swept) for t in origins}
    selected_diag = [j for j in diagnostics if cache[j.submit] is not None]
    selected_test = [j for j in holdout if cache[j.submit] is not None]
    if min(len(selected_diag), len(selected_test)) < MIN_CASES:
        raise ValueError("Fewer than 1,000 feature-eligible target rows per split")
    diagnostic_mean = (
        sum((j.wait for j in selected_diag), Decimal(0))
        / Decimal(len(selected_diag))
    )
    output.mkdir(parents=True, exist_ok=True)
    diagnostic_stats = DecimalMetrics(("static", "trend", "history"))
    test_stats = DecimalMetrics(("static", "trend", "history", "diagnostic_constant"))
    processor_stats = {
        group: DecimalMetrics(("static", "trend", "history", "diagnostic_constant"))
        for group in ("1..2", "3..16", ">16")
    }
    archives = {}
    for split, original, accumulator in (
        ("diagnostic", selected_diag, diagnostic_stats),
        ("holdout", selected_test, test_stats),
    ):
        path = output / f"{split}-original-predictions.jsonl"
        if path.exists():
            raise ValueError("First original prediction records already exist")
        with path.open("w", encoding="utf-8") as handle:
            for job in original:
                item = stringify_row(
                    job, split, cache[job.submit],
                    diagnostic_mean if split == "holdout" else None
                )
                handle.write(json.dumps(item, sort_keys=True) + "\n")
                accumulator.append(item)
                if split == "holdout":
                    processor_stats[item["processor_group"]].append(item)
        archives[split] = {
            "file": path.name, "original_bytes": path.stat().st_size,
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
    diagnostic = diagnostic_stats.summary()
    heldout = test_stats.summary()
    errors = {k: Decimal(v) for k, v in heldout["mae_seconds"].items()}
    decision = frozen_gate(errors)
    result = {
        "protocol": PROTOCOL,
        "decision": decision,
        "registered_primary_improvement_ratio": str(THRESHOLD_RATIO),
        "interpretation": "historical archive-derived aggregate wait proxy, not observed physical FIFO",
        "independent_physical_replication": "NOT_PERFORMED",
        "independent_queue_identifiers": "UNAVAILABLE",
        "scalar_C_physical_law_test": "NOT_PERFORMED",
        "new_lean_theorem": False,
        "source": provenance,
        "split": times,
        "past_start_observation_count": len(events.stamps),
        "distinct_prediction_origins": len(origins),
        "feature_eligible_targets": len(selected_diag) + len(selected_test),
        "excluded_by_zero_prior_starts": (
            len(all_targets) - len(selected_diag) - len(selected_test)
        ),
        "source_unknown_wait_records": provenance["missing_wait_count"],
        "two_queue_oracles_agree_all_origins": True,
        "source_schema_eligible_targets": EXPECTED_TARGET_ELIGIBLE,
        "diagnostic": diagnostic,
        "heldout": heldout,
        "heldout_by_allocated_processors": {
            group: stats.summary() for group, stats in processor_stats.items()
        },
        "original_prediction_files": archives,
        "holdout_constant_from_diagnostic_only_s": str(diagnostic_mean),
        "one_observational_trace_upstream_cleaned": True,
        "source_mirror_equals_original_PWA_gzip": "NOT_ESTABLISHED",
    }
    return result


def first_run(output: Path, *, raw_override: bytes | None = None) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Cannot overwrite original RP-E010-P01 first run")
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "protocol": PROTOCOL, "decision": "STOP_OBSERVATIONAL_AUDIT",
        "first_run_github_id": os.environ.get("GITHUB_RUN_ID"),
        "first_run_source_commit": os.environ.get("GITHUB_SHA"),
        "first_run_environment": platform.platform(),
        "errors": [],
        "original_results": None,
    }
    try:
        raw = fetch_exact_pinned_source() if raw_override is None else raw_override
        jobs, source = parse_verified_jobs(raw)
        with localcontext() as ctx:
            ctx.prec = 45
            report["original_results"] = evaluate_data(jobs, source, output)
        report["decision"] = report["original_results"]["decision"]
    except (OSError, TimeoutError, urllib.error.URLError, UnicodeError,
            InvalidOperation, ValueError, TypeError, AssertionError,
            OverflowError, ZeroDivisionError) as error:
        report["errors"].append({
            "kind": type(error).__name__,
            "reason": str(error)[:500],
        })
    finally:
        (output / "RP-E010-P01-first-evaluation.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = first_run(args.output)
    meta = report["original_results"]
    print(json.dumps({
        "decision": report["decision"], "errors": report["errors"],
        "diagnostic_jobs": meta["diagnostic"]["jobs"] if meta else None,
        "heldout_jobs": meta["heldout"]["jobs"] if meta else None,
        "heldout_mae": meta["heldout"]["mae_seconds"] if meta else None,
    }, sort_keys=True))
    if report["decision"] == "STOP_OBSERVATIONAL_AUDIT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
