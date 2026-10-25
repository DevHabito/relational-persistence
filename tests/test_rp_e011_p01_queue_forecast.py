"""Synthetic/adversarial-only tests for independently frozen RP-E011-P01.

These tests do not download or inspect any original external source rows.
"""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json

import pytest

from experiments import rp_e011_p01_queue_forecast as p01
from experiments.rp_e011_jsspp_source import SourceBlocked


D = Decimal


def job(number: int, submit: int, wait: int,
        queue: str = "a", requested: int = 1) -> p01.Job:
    return p01.Job(number, D(submit), D(wait), D(requested), queue)


def queries(jobs: list[p01.Job]) -> dict:
    index = p01.QueueSnapshots(jobs)
    sample = {(job.submit - lag, job.queue)
              for job in jobs for lag in (p01.PREVIOUS_SECONDS,
                                            p01.LATEST_SECONDS)}
    return index.sweep(sample)


def test_original_provenance_locked_before_prediction():
    p01.validate_prior_d04_archive()
    assert p01.SOURCE_SIZE == 59_430_886
    assert p01.EXPECTED_DIAGNOSTIC == 303_210
    assert p01.EXPECTED_HELDOUT == 169_189
    assert p01.GAIN_RATIO == D("0.90")


def test_immutable_source_hash_mismatch_prevents_parser_access(monkeypatch):
    def forbidden():
        raise AssertionError("source mismatches cannot parse D04 archive")
    monkeypatch.setattr(p01, "validate_prior_d04_archive", forbidden)
    with pytest.raises(p01.AuditStop, match="byte identity"):
        p01.parse_pinned_jobs(b"deliberately corrupted source")


def test_zero_wait_tied_events_obey_strict_event_boundary():
    events = p01.QueueSnapshots([job(1, 100, 300), job(2, 250, 0)])
    snapshots = {
        (D(100), "a"), (D(101), "a"), (D(250), "a"),
        (D(251), "a"), (D(400), "a"), (D(401), "a"),
    }
    sweep = events.sweep(snapshots)
    expected = {100: 0, 101: 1, 250: 1, 251: 1, 400: 1, 401: 0}
    for t, count in expected.items():
        assert events.binary("a", D(t)) == sweep[(D(t), "a")] == count


def test_queue_isolation_in_both_independent_backlog_oracles():
    jobs = [job(1, 0, 500, "a"), job(2, 0, 500, "b"),
            job(3, 10, 20, "a")]
    snapshots = {(D(15), "a"), (D(15), "b"), (D(40), "a"), (D(40), "b")}
    states = p01.QueueSnapshots(jobs)
    sweep = states.sweep(snapshots)
    assert sweep[(D(15), "a")] == states.binary("a", D(15)) == 2
    assert sweep[(D(15), "b")] == states.binary("b", D(15)) == 1
    assert sweep[(D(40), "a")] == 1
    assert sweep[(D(40), "b")] == 1


def test_no_prediction_of_a_target_uses_its_own_future_wait():
    early = job(1, 10, 20)
    target_a = job(2, 1000, 1)
    target_b = job(2, 1000, 50_000)
    states_a = p01.QueueSnapshots([early, target_a])
    states_b = p01.QueueSnapshots([early, target_b])
    origin = {(D(880), "a"), (D(940), "a")}
    prediction_a, features_a = p01.frozen_predictions(
        target_a, states_a, states_a.sweep(origin),
        p01.HistoricalStarts([early, target_a])
    )
    prediction_b, features_b = p01.frozen_predictions(
        target_b, states_b, states_b.sweep(origin),
        p01.HistoricalStarts([early, target_b])
    )
    assert prediction_a == prediction_b
    assert features_a == features_b
    assert prediction_a["history"] == D(20)


def test_earlier_heldout_starts_are_valid_future_online_history():
    first = job(2, 1000, 70)
    later = job(3, 1400, 0)
    history = p01.HistoricalStarts([first, later])
    assert history.historical_wait_median("a", "small", D(940)) == 0
    assert history.historical_wait_median("a", "small", D(1340)) == 70


def test_requested_processor_group_history_is_prior_only():
    jobs = [job(i + 1, 100 + i * 10, i + 1, requested=1)
            for i in range(16)]
    jobs.append(job(50, 50, 500, requested=100))
    history = p01.HistoricalStarts(jobs)
    assert history.historical_wait_median("a", "small", D(1000)) == D("8.5")
    assert history.historical_wait_median("a", "large", D(1000)) == D("8.5")
    assert history.historical_wait_median("a", "large", D(60)) == 0


def test_even_median_and_historical_rate_window_bounds():
    records = [job(1, 0, 20), job(2, 0, 30)]
    history = p01.HistoricalStarts(records)
    assert history.historical_wait_median("a", "small", D(50)) == D(25)
    assert history.queue_started_count("a", D(20), D(30)) == 1
    assert history.queue_started_count("a", D(20), D(31)) == 2


def test_no_past_queue_starts_uses_same_historical_fallback_for_all_models():
    target = job(2, 100, 300)
    indices = p01.QueueSnapshots([target])
    keys = {(target.submit - lag, "a")
            for lag in (p01.PREVIOUS_SECONDS, p01.LATEST_SECONDS)}
    model, evidence = p01.frozen_predictions(
        target, indices, indices.sweep(keys),
        p01.HistoricalStarts([target])
    )
    assert evidence["zero_past_start_fallback"] is True
    assert model == {"history": D(0), "static": D(0), "trend": D(0)}


def test_algorithm_disagreement_stops_instead_of_adjusting_count():
    target = job(2, 1000, 2)
    index = p01.QueueSnapshots([target])
    keys = {(D(880), "a"), (D(940), "a")}
    sweep = index.sweep(keys)
    sweep[(D(880), "a")] += 1
    with pytest.raises(p01.AuditStop, match="oracles disagree"):
        p01.frozen_predictions(
            target, index, sweep, p01.HistoricalStarts([target])
        )


def test_predetermined_two_comparator_positive_and_negative_decisions():
    assert p01.registered_gate({
        "trend": D(89), "static": D(100), "history": D(100)
    }) == "PASS_QUEUE_SPECIFIC_INCREMENT"
    assert p01.registered_gate({
        "trend": D(95), "static": D(100), "history": D(100)
    }) == "NO_REGISTERED_QUEUE_GAIN"
    assert p01.registered_gate({
        "trend": D(50), "static": D(100), "history": D(50)
    }) == "NO_REGISTERED_QUEUE_GAIN"
    assert p01.registered_gate({
        "trend": D(0), "static": D(0), "history": D(0)
    }) == "NO_REGISTERED_QUEUE_GAIN"


def test_nonfinite_metric_is_stop_not_negative_result():
    with pytest.raises(p01.AuditStop, match="Invalid primary error"):
        p01.registered_gate({
            "history": D(1), "static": D(2), "trend": D("Infinity")
        })


def test_synthetic_small_complete_holdout_records_all_results(monkeypatch, tmp_path):
    monkeypatch.setattr(p01, "CUTOFF", D(1000))
    jobs = [
        job(1, 0, 100, "a", 1),
        job(2, 200, 1000, "b", 8),
        job(3, 1100, 60, "a", 1),
        job(4, 1300, 2, "b", 8),
    ]
    folder = tmp_path / "first"
    result = p01.evaluate(jobs, folder, expected_holdout=2)
    assert result["heldout_target_count"] == 2
    assert result["diagnostic_target_count"] == 2
    assert result["heldout"]["jobs"] == 2
    assert set(result["heldout"]["mae_seconds"]) == set(p01.MODELS)
    assert result["decision"] in (
        "NO_REGISTERED_QUEUE_GAIN", "PASS_QUEUE_SPECIFIC_INCREMENT"
    )
    file_path = folder / "original-heldout-predictions.jsonl"
    lines = file_path.read_text().splitlines()
    assert len(lines) == 2
    assert sha256(file_path.read_bytes()).hexdigest() == result[
        "original_predictions_file"]["sha256"]
    assert all(json.loads(line)["registered_split"] == "heldout"
               for line in lines)
    with pytest.raises(p01.AuditStop, match="overwrite"):
        p01.evaluate(jobs, folder, expected_holdout=2)


def test_original_external_access_blocked_archived_as_stop(monkeypatch, tmp_path):
    def blocked():
        raise SourceBlocked("fixture original source blocked")
    monkeypatch.setattr(p01, "download_exact", blocked)
    folder = tmp_path / "out"
    original = p01.first_run(folder)
    assert original["decision"] == "STOP_SOURCE_OR_FEATURE_AUDIT"
    assert original["forecast"] is None
    assert original["errors"]
    assert original["physics_law_tested"] is False
    assert json.loads((folder / "RP-E011-P01.json").read_text()) == original
    with pytest.raises(ValueError, match="overwrite"):
        p01.first_run(folder)


def test_size_bins_do_not_use_actual_allocated_processors():
    assert job(1, 0, 1, requested=2).size_group == "small"
    assert job(1, 0, 1, requested=3).size_group == "medium"
    assert job(1, 0, 1, requested=16).size_group == "medium"
    assert job(1, 0, 1, requested=17).size_group == "large"
