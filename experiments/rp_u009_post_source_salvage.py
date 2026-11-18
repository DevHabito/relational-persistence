"""RP-U009-P02 explicit post-source schema salvage, NOT P01's first result.

Only 0.0/1.0 literal LPS representation is normalized, after a separate
timestamp-and-LPS-only D01 audit. Source/windows/outcome rules are unchanged.
No physically independent repair time or causal claim is inferred.
"""
from __future__ import annotations

from hashlib import sha256
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

from experiments import rp_u009_metropt_core as core
from experiments import rp_u009_metropt_source as source
from experiments import rp_u009_lps_token_diagnostic as d01

P02_OUTPUT=Path("docs/results/RP-U009-P02-post-source-salvage/audit.json")
P02_ADDENDUM_COMMIT="764a07a5f7489491e6da05d17d15d6ecb5695af5"
D01_JSON=Path("docs/results/RP-U009-P01-D01-post-source-token-diagnostic/audit.json")
D01_JSON_SHA="8020c11a460a97552777e75ac3be0c31c02cc535a3c5eaba8d8cdc376c5e5ee0"
P02_ALLOWED_FIRST_ZIP_SHA="aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a"
P02_ALLOWED_EXTRACTED_CSV_SHA="db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24"


def verify_previous_source_history()->dict:
    d01.verify_original_failure()
    payload=D01_JSON.read_bytes()
    if sha256(payload).hexdigest()!=D01_JSON_SHA or len(payload)!=2674:
        raise core.InvalidEvidence("P02_D01_ORIGINAL_DIAGNOSTIC_DIGEST_CHANGED")
    audit=json.loads(payload)
    if (audit.get("status")!="RP_U009_D01_BINARY_TEXT_ENCODING_ONLY"
            or audit.get("source_rows")!=core.ORIGINAL_EXPECTED_ROWS
            or audit.get("all_window_tokens_member_of_binary_encoding_set") is not True):
        raise core.InvalidEvidence("P02_INELIGIBLE_AFTER_SOURCE_DIAGNOSTIC")
    if set(audit["all_source_lps_literal_token_counts"]) != {"0.0","1.0"}:
        raise core.InvalidEvidence("P02_SOURCE_TOKENS_DO_NOT_MATCH_DECIMAL_DIAGNOSTIC")
    return audit


def secondary_reanalysis()->dict:
    diagnosed=verify_previous_source_history()
    with TemporaryDirectory(prefix="rp-u009-p02-post-source-") as tmp:
        archive=Path(tmp)/"original-uci-791.zip"
        zip_source=source.authenticated_source_zip(archive)
        if (zip_source["official_zip_bytes"]!=d01.KNOWN_P01_ZIP_SIZE or
                zip_source["official_zip_sha256"]!=P02_ALLOWED_FIRST_ZIP_SHA):
            raise core.InvalidEvidence("P02_OFFICIAL_ZIP_IDENTITY_CHANGED")
        with zipfile.ZipFile(archive) as z:
            member=source.verified_member(z)
            csv_record=source.csv_identity(z,member)
            if csv_record["original_csv_sha256"]!=P02_ALLOWED_EXTRACTED_CSV_SHA:
                raise core.InvalidEvidence("P02_OFFICIAL_CSV_IDENTITY_CHANGED")
            with z.open(member) as source_body:
                text=io.TextIOWrapper(source_body,encoding="utf-8-sig",newline="")
                physical=core.original_csv_audit(
                    text,expected_census=core.ORIGINAL_EXPECTED_ROWS,
                    allow_decimal_lps=True,
                )
    assessed=core.evaluate_summary(physical)
    raw_status=assessed.pop("status")
    status=(
        "RP_U009_P02_POST_SOURCE_BOTH_MAINTENANCE_WINDOWS_IMPROVED"
        if raw_status=="RP_U009_BOTH_REPAIRS_SHOW_LOWER_LOW_PRESSURE_OCCUPANCY"
        else "RP_U009_P02_POST_SOURCE_NO_CONCORDANT_IMPROVEMENT"
    )
    return {
        **physical,**assessed,
        "study":"RP-U009-P02",
        "status":status,
        "original_P01_status_unchanged":"RP_U009_SOURCE_OR_WINDOWS_INVALID",
        "original_first_P01_sha256":d01.ORIGINAL_INVALID_SHA,
        "post_source_lps_diagnostic_sha256":D01_JSON_SHA,
        "post_source_addendum_commit":P02_ADDENDUM_COMMIT,
        "original_archive_source":zip_source,
        "original_csv_source":csv_record,
        "source_file_equal_to_D01_retrieval":True,
        "P02_post_source_reanalysis_not_a_preregistered_P01_success":True,
        "D01_LPS_status_known_before_reading_pressure":diagnosed["status"],
        "no_actual_independently_verified_maintenance_completion":True,
        "no_biological_or_physical_law_proven":True,
    }


def main()->None:
    if P02_OUTPUT.exists():
        raise SystemExit("FIRST_P02_RESULT_EXISTS_MUST_NOT_BE_OVERWRITTEN")
    if not os.environ.get("GITHUB_SHA") or not os.environ.get("GITHUB_RUN_ID"):
        raise SystemExit("P02_REQUIRES_AUTHENTICATED_ACTIONS_RUN")
    try:
        result=secondary_reanalysis()
    except (core.InvalidEvidence,OSError,ValueError,TypeError,RuntimeError,
            zipfile.BadZipFile,UnicodeError,TimeoutError) as exc:
        result={
            "study":"RP-U009-P02",
            "status":"RP_U009_P02_SOURCE_OR_WINDOWS_INVALID",
            "original_P01_status_unchanged":"RP_U009_SOURCE_OR_WINDOWS_INVALID",
            "post_source_addendum_commit":P02_ADDENDUM_COMMIT,
            "reason_type":type(exc).__name__,
            "reason_code":str(exc)[:225],
            "not_an_eligible_physical_recovery_study":True,
        }
    result["source_commit"]=os.environ["GITHUB_SHA"]
    result["first_secondary_workflow_id"]=os.environ["GITHUB_RUN_ID"]
    P02_OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    P02_OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                          encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    if result["status"]=="RP_U009_P02_SOURCE_OR_WINDOWS_INVALID":
        raise SystemExit(2)


if __name__=="__main__":
    main()
