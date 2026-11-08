# RP-U005-D05 — Bounded original ZIP prefix header diagnosis (after D04 failure)

**Dated:** 8 November 2026  
**Parent:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`.  
**Classification:** explicitly **after the negative original RP-U005-D04 source-gate outcome**, and before any new D05 original byte-range acquisition. This is an informed debugging/provenance gate, **not** a fresh preregistered prediction about physical restoration.

## Known facts at registration

The first D04 hosted run [#42508927432](https://github.com/DevHabito/relational-persistence/actions/runs/42508927432) successfully acquired the complete compressed 2026 occurrence and interruption ZIP files, returning exact lengths **176,074,116** and **202,900,063** bytes and original compressed SHA-256 values:

- Occurrence: `7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c`.
- Interruption: `87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d`.

Its original CSV source result was **negative**: `SOURCE_GATE_NOT_PASSED`, with `SOURCE_SCHEMA_REJECTED / INVALID_HEADER_QUOTING` for each file. The D04 instrument used an unsafe header chooser that aborted if *any* delimiter candidate (semicolon or comma) raised under `csv.reader(strict=True)`. A synthetic well-formed `"A";"B";"C"` header passes with semicolon and fails with comma. This defect candidate was **recognized after seeing D04's failure** and cannot be declared a blind prediction.

No full original CSV data rows, ZIP member CRC, or column lists were recovered by D04. Do not rewrite the D04 result or claim D04 CSV passed.

## D05 narrow question

Does an independently obtained **provider-acknowledged compressed byte range from byte 0** of each of the two exact D04 resources contain a first ZIP member whose decoded **header alone** reproduces this semicolon/quoted-field delimiter scenario? We need only the header, not any original data row. One prefix is sufficient to establish the delimiter for that prefix; it is **not** enough to prove whole-object identity, full decompression, full dataset integrity or any scientific model.

## Fixed original source IDs and addresses

Use **only** these publisher source URLs:

- `occ_2026`: `https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/040c840a-b9fa-4c63-bd3-f1a99640366b/download/ocorrencias-emergenciais-rede-distribuicao-2026.zip`.
- `int_2026`: `https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/33a21bd6-4893-42fc-bc05-888154f7511e/download/interrupcoes-energia-eletrica-2026.zip`.

Read **exactly one** HTTP Range request per URL: `Range: bytes=0-65535`. No retries to mirrors, alternate years, alternate formats, no credentials, and no paid calls. Require status **206**, same official HTTPS destination, exact `Content-Range` `bytes 0-65535/TOTAL`, with `TOTAL` equal to the first D04 original complete ZIP size. If server returns 200 for an ignored range, stop without consuming the full file. Read **at most 65,537 bytes** and refuse a wrong byte count. The current ZIP SHA-256 can **not** be compared to the complete D04 SHA using only a prefix; the TOTAL-size check alone does not prove the resource body has not changed.

## Fixed header-only decoding and negative controls

Check ZIP local-file header signature `PK\x03\x04`, entry flags, ZIP entry-name length and extra-length, and compression method **8 (deflate) or 0 (stored)**. Reject encrypted or unsafe member names, non-`.csv` first entry, incomplete first header, invalid UTF-8, unsupported method, or more than **1 MiB** of decompressible header-buffer output. Parse only the first LF-terminated line as a candidate CSV header; do not parse, count, print or store the decoded operational data rows that may follow it. Do not try to validate ZIP central directory, full CRC or complete member content from this prefix.

For the header, independently attempt **both** candidate parsers, semicolon and comma, with Python `csv.reader(strict=True)`. Record for each candidate whether parsing succeeded, number of distinct nonempty columns, and the exact error class/message on failure. Preserve the entire list of **header field names** (public schema field names, not personal row values); hash the literal first header bytes. Mark schema-aligned header only if one successful candidate contains all expected 2026 required field names. If both candidates succeed, do not automatically claim an identified source delimiter without a deterministic unique-winner rule. If none succeed, report undecided, not malformed full original files.

The candidate explanation is *confirmed for the observed prefix* only if semicolon successfully parses the required fields **and** comma fails on strict quoting. If prefix access or decoding is unavailable, report `PREFIX_DIAGNOSTIC_BLOCKED`. Other outcomes: `PREFIX_DIAGNOSTIC_CONFIRMS_DELIMITER_DEFECT` or `PREFIX_DIAGNOSTIC_INCONCLUSIVE`. Neither positive outcome repairs D04's permanent negative source decision.

## Mandatory evidence and limits

First-run JSON: source ID, HTTP status, total original content-length claim, bytes actually fetched, prefix SHA-256, ZIP local entry name and compression type, first header byte SHA-256, parsed field-name list and both delimiter outcomes. Preserve JSON only (90-day GitHub Actions artifact); never upload original prefix, original decompressed rows, CNPJ values or full ZIP bodies. Print JSON and SHA-256 to CI log. Run synthetic negative tests before original range requests. Keep first-run result immutable even if code needs correction.

No meaningful claim about original full event-row counts, legitimate join, real-time observation, crew/repair costs, dynamic topology, F2 restoration or novel law follows from this source-format diagnosis. If D05 identifies a source-specific but **general parser defect**, a *later*, separately frozen D06 full-source study can fix and retest. Do not modify D04's preregistration or its first-run archive.
