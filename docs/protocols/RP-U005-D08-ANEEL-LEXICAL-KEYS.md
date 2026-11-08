# RP-U005-D08 — Source key-field lexical format diagnostic (after D07's zero-key result)

**Dated:** 8 November 2026. **Parent D07 review head:** `2f6540a83485c491dd51ee979a63c3ce6392ea9a`.  
**Classification:** source-only **post-D07** lexical diagnostic. The D07 finding that every row failed its strict two-digit month predicate, and the observed compound occurrence-code failure totals, are **already known**. This is not a pre-registered new physical forecast, a positive repair-policy test or a blind result.

## Frozen source identity and question

What are the *observed literal formats* of (a) competence month and (b) the source-defined occurrence-reference ID in the two exact ANEEL 2026 original CSV sources? The D07 population had zero keys eligible under its `01`–`12` two-character month rule; this audit must not alter that first-run result.

Use only the two exact original publisher URLs and source IDs previously pinned by D06/D07, with original compressed ZIP SHA-256:
- Occurrences: `7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c`, 176,074,116 ZIP bytes; original decoded CSV SHA `736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567`, 6,789,484 records.
- Interruptions: `87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d`, 202,900,063 ZIP bytes; decoded SHA `4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce`, 6,078,331 records.

Download within the unchanged 240 MiB compressed per-source limit through the first-party CKAN metadata API and exact HTTPS source URL. Before inspecting decoded CSV rows verify compressed SHA and length, then stream the whole single CSV member to EOF, strict UTF-8, row-width, 5 GiB uncompressed per-member limit and ZIP CRC and verify decoded SHA and full original row count. Retain no operational row, no CNPJ and no raw occurrence code.

## Registered month output categories (entire CSV)

Extract the literal `NumMesCompetencia` or `MesCompetencia` string. Report **only** counts for the **allowlisted, nonsensitive month spellings**: `1,2,3,4,5,6,7,8,9,10,11,12,01,02,03,04,05,06,07,08,09`. The duplicates `10,11,12` count once each; preserve exact source spelling and leading zeroes.

Also report count of: empty string; numeric ASCII single character outside those allowlisted month spellings; numeric ASCII two characters outside; other ASCII decimal of different length; and all other strings, **without displaying any of the latter raw values**. Do not infer `1` and `01` are semantically equivalent for an actual event: the outcome will be a description of source lexical representation only.

The sum of all categories must equal each source's pinned full original row count. No post-hoc bins, deletion or small sample examples. If all records use one-digit spellings, that is an observed **format fact**, not a retrospective repair of D07.

## Registered occurrence-code quality categories

Inspect `CodOcorrenciaEmergencial` or `CodOcorrencia`, but **never store or print the literal ID**. Report total occurrences for these **nonexclusive** syntax failures:
- empty code;
- code length above 10 characters;
- non-ASCII character;
- leading/trailing whitespace;
- forbidden key-separator U+001F.
Also report count of rows passing the complete original D07 code syntax predicate, and count of rows failing one or more. The nonexclusive categories may overlap; they do **not** sum to the failing total. Do not report sample IDs, hashes of individual IDs, top IDs, or per-distributor counts.

The original D07 total failure counts of **1,929,271** occurrence rows and **1,293,508** interruption rows are already known; use them only for **independent exact validation** of the newly measured combined-failure totals. **Any disagreement is an instrument failure or source identity violation**, not grounds to tune thresholds.

## Frozen outcomes and stop rules

- `SOURCE_FORMAT_PROFILE_COMPLETE`: both exact D06 source objects and full decoded contents verified; all row and month count conservation identities hold, and combined code-format failures equal the first D07 totals. Report all listed frequency bins, including zeros.
- `SOURCE_OBJECT_CHANGED`: any original compressed ZIP byte count or SHA mismatch. No source profile accepted.
- `SOURCE_GATE_NOT_PASSED`: required CSV header absent, malformed row, CRC, UTF-8, byte limit or original decoded SHA/count mismatch. No partially computed profile claimed as complete.
- `INSTRUMENT_FAILURE`: implementation, conservation, memory, processing resource or unexpected failure. Preserve it as such.

Original source run on an isolated GitHub-hosted Ubuntu/Python 3.11 runner, timeout 20 minutes. Synthetic spelling and code-format overlap tests **must pass before any original source download**. Only final bounded JSON aggregates may be uploaded as 90-day artifact or committed as a first-run report; no raw ZIP, uncompressed CSV, original identifiers or identifiable row examples.

## What D08 cannot prove

No full historical online availability of outage events, no unique or valid real incidence code, no source-to-source linkage success, no causal restoration timing, no assigned repair intervention or live energized topology, no greedy/lookahead empirical effect and no universal relational-persistence/physics law. A later **separately frozen** source-key normalization and join study may be proposed based on D08, but may not rewrite D07's zero-key outcome.
