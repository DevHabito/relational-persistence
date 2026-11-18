"""RP-U009: first source-authenticated MetroPT physical maintenance-window pilot.

The official UCI archive is held only in the hosted runner's temporary disk,
not copied to the repository. Its identity is recorded on first access.
Predeclared source-gates and pressure outcomes are not retuned post-data.
"""
from __future__ import annotations

from hashlib import sha256
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
import zipfile

from experiments import rp_u009_metropt_core as core

FIRST_OUTPUT = Path("docs/results/RP-U009-P01-first-run/audit.json")
READ_SIZE = 1 << 20
SOURCE_DOWNLOAD_TIMEOUT_SECONDS = 120
MAX_MEMBER_TOTAL_BYTES = 400_000_000
PRE_SOURCE_COMMIT = "744f00af2bc94a87fbe119bea2dd0e7fee791b82"


def authenticated_source_zip(path: Path) -> dict:
    hasher = sha256()
    byte_count = 0
    url_request = Request(core.OFFICIAL_UCI_URL, headers={
        "User-Agent": "RP-U009-registered-maintenance-audit/1.0"
    })
    try:
        response = urlopen(url_request, timeout=SOURCE_DOWNLOAD_TIMEOUT_SECONDS)
        with response, path.open("xb") as output:
            final_url = response.geturl()
            if not final_url.startswith("https://archive.ics.uci.edu/"):
                raise core.InvalidEvidence("UCI_ORIGINAL_ARCHIVE_REDIRECTED_AWAY")
            while True:
                payload = response.read(READ_SIZE)
                if not payload:
                    break
                byte_count += len(payload)
                if byte_count > core.ZIP_MAX_BYTES:
                    raise core.InvalidEvidence("UCI_ARCHIVE_TOO_LARGE")
                output.write(payload)
                hasher.update(payload)
    except (OSError, TimeoutError, ValueError) as exc:
        if isinstance(exc,core.InvalidEvidence):
            raise
        raise core.InvalidEvidence("OFFICIAL_UCI_SOURCE_DOWNLOAD_FAILED") from exc
    if byte_count == 0:
        raise core.InvalidEvidence("OFFICIAL_UCI_EMPTY_ARCHIVE")
    return {
        "original_source_url":core.OFFICIAL_UCI_URL,
        "final_verified_source_url":final_url,
        "official_zip_bytes":byte_count,
        "official_zip_sha256":hasher.hexdigest(),
        "official_version_not_git_fork":True,
    }


def verified_member(z: zipfile.ZipFile) -> zipfile.ZipInfo:
    infos = z.infolist()
    if not infos:
        raise core.InvalidEvidence("ORIGINAL_UCI_ZIP_HAS_NO_FILES")
    if sum(x.file_size for x in infos) > MAX_MEMBER_TOTAL_BYTES:
        raise core.InvalidEvidence("ORIGINAL_UCI_ARCHIVE_EXPANSION_EXCEEDS_BOUND")
    for x in infos:
        parts = x.filename.replace("\\", "/").split("/")
        if (x.filename.startswith("/") or
                any(p in ("..", "") for p in parts) or
                ((x.external_attr >> 16) & 0o170000) == 0o120000):
            raise core.InvalidEvidence("ORIGINAL_ZIP_UNSAFE_MEMBER_PATH")
        if x.flag_bits & 1:
            raise core.InvalidEvidence("ENCRYPTED_ORIGINAL_ZIP_MEMBER")
        if x.compress_size and x.file_size / x.compress_size > 1000:
            raise core.InvalidEvidence("ORIGINAL_UCI_ZIP_DECOMPRESSION_RATIO_INVALID")
    matches = [
        x for x in infos
        if x.filename.replace("\\", "/").split("/")[-1] ==
            core.ORIGINAL_CSV_BASENAME
    ]
    if len(matches) != 1:
        raise core.InvalidEvidence("EXACTLY_ONE_OFFICIAL_COMPRESSOR_CSV_REQUIRED")
    info = matches[0]
    if (info.file_size > core.CSV_MAX_BYTES or info.file_size == 0
            or info.is_dir()):
        raise core.InvalidEvidence("ORIGINAL_UCI_CSV_MEMBER_EXCEEDS_BOUNDS")
    return info


def csv_identity(z: zipfile.ZipFile, member: zipfile.ZipInfo) -> dict:
    h = sha256()
    size = 0
    with z.open(member) as stream:
        while True:
            chunk = stream.read(READ_SIZE)
            if not chunk:
                break
            size += len(chunk)
            if size > core.CSV_MAX_BYTES:
                raise core.InvalidEvidence("CSV_STREAM_EXCEEDS_BOUND")
            h.update(chunk)
    if size != member.file_size:
        raise core.InvalidEvidence("CSV_UNCOMPRESSED_SIZE_DIFFERS_FROM_ZIP_METADATA")
    return {
        "original_csv_member":member.filename,
        "original_csv_uncompressed_bytes":size,
        "original_csv_sha256":h.hexdigest(),
    }


def study_one_time(original_archive: Path) -> dict:
    with zipfile.ZipFile(original_archive, mode="r") as bundle:
        member=verified_member(bundle)
        identity=csv_identity(bundle,member)
        with bundle.open(member,mode="r") as f:
            text=io.TextIOWrapper(f, encoding="utf-8-sig", newline="")
            recorded=core.original_csv_audit(text)
    recorded["original_csv_identity"]=identity
    recorded.update(core.evaluate_summary(recorded))
    return recorded


def main() -> None:
    if FIRST_OUTPUT.exists():
        raise SystemExit("FIRST_RP_U009_RESULT_EXISTS_DO_NOT_REPLACE")
    if not os.environ.get("GITHUB_SHA") or not os.environ.get("GITHUB_RUN_ID"):
        raise SystemExit("FIRST_SOURCE_REQUIRED_ON_AUTHENTICATED_GITHUB_RUN")
    report = {
        "study": core.PROTOCOL,
        "status": "RP_U009_SOURCE_OR_WINDOWS_INVALID",
        "protocol_only_commit":core.PROTOCOL_ONLY_COMMIT,
        "pre_source_validation_commit":PRE_SOURCE_COMMIT,
        "first_source_runner_sha":os.environ["GITHUB_SHA"],
        "original_workflow_run_id":os.environ["GITHUB_RUN_ID"],
        "official_original_source_url":core.OFFICIAL_UCI_URL,
        "original_source_credential_required":False,
        "source_unmodified_and_never_mirrored":True,
        "published_failure_events_known_before_source":True,
        "not_independent_exact_physical_repair_timestamps":True,
    }
    try:
        with TemporaryDirectory(prefix="rp-u009-original-") as tmp:
            archive = Path(tmp)/"official-uci-791.zip"
            report["source"] = authenticated_source_zip(archive)
            result = study_one_time(archive)
            report.update(result)
    except (core.InvalidEvidence, zipfile.BadZipFile, RuntimeError,
            ValueError, TypeError, KeyError, OSError, UnicodeError) as exc:
        report["status"]="RP_U009_SOURCE_OR_WINDOWS_INVALID"
        report["failure"]={
            "kind":type(exc).__name__,
            "reason":str(exc)[:235],
        }
    FIRST_OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    FIRST_OUTPUT.write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(report,sort_keys=True,indent=2),flush=True)
    if report["status"]=="RP_U009_SOURCE_OR_WINDOWS_INVALID":
        raise SystemExit(2)


if __name__=="__main__":
    main()
