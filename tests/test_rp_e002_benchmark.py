"""Regression tests for RP-E002-A01, using synthetic fixtures ONLY.

Passing these tests must not be presented as an observational result.
"""

import csv
from dataclasses import replace
from datetime import datetime, timedelta

import numpy as np
import pytest

from experiments.rp_e002_benchmark import (
    EMBARGO,
    HORIZONS,
    DataQualityError,
    Observations,
    boundaries,
    digest,
    experiment,
    external_adjacency,
    fit_seasonal,
    load_speeds,
    metrics,
    neighbors,
    origins,
    slots,
)


def fixture_data(n=540, sensors=3):
    rng = np.random.default_rng(13)
    times = tuple(datetime(2012, 3, 1) + timedelta(minutes=5 * i) for i in range(n))
    speeds = rng.uniform(15, 67, size=(n, sensors))
    ids = tuple(f"sensor_{i}" for i in range(sensors))
    return Observations(times, ids, speeds)


def graph():
    return np.array([[0.0, 0.8, 0.0], [0.4, 0.0, 0.4], [0.0, 0.8, 0.0]])


def run_fixture(data):
    return experiment(data, graph(), {"fixture_only": "synthetic"}, {"synthetic": True})


def test_chronological_split_and_12_step_embargo():
    train, valid = boundaries(1000)
    assert (train, valid) == (700, 800)
    va = origins(train, valid, 1000)
    te = origins(valid, 1000, 1000)
    assert va[0] == train + EMBARGO
    assert te[0] == valid + EMBARGO
    assert va[-1] + max(HORIZONS) < valid
    assert te[-1] + max(HORIZONS) < 1000


def test_neighbor_average_and_zero_semantics():
    x = np.array([[10.0, 20.0, 30.0], [10.0, 0.0, 30.0]])
    np.testing.assert_allclose(neighbors(x, graph())[0], [20, 20, 20])
    np.testing.assert_allclose(neighbors(x, graph())[1], [10, 20, 30])
    np.testing.assert_allclose(neighbors(x, graph(), zero_valid=True)[1], [0, 20, 0])


def test_zero_graph_lambda_reproduces_current_observation():
    current = np.array([[12.0, 17.0, 25.0]])
    pred = (1.0 - 0.0) * current + 0.0 * neighbors(current, graph())
    np.testing.assert_array_equal(pred, current)


def test_sensor_order_relabeling_equivariance():
    x = np.array([[12.0, 18.0, 25.0], [30.0, 17.0, 35.0]])
    indices = np.array([2, 0, 1])
    actual = neighbors(x[:, indices], graph()[np.ix_(indices, indices)])
    np.testing.assert_allclose(actual, neighbors(x, graph())[:, indices])


def test_training_seasonal_excludes_all_later_data():
    obs = fixture_data()
    encoded = slots(obs.times)
    train, _ = boundaries(len(obs.times))
    original = fit_seasonal(obs.speeds, encoded, train)
    edited = obs.speeds.copy()
    edited[train:] = 900
    np.testing.assert_allclose(original, fit_seasonal(edited, encoded, train))


def test_lambda_is_unaffected_by_test_labels():
    obs = fixture_data()
    first = run_fixture(obs)
    changed = obs.speeds.copy()
    _, valid = boundaries(len(obs.times))
    changed[valid + EMBARGO :] /= 2
    other = run_fixture(replace(obs, speeds=changed))
    assert first["validation_choices"] == other["validation_choices"]
    assert first["train_end"] == other["train_end"]


def test_test_target_changes_metric_but_not_fitted_lambda():
    obs = fixture_data()
    baseline = run_fixture(obs)
    edited = obs.speeds.copy()
    edited[-40:] += 25
    other = run_fixture(replace(obs, speeds=edited))
    assert baseline["validation_choices"] == other["validation_choices"]
    assert baseline["test_metrics"]["12"]["persistence"] != other["test_metrics"]["12"]["persistence"]


def test_sensor_balanced_mae_is_not_pooled_mae():
    pred = np.array([[10.0, 30.0], [10.0, 30.0], [10.0, 30.0]])
    target = np.array([[12.0, 0.0], [12.0, 20.0], [12.0, 0.0]])
    result = metrics(pred, target, pred)
    assert result["sensor_balanced_mae"] == 6.0
    assert result["pooled_mae"] == 4.0
    assert result["eligible_pairs"] == 4


def test_zero_inclusive_sensitivity_does_not_reselect_lambdas():
    obs = fixture_data()
    values = obs.speeds.copy()
    values[330:390, 1] = 0.0
    result = run_fixture(replace(obs, speeds=values))
    for horizon in HORIZONS:
        assert str(horizon) in result["zero_inclusive_sensitivity_fixed_lambdas"]
        assert (
            result["zero_inclusive_sensitivity_fixed_lambdas"][str(horizon)]["persistence"]["eligible_pairs"]
            >= result["test_metrics"][str(horizon)]["persistence"]["eligible_pairs"]
        )


def test_no_physical_index_claim_is_generated():
    result = run_fixture(fixture_data())
    assert result["capacity_noise_latency_identification"] == "NOT_IDENTIFIED"
    assert result["decision"] in {"H1_restricted_predictive_gain", "H0_not_rejected"}
    assert result["data_kind"].startswith("observed_traffic_speeds")


def test_csv_rejects_irregular_cadence_and_duplicate_sensors(tmp_path):
    path = tmp_path / "speeds.csv"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["timestamp", "a", "b", "c"])
        for index in range(205):
            minute = index * 5 + (1 if index == 150 else 0)
            writer.writerow([datetime(2012, 3, 1) + timedelta(minutes=minute), 10, 15, 20])
    with pytest.raises(DataQualityError, match="cadence"):
        load_speeds(path, expected_sensors=3)
    path.write_text(path.read_text().replace("a,b,c", "a,b,b", 1))
    with pytest.raises(DataQualityError, match="sensor"):
        load_speeds(path, expected_sensors=3)


def test_external_graph_fails_on_sensor_id_mismatch(tmp_path):
    ids = tmp_path / "ids.txt"
    ids.write_text("a,b,c")
    distances = tmp_path / "distances.csv"
    distances.write_text("from,to,cost\na,b,10\nb,c,5\nc,a,3\n")
    matrix, report = external_adjacency(("a", "b", "c"), ids, distances)
    assert matrix.shape == (3, 3)
    assert report["directed_nonzero_edges"] > 0
    assert np.count_nonzero(np.diag(matrix)) == 0
    ids.write_text("a,b,bad")
    with pytest.raises(DataQualityError, match="sensor IDs"):
        external_adjacency(("a", "b", "c"), ids, distances)


def test_invalid_target_is_masked_and_empty_sensor_is_rejected():
    forecast = np.array([[10.0, 20.0], [10.0, 20.0]])
    target = np.array([[12.0, np.nan], [10.0, 21.0]])
    assert metrics(forecast, target, forecast)["eligible_pairs"] == 3
    with pytest.raises(DataQualityError, match="no eligible"):
        metrics(forecast, np.full_like(target, np.nan), forecast)


def test_reproducible_sha256_streaming(tmp_path):
    file = tmp_path / "source.dat"
    file.write_bytes(b"scientific checksums\n")
    assert digest(file) == "87117afb6b61b98cce855847e0cd5535de6ac787181862461f166258f90858cf"
