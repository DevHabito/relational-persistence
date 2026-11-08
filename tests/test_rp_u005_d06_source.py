"""Synthetic-only negative controls for RP-U005-D04. No ANEEL rows."""
import csv
import io
import json
import zipfile
import pytest
from experiments.rp_u005_d06_source import (
    SOURCES, SourceAccessError, SourceSchemaError, SourceResourceError,
    choose_delimiter, audit_zip_file, official_url, read_metadata, audit_one,
)


def csv_fixture(source, delimiter=";", rows=2, missing=None, short=False):
    names = list(source.required)
    if missing:
        names.remove(missing)
    out = io.StringIO(newline="")
    writer = csv.writer(out, delimiter=delimiter)
    writer.writerow(names)
    for i in range(rows):
        record = [f"fiction{i}" for _ in names]
        if short and i == 0:
            record.pop()
        writer.writerow(record)
    return out.getvalue().encode("utf-8")


def zip_fixture(tmp_path, content, name="record.csv"):
    path = tmp_path / "original.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, content)
    return path


@pytest.mark.parametrize("delimiter", [";", ","])
def test_complete_utf8_stream_with_crc_and_original_counts(tmp_path, delimiter):
    original = csv_fixture(SOURCES[0], delimiter)
    path = zip_fixture(tmp_path, original)
    result = audit_zip_file(path, SOURCES[0])
    assert result["delimiter"] == delimiter
    assert result["total_original_csv_records"] == 2
    assert result["decompressed_bytes"] == len(original)
    assert result["zip_crc_eof_checked"] is True
    assert all(n == 0 for n in result["empty_required_cells_by_field"].values())
    assert "fiction0" not in str(result)


def test_quoted_delimiter_and_null_cell_are_not_dropped(tmp_path):
    source = SOURCES[1]
    raw = (";".join(source.required) + "\n" +
           '"fiction;quoted";' + ";".join([""] + ["ok"] * (len(source.required) - 2)) +
           "\n").encode("utf-8")
    row = audit_zip_file(zip_fixture(tmp_path, raw), source)
    assert row["total_original_csv_records"] == 1
    assert row["empty_required_cells_by_field"][source.required[1]] == 1


def test_missing_required_column_is_an_explicit_failure(tmp_path):
    path = zip_fixture(tmp_path, csv_fixture(SOURCES[0], missing=SOURCES[0].required[0]))
    with pytest.raises(SourceSchemaError, match="REQUIRED_HEADERS_MISSING"):
        audit_zip_file(path, SOURCES[0])


def test_inconsistent_csv_row_width_is_not_trimmed(tmp_path):
    path = zip_fixture(tmp_path, csv_fixture(SOURCES[1], short=True))
    with pytest.raises(SourceSchemaError, match="ROW_LENGTH"):
        audit_zip_file(path, SOURCES[1])


def test_duplicate_header_rejected(tmp_path):
    source = SOURCES[0]
    fields = source.required + (source.required[0],)
    path = zip_fixture(tmp_path, (";".join(fields) + "\n" + ";".join("v" for _ in fields) + "\n").encode())
    with pytest.raises(SourceSchemaError):
        audit_zip_file(path, source)


def test_header_without_rows_rejected(tmp_path):
    path = zip_fixture(tmp_path, csv_fixture(SOURCES[1], rows=0))
    with pytest.raises(SourceSchemaError, match="NO_ORIGINAL_DATA_ROWS"):
        audit_zip_file(path, SOURCES[1])


@pytest.mark.parametrize("payload", [
    lambda s: ";".join(s.required).encode() + b"\n\xff",
    lambda s: (";".join(s.required) + '\n"unfinished').encode(),
])
def test_invalid_utf8_or_unbalanced_quotes_rejected(tmp_path, payload):
    path = zip_fixture(tmp_path, payload(SOURCES[0]))
    with pytest.raises(SourceSchemaError, match="ZIP_CRC_OR_UTF8_CSV_PARSE_FAILED"):
        audit_zip_file(path, SOURCES[0])


@pytest.mark.parametrize("unsafe", ["../record.csv", "/abs.csv", "sub\\record.csv", "record.json"])
def test_unsafe_member_name_or_type_rejected(tmp_path, unsafe):
    path = zip_fixture(tmp_path, csv_fixture(SOURCES[0]), name=unsafe)
    with pytest.raises(SourceSchemaError):
        audit_zip_file(path, SOURCES[0])


def test_two_csv_members_rejected(tmp_path):
    path = zip_fixture(tmp_path, csv_fixture(SOURCES[0]))
    with zipfile.ZipFile(path, "a") as z:
        z.writestr("extra.csv", csv_fixture(SOURCES[0]))
    with pytest.raises(SourceSchemaError, match="EXPECTED_EXACTLY_ONE_CSV_FILE"):
        audit_zip_file(path, SOURCES[0])


def test_negative_crc_mutation_rejected_at_full_stream_eof(tmp_path):
    path = zip_fixture(tmp_path, csv_fixture(SOURCES[0]))
    original = bytearray(path.read_bytes())
    directory = original.index(b"PK\x01\x02")
    # Mutate the central directory CRC, not an unused deflate bit.
    original[directory + 16] ^= 1
    path.write_bytes(original)
    with pytest.raises(SourceSchemaError, match="ZIP_CRC_OR_UTF8_CSV_PARSE_FAILED"):
        audit_zip_file(path, SOURCES[0])


@pytest.mark.parametrize("bad_url", [
    "http://dadosabertos.aneel.gov.br/",
    "https://dadosabertos.aneel.gov.br.evil.example/",
    "https://example.org/",
    "https://u:p@dadosabertos.aneel.gov.br/data.zip",
])
def test_publisher_host_guard(bad_url):
    with pytest.raises(SourceAccessError):
        official_url(bad_url)


def test_ambiguous_one_column_header_not_accepted():
    with pytest.raises(SourceSchemaError, match="AMBIGUOUS"):
        choose_delimiter("one_column")


def test_reject_mismatched_ckan_resource_url_and_identity():
    class Response:
        status = 200
        def __init__(self, body):
            self.body = body
        def geturl(self):
            return SOURCES[0].api_url
        def read(self, limit):
            return self.body[:limit]
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    class FakeOpener:
        def __init__(self, item):
            self.body = json.dumps({"success": True, "result": item}).encode()
        def open(self, request, timeout):
            return Response(self.body)
    source = SOURCES[0]
    row = {"id": source.resource_id, "package_id": source.package_id,
           "url": source.expected_url, "format": "ZIP", "size": 128}
    assert read_metadata(source, opener_obj=FakeOpener(row))["published_size_bytes"] == 128
    with pytest.raises(SourceAccessError, match="URL_NOT_PREDECLARED"):
        read_metadata(source, opener_obj=FakeOpener({**row, "url": "https://evil.example/a.zip"}))
    with pytest.raises(SourceAccessError, match="RESOURCE_IDENTITY"):
        read_metadata(source, opener_obj=FakeOpener({**row, "id": "some-other-resource"}))
    with pytest.raises(SourceAccessError, match="SIZE_OUTSIDE_BUDGET"):
        read_metadata(source, opener_obj=FakeOpener({**row, "size": 0}))


def test_source_api_failure_reports_access_block_not_a_pass(tmp_path):
    def fail(_):
        raise SourceAccessError("SYNTHETIC_ACCESS_ERROR")
    row = audit_one(SOURCES[0], tmp_path, read=fail)
    assert row["decision"] == "SOURCE_ACCESS_OR_BUDGET_BLOCKED"
    assert "original_zip_sha256" not in row


def test_only_synthetic_fixture_rows_are_used():
    assert len(SOURCES) == 2
    assert set(x.key for x in SOURCES) == {"occ_2026", "int_2026"}
    assert all(x.api_url.startswith("https://dadosabertos.aneel.gov.br/") for x in SOURCES)

def test_D06_selected_semicolon_header_survives_wrong_comma_candidate(tmp_path):
    """A confirmed D05 original-header case, built here only from synthetic names."""
    source = SOURCES[0]
    header = ";".join('"' + name + '"' for name in source.required)
    assert choose_delimiter(header + "\n") == ";"
    import csv
    with pytest.raises(csv.Error):
        next(csv.reader([header + "\n"], delimiter=",", strict=True))
    row = audit_zip_file(zip_fixture(tmp_path, (header + "\n" + ";".join("fixture" for _ in source.required) + "\n").encode()), source)
    assert row["total_original_csv_records"] == 1
    assert row["zip_crc_eof_checked"]


def test_D06_changed_source_hash_is_rejected_before_csv_decode(tmp_path):
    from experiments.rp_u005_d06_source import ORIGINAL_D04_ZIP_BYTES
    source = SOURCES[1]
    def metadata(_):
        return {"source_url": source.expected_url, "published_size_bytes": ORIGINAL_D04_ZIP_BYTES[source.key]}
    def fake_download(source, meta, path):
        return {"original_zip_sha256": "0" * 64, "original_zip_bytes": ORIGINAL_D04_ZIP_BYTES[source.key]}
    def parse_must_not_run(path, source):
        raise AssertionError("decode must not run after original source SHA mismatch")
    row = audit_one(source, tmp_path, read=metadata, download=fake_download, parse=parse_must_not_run)
    assert row["decision"] == "SOURCE_OBJECT_CHANGED"
    assert row["error"] == "ORIGINAL_ZIP_BYTES_DIFFER_FROM_D04"
