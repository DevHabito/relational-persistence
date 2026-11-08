"""Bounded first-party PDF-byte audit for four ANEEL data dictionaries.

Frozen scope: docs/protocols/RP-U005-D03-ANEEL-PDF-IDENTITY.md.
This is source identity work; it does not retrieve original incident rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

import fitz  # PyMuPDF, pinned by the audit workflow


HOST = "dadosabertos.aneel.gov.br"
MAX_BYTES = 1_048_576
MAX_PAGES = 16
BASE = f"https://{HOST}/dataset/"


@dataclass(frozen=True)
class Source:
    key: str
    package_id: str
    resource_id: str
    filename: str
    year: int
    kind: str

    @property
    def url(self) -> str:
        return f"{BASE}{self.package_id}/resource/{self.resource_id}/download/{self.filename}"


SOURCES = (
    Source("occ_2026", "ced06b4c-45a5-4cae-8a7e-f576ffc3b412", "00ddb056-c4fd-4fad-8cce-0807c527c8ee", "dm-ocorrencias-emergenciais-nas-redes-de-distribuicao.pdf", 2026, "occurrence"),
    Source("occ_pre2026", "ced06b4c-45a5-4cae-8a7e-f576ffc3b412", "8cbcef2a-fd4d-4e54-8f72-1a3a3e942314", "dm-ocorrencias-emergenciais-nas-redes-de-distribuicao.pdf", 2022, "occurrence"),
    Source("int_2026", "ccb25653-f07b-4f28-84c2-62a89d1f5a56", "6e5611de-948d-4473-b309-520d7523b762", "dm-interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao.pdf", 2026, "interruption"),
    Source("int_pre2026", "ccb25653-f07b-4f28-84c2-62a89d1f5a56", "101e4650-6a02-4f1f-8034-4c267b1ea462", "dm-interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao.pdf", 2022, "interruption"),
)


class SourceError(ValueError):
    pass


class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def require_official_url(url: str) -> None:
    part = urllib.parse.urlsplit(url)
    if part.scheme != "https" or part.hostname != HOST or part.port not in (None, 443):
        raise SourceError("NONOFFICIAL_OR_NONHTTPS_URL")
    if part.username or part.password:
        raise SourceError("CREDENTIAL_URL_REJECTED")


def bounded_download(source: Source, opener=None) -> tuple[bytes, dict]:
    require_official_url(source.url)
    if opener is None:
        opener = urllib.request.build_opener(RestrictedRedirect)
    request = urllib.request.Request(
        source.url,
        headers={"User-Agent": "RelationalPersistence-SourceAudit/1.0", "Accept": "application/pdf"},
    )
    with opener.open(request, timeout=15) as response:
        final_url = response.geturl()
        require_official_url(final_url)
        status = response.status
        if status != 200:
            raise SourceError("HTTP_STATUS_NOT_200")
        advertised = response.headers.get("Content-Length")
        if advertised is not None:
            try:
                size = int(advertised)
            except ValueError as exc:
                raise SourceError("INVALID_CONTENT_LENGTH") from exc
            if size <= 0 or size > MAX_BYTES:
                raise SourceError("PUBLISHER_SIZE_OUTSIDE_BUDGET")
        chunks, remaining = [], MAX_BYTES + 1
        while remaining:
            block = response.read(min(16_384, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        data = b"".join(chunks)
        if len(data) > MAX_BYTES:
            raise SourceError("PDF_BYTE_BUDGET_EXCEEDED")
        if advertised is not None and len(data) != size:
            raise SourceError("CONTENT_LENGTH_MISMATCH")
        return data, {
            "http_status": status,
            "final_url": final_url,
            "content_type": response.headers.get("Content-Type"),
        }


def header_fields(text: str) -> dict:
    m_version = re.search(r"Dicion[aá]rio\s+Vers[aã]o\s*:\s*([0-9]+\.[0-9]+)", text, flags=re.I)
    m_date = re.search(r"\bData\s*:\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{4})", text, flags=re.I)
    date = m_date.group(1) if m_date else None
    year = int(date[-4:]) if date else None
    return {"version": m_version.group(1) if m_version else None, "header_date": date, "header_year": year}


def inspect_pdf_bytes(source: Source, data: bytes, out_dir: Path) -> dict:
    if not data.startswith(b"%PDF-"):
        raise SourceError("INVALID_PDF_MAGIC")
    if b"%%EOF" not in data[-2048:]:
        raise SourceError("PDF_MISSING_FINAL_EOF")
    if len(data) > MAX_BYTES or len(data) == 0:
        raise SourceError("PDF_SIZE_INVALID")
    try:
        with fitz.open(stream=data, filetype="pdf") as document:
            if document.needs_pass or not (1 <= document.page_count <= MAX_PAGES):
                raise SourceError("PDF_ENCRYPTED_OR_PAGE_COUNT_INVALID")
            page = document.load_page(0)
            text = page.get_text("text")
            pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), colorspace=fitz.csRGB, alpha=False)
            png = pix.tobytes("png")
            pages = document.page_count
    except SourceError:
        raise
    except Exception as exc:
        raise SourceError("PDF_DECODE_OR_RENDER_FAILED") from exc
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{source.key}.pdf").write_bytes(data)
    (out_dir / f"{source.key}_page1.png").write_bytes(png)
    fields = header_fields(text)
    expected_phrase = {
        "occurrence": "Ocorrências Emergenciais nas Redes de Distribuição",
        "interruption": "Interrupções de Energia Elétrica nas Redes de Distribuição",
    }[source.kind]
    title_ok = expected_phrase.casefold() in " ".join(text.split()).casefold()
    return {
        "source_id": source.key,
        "source_url": source.url,
        "expected_year": source.year,
        "kind": source.kind,
        "original_pdf_bytes": len(data),
        "original_pdf_sha256": hashlib.sha256(data).hexdigest(),
        "first_page_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "first_page_png_sha256": hashlib.sha256(png).hexdigest(),
        "page_count": pages,
        "first_page_title_matches_kind": title_ok,
        **fields,
        "expected_header_year_matched": fields["header_year"] == source.year and title_ok,
    }


def decide(results: list[dict]) -> str:
    if len(results) != len(SOURCES) or {x["source_id"] for x in results} != {s.key for s in SOURCES}:
        raise SourceError("INCOMPLETE_OR_DUPLICATE_SOURCE_REPORT")
    if any("error" in x for x in results):
        return "SOURCE_ACCESS_OR_PDF_INTEGRITY_BLOCKED"
    if all(x["expected_header_year_matched"] for x in results):
        return "FOUR_DICTIONARIES_AUTHENTICATED_EXPECTED_VERSIONS"
    return "FOUR_DICTIONARIES_AUTHENTICATED_UNEXPECTED_CONTENT"


def run(out_dir: Path, acquire=bounded_download) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for source in SOURCES:
        try:
            original, metadata = acquire(source)
            item = {**inspect_pdf_bytes(source, original, out_dir), **metadata}
        except (SourceError, urllib.error.URLError, TimeoutError, OSError) as exc:
            item = {"source_id": source.key, "source_url": source.url, "expected_year": source.year,
                    "error": type(exc).__name__, "error_detail": str(exc)[:300]}
        results.append(item)
    report = {
        "study": "RP-U005-D03",
        "kind": "ORIGINAL_PUBLISHER_PDF_BYTES_ONLY",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_commit": "c46f1326e7de685af956f55d3f7b65d7d5cc4752",
        "source_count": len(results),
        "decision": decide(results),
        "source_results": results,
        "incident_rows_read": 0,
        "policy_effect_estimated": False,
        "actual_repair_cost_measured": False,
    }
    (out_dir / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    out_dir = Path("_aneel_dictionary_audit")
    print(json.dumps(run(out_dir), ensure_ascii=False, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
