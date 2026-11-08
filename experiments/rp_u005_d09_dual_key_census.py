"""RP-U005-D09 — two fixed literal-code cohorts, exact ANEEL 2026 source files.

A source-linkage census; matched *text keys* are not certified real incidents.
The first source run is only after protocol-only commit ae9e00e0....
The same temporary SQLite tables serve cohorts S (<=10) and F (full codes).
No original CNPJ/incident code or individual row is printed or uploaded.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import csv
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile

from experiments import rp_u005_d06_source as d06


PROTOCOL_COMMIT = "ae9e00e0e0ca2fcd5b08da286923f54f02a6e71c"
SOURCE_SHA = dict(d06.ORIGINAL_D04_ZIP_SHA256)
SOURCE_BYTES = dict(d06.ORIGINAL_D04_ZIP_BYTES)
UNCOMPRESSED_SHA = {
    "occ_2026": "736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567",
    "int_2026": "4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce",
}
EXPECTED_ROWS = {"occ_2026": 6789484, "int_2026": 6078331}
EXPECTED_LONG_CODE_ROWS = {"occ_2026": 1929271, "int_2026": 1293508}
KEY_FIELDS = {
    "occ_2026": ("NumCnpjDistribuidora", "NumAnoCompetencia",
                 "NumMesCompetencia", "CodOcorrenciaEmergencial"),
    "int_2026": ("NumCNPJDistribuidora", "AnoCompetencia",
                 "MesCompetencia", "CodOcorrencia"),
}
KEY_SEPARATOR = "\x1f"
MAX_ORIGINAL_CODE_CHARS = 1_048_576
SQLITE_MAX_BYTES = 6 * 1024**3
MAX_BATCH = 20_000
MONTHS = tuple(str(i) for i in range(1, 13))
FAILURES_F = ("invalid_distributor", "invalid_year", "invalid_month", "invalid_full_code")
FAILURES_S = FAILURES_F + ("code_longer_than_10",)


class CensusError(ValueError):
    """Fixed input, source and conservation gate failure."""


def check_key(values: tuple[str, str, str, str]) -> tuple[str | None, bool, tuple[str, ...]]:
    """Never normalize source IDs. Return (full-key, eligible-short, bad reasons)."""
    distributor, year, month, code = values
    reasons: list[str] = []
    if not (isinstance(distributor, str) and len(distributor) == 14
            and distributor.isascii() and distributor.isdecimal()):
        reasons.append("invalid_distributor")
    if year != "2026":
        reasons.append("invalid_year")
    if month not in MONTHS:
        reasons.append("invalid_month")
    if not (isinstance(code, str) and 1 <= len(code) <= MAX_ORIGINAL_CODE_CHARS
            and code.isascii() and code == code.strip()
            and KEY_SEPARATOR not in code):
        reasons.append("invalid_full_code")
    if reasons:
        return None, False, tuple(reasons)
    return KEY_SEPARATOR.join(values), len(code) <= 10, ()


def make_db(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA temp_store=FILE")
    con.execute("PRAGMA cache_size=-32768")
    con.execute("PRAGMA mmap_size=0")
    page_size = con.execute("PRAGMA page_size").fetchone()[0]
    con.execute(f"PRAGMA max_page_count={SQLITE_MAX_BYTES // page_size}")
    for table in ("occ", "intr"):
        con.execute(
            f"CREATE TABLE {table} "
            f"(key TEXT PRIMARY KEY NOT NULL, n INTEGER NOT NULL CHECK(n>=1), "
            f"short INTEGER NOT NULL CHECK(short IN (0,1))) WITHOUT ROWID"
        )
    con.commit()
    return con


def read_source(path: Path, source: d06.Source, con: sqlite3.Connection) -> dict:
    """Parse every original row and prove full uncompressed SHA+ZIP CRC."""
    if source.key not in KEY_FIELDS:
        raise CensusError("UNEXPECTED_SOURCE_KEY")
    table = "occ" if source.key == "occ_2026" else "intr"
    field_names = KEY_FIELDS[source.key]
    rows = valid_f = valid_s = 0
    bad_f = Counter({x: 0 for x in FAILURES_F})
    bad_s = Counter({x: 0 for x in FAILURES_S})
    literal_long_count = 0
    with zipfile.ZipFile(path, "r") as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].is_dir():
            raise CensusError("EXPECTED_ONE_NONEMPTY_CSV_MEMBER")
        member = members[0]
        if (member.filename.startswith("/") or "\\" in member.filename
                or ".." in member.filename.split("/")
                or not member.filename.lower().endswith(".csv")
                or member.flag_bits & 1
                or (member.external_attr >> 16) & 0o170000 == 0o120000
                or not (0 < member.file_size <= d06.MAX_UNCOMPRESSED)):
            raise CensusError("ZIP_MEMBER_UNSAFE_OR_TOO_LARGE")
        statement = (f"INSERT INTO {table}(key,n,short) VALUES(?,1,?) "
                     f"ON CONFLICT(key) DO UPDATE SET n=n+1")
        batch = []
        try:
            with archive.open(member) as opened:
                hashing = d06.DigestReader(opened, d06.MAX_UNCOMPRESSED)
                with io.BufferedReader(hashing, buffer_size=128 * 1024) as buffered:
                    with io.TextIOWrapper(buffered, encoding="utf-8-sig",
                                          errors="strict", newline="") as stream:
                        header_line = stream.readline(1_048_577)
                        if len(header_line) > 1_048_576:
                            raise CensusError("CSV_HEADER_TOO_LARGE")
                        delimiter = d06.choose_delimiter(header_line)
                        headers = next(csv.reader([header_line], delimiter=delimiter, strict=True))
                        if (not set(source.required).issubset(headers)
                                or not set(field_names).issubset(headers)):
                            raise CensusError("CSV_EXPECTED_HEADERS_ABSENT")
                        columns = tuple(headers.index(x) for x in field_names)
                        csv.field_size_limit(1_048_576)
                        for rec in csv.reader(stream, delimiter=delimiter, strict=True):
                            if len(rec) != len(headers):
                                raise CensusError("ORIGINAL_CSV_ROW_WIDTH_INVALID")
                            rows += 1
                            original = tuple(rec[index] for index in columns)
                            code = original[3]
                            over_ten = len(code) > 10
                            if over_ten:
                                literal_long_count += 1
                                bad_s["code_longer_than_10"] += 1
                            key, short, reasons = check_key(original)
                            if reasons:
                                bad_f.update(reasons)
                                bad_s.update(reasons)
                            else:
                                valid_f += 1
                                if short:
                                    valid_s += 1
                                batch.append((key, int(short)))
                                if len(batch) >= MAX_BATCH:
                                    con.executemany(statement, batch)
                                    con.commit()
                                    batch.clear()
                        if batch:
                            con.executemany(statement, batch)
                            con.commit()
                            batch.clear()
        except (zipfile.BadZipFile, UnicodeError, csv.Error, EOFError) as exc:
            raise CensusError("ORIGINAL_ZIP_CRC_OR_CSV_PARSE_FAILED") from exc
        if hashing.total != member.file_size:
            raise CensusError("DECOMPRESSED_BYTE_LENGTH_CHANGED")
        if hashing.digest.hexdigest() != UNCOMPRESSED_SHA[source.key]:
            raise CensusError("DECOMPRESSED_CSV_SHA_CHANGED")
        if rows != EXPECTED_ROWS[source.key]:
            raise CensusError("ORIGINAL_SOURCE_ROWS_CHANGED")
        if literal_long_count != EXPECTED_LONG_CODE_ROWS[source.key]:
            raise CensusError("LONG_CODE_ROWS_DIFFER_FROM_ORIGINAL_D08")
        if not (0 <= valid_s <= valid_f <= rows):
            raise CensusError("INVALID_COHORT_ROW_NESTING")
        if valid_f - valid_s > literal_long_count:
            raise CensusError("LONG_COHORT_ROWS_NOT_CONSERVED")
    return {
        "source_id": source.key,
        "original_csv_data_rows": rows,
        "full_key_eligible_rows": valid_f,
        "full_key_ineligible_rows": rows - valid_f,
        "short_key_eligible_rows": valid_s,
        "short_key_ineligible_rows": rows - valid_s,
        "long_code_rows_in_original": literal_long_count,
        "full_eligible_long_code_rows": valid_f - valid_s,
        "invalid_reason_counts_full_nonexclusive": dict(bad_f),
        "invalid_reason_counts_short_nonexclusive": dict(bad_s),
        "original_decompressed_sha256": hashing.digest.hexdigest(),
        "original_decompressed_bytes": hashing.total,
        "zip_crc_eof_verified": True,
        "identifiers_or_source_rows_emitted": False,
    }


def one_source(con: sqlite3.Connection, table: str, cohort: str) -> dict:
    if table not in ("occ", "intr") or cohort not in ("S", "F"):
        raise CensusError("UNKNOWN_TABLE_OR_COHORT")
    selector = "WHERE short=1" if cohort == "S" else ""
    row = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(n),0), "
        f"COALESCE(SUM(CASE WHEN n=1 THEN 1 ELSE 0 END),0), "
        f"COALESCE(SUM(CASE WHEN n>1 THEN 1 ELSE 0 END),0), "
        f"COALESCE(SUM(CASE WHEN n>1 THEN n ELSE 0 END),0) "
        f"FROM {table} {selector}"
    ).fetchone()
    distinct, eligible, once, repeat, repeat_rows = row
    return {
        "distinct_candidate_keys": distinct,
        "eligible_source_rows_from_groups": eligible,
        "keys_occurring_once": once,
        "repeated_distinct_keys": repeat,
        "source_rows_on_repeated_keys": repeat_rows,
        "surplus_rows_beyond_first": eligible - distinct,
    }


def joined(con: sqlite3.Connection, cohort: str) -> dict:
    if cohort not in ("S", "F"):
        raise CensusError("UNKNOWN_COHORT")
    constraint = " WHERE o.short=1 AND i.short=1" if cohort == "S" else ""
    row = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(o.n),0), COALESCE(SUM(i.n),0), "
        "COALESCE(SUM(CASE WHEN o.n=1 AND i.n=1 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.n=1 AND i.n>1 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.n>1 AND i.n=1 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.n>1 AND i.n>1 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.short=0 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.short=0 THEN o.n ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN i.short=0 THEN i.n ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.short<>i.short THEN 1 ELSE 0 END),0) "
        "FROM occ o INNER JOIN intr i ON o.key=i.key" + constraint
    ).fetchone()
    labels = (
        "matched_distinct_keys", "matched_occurrence_source_rows",
        "matched_interruption_source_rows", "one_to_one_keys",
        "one_to_many_keys", "many_to_one_keys", "many_to_many_keys",
        "matched_long_code_distinct_keys", "matched_long_code_occurrence_rows",
        "matched_long_code_interruption_rows", "same_key_short_flag_disagreements",
    )
    return dict(zip(labels, row))


def cohort_census(con: sqlite3.Connection, source_reports: list[dict], cohort: str) -> dict:
    if len(source_reports) != 2 or {x["source_id"] for x in source_reports} != set(EXPECTED_ROWS):
        raise CensusError("ORIGINAL_SOURCE_REPORT_SET_INVALID")
    rows_by_id = {x["source_id"]: x for x in source_reports}
    sources = {"occ_2026": one_source(con, "occ", cohort),
               "int_2026": one_source(con, "intr", cohort)}
    matched = joined(con, cohort)
    if matched["same_key_short_flag_disagreements"]:
        raise CensusError("EXACT_KEY_SHORT_FLAG_INCONSISTENT")
    categories = ("one_to_one_keys", "one_to_many_keys", "many_to_one_keys",
                  "many_to_many_keys")
    if sum(matched[x] for x in categories) != matched["matched_distinct_keys"]:
        raise CensusError("MATCHED_CARDINALITIES_NOT_CONSERVED")
    for dataset, label in (("occ_2026", "occurrence"), ("int_2026", "interruption")):
        src = sources[dataset]
        key = "short_key_eligible_rows" if cohort == "S" else "full_key_eligible_rows"
        eligible = rows_by_id[dataset][key]
        if (src["eligible_source_rows_from_groups"] != eligible
                or src["keys_occurring_once"] + src["repeated_distinct_keys"]
                != src["distinct_candidate_keys"]
                or src["source_rows_on_repeated_keys"]
                != src["surplus_rows_beyond_first"] + src["repeated_distinct_keys"]
                or src["distinct_candidate_keys"] > eligible):
            raise CensusError("SOURCE_GROUP_COUNTS_NOT_CONSERVED")
        m = matched[f"matched_{label}_source_rows"]
        if (m > eligible or matched["matched_distinct_keys"]
                > src["distinct_candidate_keys"]):
            raise CensusError("MATCHED_ROWS_OUTSIDE_ELIGIBLE_POPULATION")
        src["unmatched_valid_source_rows"] = eligible - m
        src["unmatched_distinct_keys"] = (
            src["distinct_candidate_keys"] - matched["matched_distinct_keys"]
        )
        src["matched_valid_source_rows"] = m
    return {"source_group_counts": sources, "literal_cross_source_key_counts": matched}


def dual_census(con: sqlite3.Connection, reports: list[dict]) -> dict:
    if len(reports) != 2 or {x["source_id"] for x in reports} != set(EXPECTED_ROWS):
        raise CensusError("EXPECTED_TWO_SOURCES")
    for source in reports:
        if (source["original_csv_data_rows"] !=
                source["full_key_eligible_rows"] + source["full_key_ineligible_rows"]
                or source["original_csv_data_rows"] !=
                source["short_key_eligible_rows"] + source["short_key_ineligible_rows"]):
            raise CensusError("ORIGINAL_SOURCE_ROW_IDENTITY_FAILED")
    small = cohort_census(con, reports, "S")
    full = cohort_census(con, reports, "F")
    sm, fm = small["literal_cross_source_key_counts"], full["literal_cross_source_key_counts"]
    if (fm["matched_distinct_keys"] - fm["matched_long_code_distinct_keys"]
            != sm["matched_distinct_keys"]
            or fm["matched_occurrence_source_rows"] - fm["matched_long_code_occurrence_rows"]
            != sm["matched_occurrence_source_rows"]
            or fm["matched_interruption_source_rows"] - fm["matched_long_code_interruption_rows"]
            != sm["matched_interruption_source_rows"]
            or sm["matched_long_code_distinct_keys"] != 0):
        raise CensusError("SHORT_FULL_MATCHED_COHORTS_NOT_CONSERVED")
    for src in ("occ_2026", "int_2026"):
        f = full["source_group_counts"][src]
        s = small["source_group_counts"][src]
        report = next(x for x in reports if x["source_id"] == src)
        if (f["eligible_source_rows_from_groups"] -
                s["eligible_source_rows_from_groups"]
                != report["full_eligible_long_code_rows"]
                or f["distinct_candidate_keys"] < s["distinct_candidate_keys"]
                or f["repeated_distinct_keys"] < s["repeated_distinct_keys"]
                or f["keys_occurring_once"] < s["keys_occurring_once"]):
            raise CensusError("SHORT_FULL_SOURCE_COHORTS_NOT_CONSERVED")
        f["eligible_long_code_distinct_keys"] = (
            f["distinct_candidate_keys"] - s["distinct_candidate_keys"]
        )
        f["eligible_long_code_source_rows"] = report["full_eligible_long_code_rows"]
        f["unmatched_long_code_distinct_keys"] = (
            f["eligible_long_code_distinct_keys"] - fm["matched_long_code_distinct_keys"]
        )
        label = "occurrence" if src == "occ_2026" else "interruption"
        f["unmatched_long_code_source_rows"] = (
            f["eligible_long_code_source_rows"] -
            fm[f"matched_long_code_{label}_rows"]
        )
        if (f["unmatched_long_code_distinct_keys"] < 0
                or f["unmatched_long_code_source_rows"] < 0):
            raise CensusError("LONG_SOURCE_MATCH_COUNTERS_INVALID")
    return {
        "cohort_S_documented_width_at_most_10": small,
        "cohort_F_full_original_code": full,
        "matched_source_rows_are_not_unique_real_incidents": True,
        "event_time_or_feeder_consistency_verified": False,
        "repair_policy_or_causal_effect_tested": False,
    }


def run(out: Path) -> dict:
    result = {
        "study": "RP-U005-D09", "protocol_commit": PROTOCOL_COMMIT,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "INSTRUMENT_FAILURE",
        "identifiable_source_rows_or_keys_uploaded": False,
        "causal_effect_computed": False,
        "semantic_incident_identity_proven": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="rp-u005-d09-") as temporary:
            directory = Path(temporary)
            db = make_db(directory / "candidate-keys.sqlite")
            try:
                reports = []
                for source in d06.SOURCES:
                    metadata = d06.read_metadata(source)
                    path = directory / (source.key + ".zip")
                    try:
                        original = d06.get_original_zip(source, metadata, path)
                        if (original["original_zip_sha256"] != SOURCE_SHA[source.key]
                                or original["original_zip_bytes"] != SOURCE_BYTES[source.key]):
                            raise CensusError("SOURCE_OBJECT_CHANGED")
                        row = read_source(path, source, db)
                        reports.append({
                            **row, "original_zip_sha256": original["original_zip_sha256"],
                            "original_zip_bytes": original["original_zip_bytes"],
                            "source_resource_id": source.resource_id,
                        })
                    finally:
                        path.unlink(missing_ok=True)
                census = dual_census(db, reports)
                result.update(decision="BOTH_SOURCE_DUAL_KEY_CENSUS_AUDITED",
                              original_source_aggregates=reports, census=census)
            finally:
                db.close()
    except CensusError as exc:
        msg = str(exc)
        if msg == "SOURCE_OBJECT_CHANGED":
            verdict = "SOURCE_OBJECT_CHANGED"
        elif (msg.endswith("NOT_CONSERVED") or msg.endswith("INCONSISTENT")
              or msg.endswith("IDENTITY_FAILED") or msg.endswith("COUNTERS_INVALID")):
            verdict = "INSTRUMENT_FAILURE"
        else:
            verdict = "SOURCE_GATE_NOT_PASSED"
        result.update(decision=verdict, error=msg)
    except (d06.SourceAccessError, d06.SourceResourceError, d06.SourceSchemaError) as exc:
        result.update(decision="SOURCE_GATE_NOT_PASSED", error=type(exc).__name__)
    except Exception as exc:
        # No Python exception args or database rows in public diagnostic logs.
        result.update(decision="INSTRUMENT_FAILURE",
                      error="UNEXPECTED_" + type(exc).__name__)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False), flush=True)
    return result


if __name__ == "__main__":
    run(Path("rp-u005-d09-original/audit.json"))
