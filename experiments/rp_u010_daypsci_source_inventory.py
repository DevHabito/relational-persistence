"""RP-U010-A01: bounded official DAYPSCI metadata inventory, not a data study.

No raw CSV, PCAP, ZIP, or experimental README is downloaded. A dataset DOI,
landing page and DSpace metadata are queried under a strict domain/byte cap.
Only actual official bitstream-manifest descriptors count as source access.
"""
from __future__ import annotations

from collections import deque
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

DATASET_DOI = "10.71486/2drf-1g53"
DATASET_HANDLE = "10259/11686"
SOURCE_LANDING = "https://hdl.handle.net/10259/11686"
DATASET_API = "https://api.datacite.org/dois/10.71486/2drf-1g53"
DSpace_API = "https://riubu.ubu.es/server/api/core/handles/10259/11686"
RIUBU_LANDING = "https://riubu.ubu.es/handle/10259/11686"
SEEDS = (DATASET_API, SOURCE_LANDING, DSpace_API, RIUBU_LANDING)
ALLOWED_HOSTS = frozenset({
    "api.datacite.org", "hdl.handle.net", "riubu.ubu.es", "doi.org",
})
MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_PROBES = 12
TIMEOUT_SECONDS = 12
MAX_FOLLOWED_REDIRECTS = 3
FIRST_AUDIT = Path("docs/results/RP-U010-A01-first-source/audit.json")
PROTOCOL_ONLY_COMMIT = "25d1041ab086b2c19273b5e32061ed6f130df0cb"
DISCOVERY_STATUS = (
    "RP_U010_A01_OFFICIAL_MANIFEST_AVAILABLE_NOT_YET_DATA_VERIFIED",
    "RP_U010_A01_METADATA_ONLY_SOURCE_FILES_NOT_RESOLVED",
    "RP_U010_A01_SOURCE_ACCESS_BLOCKED",
    "RP_U010_A01_INVALID_DISCOVERY_EVIDENCE",
)


class InvalidDiscovery(ValueError):
    pass


def authorize_url(url: str) -> str:
    if not isinstance(url, str):
        raise InvalidDiscovery("OFFICIAL_METADATA_URL_NOT_STRING")
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS
            or parts.username or parts.password or parts.port is not None
            or len(url) > 1600):
        raise InvalidDiscovery("UNTRUSTED_OR_NON_HTTPS_SOURCE_URL")
    if parts.hostname == "api.datacite.org":
        if parts.path.rstrip("/") != "/dois/" + DATASET_DOI:
            raise InvalidDiscovery("DATACITE_DOI_PATH_SUBSTITUTED")
    if parts.hostname == "hdl.handle.net":
        if parts.path.rstrip("/") != "/" + DATASET_HANDLE:
            raise InvalidDiscovery("OFFICIAL_HANDLE_SUBSTITUTED")
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_metadata(url: str, *, opener=None) -> dict:
    """Never request an original experimental attachment; metadata only."""
    authorize_url(url)
    if looks_like_source_attachment(url):
        raise InvalidDiscovery("A01_CANNOT_FETCH_EXPERIMENTAL_DATA")
    client = opener if opener is not None else build_opener(NoRedirect())
    current = url
    redirect_chain = []
    for _ in range(MAX_FOLLOWED_REDIRECTS + 1):
        request = Request(current, headers={
            "User-Agent": "RelationalPersistence-U010-A01-metadata-audit/1",
            "Accept": "application/json, text/html;q=0.8, */*;q=0.1",
        })
        try:
            response = client.open(request, timeout=TIMEOUT_SECONDS)
        except HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308):
                location = exc.headers.get("Location")
                if not location:
                    raise InvalidDiscovery("REDIRECT_MISSING_LOCATION") from exc
                next_url = authorize_url(urljoin(current, location))
                if looks_like_source_attachment(next_url):
                    raise InvalidDiscovery("A01_REDIRECT_TO_EXPERIMENTAL_ATTACHMENT")
                redirect_chain.append(next_url)
                current = next_url
                continue
            return {
                "requested_url": url, "final_url": current,
                "http_status": int(exc.code), "redirect_chain": redirect_chain,
                "body_bytes": 0, "content_type": exc.headers.get("Content-Type"),
                "sha256": None, "body": b"",
            }
        with response:
            body = response.read(MAX_METADATA_BYTES + 1)
            if len(body) > MAX_METADATA_BYTES:
                raise InvalidDiscovery("METADATA_BODY_EXCEEDS_BOUND")
            status = int(response.getcode())
            final_url = authorize_url(response.geturl())
            if looks_like_source_attachment(final_url):
                raise InvalidDiscovery("A01_RESPONSE_IS_EXPERIMENTAL_ATTACHMENT")
            if status != 200:
                raise InvalidDiscovery("UNEXPECTED_NON_200_METADATA_RESPONSE")
            return {
                "requested_url": url, "final_url": final_url,
                "http_status": status,
                "redirect_chain": redirect_chain,
                "body_bytes": len(body),
                "content_type": response.headers.get("Content-Type"),
                "sha256": sha256(body).hexdigest(), "body": body,
            }
    raise InvalidDiscovery("TOO_MANY_REDIRECTS")


def looks_like_source_attachment(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return path.endswith((".csv", ".pcap", ".pcapng", ".zip", ".7z", ".tar",
                          ".tar.gz", ".gz", ".parquet", ".xlsx", ".md",
                          ".pdf", "/download", "/content"))


class BoundedLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag == "a":
            found = dict(attrs).get("href")
            if isinstance(found, str) and len(self.links) < 150:
                self.links.append(found)


def unpack_metadata(body: bytes, content_type: str | None,
                    *, source_url: str) -> dict:
    """Pure parser. Return identity/provenance and safe metadata links only."""
    if len(body) > MAX_METADATA_BYTES:
        raise InvalidDiscovery("METADATA_BODY_EXCEEDS_BOUND")
    text = body.decode("utf-8-sig", "replace")
    json_like = "json" in (content_type or "").lower() or text.lstrip().startswith("{")
    if json_like:
        try:
            payload = json.loads(text)
        except ValueError as exc:
            raise InvalidDiscovery("MALFORMED_PUBLISHER_JSON") from exc
        if not isinstance(payload, dict):
            raise InvalidDiscovery("PUBLISHER_METADATA_NOT_OBJECT")
        return parse_json_metadata(payload, source_url=source_url)
    parser = BoundedLinks()
    parser.feed(text)
    links = []
    for link in parser.links:
        candidate = urljoin(source_url, link)
        try:
            authorize_url(candidate)
        except InvalidDiscovery:
            continue
        if not looks_like_source_attachment(candidate) and (
            "/server/api/core/" in candidate or "/handle/10259/11686" in candidate
        ):
            links.append(candidate)
    is_daypsci = "DAYPSCI" in text.upper()
    return {
        "identity_verified": is_daypsci or DATASET_HANDLE in text,
        "kind": "html_landing", "metadata_links": sorted(set(links))[:24],
        "claimed_source_files": [], "title_mentions_daypsci": is_daypsci,
    }


def official_link(candidate: object, base: str) -> str | None:
    if not isinstance(candidate, str):
        return None
    next_url = urljoin(base, candidate)
    try:
        authorize_url(next_url)
    except InvalidDiscovery:
        return None
    return next_url


def parse_json_metadata(payload: dict, *, source_url: str) -> dict:
    # DataCite DOI metadata is authoritative for DOI/title, NOT for file list.
    if source_url.startswith(DATASET_API):
        obj = payload.get("data")
        if not isinstance(obj, dict):
            raise InvalidDiscovery("DATACITE_MISSING_RECORD")
        attrs = obj.get("attributes") or {}
        doi = str(attrs.get("doi", "")).lower()
        if doi != DATASET_DOI:
            raise InvalidDiscovery("DATACITE_DOI_IDENTITY_MISMATCH")
        titles = attrs.get("titles") or []
        label = " ".join(x.get("title", "") for x in titles
                         if isinstance(x, dict))
        if "DAYPSCI" not in label.upper():
            raise InvalidDiscovery("DATACITE_DATASET_TITLE_MISMATCH")
        url = official_link(attrs.get("url"), source_url)
        return {
            "identity_verified": True, "kind": "datacite_doi",
            "doi": doi, "title": label[:180],
            "metadata_links": [url] if url and not looks_like_source_attachment(url) else [],
            "claimed_source_files": [],
        }

    # DSpace HAL embedded links are untrusted until domain-checked.
    links = payload.get("_links") or {}
    if not isinstance(links, dict):
        links = {}
    queued = []
    for name in ("item", "bundles", "bitstreams"):
        detail = links.get(name)
        if isinstance(detail, dict):
            candidate = official_link(detail.get("href"), source_url)
            if candidate and not looks_like_source_attachment(candidate):
                queued.append(candidate)

    embedded = payload.get("_embedded") or {}
    if not isinstance(embedded, dict):
        embedded = {}
    files = []
    bitstreams = embedded.get("bitstreams")
    if isinstance(bitstreams, list):
        for data in bitstreams[:50]:
            if not isinstance(data, dict):
                continue
            name = data.get("name")
            size = data.get("sizeBytes")
            link = ((data.get("_links") or {}).get("content") or {}).get("href")
            uri = official_link(link, source_url)
            if (isinstance(name, str) and len(name) <= 300 and
                    type(size) is int and size >= 0 and uri and
                    looks_like_source_attachment(uri)):
                check = data.get("checkSum") or {}
                files.append({
                    "name": name, "size_bytes": size,
                    "content_url": uri,
                    "publisher_checksum_algorithm": check.get("checkSumAlgorithm")
                    if isinstance(check, dict) else None,
                    "publisher_checksum_value": check.get("value")
                    if isinstance(check, dict) else None,
                })
    bundles = embedded.get("bundles")
    if isinstance(bundles, list):
        for entry in bundles[:40]:
            if not isinstance(entry, dict):
                continue
            path = ((entry.get("_links") or {}).get("bitstreams") or {}).get("href")
            uri = official_link(path, source_url)
            if uri and not looks_like_source_attachment(uri):
                queued.append(uri)
    # A DSpace "handle -> item" resolver can return a list of link objects.
    return {
        "identity_verified": bool(DATASET_HANDLE in source_url
                                  or "DAYPSCI" in str(payload.get("name", "")).upper()
                                  or "DAYPSCI" in str(payload.get("handle", "")).upper()),
        "kind": "official_repository_json",
        "metadata_links": sorted(set(queued))[:40],
        "claimed_source_files": files,
        "record_id": str(payload.get("id", ""))[:120],
    }


def status_from_discovery(attempts: list[dict], files: list[dict]) -> str:
    if files:
        return DISCOVERY_STATUS[0]
    if any(a.get("http_status") == 200 and a.get("identity_verified")
           for a in attempts):
        return DISCOVERY_STATUS[1]
    if any(a.get("integrity_violation") for a in attempts):
        return DISCOVERY_STATUS[3]
    return DISCOVERY_STATUS[2]


def live_manifest_inventory() -> dict:
    seen: set[str] = set()
    pending = deque(SEEDS)
    attempts = []
    collected = []
    while pending and len(attempts) < MAX_PROBES:
        url = pending.popleft()
        if url in seen:
            continue
        seen.add(url)
        evidence = {"requested_url": url}
        try:
            reply = request_metadata(url)
            evidence.update({
                key: reply[key] for key in (
                    "http_status", "final_url", "redirect_chain", "body_bytes",
                    "content_type", "sha256")
            })
            if reply["http_status"] == 200:
                parsed = unpack_metadata(
                    reply["body"], reply["content_type"], source_url=reply["final_url"]
                )
                evidence.update({
                    "kind": parsed["kind"],
                    "identity_verified": parsed["identity_verified"],
                    "metadata_link_count": len(parsed["metadata_links"]),
                    "file_descriptor_count": len(parsed["claimed_source_files"]),
                })
                if parsed["identity_verified"] or url in SEEDS:
                    for candidate in parsed["metadata_links"]:
                        if candidate not in seen and candidate not in pending:
                            pending.append(candidate)
                    if parsed["kind"] == "official_repository_json":
                        # No attachment fetched; this is source file metadata only.
                        collected.extend(parsed["claimed_source_files"])
        except (InvalidDiscovery, HTTPError, URLError, TimeoutError, OSError,
                UnicodeError, ValueError) as exc:
            evidence.update({
                "error_type": type(exc).__name__,
                "error_code": str(exc)[:160],
                "integrity_violation": (
                    isinstance(exc, InvalidDiscovery)
                    and "MISMATCH" in str(exc)
                ),
            })
        attempts.append(evidence)
    distinct_files = list({
        (x["name"], x["content_url"]): x for x in collected
    }.values())
    status = status_from_discovery(attempts, distinct_files)
    return {
        "study": "RP-U010-A01",
        "status": status,
        "protocol_only_commit": PROTOCOL_ONLY_COMMIT,
        "official_dataset_doi": DATASET_DOI,
        "official_dataset_handle": DATASET_HANDLE,
        "publisher_metadata_attempts": attempts,
        "file_descriptors_from_official_repository_json": distinct_files,
        "file_descriptor_count": len(distinct_files),
        "metadata_requests_made": len(attempts),
        "first_source_original_csv_or_pcapng_downloaded": False,
        "actual_fault_deactivation_verified": False,
        "independent_functional_recovery_endpoint_verified": False,
        "plc_pcap_clock_alignment_verified": False,
        "all_outcome_and_population_inference_prohibited": True,
        "no_new_formal_theorem_or_physical_law": True,
    }


def main() -> None:
    if FIRST_AUDIT.exists():
        raise SystemExit("FIRST_SOURCE_A01_ALREADY_ARCHIVED")
    if not os.environ.get("GITHUB_SHA") or not os.environ.get("GITHUB_RUN_ID"):
        raise SystemExit("HOSTED_FIRST_SOURCE_GIT_IDENTITIES_REQUIRED")
    result = live_manifest_inventory()
    result["first_source_runner_commit"] = os.environ["GITHUB_SHA"]
    result["first_source_workflow_id"] = os.environ["GITHUB_RUN_ID"]
    FIRST_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    FIRST_AUDIT.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"],
        "metadata_requests": result["metadata_requests_made"],
        "file_descriptors": result["file_descriptor_count"],
        "attempts": result["publisher_metadata_attempts"],
        "original_data_downloaded": False,
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
