"""Synthetic prefix diagnostics only, no real ANEEL rows."""
import io
import zipfile
import pytest
from experiments.rp_u005_d05_header_diagnostic import (
    SOURCES, RANGE_BYTES, PrefixAuditError,
    zip_first_header, delimiter_observations, official_url,
    original_prefix, audit_source,
)


def synthetic_zip(header):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("fictional-2026.csv", (header + "\n" + "fictional;row\n").encode())
    payload = out.getvalue()
    assert len(payload) < RANGE_BYTES
    return payload + b"\x00" * (RANGE_BYTES - len(payload))


def test_valid_semicolon_quotes_cause_wrong_comma_strict_error():
    header = '"A";"B";"C"\n'
    outcomes, diagnosed = delimiter_observations(header, ("A", "B"))
    assert outcomes["semicolon"]["parser_accepted"] is True
    assert outcomes["semicolon"]["required_field_names_present"] is True
    assert outcomes["comma"]["parser_accepted"] is False
    assert diagnosed is True


def test_a_real_schema_name_fixture_is_not_automatic_publisher_evidence():
    for source in SOURCES:
        header = ";".join('"' + name + '"' for name in source["required"])
        first = zip_first_header(synthetic_zip(header))
        outcomes, diagnosed = delimiter_observations(first["header_text"], source["required"])
        assert diagnosed
        assert first["first_zip_member_name"] == "fictional-2026.csv"
        assert first["decompressed_prefix_is_not_full_member"]


@pytest.mark.parametrize("bad", [
    b"", b"x" * RANGE_BYTES, b"PK\x03\x04",
])
def test_missing_or_truncated_zip_prefix_is_rejected(bad):
    with pytest.raises(PrefixAuditError):
        zip_first_header(bad)


@pytest.mark.parametrize("bad_url", [
    "http://dadosabertos.aneel.gov.br/foo",
    "https://evil.example/real.zip",
    "https://dadosabertos.aneel.gov.br.evil.example/zip",
])
def test_only_official_https_source_allowed(bad_url):
    with pytest.raises(PrefixAuditError):
        official_url(bad_url)


def test_http_200_cannot_be_mistaken_for_successful_bounded_range():
    source = SOURCES[0]
    class Response:
        status = 200
        headers = {"Content-Range": f"bytes 0-65535/{source['expected_total']}"}
        def geturl(self): return source["url"]
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Opener:
        def open(self, request, timeout): return Response()
    with pytest.raises(PrefixAuditError, match="HTTP_RANGE_NOT_HONORED"):
        original_prefix(source, opener_obj=Opener())


def test_wrong_total_size_is_not_identity():
    source = SOURCES[0]
    class Response:
        status = 206
        headers = {"Content-Range": "bytes 0-65535/12345"}
        def geturl(self): return source["url"]
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Opener:
        def open(self, request, timeout): return Response()
    with pytest.raises(PrefixAuditError, match="ORIGINAL_RANGE_OR_LENGTH"):
        original_prefix(source, opener_obj=Opener())


def test_failed_prefix_never_promoted_to_dataset_validity():
    def fail(source): raise PrefixAuditError("FIXTURE_RANGE_NOT_HONORED")
    result = audit_source(SOURCES[0], acquire=fail)
    assert result["decision"] == "PREFIX_DIAGNOSTIC_BLOCKED"
    assert result["first_D04_complete_zip_SHA256_not_reverified"] is True
    assert "literal_first_header_sha256" not in result


def test_no_source_row_is_inspected_in_header_only_probe():
    def fake(source):
        literal = ";".join('"' + n + '"' for n in source["required"])
        return synthetic_zip(literal), {"http_status": 206, "prefix_bytes": RANGE_BYTES}
    item = audit_source(SOURCES[1], acquire=fake)
    assert item["decision"] == "PREFIX_DIAGNOSTIC_CONFIRMS_DELIMITER_DEFECT"
    assert "fictional;row" not in str(item)
    assert item["first_D04_complete_zip_SHA256_not_reverified"]
