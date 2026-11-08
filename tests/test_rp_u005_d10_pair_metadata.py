"""Synthetic-only RP-U005-D10 temporal and feeder consistency tests.

No original ANEEL row, identifier or matched example is included in these fixtures.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import csv
import io
import json
import subprocess
import sys
import zipfile

import pytest

from experiments import rp_u005_d10_pair_metadata as d10
from experiments import rp_u005_d09_dual_key_census as d09
from experiments import rp_u005_d06_source as d06


COMPANY = "00012345000199"  # Invented fixture label, NOT original ANEEL CNPJ.
LONG = "FICTITIOUS_LONG_CODE_001"


@pytest.mark.parametrize("input_text,expected", [
    ("2026-02-03 04:05:06", datetime(2026,2,3,4,5,6)),
    ("2026-02-03T04:05:06", datetime(2026,2,3,4,5,6)),
    ("03/02/2026 04:05:06", datetime(2026,2,3,4,5,6)),
    ("2026-02-03 04:05:06.7", datetime(2026,2,3,4,5,6,700000)),
    ("03/02/2026 04:05:06.123456", datetime(2026,2,3,4,5,6,123456)),
])
def test_registered_datetime_syntax_strictly_parses(input_text,expected):
    assert d10.parse_civil(input_text) == expected


@pytest.mark.parametrize("bad", [
    "", "2026-02-30 04:05:06", "31/04/2026 04:05:06",
    "2026-01-01", "2026-01-01 12:30",
    "2026-01-01 00:00:00+03:00", "2026-01-01T00:00:00Z",
    " 2026-01-01 00:00:00", "2026-01-01 00:00:00 ",
    "2026-01-01 00:00:00.1234567", "2026-01-01 25:00:00",
    "01-01-2026 00:00:00", "2026/01/01 00:00:00",
])
def test_unregistered_or_impossible_datetime_does_not_get_imputed(bad):
    assert d10.parse_civil(bad) is None


def test_invalid_and_missing_timestamps_are_not_mislabeled_as_disjoint():
    assert d10.interval("", "2026-01-01 01:00:00")[1] == ("MISSING",)
    assert d10.interval("nonsense", "2026-01-01 01:00:00")[1] == (
        "UNSUPPORTED_OR_INVALID",)
    assert d10.interval("2026-01-02 01:00:00",
                        "2026-01-01 01:00:00")[1] == ("REVERSED",)
    assert set(d10.interval("", "unsupported")[1]) == {
        "MISSING", "UNSUPPORTED_OR_INVALID"
    }


def test_touching_intervals_are_overlapping_and_not_a_restoration_claim():
    occ = ("2026-01-01 10:00:00", "2026-01-01 11:00:00", "FEED1", "SUB1")
    intr = ("2026-01-01 11:00:00", "2026-01-01 12:00:00", "FEED1", "SUB1")
    row = d10.pair_observation(occ,intr)
    assert row["time_overlap"] == 1 and row["time_disjoint"] == 0
    assert row["time_touching"] == 1
    assert row["both_codes_equal"] == 1
    assert row["int_ends_after_occ_end"] == 1
    assert row["time_unknown"] == 0


def test_disjoint_intervals_and_conflicting_literal_feeders():
    occ = ("01/02/2026 01:00:00", "01/02/2026 02:00:00", "F", "S")
    intr = ("02/02/2026 01:00:00", "02/02/2026 02:00:00", "f", "S2")
    row = d10.pair_observation(occ,intr)
    assert row["time_disjoint"] == 1 and row["time_overlap"] == 0
    assert row["feeder_different"] == 1
    assert row["substation_different"] == 1
    assert row["both_codes_equal"] == 0


def test_original_missing_codes_are_unknown_not_automatic_disagreement():
    occ = ("", "2026-01-01 11:00:00", "", "X")
    intr = ("bad date", "", "B", "")
    row = d10.pair_observation(occ,intr)
    assert row["time_unknown"] == 1
    assert row["unknown_occ_missing"] == 1
    assert row["unknown_int_missing"] == 1
    assert row["unknown_int_invalid"] == 1
    assert row["feeder_unknown"] == 1
    assert row["substation_unknown"] == 1


def test_duplicate_group_metadata_is_erased_and_never_compared(tmp_path):
    con = d10.make_database(tmp_path / "db.sqlite")
    try:
        key = COMPANY+"\x1f2026\x1f1\x1f0001"
        sql = ("INSERT INTO occ(key,n,short,begin,finish,feeder,substation)"
               "VALUES(?,1,1,?,?,?,?) ON CONFLICT(key) DO UPDATE SET n=n+1,"
               "begin=NULL,finish=NULL,feeder=NULL,substation=NULL")
        data=(key,"2026-01-01 01:00:00","2026-01-01 02:00:00","F","S")
        con.execute(sql,data)
        con.execute(sql,data)
        con.commit()
        row=con.execute("SELECT n,begin,finish,feeder,substation FROM occ").fetchone()
        assert row == (2,None,None,None,None)
        with pytest.raises(d10.TemporalGateError,match="REPEATED_KEY_METADATA"):
            d10.pair_observation((row[1],row[2],row[3],row[4]),
                                 ("2026-01-01 01:00:00","2026-01-01 02:00:00","F","S"))
    finally:
        con.close()


def insert(con,table,code,start,end,feeder="F",substation="S"):
    key,short,errors = d09.check_key((COMPANY,"2026","1",code))
    assert not errors
    statement=(f"INSERT INTO {table}(key,n,short,begin,finish,feeder,substation) "
               "VALUES(?,1,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET n=n+1,"
               "begin=NULL,finish=NULL,feeder=NULL,substation=NULL")
    con.execute(statement,(key,int(short),start,end,feeder,substation))


def test_synthetic_parallel_unique_pairs_partition_and_temporal_metadata(tmp_path):
    con=d10.make_database(tmp_path/"test.sqlite")
    try:
        insert(con,"occ","A","2026-01-01 01:00:00","2026-01-01 05:00:00")
        insert(con,"intr","A","2026-01-01 03:00:00","2026-01-01 04:00:00")
        insert(con,"occ",LONG,"2026-01-01 10:00:00","2026-01-01 11:00:00")
        insert(con,"intr",LONG,"2026-01-01 12:00:00","2026-01-01 13:00:00","OTHER","S")
        insert(con,"occ","MULTI","2026-01-01 01:00:00","2026-01-01 02:00:00")
        insert(con,"intr","MULTI","2026-01-01 01:00:00","2026-01-01 02:00:00")
        insert(con,"intr","MULTI","2026-01-01 01:00:00","2026-01-01 02:00:00")
        con.commit()
        result=d10.compare_one_to_one(con,{"one_to_one":2},{"one_to_one":1})
        s=result["S_dictionary_width_unique_pairs"]
        f=result["F_all_full_code_unique_pairs"]
        long=result["F_only_long_code_unique_pairs"]
        assert s["pairs"]==1 and s["time_overlap"]==1 and s["both_codes_equal"]==1
        assert long["pairs"]==1 and long["time_disjoint"]==1
        assert long["feeder_different"]==1 and long["substation_equal"]==1
        assert f["pairs"]==2 and f["time_overlap"]==1 and f["time_disjoint"]==1
        assert f["feeder_equal"]==1 and f["feeder_different"]==1
        assert result["histories_of_actual_operator_decisions_audited"] is False
    finally:
        con.close()


def test_denominator_conservation_failure_is_an_explicit_error():
    row=d10.pair_observation(
        ("2026-01-01 01:00:00","2026-01-01 02:00:00","a","b"),
        ("2026-01-01 01:00:00","2026-01-01 02:00:00","a","b"))
    row["time_disjoint"]=1
    with pytest.raises(d10.TemporalGateError,match="PARTITIONS_NOT_CONSERVED"):
        d10.check_pair_accounting(row,1)


def invented_zip(tmp_path,source,record_values):
    columns=list(dict.fromkeys((*source.required,*d09.KEY_FIELDS[source.key],
                                *d10.TIMELINE_FIELDS[source.key])))
    buf=io.StringIO(newline="")
    writer=csv.writer(buf,delimiter=";")
    writer.writerow(columns)
    for code,start,end,feeder,substation in record_values:
        row={name:"fixture" for name in columns}
        for name,value in zip(d09.KEY_FIELDS[source.key],
                              (COMPANY,"2026","1",code)):
            row[name]=value
        for name,value in zip(d10.TIMELINE_FIELDS[source.key],
                              (start,end,feeder,substation)):
            row[name]=value
        writer.writerow([row[name] for name in columns])
    contents=buf.getvalue().encode("utf-8")
    path=tmp_path/"fixture.zip"
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("invented.csv",contents)
    return path,contents


def test_complete_synthetic_csv_crc_and_duplicate_collapse(tmp_path,monkeypatch):
    source=d06.SOURCES[0]
    original=[
        ("X","2026-01-01 01:00:00","2026-01-01 02:00:00","F","S"),
        ("X","2026-01-01 01:00:00","2026-01-01 03:00:00","F","S"),
        (LONG,"2026-01-02 01:00:00","2026-01-02 02:00:00","","S"),
    ]
    path,data=invented_zip(tmp_path,source,original)
    monkeypatch.setitem(d10.EXPECTED_ROWS,source.key,3)
    monkeypatch.setitem(d10.EXPECTED_LONG_ROWS,source.key,1)
    monkeypatch.setitem(d10.DECODED_SHA,source.key,sha256(data).hexdigest())
    con=d10.make_database(tmp_path/"rows.sqlite")
    try:
        out=d10.source_to_db(path,source,con)
        assert out["original_rows"]==3 and out["valid_F_rows"]==3
        assert out["valid_S_rows"]==2 and out["zip_crc_eof_checked"]
        rec=con.execute("SELECT n,begin FROM occ WHERE n=2").fetchone()
        assert rec==(2,None)
    finally:
        con.close()


def test_source_hash_mismatch_prevents_any_date_read(tmp_path,monkeypatch):
    first=d06.SOURCES[0]
    monkeypatch.setattr(d06,"SOURCES",(first,))
    monkeypatch.setattr(d06,"read_metadata",lambda _ : {"source_url":first.expected_url})
    monkeypatch.setattr(d06,"get_original_zip",lambda *_ : {
        "original_zip_sha256":"0"*64,"original_zip_bytes":d10.SOURCE_BYTES[first.key],
    })
    result=d10.run(tmp_path/"report.json")
    assert result["decision"]=="SOURCE_OBJECT_CHANGED"
    assert "one_to_one_pair_metadata" not in result
    assert result["original_identifiers_dates_or_event_rows_uploaded"] is False


def test_optimized_python_cannot_bypass_invalid_or_unknown_date():
    sample=(
        "from experiments.rp_u005_d10_pair_metadata import parse_civil;"
        "print('ACTIVE' if parse_civil('2026-02-30 00:00:00') is None "
        "else 'BROKEN')"
    )
    run=subprocess.run([sys.executable,"-O","-c",sample],
                       capture_output=True,text=True,check=False,timeout=30)
    assert run.returncode==0 and run.stdout.strip()=="ACTIVE"
