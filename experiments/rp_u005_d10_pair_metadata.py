"""RP-U005-D10 — temporal intervals and literal feeder/substation consistency.

Registered in protocol-only commit d0a7afed425ac7460a4e2be94a6a723869847381.
This is an observational metadata *consistency* check for D09's UNIQUE
one-to-one source text keys, not certification of actual physical identity.
Original rows/identifiers/dates are never included in public output.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from datetime import timezone
from datetime import datetime as DateTime
from datetime import timezone as TimeZone
import csv
import io
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import zipfile

from experiments import rp_u005_d06_source as d06
from experiments import rp_u005_d09_dual_key_census as d09


PROTOCOL_COMMIT = "d0a7afed425ac7460a4e2be94a6a723869847381"
SOURCE_SHA = dict(d09.SOURCE_SHA)
SOURCE_BYTES = dict(d09.SOURCE_BYTES)
DECODED_SHA = dict(d09.UNCOMPRESSED_SHA)
EXPECTED_ROWS = dict(d09.EXPECTED_ROWS)
EXPECTED_LONG_ROWS = dict(d09.EXPECTED_LONG_CODE_ROWS)
EXPECTED_D09_MATCH = {
    "S": {"all": 2968556, "one_to_one": 2716202,
          "one_to_many": 252093, "many_to_one": 0, "many_to_many": 261},
    "F": {"all": 3609614, "one_to_one": 3307396,
          "one_to_many": 301957, "many_to_one": 0, "many_to_many": 261},
}
EXPECTED_D09_SOURCE_DISTINCT = {
    "S": {"occ_2026": 4859730, "int_2026": 3182671},
    "F": {"occ_2026": 6789001, "int_2026": 4155664},
}
TIMELINE_FIELDS = {
    "occ_2026": ("DthIniOcorrencia", "DthFimOcorrencia",
                 "CodAlimentador", "CodSubestacao"),
    "int_2026": ("DatInicioInterrupcao", "DatFimInterrupcao",
                 "CodAlimentador", "CodSubestacao"),
}
ISO = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})[ T]"
    r"([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,6}))?\Z"
)
BR = re.compile(
    r"([0-9]{2})/([0-9]{2})/([0-9]{4}) "
    r"([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,6}))?\Z"
)
SQLITE_MAX_BYTES = 6 * 1024**3
MAX_BATCH = 20000
COUNTERS = (
    "pairs", "time_overlap", "time_disjoint", "time_unknown",
    "time_touching", "int_starts_before_occ_start",
    "int_ends_after_occ_end", "unknown_occ_missing",
    "unknown_int_missing", "unknown_occ_invalid",
    "unknown_int_invalid", "unknown_occ_reversed",
    "unknown_int_reversed", "feeder_equal", "feeder_different",
    "feeder_unknown", "substation_equal", "substation_different",
    "substation_unknown", "both_codes_equal",
)


class TemporalGateError(ValueError):
    """A declared source, counter or computational gate failed."""


def parse_civil(text: str) -> DateTime | None:
    """Strict civil datetime with no timezone inference or imputed seconds."""
    if not isinstance(text, str):
        return None
    a = ISO.fullmatch(text)
    if a:
        y, month, day, hour, minute, sec, fractional = a.groups()
    else:
        b = BR.fullmatch(text)
        if b is None:
            return None
        day, month, y, hour, minute, sec, fractional = b.groups()
    try:
        us = int(fractional.ljust(6, "0")) if fractional else 0
        return DateTime(int(y), int(month), int(day),
                        int(hour), int(minute), int(sec), us)
    except ValueError:
        return None


def interval(first: str, last: str) -> tuple[tuple[DateTime, DateTime] | None, tuple[str, ...]]:
    """UNKNOWN reasons can be nonexclusive. REVERSED only with two valid dates."""
    problems = []
    if first == "" or last == "":
        problems.append("MISSING")
    x = parse_civil(first) if first != "" else None
    y = parse_civil(last) if last != "" else None
    if (first != "" and x is None) or (last != "" and y is None):
        problems.append("UNSUPPORTED_OR_INVALID")
    if x is not None and y is not None and y < x:
        problems.append("REVERSED")
    if problems:
        return None, tuple(problems)
    if x is None or y is None:
        return None, ("UNSUPPORTED_OR_INVALID",)
    return (x, y), ()


def compare_literal(left: str | None, right: str | None) -> str:
    """Two nonempty *unmodified* strings are equal or different, never normalized."""
    if not left or not right:
        return "unknown"
    return "equal" if left == right else "different"


def pair_observation(occ: tuple[str | None, ...],
                     intr: tuple[str | None, ...]) -> dict[str, int]:
    """Input is only the four source metadata fields, never the key itself."""
    if len(occ) != 4 or len(intr) != 4:
        raise TemporalGateError("EXPECTED_TWO_FOUR_FIELD_METADATA_SETS")
    if any(item is None for item in occ + intr):
        raise TemporalGateError("REPEATED_KEY_METADATA_MUST_NOT_BE_COMPARED")
    a, b, c, d = occ
    x, y, z, w = intr
    row = Counter({name: 0 for name in COUNTERS})
    row["pairs"] = 1
    oi, orr = interval(a, b)
    ii, irr = interval(x, y)
    if oi is None or ii is None:
        row["time_unknown"] = 1
        for tag, why in (("occ", orr), ("int", irr)):
            for reason in why:
                suffix = {"MISSING": "missing", "UNSUPPORTED_OR_INVALID": "invalid",
                          "REVERSED": "reversed"}[reason]
                row[f"unknown_{tag}_{suffix}"] += 1
    else:
        start_o, end_o = oi
        start_i, end_i = ii
        if start_i < start_o:
            row["int_starts_before_occ_start"] = 1
        if end_i > end_o:
            row["int_ends_after_occ_end"] = 1
        if max(start_o, start_i) <= min(end_o, end_i):
            row["time_overlap"] = 1
            if max(start_o, start_i) == min(end_o, end_i):
                row["time_touching"] = 1
        else:
            row["time_disjoint"] = 1
    feeder = compare_literal(c, z)
    substation = compare_literal(d, w)
    row["feeder_" + feeder] = 1
    row["substation_" + substation] = 1
    if feeder == "equal" and substation == "equal":
        row["both_codes_equal"] = 1
    return dict(row)


def make_database(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA temp_store=FILE")
    con.execute("PRAGMA cache_size=-32768")
    con.execute("PRAGMA mmap_size=0")
    pagesize = con.execute("PRAGMA page_size").fetchone()[0]
    con.execute(f"PRAGMA max_page_count={SQLITE_MAX_BYTES // pagesize}")
    for name in ("occ", "intr"):
        con.execute(
            f"CREATE TABLE {name} ("
            "key TEXT PRIMARY KEY NOT NULL, n INTEGER NOT NULL CHECK(n>=1), "
            "short INTEGER NOT NULL CHECK(short IN (0,1)), "
            "begin TEXT, finish TEXT, feeder TEXT, substation TEXT)"
            " WITHOUT ROWID"
        )
    con.commit()
    return con


def source_to_db(path: Path, source: d06.Source, con: sqlite3.Connection) -> dict:
    """Read and authenticate whole source; group per key and erase duplicate metadata."""
    if source.key not in TIMELINE_FIELDS:
        raise TemporalGateError("UNEXPECTED_SOURCE")
    tbl = "occ" if source.key == "occ_2026" else "intr"
    row_number = valid_F = valid_S = long_code = 0
    key_columns = d09.KEY_FIELDS[source.key]
    date_columns = TIMELINE_FIELDS[source.key]
    statement = (
        f"INSERT INTO {tbl}(key,n,short,begin,finish,feeder,substation) "
        "VALUES(?,1,?,?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET n=n+1,"
        "begin=NULL,finish=NULL,feeder=NULL,substation=NULL"
    )
    with zipfile.ZipFile(path, "r") as archive:
        info = archive.infolist()
        if len(info) != 1 or info[0].is_dir():
            raise TemporalGateError("EXPECTED_ONE_CSV_MEMBER")
        member = info[0]
        if (not member.filename.lower().endswith(".csv")
                or member.filename.startswith("/")
                or "\\" in member.filename
                or ".." in member.filename.split("/")
                or member.flag_bits & 1
                or (member.external_attr >> 16) & 0o170000 == 0o120000
                or not (0 < member.file_size <= d06.MAX_UNCOMPRESSED)):
            raise TemporalGateError("SOURCE_ZIP_MEMBER_UNSAFE")
        batch: list[tuple] = []
        try:
            with archive.open(member, "r") as original:
                hashing = d06.DigestReader(original, d06.MAX_UNCOMPRESSED)
                with io.BufferedReader(hashing, buffer_size=128 * 1024) as buf:
                    with io.TextIOWrapper(buf, encoding="utf-8-sig",
                                          errors="strict", newline="") as decoded:
                        header_line = decoded.readline(1_048_577)
                        if len(header_line) > 1_048_576:
                            raise TemporalGateError("CSV_HEADER_TOO_LONG")
                        sep = d06.choose_delimiter(header_line)
                        columns = next(csv.reader([header_line], delimiter=sep, strict=True))
                        if (not set(source.required).issubset(columns)
                                or not set(key_columns).issubset(columns)
                                or not set(date_columns).issubset(columns)):
                            raise TemporalGateError("SOURCE_COLUMNS_MISSING")
                        ki = tuple(columns.index(col) for col in key_columns)
                        mi = tuple(columns.index(col) for col in date_columns)
                        csv.field_size_limit(1_048_576)
                        for rec in csv.reader(decoded, delimiter=sep, strict=True):
                            if len(rec) != len(columns):
                                raise TemporalGateError("ORIGINAL_CSV_ROW_WIDTH_CHANGED")
                            row_number += 1
                            key_data = tuple(rec[i] for i in ki)
                            key, is_short, errors = d09.check_key(key_data)
                            if len(key_data[3]) > 10:
                                long_code += 1
                            if errors:
                                continue
                            valid_F += 1
                            if is_short:
                                valid_S += 1
                            details = tuple(rec[i] for i in mi)
                            batch.append((key, int(is_short), *details))
                            if len(batch) >= MAX_BATCH:
                                con.executemany(statement, batch)
                                con.commit()
                                batch.clear()
                        if batch:
                            con.executemany(statement, batch)
                            con.commit()
                            batch.clear()
        except (zipfile.BadZipFile, UnicodeError, csv.Error, EOFError) as exc:
            raise TemporalGateError("CRC_OR_CSV_DECODE_FAILED") from exc
        if hashing.total != member.file_size:
            raise TemporalGateError("DECODED_MEMBER_LENGTH_CHANGED")
        if hashing.digest.hexdigest() != DECODED_SHA[source.key]:
            raise TemporalGateError("DECODED_SOURCE_HASH_CHANGED")
        if row_number != EXPECTED_ROWS[source.key]:
            raise TemporalGateError("ORIGINAL_ROW_COUNT_CHANGED")
        if long_code != EXPECTED_LONG_ROWS[source.key]:
            raise TemporalGateError("ORIGINAL_LONG_CODE_COUNT_CHANGED")
        if (valid_F != EXPECTED_ROWS[source.key]
                or valid_S != EXPECTED_ROWS[source.key]-long_code):
            raise TemporalGateError("D09_ORIGINAL_ELIGIBILITY_NOT_REPRODUCED")
    return {
        "source_id": source.key,
        "original_rows": row_number, "valid_F_rows": valid_F,
        "valid_S_rows": valid_S, "original_long_code_rows": long_code,
        "decoded_sha256": hashing.digest.hexdigest(),
        "decompressed_bytes": hashing.total, "zip_crc_eof_checked": True,
        "identifiable_source_values_uploaded": False,
    }


def d09_reference_counts(con: sqlite3.Connection, cohort: str) -> dict:
    if cohort not in ("S", "F"):
        raise TemporalGateError("UNEXPECTED_COHORT")
    constraint = " WHERE o.short=1 AND i.short=1" if cohort == "S" else ""
    row = con.execute(
        "SELECT COUNT(*), "
        "COALESCE(SUM(CASE WHEN o.n=1 AND i.n=1 THEN 1 ELSE 0 END),0),"
        "COALESCE(SUM(CASE WHEN o.n=1 AND i.n>1 THEN 1 ELSE 0 END),0),"
        "COALESCE(SUM(CASE WHEN o.n>1 AND i.n=1 THEN 1 ELSE 0 END),0),"
        "COALESCE(SUM(CASE WHEN o.n>1 AND i.n>1 THEN 1 ELSE 0 END),0),"
        "COALESCE(SUM(CASE WHEN o.short<>i.short THEN 1 ELSE 0 END),0)"
        "FROM occ o JOIN intr i ON o.key=i.key" + constraint
    ).fetchone()
    counts = dict(zip(("all", "one_to_one", "one_to_many",
                       "many_to_one", "many_to_many", "short_flag_mismatch"), row))
    if counts.pop("short_flag_mismatch"):
        raise TemporalGateError("SOURCE_KEY_FLAG_INCONSISTENT")
    if counts != EXPECTED_D09_MATCH[cohort]:
        raise TemporalGateError("D09_REFERENCE_MATCH_COUNTS_DIFFER")
    for table, source in (("occ", "occ_2026"), ("intr", "int_2026")):
        c = con.execute(f"SELECT COUNT(*) FROM {table}"
                        + (" WHERE short=1" if cohort == "S" else "")).fetchone()[0]
        if c != EXPECTED_D09_SOURCE_DISTINCT[cohort][source]:
            raise TemporalGateError("D09_REFERENCE_SOURCE_GROUP_COUNTS_DIFFER")
    return counts


def check_pair_accounting(counts: Counter, expected: int) -> dict:
    if counts["pairs"] != expected:
        raise TemporalGateError("ONE_TO_ONE_PAIR_DENOMINATOR_MISMATCH")
    if (counts["time_overlap"]+counts["time_disjoint"]+counts["time_unknown"] != expected
            or counts["feeder_equal"]+counts["feeder_different"]+counts["feeder_unknown"] != expected
            or counts["substation_equal"]+counts["substation_different"]+counts["substation_unknown"] != expected):
        raise TemporalGateError("PAIR_STATUS_PARTITIONS_NOT_CONSERVED")
    if (counts["time_touching"] > counts["time_overlap"]
            or counts["both_codes_equal"] > min(counts["feeder_equal"],counts["substation_equal"])
            or counts["int_starts_before_occ_start"] > expected-counts["time_unknown"]
            or counts["int_ends_after_occ_end"] > expected-counts["time_unknown"]):
        raise TemporalGateError("PAIR_SUBSET_COUNTS_NOT_CONSERVED")
    for reason in ("unknown_occ_missing", "unknown_int_missing",
                   "unknown_occ_invalid", "unknown_int_invalid",
                   "unknown_occ_reversed", "unknown_int_reversed"):
        if counts[reason] > counts["time_unknown"]:
            raise TemporalGateError("UNKNOWN_REASON_COUNT_NOT_SUBSET")
    if any(k not in COUNTERS for k in counts):
        raise TemporalGateError("UNREGISTERED_PAIR_COUNTER")
    return {name: counts.get(name, 0) for name in COUNTERS}


def compare_one_to_one(con: sqlite3.Connection, counts_F: dict,
                       counts_S: dict) -> dict:
    observed = {name: Counter({field:0 for field in COUNTERS})
                for name in ("S", "F", "LONG")}
    query = (
        "SELECT o.short,o.begin,o.finish,o.feeder,o.substation,"
        "i.begin,i.finish,i.feeder,i.substation "
        "FROM occ o JOIN intr i ON o.key=i.key WHERE o.n=1 AND i.n=1"
    )
    for short, ob, oe, ofe, osu, ib, ie, ife, isu in con.execute(query):
        delta = pair_observation((ob,oe,ofe,osu),(ib,ie,ife,isu))
        observed["F"].update(delta)
        observed["S" if short else "LONG"].update(delta)
    expected_F = counts_F["one_to_one"]
    expected_S = counts_S["one_to_one"]
    full = check_pair_accounting(observed["F"],expected_F)
    short = check_pair_accounting(observed["S"],expected_S)
    long = check_pair_accounting(observed["LONG"],expected_F-expected_S)
    if any(full[k] != short[k]+long[k] for k in COUNTERS):
        raise TemporalGateError("SHORT_LONG_PAIR_PARTITION_NOT_CONSERVED")
    return {
        "F_all_full_code_unique_pairs": full,
        "S_dictionary_width_unique_pairs": short,
        "F_only_long_code_unique_pairs": long,
        "temporal_and_metadata_equality_is_not_real_incident_identity": True,
        "histories_of_actual_operator_decisions_audited": False,
    }


def run(output: Path) -> dict:
    report = {
        "study": "RP-U005-D10", "protocol_commit": PROTOCOL_COMMIT,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "INSTRUMENT_FAILURE",
        "original_identifiers_dates_or_event_rows_uploaded": False,
        "physical_incident_identity_proven": False,
        "causal_repair_policy_tested": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="rp-u005-d10-") as tmp:
            directory = Path(tmp)
            con = make_database(directory / "private-keys.sqlite")
            try:
                originals = []
                for source in d06.SOURCES:
                    metadata = d06.read_metadata(source)
                    path = directory / (source.key+".zip")
                    try:
                        zip_report = d06.get_original_zip(source,metadata,path)
                        if (zip_report["original_zip_sha256"] != SOURCE_SHA[source.key]
                                or zip_report["original_zip_bytes"] != SOURCE_BYTES[source.key]):
                            raise TemporalGateError("SOURCE_OBJECT_CHANGED")
                        inspected = source_to_db(path,source,con)
                        originals.append({
                            **inspected, "compressed_sha256":zip_report["original_zip_sha256"],
                            "compressed_bytes":zip_report["original_zip_bytes"]
                        })
                    finally:
                        path.unlink(missing_ok=True)
                if {s["source_id"] for s in originals} != set(EXPECTED_ROWS):
                    raise TemporalGateError("EXPECTED_TWO_SOURCE_REPORTS")
                refs = {kind:d09_reference_counts(con,kind) for kind in ("S","F")}
                observations = compare_one_to_one(con,refs["F"],refs["S"])
                report.update(
                    decision="SOURCE_PAIR_METADATA_CENSUS_COMPLETE",
                    original_source_aggregates=originals,
                    reference_D09_literal_key_counts=refs,
                    one_to_one_pair_metadata=observations,
                    original_csv_row_values_uploaded=False,
                )
            finally:
                con.close()
    except TemporalGateError as exc:
        message = str(exc)
        if message == "SOURCE_OBJECT_CHANGED":
            verdict = "SOURCE_OBJECT_CHANGED"
        elif ("NOT_CONSERVED" in message or message.startswith("D09_REFERENCE")
              or message.endswith("MISMATCH") or message.endswith("INCONSISTENT")
              or message=="EXPECTED_TWO_SOURCE_REPORTS"):
            verdict = "INSTRUMENT_FAILURE"
        else:
            verdict = "SOURCE_GATE_NOT_PASSED"
        report.update(decision=verdict,error=message)
    except (d06.SourceAccessError,d06.SourceSchemaError,d06.SourceResourceError) as exc:
        report.update(decision="SOURCE_GATE_NOT_PASSED",error=type(exc).__name__)
    except Exception as exc:
        report.update(decision="INSTRUMENT_FAILURE",
                      error="UNEXPECTED_"+type(exc).__name__)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2),flush=True)
    return report


if __name__=="__main__":
    run(Path("rp-u005-d10-original/audit.json"))
