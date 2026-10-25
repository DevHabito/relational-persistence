"""RP-E010 observational forecasting adversarial tests (synthetic fixtures ONLY).

No result about HPC2N is inferred from these fixtures; original third-party
data remain unexamined until a preregistered hosted first-run evaluation.
"""

from __future__ import annotations

from decimal import Decimal
import json

import pytest

from experiments.rp_e010_observational_forecast import (
    HISTORY_SECONDS, LATEST_SECONDS, MIN_CASES, PRIOR_SECONDS,
    THRESHOLD_RATIO, DecimalMetrics, Job, RecordedEvents, cohort,
    evaluate_data, feature_at_origin, first_run, frozen_gate,
    parse_verified_jobs, processor_group, stringify_row,
)


def job(ident: int, arrival: str, wait: str, *, runtime="1",
        processors=1, status=1) -> Job:
    return Job(ident, Decimal(arrival), Decimal(wait),
               Decimal(runtime), processors, status)


def test_binsearch_and_event_sweep_have_identical_strict_boundary_rules():
    records = [
        job(1, "10", "100"),
        job(2, "20", "0"),
        job(3, "50", "200"),
    ]
    events = RecordedEvents(records)
    points = [Decimal(x) for x in (0, 10, 20, 21, 25, 50, 110, 111, 250, 251)]
    swept = events.swept_backlog(list(reversed(points)) + points)
    assert {str(t): swept[t] for t in points} == {
        "0": 0, "10": 0, "20": 1, "21": 1, "25": 1,
        "50": 1, "110": 2, "111": 1, "250": 1, "251": 0,
    }
    assert all(events.binary_backlog(t) == swept[t] for t in points)


def test_past_start_history_is_inclusive_low_and_exclusive_high():
    items = [
        job(1, "1300", "100"),  # starts exactly t-3600, admissible
        job(2, "4800", "139"),  # starts t-61, admissible
        job(3, "4940", "0"),    # starts t-60, strictly excluded
        job(4, "5000", "9999"), # current target cannot enter its features
    ]
    events = RecordedEvents(items)
    count, total = events.history(Decimal(5000))
    assert count == 2
    assert total == Decimal(239)
    assert HISTORY_SECONDS == 3600
    assert LATEST_SECONDS == 60
    assert PRIOR_SECONDS == 120


def test_unchanged_frozen_feature_does_not_include_own_future_wait_label():
    base = [
        job(1, "1300", "100"), job(2, "4800", "139"),
        job(3, "5000", "300"),
    ]
    altered = base[:-1] + [job(3, "5000", "300000")]
    previous = Decimal(5000) - PRIOR_SECONDS
    latest = Decimal(5000) - LATEST_SECONDS
    calculated = []
    for items in (base, altered):
        source = RecordedEvents(items)
        swept = source.swept_backlog([previous, latest])
        calculated.append(feature_at_origin(Decimal(5000), source, swept))
    assert calculated[0] == calculated[1]


def test_frozen_predictions_divide_by_measured_history_start_rate_not_physical_capacity():
    source = RecordedEvents([
        job(1, "1300", "100"),
        job(2, "4800", "139"),
        job(3, "4801", "200"),  # additional live backlog at both snapshots
    ])
    origin = Decimal(5000)
    features = feature_at_origin(
        origin, source,
        source.swept_backlog([origin - 120, origin - 60])
    )
    assert features is not None
    assert features["historical_starts"] == 2
    assert features["observed_B_starts_per_second"] == Decimal(2) / Decimal(3540)
    assert features["q_previous"] == 2
    assert features["q_latest"] == 1
    assert features["model_predictions"]["static"] == Decimal(1770)
    assert features["model_predictions"]["trend"] == 0
    assert features["model_predictions"]["history"] == Decimal("119.5")


def test_future_source_cannot_replace_observed_queue_at_previous_snapshots():
    original = RecordedEvents([job(1, "100", "200")])
    changed = RecordedEvents([
        job(1, "100", "200"),
        job(2, "1000", "9999999"),
    ])
    points = [Decimal(150), Decimal(175)]
    assert original.swept_backlog(points) == changed.swept_backlog(points)


def test_swapped_oracle_count_is_detected(monkeypatch):
    source = RecordedEvents([
        job(1, "1300", "100"), job(2, "4800", "139"),
    ])
    origin = Decimal(5000)
    real = source.swept_backlog([origin - 120, origin - 60])
    corrupted = dict(real)
    corrupted[origin - 60] += 1
    with pytest.raises(ValueError, match="oracles disagree"):
        feature_at_origin(origin, source, corrupted)


def test_bad_zero_historical_starts_drops_target_before_prediction():
    source = RecordedEvents([job(1, "5000", "500")])
    origin = Decimal(5000)
    assert feature_at_origin(
        origin, source, source.swept_backlog([origin - 120, origin - 60])
    ) is None


def test_no_event_can_be_negative_or_precede_submit_if_wait_valid():
    source = RecordedEvents([
        job(1, "0", "0"), job(2, "0", "0"), job(3, "0", "100")
    ])
    points = [Decimal(-1), Decimal(0), Decimal("0.1"), Decimal(100)]
    assert [source.binary_backlog(t) for t in points] == [0, 0, 1, 1]
    assert source.swept_backlog(points)[Decimal(100)] == 1


def test_chronological_split_is_unaffected_by_wait_labels_and_later_tuning():
    jobs = [
        job(1, "0", "1"),
        job(2, "4000", "200"),
        job(3, "10000", "0"),
        job(4, "20000", "300"),
    ]
    _, _, initial = cohort(jobs)
    updated = [job(i.job_id, str(i.submit), str(i.wait + 100))
               for i in jobs]
    _, _, modified = cohort(updated)
    assert initial == modified
    assert Decimal(initial["chronological_cutoff_seconds"]) == Decimal(14000)


def test_frozen_dual_control_gate_requires_both_comparators():
    good = {
        "static": Decimal("100"),
        "history": Decimal("90"),
        "trend": Decimal("80"),
    }
    assert frozen_gate(good) == "PASS_OBSERVATIONAL_INCREMENT"
    assert frozen_gate({**good, "trend": Decimal("89")}) == (
        "NO_REGISTERED_OBSERVATIONAL_GAIN"
    )
    assert frozen_gate({**good, "static": Decimal("0")}) == (
        "NO_REGISTERED_OBSERVATIONAL_GAIN"
    )
    assert frozen_gate({**good, "history": Decimal("0")}) == (
        "NO_REGISTERED_OBSERVATIONAL_GAIN"
    )
    assert THRESHOLD_RATIO == Decimal("0.90")


@pytest.mark.parametrize("bad", [
    {"static": Decimal("5"), "trend": Decimal("-1"), "history": Decimal("8")},
    {"static": Decimal("5"), "trend": Decimal("NaN"), "history": Decimal("8")},
    {"static": Decimal("5"), "trend": Decimal("Infinity"), "history": Decimal("8")},
])
def test_corrupt_or_nonfinite_source_errors_stop(bad):
    with pytest.raises(ValueError):
        frozen_gate(bad)


def test_missing_primary_control_is_not_silent():
    with pytest.raises(ValueError):
        frozen_gate({"static": Decimal(2), "trend": Decimal(1)})


def test_group_boundaries_follow_frozen_allocated_processors():
    assert processor_group(1) == processor_group(2) == "1..2"
    assert processor_group(3) == processor_group(16) == "3..16"
    assert processor_group(17) == ">16"
    with pytest.raises(ValueError):
        processor_group(0)


def test_decimal_metric_keeps_untrimmed_large_wait_and_zero_label():
    acc = DecimalMetrics(("static", "trend"))
    acc.append({
        "observed_wait_seconds": "0",
        "absolute_errors_seconds": {"static": "100000", "trend": "0"},
        "signed_errors_seconds": {"static": "100000", "trend": "0"},
    })
    acc.append({
        "observed_wait_seconds": "1000000",
        "absolute_errors_seconds": {"static": "999999", "trend": "1000000"},
        "signed_errors_seconds": {"static": "-999999", "trend": "-1000000"},
    })
    assert acc.summary()["jobs"] == 2
    assert acc.summary()["zero_wait_jobs"] == 1
    assert Decimal(acc.summary()["mae_seconds"]["static"]) == Decimal("549999.5")


def test_historical_predictor_never_uses_current_target_wait():
    items = [
        job(1, "1300", "100"), job(2, "4800", "139"),
        job(3, "5000", "10"),
    ]
    source = RecordedEvents(items)
    origin = Decimal(5000)
    feature = feature_at_origin(
        origin, source, source.swept_backlog([origin-120, origin-60])
    )
    a = stringify_row(items[2], "holdout", feature, Decimal(12))
    b = stringify_row(job(3, "5000", "999999"), "holdout", feature, Decimal(12))
    assert a["predictions_seconds"] == b["predictions_seconds"]
    assert a["absolute_errors_seconds"] != b["absolute_errors_seconds"]
    assert a["causal_snapshot_latest_seconds"] == "4940"


def test_lack_of_original_source_bytes_does_not_masquerade_as_pass(tmp_path):
    result = first_run(tmp_path / "original", raw_override=b"not a SWF")
    assert result["decision"] == "STOP_OBSERVATIONAL_AUDIT"
    assert result["original_results"] is None
    record = json.loads(
        (tmp_path / "original" / "RP-E010-P01-first-evaluation.json").read_text()
    )
    assert record["decision"] == "STOP_OBSERVATIONAL_AUDIT"
    assert record["errors"]


def test_source_identity_checked_before_parsing_even_valid_synthetic_swf():
    with pytest.raises(ValueError, match="Pinned external source"):
        parse_verified_jobs(b"; SWF 2.2\n" + b"1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18\n")


def test_first_run_is_never_replaced_even_by_negative_data(tmp_path):
    original = tmp_path / "study"
    original.mkdir()
    (original / "RP-E010-P01-first-evaluation.json").write_text("original")
    with pytest.raises(ValueError, match="overwrite"):
        first_run(original, raw_override=b"arbitrary")


def test_small_synthetic_scoring_works_without_claiming_empirical_result(
    tmp_path, monkeypatch
):
    from experiments import rp_e010_observational_forecast as study
    monkeypatch.setattr(study, "MIN_CASES", 1)
    # This fixture is a code check, NOT a real HPC trace or held-out result.
    items = [
        job(1, "1000", "4900"),      # starts 5900, historical at origin 6000
        job(2, "6000", "0"),        # diagnostic
        job(3, "13500", "3300"),   # starts 16800, historical at origin 17000
        job(4, "17000", "0"),      # heldout
    ]
    result = evaluate_data(items, {"missing_wait_count": 0}, tmp_path / "test")
    assert result["diagnostic"]["jobs"] == 1
    assert result["heldout"]["jobs"] == 1
    assert result["two_queue_oracles_agree_all_origins"] is True
    assert result["source_unknown_wait_records"] == 0
    assert (tmp_path / "test" / "holdout-original-predictions.jsonl").exists()
    assert result["decision"] in (
        "PASS_OBSERVATIONAL_INCREMENT",
        "NO_REGISTERED_OBSERVATIONAL_GAIN",
    )
    # A fixture's positive or negative classification has NO research meaning.
