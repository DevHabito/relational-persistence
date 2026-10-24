"""RP-E006-P01: re-audit original train/test source bytes, then evaluate once.

The held-out test targets cannot enter model fitting; no attempt is made
to fit a physical law or estimate population-level effects.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from experiments.rp_e006_acquire import (
    PROTOCOL, ROLE_FILENAMES, SPLIT_REPETITIONS, SPLIT_SEEDS,
    audit_trial, cases_for_split, sha256,
)

MODELS = ("index_only", "constant", "queue_fluid", "tau_only", "load_only")


def load_object(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Not a JSON object: {path}")
    return obj


def validate_split(directory: Path, split: str, run_id: str,
                   source_sha: str, protocol_sha: str) -> tuple[list[dict], dict]:
    """Never accept archived metric columns without replaying their source."""
    provenance = load_object(directory / "provenance.json")
    report = load_object(directory / "summary.json")
    for evidence in (provenance, report):
        expected = {
            "protocol": PROTOCOL, "split": split,
            "source_commit": source_sha,
            "workflow_run_id": run_id,
            "protocol_sha256": protocol_sha,
            "trial_seed": SPLIT_SEEDS[split],
            "hardware_independence": "NOT_ESTABLISHED",
            "physical_law_test": "NOT_PERFORMED",
            "scheduled_trials": cases_for_split(split),
        }
        for name, value in expected.items():
            if evidence.get(name) != value:
                raise ValueError(f"{split}: metadata mismatch: {name}")
        if not str(evidence.get("python", "")).startswith("3.12."):
            raise ValueError(f"{split}: wrong Python runtime")
        if not str(evidence.get("platform", "")).startswith("Linux-"):
            raise ValueError(f"{split}: unregistered machine platform")
    if report.get("run_quality") != "PASS_ALL_RECORDED":
        raise ValueError(f"{split}: original run did not pass")
    expected_trials = cases_for_split(split)
    claimed = report.get("observations")
    if not isinstance(claimed, list) or len(claimed) != len(expected_trials):
        raise ValueError(f"{split}: missing or duplicated trial results")
    verified = []
    inventory = {}
    for spec, observation in zip(expected_trials, claimed):
        if observation.get("trial_id") != spec["trial_id"]:
            raise ValueError(f"{split}: trial order or identity mismatch")
        folder = directory / spec["trial_id"]
        for filename in ROLE_FILENAMES:
            source = folder / filename
            if not source.is_file():
                raise ValueError(f"{split}: missing original {spec['trial_id']}/{filename}")
            file_hash = sha256(source)
            if observation.get("file_sha256", {}).get(filename) != file_hash:
                raise ValueError(f"{split}: raw source has changed: {spec['trial_id']}/{filename}")
            inventory[f"{split}/{spec['trial_id']}/{filename}"] = file_hash
        reaudited = audit_trial(folder, spec, preserve_snapshot=False)
        if reaudited != observation:
            raise ValueError(f"{split}: original claimed measurement does not replay")
        verified.append(reaudited)
    return verified, inventory


def finite_float(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{label}: a finite numeric value is required")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label}: a nonfinite measurement")
    return result


def value_of(row: dict, feature: str) -> float:
    if feature == "reciprocal_C":
        c = finite_float(row["candidate_C_inverse_s"], "C")
        if c <= 0:
            raise ValueError("The defined positive C is required")
        return 1 / c
    if feature == "tau":
        return finite_float(row["measured_tau_s"], "tau")
    if feature == "N":
        return finite_float(row["work_units"], "N")
    raise ValueError("Unsupported frozen feature")


def fit_linear(training: list[dict], feature: str) -> dict:
    """Single-regressor OLS with an intercept, fitted on train only."""
    if len(training) != 18:
        raise ValueError("Missing registered training block")
    xs = [value_of(row, feature) for row in training]
    ys = [finite_float(row["sampled_recovery_Y_s"], "train Y") for row in training]
    xmean = math.fsum(xs) / len(xs)
    ymean = math.fsum(ys) / len(ys)
    sxx = math.fsum((x - xmean) ** 2 for x in xs)
    if not math.isfinite(sxx) or sxx <= 1e-16:
        raise ValueError(f"Degenerate {feature} training variation")
    sxy = math.fsum((x - xmean) * (y - ymean) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = ymean - slope * xmean
    if not all(math.isfinite(z) for z in (slope, intercept)):
        raise ValueError("Invalid OLS fit")
    return {"feature": feature, "intercept": intercept, "slope": slope}


def fit_models(training: list[dict]) -> dict:
    if len(training) != 18:
        raise ValueError("Expected 18 train labels")
    average = math.fsum(
        finite_float(row["sampled_recovery_Y_s"], "train Y")
        for row in training
    ) / len(training)
    return {
        "index_only": fit_linear(training, "reciprocal_C"),
        "constant": {"mean": average},
        "queue_fluid": {"calibration": "unfitted backlog/(2*B)"},
        "tau_only": fit_linear(training, "tau"),
        "load_only": fit_linear(training, "N"),
    }


def predict(models: dict, row: dict) -> dict:
    result = {}
    for name in MODELS:
        parameters = models[name]
        if name == "constant":
            estimate = parameters["mean"]
        elif name == "queue_fluid":
            backlog = finite_float(row["last_pre_end_backlog"], "pre-end backlog")
            capacity = finite_float(row["calibrated_B_work_per_s"], "B")
            if capacity <= 0 or backlog < 0:
                raise ValueError("Undefined queue-based comparator")
            estimate = backlog / (2 * capacity)
        else:
            estimate = parameters["intercept"] + (
                parameters["slope"] * value_of(row, parameters["feature"])
            )
        if not math.isfinite(estimate):
            raise ValueError(f"{name}: nonfinite prediction")
        result[name] = max(0.0, estimate)
    return result


def score(test: list[dict], models: dict) -> dict:
    if len(test) != 9:
        raise ValueError("Expected nine held-out outcomes")
    predictions = []
    for row in test:
        estimates = predict(models, row)
        true_y = finite_float(row["sampled_recovery_Y_s"], "test Y")
        predictions.append({
            "trial_id": row["trial_id"],
            "work_units": row["work_units"],
            "scheduled_lag_ms": row["scheduled_lag_ms"],
            "B_work_per_s": row["calibrated_B_work_per_s"],
            "I_work_per_s": row["measured_I_work_per_s"],
            "tau_s": row["measured_tau_s"],
            "observed_recovery_s": true_y,
            "index_inverse_seconds": row["candidate_C_inverse_s"],
            "queue_at_pre_end": row["last_pre_end_backlog"],
            "predictions_s": estimates,
            "absolute_errors_s": {
                name: abs(value - true_y) for name, value in estimates.items()
            },
        })
    maes = {
        name: math.fsum(r["absolute_errors_s"][name] for r in predictions) / 9
        for name in MODELS
    }
    if not all(math.isfinite(val) and val >= 0 for val in maes.values()):
        raise ValueError("Invalid held-out error")
    wins_both = (
        maes["constant"] > 0 and maes["queue_fluid"] > 0
        and maes["index_only"] <= 0.9 * maes["constant"]
        and maes["index_only"] <= 0.9 * maes["queue_fluid"]
    )
    biases = {
        name: math.fsum(
            r["predictions_s"][name] - r["observed_recovery_s"]
            for r in predictions
        ) / 9 for name in MODELS
    }
    return {
        "decision": "PASS_PREDICTIVE_GAIN" if wins_both
        else "NO_REGISTERED_PREDICTIVE_GAIN",
        "primary_threshold": "MAE_C <= 0.9 * both MAE_constant and MAE_queue",
        "test_mae_seconds": maes,
        "test_mean_signed_bias_seconds": biases,
        "heldout_predictions": predictions,
        "test_samples": 9,
    }


def evaluate(directory: Path, repository_root: Path, run_id: str,
             source_sha: str) -> dict:
    protocol_sha = sha256(repository_root / "docs/preregistration/RP-E006-P01.md")
    errors = []
    observations = {}
    inventories = {}
    for split in ("train", "test"):
        try:
            observations[split], inventories[split] = validate_split(
                directory / f"rp-e006-p01-{split}", split,
                run_id, source_sha, protocol_sha,
            )
        except (ValueError, OSError, KeyError, TypeError, AssertionError) as error:
            errors.append({"split": split, "error": f"{type(error).__name__}: {error}"})
    response = {
        "protocol": PROTOCOL, "source_commit": source_sha,
        "workflow_run_id": run_id,
        "preregistration_sha256": protocol_sha,
        "expected_training_trials": 18, "expected_heldout_trials": 9,
        "replayed_training_trials": len(observations.get("train", [])),
        "replayed_heldout_trials": len(observations.get("test", [])),
        "source_sha256": {key: value for part in inventories.values()
                          for key, value in part.items()},
        "errors": errors, "models": None, "heldout_scoring": None,
        "decision": "STOP_INSTRUMENTATION",
        "physical_law_test": "NOT_PERFORMED",
        "external_hardware_replication": "NOT_ESTABLISHED",
    }
    if errors:
        return response
    try:
        models = fit_models(observations["train"])
        scored = score(observations["test"], models)
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as error:
        response["errors"] = [{
            "stage": "model", "error": f"{type(error).__name__}: {error}"
        }]
        response["decision"] = "STOP_MODEL_IDENTIFICATION"
        return response
    response["models"] = models
    response["heldout_scoring"] = scored
    response["decision"] = scored["decision"]
    return response


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    result = evaluate(args.input, project, args.run_id, args.source_sha)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "RP-E006-P01.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": result["decision"], "train": result["replayed_training_trials"],
        "test": result["replayed_heldout_trials"], "errors": result["errors"],
        "mae": result["heldout_scoring"]["test_mae_seconds"]
        if result["heldout_scoring"] else None,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
