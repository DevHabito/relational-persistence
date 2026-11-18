"""RP-U008 first external publisher raw-trace audit, strictly read-only.

Download only a pinned externally collected single-vantage CSV. Authenticate
its original Git blob and byte size before parsing any source record. Emit
bounded, aggregated HTTP/gateway recovery observations, never private notes,
network addresses or the source's whole raw time series.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from experiments import rp_u008_external_recovery_core as core

ORIGINAL_URL = (
    "https://raw.githubusercontent.com/Ezharjan/LocalNetDynamicsDataset/"
    f"{core.SOURCE_COMMIT}/dataset/raw/localnet_desktop-eth_20260920_123407.csv"
)
FIRST_RESULT = Path("docs/results/RP-U008-P01-first-run/audit.json")
PROTOCOL_ONLY_COMMIT = "0cfd8327a58f4e507967b074e612c581a8f24a39"
SOURCE_FREE_IMPLEMENTATION = "f85229514fb2a447efbaf5c708ccf7e4522f7d43"
BUFFER_SIZE = 2**20


class NoSourceRedirects:
    """urllib-compatible opener; prevents silently swapping original sources."""

    def __init__(self) -> None:
        from urllib.request import HTTPRedirectHandler
        class NoRedirects(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        self.opener = build_opener(NoRedirects())

    def open(self, request, timeout):
        return self.opener.open(request, timeout=timeout)


def verify_publisher_source(body: bytes) -> dict:
    if not isinstance(body, bytes) or len(body) != core.SOURCE_SIZE:
        raise core.InvalidSource("PUBLISHER_RAW_FILE_BYTES_CHANGED")
    git_header = f"blob {len(body)}\0".encode("ascii")
    blob_id = sha1(git_header + body).hexdigest()
    if blob_id != core.SOURCE_BLOB_SHA1:
        raise core.InvalidSource("PINNED_PUBLISHER_GIT_OBJECT_CONFLICT")
    return {
        "publisher_commit": core.SOURCE_COMMIT,
        "publisher_original_git_blob_sha1": blob_id,
        "original_bytes": len(body),
        "original_sha256": sha256(body).hexdigest(),
        "verified_publisher_source_not_labelled_derivative": True,
    }


def fetch_publisher_raw(*, opener=None) -> tuple[bytes, dict]:
    external = opener if opener is not None else NoSourceRedirects()
    request = Request(
        ORIGINAL_URL, headers={"User-Agent": "RP-U008-P01-original-source/1"}
    )
    received = bytearray()
    try:
        with external.open(request, timeout=100) as response:
            if response.geturl() != ORIGINAL_URL:
                raise core.InvalidSource("PUBLISHER_SOURCE_REDIRECT_OR_LOCATION_CHANGED")
            while True:
                batch = response.read(BUFFER_SIZE)
                if not batch:
                    break
                if len(received) + len(batch) > core.SOURCE_SIZE:
                    raise core.InvalidSource("PUBLISHER_SOURCE_EXCEEDS_FROZEN_BYTE_COUNT")
                received.extend(batch)
    except (OSError, TimeoutError, HTTPError, URLError) as exc:
        raise core.InvalidSource("PINNED_ORIGINAL_PUBLISHER_SOURCE_UNAVAILABLE") from exc
    body = bytes(received)
    return body, verify_publisher_source(body)


def source_audit() -> dict:
    body, provenance = fetch_publisher_raw()
    try:
        text = body.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise core.InvalidSource("PUBLISHER_RAW_SOURCE_NOT_UTF8") from exc
    rows = core.parse_original(text)
    report = core.evaluate(rows)
    report.update({
        "source": provenance,
        "protocol_only_commit": PROTOCOL_ONLY_COMMIT,
        "pre_source_implementation_commit": SOURCE_FREE_IMPLEMENTATION,
        "first_utc": rows[0]["utc"],
        "last_utc": rows[-1]["utc"],
        "source_sampling_nominal_interval_seconds": 30,
        "first_run_no_original_csv_uploaded": True,
        "recovery_timestamp_is_row_epoch_not_exact_probe_completion": True,
        "original_dataset_already_described_outages": True,
    })
    return report


def main() -> None:
    if FIRST_RESULT.exists():
        raise SystemExit("FIRST_U008_ARCHIVE_EXISTS_AND_MUST_NOT_BE_OVERWRITTEN")
    try:
        report = source_audit()
    except (core.InvalidSource, ValueError, TypeError, OSError,
            TimeoutError, UnicodeError) as exc:
        report = {
            "study": core.STUDY,
            "status": "RP_U008_SOURCE_INVALID",
            "source_url": ORIGINAL_URL,
            "source_protocol_only_commit": PROTOCOL_ONLY_COMMIT,
            "failure_type": type(exc).__name__,
            "failure_code": str(exc)[:190],
            "original_external_observation_complete": False,
        }
    FIRST_RESULT.parent.mkdir(parents=True, exist_ok=True)
    FIRST_RESULT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    if report["status"] == "RP_U008_SOURCE_INVALID":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
