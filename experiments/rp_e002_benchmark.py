"""RP-E002-A01: preregistered observational forecast experiment.

This does not estimate physical response latency, B, I, or B/(I*tau).
Observed METR-LA targets are never inspected during parameter selection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

PROTOCOL = "RP-E002-A01"
EXPECTED_MD5 = "d3adaa79856bf610f25558fc242c7190"
EXPECTED_SENSORS = 207
HORIZONS = (3, 6, 12)
LAMBDA_GRID = (0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.0)
SEED = 20261023
EMBARGO = 12
MIN_GAIN = 0.01


class DataQualityError(ValueError):
    """Fail closed rather than silently repair invalid experimental input."""


@dataclass(frozen=True)
class Observations:
    times: tuple[datetime, ...]
    sensor_ids: tuple[str, ...]
    speeds: np.ndarray


def digest(path: Path, name: str = "sha256") -> str:
    hasher = hashlib.new(name)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            hasher.update(block)
    return hasher.hexdigest()


def load_speeds(path: Path, expected_sensors: int = EXPECTED_SENSORS) -> Observations:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream)
        try:
            header = next(rows)
        except StopIteration as exc:
            raise DataQualityError("Empty speeds CSV") from exc
        ids = tuple(value.strip() for value in header[1:])
        if len(ids) != expected_sensors or len(set(ids)) != len(ids) or not all(ids):
            raise DataQualityError("Wrong, empty or repeated sensor columns")
        times: list[datetime] = []
        speeds: list[list[float]] = []
        prev = None
        for row_number, row in enumerate(rows, 2):
            if len(row) != len(header):
                raise DataQualityError(f"Malformed row width: {row_number}")
            try:
                time = datetime.fromisoformat(row[0].strip())
            except ValueError as exc:
                raise DataQualityError(f"Invalid timestamp: row {row_number}") from exc
            if time.tzinfo is not None:
                raise DataQualityError("Do not assume a timezone; this CSV must use naive timestamps")
            if prev is not None and time - prev != timedelta(minutes=5):
                raise DataQualityError(f"Unexpected timestamp cadence: row {row_number}")
            prev = time
            values = []
            for raw in row[1:]:
                try:
                    value = float(raw) if raw.strip() else float("nan")
                except ValueError as exc:
                    raise DataQualityError(f"Nonnumeric speed: row {row_number}") from exc
                if math.isinf(value) or (math.isfinite(value) and value < 0):
                    raise DataQualityError(f"Negative/infinite speed: row {row_number}")
                values.append(value)
            times.append(time)
            speeds.append(values)
    if len(times) < 200:
        raise DataQualityError("Insufficient time series")
    return Observations(tuple(times), ids, np.asarray(speeds, dtype=np.float64))


def external_adjacency(
    ids: tuple[str, ...], sensor_ids_path: Path, distances_path: Path,
) -> tuple[np.ndarray, dict]:
    external_ids = tuple(
        value.strip() for value in sensor_ids_path.read_text(encoding="utf-8-sig").strip().split(",")
    )
    if len(set(external_ids)) != len(external_ids) or set(ids) != set(external_ids):
        raise DataQualityError("Traffic sensor IDs disagree with external graph")
    index = {sensor: i for i, sensor in enumerate(ids)}
    distance = np.full((len(ids), len(ids)), np.inf)
    with distances_path.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"from", "to", "cost"}.issubset(reader.fieldnames or []):
            raise DataQualityError("Graph must contain from,to,cost")
        for row in reader:
            origin, destination = row["from"].strip(), row["to"].strip()
            if origin not in index or destination not in index:
                continue
            try:
                cost = float(row["cost"])
            except (ValueError, TypeError) as exc:
                raise DataQualityError("Nonnumeric graph distance") from exc
            if not math.isfinite(cost) or cost < 0:
                raise DataQualityError("Negative or invalid graph distance")
            i, j = index[origin], index[destination]
            if math.isfinite(distance[i, j]) and distance[i, j] != cost:
                raise DataQualityError("Contradictory repeated graph distances")
            distance[i, j] = cost
    finite = distance[np.isfinite(distance)]
    if finite.size == 0:
        raise DataQualityError("No available graph costs")
    std = float(np.std(finite))
    if std <= 0:
        raise DataQualityError("Graph cost scale is zero")
    with np.errstate(over="ignore"):
        graph = np.exp(-np.square(distance / std))
    graph[~np.isfinite(graph)] = 0.0
    graph[graph < 0.1] = 0.0
    np.fill_diagonal(graph, 0.0)
    valid_rows = int(np.count_nonzero(np.any(graph > 0, axis=1)))
    if valid_rows < len(ids) // 2:
        raise DataQualityError("Graph has insufficient nonempty neighbor rows")
    return graph, {
        "directed_nonzero_edges": int(np.count_nonzero(graph)),
        "vertices_with_neighbors": valid_rows,
        "graph_scale_from_external_costs": std,
        "distance_count": int(finite.size),
        "graph_provenance": "DCRNN directed Gaussian distance kernel, threshold 0.1",
    }


def boundaries(length: int) -> tuple[int, int]:
    train_end = length * 7 // 10
    validation_end = length * 8 // 10
    if validation_end - train_end < 50 or length - validation_end < 50:
        raise DataQualityError("Insufficient split support")
    return train_end, validation_end


def origins(start: int, end: int, length: int) -> np.ndarray:
    first = start + EMBARGO
    last_exclusive = min(end - EMBARGO, length - max(HORIZONS))
    if first >= last_exclusive:
        raise DataQualityError("No usable forecast origins after fixed embargo")
    return np.arange(first, last_exclusive)


def slots(times: tuple[datetime, ...]) -> np.ndarray:
    return np.fromiter(
        (time.weekday() * 288 + time.hour * 12 + time.minute // 5 for time in times),
        dtype=np.int64,
        count=len(times),
    )


def fit_seasonal(values: np.ndarray, encoded_slots: np.ndarray, train_end: int) -> np.ndarray:
    valid = np.isfinite(values[:train_end]) & (values[:train_end] > 0)
    n = values.shape[1]
    counts = np.zeros((2016, n), dtype=np.int64)
    sums = np.zeros((2016, n), dtype=np.float64)
    row, col = np.nonzero(valid)
    np.add.at(counts, (encoded_slots[row], col), 1)
    np.add.at(sums, (encoded_slots[row], col), values[row, col])
    per_sensor_n = valid.sum(axis=0)
    if not np.all(per_sensor_n > 0):
        raise DataQualityError("A sensor has no training observations")
    fallback = np.where(valid, values[:train_end], 0).sum(axis=0) / per_sensor_n
    return np.divide(sums, counts, out=np.broadcast_to(fallback, sums.shape).copy(), where=counts > 0)


def neighbors(current: np.ndarray, graph: np.ndarray, *, zero_valid: bool = False) -> np.ndarray:
    if current.ndim != 2 or graph.shape != (current.shape[1], current.shape[1]):
        raise DataQualityError("Graph/observation shape mismatch")
    valid = np.isfinite(current) & (current >= 0 if zero_valid else current > 0)
    source = np.where(valid, current, 0.0)
    total = source @ graph.T
    weights = valid.astype(float) @ graph.T
    return np.divide(total, weights, out=source.copy(), where=weights > 0)


def metrics(prediction, target, current, *, zero_valid: bool = False) -> dict:
    if prediction.shape != target.shape or current.shape != target.shape:
        raise DataQualityError("Misaligned forecasts and targets")
    valid = np.isfinite(target) & np.isfinite(current)
    valid &= ((target >= 0) & (current >= 0)) if zero_valid else ((target > 0) & (current > 0))
    if not np.all(np.isfinite(prediction[valid])):
        raise DataQualityError("Nonfinite forecast in evaluated mask")
    counts = valid.sum(axis=0)
    if not np.all(counts > 0):
        raise DataQualityError("At least one sensor has no eligible evaluation target")
    errors = np.where(valid, np.abs(prediction - target), 0.0)
    per_sensor = errors.sum(axis=0) / counts
    n = int(valid.sum())
    return {
        "sensor_balanced_mae": float(per_sensor.mean()),
        "pooled_mae": float(errors.sum() / n),
        "pooled_rmse": float(np.sqrt(np.square(errors).sum() / n)),
        "eligible_pairs": n,
        "valid_fraction": float(n / valid.size),
        "sensor_mae_min": float(np.min(per_sensor)),
        "sensor_mae_median": float(np.median(per_sensor)),
        "sensor_mae_max": float(np.max(per_sensor)),
    }


def select_lambda(current: np.ndarray, spatial: np.ndarray, target: np.ndarray) -> float:
    return min(
        (metrics((1 - value) * current + value * spatial, target, current)["sensor_balanced_mae"], value)
        for value in LAMBDA_GRID
    )[1]


def experiment(
    observed: Observations, graph: np.ndarray, hashes: dict[str, str], graph_report: dict,
) -> dict:
    if graph.shape != (len(observed.sensor_ids), len(observed.sensor_ids)):
        raise DataQualityError("Graph dimensions inconsistent with sensor columns")
    if not np.all(np.isfinite(graph)) or np.any(graph < 0):
        raise DataQualityError("Invalid graph weights")
    n = len(observed.times)
    train_end, val_end = boundaries(n)
    encoded = slots(observed.times)
    season = fit_seasonal(observed.speeds, encoded, train_end)
    permutation = np.random.default_rng(SEED).permutation(len(observed.sensor_ids))
    placebo_graph = graph[np.ix_(permutation, permutation)]

    train_val_origins = origins(train_end, val_end, n)
    current = observed.speeds[train_val_origins]
    spatial = neighbors(current, graph)
    placebo_spatial = neighbors(current, placebo_graph)
    tuned: dict[int, tuple[float, float]] = {}
    for horizon in HORIZONS:
        target = observed.speeds[train_val_origins + horizon]
        tuned[horizon] = (
            select_lambda(current, spatial, target),
            select_lambda(current, placebo_spatial, target),
        )

    test_origins = origins(val_end, n, n)
    current = observed.speeds[test_origins]
    spatial = neighbors(current, graph)
    placebo_spatial = neighbors(current, placebo_graph)
    spatial_with_zero = neighbors(current, graph, zero_valid=True)
    placebo_with_zero = neighbors(current, placebo_graph, zero_valid=True)
    outcomes: dict[str, dict] = {}
    sensitivity: dict[str, dict] = {}
    for horizon in HORIZONS:
        lam, lam_perm = tuned[horizon]
        target = observed.speeds[test_origins + horizon]
        seasonal_forecast = season[encoded[test_origins + horizon]]
        forecasts = {
            "persistence": current,
            "seasonal": seasonal_forecast,
            "graph": (1 - lam) * current + lam * spatial,
            "permuted_graph": (1 - lam_perm) * current + lam_perm * placebo_spatial,
        }
        report = {name: metrics(pred, target, current) for name, pred in forecasts.items()}
        best_base = min(report["persistence"]["sensor_balanced_mae"], report["seasonal"]["sensor_balanced_mae"])
        graph_mae = report["graph"]["sensor_balanced_mae"]
        placebo_mae = report["permuted_graph"]["sensor_balanced_mae"]
        if best_base <= 0 or placebo_mae <= 0:
            raise DataQualityError("Nonpositive preregistered comparison denominator")
        gain_base = (best_base - graph_mae) / best_base
        gain_placebo = (placebo_mae - graph_mae) / placebo_mae
        report["relative_gain_vs_best_temporal_baseline"] = float(gain_base)
        report["relative_gain_vs_permuted_graph"] = float(gain_placebo)
        report["lambda_graph"] = lam
        report["lambda_permuted_graph"] = lam_perm
        report["passes_both"] = gain_base >= MIN_GAIN and gain_placebo >= MIN_GAIN
        outcomes[str(horizon)] = report

        zero_forecasts = {
            "persistence": current,
            "seasonal": seasonal_forecast,
            "graph": (1 - lam) * current + lam * spatial_with_zero,
            "permuted_graph": (1 - lam_perm) * current + lam_perm * placebo_with_zero,
        }
        sensitivity[str(horizon)] = {
            name: metrics(pred, target, current, zero_valid=True)
            for name, pred in zero_forecasts.items()
        }

    return {
        "protocol": PROTOCOL,
        "decision": (
            "H1_restricted_predictive_gain" if all(row["passes_both"] for row in outcomes.values())
            else "H0_not_rejected"
        ),
        "capacity_noise_latency_identification": "NOT_IDENTIFIED",
        "data_kind": "observed_traffic_speeds; predictions_are_model_outputs",
        "horizons_steps": HORIZONS,
        "lambda_grid": LAMBDA_GRID,
        "validation_choices": {str(h): {"graph": values[0], "permuted_graph": values[1]}
                               for h, values in tuned.items()},
        "test_metrics": outcomes,
        "zero_inclusive_sensitivity_fixed_lambdas": sensitivity,
        "test_forecast_origins": len(test_origins),
        "train_end": train_end,
        "validation_end": val_end,
        "gap_steps": EMBARGO,
        "rows": n,
        "sensors": len(observed.sensor_ids),
        "start_timestamp": observed.times[0].isoformat(),
        "end_timestamp": observed.times[-1].isoformat(),
        "nan_fraction": float(np.mean(np.isnan(observed.speeds))),
        "zero_fraction": float(np.mean(observed.speeds == 0)),
        "graph_audit": graph_report,
        "inputs_sha256": hashes,
        "git_sha": os.environ.get("GITHUB_SHA", "unavailable"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "speed_units": "provider-native; no unverified conversion",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speeds", type=Path, required=True)
    parser.add_argument("--sensor-ids", type=Path, required=True)
    parser.add_argument("--distances", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if digest(args.speeds, "md5") != EXPECTED_MD5:
        raise DataQualityError("Pinned Zenodo v5 METR-LA.csv MD5 mismatch; stop")
    paths = (args.speeds, args.sensor_ids, args.distances)
    checksums = {path.name: digest(path) for path in paths}
    observed = load_speeds(args.speeds)
    graph, audit = external_adjacency(observed.sensor_ids, args.sensor_ids, args.distances)
    result = experiment(observed, graph, checksums, audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"protocol": PROTOCOL, "decision": result["decision"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
