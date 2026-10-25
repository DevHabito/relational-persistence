"""RP-E011-D01: first-party Polaris CSV SOURCE-ELIGIBILITY ONLY.

The precise source catalog, document metadata, gates and restrictions were
frozen on main BEFORE this code or any Polaris data acquisition.

DO NOT compute predictive targets, fit a model, inspect a holdout error,
redistribute individual jobs, or validate a proposed physical law here.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import gzip
from hashlib import sha256
from html.parser import HTMLParser
from io import StringIO
import json
import os
from pathlib import Path
import platform
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

PROTOCOL = "RP-E011-D01"
PAGE = (
    "https://reports.alcf.anl.gov/data/"
    "ANL-ALCF-DJC-POLARIS_20220809_20221231.html"
)
FILENAME = "ANL-ALCF-DJC-POLARIS_20220809_20221231.csv"
ORIGIN = "reports.alcf.anl.gov"
EXPECTED_CSV_BYTES = 27_825_794
CATALOG_COMPRESSED_BYTES = 2_261_468
MAX_DOWNLOAD_BYTES = 36_000_000
TIMESTAMP_FORMAT = "YYYY-MM-DD HH:MM:SS[.fraction]"
REQUIRED_COLUMNS = (
    "COBALT_JOBID", "MACHINE_NAME", "QUEUED_TIMESTAMP",
    "START_TIMESTAMP", "END_TIMESTAMP", "QUEUE_NAME",
    "NODES_REQUESTED", "NODES_USED", "WALLTIME_SECONDS",
    "QUEUED_WAIT_SECONDS", "ELIGIBLE_WAIT_SECONDS",
    "DATA_LOAD_STATUS",
)
MISSING = ("", "NULL", "null", "None", "none")


class SourceBlocked(Exception):
    """No verified official source; never substitute an unofficial mirror."""


class DownloadLinks(HTMLParser):
    """Discover explicit URLs/actions advertised by the canonical page."""

    def __init__(self) -> None:
        super().__init__()
        self.urls: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        info = dict(attrs)
        for prop in ("href", "action", "data-href", "data-url", "data-download"):
            value = info.get(prop)
            if value:
                self.urls.append((f"{tag}.{prop}", value))
        javascript = info.get("onclick", "")
        if javascript:
            for value in re.findall(r"['\"]([^'\"]+)['\"]", javascript):
                self.urls.append((f"{tag}.onclick", value))
        # A named download button can point to an official same-origin endpoint.
        # Ignore href-less download labels rather than fabricate a URL.
        if (info.get("download") == FILENAME and info.get("href")):
            self.urls.append((f"{tag}.named-download", info["href"]))


def official_url(url: str) -> bool:
    parts = urlsplit(url)
    return (parts.scheme == "https" and parts.hostname == ORIGIN
            and parts.username is None and parts.password is None
            and parts.port in (None, 443))


def resolve_download(page: str) -> tuple[str, dict]:
    parser = DownloadLinks()
    parser.feed(page)
    candidates = {}
    for method, value in parser.urls:
        absolute = urljoin(PAGE, value.strip())
        if not official_url(absolute):
            continue
        path = urlsplit(absolute).path.lower()
        # Direct source (or explicitly linked official download endpoint).
        if (FILENAME.lower() in absolute.lower()
                and (path.endswith(".csv") or path.endswith(".csv.gz")
                     or "download" in path)):
            candidates.setdefault(absolute, set()).add(method)
    info = {
        "html_sha256": sha256(page.encode("utf-8")).hexdigest(),
        "linked_urls_total": len(parser.urls),
        "trusted_matching_direct_downloads": len(candidates),
        "matching_resolution_methods": sorted({
            name for methods in candidates.values() for name in methods
        }),
    }
    if len(candidates) != 1:
        raise SourceBlocked(
            "Official page does not expose exactly one qualifying download action; "
            f"matched={len(candidates)}, scanned={len(parser.urls)}"
        )
    url = next(iter(candidates))
    if url == PAGE:
        raise SourceBlocked("Only a metadata page was discovered")
    return url, info


def open_official(url: str, *, max_bytes: int) -> tuple[bytes, dict]:
    if not official_url(url):
        raise SourceBlocked("Off-origin or non-HTTPS source blocked")
    request = Request(
        url,
        headers={
            "User-Agent": "relational-persistence-RP-E011-D01/1.0",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            final = response.geturl()
            if not official_url(final):
                raise SourceBlocked("Download redirected outside official origin")
            payload = response.read(max_bytes + 1)
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            content_disposition = response.headers.get("Content-Disposition", "")
    except (OSError, TimeoutError) as exc:
        raise SourceBlocked(f"Cannot access official URL: {type(exc).__name__}") from exc
    if len(payload) > max_bytes:
        raise SourceBlocked("Official response exceeds frozen maximum size")
    if status != 200:
        raise SourceBlocked(f"Official resource returned HTTP status {status}")
    return payload, {
        "requested_url": url, "final_url": final, "http_status": status,
        "content_type": content_type,
        "content_disposition": content_disposition,
        "downloaded_bytes": len(payload),
        "downloaded_sha256": sha256(payload).hexdigest(),
    }


def decode_response(payload: bytes) -> tuple[bytes, str]:
    if payload[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(payload)
        except (OSError, EOFError) as exc:
            raise ValueError("Invalid official gzip content") from exc
        if len(raw) > EXPECTED_CSV_BYTES + 1:
            raise ValueError("Decompressed official CSV is oversized")
        return raw, "gzip"
    if payload.lstrip().startswith((b"<!DOCTYPE", b"<html", b"<HTML")):
        raise SourceBlocked("Official download resolves to HTML instead of CSV")
    return payload, "plain-csv"


def safe_decimal(value: str | None) -> Decimal | None:
    if value is None or value.strip() in MISSING:
        return None
    try:
        result = Decimal(value.strip())
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def safe_time(value: str | None) -> datetime | None:
    if value is None or value.strip() in MISSING:
        return None
    try:
        result = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    # Existing data dictionary does not specify timezone normalization.
    # Validate timestamps, recording naive/aware status without coercion.
    return result


def structural_audit(source: bytes) -> dict:
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("CSV is not valid UTF-8") from exc
    rows = csv.DictReader(StringIO(text, newline=""))
    fieldnames = rows.fieldnames or []
    missing_cols = sorted(set(REQUIRED_COLUMNS) - set(fieldnames))
    counts = Counter()
    job_ids = set()
    queues = set()
    tz_kinds = Counter()
    statuses = Counter()
    first_errors = []
    for i, row in enumerate(rows, 2):
        counts["data_rows"] += 1
        if row.get(None) is not None or any(row.get(name) is None for name in fieldnames):
            counts["bad_width"] += 1
            if len(first_errors) < 10:
                first_errors.append({"row": i, "error": "CSV field count mismatch"})
            continue

        ident = row.get("COBALT_JOBID")
        if not ident or not ident.strip():
            counts["missing_job_id"] += 1
        else:
            try:
                value = int(ident)
                if value < 0:
                    raise ValueError("Negative job ID")
            except ValueError:
                counts["invalid_job_id"] += 1
            else:
                if value in job_ids:
                    counts["duplicate_job_id"] += 1
                job_ids.add(value)

        times = {}
        for key in ("QUEUED_TIMESTAMP", "START_TIMESTAMP", "END_TIMESTAMP"):
            value = safe_time(row.get(key))
            times[key] = value
            if value is None:
                counts[f"missing_or_invalid_{key.lower()}"] += 1
            else:
                tz_kinds["aware" if value.tzinfo is not None else "naive"] += 1

        numeric = {}
        for key in (
            "NODES_REQUESTED", "NODES_USED", "WALLTIME_SECONDS",
            "QUEUED_WAIT_SECONDS", "ELIGIBLE_WAIT_SECONDS",
        ):
            numeric[key] = safe_decimal(row.get(key))
            if numeric[key] is None:
                counts[f"missing_or_invalid_{key.lower()}"] += 1
            elif numeric[key] < 0:
                counts[f"negative_{key.lower()}"] += 1

        queue = (row.get("QUEUE_NAME") or "").strip()
        if not queue:
            counts["missing_queue_name"] += 1
        else:
            queues.add(queue)
        state = (row.get("DATA_LOAD_STATUS") or "").strip()
        statuses["missing" if not state else "present"] += 1

        queued, started = times["QUEUED_TIMESTAMP"], times["START_TIMESTAMP"]
        valid_order = False
        if queued is not None and started is not None:
            try:
                valid_order = started >= queued
            except TypeError:
                counts["timezone_mismatch"] += 1
            if not valid_order:
                counts["start_before_queue_or_noncomparable"] += 1
            if valid_order and numeric["QUEUED_WAIT_SECONDS"] is not None:
                difference = Decimal(str((started - queued).total_seconds()))
                if abs(difference - numeric["QUEUED_WAIT_SECONDS"]) > 1:
                    counts["documented_queued_wait_disagreements_over_1s"] += 1
        else:
            counts["unknown_queue_to_start_interval"] += 1

        if (valid_order and queue
                and numeric["NODES_REQUESTED"] is not None
                and numeric["NODES_REQUESTED"] > 0):
            counts["structurally_usable_queued_and_started_rows"] += 1

    # Independent reader: separate CSV row-width count on identical bytes.
    other = csv.reader(StringIO(text, newline=""))
    try:
        other_header = next(other)
    except StopIteration:
        other_header = []
    other_total = other_wrong = 0
    for fields in other:
        other_total += 1
        other_wrong += int(len(fields) != len(other_header))

    outcome = {
        "data_rows": counts["data_rows"],
        "wrong_width_rows": counts["bad_width"],
        "independent_csv_reader_rows": other_total,
        "independent_csv_reader_wrong_width_rows": other_wrong,
        "independent_csv_readers_agree": (
            other_header == fieldnames and
            other_total == counts["data_rows"] and
            other_wrong == counts["bad_width"]
        ),
        "field_names": fieldnames,
        "missing_required_columns": missing_cols,
        "distinct_nonempty_queue_name_count": len(queues),
        "job_id_distinct_count": len(job_ids),
        "missing_and_invalid_counts": dict(sorted(counts.items())),
        "timezone_timestamp_forms": dict(sorted(tz_kinds.items())),
        "data_load_status_presence_only": dict(sorted(statuses.items())),
        "first_source_quality_errors": first_errors,
    }
    return outcome


def source_gate(csv_bytes: bytes, inspection: dict) -> str:
    counts = inspection["missing_and_invalid_counts"]
    if (len(csv_bytes) != EXPECTED_CSV_BYTES
            or not inspection["independent_csv_readers_agree"]
            or inspection["wrong_width_rows"] != 0
            or inspection["missing_required_columns"]
            or counts.get("duplicate_job_id", 0)
            or counts.get("invalid_job_id", 0)
            or inspection["distinct_nonempty_queue_name_count"] < 2
            or counts.get("structurally_usable_queued_and_started_rows", 0) < 1000):
        return "DATASET_SCHEMA_REJECTED"
    return "DATASET_SCHEMA_VERIFIED"


def first_audit(output: Path, *, page_override: str | None = None,
                download_override: bytes | None = None) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Cannot overwrite first RP-E011 source audit")
    output.mkdir(parents=True, exist_ok=True)
    record = {
        "protocol": PROTOCOL,
        "first_github_run_id": os.getenv("GITHUB_RUN_ID"),
        "first_github_source_commit": os.getenv("GITHUB_SHA"),
        "official_resource_page": PAGE,
        "provider": "Argonne Leadership Computing Facility",
        "original_provider_citation": (
            "This data was generated from resources of the Argonne "
            "Leadership Computing Facility, which is a DOE Office of "
            "Science User Facility supported under Contract DE-AC02-06CH11357."
        ),
        "catalog_declared_raw_csv_bytes": EXPECTED_CSV_BYTES,
        "catalog_declared_compressed_bytes": CATALOG_COMPRESSED_BYTES,
        "timestamp_format": TIMESTAMP_FORMAT,
        "source_version_pinned_before_retrieval": False,
        "new_lean_theorem": False,
        "queue_prediction_scored": False,
        "physical_law_validated": False,
        "decision": "SOURCE_ACCESS_BLOCKED",
        "acquisition": None, "schema": None, "errors": [],
    }
    try:
        if page_override is None:
            page_bytes, meta = open_official(PAGE, max_bytes=2_000_000)
            page = page_bytes.decode("utf-8", errors="strict")
        else:
            page = page_override
            meta = {"requested_url": PAGE, "final_url": PAGE,
                    "http_status": 200, "fixture_only": True}
        url, resolution = resolve_download(page)
        record["acquisition"] = {
            "catalog_page": meta,
            "resolution": resolution,
            "download_url": url,
        }
        if download_override is None:
            payload, headers = open_official(url, max_bytes=MAX_DOWNLOAD_BYTES)
        else:
            payload = download_override
            headers = {"fixture_only": True, "final_url": url,
                       "downloaded_bytes": len(payload),
                       "downloaded_sha256": sha256(payload).hexdigest()}
        raw, encoding = decode_response(payload)
        record["acquisition"].update({
            "download": headers, "encoding": encoding,
            "uncompressed_csv_bytes": len(raw),
            "uncompressed_csv_sha256": sha256(raw).hexdigest(),
        })
        # Even a size mismatch must be kept as a source rejection.
        if len(raw) != EXPECTED_CSV_BYTES:
            record["decision"] = "DATASET_SCHEMA_REJECTED"
            record["errors"].append({
                "stage": "catalog content length", "reason":
                f"Original CSV bytes={len(raw)} but catalog declares {EXPECTED_CSV_BYTES}",
            })
        else:
            schema = structural_audit(raw)
            record["schema"] = schema
            record["decision"] = source_gate(raw, schema)
        # Retain only as a temporary Actions artifact; not in Git.
        (output / "temporary-provider-original.bytes").write_bytes(payload)
    except SourceBlocked as exc:
        record["errors"].append({
            "stage": "official-source-access",
            "reason": str(exc)[:600],
        })
    except (ValueError, UnicodeError, OSError, csv.Error) as exc:
        record["decision"] = "DATASET_SCHEMA_REJECTED"
        record["errors"].append({
            "stage": "source-format",
            "reason": f"{type(exc).__name__}: {str(exc)[:500]}",
        })
    finally:
        (output / "RP-E011-D01.json").write_text(
            json.dumps(record, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = first_audit(args.output)
    print(json.dumps({
        "decision": record["decision"],
        "download_bytes": record["acquisition"]["uncompressed_csv_bytes"]
        if record["acquisition"] and "uncompressed_csv_bytes" in record["acquisition"]
        else None,
        "queue_count": record["schema"]["distinct_nonempty_queue_name_count"]
        if record["schema"] else None,
        "errors": record["errors"],
    }, sort_keys=True))
    if record["decision"] != "DATASET_SCHEMA_VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
