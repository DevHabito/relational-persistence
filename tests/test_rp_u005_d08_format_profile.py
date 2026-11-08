"""D08 synthetic format diagnostics, no original ANEEL events or raw IDs."""
import csv
import hashlib
import io
import json
import subprocess
import sys
import zipfile

import pytest

from experiments import rp_u005_d08_format_profile as a
from experiments import rp_u005_d06_source as d06


def test_month_allowlist_preserves_representation_not_normalized_month():
    assert len(a.ALLOWLIST_MONTHS) == 21
    assert len(set(a.ALLOWLIST_MONTHS)) == 21
    assert a.month_bin("1") == "1"
    assert a.month_bin("01") == "01"
    assert a.month_bin("12") == "12"
    assert a.month_bin("") == "EMPTY"
    assert a.month_bin("00") == "OTHER_ASCII_TWO_DIGITS"
    assert a.month_bin("13") == "OTHER_ASCII_TWO_DIGITS"
    assert a.month_bin("001") == "OTHER_ASCII_LONG_NUMERIC"
    assert a.month_bin("OTHER-SENSITIVE-UNEXPECTED") == "OTHER_NONNUMERIC_OR_NONASCII"


def test_code_bad_reasons_are_nonexclusive_and_no_original_value_is_returned():
    assert a.code_failure_reasons("000123") == ()
    assert a.code_failure_reasons("") == ("EMPTY_CODE",)
    assert a.code_failure_reasons("A" * 11) == ("CODE_LONGER_THAN_TEN",)
    assert set(a.code_failure_reasons(" É" + "x" * 10)) == {
        "CODE_LONGER_THAN_TEN", "NONASCII_CODE", "SURROUNDING_WHITESPACE"
    }
    assert a.code_failure_reasons("001\x1f002") == ("RESERVED_SEPARATOR",)


def fixture(tmp_path, source, examples):
    headers = list(source.required)
    month_name, code_name = a.FIELD_PAIR[source.key]
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(headers)
    for month, code in examples:
        row = {name: "test" for name in headers}
        row[month_name] = month
        row[code_name] = code
        writer.writerow([row[name] for name in headers])
    contents = output.getvalue().encode("utf-8")
    path = tmp_path / "fixture.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("test.csv", contents)
    return path, contents


def test_whole_fixture_csv_crc_month_bins_and_combined_id_failure(tmp_path, monkeypatch):
    source = d06.SOURCES[1]
    examples = [
        ("1", "001"),
        ("01", "0001"),
        ("13", "bad" * 5),
        ("", " 777"),
        ("rare-untrusted-month-string", "nonascii-é"),
    ]
    zip_path, contents = fixture(tmp_path, source, examples)
    monkeypatch.setitem(a.EXPECTED_ROWS, source.key, len(examples))
    monkeypatch.setitem(a.EXPECTED_DECODED_SHA, source.key,
                        hashlib.sha256(contents).hexdigest())
    monkeypatch.setitem(a.EXPECTED_D07_CODE_FAILURES, source.key, 3)
    actual = a.read_original_format(zip_path, source)
    assert actual["original_csv_rows"] == 5
    assert actual["zip_crc_eof_verified"] is True
    assert actual["literal_month_spelling_counts"]["1"] == 1
    assert actual["literal_month_spelling_counts"]["01"] == 1
    assert actual["literal_month_spelling_counts"]["OTHER_ASCII_TWO_DIGITS"] == 1
    assert actual["literal_month_spelling_counts"]["EMPTY"] == 1
    assert actual["literal_month_spelling_counts"]["OTHER_NONNUMERIC_OR_NONASCII"] == 1
    assert "rare-untrusted-month-string" not in str(actual)
    assert "nonascii-é" not in str(actual)
    assert actual["invalid_code_rows"] == 3
    assert actual["code_rows_passing_D07_code_syntax"] == 2
    assert actual["invalid_code_reason_counts_nonexclusive"]["CODE_LONGER_THAN_TEN"] == 1
    assert actual["invalid_code_reason_counts_nonexclusive"]["SURROUNDING_WHITESPACE"] == 1
    assert actual["invalid_code_reason_counts_nonexclusive"]["NONASCII_CODE"] == 1


def test_original_D07_compound_failure_total_is_not_adjusted_post_hoc(tmp_path, monkeypatch):
    source = d06.SOURCES[0]
    examples = [("1", "0001"), ("2", " 002")]
    zip_path, contents = fixture(tmp_path, source, examples)
    monkeypatch.setitem(a.EXPECTED_ROWS, source.key, len(examples))
    monkeypatch.setitem(a.EXPECTED_DECODED_SHA, source.key,
                        hashlib.sha256(contents).hexdigest())
    monkeypatch.setitem(a.EXPECTED_D07_CODE_FAILURES, source.key, 2)
    with pytest.raises(a.FormatGateError, match="DISAGREES_WITH_D07"):
        a.read_original_format(zip_path, source)


def test_unchanged_original_compressed_SHA_is_required_before_source_fields(monkeypatch, tmp_path):
    first = d06.SOURCES[0]
    monkeypatch.setattr(d06, "SOURCES", (first,))
    monkeypatch.setattr(d06, "read_metadata", lambda _: {"source_url": first.expected_url})
    monkeypatch.setattr(d06, "get_original_zip", lambda *_: {
        "original_zip_sha256": "0" * 64, "original_zip_bytes": a.SOURCE_BYTES[first.key],
    })
    document = a.run(tmp_path / "result.json")
    assert document["decision"] == "SOURCE_OBJECT_CHANGED"
    assert "source_profiles" not in document
    assert document["original_identifiable_values_published"] is False


def test_original_raw_values_are_not_exposed_by_month_classifier_under_python_optimized():
    probe = (
        "from experiments.rp_u005_d08_format_profile import month_bin;"
        "print(month_bin('SENSITIVE-UNEXPECTED-VALUE'))"
    )
    outcome = subprocess.run(
        [sys.executable, "-O", "-c", probe],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert outcome.returncode == 0
    assert outcome.stdout.strip() == "OTHER_NONNUMERIC_OR_NONASCII"


def test_dictionary_scope_is_nonidentifying_and_fixed():
    assert set(a.EXPECTED_D07_CODE_FAILURES) == {"occ_2026", "int_2026"}
    assert all(x in a.FIELD_PAIR for x in a.EXPECTED_ROWS)
    assert all(isinstance(x, str) for x in a.ALLOWLIST_MONTHS)
