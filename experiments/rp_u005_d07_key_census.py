"""RP-U005-D07: exact candidate-key census across fixed ANEEL 2026 ZIP sources.

Source-only. No original incident IDs, CNPJs, matched examples, or raw rows
are emitted or persisted outside the runner's disposable temporary directory.
Never infer that a textual key match establishes causal restoration.
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


PROTOCOL_COMMIT = "723681a8aa599eeeb20576c06530fe3f9c947796"
SOURCE_SHA = dict(d06.ORIGINAL_D04_ZIP_SHA256)
SOURCE_BYTES = dict(d06.ORIGINAL_D04_ZIP_BYTES)
UNCOMPRESSED_SHA = {
    "occ_2026": "736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567",
    "int_2026": "4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce",
}
EXPECTED_ROWS = {"occ_2026": 6789484, "int_2026": 6078331}
KEY_FIELDS = {
    "occ_2026": (
        "NumCnpjDistribuidora", "NumAnoCompetencia",
        "NumMesCompetencia", "CodOcorrenciaEmergencial",
    ),
    "int_2026": (
        "NumCNPJDistribuidora", "AnoCompetencia",
        "MesCompetencia", "CodOcorrencia",
    ),
}
KEY_SEPARATOR = "\x1f"
SQLITE_LIMIT_BYTES = 6 * 1024**3
MAX_BATCH = 20_000


class LinkageGateError(ValueError):
    """Source/schema/provenance gate or accounting condition failed."""


def validated_key(row: tuple[str, str, str, str]) -> tuple[str | None, tuple[str, ...]]:
    """The four literal source strings; no normalization of original IDs."""
    company, year, month, incident = row
    failures = []
    if not (len(company) == 14 and company.isascii() and company.isdecimal()):
        failures.append("invalid_distributor")
    if year != "2026":
        failures.append("invalid_competence_year")
    if not (len(month) == 2 and month.isascii() and month.isdecimal()
            and "01" <= month <= "12"):
        failures.append("invalid_competence_month")
    if not (1 <= len(incident) <= 10 and incident.isascii()
            and incident == incident.strip() and KEY_SEPARATOR not in incident):
        failures.append("invalid_occurrence_code")
    if failures:
        return None, tuple(failures)
    key = KEY_SEPARATOR.join(row)
    return key, ()


def create_database(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA temp_store=FILE")
    con.execute("PRAGMA cache_size=-32768")
    con.execute("PRAGMA mmap_size=0")
    # The SQLite page file contains only temporary original *candidate keys*.
    page_size = con.execute("PRAGMA page_size").fetchone()[0]
    con.execute(f"PRAGMA max_page_count={SQLITE_LIMIT_BYTES // page_size}")
    for table in ("occ", "intr"):
        con.execute(
            f"CREATE TABLE {table} (key TEXT PRIMARY KEY NOT NULL, n INTEGER NOT NULL) WITHOUT ROWID"
        )
    con.commit()
    return con


def read_all_keys(zip_path: Path, source: d06.Source, con: sqlite3.Connection) -> dict:
    """Full CRC/EOF and original decompressed digest, with no raw row logging."""
    table = {"occ_2026": "occ", "int_2026": "intr"}[source.key]
    key_fields = KEY_FIELDS[source.key]
    columns = None
    invalid_reasons = Counter({
        "invalid_distributor": 0,
        "invalid_competence_year": 0,
        "invalid_competence_month": 0,
        "invalid_occurrence_code": 0,
    })
    rows = valid_rows = invalid_rows = 0
    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].is_dir():
            raise LinkageGateError("UNEXPECTED_ZIP_MEMBER_COUNT")
        member = members[0]
        name = member.filename
        if (not name.lower().endswith(".csv") or name.startswith("/")
                or ".." in name.split("/") or "\\" in name
                or member.flag_bits & 1
                or (member.external_attr >> 16) & 0o170000 == 0o120000
                or not (0 < member.file_size <= d06.MAX_UNCOMPRESSED)):
            raise LinkageGateError("ZIP_MEMBER_UNSAFE_OR_OVER_BUDGET")
        try:
            with archive.open(member, "r") as raw:
                hashing = d06.DigestReader(raw, d06.MAX_UNCOMPRESSED)
                with io.BufferedReader(hashing, buffer_size=128 * 1024) as buffered:
                    with io.TextIOWrapper(
                        buffered, encoding="utf-8-sig", errors="strict", newline=""
                    ) as stream:
                        header_line = stream.readline(1_048_577)
                        if len(header_line) > 1_048_576:
                            raise LinkageGateError("CSV_HEADER_OVER_BUDGET")
                        delimiter = d06.choose_delimiter(header_line)
                        columns = next(csv.reader(
                            [header_line], delimiter=delimiter, strict=True
                        ))
                        if (not set(source.required).issubset(columns)
                                or not set(key_fields).issubset(columns)):
                            raise LinkageGateError("REQUIRED_HEADER_FIELDS_MISSING")
                        positions = tuple(columns.index(col) for col in key_fields)
                        csv.field_size_limit(1_048_576)
                        reader = csv.reader(stream, delimiter=delimiter, strict=True)
                        buffer = []
                        sql = (
                            f"INSERT INTO {table}(key,n) VALUES(?,1) "
                            f"ON CONFLICT(key) DO UPDATE SET n = n + 1"
                        )
                        for record in reader:
                            if len(record) != len(columns):
                                raise LinkageGateError("CSV_ROW_WIDTH_INVALID")
                            rows += 1
                            key, failures = validated_key(
                                tuple(record[pos] for pos in positions)
                            )
                            if failures:
                                invalid_rows += 1
                                invalid_reasons.update(failures)
                            else:
                                valid_rows += 1
                                buffer.append((key,))
                                if len(buffer) >= MAX_BATCH:
                                    con.executemany(sql, buffer)
                                    con.commit()
                                    buffer.clear()
                        if buffer:
                            con.executemany(sql, buffer)
                            con.commit()
                            buffer.clear()
        except (zipfile.BadZipFile, UnicodeError, csv.Error, EOFError) as exc:
            raise LinkageGateError("ZIP_CRC_OR_CSV_STREAM_FAILED") from exc
        if hashing.total != member.file_size:
            raise LinkageGateError("DECOMPRESSED_MEMBER_BYTE_COUNT_MISMATCH")
        if hashing.digest.hexdigest() != UNCOMPRESSED_SHA[source.key]:
            raise LinkageGateError("DECOMPRESSED_SOURCE_DIGEST_CHANGED")
        if rows != EXPECTED_ROWS[source.key]:
            raise LinkageGateError("ORIGINAL_CSV_ROW_COUNT_CHANGED")
        if rows != valid_rows + invalid_rows:
            raise LinkageGateError("SOURCE_ROW_COUNT_NOT_CONSERVED")
    return {
        "source_id": source.key,
        "original_csv_records": rows,
        "valid_candidate_key_rows": valid_rows,
        "invalid_candidate_key_rows": invalid_rows,
        "invalid_key_reason_counts_nonexclusive": dict(invalid_reasons),
        "decompressed_bytes": hashing.total,
        "decompressed_sha256": hashing.digest.hexdigest(),
        "zip_member_crc_eof_checked": True,
        "original_header_fields_count": len(columns),
        "original_identifiable_values_uploaded": False,
    }


def census_one(con: sqlite3.Connection, table: str) -> dict:
    if table not in ("occ", "intr"):
        raise LinkageGateError("UNEXPECTED_SQLITE_TABLE")
    k, row_total, repeated_keys, repeated_rows = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(n),0), "
        f"COALESCE(SUM(CASE WHEN n>1 THEN 1 ELSE 0 END),0), "
        f"COALESCE(SUM(CASE WHEN n>1 THEN n ELSE 0 END),0) "
        f"FROM {table}"
    ).fetchone()
    return {
        "distinct_valid_candidate_keys": k,
        "valid_candidate_key_rows_from_sqlite": row_total,
        "repeated_candidate_keys": repeated_keys,
        "rows_on_repeated_keys": repeated_rows,
        "unique_occurrence_keys_exactly_once": k - repeated_keys,
        "extra_rows_on_repeated_keys": row_total - k,
    }


def census_matches(con: sqlite3.Connection) -> dict:
    row = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(o.n),0), COALESCE(SUM(i.n),0), "
        "COALESCE(SUM(CASE WHEN o.n=1 AND i.n=1 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.n=1 AND i.n>1 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.n>1 AND i.n=1 THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(CASE WHEN o.n>1 AND i.n>1 THEN 1 ELSE 0 END),0) "
        "FROM occ o INNER JOIN intr i ON o.key=i.key"
    ).fetchone()
    names = (
        "matched_distinct_candidate_keys",
        "occurrence_rows_on_matched_keys",
        "interruption_rows_on_matched_keys",
        "matched_one_to_one_keys",
        "matched_one_to_many_keys",
        "matched_many_to_one_keys",
        "matched_many_to_many_keys",
    )
    return dict(zip(names, row))


def audited_census(con: sqlite3.Connection, sources: list[dict]) -> dict:
    if len(sources) != 2 or {r["source_id"] for r in sources} != {"occ_2026", "int_2026"}:
        raise LinkageGateError("EXPECTED_TWO_COMPLETE_SOURCES")
    by_id = {x["source_id"]: x for x in sources}
    original_census = census_one(con, "occ")
    interruption_census = census_one(con, "intr")
    match = census_matches(con)
    for key, population in (
        ("occ_2026", original_census), ("int_2026", interruption_census)
    ):
        data = by_id[key]
        if (population["valid_candidate_key_rows_from_sqlite"]
                != data["valid_candidate_key_rows"]
                or data["original_csv_records"] !=
                data["valid_candidate_key_rows"] + data["invalid_candidate_key_rows"]
                or population["distinct_valid_candidate_keys"]
                != population["unique_occurrence_keys_exactly_once"] + population["repeated_candidate_keys"]):
            raise LinkageGateError("SOURCE_GROUP_CONSERVATION_FAILED")
    categories = ("matched_one_to_one_keys", "matched_one_to_many_keys",
                  "matched_many_to_one_keys", "matched_many_to_many_keys")
    if sum(match[x] for x in categories) != match["matched_distinct_candidate_keys"]:
        raise LinkageGateError("LINKAGE_CARDINALITIES_NOT_CONSERVED")
    for source_key, grouped, matched_field, label in (
        ("occ_2026", original_census, "occurrence_rows_on_matched_keys", "occurrence"),
        ("int_2026", interruption_census, "interruption_rows_on_matched_keys", "interruption"),
    ):
        joined = match[matched_field]
        valid_rows = by_id[source_key]["valid_candidate_key_rows"]
        keys = grouped["distinct_valid_candidate_keys"]
        matched_keys = match["matched_distinct_candidate_keys"]
        if joined > valid_rows or matched_keys > keys:
            raise LinkageGateError("JOIN_COUNTS_NOT_CONSERVED")
        match[f"unmatched_valid_{label}_rows"] = valid_rows - joined
        match[f"unmatched_distinct_{label}_keys"] = keys - matched_keys
    return {
        "per_source": {"occ_2026": original_census, "int_2026": interruption_census},
        "literal_candidate_key_cross_source": match,
        "semantic_incident_identity_proven": False,
        "event_time_consistency_tested": False,
        "causal_time_availability_tested": False,
        "physical_repair_policy_tested": False,
    }


def run(output: Path) -> dict:
    record = {
        "study": "RP-U005-D07",
        "source_gate_protocol_commit": PROTOCOL_COMMIT,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "original_raw_rows_or_keys_uploaded": False,
        "policy_effect_estimated": False,
        "decision": "INSTRUMENT_FAILURE",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="rp-u005-d07-") as path:
            workdir = Path(path)
            con = create_database(workdir / "source-keys.sqlite")
            try:
                sources = []
                for source in d06.SOURCES:
                    file_path = workdir / f"{source.key}.zip"
                    metadata = d06.read_metadata(source)
                    try:
                        downloaded = d06.get_original_zip(source, metadata, file_path)
                        if (downloaded["original_zip_sha256"] != SOURCE_SHA[source.key]
                                or downloaded["original_zip_bytes"] != SOURCE_BYTES[source.key]):
                            raise LinkageGateError("SOURCE_OBJECT_CHANGED")
                        row = read_all_keys(file_path, source, con)
                        sources.append({
                            **row,
                            "original_compressed_sha256": downloaded["original_zip_sha256"],
                            "original_compressed_bytes": downloaded["original_zip_bytes"],
                            "source_resource_id": source.resource_id,
                        })
                    finally:
                        file_path.unlink(missing_ok=True)
                census = audited_census(con, sources)
                record.update(
                    decision="BOTH_SOURCE_KEY_CENSUS_AUDITED",
                    original_source_files=sources,
                    census=census,
                    original_full_zip_crc_checked=True,
                    historical_event_time_checked=False,
                )
            finally:
                con.close()
    except LinkageGateError as exc:
        record.update(decision=("SOURCE_OBJECT_CHANGED" if str(exc) == "SOURCE_OBJECT_CHANGED"
                                else "SOURCE_GATE_NOT_PASSED"), error=str(exc))
    except (d06.SourceAccessError, d06.SourceResourceError, d06.SourceSchemaError) as exc:
        record.update(decision="SOURCE_GATE_NOT_PASSED", error=type(exc).__name__ + ":" + str(exc)[:120])
    except (sqlite3.Error, OSError, MemoryError, ValueError) as exc:
        record.update(decision="INSTRUMENT_FAILURE", error=type(exc).__name__)
    except Exception as exc:
        record.update(decision="INSTRUMENT_FAILURE", error="UNEXPECTED_" + type(exc).__name__)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False), flush=True)
    return record


if __name__ == "__main__":
    run(Path("rp-u005-d07-original/audit.json"))
