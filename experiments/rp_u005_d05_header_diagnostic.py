"""RP-U005-D05 — read-only 64 KiB original ANEEL ZIP prefix header check.

Explicitly post-D04; a prefix is not an authenticated full source ZIP.
Protocol: docs/protocols/RP-U005-D05-ANEEL-HEADER-DIAGNOSTIC.md.
"""
from __future__ import annotations
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import urllib.error
import urllib.parse
import urllib.request
import zlib

HOST = "dadosabertos.aneel.gov.br"
RANGE_BYTES = 65_536
MAX_HEADER_OUTPUT = 1_048_576
PROTOCOL = "dacefbf39be9987bc9b9c5b37ce5cb45015b8307"

SOURCES = (
    {
        "id": "occ_2026",
        "url": "https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/040c840a-b9fa-4c63-bd3c-f1a99640366b/download/ocorrencias-emergenciais-rede-distribuicao-2026.zip",
        "expected_total": 176074116,
        "required": ("NumCnpjDistribuidora", "CodOcorrenciaEmergencial",
                     "NumAnoCompetencia", "NumMesCompetencia",
                     "DthIniOcorrencia", "DthFimOcorrencia"),
    },
    {
        "id": "int_2026",
        "url": "https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/33a21bd6-4893-42fc-bc05-888154f7511e/download/interrupcoes-energia-eletrica-2026.zip",
        "expected_total": 202900063,
        "required": ("NumCNPJDistribuidora", "CodOcorrencia",
                     "AnoCompetencia", "MesCompetencia",
                     "DatInicioInterrupcao", "DatFimInterrupcao"),
    },
)


class PrefixAuditError(ValueError):
    pass


def official_url(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != HOST
            or parsed.port not in (None, 443) or parsed.username or parsed.password
            or parsed.fragment):
        raise PrefixAuditError("NONOFFICIAL_URL")


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def original_prefix(source, opener_obj=None):
    official_url(source["url"])
    op = opener_obj or urllib.request.build_opener(SameHostRedirect)
    request = urllib.request.Request(
        source["url"],
        headers={"Range": "bytes=0-65535",
                 "Accept": "application/zip",
                 "User-Agent": "RelationalPersistence-ANEEL-Header-Diagnostic/1.0"},
    )
    try:
        with op.open(request, timeout=30) as response:
            final_url = response.geturl()
            official_url(final_url)
            if final_url != source["url"]:
                raise PrefixAuditError("UNEXPECTED_ORIGINAL_SOURCE_REDIRECT")
            if response.status != 206:
                raise PrefixAuditError("HTTP_RANGE_NOT_HONORED")
            content_range = response.headers.get("Content-Range", "")
            expected_range = f"bytes 0-65535/{source['expected_total']}"
            if content_range != expected_range:
                raise PrefixAuditError("ORIGINAL_RANGE_OR_LENGTH_NOT_VERIFIED")
            data = response.read(RANGE_BYTES + 1)
            if len(data) != RANGE_BYTES:
                raise PrefixAuditError("ORIGINAL_PREFIX_LENGTH_MISMATCH")
            return data, {
                "http_status": 206,
                "content_range": content_range,
                "complete_source_sha256_reverified": False,
                "prefix_bytes": len(data),
                "original_prefix_sha256": hashlib.sha256(data).hexdigest(),
                "final_url": final_url,
            }
    except (urllib.error.URLError, TimeoutError) as exc:
        raise PrefixAuditError("ORIGINAL_RANGE_NETWORK_UNAVAILABLE") from exc


def zip_first_header(prefix: bytes) -> dict:
    if len(prefix) < 30 or prefix[:4] != b"PK\x03\x04":
        raise PrefixAuditError("MISSING_OR_BAD_ZIP_LOCAL_HEADER")
    (_, version, flags, method, date_time, date, crc, compressed,
     uncompressed, name_size, extra_size) = struct.unpack_from("<IHHHHHIIIHH", prefix, 0)
    if flags & 1 or method not in (0, 8):
        raise PrefixAuditError("UNSUPPORTED_ZIP_ENTRY_FLAGS_OR_METHOD")
    start = 30 + name_size + extra_size
    if start >= len(prefix) or name_size <= 0:
        raise PrefixAuditError("TRUNCATED_ZIP_LOCAL_ENTRY")
    try:
        name = prefix[30:30 + name_size].decode("utf-8")
    except UnicodeError as exc:
        raise PrefixAuditError("ZIP_MEMBER_NAME_NOT_UTF8") from exc
    if (name.startswith("/") or "\\" in name or ".." in name.split("/")
            or not name.lower().endswith(".csv")):
        raise PrefixAuditError("UNSAFE_OR_NONCSV_FIRST_MEMBER")
    compressed_prefix = prefix[start:]
    try:
        if method == 8:
            text_prefix = zlib.decompressobj(-15).decompress(
                compressed_prefix, MAX_HEADER_OUTPUT + 1)
        else:
            text_prefix = compressed_prefix[:MAX_HEADER_OUTPUT + 1]
    except zlib.error as exc:
        raise PrefixAuditError("FIRST_ZIP_MEMBER_DEFLATE_FAILED") from exc
    if len(text_prefix) > MAX_HEADER_OUTPUT:
        raise PrefixAuditError("DECOMPRESSED_HEADER_BUDGET_EXCEEDED")
    cut = text_prefix.find(b"\n")
    if cut == -1:
        raise PrefixAuditError("FIRST_CSV_HEADER_NOT_COMPLETE_WITHIN_PREFIX")
    literal = text_prefix[:cut + 1]
    try:
        header = literal.decode("utf-8-sig")
    except UnicodeError as exc:
        raise PrefixAuditError("FIRST_CSV_HEADER_UTF8_INVALID") from exc
    return {
        "first_zip_member_name": name,
        "first_zip_member_method": method,
        "literal_first_header_sha256": hashlib.sha256(literal).hexdigest(),
        "header_text": header,
        "decompressed_prefix_is_not_full_member": True,
    }


def delimiter_observations(header, expected_fields):
    outcomes = {}
    required = set(expected_fields)
    for delimiter, label in ((";", "semicolon"), (",", "comma")):
        try:
            fields = next(csv.reader([header], delimiter=delimiter, strict=True))
            valid = (bool(fields) and len(fields) == len(set(fields))
                     and all(field != "" and field == field.strip() for field in fields))
            outcomes[label] = {
                "parser_accepted": True, "header_names": fields,
                "unique_nonempty": valid,
                "required_field_names_present": required.issubset(fields),
            }
        except (csv.Error, StopIteration) as exc:
            outcomes[label] = {
                "parser_accepted": False,
                "parser_error_class": type(exc).__name__,
                "parser_error": str(exc)[:180],
                "required_field_names_present": False,
            }
    semicolon = outcomes["semicolon"]
    comma = outcomes["comma"]
    diagnosed = bool(semicolon["parser_accepted"] and
                     semicolon["required_field_names_present"] and
                     semicolon["unique_nonempty"] and
                     not comma["parser_accepted"])
    return outcomes, diagnosed


def audit_source(source, acquire=original_prefix):
    result = {"source_id": source["id"], "original_url": source["url"],
              "first_D04_complete_zip_SHA256_not_reverified": True}
    try:
        data, transport = acquire(source)
        result.update(transport)
        first = zip_first_header(data)
        outcomes, diagnosed = delimiter_observations(first.pop("header_text"),
                                                     source["required"])
        result.update(first)
        result["candidate_delimiters"] = outcomes
        result["decision"] = (
            "PREFIX_DIAGNOSTIC_CONFIRMS_DELIMITER_DEFECT" if diagnosed
            else "PREFIX_DIAGNOSTIC_INCONCLUSIVE")
    except PrefixAuditError as exc:
        result.update(decision="PREFIX_DIAGNOSTIC_BLOCKED", error=str(exc))
    except Exception as exc:
        result.update(decision="PREFIX_DIAGNOSTIC_BLOCKED",
                      error="INSTRUMENT_FAILURE_" + type(exc).__name__)
    return result


def run(out: Path):
    results = [audit_source(source) for source in SOURCES]
    document = {
        "study": "RP-U005-D05", "protocol_commit": PROTOCOL,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "source_results": results,
        "all_prefixes_confirm_delimiter_defect": all(
            row["decision"] == "PREFIX_DIAGNOSTIC_CONFIRMS_DELIMITER_DEFECT"
            for row in results),
        "full_original_source_files_downloaded": False,
        "original_event_rows_parsed": 0, "full_zip_crc_verified": False,
        "policy_effect_computed": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, sort_keys=True, ensure_ascii=False, indent=2)
                   + "\n", encoding="utf-8")
    print(json.dumps(document, sort_keys=True, ensure_ascii=False, indent=2), flush=True)
    return document


if __name__ == "__main__":
    run(Path("rp-u005-d05-original/audit.json"))
