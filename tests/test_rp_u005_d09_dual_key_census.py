"""Only invented identifiers and synthetic CSV sources; never ANEEL event rows."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from experiments import rp_u005_d09_dual_key_census as m
from experiments import rp_u005_d06_source as d06

A = "00123456000199"  # Explicit synthetic label; no original CNPJ.
B = "00000001000123"  # Explicit synthetic label.
LONG = "LONG_CODE_000001"  # Deliberately >10, not shortened or coerced.


def identity(code, company=A, month="1", year="2026"):
    key, short, reasons = m.check_key((company, year, month, code))
    if reasons:
        raise ValueError("invalid invented fixture")
    return key, short


def put(con, table, codes):
    if table not in ("occ", "intr"):
        raise ValueError("invalid fixture table")
    sql = (f"INSERT INTO {table}(key,n,short) VALUES(?,1,?) "
           "ON CONFLICT(key) DO UPDATE SET n=n+1")
    con.executemany(sql, [identity(k) for k in codes])
    con.commit()


def test_literal_format_and_both_code_width_cohorts():
    short, eligible, errors = m.check_key((A, "2026", "1", "000001"))
    assert not errors and eligible is True
    assert short.endswith("000001")
    long, in_short, errors = m.check_key((A, "2026", "1", LONG))
    assert not errors and in_short is False
    assert long.endswith(LONG)
    assert long != short
    assert m.check_key((A, "2026", "01", "000001"))[0] is None
    assert m.check_key((A, "2026", "2", "000001"))[0] != short
    assert m.check_key((B, "2026", "1", "000001"))[0] != short
    assert m.check_key((A, "2026", "1", "000001"))[0] != m.check_key(
        (A, "2026", "1", "1"))[0]
    assert m.check_key((A, "2026", "1", "MixedCASE"))[0] != m.check_key(
        (A, "2026", "1", "mixedcase"))[0]


@pytest.mark.parametrize("values,reason", [
    ((A[:-1], "2026", "1", "0001"), "invalid_distributor"),
    (("1" * 14, "2025", "1", "0001"), "invalid_year"),
    ((A, "2026", "01", "0001"), "invalid_month"),
    ((A, "2026", "13", "0001"), "invalid_month"),
    ((A, "2026", "1", ""), "invalid_full_code"),
    ((A, "2026", "1", " 001"), "invalid_full_code"),
    ((A, "2026", "1", "001\x1f002"), "invalid_full_code"),
    ((A, "2026", "1", "á"), "invalid_full_code"),
    ((A, "2026", "1", "a" * (m.MAX_ORIGINAL_CODE_CHARS + 1)), "invalid_full_code"),
])
def test_invalid_literals_are_not_normalized(values, reason):
    key, in_short, causes = m.check_key(values)
    assert key is None and in_short is False and reason in causes


def test_nonexclusive_failure_reasons_are_preserved():
    key, eligible, reasons = m.check_key(("wrong", "2025", "01", " x"))
    assert key is None and eligible is False
    assert set(reasons) == {
        "invalid_distributor", "invalid_year",
        "invalid_month", "invalid_full_code"
    }


def test_join_cardinalities_both_cohorts_and_long_partition(tmp_path):
    db = m.make_db(tmp_path / "synthetic.sqlite")
    try:
        # A: 1x1; B: 1x2; C: 2x1; D: 2x2; E: short unmatched;
        # LONG: 2x3 (full only), LONG2: longer unmatched occurrence.
        occ = ["A", "B", "C", "C", "D", "D", "E",
               LONG, LONG, "LONG_CODE_000002"]
        intr = ["A", "B", "B", "C", "D", "D", "Q",
                LONG, LONG, LONG, "LONG_CODE_000003"]
        put(db, "occ", occ)
        put(db, "intr", intr)
        reports = [
            {"source_id": "occ_2026", "original_csv_data_rows": len(occ),
             "full_key_eligible_rows": len(occ), "full_key_ineligible_rows": 0,
             "short_key_eligible_rows": 7, "short_key_ineligible_rows": 3,
             "full_eligible_long_code_rows": 3},
            {"source_id": "int_2026", "original_csv_data_rows": len(intr),
             "full_key_eligible_rows": len(intr), "full_key_ineligible_rows": 0,
             "short_key_eligible_rows": 7, "short_key_ineligible_rows": 4,
             "full_eligible_long_code_rows": 4},
        ]
        outcome = m.dual_census(db, reports)
        short = outcome["cohort_S_documented_width_at_most_10"]
        full = outcome["cohort_F_full_original_code"]
        short_link = short["literal_cross_source_key_counts"]
        full_link = full["literal_cross_source_key_counts"]
        assert short_link["matched_distinct_keys"] == 4
        assert short_link["one_to_one_keys"] == 1
        assert short_link["one_to_many_keys"] == 1
        assert short_link["many_to_one_keys"] == 1
        assert short_link["many_to_many_keys"] == 1
        assert short_link["matched_occurrence_source_rows"] == 6
        assert short_link["matched_interruption_source_rows"] == 6
        assert full_link["matched_distinct_keys"] == 5
        assert full_link["matched_long_code_distinct_keys"] == 1
        assert full_link["matched_long_code_occurrence_rows"] == 2
        assert full_link["matched_long_code_interruption_rows"] == 3
        assert full_link["many_to_many_keys"] == 2
        assert short["source_group_counts"]["occ_2026"]["unmatched_valid_source_rows"] == 1
        assert full["source_group_counts"]["occ_2026"]["unmatched_valid_source_rows"] == 2
        assert full["source_group_counts"]["occ_2026"]["eligible_long_code_distinct_keys"] == 2
        assert full["source_group_counts"]["occ_2026"]["unmatched_long_code_distinct_keys"] == 1
        assert full["source_group_counts"]["int_2026"]["unmatched_long_code_distinct_keys"] == 1
        assert full["source_group_counts"]["occ_2026"]["unmatched_long_code_source_rows"] == 1
        assert full["source_group_counts"]["int_2026"]["unmatched_long_code_source_rows"] == 1
        assert outcome["event_time_or_feeder_consistency_verified"] is False
        assert outcome["repair_policy_or_causal_effect_tested"] is False
    finally:
        db.close()


def test_wrong_source_count_and_corrupted_group_counts_fail_closed(tmp_path):
    db = m.make_db(tmp_path / "bad.sqlite")
    try:
        put(db, "occ", ["A"])
        put(db, "intr", ["A"])
        fake = [
            {"source_id": "occ_2026", "original_csv_data_rows": 2,
             "full_key_eligible_rows": 2, "full_key_ineligible_rows": 0,
             "short_key_eligible_rows": 2, "short_key_ineligible_rows": 0,
             "full_eligible_long_code_rows": 0},
            {"source_id": "int_2026", "original_csv_data_rows": 1,
             "full_key_eligible_rows": 1, "full_key_ineligible_rows": 0,
             "short_key_eligible_rows": 1, "short_key_ineligible_rows": 0,
             "full_eligible_long_code_rows": 0},
        ]
        with pytest.raises(m.CensusError, match="SOURCE_GROUP_COUNTS_NOT_CONSERVED"):
            m.dual_census(db, fake)
        with pytest.raises(m.CensusError, match="EXPECTED_TWO_SOURCES"):
            m.dual_census(db, fake[:1])
    finally:
        db.close()


def fixture_zip(tmp_path, source, values):
    original_headers = list(source.required)
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(original_headers)
    for company, year, month, code in values:
        row = {h: "fiction" for h in original_headers}
        for col, val in zip(m.KEY_FIELDS[source.key], (company,year,month,code)):
            row[col] = val
        writer.writerow([row[h] for h in original_headers])
    csv_data = output.getvalue().encode("utf-8")
    archive = tmp_path / "fiction.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("fiction.csv", csv_data)
    return archive, csv_data


def test_synthetic_complete_crc_and_long_partition_and_nonexclusive_bad_rows(tmp_path, monkeypatch):
    source = d06.SOURCES[0]
    values = [
        (A, "2026", "1", "001"), (A, "2026", "1", "001"),
        (A, "2026", "2", LONG), (A, "2026", "01", "002"),
        ("wrong", "2025", "01", " bad"),
    ]
    archive, data = fixture_zip(tmp_path, source, values)
    monkeypatch.setitem(m.EXPECTED_ROWS, source.key, len(values))
    monkeypatch.setitem(m.EXPECTED_LONG_CODE_ROWS, source.key, 1)
    monkeypatch.setitem(m.UNCOMPRESSED_SHA, source.key, hashlib.sha256(data).hexdigest())
    db = m.make_db(tmp_path / "db.sqlite")
    try:
        actual = m.read_source(archive, source, db)
        assert actual["original_csv_data_rows"] == 5
        assert actual["full_key_eligible_rows"] == 3
        assert actual["short_key_eligible_rows"] == 2
        assert actual["invalid_reason_counts_full_nonexclusive"]["invalid_month"] == 2
        assert actual["invalid_reason_counts_full_nonexclusive"]["invalid_distributor"] == 1
        assert actual["invalid_reason_counts_full_nonexclusive"]["invalid_year"] == 1
        assert actual["invalid_reason_counts_full_nonexclusive"]["invalid_full_code"] == 1
        assert actual["invalid_reason_counts_short_nonexclusive"]["code_longer_than_10"] == 1
        assert actual["zip_crc_eof_verified"] is True
        assert actual["original_decompressed_sha256"] == hashlib.sha256(data).hexdigest()
        assert m.one_source(db, "occ", "F")["eligible_source_rows_from_groups"] == 3
        assert m.one_source(db, "occ", "S")["eligible_source_rows_from_groups"] == 2
    finally:
        db.close()


def test_changed_original_compressed_sha_stops_before_any_key_join(tmp_path, monkeypatch):
    first = d06.SOURCES[0]
    monkeypatch.setattr(d06, "SOURCES", (first,))
    monkeypatch.setattr(d06, "read_metadata", lambda _: {"source_url": first.expected_url})
    monkeypatch.setattr(d06, "get_original_zip", lambda *_: {
        "original_zip_sha256": "0" * 64, "original_zip_bytes": m.SOURCE_BYTES[first.key],
    })
    report = m.run(tmp_path / "report.json")
    assert report["decision"] == "SOURCE_OBJECT_CHANGED"
    assert "census" not in report
    assert "original_source_aggregates" not in report
    assert report["identifiable_source_rows_or_keys_uploaded"] is False


def test_key_validation_stays_active_with_python_optimized_mode():
    sample = (
        "from experiments.rp_u005_d09_dual_key_census import check_key;"
        "key, short, errors=check_key(('bad','2026','01','X'));"
        "print('GUARD_ACTIVE' if key is None and 'invalid_month' in errors "
        "else 'GUARD_FAILED')"
    )
    result = subprocess.run(
        [sys.executable, "-O", "-c", sample], capture_output=True,
        text=True, check=False, timeout=30,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "GUARD_ACTIVE"


def test_no_original_source_values_in_public_aggregate_output(tmp_path, monkeypatch):
    first = d06.SOURCES[0]
    monkeypatch.setattr(d06, "SOURCES", (first,))
    monkeypatch.setattr(d06, "read_metadata", lambda _: {"source_url": first.expected_url})
    monkeypatch.setattr(d06, "get_original_zip", lambda *_: {
        "original_zip_sha256": "0" * 64, "original_zip_bytes": m.SOURCE_BYTES[first.key],
    })
    item = m.run(tmp_path / "report.json")
    text = (tmp_path / "report.json").read_text(encoding="utf-8")
    assert item["decision"] == "SOURCE_OBJECT_CHANGED"
    assert A not in text and B not in text and LONG not in text
