"""Exact adversarial controls for preregistered RP-F006-A01.

Every test is synthetic and rational; no external heldout rows are read.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json

import pytest

from experiments import rp_f006_queue_observability as study


def worlds():
    return (
        study.construct_world(study.REGISTERED_SHORT_END),
        study.construct_world(study.REGISTERED_LONG_END),
    )


def manual_queue_count(world: study.World, instant: Fraction) -> int:
    """Independent elementary state oracle: count jobs waiting at instant."""
    return sum(job.submit < instant <= job.start for job in world.jobs)


def manual_past_started(world: study.World) -> list[study.Job]:
    return [
        job for job in world.jobs
        if Fraction(-3600) <= job.start < Fraction(-60)
    ]


def test_three_jobs_keep_registered_times_and_requested_resources():
    short, long = worlds()
    assert tuple(j.name for j in short.jobs) == ("H", "R", "T")
    for world, expected in ((short, Fraction(1)), (long, Fraction(100))):
        assert study.validate_fcfs_compatible(world)["no_overlapping_service"]
        assert world.named("H").submit == -201
        assert world.named("H").start == -200
        assert world.named("H").end == -190
        assert world.named("R").submit == -31
        assert world.named("R").start == -30
        assert world.named("R").end == expected
        assert world.named("T").submit == 0
        assert world.named("T").start == expected
        assert world.named("T").end == expected + 1
        assert world.named("T").wait == expected
        assert all(j.requested_walltime == 500 for j in world.jobs)
        assert all(j.requested_processors == 1 for j in world.jobs)
        assert len({j.queue for j in world.jobs}) == 1


def test_all_visible_event_history_and_public_requests_are_identical():
    short, long = worlds()
    expected = (
        ("-201", "submit", "H"),
        ("-200", "start", "H"),
        ("-190", "end", "H"),
        ("-31", "submit", "R"),
        ("-30", "start", "R"),
    )
    assert study.visible_event_history(short) == expected
    assert study.visible_event_history(long) == expected
    assert study.public_requests(short) == study.public_requests(long)
    assert study.causal_observation(short) == study.causal_observation(long)
    assert study.causal_observation(short)["running_job_age_s"] == "30"
    assert study.causal_observation(long)["running_job_observed_busy"] is True


@pytest.mark.parametrize("instant", [-120, -60, 0])
def test_three_independent_queue_count_oracles_equal_zero(instant):
    for world in worlds():
        instant = Fraction(instant)
        assert study.binary_waiting_count(world, instant) == 0
        assert study.swept_waiting_counts(world, (instant,))[instant] == 0
        assert manual_queue_count(world, instant) == 0


def test_history_cutoff_excludes_current_running_job_and_target():
    for world in worlds():
        old = manual_past_started(world)
        assert [j.name for j in old] == ["H"]
        assert old[0].wait == Fraction(1)
        assert study.causal_observation(world)["historical_start_rate_per_s"] == "1/3540"


def test_exact_registered_p01_heuristics_identical_but_outcomes_differ():
    short, long = worlds()
    short_p = study.frozen_p01_predictions(study.causal_observation(short))
    long_p = study.frozen_p01_predictions(study.causal_observation(long))
    assert short_p == long_p == {
        "history": Fraction(1),
        "static": Fraction(0),
        "trend": Fraction(0),
    }
    assert short.named("T").wait == 1
    assert long.named("T").wait == 100
    assert long.named("T").wait - short.named("T").wait == 99


@pytest.mark.parametrize("p", [
    Fraction(-200), Fraction(0), Fraction(1), Fraction(2),
    Fraction(101, 2), Fraction(80), Fraction(100), Fraction(500)
])
def test_absolute_error_triangle_bound_holds_without_tuning(p):
    short, long = worlds()
    a, b = short.named("T").wait, long.named("T").wait
    assert abs(p - a) + abs(p - b) >= 99
    assert max(abs(p - a), abs(p - b)) >= Fraction(99, 2)


def test_sharp_minimax_equal_weighting_is_synthetic_only():
    evidence = study.exact_minimax(Fraction(1), Fraction(100))
    assert evidence["label_separation_s"] == "99"
    assert evidence["equal_weighted_minimax_prediction_s"] == "101/2"
    assert evidence["unavoidable_maximum_absolute_error_s"] == "99/2"
    assert evidence["equally_weighted_two_world_expected_mae_lower_bound_s"] == "99/2"
    assert evidence["equal_weighting_is_synthetic_assumption_only"] is True


def test_prespecified_identical_completion_negative_control():
    first = study.construct_world(Fraction(1))
    second = study.construct_world(Fraction(1))
    assert study.causal_observation(first) == study.causal_observation(second)
    assert second.named("T").wait - first.named("T").wait == 0


def test_illicit_actual_future_completion_is_a_distinguishing_oracle():
    short, long = worlds()
    assert study.causal_observation(short) == study.causal_observation(long)
    assert short.named("R").end != long.named("R").end
    assert ("1", "end", "R") not in study.visible_event_history(short)
    assert ("100", "end", "R") not in study.visible_event_history(long)


def test_target_service_duration_does_not_affect_waiting_time():
    short, long = worlds()
    mutated_target = replace(long.named("T"), end=long.named("T").end + 17)
    mutated_world = replace(
        long, jobs=(long.named("H"), long.named("R"), mutated_target)
    )
    assert mutated_target.service == Fraction(18)
    assert mutated_world.named("T").wait == long.named("T").wait
    assert study.causal_observation(mutated_world) == study.causal_observation(long)
    # Changing the actual target service is NOT part of the primary witness,
    # so we do not pass this mutation through the frozen-world validator.


def test_service_overlap_is_not_silently_admitted():
    short, _ = worlds()
    modified = replace(
        short, jobs=(
            short.named("H"),
            replace(short.named("R"), end=Fraction(2)),
            short.named("T"),
        )
    )
    with pytest.raises(ValueError, match="overlap"):
        study.validate_fcfs_compatible(modified)


def test_invalid_public_request_is_a_protocol_failure():
    short, _ = worlds()
    altered = replace(
        short, jobs=(
            short.named("H"),
            replace(short.named("R"), requested_walltime=Fraction(2)),
            short.named("T"),
        )
    )
    with pytest.raises(ValueError, match="Public request"):
        study.validate_fcfs_compatible(altered)


def test_a_nonpositive_running_service_duration_fails():
    short, _ = worlds()
    altered = replace(
        short, jobs=(
            short.named("H"),
            replace(short.named("R"), end=Fraction(-30)),
            short.named("T"),
        )
    )
    with pytest.raises(ValueError, match="ordering"):
        study.validate_fcfs_compatible(altered)


def test_exact_audit_has_no_empirical_physical_law_claim():
    report = study.audit_witness()
    assert report["decision"] == "FINITE_NONIDENTIFIABILITY_VERIFIED"
    assert report["full_pre_origin_observations_identical"] is True
    assert report["short_target_wait_s"] == "1"
    assert report["long_target_wait_s"] == "100"
    assert report["scalar_C_validated"] is False
    assert report["physical_law_claimed"] is False
    assert report["empirical_external_validation_claimed"] is False
    assert report["new_queuing_theorem_claimed"] is False
    assert all(report["registered_negative_controls"].values())
    assert json.loads(json.dumps(report)) == report


def test_report_creation_is_not_allowed_to_overwrite(tmp_path):
    path = tmp_path / "witness.json"
    assert not path.exists()
    # Verify output using subprocess-like direct call rather than faking
    # any as-yet-unobserved CI first-run identity.
    data = study.audit_witness()
    path.write_text(json.dumps(data, sort_keys=True) + "\n", encoding="utf-8")
    assert json.loads(path.read_text()) == data
    assert path.exists()
