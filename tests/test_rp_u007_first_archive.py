"""Immutable original RP-U007 negative source decision with full role replay."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from experiments import rp_u007_forecast_core as core
from experiments import rp_u007_observed_source as run

ROOT=Path("docs/results/RP-U007-P01-first-run")
FIRST_BYTES=28031
FIRST_SHA="546c127e480422408278f87b816067bb9a0f8070531a1a5fbaabba4fb97a3fe8"


def original() -> dict:
    b=(ROOT/"summary.json").read_bytes()
    assert len(b)==FIRST_BYTES
    assert sha256(b).hexdigest()==FIRST_SHA
    return json.loads(b)


def test_original_file_hash_all_three_calibrations_and_holdout_order():
    j=original()
    assert j["study"]=="RP-U007-P01"
    assert j["protocol_only_commit"]==core.PROTOCOL_SHA
    assert j["source_commit"]=="4951b1331cd1b2c8ca2e03017b7c5a5a32bf4534"
    assert j["original_workflow_run_id"]=="44206490270"
    assert j["status"]=="RP_U007_COMPLETE_NO_CONFIRMED_INCREMENT"
    assert j["original_sources_all_valid"] is True
    assert len(j["calibration"])==3
    assert [x["regime"] for x in j["calibration"]]==list(core.CALIBRATION_ORDER)
    assert len(j["holdouts"])==12
    assert [(x["regime"],x["initial_jobs"]) for x in j["holdouts"]]==[
        (p.regime,p.initial_jobs) for p in core.HOLDOUTS
    ]
    # Original 89 files, plus an independently authored archive index.
    assert len([p for p in ROOT.rglob("*") if p.is_file()
                and p.name != "archive-index.json"])==89


def test_all_original_service_and_monitor_roles_are_replayed():
    j=original()
    intervals={}
    total_samples=0
    for i,entry in enumerate([*j["calibration"],*j["holdouts"]]):
        calibration=i<3
        label=(f"calibration-{i+1:02d}-{entry['regime']}" if calibration
               else f"holdout-{i-2:02d}-{entry['regime']}")
        folder=ROOT/label
        assert len([x for x in folder.iterdir() if x.is_file()])==(
            5 if calibration else 6
        )
        for filename,key in (
            ("service-events.jsonl","event_file_sha256"),
            ("monitor-samples.jsonl","monitor_file_sha256"),
            ("controller-injector.json","controller_file_sha256"),
        ):
            assert sha256((folder/filename).read_bytes()).hexdigest()==entry[key]
        events=run.jsonl(folder/"service-events.jsonl")
        monitors=run.jsonl(folder/"monitor-samples.jsonl")
        verification=core.validate_events(
            events,initial=entry["initial_jobs"],calibration=calibration)
        core.validate_samples(
            monitors,
            total=entry["initial_jobs"] if calibration else entry["initial_jobs"]+6,
            enable_ns=verification["enable_ns"],
        )
        assert entry["service_process_exitcode"]==0
        assert entry["monitor_process_exitcode"]==0
        assert verification["enable_ns"]==entry["server_enable_ns"]
        assert entry["complete_job_count"]==verification["completed_count"]
        assert entry["valid_original_trial"] is True
        total_samples+=len(monitors)
        if calibration:
            interval=core.calibrated_interval(events)
            intervals[entry["regime"]]=interval
            assert interval==entry["calibrated_interval_seconds"]
        else:
            landmark=verification["enable_ns"]+core.LANDMARK_NS
            assert landmark==entry["registered_landmark_ns"]
            latest=core.select_landmark_sample(
                monitors,enable_ns=verification["enable_ns"],
                expected_accepted=entry["initial_jobs"]+4
            )
            assert latest==entry["prelandmark_live_sample"]
            assert entry["accepted_by_landmark"]==entry["initial_jobs"]+4
            assert entry["prediction_created_ns"]<verification[
                "last_batch_last_accept_ns"]
            assert verification["first_two_post_batches_last_accept_ns"]<=landmark
            assert verification["last_batch_last_accept_ns"]>landmark
            original_target=core.measured_recovery(
                monitors,landmark_ns=landmark,
                final_batch_accept_ns=verification["last_batch_last_accept_ns"]
            )
            assert original_target==entry["measured_recovery_from_landmark_seconds"]
            predicted=core.original_forecasts(
                intervals[entry["regime"]],
                accepted_at_landmark=entry["accepted_by_landmark"],
                observed_outstanding=latest["accepted"]-latest["completed"],
            )
            assert predicted==entry["predictions"]
            pre=folder/"prediction-prelast.json"
            assert sha256(pre.read_bytes()).hexdigest()==entry[
                "prediction_prelast_file_sha256"]
            pre_json=json.loads(pre.read_bytes())
            assert pre_json["model_predictions"]==predicted
            assert pre_json["source_monitored_health"]==latest
            assert pre_json["model_computed_time_ns"]==entry["prediction_created_ns"]
    assert total_samples==544


def test_original_negative_result_and_3_2_7_comparison_is_immutable():
    j=original()
    ready=dict(j)
    ready["status"]="RP_U007_SOURCE_READY_FOR_EVALUATION"
    recomputed=core.evaluate_original(ready)
    assert recomputed["status"]==j["status"]
    assert recomputed["strict_state_wins"]==j["strict_state_wins"]==3
    assert recomputed["registered_increment_confirmed_within_host"] is False
    assert recomputed["input_capacity_MAE_seconds"]==j[
        "input_capacity_MAE_seconds"]
    assert recomputed["observed_state_MAE_seconds"]==j[
        "observed_state_MAE_seconds"]
    assert j["input_capacity_MAE_seconds"]==0.012734143750000008
    assert j["observed_state_MAE_seconds"]==0.012586991583333353
    assert 0 < j["relative_MAE_reduction"] < .02
    outcomes=j["all_individual_comparisons"]
    winners=sum(x["state_strictly_better"] for x in outcomes)
    ties=sum(x["input_capacity_absolute_error_seconds"]==
             x["measured_state_absolute_error_seconds"] for x in outcomes)
    losers=12-winners-ties
    assert (winners,losers,ties)==(3,2,7)
    assert j["physical_network_repair_or_biological_recovery_measured"] is False


def test_archive_index_identifies_unique_source_and_archive_history():
    index=json.loads((ROOT/"archive-index.json").read_text(encoding="utf-8"))
    assert index["first_original_summary_sha256"]==FIRST_SHA
    assert index["first_original_summary_size_bytes"]==FIRST_BYTES
    assert index["first_original_source_files"]==89
    assert index["first_original_trial_count"]==15
    assert index["first_original_monitored_source_samples"]==544
    assert index["first_source_github_artifact_id"]==14383966850
    assert index["strict_state_wins"]==3
    assert index["strict_state_losses"]==2
    assert index["observed_equals_predicted_backlog_count"]==7
    assert index["first_source_status"]=="RP_U007_COMPLETE_NO_CONFIRMED_INCREMENT"
