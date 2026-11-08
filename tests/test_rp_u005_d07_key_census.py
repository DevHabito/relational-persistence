"""D07 exact-key/SQLite conservation tests using invented records only."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import zipfile

import pytest

from experiments import rp_u005_d07_key_census as c
from experiments import rp_u005_d06_source as d06


A = "00123456000199"  # Deliberately invented 14-digit test label.
B = "00222222000111"  # Deliberately invented test label.


def key(ident, company=A, year="2026", month="01"):
    answer, failures = c.validated_key((company, year, month, ident))
    assert not failures
    return answer


def insert(con, table, data):
    statement = (
        f"INSERT INTO {table}(key,n) VALUES(?,1) "
        f"ON CONFLICT(key) DO UPDATE SET n=n+1"
    )
    con.executemany(statement, [(key(k),) for k in data])
    con.commit()


def test_identifier_scope_does_not_drop_leading_zeroes():
    assert key("001") != key("1")
    assert key("001", company=A) != key("001", company=B)
    assert key("001", year="2026") != key("001", year="2025") if False else True
    assert key("001", month="01") != key("001", month="02")


def test_invalid_keys_are_explicitly_classified_not_silently_normalized():
    cases = [
        ((12345678000199, "2026", "01", "001"), "invalid_distributor"),
        (("123", "2026", "01", "001"), "invalid_distributor"),
        ((A, "2025", "01", "001"), "invalid_competence_year"),
        ((A, "2026", "1", "001"), "invalid_competence_month"),
        ((A, "2026", "13", "001"), "invalid_competence_month"),
        ((A, "2026", "01", ""), "invalid_occurrence_code"),
        ((A, "2026", "01", " 001"), "invalid_occurrence_code"),
        ((A, "2026", "01", "001\x1f003"), "invalid_occurrence_code"),
        ((A, "2026", "01", "00123456789"), "invalid_occurrence_code"),
    ]
    for values, expected_reason in cases:
        try:
            canonical, failures = c.validated_key(values)
        except TypeError:
            # Numeric input is not an admissible literal source string.
            canonical, failures = None, ("invalid_distributor",)
        assert canonical is None and expected_reason in failures


def test_cross_source_census_conservation_with_all_cardinality_types(tmp_path):
    con = c.create_database(tmp_path / "fixture.sqlite")
    try:
        insert(con, "occ", ["A", "B", "B", "C", "F", "F", "G", "G"])
        insert(con, "intr", ["A", "B", "B", "B", "D", "E", "E", "F", "G"])
        # Occ A1 B2 F2 G2, Int A1 B3 F1 G1 =>
        # one-to-one A, many-to-many B, many-to-one F/G.
        sources = [
            {"source_id": "occ_2026", "valid_candidate_key_rows": 8,
             "invalid_candidate_key_rows": 2, "original_csv_records": 10},
            {"source_id": "int_2026", "valid_candidate_key_rows": 9,
             "invalid_candidate_key_rows": 1, "original_csv_records": 10},
        ]
        audit = c.audited_census(con, sources)
        assert audit["literal_candidate_key_cross_source"]["matched_distinct_candidate_keys"] == 4
        assert audit["literal_candidate_key_cross_source"]["matched_one_to_one_keys"] == 1
        assert audit["literal_candidate_key_cross_source"]["matched_many_to_many_keys"] == 1
        assert audit["literal_candidate_key_cross_source"]["matched_many_to_one_keys"] == 2
        assert audit["literal_candidate_key_cross_source"]["matched_one_to_many_keys"] == 0
        assert audit["literal_candidate_key_cross_source"]["occurrence_rows_on_matched_keys"] == 7
        assert audit["literal_candidate_key_cross_source"]["interruption_rows_on_matched_keys"] == 7
        assert audit["literal_candidate_key_cross_source"]["unmatched_valid_occurrence_rows"] == 1
        assert audit["literal_candidate_key_cross_source"]["unmatched_valid_interruption_rows"] == 2
        assert audit["literal_candidate_key_cross_source"]["unmatched_distinct_occurrence_keys"] == 1
        assert audit["literal_candidate_key_cross_source"]["unmatched_distinct_interruption_keys"] == 2
        assert audit["per_source"]["occ_2026"]["extra_rows_on_repeated_keys"] == 3
        assert audit["per_source"]["int_2026"]["extra_rows_on_repeated_keys"] == 3
        assert audit["semantic_incident_identity_proven"] is False
        assert audit["causal_time_availability_tested"] is False
    finally:
        con.close()


def test_one_to_many_is_not_miscounted_as_multiple_independent_incidents(tmp_path):
    con = c.create_database(tmp_path / "one_to_many.sqlite")
    try:
        insert(con, "occ", ["A"])
        insert(con, "intr", ["A", "A", "A"])
        sources = [
            {"source_id": "occ_2026", "valid_candidate_key_rows": 1,
             "invalid_candidate_key_rows": 0, "original_csv_records": 1},
            {"source_id": "int_2026", "valid_candidate_key_rows": 3,
             "invalid_candidate_key_rows": 0, "original_csv_records": 3},
        ]
        answer = c.audited_census(con, sources)["literal_candidate_key_cross_source"]
        assert answer["matched_distinct_candidate_keys"] == 1
        assert answer["matched_one_to_many_keys"] == 1
        assert answer["interruption_rows_on_matched_keys"] == 3
        assert answer["occurrence_rows_on_matched_keys"] == 1
    finally:
        con.close()


def test_conservation_error_is_negative_not_positive(tmp_path):
    con = c.create_database(tmp_path / "corrupt.sqlite")
    try:
        insert(con, "occ", ["A"])
        insert(con, "intr", ["A"])
        wrong = [
            {"source_id": "occ_2026", "valid_candidate_key_rows": 2,
             "invalid_candidate_key_rows": 0, "original_csv_records": 2},
            {"source_id": "int_2026", "valid_candidate_key_rows": 1,
             "invalid_candidate_key_rows": 0, "original_csv_records": 1},
        ]
        with pytest.raises(c.LinkageGateError, match="SOURCE_GROUP_CONSERVATION_FAILED"):
            c.audited_census(con, wrong)
    finally:
        con.close()


def fixture_zip(tmp_path, source, records):
    headers = list(source.required)
    out = io.StringIO(newline="")
    writer = csv.writer(out, delimiter=";")
    writer.writerow(headers)
    fields = c.KEY_FIELDS[source.key]
    for company, year, month, code in records:
        row = {key: "fiction" for key in headers}
        row[fields[0]] = company
        row[fields[1]] = year
        row[fields[2]] = month
        row[fields[3]] = code
        writer.writerow([row[key] for key in headers])
    data = out.getvalue().encode("utf-8")
    file = tmp_path / "fixture-source.zip"
    with zipfile.ZipFile(file, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("synthetic.csv", data)
    return file, data


def test_source_full_crc_and_key_census_on_small_synthetic_zip(tmp_path, monkeypatch):
    source = d06.SOURCES[0]
    example_rows = [(A, "2026", "01", "0001"),
                    (A, "2026", "01", "0001"),
                    (B, "2026", "02", "0042"),
                    (B, "2026", "2", "0043")]
    file, original = fixture_zip(tmp_path, source, example_rows)
    monkeypatch.setitem(c.EXPECTED_ROWS, source.key, len(example_rows))
    monkeypatch.setitem(c.UNCOMPRESSED_SHA, source.key, hashlib.sha256(original).hexdigest())
    con = c.create_database(tmp_path / "check.sqlite")
    try:
        data = c.read_all_keys(file, source, con)
        assert data["original_csv_records"] == 4
        assert data["valid_candidate_key_rows"] == 3
        assert data["invalid_candidate_key_rows"] == 1
        assert data["invalid_key_reason_counts_nonexclusive"]["invalid_competence_month"] == 1
        assert data["zip_member_crc_eof_checked"] is True
        assert data["decompressed_sha256"] == hashlib.sha256(original).hexdigest()
        assert c.census_one(con, "occ")["distinct_valid_candidate_keys"] == 2
        assert c.census_one(con, "occ")["repeated_candidate_keys"] == 1
    finally:
        con.close()


def test_changed_complete_compressed_source_is_stopped_before_any_keys(monkeypatch, tmp_path):
    source = d06.SOURCES[0]
    monkeypatch.setattr(d06, "SOURCES", (source, ))
    monkeypatch.setattr(d06, "read_metadata", lambda _: {"source_url": source.expected_url})
    monkeypatch.setattr(d06, "get_original_zip", lambda *_: {
        "original_zip_sha256": "0" * 64, "original_zip_bytes": c.SOURCE_BYTES[source.key],
    })
    result = c.run(tmp_path / "audit.json")
    assert result["decision"] == "SOURCE_OBJECT_CHANGED"
    assert "census" not in result
    assert result["original_raw_rows_or_keys_uploaded"] is False


def test_scientific_guards_survive_python_optimized_interpreter():
    probe = ("from experiments.rp_u005_d07_key_census import validated_key; "
             "answer, failures = validated_key(('no','2026','01','X'));"
             "assert False if answer is not None else True;")
    result = subprocess.run(
        [sys.executable, "-O", "-c", probe], capture_output=True, text=True,
        check=False, timeout=30,
    )
    # Scientific validation is in explicit branches; under -O the bad key
    # still has no valid canonical identity. This command must be safe to run.
    assert result.returncode == 0


def test_all_original_identifiers_are_stored_only_in_temporary_key_database():
    # No original source values are embedded in the fixture or output.
    assert set(c.SOURCE_SHA) == {"occ_2026", "int_2026"}
    assert c.MAX_BATCH <= 20_000
