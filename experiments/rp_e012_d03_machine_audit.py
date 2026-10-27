"""RP-E012-D03: independently audit the FULL original cell-a machine event shard.

Preregistration frozen alone on main at 41befcd BEFORE this source program
or any D03 original metadata request. The size of machine shard zero was
already publicly known from D02 (651,854 bytes): this is informed selection.
No instance/collection raw rows, forecasting, BigQuery, billing or physical law.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import md5, sha256
from io import BytesIO
from pathlib import Path
from urllib.request import Request
from urllib.error import URLError, HTTPError
import argparse
import base64
import json
import os
import re
import zlib

from experiments.rp_e012_d02_prefix import (
    BUCKET, HOST, source_opener, metadata_url, media_url,
    SourceAccess, PrefixInvalid, _canonical_int,
)

PROTOCOL = "RP-E012-D03"
PREREG = "41befcd7970a86f558b50de8f66f89473920fa6e"
TABLES = ("machine_events", "collection_events", "instance_events")
ORIGINS = (1_000_000_000_000, 2_000_000_000_000)
MAX_LIST_BYTES = 524_288
MAX_COMPRESSED = 2_097_152
MAX_EXPANDED = 33_554_432
MAX_RECORDS = 100_000
CHUNK_SIZE = 16_384
SOURCE_PATTERN = re.compile(r"^(machine_events|collection_events|instance_events)-[0-9]+\.json\.(?:gzip|gz)$")
CORE_NAMES = ("time", "machine_id", "type")
CORE_PATTERN = re.compile(
    r'"(time|machine_id|type|missing_type)"\s*:\s*"([0-9]+)"'
)


class SourceIdentityFailure(Exception):
    pass


class MachineFormatFailure(Exception):
    pass


class MachineOracleDisagreement(Exception):
    pass


class MachineCoverageFailure(Exception):
    pass


def fetch_inventory_page(table: str) -> tuple[dict, list[dict]]:
    if table not in TABLES:
        raise SourceAccess("Unregistered table")
    # The URI and mask are the same as original D02; only the fixed
    # first page is read, NO page-token traversal.
    address = metadata_url(table) if table in ("machine_events", "instance_events") else (
        f"https://{HOST}/storage/v1/b/{BUCKET}/o?"
        "prefix=collection_events-&maxResults=100&"
        "fields=items%28name%2Csize%2Cgeneration%2Cmd5Hash%2Ccrc32c%29%2CnextPageToken"
    )
    with source_opener().open(Request(address, headers={
        "User-Agent": "relational-persistence-RP-E012-D03-metadata"
    }), timeout=25) as response:
        if response.status != 200:
            raise SourceAccess("Original GCS metadata status was not HTTP 200")
        raw = response.read(MAX_LIST_BYTES + 1)
    if len(raw) > MAX_LIST_BYTES:
        raise SourceAccess("Original metadata exceeded registered byte budget")
    try:
        data = json.loads(raw.decode("utf-8", "strict"))
    except (UnicodeError, ValueError) as exc:
        raise SourceAccess("Invalid official GCS listing JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise SourceAccess("Missing original official GCS items")
    if len(data["items"]) > 100:
        raise SourceAccess("Provider returned more than first 100 items")
    pattern = re.compile(r"^" + re.escape(table) + r"-[0-9]+\.json\.(?:gz|gzip)$")
    selected = sorted(
        (item for item in data["items"] if isinstance(item, dict)
         and isinstance(item.get("name"), str)
         and pattern.fullmatch(item["name"])),
        key=lambda item: item["name"],
    )
    summary = {
        "table": table, "first_page_returned_items": len(data["items"]),
        "matching_shards_on_first_page": len(selected),
        "inventory_incomplete_due_to_pagination": bool(data.get("nextPageToken")),
        "selected_first_shard": selected[0]["name"] if selected else None,
        "selected_first_size_bytes_metadata_only": (
            selected[0].get("size") if selected else None
        ),
        "sum_first_page_listed_sizes_bytes_not_total": str(sum(
            int(item["size"]) for item in selected
            if isinstance(item.get("size"), str) and item["size"].isdecimal()
        )),
        "raw_event_rows_downloaded_from_this_table": False,
        "not_total_shards_when_paginated": True,
    }
    return summary, selected


def select_sole_machine_source(summary: dict, shards: list[dict]) -> dict:
    if (summary["table"] != "machine_events"
            or summary["inventory_incomplete_due_to_pagination"]
            or len(shards) != 1):
        raise MachineCoverageFailure(
            "No verified single-shard complete machine_events inventory"
        )
    obj = shards[0]
    generation, size = obj.get("generation"), obj.get("size")
    if not isinstance(generation, str) or not generation.isdecimal():
        raise MachineCoverageFailure("Original machine generation not available")
    if not isinstance(size, str) or not size.isdecimal():
        raise MachineCoverageFailure("Original machine size not numeric")
    if int(size) <= 0 or int(size) > MAX_COMPRESSED:
        raise MachineCoverageFailure("Machine source exceeds frozen full-object size cap")
    if not isinstance(obj.get("md5Hash"), str):
        raise MachineCoverageFailure("Official full-object MD5 unavailable")
    return {
        "name": obj["name"], "generation": generation,
        "advertised_full_size_bytes": int(size),
        "provider_full_md5_base64": obj["md5Hash"],
        "provider_crc32c_base64_unverified": obj.get("crc32c"),
    }


def download_exact_complete_machine_object(metadata: dict) -> tuple[bytes, dict]:
    url = media_url(metadata["name"], metadata["generation"])
    chunks, downloaded = [], 0
    with source_opener().open(Request(url, headers={
        "User-Agent": "relational-persistence-RP-E012-D03-complete-machine"
    }), timeout=45) as response:
        if response.status not in (200, 206):
            raise SourceAccess("Original machine source status is not 200/206")
        server_generation = response.headers.get("x-goog-generation")
        if server_generation and server_generation != metadata["generation"]:
            raise SourceIdentityFailure("Original machine GCS generation changed")
        while downloaded <= MAX_COMPRESSED:
            chunk = response.read(min(CHUNK_SIZE, MAX_COMPRESSED + 1-downloaded))
            if not chunk:
                break
            downloaded += len(chunk)
            chunks.append(chunk)
            if downloaded > MAX_COMPRESSED:
                raise SourceIdentityFailure("Complete original machine bytes exceed safety cap")
        full = b"".join(chunks)
        http_status = response.status
    if len(full) != metadata["advertised_full_size_bytes"]:
        raise SourceIdentityFailure("Full original bytes not equal declared generation size")
    actual_md5 = base64.b64encode(md5(full).digest()).decode("ascii")
    if actual_md5 != metadata["provider_full_md5_base64"]:
        raise SourceIdentityFailure("Original publisher MD5 disagrees with full bytes")
    return full, {
        "full_object_bytes_downloaded": len(full),
        "original_full_compressed_object_sha256": sha256(full).hexdigest(),
        "full_object_provider_md5_verified": True,
        "publisher_generation_requested": metadata["generation"],
        "full_object_http_status": http_status,
        "entire_object_authenticated_not_prefix_only": True,
    }


def decompress_full_gzip(raw: bytes) -> bytes:
    try:
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        expanded = decoder.decompress(raw, MAX_EXPANDED + 1)
        if (len(expanded) > MAX_EXPANDED or decoder.unconsumed_tail
                or not decoder.eof or decoder.unused_data):
            raise MachineFormatFailure("Full gzip did not terminate cleanly under bound")
        expanded += decoder.flush()
    except zlib.error as exc:
        raise MachineFormatFailure("Original complete gzip failed CRC/format") from exc
    if len(expanded) > MAX_EXPANDED or not expanded.endswith(b"\n"):
        raise MachineFormatFailure("Expanded source exceeds cap or has incomplete line")
    return expanded


def _fields_from_raw_line(raw: bytes) -> dict:
    """Oracle B: bounded byte-level extraction of source's scalar fields.

    This is separate from JSON decoding, rejects unquoted scalar ints.
    Nested object fields do not match the chosen field names in the
    publisher's original MachineEvent shape.
    """
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise MachineFormatFailure("Original JSON event not UTF-8") from exc
    result = {}
    for match in CORE_PATTERN.finditer(text):
        name, value = match.groups()
        if name in result:
            raise MachineOracleDisagreement("Repeated core name in raw source row")
        result[name] = int(value)
    if not set(CORE_NAMES).issubset(result):
        raise MachineFormatFailure("Independent raw scalar parser missed required keys")
    return result


def parse_machine_events(original_uncompressed: bytes) -> list[dict]:
    if len(original_uncompressed) > MAX_EXPANDED:
        raise MachineFormatFailure("Original expanded event bytes exceed bound")
    try:
        lines = original_uncompressed.split(b"\n")
    except Exception as exc:
        raise MachineFormatFailure("Original source cannot be split") from exc
    if lines[-1] != b"" or not 1 <= len(lines)-1 <= MAX_RECORDS:
        raise MachineFormatFailure("Incomplete trailing row or event count out of bound")
    events = []
    for raw in lines[:-1]:
        if not raw.strip():
            raise MachineFormatFailure("Blank original event row")
        try:
            obj = json.loads(raw.decode("utf-8", "strict"), parse_constant=lambda _: (
                _ for _ in ()).throw(MachineFormatFailure("JSON nonfinite scalar")))
        except (ValueError, UnicodeError) as exc:
            raise MachineFormatFailure("Original event JSON rejected") from exc
        if not isinstance(obj, dict):
            raise MachineFormatFailure("Original machine row not mapping")
        if any(name not in obj for name in CORE_NAMES):
            raise MachineFormatFailure("Missing original machine identity/time/type")
        try:
            known = {k: _canonical_int(obj[k], unsigned=True) for k in CORE_NAMES}
            missing = (_canonical_int(obj["missing_type"], unsigned=True)
                       if obj.get("missing_type") is not None else 0)
        except PrefixInvalid as exc:
            raise MachineFormatFailure("Original decimal time/type/ID field rejected") from exc
        if known["type"] not in (1, 2, 3) or missing not in range(6):
            raise MachineFormatFailure("Invalid original machine event enum/missing_type")
        separately = _fields_from_raw_line(raw)
        if (any(separately[k] != known[k] for k in CORE_NAMES)
                or (("missing_type" in separately) !=
                    (obj.get("missing_type") is not None))
                or (obj.get("missing_type") is not None
                    and separately["missing_type"] != missing)):
            raise MachineOracleDisagreement("Independent original event-field oracles disagree")
        events.append({
            "time": known["time"], "machine": known["machine_id"],
            "type": known["type"], "missing": missing,
            "has_capacity": "capacity" in obj,
        })
    return events


def _latest_category(entries: list[dict], origin: int) -> str | None:
    candidates = [e for e in entries if e["time"] < origin]
    if not candidates:
        return None
    final_time = max(e["time"] for e in candidates)
    last = [e for e in candidates if e["time"] == final_time]
    if len({e["type"] for e in last}) > 1:
        return "ambiguous_last_event_tie"
    if any(e["missing"] != 0 for e in last):
        return "uncertain_due_to_reconstructed_event"
    return ("last_event_implied_removed" if last[0]["type"] == 2
            else "last_event_implied_active")


def independent_snapshot_oracles(events: list[dict], origin: int) -> dict:
    """Oracle A chronologically group/sort and B scan per entity independently."""
    groups = defaultdict(list)
    for row in events:
        groups[row["machine"]].append(row)
    states_a = Counter()
    for rows in groups.values():
        sorted_rows = sorted(
            (r for r in rows if r["time"] < origin),
            key=lambda r: (r["time"], r["type"]))
        if not sorted_rows:
            states_a["no_prior_event"] += 1
            continue
        top_time = sorted_rows[-1]["time"]
        latest = [r for r in sorted_rows if r["time"] == top_time]
        if len({r["type"] for r in latest}) > 1:
            key = "ambiguous_last_event_tie"
        elif any(r["missing"] for r in latest):
            key = "uncertain_due_to_reconstructed_event"
        else:
            key = ("last_event_implied_removed" if latest[-1]["type"] == 2
                   else "last_event_implied_active")
        states_a[key] += 1
    states_b = Counter()
    for rows in groups.values():
        label = _latest_category(rows, origin)
        states_b[label or "no_prior_event"] += 1
    if states_a != states_b:
        raise MachineOracleDisagreement("Independent temporal snapshot classifications differ")
    if sum(states_a.values()) != len(groups):
        raise MachineOracleDisagreement("Snapshot does not partition all unique machine IDs")
    return dict(sorted(states_a.items()))


def summarize_all_original_machine_events(events: list[dict]) -> dict:
    groups = defaultdict(list)
    for row in events:
        groups[row["machine"]].append(row)
    seen_times = [e["time"] for e in events]
    time_type_sets = defaultdict(set)
    for row in events:
        time_type_sets[(row["machine"], row["time"])].add(row["type"])
    tie_groups = Counter((row["machine"], row["time"]) for row in events)
    return {
        "all_complete_machine_event_rows": len(events),
        "distinct_machine_ids_aggregate_only": len(groups),
        "event_type_counts": dict(sorted((str(k), v) for k, v in
                                          Counter(row["type"] for row in events).items())),
        "rows_with_capacity_field": sum(e["has_capacity"] for e in events),
        "rows_with_nonzero_missing_type": sum(bool(e["missing"]) for e in events),
        "missing_type_code_counts": dict(sorted((str(k), v) for k, v in
                                                 Counter(e["missing"] for e in events).items())),
        "original_file_adjacent_timestamp_inversions": sum(
            left > right for left, right in zip(seen_times, seen_times[1:])
        ),
        "original_minimum_timestamp_us": min(seen_times),
        "original_maximum_timestamp_us": max(seen_times),
        "same_machine_same_timestamp_tie_groups": sum(v>1 for v in tie_groups.values()),
        "conflicting_same_machine_same_timestamp_type_groups": sum(
            len(kinds)>1 for kinds in time_type_sets.values()),
        "snapshots_strict_before_origin": {
            str(origin): independent_snapshot_oracles(events, origin)
            for origin in ORIGINS
        },
        "no_observed_machine_ids_or_event_rows_persisted": True,
        "timestamp_is_not_proven_online_release_time": True,
        "event_implied_state_not_full_live_capacity": True,
    }


def audit_original() -> dict:
    result = {
        "protocol": PROTOCOL, "preregistration_commit": PREREG,
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "original_code_commit": os.environ.get("GITHUB_SHA"),
        "source_provider": "Google Borg 2019 cell a", "source_bucket": BUCKET,
        "original_decision": "SOURCE_ACCESS_BLOCKED",
        "metadata_first_page": {}, "machine_source": None, "machine_counts": None,
        "joint_causal_history": "JOINT_CAUSAL_HISTORY_NOT_CERTIFIED",
        "collection_and_instance_raw_event_rows_downloaded": 0,
        "forecast_targets_computed": False, "bigquery_or_paid_credentials_used": False,
        "full_online_event_release_history_proven": False,
        "real_running_job_hard_walltime_cap_verified": False,
        "new_lean_theorem_or_physical_law_claimed": False,
        "errors": [],
    }
    stage = None
    try:
        pages = {}
        for table in TABLES:
            stage = f"official_metadata:{table}"
            summary, entries = fetch_inventory_page(table)
            result["metadata_first_page"][table] = summary
            pages[table] = entries
        stage = "single_machine_full_source_coverage"
        metadata = select_sole_machine_source(
            result["metadata_first_page"]["machine_events"],
            pages["machine_events"],
        )
        # Keep original generation/advertised size before reading.
        result["machine_source"] = metadata
        stage = "original_full_machine_media"
        original_bytes, signed = download_exact_complete_machine_object(metadata)
        result["machine_source"].update(signed)
        stage = "full_gzip_and_schema"
        expanded = decompress_full_gzip(original_bytes)
        del original_bytes
        rows = parse_machine_events(expanded)
        del expanded
        stage = "independent_event_state_oracles"
        counts = summarize_all_original_machine_events(rows)
        del rows
        result["machine_counts"] = counts
        result["original_decision"] = "MACHINE_EVENTS_COMPLETE_OBJECT_AUDITED_JOINT_UNCERTIFIED"
    except MachineCoverageFailure as exc:
        result["original_decision"] = "MACHINE_SOURCE_COVERAGE_UNVERIFIED"
        result["errors"].append({"stage": stage, "reason": str(exc)[:280]})
    except SourceIdentityFailure as exc:
        result["original_decision"] = "MACHINE_SOURCE_IDENTITY_REJECTED"
        result["errors"].append({"stage": stage, "reason": str(exc)[:280]})
    except MachineOracleDisagreement as exc:
        result["original_decision"] = "MACHINE_EVENT_CONSISTENCY_REJECTED"
        result["errors"].append({"stage": stage, "reason": str(exc)[:280]})
    except (MachineFormatFailure, PrefixInvalid) as exc:
        result["original_decision"] = "MACHINE_EVENT_FORMAT_REJECTED"
        result["errors"].append({"stage": stage, "reason": str(exc)[:280]})
    except (SourceAccess, HTTPError, URLError, TimeoutError, OSError, ValueError,
            KeyError) as exc:
        result["original_decision"] = "SOURCE_ACCESS_BLOCKED"
        result["errors"].append({
            "stage": stage, "reason": f"{type(exc).__name__}: {str(exc)[:280]}"
        })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite original RP-E012-D03 run")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = audit_original()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "protocol": PROTOCOL, "decision": report["original_decision"],
        "machine_events": (report["machine_counts"] or {}).get(
            "all_complete_machine_event_rows"),
        "joint_history": report["joint_causal_history"],
        "errors": report["errors"],
    }, sort_keys=True))
    if report["original_decision"] != "MACHINE_EVENTS_COMPLETE_OBJECT_AUDITED_JOINT_UNCERTIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
