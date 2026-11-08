"""RP-U005-D06 — independently re-registered full ANEEL original ZIP replay.

Frozen scope: docs/protocols/RP-U005-D06-ANEEL-FULL-ZIP-REPLAY.md.
This does not join sources, predict restoration, or compare repair policies.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

HOST = "dadosabertos.aneel.gov.br"
MAX_API = 65_536
MAX_ZIP = 240 * 1024**2
MAX_UNCOMPRESSED = 5 * 1024**3
MAX_TOTAL_UNCOMPRESSED = 10 * 1024**3
PROTOCOL_COMMIT = "05e41f1a85d3baf5173a9198f1938349abbd1adf"
ORIGINAL_D04_ZIP_SHA256 = {
    "occ_2026": "7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c",
    "int_2026": "87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d",
}
ORIGINAL_D04_ZIP_BYTES = {"occ_2026": 176074116, "int_2026": 202900063}


@dataclass(frozen=True)
class Source:
    key: str
    package_id: str
    resource_id: str
    filename: str
    required: tuple[str, ...]

    @property
    def expected_url(self) -> str:
        return (f"https://{HOST}/dataset/{self.package_id}/resource/"
                f"{self.resource_id}/download/{self.filename}")

    @property
    def api_url(self) -> str:
        return f"https://{HOST}/api/3/action/resource_show?id={self.resource_id}"


SOURCES = (
    Source("occ_2026", "ced06b4c-45a5-4cae-8a7e-f576ffc3b412",
           "040c840a-b9fa-4c63-bd3c-f1a99640366b",
           "ocorrencias-emergenciais-rede-distribuicao-2026.zip", (
               "NumCnpjDistribuidora", "CodOcorrenciaEmergencial",
               "NumAnoCompetencia", "NumMesCompetencia", "DthIniOcorrencia",
               "DthFimOcorrencia", "NumTempoPreparacao",
               "NumTempoDeslocamento", "NumTempoExecucao")),
    Source("int_2026", "ccb25653-f07b-4f28-84c2-62a89d1f5a56",
           "33a21bd6-4893-42fc-bc05-888154f7511e",
           "interrupcoes-energia-eletrica-2026.zip", (
               "NumCNPJDistribuidora", "CodOcorrencia", "AnoCompetencia",
               "MesCompetencia", "DatInicioInterrupcao",
               "DatFimInterrupcao", "QtdConsumidoresAfetados")),
)


class SourceAccessError(ValueError):
    pass


class SourceSchemaError(ValueError):
    pass


class SourceResourceError(ValueError):
    pass


class SourceObjectChanged(ValueError):
    pass


def official_url(url: str) -> None:
    part = urllib.parse.urlsplit(url)
    if (part.scheme != "https" or part.hostname != HOST
            or part.port not in (None, 443) or part.username or part.password
            or part.fragment):
        raise SourceAccessError("NONOFFICIAL_URL")


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def opener():
    return urllib.request.build_opener(OfficialRedirect)


def read_metadata(source: Source, opener_obj=None) -> dict:
    official_url(source.api_url)
    op = opener_obj or opener()
    req = urllib.request.Request(source.api_url, headers={
        "Accept": "application/json",
        "User-Agent": "RelationalPersistence-ANEEL-Source-Audit/1.0",
    })
    try:
        with op.open(req, timeout=30) as response:
            official_url(response.geturl())
            if response.status != 200:
                raise SourceAccessError("METADATA_HTTP_NOT_200")
            payload = response.read(MAX_API + 1)
            if len(payload) > MAX_API:
                raise SourceAccessError("METADATA_OVER_BUDGET")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SourceAccessError("METADATA_NETWORK_UNAVAILABLE") from exc
    digest = hashlib.sha256(payload).hexdigest()
    try:
        document = json.loads(payload)
        result = document["result"]
    except (ValueError, TypeError, KeyError) as exc:
        raise SourceAccessError("METADATA_BAD_JSON") from exc
    if document.get("success") is not True or not isinstance(result, dict):
        raise SourceAccessError("METADATA_NOT_SUCCESSFUL")
    if result.get("id") != source.resource_id or result.get("package_id") != source.package_id:
        raise SourceAccessError("METADATA_RESOURCE_IDENTITY_MISMATCH")
    if str(result.get("format", "")).upper() != "ZIP":
        raise SourceAccessError("METADATA_FORMAT_NOT_ZIP")
    actual_url = result.get("url")
    if actual_url != source.expected_url:
        raise SourceAccessError("METADATA_URL_NOT_PREDECLARED")
    official_url(actual_url)
    reported_size = result.get("size")
    if (isinstance(reported_size, bool) or not isinstance(reported_size, int)
            or not (0 < reported_size <= MAX_ZIP)):
        raise SourceAccessError("METADATA_SIZE_OUTSIDE_BUDGET")
    return {
        "metadata_sha256": digest,
        "published_size_bytes": reported_size,
        "publisher_hash_unverified_algorithm": result.get("hash"),
        "publisher_last_modified": result.get("last_modified"),
        "publisher_created": result.get("created"),
        "format": result.get("format"),
        "source_url": actual_url,
    }


def get_original_zip(source: Source, metadata: dict, path: Path,
                     opener_obj=None, sleep=time.sleep) -> dict:
    url = metadata["source_url"]
    if url != source.expected_url:
        raise SourceAccessError("URL_CHANGED_AFTER_METADATA")
    official_url(url)
    op = opener_obj or opener()
    for attempt in range(1, 4):
        if attempt > 1:
            sleep((2, 4)[attempt - 2])
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/zip",
                "User-Agent": "RelationalPersistence-ANEEL-Source-Audit/1.0",
            })
            with op.open(req, timeout=30) as response:
                official_url(response.geturl())
                if response.geturl() != url or response.status != 200:
                    raise SourceAccessError("SOURCE_URL_OR_HTTP_UNEXPECTED")
                advertised = response.headers.get("Content-Length")
                if advertised is not None:
                    try:
                        length = int(advertised)
                    except ValueError as exc:
                        raise SourceAccessError("HTTP_CONTENT_LENGTH_INVALID") from exc
                    if length <= 0 or length > MAX_ZIP:
                        raise SourceAccessError("HTTP_SOURCE_SIZE_OVER_BUDGET")
                else:
                    length = None
                count, digest = 0, hashlib.sha256()
                with path.open("wb") as sink:
                    while True:
                        block = response.read(min(128 * 1024, MAX_ZIP + 1 - count))
                        if not block:
                            break
                        count += len(block)
                        if count > MAX_ZIP:
                            raise SourceAccessError("ZIP_EXCEEDED_FIXED_DOWNLOAD_BUDGET")
                        digest.update(block)
                        sink.write(block)
                if not count or count != metadata["published_size_bytes"]:
                    raise SourceAccessError("DOWNLOADED_LENGTH_DIFFERS_FROM_CKAN")
                if length is not None and count != length:
                    raise SourceAccessError("DOWNLOADED_LENGTH_DIFFERS_FROM_HTTP")
                return {
                    "original_zip_bytes": count,
                    "original_zip_sha256": digest.hexdigest(),
                    "download_attempts": attempt,
                    "http_status": response.status,
                    "final_url": response.geturl(),
                    "http_content_type": response.headers.get("Content-Type"),
                }
        except urllib.error.HTTPError as exc:
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == 3:
                raise SourceAccessError("ZIP_HTTP_REQUEST_FAILED") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == 3:
                raise SourceAccessError("ZIP_NETWORK_UNAVAILABLE_AFTER_FIXED_RETRIES") from exc
    raise SourceAccessError("ZIP_DOWNLOAD_NOT_COMPLETED")


class DigestReader(io.RawIOBase):
    def __init__(self, child, limit: int):
        self.child, self.limit, self.total = child, limit, 0
        self.digest = hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, buffer):
        view = memoryview(buffer)
        chunk = self.child.read(min(len(view), max(1, self.limit + 1 - self.total)))
        if not chunk:
            return 0
        self.total += len(chunk)
        if self.total > self.limit:
            raise SourceResourceError("UNCOMPRESSED_BUDGET_EXCEEDED")
        self.digest.update(chunk)
        view[:len(chunk)] = chunk
        return len(chunk)


def choose_delimiter(header_line: str) -> str:
    """Ignore failure from an irrelevant candidate, not from the selected CSV.

    The *original* D04 error is preserved in its first-run archive. This is
    the one, separately registered D06 parser change after D05 diagnosis.
    """
    candidates = []
    for delimiter in (";", ","):
        try:
            values = next(csv.reader([header_line], delimiter=delimiter, strict=True))
        except (csv.Error, StopIteration):
            continue  # A failed alternative cannot veto a good candidate.
        if all(v and v == v.strip() for v in values) and len(set(values)) == len(values):
            candidates.append((len(values), delimiter))
    best = max((x[0] for x in candidates), default=0)
    winners = [sep for count, sep in candidates if count == best]
    if best <= 1 or len(winners) != 1:
        raise SourceSchemaError("NO_UNAMBIGUOUS_VALID_CSV_HEADER_DELIMITER")
    return winners[0]


def audit_zip_file(path: Path, source: Source) -> dict:
    try:
        with zipfile.ZipFile(path, mode="r", allowZip64=True) as archive:
            members = archive.infolist()
            if len(members) != 1 or members[0].is_dir():
                raise SourceSchemaError("EXPECTED_EXACTLY_ONE_CSV_FILE")
            member = members[0]
            if (member.filename.startswith("/") or "\\" in member.filename
                    or ".." in member.filename.split("/")
                    or not member.filename.lower().endswith(".csv")):
                raise SourceSchemaError("ZIP_MEMBER_PATH_OR_EXTENSION_UNSAFE")
            if member.flag_bits & 1 or (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise SourceSchemaError("ENCRYPTED_OR_SYMLINK_MEMBER")
            if member.file_size <= 0 or member.file_size > MAX_UNCOMPRESSED:
                raise SourceResourceError("ZIP_UNCOMPRESSED_SIZE_OUTSIDE_LIMIT")
            if member.file_size > MAX_TOTAL_UNCOMPRESSED:
                raise SourceResourceError("ZIP_GLOBAL_UNCOMPRESSED_SIZE_OUTSIDE_LIMIT")
            with archive.open(member, "r") as raw:
                hashing = DigestReader(raw, MAX_UNCOMPRESSED)
                with io.BufferedReader(hashing, buffer_size=128 * 1024) as buffered:
                    with io.TextIOWrapper(buffered, encoding="utf-8-sig", errors="strict", newline="") as text:
                        header_line = text.readline(1_048_577)
                        if len(header_line) > 1_048_576:
                            raise SourceSchemaError("HEADER_LINE_OVER_BUDGET")
                        delimiter = choose_delimiter(header_line)
                        headers = next(csv.reader([header_line], delimiter=delimiter, strict=True))
                        missing = sorted(set(source.required) - set(headers))
                        if missing:
                            raise SourceSchemaError("REQUIRED_HEADERS_MISSING:" + ",".join(missing))
                        positions = {name: headers.index(name) for name in source.required}
                        csv.field_size_limit(1_048_576)
                        reader = csv.reader(text, delimiter=delimiter, strict=True)
                        empty = Counter({name: 0 for name in source.required})
                        rows = 0
                        for record in reader:
                            if len(record) != len(headers):
                                raise SourceSchemaError("CSV_ROW_LENGTH_MISMATCH")
                            rows += 1
                            for name, index in positions.items():
                                if record[index] == "":
                                    empty[name] += 1
                        if rows == 0:
                            raise SourceSchemaError("NO_ORIGINAL_DATA_ROWS")
                if hashing.total != member.file_size:
                    raise SourceSchemaError("UNCOMPRESSED_MEMBER_SIZE_DISAGREES")
                return {
                    "zip_member_name": member.filename,
                    "zip_member_crc32": f"{member.CRC:08x}",
                    "zip_crc_eof_checked": True,
                    "decompressed_bytes": hashing.total,
                    "decompressed_sha256": hashing.digest.hexdigest(),
                    "delimiter": delimiter,
                    "original_header_columns": headers,
                    "total_original_csv_records": rows,
                    "empty_required_cells_by_field": dict(empty),
                    "no_event_row_values_archived": True,
                }
    except (zipfile.BadZipFile, UnicodeError, csv.Error, EOFError) as exc:
        raise SourceSchemaError("ZIP_CRC_OR_UTF8_CSV_PARSE_FAILED") from exc


def audit_one(source: Source, workdir: Path, read=read_metadata,
              download=get_original_zip, parse=audit_zip_file) -> dict:
    result = {"source_id": source.key, "resource_id": source.resource_id,
              "publisher": "ANEEL", "source_class": "ORIGINAL_2026_ZIP"}
    try:
        metadata = read(source)
        result.update(metadata)
        zip_path = workdir / (source.key + ".zip")
        result.update(download(source, metadata, zip_path))
        if (result["original_zip_sha256"] != ORIGINAL_D04_ZIP_SHA256[source.key]
                or result["original_zip_bytes"] != ORIGINAL_D04_ZIP_BYTES[source.key]):
            raise SourceObjectChanged("ORIGINAL_ZIP_BYTES_DIFFER_FROM_D04")
        result.update(parse(zip_path, source))
        result["decision"] = "SOURCE_COMPLETE_SCHEMA_AUDITED"
    except SourceObjectChanged as exc:
        result.update(decision="SOURCE_OBJECT_CHANGED", error=str(exc))
    except SourceAccessError as exc:
        result.update(decision="SOURCE_ACCESS_OR_BUDGET_BLOCKED", error=str(exc))
    except (SourceSchemaError, SourceResourceError) as exc:
        result.update(
            decision=("SOURCE_SCHEMA_REJECTED" if isinstance(exc, SourceSchemaError)
                      else "SOURCE_ACCESS_OR_BUDGET_BLOCKED"), error=str(exc))
    except Exception as exc:
        result.update(decision="INSTRUMENT_FAILURE", error="UNEXPECTED_" + type(exc).__name__)
    finally:
        (workdir / (source.key + ".zip")).unlink(missing_ok=True)
    return result


def run(output: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="rp-u005-d04-") as directory:
        results = [audit_one(source, Path(directory)) for source in SOURCES]
    verdict = ("BOTH_SOURCE_SCHEMAS_AUDITED" if all(
        r["decision"] == "SOURCE_COMPLETE_SCHEMA_AUDITED" for r in results)
        else "SOURCE_GATE_NOT_PASSED")
    report = {
        "study": "RP-U005-D06",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_commit": PROTOCOL_COMMIT,
        "decision": verdict,
        "original_zip_sources": results,
        "new_prediction_test": False,
        "original_raw_rows_persisted": False,
        "cross_dataset_joins_performed": 0,
        "observed_policy_effects_computed": False,
        "new_lean_proof": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2), flush=True)
    return report


if __name__ == "__main__":
    run(Path("rp-u005-d06-original/audit.json"))
