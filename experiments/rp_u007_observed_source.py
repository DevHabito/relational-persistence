"""RP-U007 first prospective held-out, variable-service source experiment.

Runs exactly three fresh capacity calibrations then 12 frozen holdout scenarios,
with source server, independent monitor process and controller/injector logs.
If any evidence gate fails, the first source result is INELIGIBLE, not positive.
No field network, independent hardware sensor or real-world biology is measured.
"""
from __future__ import annotations

import argparse
import asyncio
from hashlib import sha256
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import socket
import time

from experiments import rp_u007_forecast_core as core
from experiments.rp_u007_gated_service import run_service

PROTOCOL = Path("docs/preregistration/RP-U007-P01.md")
OUTPUT = Path("docs/results/RP-U007-P01-first-run")
STARTUP_DEADLINE = 5.0
DRAIN_DEADLINE = 6.0
RPC_TIMEOUT = 2.0
POLL_SECONDS = .012
MONITOR_START_BEFORE_ENABLE_SECONDS = .065
MONITOR_FOLLOWUP_AFTER_DRAIN_SECONDS = .16
PROCESS_JOIN = 4.0


def write_new(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise core.InvalidEvidence("ORIGINAL_SOURCE_FILE_EXISTS")
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise core.InvalidEvidence("MISSING_ORIGINAL_ROLE_LOG")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise core.InvalidEvidence("ORIGINAL_ROLE_LOG_IS_EMPTY")
    parsed = [json.loads(line) for line in lines]
    if any(not isinstance(row,dict) for row in parsed):
        raise core.InvalidEvidence("INVALID_ORIGINAL_EVENT_ROW")
    return parsed


def choose_port() -> int:
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1",0))
        return int(s.getsockname()[1])


async def rpc(port: int, operation: str,
              *, count: int | None = None) -> tuple[dict,int]:
    reader,writer=await asyncio.wait_for(
        asyncio.open_connection("127.0.0.1",port),timeout=RPC_TIMEOUT)
    try:
        body={"op":operation}
        if count is not None:
            body["count"]=count
        writer.write((json.dumps(body)+"\n").encode())
        await asyncio.wait_for(writer.drain(),timeout=RPC_TIMEOUT)
        raw=await asyncio.wait_for(writer.drain(),timeout=RPC_TIMEOUT) if False else None
        response_bytes=await asyncio.wait_for(reader.readline(),timeout=RPC_TIMEOUT)
        receipt=time.monotonic_ns()
        response=json.loads(response_bytes)
        if not isinstance(response,dict) or "error" in response:
            raise core.InvalidEvidence("SERVICE_RPC_REJECTED_"+operation.upper())
        return response,receipt
    finally:
        writer.close()
        await writer.wait_closed()


def synchronous_health(port:int) -> tuple[dict,int]:
    with socket.create_connection(("127.0.0.1",port),timeout=RPC_TIMEOUT) as s:
        s.settimeout(RPC_TIMEOUT)
        s.sendall(b'{"op":"health"}\n')
        with s.makefile("rb") as file:
            raw=file.readline()
        observed=time.monotonic_ns()
    response=json.loads(raw)
    if not isinstance(response,dict) or "error" in response:
        raise core.InvalidEvidence("ORIGINAL_MONITOR_HEALTH_REJECTED")
    return response,observed


def monitor_process(port:int,filename:str,stop:mp.synchronize.Event)->None:
    """Only read-only RPC; independent OS process, not an independent sensor."""
    path=Path(filename)
    try:
        with path.open("x",encoding="utf-8") as out:
            while not stop.is_set():
                health,receipt=synchronous_health(port)
                row={
                    "observed_ns":receipt,
                    "server_snapshot_ns":health["server_snapshot_ns"],
                    "queued":health["queued"],
                    "active":health["active"],
                    "accepted":health["accepted"],
                    "completed":health["completed"],
                    "available":health["available"],
                }
                out.write(json.dumps(row,sort_keys=True)+"\n")
                out.flush()
                time.sleep(POLL_SECONDS)
    except Exception as exc:
        with (path.parent/"monitor-failure.json").open("x",encoding="utf-8") as stream:
            stream.write(json.dumps({
                "error_type":type(exc).__name__,
                "failure":str(exc)[:180],
            },sort_keys=True)+"\n")
        raise


async def wait_until_ns(instant_ns: int) -> None:
    remaining=(instant_ns-time.monotonic_ns())/1e9
    if remaining>0:
        await asyncio.sleep(remaining)


async def await_startup(port:int)->None:
    deadline=time.monotonic()+STARTUP_DEADLINE
    while time.monotonic()<deadline:
        try:
            result,_=await rpc(port,"ping")
            if result=={"ready":True}:
                return
        except (OSError,RuntimeError,asyncio.TimeoutError,core.InvalidEvidence):
            await asyncio.sleep(.02)
    raise core.InvalidEvidence("NEW_SERVICE_PROCESS_NOT_READY")


def cleanup(process:mp.Process)->None:
    if process.is_alive():
        process.terminate()
    process.join(PROCESS_JOIN)
    if process.is_alive():
        process.kill()
        process.join(PROCESS_JOIN)


async def one_trial(folder:Path,*,regime:str,initial:int,ordinal:int,
                    calibration:bool,
                    service_interval:float|None=None)->dict:
    if folder.exists():
        raise core.InvalidEvidence("ORIGINAL_TRIAL_FOLDER_EXISTS")
    folder.mkdir(parents=True,exist_ok=False)
    if regime not in core.REGIMES:
        raise core.InvalidEvidence("UNKNOWN_ORIGINAL_SERVICE_REGIME")
    config={
        "study":core.PROTOCOL,
        "ordinal":ordinal,"regime":regime,"calibration":calibration,
        "initial_jobs":initial,
        "registered_future_batches":[] if calibration else [
            {"offset_from_enable_ms":t,"additional_jobs":2} for t in (40,80,160)
        ],
        "monitor_poll_nominal_ms":12,
        "worker_available_before_enable":False,
        "source_nominal_service_ms_options":list(core.REGIMES[regime]),
    }
    write_new(folder/"configuration.json",config)
    ctx=mp.get_context("spawn")
    port=choose_port()
    service=ctx.Process(target=run_service,
                        args=(port,str(folder/"service-events.jsonl"),regime))
    stop=ctx.Event()
    monitor=ctx.Process(target=monitor_process,
                        args=(port,str(folder/"monitor-samples.jsonl"),stop))
    service_started=False
    monitor_started=False
    try:
        service.start()
        service_started=True
        await await_startup(port)
        monitor.start()
        monitor_started=True
        await asyncio.sleep(MONITOR_START_BEFORE_ENABLE_SECONDS)
        batch_acks=[]
        pre_snapshot=None
        forecast=None
        feature_source=None
        prediction_stamp=None
        if calibration:
            enabled,enable_ack=await rpc(port,"enable")
            initial_ack,ack_ns=await rpc(port,"batch",count=initial)
        else:
            initial_ack,ack_ns=await rpc(port,"batch",count=initial)
            pre_snapshot,_=await rpc(port,"health")
            if (pre_snapshot["accepted"]!=initial
                    or pre_snapshot["completed"]!=0
                    or pre_snapshot["queued"]+pre_snapshot["active"]!=initial
                    or pre_snapshot["available"] is not False):
                raise core.InvalidEvidence("INITIAL_DISABLED_WORK_STATE_NOT_VALID")
            enabled,enable_ack=await rpc(port,"enable")
        enable_ns=enabled.get("server_enable_ns")
        if (enabled.get("enabled") is not True
                or type(enable_ns) is not int
                or enable_ack<enable_ns or
                initial_ack.get("accepted_total")!=initial):
            raise core.InvalidEvidence("INITIAL_OR_ENABLE_ACK_INVALID")
        landmark_ns=enable_ns+core.LANDMARK_NS
        if not calibration:
            for offset in (40_000_000,80_000_000):
                await wait_until_ns(enable_ns+offset)
                response,receipt=await rpc(port,"batch",count=2)
                batch_acks.append({
                    "scheduled_offset_ns":offset,"response":response,
                    "receipt_ns":receipt,
                })
                if receipt>landmark_ns:
                    raise core.InvalidEvidence("EARLY_BATCH_ARRIVED_AFTER_LANDMARK")
            await wait_until_ns(landmark_ns+4_000_000)
            # Only read monitor records already written at this actual time;
            # freeze selection against the landmark; no late data can enter.
            snapshot_source=jsonl(folder/"monitor-samples.jsonl")
            latest=core.select_landmark_sample(
                snapshot_source,enable_ns=enable_ns,
                expected_accepted=initial+core.EXPECTED_EARLY_ADDED_JOBS,
            )
            feature_source=latest
            forecast=core.original_forecasts(
                service_interval,
                accepted_at_landmark=initial+core.EXPECTED_EARLY_ADDED_JOBS,
                observed_outstanding=latest["accepted"]-latest["completed"],
            )
            prediction_stamp=time.monotonic_ns()
            if prediction_stamp>enable_ns+core.FORECAST_DEADLINE_NS:
                raise core.InvalidEvidence("PRE_FINAL_BATCH_PREDICTION_LATE")
            write_new(folder/"prediction-prelast.json",{
                "regime":regime,"initial_jobs":initial,
                "source_monitored_health":latest,
                "model_predictions":forecast,
                "model_computed_time_ns":prediction_stamp,
                "registered_landmark_ns":landmark_ns,
                "expected_final_batch_arrival_count":2,
                "access_to_future_service_completions":False,
            })
            if time.monotonic_ns()>enable_ns+core.FORECAST_DEADLINE_NS:
                raise core.InvalidEvidence("PRE_FINAL_BATCH_SOURCE_FILE_LATE")
            await wait_until_ns(enable_ns+core.FUTURE_BATCH_OFFSET_NS)
            final,response_time=await rpc(port,"batch",count=2)
            batch_acks.append({
                "scheduled_offset_ns":core.FUTURE_BATCH_OFFSET_NS,
                "response":final,"receipt_ns":response_time,
            })
            if response_time<=landmark_ns:
                raise core.InvalidEvidence("FINAL_BATCH_NOT_AFTER_LANDMARK")
        total=initial if calibration else initial+6
        finish_deadline=time.monotonic()+DRAIN_DEADLINE
        while time.monotonic()<finish_deadline:
            health,_=await rpc(port,"health")
            if (health["accepted"]==total and health["completed"]==total
                    and health["queued"]==0 and health["active"]==0):
                break
            await asyncio.sleep(.012)
        else:
            raise core.InvalidEvidence("SOURCE_WORK_NOT_DRAINED_BY_DEADLINE")
        await asyncio.sleep(MONITOR_FOLLOWUP_AFTER_DRAIN_SECONDS)
        stop.set()
        monitor.join(PROCESS_JOIN)
        if monitor.is_alive() or monitor.exitcode!=0:
            raise core.InvalidEvidence("MONITOR_PROCESS_DID_NOT_COMPLETE")
        shutdown,_=await rpc(port,"shutdown")
        if shutdown.get("shutdown") is not True:
            raise core.InvalidEvidence("SERVICE_SHUTDOWN_REJECTED")
        service.join(PROCESS_JOIN)
        if service.is_alive() or service.exitcode!=0:
            raise core.InvalidEvidence("SOURCE_PROCESS_DID_NOT_EXIT_CLEANLY")
        controller={
            "enable":enabled,
            "enable_ack_receipt_ns":enable_ack,
            "initial_batch":initial_ack,
            "initial_batch_receipt_ns":ack_ns,
            "pre_enable_health":pre_snapshot,
            "post_enable_batches":batch_acks,
            "prediction_file_written_before_final_batch":not calibration,
            "prediction_created_ns":prediction_stamp,
        }
        write_new(folder/"controller-injector.json",controller)
        service_events=jsonl(folder/"service-events.jsonl")
        samples=jsonl(folder/"monitor-samples.jsonl")
        event_validation=core.validate_events(
            service_events,initial=initial,calibration=calibration
        )
        if event_validation["enable_ns"]!=enable_ns:
            raise core.InvalidEvidence("SERVER_ENABLE_IDENTITY_CHANGED")
        core.validate_samples(samples,total=total,enable_ns=enable_ns)
        record={
            "regime":regime,"initial_jobs":initial,"ordinal":ordinal,
            "calibration":calibration,"valid_original_trial":True,
            "server_enable_ns":enable_ns,
            "complete_job_count":event_validation["completed_count"],
            "all_source_job_identity_verified":True,
            "event_file_sha256":digest(folder/"service-events.jsonl"),
            "monitor_file_sha256":digest(folder/"monitor-samples.jsonl"),
            "controller_file_sha256":digest(folder/"controller-injector.json"),
            "monitor_samples":len(samples),
            "service_events":len(service_events),
            "service_process_exitcode":service.exitcode,
            "monitor_process_exitcode":monitor.exitcode,
        }
        if calibration:
            record["calibrated_interval_seconds"]=core.calibrated_interval(
                service_events)
            if record["calibrated_interval_seconds"]<=0:
                raise core.InvalidEvidence("NONPOSITIVE_CALIBRATION_INTERVAL")
        else:
            if (event_validation["first_two_post_batches_last_accept_ns"] >
                    landmark_ns
                    or event_validation["last_batch_last_accept_ns"]<=landmark_ns):
                raise core.InvalidEvidence("INDEPENDENT_SOURCE_BATCH_TIMELINE_CHANGED")
            first_two=controller["post_enable_batches"][:2]
            if (any(x["receipt_ns"]>landmark_ns for x in first_two)
                    or controller["post_enable_batches"][2]["receipt_ns"]<=landmark_ns):
                raise core.InvalidEvidence("CONTROLLER_BATCH_LANDMARK_ORDER_CHANGED")
            expected_source=core.select_landmark_sample(
                samples,enable_ns=enable_ns,expected_accepted=initial+4)
            if expected_source!=feature_source:
                raise core.InvalidEvidence("PRE_SOURCE_FEATURE_SAMPLE_CHANGED")
            if prediction_stamp>=event_validation["last_batch_last_accept_ns"]:
                raise core.InvalidEvidence("PREDICTION_CREATED_AFTER_FINAL_ARRIVAL")
            measured=core.measured_recovery(
                samples,landmark_ns=landmark_ns,
                final_batch_accept_ns=event_validation["last_batch_last_accept_ns"],
            )
            if prediction_stamp>=landmark_ns+int(measured*1e9):
                raise core.InvalidEvidence("PREDICTION_CREATED_AFTER_RECOVERY")
            if forecast!=core.original_forecasts(
                    service_interval,accepted_at_landmark=initial+4,
                    observed_outstanding=feature_source["accepted"]-
                    feature_source["completed"]):
                raise core.InvalidEvidence("PRE_SOURCE_FORECAST_WAS_MODIFIED")
            record.update({
                "registered_landmark_ns":landmark_ns,
                "accepted_by_landmark":initial+4,
                "prelandmark_live_sample":feature_source,
                "prediction_created_ns":prediction_stamp,
                "final_batch_accept_ns":
                    event_validation["last_batch_last_accept_ns"],
                "measured_recovery_from_landmark_seconds":measured,
                "predictions":forecast,
                "prediction_prelast_file_sha256":digest(
                    folder/"prediction-prelast.json"),
            })
        write_new(folder/"trial-summary.json",record)
        return record
    finally:
        stop.set()
        if monitor_started:
            cleanup(monitor)
        if service_started:
            cleanup(service)


def run_first(folder:Path)->dict:
    if not os.environ.get("GITHUB_SHA") or not os.environ.get("GITHUB_RUN_ID"):
        raise core.InvalidEvidence("HOSTED_SOURCE_RUN_ID_AND_COMMIT_REQUIRED")
    if folder.exists():
        raise core.InvalidEvidence("FIRST_SOURCE_DIRECTORY_ALREADY_EXISTS")
    folder.mkdir(parents=True,exist_ok=False)
    source={
        "study":core.PROTOCOL,
        "protocol_only_commit":core.PROTOCOL_SHA,
        "source_commit":os.environ["GITHUB_SHA"],
        "original_workflow_run_id":os.environ["GITHUB_RUN_ID"],
        "original_protocol_sha256":digest(PROTOCOL),
        "platform":platform.platform(),
        "python_version":platform.python_version(),
        "calibration":[],
        "holdouts":[],
        "registered_calibration_order":list(core.CALIBRATION_ORDER),
        "registered_holdout_order":[
            {"regime":p.regime,"initial_jobs":p.initial_jobs}
            for p in core.HOLDOUTS
        ],
        "random_per_job_nominal_duration_from_os_entropy":True,
        "worker_restore_is_software_not_physical_network":True,
        "separate_monitor_process_uses_server_reported_counters":True,
        "original_sources_all_valid":False,
        "status":"RP_U007_MEASUREMENT_INVALID",
    }
    write_new(folder/"provenance.json",{
        key:source[key] for key in (
            "study","protocol_only_commit","source_commit",
            "original_workflow_run_id","original_protocol_sha256",
            "platform","python_version","registered_calibration_order",
            "registered_holdout_order",
        )
    })
    try:
        calibrations={}
        for i,regime in enumerate(core.CALIBRATION_ORDER,start=1):
            entry=asyncio.run(one_trial(
                folder/f"calibration-{i:02d}-{regime}",
                regime=regime,initial=core.CALIBRATION_TASKS,
                ordinal=i,calibration=True,
            ))
            calibrations[regime]=entry["calibrated_interval_seconds"]
            source["calibration"].append(entry)
        for i,spec in enumerate(core.HOLDOUTS,start=1):
            entry=asyncio.run(one_trial(
                folder/f"holdout-{i:02d}-{spec.regime}",
                regime=spec.regime,initial=spec.initial_jobs,
                ordinal=i,calibration=False,
                service_interval=calibrations[spec.regime],
            ))
            source["holdouts"].append(entry)
        source["original_sources_all_valid"]=True
        source["status"]="RP_U007_SOURCE_READY_FOR_EVALUATION"
        outcome=core.evaluate_original(source)
        source.update(outcome)
    except (OSError,RuntimeError,TypeError,ValueError,KeyError,TimeoutError,
            asyncio.TimeoutError,AssertionError) as exc:
        source["status"]="RP_U007_MEASUREMENT_INVALID"
        source["failure"]={
            "type":type(exc).__name__,"code":str(exc)[:225],
            "completed_calibrations":len(source["calibration"]),
            "completed_holdouts":len(source["holdouts"]),
        }
    write_new(folder/"summary.json",source)
    return source


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args=parser.parse_args()
    result=run_first(args.output)
    print(json.dumps({
        "status":result["status"],
        "calibrations":len(result["calibration"]),
        "holdouts":len(result["holdouts"]),
        "error":result.get("failure"),
        "MAE_input":result.get("input_capacity_MAE_seconds"),
        "MAE_state":result.get("observed_state_MAE_seconds"),
        "wins":result.get("strict_state_wins"),
    },sort_keys=True,indent=2),flush=True)
    if result["status"]=="RP_U007_MEASUREMENT_INVALID":
        raise SystemExit(2)


if __name__=="__main__":
    main()
