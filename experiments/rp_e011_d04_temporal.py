"""RP-E011-D04: source-only temporal feasibility on pinned JSSPP CERIT-SC.

Frozen before D04 implementation at c6e33b1. The known first-record zero
ID is an explicitly POST-D02/D03 informed exclusion for this NEW question.
D02's original rejection remains final; no forecasts or test errors here.
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

from experiments.rp_e011_jsspp_source import (
    SourceBlocked, download_exact, parse_original,
)
from experiments.rp_e011_d03_anomaly import inspect_id_rows

PROTOCOL = "RP-E011-D04"
ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "dd48cf7ca369d485b14add5d2baca70a1001c19d9b447688ff7639812673dc7c"
SOURCE_SIZE = 59_430_886
D02_AUDIT_SHA = "99be405c4e88dfd3646ea1812030eb7927b0a076de808f0257cd55d6e5db11f0"
D03_AUDIT_SHA = "a3031311456ed5949bfbc73cd4f634c6bfa688c768806a94d6998ba20719e75d"
D03_FIRST_LINE_SHA = "37fa5779391bcf43b42d672f89b13206efcf3f9336f2ec31d19d1874f848056c"
EXPECTED_ROWS = 472_400
EXPECTED_ELIGIBLE = 472_399
EXPECTED_QUEUES = 13
MIN_SPLIT = 1000
MIN_CROSS_QUEUE = 100
MIN_CROSS_QUEUES = 2


class SchemaDisagreement(Exception):
    """Original format, metadata, or independently recovered source disagrees."""


def required_decimal(value: str, name: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise SchemaDisagreement(f"Invalid finite field: {name}") from exc
    if not parsed.is_finite():
        raise SchemaDisagreement(f"Nonfinite field: {name}")
    return parsed


def verify_original_archives() -> None:
    """Check the permanent prior bytes before trusting their metadata."""
    for study, expected in (("D02", D02_AUDIT_SHA), ("D03", D03_AUDIT_SHA)):
        path = ROOT / f"docs/results/RP-E011-{study}-first-run/audit.json"
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise SchemaDisagreement(f"Original {study} audit SHA differs")
        data = json.loads(raw)
        if study == "D02":
            if (data["decision"] != "DATASET_SCHEMA_REJECTED"
                    or data["source"]["sha256"] != SOURCE_SHA
                    or data["schema"]["counts"]["invalid_job_id"] != 1):
                raise SchemaDisagreement("Original D02 source verdict has changed")
        else:
            loc = data["diagnostic"]["nonpositive_job_ids"]
            if (data["decision"] != "ANOMALY_LOCALIZED"
                    or data["source_identity"]["observed_sha256"] != SOURCE_SHA
                    or len(loc) != 1
                    or loc[0]["integer_job_id"] != 0
                    or loc[0]["physical_line"] != 1
                    or loc[0]["data_record_ordinal"] != 1
                    or loc[0]["original_line_without_newline_sha256"]
                    != D03_FIRST_LINE_SHA):
                raise SchemaDisagreement("Original D03 first-row finding changed")


def match_original_d02(raw: bytes) -> None:
    """Separate D02 schema oracle; never declare its rejected gate passed."""
    original = parse_original(raw)
    c = original["counts"]
    if not (
        c.get("data_rows", 0) == EXPECTED_ROWS
        and c.get("valid_numeric_prefix_rows", 0) == EXPECTED_ROWS
        and c.get("prefix_oracle_valid_shlex", 0) == EXPECTED_ROWS
        and c.get("prefix_oracle_valid_whitespace", 0) == EXPECTED_ROWS
        and c.get("invalid_job_id", 0) == 1
        and c.get("standard_eligible_rows", 0) == EXPECTED_ELIGIBLE
        and c.get("eligible_with_documented_extended_queue_name", 0)
        == EXPECTED_ELIGIBLE
        and c.get("duplicate_job_id", 0) == 0
        and original["parsed_record_widths"] == {"22": EXPECTED_ROWS}
        and original["distinct_documented_extended_queue_names_on_eligible_jobs"]
        == EXPECTED_QUEUES
        and original["independent_standard_prefix_readers_agree"] is True
    ):
        raise SchemaDisagreement("New audit disagrees with D02's ORIGINAL profile")
    first_ids = inspect_id_rows(raw)
    anomalous = first_ids["nonpositive_job_ids"]
    if (first_ids["data_rows"] != EXPECTED_ROWS
            or first_ids["duplicate_job_id_count"] != 0
            or len(anomalous) != 1
            or anomalous[0] != {
                "physical_line": 1,
                "data_record_ordinal": 1,
                "integer_job_id": 0,
                "original_line_without_newline_sha256": D03_FIRST_LINE_SHA,
            }):
        raise SchemaDisagreement("Independent D03 first-line ID audit disagrees")


def parse_temporal_candidates(raw: bytes) -> tuple[list[tuple[Decimal, int, str]], dict]:
    """Do not retain waits/starts, full SWF rows, or any user identifiers.

    Strict source scanner reads the full payload but emits only submit, ID,
    queue for schema-only split feasibility. A job's future status is never
    an inclusion predicate. The original row 1 is counted, not silently hidden.
    """
    try:
        source = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise SchemaDisagreement("Source is not UTF-8") from exc
    candidates: list[tuple[Decimal, int, str]] = []
    seen = set()
    data_ordinal = 0
    exceptions = 0
    original_prev_submit: Decimal | None = None
    inversions = ties = 0
    statuses = Counter()
    for physical_line, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        data_ordinal += 1
        try:
            parts = shlex.split(stripped, comments=False, posix=True)
        except ValueError as exc:
            raise SchemaDisagreement("Unbalanced SWF quoting") from exc
        if len(parts) != 22:
            raise SchemaDisagreement("Expected 22 extended SWF fields")
        try:
            job_id = int(parts[0])
            status = int(parts[10])
        except ValueError as exc:
            raise SchemaDisagreement("Invalid job integer field") from exc
        submit = required_decimal(parts[1], "submit")
        wait = required_decimal(parts[2], "wait")
        runtime = required_decimal(parts[3], "runtime")
        allocated = required_decimal(parts[4], "allocated")
        requested = required_decimal(parts[7], "requested")
        started = submit + wait
        if not started.is_finite() or started < submit:
            raise SchemaDisagreement("Invalid derived actual start timestamp")
        if original_prev_submit is not None:
            inversions += int(submit < original_prev_submit)
            ties += int(submit == original_prev_submit)
        original_prev_submit = submit
        if job_id in seen:
            raise SchemaDisagreement("Original record has duplicate job ID")
        seen.add(job_id)
        if job_id == 0 and physical_line == 1 and data_ordinal == 1:
            exceptions += 1
            continue
        if job_id <= 0:
            raise SchemaDisagreement("Unexpected additional nonpositive job ID")
        if (min(submit, wait, runtime) < 0
                or allocated <= 0 or requested <= 0):
            raise SchemaDisagreement("Other invalid eligible SWF row encountered")
        queue = parts[19].strip()
        if queue.lower() in ("", "-1", "none", "null", "?"):
            raise SchemaDisagreement("Original otherwise eligible row lacks queue")
        statuses[str(status)] += 1
        candidates.append((submit, job_id, queue))
    if data_ordinal != EXPECTED_ROWS or exceptions != 1:
        raise SchemaDisagreement("Known first line or expected source-row count changed")
    return candidates, {
        "original_source_data_rows": data_ordinal,
        "known_first_line_id_zero_exception_count": exceptions,
        "original_file_adjacent_submit_inversions": inversions,
        "original_file_adjacent_submit_ties": ties,
        "included_status_counts": dict(sorted(statuses.items())),
    }


def temporal_coverage(
    candidates: list[tuple[Decimal, int, str]],
    min_split: int = MIN_SPLIT,
    min_queue: int = MIN_CROSS_QUEUE,
    cross_queues: int = MIN_CROSS_QUEUES,
) -> dict:
    """Two independent total/split-count routes: loop versus sorted partition."""
    if not candidates:
        return {"feasible": False, "reason": "no eligible target records"}
    submits = [item[0] for item in candidates]
    first, last = min(submits), max(submits)
    cutoff = first + Decimal(7) * (last - first) / Decimal(10)
    counts = Counter()
    queues = {"diagnostic": Counter(), "heldout": Counter()}
    for submit, job_id, queue in candidates:
        side = "diagnostic" if submit < cutoff else "heldout"
        counts[side] += 1
        queues[side][queue] += 1
    independent = sorted(candidates, key=lambda item: (item[0], item[1]))
    independent_diag = sum(1 for t, _, _ in independent if t < cutoff)
    independent_holdout = len(independent) - independent_diag
    count_agreement = (
        independent_diag == counts["diagnostic"]
        and independent_holdout == counts["heldout"]
        and len(independent) == sum(counts.values())
        and len({j for _, j, _ in independent}) == len(independent)
    )
    shared = set(queues["diagnostic"]) & set(queues["heldout"])
    qualified = sum(
        queues["diagnostic"][q] >= min_queue and queues["heldout"][q] >= min_queue
        for q in shared
    )
    feasible = (
        count_agreement and len(candidates) == EXPECTED_ELIGIBLE
        and counts["diagnostic"] >= min_split
        and counts["heldout"] >= min_split
        and qualified >= cross_queues
    )
    return {
        "feasible": feasible,
        "submit_min_seconds": str(first),
        "submit_max_seconds": str(last),
        "fixed_chronological_cutoff_seconds": str(cutoff),
        "diagnostic_candidate_count": counts["diagnostic"],
        "heldout_candidate_count": counts["heldout"],
        "eligible_total_count": len(independent),
        "distinct_queue_count": len(set(queues["diagnostic"]) | set(queues["heldout"])),
        "shared_queues_meeting_100_jobs_on_each_side": qualified,
        "independent_sorted_vs_streaming_split_counts_agree": count_agreement,
        "tied_submit_handling": "submit < T diagnostic, submit >= T heldout",
        "forecast_or_wait_loss_computed": False,
    }


def audit_verified_bytes(raw: bytes, provider: dict | None = None) -> dict:
    identity = {
        "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
        "expected_bytes": SOURCE_SIZE, "expected_sha256": SOURCE_SHA,
    }
    if provider:
        identity["provider"] = provider
    result = {
        "decision": "SOURCE_SHA_MISMATCH",
        "source_identity": identity,
        "schema": None,
        "temporal_coverage": None,
        "errors": [],
        "d02_original_verdict_unchanged": "DATASET_SCHEMA_REJECTED",
        "predictions_computed": False,
        "new_lean_theorem": False,
        "physics_claimed": False,
    }
    if identity["bytes"] != SOURCE_SIZE or identity["sha256"] != SOURCE_SHA:
        return result
    try:
        verify_original_archives()
        match_original_d02(raw)
        jobs, profile = parse_temporal_candidates(raw)
        result["schema"] = profile
        result["temporal_coverage"] = temporal_coverage(jobs)
        result["decision"] = (
            "TEMPORAL_SOURCE_FEASIBLE"
            if result["temporal_coverage"]["feasible"]
            else "TEMPORAL_SOURCE_INFEASIBLE"
        )
    except (SchemaDisagreement, ValueError, KeyError) as exc:
        result["decision"] = "SOURCE_SCHEMA_DISAGREEMENT"
        result["errors"] = [{
            "stage": "strict-timing-or-original-schema",
            "reason": f"{type(exc).__name__}: {str(exc)[:250]}",
        }]
    return result


def first_run(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Cannot overwrite the original D04 audit")
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "protocol": PROTOCOL, "decision": "SOURCE_ACCESS_BLOCKED",
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "environment": platform.platform(),
        "d02_original_verdict_unchanged": "DATASET_SCHEMA_REJECTED",
        "source_identity": None, "schema": None,
        "temporal_coverage": None, "errors": [],
        "predictions_computed": False, "new_lean_theorem": False,
        "physics_claimed": False,
    }
    try:
        source, provider = download_exact()
        result.update(audit_verified_bytes(source, provider))
    except SourceBlocked as exc:
        result["errors"].append({"stage": "original-official-source", "reason": str(exc)[:250]})
    finally:
        (output / "RP-E011-D04.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = first_run(args.output)
    print(json.dumps({
        "protocol": PROTOCOL, "decision": result["decision"],
        "diagnostic_count": (result["temporal_coverage"] or {}).get(
            "diagnostic_candidate_count"),
        "heldout_count": (result["temporal_coverage"] or {}).get(
            "heldout_candidate_count"),
        "errors": result["errors"],
    }))
    if result["decision"] != "TEMPORAL_SOURCE_FEASIBLE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
