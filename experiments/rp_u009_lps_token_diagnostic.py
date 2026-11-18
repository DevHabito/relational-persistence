"""RP-U009-D01 post-original-failure LPS token inspection ONLY.

Inspects only timestamp and literal LPS tokens from identical verified UCI
ZIP. This post-source diagnostic MUST NOT read or output compressor pressure
or maintenance outcome. The first P01 invalid result remains untouched.
"""
from __future__ import annotations

from collections import Counter
import csv
from hashlib import sha256
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

from experiments import rp_u009_metropt_core as core
from experiments import rp_u009_metropt_source as source

KNOWN_P01_ZIP_SIZE = 218_381_995
KNOWN_P01_ZIP_SHA = (
    "aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a"
)
ALLOWED_TOKENS = frozenset(("0", "1", "0.0", "1.0"))
D01_OUTPUT = Path("docs/results/RP-U009-P01-D01-post-source-token-diagnostic/audit.json")
D01_ADDENDUM_COMMIT = "26cf6dff3e15805124f58c61529ff54924be6b24"
ORIGINAL_INVALID_SHA = (
    "0b74889ed609a43d8924880e702d93fb8e723fd517fd718734463125991c13e3"
)


def verify_original_failure() -> None:
    p = source.FIRST_OUTPUT
    if not p.exists():
        raise core.InvalidEvidence("ORIGINAL_INVALID_RESULT_MISSING")
    raw=p.read_bytes()
    if sha256(raw).hexdigest()!=ORIGINAL_INVALID_SHA or len(raw)!=1170:
        raise core.InvalidEvidence("ORIGINAL_INVALID_SOURCE_ARCHIVE_CHANGED")
    result=json.loads(raw)
    if (result.get("status")!="RP_U009_SOURCE_OR_WINDOWS_INVALID"
            or result.get("failure",{}).get("reason")!="LOW_PRESSURE_SWITCH_MUST_BE_BINARY"):
        raise core.InvalidEvidence("D01_NO_LONGER_MATCHES_FIRST_SOURCE_FAILURE")


def token_only_diagnostic(z: zipfile.ZipFile, member: zipfile.ZipInfo) -> dict:
    windows=core.fixed_windows()
    counters=[Counter() for _ in windows]
    overall=Counter()
    last=None
    count=0
    first=None
    zero_or_negative=0
    gaps=[]
    with z.open(member) as binary:
        src=csv.DictReader(io.TextIOWrapper(binary,encoding="utf-8-sig",newline=""))
        if (src.fieldnames is None or
                len(set(src.fieldnames))!=len(src.fieldnames) or
                not {"timestamp","LPS"}<=set(src.fieldnames)):
            raise core.InvalidEvidence("D01_SOURCE_TIMESTAMP_OR_LPS_COLUMN_MISSING")
        for row in src:
            if None in row or any(v is None for v in row.values()):
                raise core.InvalidEvidence("D01_ORIGINAL_SOURCE_ROW_MALFORMED")
            stamp=core.date_from_source(row["timestamp"])
            if last is not None:
                gap=(stamp-last).total_seconds()
                if gap<=0:
                    zero_or_negative+=1
                    raise core.InvalidEvidence("D01_SOURCE_TIMESTAMP_NOT_STRICTLY_INCREASING")
                gaps.append(gap)
            if first is None:
                first=stamp
            last=stamp
            token=row["LPS"].strip()
            overall[token]+=1
            for i,window in enumerate(windows):
                if window["begin_clock"]<=stamp<window["end_clock"]:
                    counters[i][token]+=1
            count+=1
    if count!=core.ORIGINAL_EXPECTED_ROWS:
        raise core.InvalidEvidence("D01_SOURCE_ROW_CENSUS_FAILED")
    if not gaps:
        raise core.InvalidEvidence("D01_NO_VALID_SAMPLING_GAPS")
    gaps.sort()
    permitted=all(set(counts)<=ALLOWED_TOKENS for counts in counters)
    return {
        "status":(
            "RP_U009_D01_BINARY_TEXT_ENCODING_ONLY" if permitted
            else "RP_U009_D01_UNEXPECTED_LPS_SEMANTIC_VALUES"
        ),
        "source_rows":count,
        "first_source_clock":first.strftime("%Y-%m-%d %H:%M:%S"),
        "last_source_clock":last.strftime("%Y-%m-%d %H:%M:%S"),
        "observed_min_gap_seconds":gaps[0],
        "observed_median_gap_seconds":core.safe_percentile(gaps,.5),
        "observed_p95_gap_seconds":core.safe_percentile(gaps,.95),
        "observed_max_gap_seconds":gaps[-1],
        "zero_or_negative_gaps":zero_or_negative,
        "per_window_lps_literal_tokens":[
            {"event_number":window["event_number"],
             "window_side":window["side"],
             "maintenance_clock_label":window["maintenance_clock_label"],
             "literal_token_counts":dict(sorted(tokens.items())),
             "rows":sum(tokens.values())}
            for window,tokens in zip(windows,counters,strict=True)
        ],
        "all_source_lps_literal_token_counts":dict(sorted(overall.items())),
        "all_window_tokens_member_of_binary_encoding_set":permitted,
        "no_pressure_values_read":True,
        "no_motor_current_values_read":True,
        "no_original_P01_result_replaced":True,
    }


def run_diagnostic() -> dict:
    verify_original_failure()
    with TemporaryDirectory(prefix="rp-u009-d01-tokens-") as tmp:
        zip_path=Path(tmp)/"verified-original.zip"
        provenance=source.authenticated_source_zip(zip_path)
        if (provenance["official_zip_bytes"]!=KNOWN_P01_ZIP_SIZE or
                provenance["official_zip_sha256"]!=KNOWN_P01_ZIP_SHA):
            raise core.InvalidEvidence("D01_SOURCE_CHANGED_SINCE_FIRST_FAILURE")
        with zipfile.ZipFile(zip_path) as z:
            member=source.verified_member(z)
            audit=token_only_diagnostic(z,member)
            audit["csv_original_identity"]=source.csv_identity(z,member)
    audit.update({
        "study":"RP-U009-P01-D01",
        "original_first_P01_failure_sha256":ORIGINAL_INVALID_SHA,
        "original_first_workflow_id":"44212185197",
        "post_original_failure_addendum_commit":D01_ADDENDUM_COMMIT,
        "official_source_zip":provenance,
        "source_values_restricted_to_timestamp_and_LPS":True,
        "no_pressure_or_maintenance_functional_outcome_computed":True,
    })
    return audit


def main() -> None:
    if D01_OUTPUT.exists():
        raise SystemExit("D01_DIAGNOSTIC_ALREADY_EXISTS")
    if not os.environ.get("GITHUB_RUN_ID") or not os.environ.get("GITHUB_SHA"):
        raise SystemExit("D01_ONLY_IN_HOSTED_ACTIONS")
    try:
        report=run_diagnostic()
    except (core.InvalidEvidence,zipfile.BadZipFile,ValueError,
            OSError,UnicodeError,TimeoutError) as exc:
        report={
            "study":"RP-U009-P01-D01",
            "status":"RP_U009_D01_SOURCE_INCOMPLETE",
            "failure_type":type(exc).__name__,
            "failure_code":str(exc)[:195],
            "first_original_P01_remains_invalid":True,
        }
    report["diagnostic_workflow_id"]=os.environ["GITHUB_RUN_ID"]
    report["diagnostic_code_commit"]=os.environ["GITHUB_SHA"]
    D01_OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    D01_OUTPUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",
                          encoding="utf-8")
    print(json.dumps(report,sort_keys=True,indent=2),flush=True)
    if report["status"]=="RP_U009_D01_SOURCE_INCOMPLETE":
        raise SystemExit(2)


if __name__=="__main__":
    main()
