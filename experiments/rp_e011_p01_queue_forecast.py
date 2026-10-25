"""RP-E011-P01: preregistered, externally observed, queue-aware wait forecast.

Protocol frozen on main BEFORE this module. No fit, parameter selection,
holdout outcome trimming or new physics. Historical starts/waits become
causally visible only after their start event, with a 60-second buffer.

All raw third-party and per-job prediction lines stay in temporary GitHub
Actions artifacts; only metadata plus SHA hashes belong in permanent Git.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import platform
import shlex

from experiments.rp_e011_jsspp_source import SourceBlocked, download_exact
from experiments.rp_e011_d04_temporal import (
    ROOT, SOURCE_SIZE, SOURCE_SHA, audit_verified_bytes
)

PROTOCOL = "RP-E011-P01"
D04_AUDIT_SHA = "be9b871e29b2bd014d0bc365f4ae6d2f23f8ad428aa41b1932446edf173fb240"
CUTOFF = Decimal("1472994372.8")
EXPECTED_DIAGNOSTIC = 303_210
EXPECTED_HELDOUT = 169_189
EXPECTED_ELIGIBLE = 472_399
MIN_HISTORY_GROUP = 16
HISTORY_LAST_K = 64
PREVIOUS_SECONDS = Decimal(120)
LATEST_SECONDS = Decimal(60)
HISTORY_WINDOW_SECONDS = Decimal(3600)
RATE_DENOMINATOR_SECONDS = Decimal(3540)
GAIN_RATIO = Decimal("0.90")
MODELS = ("history", "static", "trend")


class AuditStop(Exception):
    """Do not replace a structural failure with a predictive result."""


@dataclass(frozen=True, slots=True)
class Job:
    job_id: int
    submit: Decimal
    wait: Decimal
    requested: Decimal
    queue: str

    @property
    def start(self) -> Decimal:
        return self.submit + self.wait

    @property
    def size_group(self) -> str:
        if self.requested <= 2:
            return "small"
        if self.requested <= 16:
            return "medium"
        return "large"


def finite(cell: str) -> Decimal:
    try:
        number = Decimal(cell)
    except InvalidOperation as exc:
        raise AuditStop("Invalid external numeric SWF field") from exc
    if not number.is_finite():
        raise AuditStop("Nonfinite original SWF numeric field")
    return number


def validate_prior_d04_archive() -> None:
    path = ROOT / "docs/results/RP-E011-D04-first-run/audit.json"
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != D04_AUDIT_SHA:
        raise AuditStop("Frozen original D04 metadata SHA differs")
    data = json.loads(payload)
    if (data["decision"] != "TEMPORAL_SOURCE_FEASIBLE"
            or data["source_identity"]["sha256"] != SOURCE_SHA
            or data["temporal_coverage"]["diagnostic_candidate_count"]
            != EXPECTED_DIAGNOSTIC
            or data["temporal_coverage"]["heldout_candidate_count"]
            != EXPECTED_HELDOUT
            or data["schema"]["known_first_line_id_zero_exception_count"] != 1
            or data["d02_original_verdict_unchanged"]
            != "DATASET_SCHEMA_REJECTED"):
        raise AuditStop("Prior D04 source evidence is not the frozen original")


def parse_pinned_jobs(raw: bytes) -> tuple[list[Job], dict]:
    """Only after hash-first validation; D04 oracles are an additional gate."""
    if len(raw) != SOURCE_SIZE or sha256(raw).hexdigest() != SOURCE_SHA:
        raise AuditStop("Original external byte identity failure")
    validate_prior_d04_archive()
    source_audit = audit_verified_bytes(raw)
    if source_audit["decision"] != "TEMPORAL_SOURCE_FEASIBLE":
        raise AuditStop("Frozen D04 source/schema/original ID gate disagrees")
    jobs = []
    seen = set()
    data_ordinal = 0
    for physical_line, line in enumerate(raw.decode("utf-8", "strict").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        data_ordinal += 1
        try:
            fields = shlex.split(stripped, comments=False, posix=True)
        except ValueError as exc:
            raise AuditStop("Original extended SWF quoting is not parseable") from exc
        if len(fields) != 22:
            raise AuditStop("Original extended record differs from 22 fields")
        try:
            job_id = int(fields[0])
        except ValueError as exc:
            raise AuditStop("Noninteger source job ID") from exc
        if job_id == 0 and physical_line == 1 and data_ordinal == 1:
            continue
        if job_id <= 0 or job_id in seen:
            raise AuditStop("Unexpected invalid or duplicate source job ID")
        seen.add(job_id)
        submit, wait, requested = finite(fields[1]), finite(fields[2]), finite(fields[7])
        queue = fields[19].strip()
        if (submit < 0 or wait < 0 or requested <= 0
                or queue.lower() in ("", "-1", "none", "null", "?")):
            raise AuditStop("Unexpected ineligible job under D04 definition")
        jobs.append(Job(job_id, submit, wait, requested, queue))
    if data_ordinal != EXPECTED_ELIGIBLE + 1 or len(jobs) != EXPECTED_ELIGIBLE:
        raise AuditStop("Unexpected source rows or excluded job count")
    diagnostic = sum(job.submit < CUTOFF for job in jobs)
    if (diagnostic != EXPECTED_DIAGNOSTIC
            or len(jobs) - diagnostic != EXPECTED_HELDOUT
            or len({j.queue for j in jobs}) != 13):
        raise AuditStop("Population or preregistered chronological partition changed")
    return jobs, {
        "downloaded_source_bytes": len(raw),
        "source_sha256": sha256(raw).hexdigest(),
        "original_D04_audit_sha256": D04_AUDIT_SHA,
        "original_D02_verdict_unchanged": "DATASET_SCHEMA_REJECTED",
        "known_ID_zero_first_line_exclusion": 1,
        "source_eligible_jobs": len(jobs),
        "diagnostic_jobs": diagnostic,
        "heldout_jobs": len(jobs) - diagnostic,
        "queue_count": 13,
        "source_is_independently_collected_observational_data": True,
    }


def median(values: list[Decimal]) -> Decimal:
    """Classical exact median, even-length midpoint from two inner values."""
    if not values:
        return Decimal(0)
    ordered = sorted(values)
    center = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[center]
    return (ordered[center - 1] + ordered[center]) / 2


class HistoricalStarts:
    """History sources contain start-time events; none are used before start."""

    def __init__(self, jobs: list[Job]) -> None:
        self.by_queue: dict[str, list[tuple[Decimal, int, Decimal]]] = defaultdict(list)
        self.by_queue_group: dict[tuple[str, str], list[tuple[Decimal, int, Decimal]]] = defaultdict(list)
        self.all_starts: list[tuple[Decimal, int, Decimal]] = []
        for job in jobs:
            item = (job.start, job.job_id, job.wait)
            self.by_queue[job.queue].append(item)
            self.by_queue_group[(job.queue, job.size_group)].append(item)
            self.all_starts.append(item)
        self.keys: dict[tuple[str, str | None], list[tuple[Decimal, int]]] = {}
        for queue, records in self.by_queue.items():
            records.sort(key=lambda item: (item[0], item[1]))
            self.keys[(queue, None)] = [(s, jid) for s, jid, _ in records]
        for key, records in self.by_queue_group.items():
            records.sort(key=lambda item: (item[0], item[1]))
            self.keys[key] = [(s, jid) for s, jid, _ in records]
        self.all_starts.sort(key=lambda item: (item[0], item[1]))
        self.global_keys = [(s, jid) for s, jid, _ in self.all_starts]

    @staticmethod
    def before(keys: list[tuple[Decimal, int]], cutoff: Decimal) -> int:
        # Every original valid job ID > 0; (time, 0) means strictly before.
        return bisect_left(keys, (cutoff, 0))

    def queue_started_count(self, queue: str, low: Decimal,
                            high: Decimal) -> int:
        keys = self.keys.get((queue, None), [])
        return self.before(keys, high) - self.before(keys, low)

    def historical_wait_median(self, queue: str, size: str,
                               high: Decimal) -> Decimal:
        records = self.by_queue_group.get((queue, size), [])
        keys = self.keys.get((queue, size), [])
        end = self.before(keys, high)
        if end >= MIN_HISTORY_GROUP:
            return median([wait for _, _, wait in records[
                max(0, end - HISTORY_LAST_K):end
            ]])
        records = self.by_queue.get(queue, [])
        end = self.before(self.keys.get((queue, None), []), high)
        if end == 0:
            records = self.all_starts
            end = self.before(self.global_keys, high)
        return median([wait for _, _, wait in records[
            max(0, end - HISTORY_LAST_K):end
        ]])


class QueueSnapshots:
    """Binary-count oracle and a separate chronological event-sweep oracle."""

    def __init__(self, jobs: list[Job]) -> None:
        by_queue_submits = defaultdict(list)
        by_queue_starts = defaultdict(list)
        self.event_stream = []
        for job in jobs:
            by_queue_submits[job.queue].append(job.submit)
            by_queue_starts[job.queue].append(job.start)
            self.event_stream.append((job.submit, job.queue, +1))
            self.event_stream.append((job.start, job.queue, -1))
        self.arrivals = {q: sorted(s) for q, s in by_queue_submits.items()}
        self.starts = {q: sorted(s) for q, s in by_queue_starts.items()}
        self.event_stream.sort(key=lambda event: event[0])

    def binary(self, queue: str, snapshot: Decimal) -> int:
        left = bisect_left(self.arrivals.get(queue, []), snapshot)
        right = bisect_left(self.starts.get(queue, []), snapshot)
        value = left - right
        if value < 0:
            raise AuditStop("Negative causal queue count from binary oracle")
        return value

    def sweep(self, requested: set[tuple[Decimal, str]]) -> dict[tuple[Decimal, str], int]:
        """Observe events only if event_time < snapshot, never <=."""
        counts = defaultdict(int)
        responses = {}
        event = 0
        for moment, queue in sorted(requested, key=lambda item: (item[0], item[1])):
            while (event < len(self.event_stream)
                   and self.event_stream[event][0] < moment):
                _, label, delta = self.event_stream[event]
                counts[label] += delta
                event += 1
            value = counts[queue]
            if value < 0:
                raise AuditStop("Negative causal queue count from event sweep")
            responses[(moment, queue)] = value
        return responses


def frozen_predictions(
    job: Job, snapshots: QueueSnapshots, swept: dict[tuple[Decimal, str], int],
    history: HistoricalStarts,
) -> tuple[dict[str, Decimal], dict]:
    t = job.submit
    earlier, latest = t - PREVIOUS_SECONDS, t - LATEST_SECONDS
    q_prev = snapshots.binary(job.queue, earlier)
    q_latest = snapshots.binary(job.queue, latest)
    if ((earlier, job.queue) not in swept
            or (latest, job.queue) not in swept
            or swept[(earlier, job.queue)] != q_prev
            or swept[(latest, job.queue)] != q_latest):
        raise AuditStop("Independent queue-state oracles disagree")
    prior_median = history.historical_wait_median(
        job.queue, job.size_group, latest
    )
    previous_starts = history.queue_started_count(
        job.queue, t - HISTORY_WINDOW_SECONDS, latest
    )
    if previous_starts < 0:
        raise AuditStop("Negative past-start count")
    if previous_starts == 0:
        models = {name: prior_median for name in MODELS}
    else:
        models = {
            "history": prior_median,
            "static": Decimal(q_latest) * RATE_DENOMINATOR_SECONDS
            / Decimal(previous_starts),
            "trend": Decimal(max(0, 2 * q_latest - q_prev))
            * RATE_DENOMINATOR_SECONDS / Decimal(previous_starts),
        }
    if any(not prediction.is_finite() or prediction < 0
           for prediction in models.values()):
        raise AuditStop("Nonfinite or negative registered forecast")
    return models, {
        "q_previous": q_prev,
        "q_latest": q_latest,
        "prior_started_queue_count_in_window": previous_starts,
        "zero_past_start_fallback": previous_starts == 0,
        "causal_snapshots_verified": True,
    }


class Metrics:
    def __init__(self) -> None:
        self.jobs = 0
        self.zero_waits = 0
        self.zero_rate_fallbacks = 0
        self.error = {name: Decimal(0) for name in MODELS}
        self.bias = {name: Decimal(0) for name in MODELS}

    def add(self, job: Job, forecasts: dict[str, Decimal], feature: dict) -> None:
        self.jobs += 1
        self.zero_waits += int(job.wait == 0)
        self.zero_rate_fallbacks += int(feature["zero_past_start_fallback"])
        for name in MODELS:
            difference = forecasts[name] - job.wait
            self.error[name] += abs(difference)
            self.bias[name] += difference

    def summary(self) -> dict:
        return {
            "jobs": self.jobs,
            "zero_waits": self.zero_waits,
            "zero_past_start_rate_fallbacks": self.zero_rate_fallbacks,
            "mae_seconds": ({name: str(total / self.jobs)
                for name, total in self.error.items()} if self.jobs else None),
            "bias_seconds": ({name: str(total / self.jobs)
                for name, total in self.bias.items()} if self.jobs else None),
        }


def registered_gate(scores: dict[str, Decimal]) -> str:
    if set(scores) != set(MODELS):
        raise AuditStop("The three preregistered models must all be scored")
    if any(not value.is_finite() or value < 0 for value in scores.values()):
        raise AuditStop("Invalid primary error metric")
    if (scores["static"] > 0 and scores["history"] > 0
            and scores["trend"] <= GAIN_RATIO * scores["static"]
            and scores["trend"] <= GAIN_RATIO * scores["history"]):
        return "PASS_QUEUE_SPECIFIC_INCREMENT"
    return "NO_REGISTERED_QUEUE_GAIN"


def evaluate(jobs: list[Job], output: Path,
             *, expected_holdout: int = EXPECTED_HELDOUT) -> dict:
    """Causal, prequential heldout evaluation with immutable per-job output."""
    diagnostic = [j for j in jobs if j.submit < CUTOFF]
    heldout = sorted(
        (j for j in jobs if j.submit >= CUTOFF),
        key=lambda j: (j.submit, j.job_id),
    )
    if len(heldout) != expected_holdout:
        raise AuditStop("Heldout target identity or count has changed")
    if expected_holdout == EXPECTED_HELDOUT and len(diagnostic) != EXPECTED_DIAGNOSTIC:
        raise AuditStop("Original diagnostic target count changed")
    queue_index = QueueSnapshots(jobs)
    histories = HistoricalStarts(jobs)
    queries = {
        (j.submit - delay, j.queue)
        for j in heldout
        for delay in (PREVIOUS_SECONDS, LATEST_SECONDS)
    }
    sweep = queue_index.sweep(queries)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "original-heldout-predictions.jsonl"
    if destination.exists():
        raise AuditStop("Cannot overwrite first original per-job predictions")
    primary = Metrics()
    per_queue: dict[str, Metrics] = defaultdict(Metrics)
    per_group: dict[str, Metrics] = defaultdict(Metrics)
    queue_hashed = {j.queue: sha256(j.queue.encode("utf-8")).hexdigest()
                    for j in jobs}
    with destination.open("w", encoding="utf-8") as handle:
        for job in heldout:
            estimates, feature = frozen_predictions(
                job, queue_index, sweep, histories
            )
            primary.add(job, estimates, feature)
            per_queue[job.queue].add(job, estimates, feature)
            per_group[job.size_group].add(job, estimates, feature)
            record = {
                "job_id": job.job_id,
                "submit_seconds": str(job.submit),
                "queue_sha256": queue_hashed[job.queue],
                "requested_size_group": job.size_group,
                "observed_wait_seconds": str(job.wait),
                "forecast_seconds": {k: str(v) for k, v in estimates.items()},
                "absolute_errors_seconds": {
                    k: str(abs(v - job.wait)) for k, v in estimates.items()
                },
                "features": feature,
                "registered_split": "heldout",
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    summary = primary.summary()
    maes = {key: Decimal(val) for key, val in summary["mae_seconds"].items()}
    verdict = registered_gate(maes)
    return {
        "decision": verdict,
        "split_cutoff_seconds": str(CUTOFF),
        "diagnostic_target_count": len(diagnostic),
        "heldout_target_count": len(heldout),
        "heldout": summary,
        "heldout_by_queue_sha256": {
            queue_hashed[name]: stats.summary()
            for name, stats in sorted(per_queue.items())
        },
        "heldout_by_requested_processor_group": {
            key: per_group[key].summary() for key in ("small", "medium", "large")
        },
        "independent_binary_and_sweep_oracles_agree": True,
        "all_requested_snapshots_checked": len(queries),
        "no_new_predictor_parameters_fit": True,
        "strict_pre_origin_feature_cutoff_s": "60",
        "live_online_history_from_previously_started_jobs_only": True,
        "original_predictions_file": {
            "name": destination.name,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination.read_bytes()).hexdigest(),
        },
    }


def first_run(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Cannot overwrite FIRST RP-E011-P01 original prediction run")
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "protocol": PROTOCOL,
        "decision": "STOP_SOURCE_OR_FEATURE_AUDIT",
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "source_code_commit": os.environ.get("GITHUB_SHA"),
        "environment": platform.platform(),
        "original_D02_schema_verdict_unchanged": "DATASET_SCHEMA_REJECTED",
        "original_RP_E010_negative_unchanged": True,
        "source": None,
        "forecast": None,
        "errors": [],
        "scalar_C_validated": False,
        "physics_law_tested": False,
        "new_lean_theorem": False,
    }
    try:
        raw, provider = download_exact()
        if len(raw) != SOURCE_SIZE or sha256(raw).hexdigest() != SOURCE_SHA:
            raise AuditStop("Source SHA256 or original byte length mismatch")
        jobs, provenance = parse_pinned_jobs(raw)
        report["source"] = {**provider, **provenance}
        study = evaluate(jobs, output)
        report["forecast"] = study
        report["decision"] = study["decision"]
    except (AuditStop, SourceBlocked, ValueError, KeyError, UnicodeError) as exc:
        report["errors"].append({
            "stage": "source-or-registered-model-gate",
            "reason": f"{type(exc).__name__}: {str(exc)[:350]}",
        })
    finally:
        (output / "RP-E011-P01.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = first_run(args.output)
    print(json.dumps({
        "protocol": PROTOCOL,
        "decision": result["decision"],
        "heldout_jobs": (result["forecast"] or {}).get("heldout_target_count"),
        "mae_seconds": ((result["forecast"] or {}).get("heldout") or {}).get("mae_seconds"),
        "errors": result["errors"],
    }, sort_keys=True))
    if result["decision"] == "STOP_SOURCE_OR_FEATURE_AUDIT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
