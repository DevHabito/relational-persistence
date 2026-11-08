# RP-U005-D04 — Bounded original ANEEL 2026 operational ZIP source gate

**Dated:** 8 November 2026  
**Repository parent:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`.  
**Status:** independent source-only study whose protocol was frozen **before any new ANEEL event ZIP byte or row was read in this D04 study**. Catalog metadata, original dictionary PDFs and their hashes were already inspected; this is informed source selection, not a blind discovery. No forecasting, policy optimization, statistical effect or universal law may be inferred here.

## Question

Can two exact first-party ANEEL 2026 annual-to-date ZIP source objects be acquired completely on a hosted runner, authenticated from their entire compressed bytes, decoded without truncation or silent record exclusion, and checked for their documented 2026 header fields? This is **source and record-format eligibility** only. It cannot yet establish completeness of the publisher's reporting population, cross-dataset join correctness, causal-time access or real repair effectiveness.

## The two and only two fixed sources

Use the published CKAN resource metadata API on the **same official host** `https://dadosabertos.aneel.gov.br/api/3/action/resource_show?id=...`. Only these exact resource IDs are allowed; each metadata response must assert `success=true`, the matching resource ID and matching `package_id`, and its URL must have official HTTPS host and the exact resource path, ending in the intended ZIP filename:

1. `occ_2026`: resource ID `040c840a-b9fa-4c63-bd3-f1a99640366b`, package ID `ced06b4c-45a5-4cae-8a7e-f576ffc3b412`, exact expected URL
   `https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/040c840a-b9fa-4c63-bd3-f1a99640366b/download/ocorrencias-emergenciais-rede-distribuicao-2026.zip`.
2. `int_2026`: resource ID `33a21bd6-4893-42fc-bc05-888154f7511e`, package ID `ccb25653-f07b-4f28-84c2-62a89d1f5a56`, expected URL
   `https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/33a21bd6-4893-42fc-bc05-888154f7511e/download/interrupcoes-energia-eletrica-2026.zip`.

The URL values are **predeclared expectations** from the official resource IDs and filename convention; occurrence's exact first-party URL has been independently observed in its publisher page. The interruption filename is **not** accepted as authenticated until the live official CKAN API confirms the URL. Any unexpected URL or API failure must STOP the corresponding source, not silently substitute a guess or alternate ZIP/Parquet/mirror/other year.

The catalog previously listed 167.9 MiB (occurrence) and 193.5 MiB (interruption) compressed ZIP resources, with 2026 partial-year metadata last updated in September 2026. The listed 32-hex catalog hash has **unknown algorithm** and is not declared to be SHA-256. Because CKAN resources may be revised, record the response's exact metadata, revision and whole-object SHA from the observed run. Never describe an arbitrary present-time resource version as a frozen independent historical source population.

## Fixed limits and sequence

1. Single GitHub Ubuntu hosted job, Python 3.11, no credentials/paid APIs or source mirrors. `urllib` HTTPS, 30s connect/read timeout, same-host redirects only and maximum 3 total retries **of the same original URL** on transient network errors (log attempts). Waits are fixed 2, 4, 8 seconds. No alternative source if all attempts fail. Max API response 64 KiB each.
2. Read the metadata for both exact resource IDs, record full response SHA-256 (not the raw metadata body in public project if it contains sensitive data; metadata only), published size, update timestamp, content type, final URL, advertised catalog hash. Fail source if ID/package/format/URL differ or source size `<=0` or `> 240 MiB`.
3. Sequential bounded source downloads to **temporary disk only**; at most **240 MiB per compressed object** plus 1 sentinel. Compare actual compressed byte count to both HTTP Content-Length (when provided) and publisher metadata's `size` when it is a positive integer. Record original-compressed ZIP SHA-256, not a guessed hash algorithm. Record actual final URL and HTTP 200. Do not commit or publish raw operational event rows to GitHub or user conversation.
4. Verify ZIP directory, exactly one non-directory `.csv` member per ZIP, no path traversal, encryption, symlinks or unexpected archive payloads, and no ZIP-level modification. Max declared uncompressed member size **5 GiB** each; total **10 GiB**, with an additional decompressed read sentinel and strict ZIP CRC on entire member. Do not call a prefix a full file.
5. Entire original member must be a valid **strict UTF-8 CSV stream** with one header and no malformed records. Candidate delimiters are **semicolon or comma only**: determine solely from the first complete header line by choosing the one that yields the largest number of nonempty distinct field names, with a deterministic failure on a tie; never choose based on outcome data. No quoting repair, no character replacement and no dropped rows. The first header is not counted as a data row. Reject duplicate or empty column names, row-length mismatches, null or invalid UTF-8, incomplete trailing quoted records, and decompression/CRC errors. A CSV schema check requires the exact fields frozen below; additional fields may be reported, not silently dropped.
6. Required occurrence fields: `NumCnpjDistribuidora`, `CodOcorrenciaEmergencial`, `NumAnoCompetencia`, `NumMesCompetencia`, `DthIniOcorrencia`, `DthFimOcorrencia`, `NumTempoPreparacao`, `NumTempoDeslocamento`, `NumTempoExecucao`. Required interruption fields: `NumCNPJDistribuidora`, `CodOcorrencia`, `AnoCompetencia`, `MesCompetencia`, `DatInicioInterrupcao`, `DatFimInterrupcao`, `QtdConsumidoresAfetados`. The original 2026 dictionary PDF SHA-256 anchors are `e12befc9c8984d6f13df545f50c2f6373e2f35318f30d986ca2a54f47a3db4dd` and `d510fabae63909fa9237215c0f17860e8144810de2e3c2ed65fd4fad516062ad` (RP-U005-D03 original byte audit).
7. For every fully checked file record original compressed SHA-256, all original uncompressed bytes SHA-256 (through a streaming hash), ZIP member CRC status, UTF-8 and CSV parse outcome, exact original column names in published order, total data rows and **descriptive counts of empty required fields**. A missing occurrence ID is **not automatically treated as a scientific falsification**; it is a reported data-quality property. Do not log or store row values, identities, CNPJ strings or raw contents.
8. No attempt to join records, infer duplicate rates by sampling, reconstruct topology, estimate empirical repair cost or use an outcome. No row exclusion, one-to-many suppression or tuning a denominator. A source that downloads but contains required-field gaps yields `DATA_QUALITY_REPORTED`, not a passed prediction or a fabricated full population.

## Frozen statuses, applied per source and together

- `SOURCE_COMPLETE_SCHEMA_AUDITED`: full original ZIP authenticated and full declared CSV member stream parsed to EOF with CRC, header contains all required fields, no malformed rows. Empty required values may be reported as descriptive quality counts. This **does not** certify completeness of ANEEL's reporting population or correct linkage between datasets.
- `SOURCE_SCHEMA_REJECTED`: full authenticated ZIP/CSV has an absent required column, duplicate/empty header, corrupt/invalid member, parsing error, UTF-8 failure or row-length mismatch. Preserve evidence and failure; do not try to fix the source in this protocol.
- `SOURCE_ACCESS_OR_BUDGET_BLOCKED`: metadata API fails or disagrees, source download fails, byte/time/size budget is exceeded or provider authenticates an unexpected URL/format. No claim of complete ZIP identity for an object not fully received.
- `INSTRUMENT_FAILURE`: missing test dependencies, unexpected code defect, system failure or auditing runtime error. Never rewrite this as failed data quality without evidence.
- Overall `BOTH_SOURCE_SCHEMAS_AUDITED` only if both sources attain `SOURCE_COMPLETE_SCHEMA_AUDITED`; otherwise report each exact outcome and `SOURCE_GATE_NOT_PASSED`.

Stop with an original JSON **even on negative source decisions**. Preserve original full source ZIPs only temporarily in the hosted runner; upload only summary JSON as an Actions artifact, retain 90 days, print entire bounded JSON and its digest to the job log. No automatic pushes to `main`, no credentials beyond read-only checkout.

## Planned adversarial controls

Before the first real source request, test: corrupt compressed CRC/member, wrong ZIP magic, duplicate/unknown header, missing required columns, unbalanced quoted record, Unicode decoding failure, wrong row-length, overdeclared archive size, malformed resource API object, forced unexpected host, byte-budget rejection, strict EOF and proper zero-row source classification. All synthetic fixtures only, no real ANEEL rows.

**Predeclared stop:** If the source API is inaccessible or any source size is too large, record the failure; do not switch to a different 2026 representation post hoc. If the source has unexpected member structure, record it exactly; alternative parsing requires a separate and clearly **post-first-run** protocol.

## Conclusions explicitly not licensed

No evaluated real join, causal-time awareness, dynamic graph, selected edge repair, policy counterfactual, known operator decision computation cost, F2 operational outcome, physical pregeometry or `C=B/(I*tau)` law. A passing software CI or even successful complete data file parsing does not provide them. A new source eligibility study is not a fresh prediction of network resilience.
