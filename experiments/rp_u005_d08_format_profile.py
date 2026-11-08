"""RP-U005-D08: original 2026 ANEEL month/code lexical format profiles.

Post-D07 format investigation. Original individual IDs/CNPJs are neither
collected nor uploaded, and no event matching or policy effects are attempted.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import csv
import io
import json
from pathlib import Path
import tempfile
import zipfile

from experiments import rp_u005_d06_source as d06


PROTOCOL_COMMIT = "7404adde5753b23e8d8a1050b6dccbe2a69cfa71"
SOURCE_SHA = dict(d06.ORIGINAL_D04_ZIP_SHA256)
SOURCE_BYTES = dict(d06.ORIGINAL_D04_ZIP_BYTES)
EXPECTED_DECODED_SHA = {
    "occ_2026": "736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567",
    "int_2026": "4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce",
}
EXPECTED_ROWS = {"occ_2026": 6789484, "int_2026": 6078331}
EXPECTED_D07_CODE_FAILURES = {"occ_2026": 1929271, "int_2026": 1293508}
FIELD_PAIR = {
    "occ_2026": ("NumMesCompetencia", "CodOcorrenciaEmergencial"),
    "int_2026": ("MesCompetencia", "CodOcorrencia"),
}
ALLOWLIST_MONTHS = tuple(str(i) for i in range(1, 13)) + tuple(
    f"{i:02d}" for i in range(1, 10)
)
OTHER_MONTH_BINS = (
    "EMPTY",
    "OTHER_ASCII_ONE_DIGIT",
    "OTHER_ASCII_TWO_DIGITS",
    "OTHER_ASCII_LONG_NUMERIC",
    "OTHER_NONNUMERIC_OR_NONASCII",
)
CODE_REASONS = (
    "EMPTY_CODE", "CODE_LONGER_THAN_TEN",
    "NONASCII_CODE", "SURROUNDING_WHITESPACE", "RESERVED_SEPARATOR",
)


class FormatGateError(ValueError):
    pass


def month_bin(text: str) -> str:
    if text in ALLOWLIST_MONTHS:
        return text
    if text == "":
        return "EMPTY"
    if text.isascii() and text.isdecimal():
        if len(text) == 1:
            return "OTHER_ASCII_ONE_DIGIT"
        if len(text) == 2:
            return "OTHER_ASCII_TWO_DIGITS"
        return "OTHER_ASCII_LONG_NUMERIC"
    return "OTHER_NONNUMERIC_OR_NONASCII"


def code_failure_reasons(text: str) -> tuple[str, ...]:
    reasons = []
    if text == "":
        reasons.append("EMPTY_CODE")
    if len(text) > 10:
        reasons.append("CODE_LONGER_THAN_TEN")
    if not text.isascii():
        reasons.append("NONASCII_CODE")
    if text != text.strip():
        reasons.append("SURROUNDING_WHITESPACE")
    if "\x1f" in text:
        reasons.append("RESERVED_SEPARATOR")
    return tuple(reasons)


def read_original_format(zip_path: Path, source: d06.Source) -> dict:
    month_name, code_name = FIELD_PAIR[source.key]
    counts = Counter({v: 0 for v in (*ALLOWLIST_MONTHS, *OTHER_MONTH_BINS)})
    reasons = Counter({v: 0 for v in CODE_REASONS})
    rows = invalid_code_rows = 0
    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].is_dir():
            raise FormatGateError("SOURCE_ZIP_MEMBER_COUNT_INVALID")
        info = members[0]
        name = info.filename
        if (name.startswith("/") or "\\" in name or ".." in name.split("/")
                or not name.lower().endswith(".csv")
                or info.flag_bits & 1
                or (info.external_attr >> 16) & 0o170000 == 0o120000
                or not (0 < info.file_size <= d06.MAX_UNCOMPRESSED)):
            raise FormatGateError("SOURCE_ZIP_MEMBER_UNSAFE")
        try:
            with archive.open(info) as raw:
                hashing = d06.DigestReader(raw, d06.MAX_UNCOMPRESSED)
                with io.BufferedReader(hashing, buffer_size=128 * 1024) as buffer:
                    with io.TextIOWrapper(
                        buffer, encoding="utf-8-sig", errors="strict", newline=""
                    ) as stream:
                        header = stream.readline(1_048_577)
                        if len(header) > 1_048_576:
                            raise FormatGateError("SOURCE_CSV_HEADER_OVER_BUDGET")
                        sep = d06.choose_delimiter(header)
                        fields = next(csv.reader([header], delimiter=sep, strict=True))
                        if (not set(source.required).issubset(fields)
                                or month_name not in fields or code_name not in fields):
                            raise FormatGateError("SOURCE_CSV_HEADER_FIELDS_MISMATCH")
                        month_index, code_index = fields.index(month_name), fields.index(code_name)
                        csv.field_size_limit(1_048_576)
                        for item in csv.reader(stream, delimiter=sep, strict=True):
                            if len(item) != len(fields):
                                raise FormatGateError("SOURCE_CSV_ROW_LENGTH_MISMATCH")
                            rows += 1
                            counts[month_bin(item[month_index])] += 1
                            bad_reasons = code_failure_reasons(item[code_index])
                            if bad_reasons:
                                invalid_code_rows += 1
                                reasons.update(bad_reasons)
        except (zipfile.BadZipFile, UnicodeError, csv.Error, EOFError) as exc:
            raise FormatGateError("ORIGINAL_ZIP_CRC_OR_CSV_STREAM_FAILED") from exc
        if hashing.total != info.file_size:
            raise FormatGateError("SOURCE_DECOMPRESSED_BYTE_LENGTH_MISMATCH")
        if hashing.digest.hexdigest() != EXPECTED_DECODED_SHA[source.key]:
            raise FormatGateError("SOURCE_DECOMPRESSED_SHA_CHANGED")
        if rows != EXPECTED_ROWS[source.key]:
            raise FormatGateError("SOURCE_ROW_COUNT_CHANGED")
        if sum(counts.values()) != rows:
            raise FormatGateError("MONTH_BIN_CONSERVATION_FAILED")
        if invalid_code_rows != EXPECTED_D07_CODE_FAILURES[source.key]:
            raise FormatGateError("CODE_INVALID_COUNT_DISAGREES_WITH_D07")
        if any(value > invalid_code_rows for value in reasons.values()):
            raise FormatGateError("CODE_REASON_INVARIANT_FAILED")
    return {
        "source_id": source.key,
        "original_csv_rows": rows,
        "original_uncompressed_bytes": hashing.total,
        "original_uncompressed_sha256": hashing.digest.hexdigest(),
        "zip_crc_eof_verified": True,
        "literal_month_spelling_counts": dict(counts),
        "invalid_code_reason_counts_nonexclusive": dict(reasons),
        "invalid_code_rows": invalid_code_rows,
        "code_rows_passing_D07_code_syntax": rows - invalid_code_rows,
        "original_identifiers_published": False,
        "joins_performed": 0,
    }


def run(output: Path) -> dict:
    result = {
        "study": "RP-U005-D08",
        "protocol_commit": PROTOCOL_COMMIT,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "original_identifiable_values_published": False,
        "joins_performed": 0,
        "repair_policy_effect_computed": False,
        "decision": "INSTRUMENT_FAILURE",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="rp-u005-d08-") as base:
            work = Path(base)
            profiles = []
            for source in d06.SOURCES:
                metadata = d06.read_metadata(source)
                zip_path = work / (source.key + ".zip")
                try:
                    downloaded = d06.get_original_zip(source, metadata, zip_path)
                    if (downloaded["original_zip_sha256"] != SOURCE_SHA[source.key]
                            or downloaded["original_zip_bytes"] != SOURCE_BYTES[source.key]):
                        raise FormatGateError("SOURCE_OBJECT_CHANGED")
                    item = read_original_format(zip_path, source)
                    profiles.append({
                        **item,
                        "original_zip_sha256": downloaded["original_zip_sha256"],
                        "original_zip_bytes": downloaded["original_zip_bytes"],
                    })
                finally:
                    zip_path.unlink(missing_ok=True)
            if len(profiles) != 2 or {x["source_id"] for x in profiles} != set(EXPECTED_ROWS):
                raise FormatGateError("TWO_SOURCE_CONSERVATION_FAILED")
            result.update(
                decision="SOURCE_FORMAT_PROFILE_COMPLETE",
                source_profiles=profiles,
                summary_scope="LEXICAL_FIELD_FORMAT_ONLY",
            )
    except FormatGateError as exc:
        message = str(exc)
        if message == "SOURCE_OBJECT_CHANGED":
            verdict = "SOURCE_OBJECT_CHANGED"
        elif message in ("MONTH_BIN_CONSERVATION_FAILED",
                         "CODE_REASON_INVARIANT_FAILED",
                         "CODE_INVALID_COUNT_DISAGREES_WITH_D07",
                         "TWO_SOURCE_CONSERVATION_FAILED"):
            verdict = "INSTRUMENT_FAILURE"
        else:
            verdict = "SOURCE_GATE_NOT_PASSED"
        result.update(decision=verdict, error=message)
    except (d06.SourceSchemaError, d06.SourceResourceError, d06.SourceAccessError) as exc:
        result.update(decision="SOURCE_GATE_NOT_PASSED",
                      error=type(exc).__name__ + ":" + str(exc)[:110])
    except Exception as exc:
        result.update(decision="INSTRUMENT_FAILURE",
                      error="UNEXPECTED_" + type(exc).__name__)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False), flush=True)
    return result


if __name__ == "__main__":
    run(Path("rp-u005-d08-original/audit.json"))
