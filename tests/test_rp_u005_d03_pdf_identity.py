"""No ANEEL source bytes. All PDFs below are constructed locally."""
import hashlib
import urllib.error

import fitz
import pytest

from experiments.rp_u005_d03_pdf_identity import (
    SOURCES, SourceError, header_fields, require_official_url,
    inspect_pdf_bytes, decide, run, MAX_BYTES,
)


def fake_pdf(text: str) -> bytes:
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((40, 70), text, fontsize=12)
        return document.tobytes()


def test_fixed_four_urls_and_roles():
    assert len(SOURCES) == 4
    assert {s.key for s in SOURCES} == {"occ_2026", "occ_pre2026", "int_2026", "int_pre2026"}
    assert {s.year for s in SOURCES} == {2022, 2026}
    assert len({s.resource_id for s in SOURCES}) == 4
    for source in SOURCES:
        require_official_url(source.url)


@pytest.mark.parametrize("url", [
    "http://dadosabertos.aneel.gov.br/dataset/foo",
    "https://evil.example/dataset/foo",
    "https://dadosabertos.aneel.gov.br.evil.example/",
    "https://user:password@dadosabertos.aneel.gov.br/dataset/foo",
    "https://dadosabertos.aneel.gov.br:8443/dataset/foo",
])
def test_official_host_guard(url):
    with pytest.raises(SourceError):
        require_official_url(url)


def test_old_and_new_header_parsing():
    assert header_fields("Dicionário Versão: 1.1\nData: 28/07/2026") == {
        "version": "1.1", "header_date": "28/07/2026", "header_year": 2026
    }
    assert header_fields("Dicionário Versão: 1.0\nData: 11-10-2022")["header_year"] == 2022
    assert header_fields("No version\nNo date")["header_year"] is None


def test_constructed_pdf_sha_and_page_raster(tmp_path):
    original = fake_pdf("Dicionario Versao: 1.1")
    assert original.startswith(b"%PDF-")
    source = SOURCES[0]
    row = inspect_pdf_bytes(source, original, tmp_path)
    assert row["original_pdf_sha256"] == hashlib.sha256(original).hexdigest()
    assert row["page_count"] == 1
    assert len(row["first_page_png_sha256"]) == 64
    assert (tmp_path / f"{source.key}.pdf").read_bytes() == original
    assert row["expected_header_year_matched"] is False


@pytest.mark.parametrize("broken", [b"", b"NOT A PDF", b"%PDF-1.4\ntruncated", b"X" * (MAX_BYTES+1)])
def test_bad_magic_trailer_or_size_fails(tmp_path, broken):
    with pytest.raises(SourceError):
        inspect_pdf_bytes(SOURCES[0], broken, tmp_path)


def test_decision_strictly_partitions_frozen_categories():
    rows = [{"source_id": s.key, "expected_header_year_matched": True} for s in SOURCES]
    assert decide(rows) == "FOUR_DICTIONARIES_AUTHENTICATED_EXPECTED_VERSIONS"
    rows[2]["expected_header_year_matched"] = False
    assert decide(rows) == "FOUR_DICTIONARIES_AUTHENTICATED_UNEXPECTED_CONTENT"
    rows[2]["error"] = "URLError"
    assert decide(rows) == "SOURCE_ACCESS_OR_PDF_INTEGRITY_BLOCKED"
    with pytest.raises(SourceError):
        decide(rows[:-1])
    with pytest.raises(SourceError):
        decide([rows[0]]*4)


def test_failed_acquisition_is_reported_without_inventing_a_hash(tmp_path):
    def never_download(source):
        raise urllib.error.URLError("TEST_SENTINEL_OFFLINE")
    report = run(tmp_path, acquire=never_download)
    assert report["decision"] == "SOURCE_ACCESS_OR_PDF_INTEGRITY_BLOCKED"
    assert report["incident_rows_read"] == 0
    assert all("original_pdf_sha256" not in row for row in report["source_results"])
    assert (tmp_path / "audit.json").exists()


def test_no_assertion_based_audit_guards():
    with pytest.raises(SourceError):
        decide([])
