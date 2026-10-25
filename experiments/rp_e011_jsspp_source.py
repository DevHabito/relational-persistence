"""RP-E011-D02: separate JSSPP CERIT-SC *source-only* eligibility audit.

This distinct candidate follows the original RP-E011-D01 ALCF HTTP access
block. The D02 scientific rules were frozen on main before this code or any
D02 source bytes were downloaded or inspected. No predictions are made.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import platform
import shlex
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PROTOCOL = "RP-E011-D02"
SOURCE_URL = "https://jsspp.org/workload/logs/2017/cerit/grid-jobs.swf"
SOURCE_PAGE = "https://jsspp.org/workload/index.php?page=cerit"
SOURCE_HOST = "jsspp.org"
MAX_ORIGINAL_BYTES = 150_000_000
STANDARD_FIELDS = 18
DOCUMENTED_QUEUE_INDEX = 19
MIN_ELIGIBLE = 1000


class SourceBlocked(Exception):
    """A source-acquisition failure must not be treated as data rejection."""


def official_origin(url: str) -> bool:
    parts = urlsplit(url)
    return (parts.scheme == "https" and parts.hostname == SOURCE_HOST
            and parts.username is None and parts.password is None
            and parts.port in (None, 443))


def download_exact() -> tuple[bytes, dict]:
    if not official_origin(SOURCE_URL):
        raise SourceBlocked("Frozen original source URI fails HTTPS host restriction")
    request = Request(
        SOURCE_URL,
        headers={
            "User-Agent": "relational-persistence-RP-E011-D02/1.0",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urlopen(request, timeout=50) as response:
            final_url = response.geturl()
            if not official_origin(final_url):
                raise SourceBlocked("Original academic download redirects off origin")
            response_code = response.status
            content_type = response.headers.get("Content-Type", "")
            payload = response.read(MAX_ORIGINAL_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise SourceBlocked(
            f"Original academic source not accessible: {type(exc).__name__}: {exc}"
        ) from exc
    if response_code != 200:
        raise SourceBlocked(f"HTTP status {response_code} from original archive")
    if not payload or len(payload) > MAX_ORIGINAL_BYTES:
        raise SourceBlocked("Original source empty or exceeds 150 MB acquisition cap")
    return payload, {
        "requested_url": SOURCE_URL,
        "final_url": final_url,
        "status": response_code,
        "content_type": content_type,
        "original_bytes": len(payload),
        "sha256": sha256(payload).hexdigest(),
    }


def finite_decimal(cell: str) -> Decimal | None:
    try:
        result = Decimal(cell)
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def standard_swf_fields(tokens: list[str]) -> tuple | None:
    if len(tokens) < STANDARD_FIELDS:
        return None
    try:
        job_id = int(tokens[0])
        submit = finite_decimal(tokens[1])
        wait = finite_decimal(tokens[2])
        runtime = finite_decimal(tokens[3])
        allocated = finite_decimal(tokens[4])
        requested = finite_decimal(tokens[7])
        status = int(tokens[10])
        numeric_queue = int(tokens[14])
    except (ValueError, TypeError):
        return None
    if any(x is None for x in (submit, wait, runtime, allocated, requested)):
        return None
    return (job_id, submit, wait, runtime, allocated,
            requested, status, numeric_queue)


def parse_original(raw: bytes) -> dict:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("Original source is not UTF-8 SWF text") from exc
    if b"\x00" in raw[:4096]:
        raise ValueError("Original resource appears binary, not text SWF")
    counts = Counter()
    seen_ids = set()
    queue_names = set()
    header_fragments = []
    first_issues = []
    widths = Counter()
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            counts["blank_lines"] += 1
            continue
        if stripped.startswith(";"):
            counts["comment_lines"] += 1
            if len(header_fragments) < 10:
                header_fragments.append(stripped[:180])
            continue
        counts["data_rows"] += 1
        try:
            parsed = shlex.split(stripped, comments=False, posix=True)
        except ValueError:
            counts["quote_parse_failures"] += 1
            if len(first_issues) < 10:
                first_issues.append({
                    "line": line_no, "issue": "unbalanced or invalid SWF quoting"
                })
            continue

        # Independent prefix validator: whitespace tokenization of exactly
        # the standard 18 columns, no shared shlex logic or derived values.
        prefix = stripped.split(maxsplit=STANDARD_FIELDS)[:STANDARD_FIELDS]
        first = standard_swf_fields(prefix)
        second = standard_swf_fields(parsed[:STANDARD_FIELDS])
        counts["prefix_oracle_valid_whitespace"] += int(first is not None)
        counts["prefix_oracle_valid_shlex"] += int(second is not None)

        if first != second:
            counts["prefix_oracle_disagreements"] += 1
            if len(first_issues) < 10:
                first_issues.append({
                    "line": line_no, "issue": "two SWF prefix readers disagree"
                })
            continue
        if first is None:
            counts["bad_18_field_swf_prefixes"] += 1
            if len(first_issues) < 10:
                first_issues.append({
                    "line": line_no, "issue": "unparseable 18-column SWF prefix"
                })
            continue

        counts["valid_numeric_prefix_rows"] += 1
        widths[len(parsed)] += 1
        (job_id, submit, wait, runtime, allocated,
         requested, status, numeric_queue) = first
        if job_id <= 0:
            counts["invalid_job_id"] += 1
        if job_id in seen_ids:
            counts["duplicate_job_id"] += 1
        seen_ids.add(job_id)
        if submit < 0:
            counts["missing_submit"] += 1
        if wait < 0:
            counts["missing_wait"] += 1
        if runtime < 0:
            counts["missing_runtime"] += 1
        if allocated <= 0:
            counts["nonpositive_allocated_processors"] += 1
        if requested <= 0:
            counts["nonpositive_requested_processors"] += 1
        if status < 0:
            counts["unknown_status"] += 1
        if numeric_queue < 0:
            counts["missing_standard_numeric_queue"] += 1
        valid = (job_id > 0 and submit >= 0 and wait >= 0
                 and runtime >= 0 and allocated > 0 and requested > 0)
        counts["standard_eligible_rows"] += int(valid)
        if len(parsed) <= DOCUMENTED_QUEUE_INDEX:
            counts["missing_documented_extended_queue_column"] += 1
            continue
        name = parsed[DOCUMENTED_QUEUE_INDEX].strip()
        if name.lower() in ("", "-1", "none", "null", "?"):
            counts["missing_documented_extended_queue_name"] += 1
            continue
        if valid:
            counts["eligible_with_documented_extended_queue_name"] += 1
            queue_names.add(name)

    return {
        "counts": dict(sorted(counts.items())),
        "parsed_record_widths": {str(n): c for n, c in sorted(widths.items())},
        "independent_standard_prefix_readers_agree": (
            counts["prefix_oracle_disagreements"] == 0 and
            counts["prefix_oracle_valid_whitespace"] ==
            counts["prefix_oracle_valid_shlex"]
        ),
        "distinct_documented_extended_queue_names_on_eligible_jobs": len(queue_names),
        "header_comment_preview": header_fragments,
        "first_10_source_structure_problems": first_issues,
        "source_provenance": "original JSSPP CERIT-SC 2017 grid-jobs extended SWF",
        "all_rows_from_independently_collected_operational_trace": True,
        "queue_wait_predictions_computed": False,
        "source_immutable_prior_to_first_retrieval": False,
    }


def classify(result: dict) -> str:
    counts = result["counts"]
    if (not result["independent_standard_prefix_readers_agree"]
            or counts.get("quote_parse_failures", 0)
            or counts.get("bad_18_field_swf_prefixes", 0)
            or counts.get("duplicate_job_id", 0)
            or counts.get("invalid_job_id", 0)
            or counts.get("valid_numeric_prefix_rows", 0) != counts.get("data_rows", 0)
            or counts.get("standard_eligible_rows", 0) < MIN_ELIGIBLE
            or result["distinct_documented_extended_queue_names_on_eligible_jobs"] < 2):
        return "DATASET_SCHEMA_REJECTED"
    return "DATASET_SCHEMA_VERIFIED"


def first_source(output: Path, *, byte_override: bytes | None = None) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Cannot replace first RP-E011-D02 source trial")
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "protocol": PROTOCOL, "decision": "SOURCE_ACCESS_BLOCKED",
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "first_source_commit": os.environ.get("GITHUB_SHA"),
        "execution_environment": platform.platform(),
        "original_publisher_page": SOURCE_PAGE,
        "original_download_url": SOURCE_URL,
        "source_unmodified": True,
        "retrospective_forecast_evaluated": False,
        "scalar_C_law_tested": False,
        "physical_generalization_claimed": False,
        "source": None, "schema": None, "errors": [],
    }
    try:
        if byte_override is None:
            raw, metadata = download_exact()
        else:
            raw = byte_override
            metadata = {
                "fixture_only": True,
                "original_bytes": len(raw),
                "sha256": sha256(raw).hexdigest(),
                "requested_url": SOURCE_URL,
                "final_url": SOURCE_URL,
            }
        result["source"] = metadata
        parsed = parse_original(raw)
        result["schema"] = parsed
        result["decision"] = classify(parsed)
        (output / "temporary-original-jsspp-source.swf").write_bytes(raw)
    except SourceBlocked as exc:
        result["errors"].append({
            "stage": "exact-original-provider-acquisition",
            "reason": str(exc)[:500],
        })
    except (UnicodeError, ValueError, TypeError) as exc:
        result["decision"] = "DATASET_SCHEMA_REJECTED"
        result["errors"].append({
            "stage": "source-prefix-or-encoding",
            "reason": f"{type(exc).__name__}: {str(exc)[:500]}",
        })
    finally:
        (output / "RP-E011-D02.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    x = first_source(args.output)
    print(json.dumps({
        "protocol": PROTOCOL, "decision": x["decision"],
        "original_bytes": x["source"]["original_bytes"] if x["source"] else None,
        "records": x["schema"]["counts"].get("data_rows")
        if x["schema"] else None,
        "extended_queue_names": x["schema"][
            "distinct_documented_extended_queue_names_on_eligible_jobs"
        ] if x["schema"] else None,
        "errors": x["errors"],
    }, sort_keys=True))
    if x["decision"] != "DATASET_SCHEMA_VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
