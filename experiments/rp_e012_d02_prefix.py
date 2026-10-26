"""RP-E012-D02: bounded source-prefix audit of original Google Borg 2019 GCS JSON.

Protocol frozen on main at e5efc724 before implementation, metadata or rows.
Google documentation identifying public object buckets was known beforehand.
No BigQuery, billed credentials, alternative mirrors or model forecasts.

This intentionally examines at most 500 prefix records for TWO shard files;
it is never a random or representative sample of any cell/table.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode, quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.error import HTTPError, URLError
import zlib

PROTOCOL = "RP-E012-D02"
PREREG = "e5efc72498fb3377aed4fd5302a288df95c57a23"
BUCKET = "clusterdata_2019_a"
TABLES = ("machine_events", "instance_events")
HOST = "storage.googleapis.com"
MAX_METADATA_BYTES = 1_048_576
MAX_COMPRESSED = 2_097_152
MAX_UNCOMPRESSED = 4_194_304
MAX_ROWS = 500
READ_CHUNK = 16_384


class SourceAccess(Exception):
    """Official GCS access/metadata was blocked. Never use a fallback."""


class PrefixInvalid(Exception):
    """Bounded original prefix violates preregistered format checks."""


class HostRestrictedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        info = urlsplit(newurl)
        if info.scheme != "https" or info.hostname != HOST:
            raise SourceAccess("Original publisher redirected off approved HTTPS host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def source_opener():
    return build_opener(HostRestrictedRedirect())


def metadata_url(table: str) -> str:
    if table not in TABLES:
        raise SourceAccess("Unregistered table requested")
    params = urlencode({
        "prefix": table + "-",
        "maxResults": 100,
        "fields": "items(name,size,generation,md5Hash,crc32c),nextPageToken",
    })
    return f"https://{HOST}/storage/v1/b/{BUCKET}/o?{params}"


def media_url(name: str, generation: str) -> str:
    if not generation.isdecimal() or int(generation) < 1:
        raise SourceAccess("Source generation not a positive decimal string")
    if "/" in name or ".." in name or not re.fullmatch(
        r"(?:machine_events|instance_events)-[0-9]+\.json\.(?:gzip|gz)",
        name
    ):
        raise SourceAccess("Unregistered GCS source object")
    return (
        f"https://{HOST}/storage/v1/b/{BUCKET}/o/"
        f"{quote(name, safe='')}?{urlencode({'alt': 'media', 'generation': generation})}"
    )


def select_exact_first_shard(table: str, listing: dict) -> dict:
    """Lexicographic first of the first 100 provider-listed metadata entries."""
    if not isinstance(listing, dict) or not isinstance(listing.get("items"), list):
        raise SourceAccess("No usable official object metadata listing")
    if len(listing["items"]) > 100:
        raise SourceAccess("Provider listing exceeds frozen maxResults")
    pattern = re.compile(r"^" + re.escape(table) + r"-[0-9]+\.json\.(?:gzip|gz)$")
    chosen = sorted(
        (item for item in listing["items"] if isinstance(item, dict)
         and isinstance(item.get("name"), str)
         and pattern.fullmatch(item["name"])),
        key=lambda x: x["name"],
    )
    if not chosen:
        raise SourceAccess("No frozen-table gzip object in first 100 metadata entries")
    obj = chosen[0]
    name = obj["name"]
    generation = obj.get("generation")
    size = obj.get("size")
    if (not isinstance(generation, str) or not generation.isdecimal()
            or int(generation) < 1 or not isinstance(size, str)
            or not size.isdecimal() or int(size) < 1):
        raise SourceAccess("Provider object size/generation metadata unavailable")
    return {
        "name": name, "generation": generation, "full_object_size_bytes": size,
        "provider_md5Hash_whole_object_unverified": obj.get("md5Hash"),
        "provider_crc32c_whole_object_unverified": obj.get("crc32c"),
        "metadata_selection": "lexicographically_first_valid_shard_in_first_100",
        "first_100_listing_was_paginated": bool(listing.get("nextPageToken")),
    }


def list_official(table: str) -> dict:
    with source_opener().open(
        Request(metadata_url(table), headers={
            "User-Agent": "relational-persistence-RP-E012-D02-no-paid-query"
        }), timeout=25,
    ) as response:
        if response.status != 200:
            raise SourceAccess(f"Metadata listing HTTP status {response.status}")
        data = response.read(MAX_METADATA_BYTES + 1)
    if len(data) > MAX_METADATA_BYTES:
        raise SourceAccess("Publisher metadata exceeded source size budget")
    try:
        listing = json.loads(data, parse_constant=lambda _: (_ for _ in ()).throw(
            SourceAccess("Nonfinite provider metadata")))
    except (UnicodeError, ValueError) as exc:
        raise SourceAccess("Invalid original GCS listing JSON") from exc
    return select_exact_first_shard(table, listing)


def _canonical_int(value, *, unsigned: bool = False) -> int:
    if not isinstance(value, str) or not re.fullmatch(
        r"(?:0|[1-9][0-9]*)" if unsigned else r"(?:0|-?[1-9][0-9]*)",
        value,
    ):
        raise PrefixInvalid("Noncanonical decimal STRING identity/time/type")
    integer = int(value)
    if unsigned and integer < 0:
        raise PrefixInvalid("Negative origin time or event type")
    try:
        alternative = Decimal(value)
    except InvalidOperation as exc:
        raise PrefixInvalid("Independent decimal parser rejected field") from exc
    if alternative != integer:
        raise PrefixInvalid("Two numeric parsers disagree")
    return integer


def verify_line(line: bytes, table: str) -> tuple[dict, dict]:
    """JSON + separately validated original decimal-string event fields."""
    try:
        item = json.loads(line.decode("utf-8", "strict"),
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              PrefixInvalid("NaN/Infinity invalid JSON")))
    except (UnicodeError, ValueError) as exc:
        raise PrefixInvalid("Strict UTF-8/JSON row rejected") from exc
    if not isinstance(item, dict):
        raise PrefixInvalid("Original line not a JSON object")
    mandatory = (
        ("time", "machine_id", "type") if table == "machine_events"
        else ("time", "collection_id", "instance_index", "type")
    )
    if any(name not in item for name in mandatory):
        raise PrefixInvalid("Missing mandatory original event identity/time/type")
    moment = _canonical_int(item["time"], unsigned=True)
    event_type = _canonical_int(item["type"], unsigned=True)
    _canonical_int(item["machine_id"] if table == "machine_events"
                   else item["collection_id"])
    if table == "instance_events":
        _canonical_int(item["instance_index"])
    allowed = {1, 2, 3} if table == "machine_events" else set(range(11))
    if event_type not in allowed:
        raise PrefixInvalid("Original event type outside declared v3 enum")
    missing = item.get("missing_type")
    if missing is not None:
        missing_type = _canonical_int(missing, unsigned=True)
        if missing_type not in set(range(6)):
            raise PrefixInvalid("Unknown original missing-event kind")
    else:
        missing_type = None
    return item, {
        "time": moment, "type": event_type,
        "nonzero_missing_flag": bool(missing_type),
        "declares_missing_type": missing is not None,
    }


def parse_bounded_gzip_prefix(compressed_chunks: list[bytes], table: str) -> dict:
    """Parse at most 500 complete lines, and at most the registered budgets.

    Intended for an HTTP prefix. No gzip trailer/CRC guarantee unless
    the complete compressed stream happens to end inside the prefix.
    """
    if table not in TABLES:
        raise PrefixInvalid("Unregistered table")
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    buffer = bytearray()
    byte_counter = 0
    expanded = 0
    observed = []
    content = bytearray()
    source_exhausted = False
    for chunk in compressed_chunks:
        if not isinstance(chunk, bytes):
            raise PrefixInvalid("Gzip chunk must be original bytes")
        byte_counter += len(chunk)
        if byte_counter > MAX_COMPRESSED:
            raise PrefixInvalid("Compressed prefix exceeded safety limit")
        content.extend(chunk)
        try:
            data = decoder.decompress(chunk, MAX_UNCOMPRESSED - expanded + 1)
        except zlib.error as exc:
            raise PrefixInvalid("Source is not a valid gzip prefix") from exc
        expanded += len(data)
        if expanded > MAX_UNCOMPRESSED or decoder.unconsumed_tail:
            raise PrefixInvalid("Original gzip expansion exceeded safety cap")
        buffer.extend(data)
        while b"\n" in buffer and len(observed) < MAX_ROWS:
            row, _, rest = buffer.partition(b"\n")
            buffer = bytearray(rest)
            if not row.strip():
                raise PrefixInvalid("Empty original production event line")
            _, item = verify_line(bytes(row), table)
            observed.append(item)
        if len(observed) >= MAX_ROWS:
            break
        if decoder.eof:
            source_exhausted = True
            break
    if not observed:
        raise PrefixInvalid("No complete valid original event lines in bounded prefix")
    times = [row["time"] for row in observed]
    events = Counter(str(row["type"]) for row in observed)
    return {
        "parsed_complete_prefix_rows": len(observed),
        "compressed_prefix_bytes_consumed": byte_counter,
        "compressed_prefix_sha256": sha256(content).hexdigest(),
        "uncompressed_bytes_released_by_decoder": expanded,
        "gzip_member_end_reached": bool(decoder.eof),
        "gzip_trailer_validated": bool(decoder.eof),
        "incomplete_trailing_line_not_parsed": bool(buffer),
        "event_type_counts_prefix_only": dict(sorted(events.items())),
        "time_min_microseconds_from_trace_start": min(times),
        "time_max_microseconds_from_trace_start": max(times),
        "adjacent_event_time_inversions_in_prefix": sum(
            a > b for a, b in zip(times, times[1:])
        ),
        "rows_with_declared_missing_flag": sum(
            item["declares_missing_type"] for item in observed
        ),
        "rows_with_nonzero_missing_event_flag": sum(
            item["nonzero_missing_flag"] for item in observed
        ),
        "max_rows": MAX_ROWS,
        "no_production_ids_or_raw_lines_retained": True,
        "not_a_population_representative_sample": True,
    }


def strictly_available(event_time: int, origin_time: int,
                       *, reconstructed: bool = False) -> bool:
    return event_time < origin_time and not reconstructed


def usage_window_available(start: int, end: int, origin: int) -> bool:
    return start < end < origin


def synthetic_temporal_safety_gate() -> bool:
    return (
        strictly_available(99, 100)
        and not strictly_available(100, 100)
        and not strictly_available(101, 100)
        and not strictly_available(99, 100, reconstructed=True)
        and usage_window_available(0, 300, 301)
        and not usage_window_available(0, 300, 300)
        and not usage_window_available(0, 300, 150)
    )


def read_exact_prefix(table: str, metadata: dict) -> dict:
    url = media_url(metadata["name"], metadata["generation"])
    with source_opener().open(Request(
        url,
        headers={
            "Range": f"bytes=0-{MAX_COMPRESSED-1}",
            "User-Agent": "relational-persistence-RP-E012-D02-bounded-prefix",
        },
    ), timeout=40) as response:
        http_status = response.status
        if http_status not in (200, 206):
            raise SourceAccess(f"Original object download HTTP {http_status}")
        server_generation = response.headers.get("x-goog-generation")
        if (server_generation and
                server_generation != metadata["generation"]):
            raise SourceAccess("GCS object generation changed during read")
        content_range = response.headers.get("Content-Range")
        if http_status == 206 and (
            not content_range or not content_range.startswith("bytes 0-")
        ):
            raise SourceAccess("Partial GCS byte range does not start at zero")
        chunks = []
        consumed = 0
        pending = b""
        # Never read beyond 2MiB in total, even if Range was not honored.
        while consumed < MAX_COMPRESSED:
            chunk = response.read(min(READ_CHUNK, MAX_COMPRESSED - consumed))
            if not chunk:
                break
            consumed += len(chunk)
            chunks.append(chunk)
            # Termination bounded by the source reader's fixed bytes cap;
            # the decompressor may stop earlier if it reaches 500 rows.
    evidence = parse_bounded_gzip_prefix(chunks, table)
    if evidence["compressed_prefix_bytes_consumed"] > consumed:
        raise PrefixInvalid("Parser consumed unreceived source bytes")
    evidence["http_status"] = http_status
    evidence["server_content_range"] = content_range
    evidence["server_object_generation_confirmed"] = (
        server_generation == metadata["generation"]
        if server_generation is not None else None
    )
    evidence["requested_range"] = f"bytes=0-{MAX_COMPRESSED-1}"
    evidence["server_honored_range"] = http_status == 206
    evidence["full_object_digest_verified"] = False
    evidence["no_provider_runtime_walltime_enforcement_verified"] = True
    return evidence


def run_first(output: Path) -> dict:
    if output.exists():
        raise ValueError("Cannot overwrite first RP-E012-D02 original audit")
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "protocol": PROTOCOL,
        "preregistration_commit": PREREG,
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "original_code_commit": os.environ.get("GITHUB_SHA"),
        "source_bucket": BUCKET,
        "decision": "SOURCE_ACCESS_OR_LISTING_BLOCKED",
        "table_evidence": {},
        "errors": [],
        "synthetic_strict_causal_boundary_passed": False,
        "production_rows_are_nonrepresentative_prefixes": True,
        "complete_event_history_asserted": False,
        "bigquery_used": False,
        "user_auth_or_paid_query_used": False,
        "forecast_or_holdout_calculated": False,
        "physical_scalar_C_or_new_lean_theorem_claimed": False,
    }
    current_table = None
    try:
        if not synthetic_temporal_safety_gate():
            raise PrefixInvalid("Synthetic causal time boundary failed")
        report["synthetic_strict_causal_boundary_passed"] = True
        for table in TABLES:
            current_table = table
            metadata = list_official(table)
            report["table_evidence"][table] = {"object_metadata": metadata}
            try:
                prefixes = read_exact_prefix(table, metadata)
            except PrefixInvalid:
                raise
            report["table_evidence"][table]["prefix"] = prefixes
        report["decision"] = "SOURCE_PREFIX_AUDITED"
    except PrefixInvalid as exc:
        report["decision"] = "SOURCE_PREFIX_FORMAT_REJECTED"
        report["errors"].append({
            "table": current_table,
            "stage": "prefix-decompression-or-record-gate",
            "reason": str(exc)[:350],
        })
    except (SourceAccess, HTTPError, URLError, TimeoutError, OSError,
            UnicodeError, ValueError, KeyError) as exc:
        report["decision"] = "SOURCE_ACCESS_OR_LISTING_BLOCKED"
        report["errors"].append({
            "table": current_table,
            "stage": "original-official-source-access",
            "reason": f"{type(exc).__name__}: {str(exc)[:350]}",
        })
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_first(args.output)
    print(json.dumps({
        "protocol": PROTOCOL,
        "decision": report["decision"],
        "tables": list(report["table_evidence"]),
        "errors": report["errors"],
    }, sort_keys=True))
    if report["decision"] != "SOURCE_PREFIX_AUDITED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
