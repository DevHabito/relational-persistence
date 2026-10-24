"""RP-E007-P01: prospectively fixed static vs two-sample backlog forecast.

Scientific verdict derives exclusively from newly acquired RP-E007
source files. Historical RP-E006 records cannot be loaded as E007
measurements. Reuses the frozen E006 instrumentation *schema*, not data.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from experiments.rp_e004_p02 import read_jsonlines
from experiments.rp_e006_evaluate import finite_float, validate_split
from experiments.rp_e006_acquire import sha256

PROTOCOL = "RP-E007-P01"
GAP_LIMIT_NS = 150_000_000
FROZEN_THRESHOLD_RATIO = 0.90


def require_integer(number: object, label: str) -> int:
    if type(number) is not int or number < 0:
        raise ValueError(f"Invalid nonnegative integer {label}")
    return number


def pre_end_pair(samples: list[dict], end_ns: int) -> tuple[dict, dict]:
    """Only the last two recorded samples whose observation precedes end."""
    end_ns = require_integer(end_ns, "injector end")
    prior = [row for row in samples if row["observed_ns"] <= end_ns]
    if len(prior) < 2:
        raise ValueError("Fewer than two original pre-end monitor records")
    previous, latest = prior[-2:]
    for row in (previous, latest):
        for name in ("observed_ns", "server_snapshot_ns",
                     "queued", "active", "completed"):
            require_integer(row[name], name)
        if row["server_snapshot_ns"] > row["observed_ns"]:
            raise ValueError("Service timestamp later than observation")
    t0 = previous["observed_ns"]
    t1 = latest["observed_ns"]
    if not 0 <= t0 < t1 <= end_ns:
        raise ValueError("Invalid two-point observation ordering")
    gap = t1 - t0
    age = end_ns - t1
    if gap > GAP_LIMIT_NS or age > GAP_LIMIT_NS:
        raise ValueError("Pre-end observation gap/age exceeds frozen limit")
    return previous, latest


def predict_from_source(samples: list[dict], end_ns: int,
                        capacity_B: float) -> dict:
    """Unfitted finite backlog forecast, then its frozen linear trend."""
    b = finite_float(capacity_B, "calibrated B")
    if b <= 0:
        raise ValueError("Positive calibrated throughput required")
    prev, last = pre_end_pair(samples, end_ns)
    t0, t1 = prev["observed_ns"], last["observed_ns"]
    q0 = prev["queued"] + prev["active"]
    q1 = last["queued"] + last["active"]
    slope = (q1 - q0) * 1_000_000_000 / (t1 - t0)
    age_s = (end_ns - t1) / 1_000_000_000
    extrapolated = max(0.0, q1 + slope * age_s)
    static = max(0.0, q1 / (2 * b))
    trend = max(0.0, extrapolated / (2 * b))
    if not all(math.isfinite(v) for v in (slope, age_s, extrapolated, static, trend)):
        raise ValueError("Nonfinite registered trend forecast")
    return {
        "previous_pre_end_ns": t0,
        "latest_pre_end_ns": t1,
        "injector_end_ns": end_ns,
        "previous_backlog": q0,
        "latest_backlog": q1,
        "latest_sample_age_s": age_s,
        "observed_backlog_slope_units_per_second": slope,
        "extrapolated_backlog_at_origin": extrapolated,
        "prediction_static_s": static,
        "prediction_trend_s": trend,
    }


def audit_block(directory: Path, split: str, run_id: str,
                source_sha: str, e006_sha: str) -> tuple[list[dict], dict]:
    """E006 raw trial audit first, independently of either predictor."""
    rows, hashes = validate_split(
        directory, split, run_id, source_sha, e006_sha
    )
    audited = []
    for row in rows:
        folder = directory / row["trial_id"]
        samples = read_jsonlines(folder / "monitor-samples.jsonl")
        pred = predict_from_source(
            samples, row["injection_end_ns"],
            row["calibrated_B_work_per_s"],
        )
        if (pred["latest_pre_end_ns"] != row["last_pre_end_observed_ns"]
                or pred["latest_backlog"] != row["last_pre_end_backlog"]
                or pred["injector_end_ns"] >=
                row["first_post_end_observed_ns"]):
            raise ValueError(f"{row['trial_id']}: features differ from frozen origin")
        y = finite_float(row["sampled_recovery_Y_s"], "independent Y")
        if y < 0:
            raise ValueError("Negative recovery outcome")
        audited.append({
            "trial_id": row["trial_id"],
            "work_units": row["work_units"],
            "scheduled_lag_ms": row["scheduled_lag_ms"],
            "source_monitor_sha256": sha256(folder / "monitor-samples.jsonl"),
            "observed_recovery_s": y,
            **pred,
        })
    return audited, hashes


def score(training: list[dict], test: list[dict]) -> dict:
    """Only secondary constant uses training Y; static/trend are unfitted."""
    if len(training) != 18 or len(test) != 9:
        raise ValueError("Require all 18 historical-independent train and 9 new test rows")
    mean_train = math.fsum(row["observed_recovery_s"] for row in training) / 18
    results = []
    for row in test:
        y = finite_float(row["observed_recovery_s"], "test Y")
        preds = {
            "static": row["prediction_static_s"],
            "two_sample_trend": row["prediction_trend_s"],
            "train_constant": mean_train,
        }
        errors = {k: abs(finite_float(v, k) - y) for k, v in preds.items()}
        results.append({**row, "predictions_s": preds, "absolute_errors_s": errors})
    maes = {
        model: math.fsum(x["absolute_errors_s"][model] for x in results) / 9
        for model in ("static", "two_sample_trend", "train_constant")
    }
    passed = (
        maes["static"] > 0
        and maes["two_sample_trend"] <= FROZEN_THRESHOLD_RATIO * maes["static"]
    )
    return {
        "decision": "PASS_TREND_INCREMENT" if passed
        else "NO_REGISTERED_TREND_GAIN",
        "frozen_threshold_ratio": FROZEN_THRESHOLD_RATIO,
        "heldout_n": 9, "train_n": 18,
        "train_constant_s": mean_train,
        "heldout_mae_s": maes,
        "heldout_trial_predictions": results,
        "scope": "unfitted classical queue-state extrapolation only",
    }


def evaluate(source_root: Path, project_root: Path,
             run_id: str, source_sha: str) -> dict:
    if not run_id or not source_sha:
        raise ValueError("New GitHub experiment ID and commit required")
    protocol_sha = sha256(project_root / "docs/preregistration/RP-E007-P01.md")
    source_schema_sha = sha256(project_root / "docs/preregistration/RP-E006-P01.md")
    data = {}
    hashes = {}
    errors = []
    for split in ("train", "test"):
        try:
            data[split], hashes[split] = audit_block(
                source_root / f"rp-e007-p01-{split}",
                split, run_id, source_sha, source_schema_sha,
            )
        except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
            errors.append({
                "block": split,
                "reason": f"{type(error).__name__}: {error}",
            })
    report = {
        "protocol": PROTOCOL,
        "preregistration_sha256": protocol_sha,
        "reused_instrumentation_protocol_sha256": source_schema_sha,
        "new_source_commit": source_sha,
        "new_workflow_run_id": run_id,
        "original_training_trials_audited": len(data.get("train", [])),
        "original_heldout_trials_audited": len(data.get("test", [])),
        "verified_original_role_file_count": sum(map(len, hashes.values())),
        "original_source_sha256": {name: digest
                                  for block in hashes.values()
                                  for name, digest in block.items()},
        "errors": errors,
        "scoring": None,
        "decision": "STOP_INSTRUMENTATION",
        "historical_rp_e006_data_reused": False,
        "new_lean_theorem": False,
        "physical_law_test": "NOT_PERFORMED",
        "hardware_independence": "NOT_ESTABLISHED",
    }
    if errors:
        return report
    try:
        outcome = score(data["train"], data["test"])
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        report["errors"] = [{
            "block": "scoring",
            "reason": f"{type(error).__name__}: {error}",
        }]
        return report
    report["scoring"] = outcome
    report["decision"] = outcome["decision"]
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    decision = evaluate(args.input, root, args.run_id, args.source_sha)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "RP-E007-P01.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": decision["decision"], "errors": decision["errors"],
        "n_train": decision["original_training_trials_audited"],
        "n_test": decision["original_heldout_trials_audited"],
        "mae": decision["scoring"]["heldout_mae_s"]
        if decision["scoring"] else None,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
