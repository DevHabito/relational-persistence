# RP-U005-D06 — Re-audit of identical ANEEL 2026 ZIP objects with a corrected delimiter chooser

**Protocol date:** 8 November 2026. **Baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`.  
**Classification:** separately registered *after* D04 original source-gate failure and *after* D05 confirmed the delimiter instrumentation defect. This is NOT a blind hypothesis about network recovery; the favorable header-level fact is already known.

## Known historical outcomes (not being erased)

- Original D04 run `42508927432`: complete ZIP bytes received (176,074,116 emergency occurrence bytes, 202,900,063 interruption bytes) with original whole-ZIP SHA-256, but a faulty wrong-delimiter test rejected both before full CSV parsing. The original negative D04 JSON is immutable.
- D05 run `42509613295`: 65,536-byte original-compressed prefixes showed valid semicolon-delimited, quoted 2026 headers with 23 and 26 columns. The strict comma candidate raised `',' expected after '"'`. D05 did **not** verify entire source bodies or data rows.

## Exact source population and frozen byte identities

Download **only** the same two original publisher 2026 ZIP resources and exact URL strings/source identities registered in [D04](RP-U005-D04-ANEEL-OPERATIONAL-SOURCE.md), through the first-party CKAN metadata API and same-host HTTPS. No mirrors, no Parquet, no second calendar-year selection and no suffix substitutions.

1. `occ_2026`: original complete compressed size **176074116**, original SHA-256 **`7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c`**.
2. `int_2026`: original complete compressed size **202900063**, original SHA-256 **`87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d`**.

These full-object exact bytes are the population. If the publisher changes or the new bytes differ, return `SOURCE_OBJECT_CHANGED` for that file, and **do not** infer it is the same source, use new data to salvage the experiment, or alter the frozen SHA. A separately scoped source-version study would be needed.

## Only one algorithmic correction authorized

Reuse D04's read-only full-ZIP downloader and CSV reader limits **unchanged**: CKAN metadata identity/URL/format checks, 240 MiB compressed per ZIP, strict HTTP length agreement, one safe non-encrypted CSV ZIP member, 5 GiB original uncompressed byte limit and 10 GiB aggregate budget, complete UTF-8 decoding, complete ZIP EOF/CRC, exact registered 2026 fields, 1 MiB max header/field size, exact CSV row-width checking, immutable aggregate metadata only and never persisting raw rows.

The *only* parser fix is in `choose_delimiter`: independently catch parse failures from semicolon and comma alternatives. **A failed irrelevant candidate must not veto another valid candidate**. For each candidate, require nonempty, distinct header fields. Select uniquely the candidate with the most valid field names if at least two fields; otherwise reject. Both no candidates and ambiguous ties must still fail. There must be a new controlled regression with a semicolon-separated, quoted header that succeeds even though the comma candidate raises. All other existing negative controls from D04 must remain enforced.

**Additional provenance guard:** before processing any decompressed original CSV, verify the newly obtained complete compressed-byte SHA against the exact pinned D04 full-ZIP digest. Preserve SHA mismatch as `SOURCE_OBJECT_CHANGED`, not as corrupt ANEEL CSV.

## Primary source-only gate

For each exact file, report total complete original CSV rows, original header columns, empty required-field cells, decompressed original byte count/SHA, ZIP member name/CRC after full EOF, source size and compressed SHA. **Do not record or publish any CNPJ or individual operational row.** No source joins, duplicate-ID inference, splitting records for a favorable result, forecasting, topology transfer or restoration score. The 2026 year remains partial and changing; the exact SHA is an audit snapshot, not a representative complete-year population.

Predeclared statuses: `SOURCE_COMPLETE_SCHEMA_AUDITED`, `SOURCE_SCHEMA_REJECTED`, `SOURCE_ACCESS_OR_BUDGET_BLOCKED`, `SOURCE_OBJECT_CHANGED`, `INSTRUMENT_FAILURE`. Overall `BOTH_SOURCE_SCHEMAS_AUDITED` only if both complete source EOF/CRC checks passed with exact D04 SHA.

A row-length mismatch, bad UTF-8, bad archive CRC, missing required column or byte limit remains a STOP. In particular, record *zero* full-record counts if parsing stopped early rather than inventing a representative subset. A source that fully parses with missing key values reports them in the predeclared counts, not as an automatically healthy population.

## Hosted execution and original outcome

Commit this protocol alone before creating D06 implementation and workflow. Run synthetic fixture controls **before** any original download. A new one-time isolated branch GitHub Actions workflow may download exactly these two full ZIPs within the frozen budget and print JSON + SHA-256, uploading only the 90-day JSON artifact. It must not write to `main`, overwrite previous D04/D05 archives or persist raw event bodies.

A positive result confirms only that the fixed exact 2026 data files can be parsed fully under these declared structural rules. It does **not** certify event reports as complete/representative, causal-time feature availability, occurrence-to-interruption matches, valid outage recovery endpoints, physically meaningful F2 or superiority of any repair policy. A later *separate* protocol must register those tests before running any join.
