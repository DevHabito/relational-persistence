"""RP-E010-D01: *source-feasibility only* audit of independent HPC2N SWF.

Do not call a queue forecast, derive recovery labels, fit parameters, select
holdout windows or test any RP physical law here. All source coordinates and
decision gates were frozen in docs/preregistration/RP-E010-D01.md first.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import urllib.error
import urllib.request

PROTOCOL = "RP-E010-D01"
REPOSITORY = "wrench-project/task_clustering_batch_datasets"
REVISION = "f349db7f7783333f668e79618da62f8714fd7f2c"
FILEPATH = "workloads/hpc2n.swf"
EXPECTED_BLOB = "6d3cf513d74f6b839dc8425dd30bc889e15dc3be"
EXPECTED_BYTES = 19_242_100
SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    f"{REPOSITORY}/{REVISION}/{FILEPATH}"
)
KEYS = (
    "header_lines", "data_lines", "bad_width", "invalid_numeric",
    "nonpositive_job_id", "duplicate_job_ids", "missing_submit",
    "missing_wait", "missing_runtime", "missing_processors",
    "missing_status", "missing_queue", "unsorted_submit",
    "eligible_completed", "first_bad_lines",
)


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(content)}\0".encode("ascii") + content
    ).hexdigest()


def empty_statistics() -> dict:
    return {
        **{name: 0 for name in KEYS if name != "first_bad_lines"},
        "first_bad_lines": [],
    }


def observed_record(stat: dict, line: int, reason: str) -> None:
    if len(stat["first_bad_lines"]) < 8:
        stat["first_bad_lines"].append({
            "line_number": line, "reason": reason,
        })


def parse_numbers(values: list[str]) -> tuple[int, Decimal, Decimal,
                                              Decimal, Decimal, int, int]:
    # Indexes are frozen by the SWF 2.2 field definition, not inferred
    # from column distributions or held-out outcomes.
    job_id = int(values[0])
    submit = Decimal(values[1])
    wait = Decimal(values[2])
    runtime = Decimal(values[3])
    processors = Decimal(values[4])
    status = int(values[10])
    queue = int(values[14])
    if any(not x.is_finite() for x in (submit, wait, runtime, processors)):
        raise ValueError("Nonfinite source field")
    if processors != processors.to_integral_value():
        raise ValueError("Nonintegral processor count")
    return job_id, submit, wait, runtime, processors, status, queue


def count_valid_row(stat: dict, seen: set[int], previous_submit: Decimal | None,
                    row: tuple[int, Decimal, Decimal, Decimal, Decimal, int, int],
                    lineno: int) -> Decimal | None:
    job, submit, wait, runtime, processors, status, queue = row
    if job <= 0:
        stat["nonpositive_job_id"] += 1
        observed_record(stat, lineno, "nonpositive job id")
    if job in seen:
        stat["duplicate_job_ids"] += 1
        observed_record(stat, lineno, "duplicate job id")
    seen.add(job)
    if submit < 0:
        stat["missing_submit"] += 1
    elif previous_submit is not None and submit < previous_submit:
        stat["unsorted_submit"] += 1
        observed_record(stat, lineno, "submit timestamp decreased")
    if submit >= 0:
        previous_submit = submit
    if wait < 0:
        stat["missing_wait"] += 1
    if runtime < 0:
        stat["missing_runtime"] += 1
    if processors <= 0:
        stat["missing_processors"] += 1
    if status < 0:
        stat["missing_status"] += 1
    if queue < 0:
        stat["missing_queue"] += 1
    if (job > 0 and submit >= 0 and wait >= 0
            and runtime >= 0 and processors > 0 and status == 1):
        stat["eligible_completed"] += 1
    return previous_submit


def parse_swf_primary(content: bytes) -> dict:
    lines = content.decode("utf-8", errors="strict").splitlines()
    stat = empty_statistics()
    seen: set[int] = set()
    previous = None
    for number, line in enumerate(lines, 1):
        data = line.strip()
        if not data:
            continue
        if data.startswith(";"):
            stat["header_lines"] += 1
            continue
        stat["data_lines"] += 1
        cells = data.split()
        if len(cells) != 18:
            stat["bad_width"] += 1
            observed_record(stat, number, "not 18 SWF columns")
            continue
        try:
            row = parse_numbers(cells)
        except (ValueError, InvalidOperation, OverflowError):
            stat["invalid_numeric"] += 1
            observed_record(stat, number, "invalid SWF numeric field")
            continue
        previous = count_valid_row(stat, seen, previous, row, number)
    return stat


def parse_swf_independent(content: bytes) -> dict:
    """Independent tokenization and numeric parsing, same frozen counters.

    This is a second parser oracle, not an independent scientific dataset.
    """
    text = content.decode("utf-8", errors="strict")
    result = empty_statistics()
    seen: set[int] = set()
    prior = None
    for index, line in enumerate(re.findall(r"[^\r\n]+", text), 1):
        tokens = re.findall(r"\S+", line)
        if not tokens:
            continue
        if tokens[0].startswith(";"):
            result["header_lines"] += 1
            continue
        result["data_lines"] += 1
        if len(tokens) != 18:
            result["bad_width"] += 1
            observed_record(result, index, "not 18 SWF columns")
            continue
        try:
            job = int(tokens[0])
            numbers = [Decimal(tokens[k]) for k in (1, 2, 3, 4)]
            status, queue = int(tokens[10]), int(tokens[14])
            if not all(x.is_finite() for x in numbers):
                raise ValueError("nonfinite value")
            if numbers[3] != numbers[3].to_integral_value():
                raise ValueError("nonintegral processors")
            row = (job, *numbers, status, queue)
        except (InvalidOperation, ValueError, OverflowError):
            result["invalid_numeric"] += 1
            observed_record(result, index, "invalid SWF numeric field")
            continue
        prior = count_valid_row(result, seen, prior, row, index)
    return result


def classify(stat: dict, *, identity_verified: bool) -> str:
    if not identity_verified:
        return "DATASET_SCHEMA_REJECTED"
    if (stat["bad_width"] or stat["invalid_numeric"]
            or stat["nonpositive_job_id"] or stat["duplicate_job_ids"]
            or stat["unsorted_submit"]
            or stat["eligible_completed"] < 1000):
        return "DATASET_SCHEMA_REJECTED"
    return "DATASET_SCHEMA_VERIFIED"


def inspect_bytes(content: bytes) -> dict:
    identity = {
        "actual_bytes": len(content),
        "actual_sha256": sha256(content),
        "actual_git_blob_sha1": git_blob_sha1(content),
        "expected_bytes": EXPECTED_BYTES,
        "expected_git_blob_sha1": EXPECTED_BLOB,
        "identity_verified": (
            len(content) == EXPECTED_BYTES
            and git_blob_sha1(content) == EXPECTED_BLOB
        ),
    }
    left = parse_swf_primary(content)
    right = parse_swf_independent(content)
    return {
        **identity,
        "counters": left,
        "independent_parser_agreement": left == right,
        "independent_parser_counters": right,
        "decision": classify(left, identity_verified=identity["identity_verified"])
        if left == right else "DATASET_SCHEMA_REJECTED",
    }


def fetch_exact_pinned_source() -> bytes:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "relational-persistence-RP-E010-D01/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read(EXPECTED_BYTES + 1)
    return payload


def audit(output: Path, *, source_override: bytes | None = None) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("First source provenance may not be overwritten")
    output.mkdir(parents=True, exist_ok=True)
    project = Path(__file__).resolve().parents[1]
    protocol_path = project / "docs/preregistration/RP-E010-D01.md"
    report = {
        "protocol": PROTOCOL,
        "source_repository": REPOSITORY,
        "source_revision": REVISION,
        "source_path": FILEPATH,
        "source_url": SOURCE_URL,
        "preregistration_sha256": sha256(protocol_path.read_bytes()),
        "github_source_commit": os.getenv("GITHUB_SHA"),
        "github_first_run_id": os.getenv("GITHUB_RUN_ID"),
        "runtime": platform.python_version(),
        "platform": platform.platform(),
        "real_world_queue_predictive_test": "NOT_PERFORMED",
        "scalar_C_prediction_test": "NOT_PERFORMED",
        "original_NASA_submission_times_observed": False,
        "result": None,
        "decision": "SOURCE_ACCESS_BLOCKED",
        "errors": [],
    }
    try:
        source = fetch_exact_pinned_source() if source_override is None else source_override
    except (TimeoutError, urllib.error.HTTPError,
            urllib.error.URLError, OSError) as error:
        report["errors"].append({
            "stage": "pinned source access",
            "reason": f"{type(error).__name__}: {error}",
        })
    else:
        try:
            result = inspect_bytes(source)
            report["result"] = result
            report["decision"] = result["decision"]
            # An Actions artifact may temporarily retain the exact input
            # for byte-level follow-up, but do NOT commit/rehost it in Git.
            (output / "temporary-original-hpc2n.swf").write_bytes(source)
        except (UnicodeError, ValueError, InvalidOperation, OverflowError) as error:
            report["decision"] = "DATASET_SCHEMA_REJECTED"
            report["errors"].append({
                "stage": "SWF byte/schema parse",
                "reason": f"{type(error).__name__}: {error}",
            })
    finally:
        (output / "RP-E010-D01.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.output)
    print(json.dumps({
        "decision": report["decision"],
        "identity_verified": report["result"]["identity_verified"]
        if report["result"] else None,
        "valid_rows": report["result"]["counters"]["eligible_completed"]
        if report["result"] else None,
        "errors": report["errors"],
    }, sort_keys=True))
    if report["decision"] != "DATASET_SCHEMA_VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
