# RP-U005-D03 — Original ANEEL dictionary byte-identity gate

**Dated:** 8 November 2026.  
**Baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`.  
**Classification:** separate **source-only** experiment, planned after reading existing publisher web text and observing an inconsistent third-party PDF screenshot. This is *not* an independent blind scientific test of recovery or of any policy. This scope is committed **before** the new hosted full-byte download.

## Original problem and prior observations

The publisher's page for each of ANEEL's emergency-occurrence and interruption datasets distinguishes a data dictionary for records starting January 2026 from a separate dictionary for data through December 2025. The 2026 occurrence PDF's web text gives **v1.1, 28 July 2026**, whereas the web PDF screenshot tool showed **v1.0, 11 October 2022**, even for the explicitly 2026 link. The corresponding interruption link's extracted text gave **v1.0, 21 July 2026** and its screenshot likewise showed the 2022 first page. The older links' text and screenshots agreed on 2022.

This discrepancy was already known before the protocol and cannot now be called a fresh prediction. It could originate in a third-party viewer/cache/tool or the upstream resource; **no cause has been established**. An attempt to download source PDFs in the present analysis container failed at DNS, before reaching the official host. The original PDF bytes have not yet been authenticated.

## Source population: exactly four official published resources, no alternates

The only eligible sources are these four URLs (same filenames, different resource IDs); URL and intended role are fixed before downloading:

1. **occ_2026** — `https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/00ddb056-c4fd-4fad-8cce-0807c527c8ee/download/dm-ocorrencias-emergenciais-nas-redes-de-distribuicao.pdf`
2. **occ_pre2026** — `https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/8cbcef2a-fd4d-4e54-8f72-1a3a3e942314/download/dm-ocorrencias-emergenciais-nas-redes-de-distribuicao.pdf`
3. **int_2026** — `https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/6e5611de-948d-4473-b309-520d7523b762/download/dm-interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao.pdf`
4. **int_pre2026** — `https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/101e4650-6a02-4f1f-8034-4c267b1ea462/download/dm-interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao.pdf`

**Never** silently replace a URL with an alternate, a stale cache, a locally installed sample or an invented fallback. These links were inspected as first-party publisher download links through web search on 8 November 2026, but no hashes were obtained.

## Bounded acquisition and authentication protocol

1. Use a single Ubuntu GitHub-hosted runner with Python 3.11 and `PyMuPDF==1.26.5` for bounded PDF parsing/rendering. No privileged credentials, account keys, paid query, or remote code execution.
2. Download sequentially (not concurrently), with `urllib.request`, a 15-second per-request timeout, and maximum **1,048,576 bytes per PDF**; read one additional sentinel byte to detect an overlimit file. Four PDFs combined must not exceed **4 MiB**. Only HTTPS and publisher-host `dadosabertos.aneel.gov.br` are accepted as final destinations. No retries to other hosts or mirrors; an HTTP/DNS error is a source-access result, not a reason to forge bytes.
3. Record the final HTTP status, returned Content-Type (descriptive), final URL, byte count, exact complete original PDF SHA-256 and SHA-256 of its first-page rasterized PNG (at fixed scale = 1, RGB) for successfully downloaded objects. Reject blank, non-`%PDF-`, incomplete `%%EOF`, over-budget, invalid PDF, wrong-host redirects or missing pages; do not trim or repair corrupt bytes.
4. Extract first-page text with PyMuPDF, normalize Unicode only for **header recognition** (not hashes), record the first-page version/date strings if extractable. A missing/ambiguous version is marked `VERSION_NOT_CERTIFIED` rather than guessed from the expected filename. Record page count and a deterministic text-digest on the extracted first-page text (not source-byte identity).
5. Compare the first-page original raster hashes, whole-file SHA-256 and version/date labels across the two 2026-vs-old pairs. PDF bytes can be different even when pages visually match; never infer byte equivalence from equal displayed text alone.
6. Print the bounded audit JSON (with **no original file bodies**) to CI logs, save that JSON plus public-source PDFs and first-page PNG renderings as a GitHub Actions artifact (max 4 MiB PDFs plus images). For long-term repo evidence, preserve the **JSON report only**, copied with exact SHA and provenance after the first run. Do not replace or rerun results silently to obtain a preferred outcome.
7. Tests of the local scientific guards are synthetic; they are **not** evidence about the actual publisher files. Do not mark the source passed until the original hosted download run is separately inspected and recorded.

## Registered decisions, no post-hoc threshold changes

- `FOUR_DICTIONARIES_AUTHENTICATED_EXPECTED_VERSIONS`: all four full PDFs independently obtained, both old items give header year 2022, both new items give header year 2026, and the extracted source content matches the expected category.
- `FOUR_DICTIONARIES_AUTHENTICATED_UNEXPECTED_CONTENT`: all four complete original PDFs obtained but header years are missing, ambiguous or contradict the expected item role. Preserve the exact mismatch; **do not** invent a resolution.
- `SOURCE_ACCESS_OR_PDF_INTEGRITY_BLOCKED`: at least one URL fails bounded download, host restrictions, byte-integrity guard, PDF validation, or execution prerequisite; no PDF or version conformance claim for that missing item. Keep any successful source hashes, and don't silently discard adverse items.

These classifications concern **only the four PDF dictionary objects at the time of this run**. Even a full success does NOT establish field-level records, 2026 database completeness, join correctness, live topology, known online observation times, repair-action counterfactuals, operator decision costs, electricity restoration efficacy or a relational-persistence physical law. The ANEEL dataset source files (hundreds of MiB) are outside this protocol and must **not** be downloaded.

## Testing and evidence integrity

Create self-contained, deliberately false PDFs using PyMuPDF to test valid/wrong dates, bad magic, over-budget, nonhost redirects, missing versions and exact duplicate-body classification. Do not test original publisher content until after this protocol commit; don't edit these conditions after reading first results. Any bug correction is documented in a separate commit with evidence of first-run failure or initial behavior, never represented as an original preregistered success.

**Stop after this source-identity result.** A later, distinct and reviewed protocol is needed to attempt a bounded, original-row audit of ANEEL's larger event resources.
