# RP-U005-D09 — Parallel literal-key census of ANEEL 2026 original source snapshots

**Protocol dated:** 8 November 2026. **Parent:** D08 reviewed head `3d96b4f01dfec2edb50752368560d48e8c953fb8`.  
**Registration:** this document is committed **alone** before D09 code and before any D09 original record is read. All D06/D07/D08 original outputs are previously known; this is a transparent, **retrospective source-linkage study**, not an unseen prediction, intervention evaluation, or physical-law test.

## Why this additional source gate exists

D06 authenticated full original ANEEL emergency-occurrence and interruption ZIP/CSV files (6,789,484 and 6,078,331 source rows). D07's frozen month rule required exactly two characters (`01`–`12`), so it admitted zero candidate keys. D08 independently showed that *all* original month representations in these sources are unpadded `1`–`8` or `1`–`7`. D08 also showed 1,929,271 occurrence and 1,293,508 interruption original records contain occurrence codes longer than the authenticated PDF dictionary's stated ten-character field width, and that no record failed the empty, non-ASCII or outer-whitespace tests. Those observations were **all already known when this protocol was written**.

The D07 first outcome remains a scientifically meaningful **failed key specification**, never revised or reclassified. This D09 asks a **different, jointly complete and exhaustively specified question**: how do candidate textual-key matches behave under two predeclared interpretations of the 2026 dictionary's code-width mismatch?

## Fixed source objects — both independently revalidated to EOF

Use **exactly** the first-party ANEEL CKAN 2026 resource URLs, resource and package IDs, and authentication rules inherited unchanged from D06 for:
- `occ_2026`: complete original compressed ZIP **176,074,116** bytes, SHA-256 `7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c`; full decoded CSV **2,236,732,733** bytes, SHA-256 `736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567`; **6,789,484** original data rows.
- `int_2026`: complete compressed ZIP **202,900,063** bytes, SHA-256 `87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d`; decoded CSV **2,328,209,339** bytes, SHA-256 `4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce`; **6,078,331** rows.

The original ZIP/CSV sha hashes and byte counts must be checked, not merely original filenames or HTTP responses. The 2026 resources are **partial-year published snapshots**, not an exhaustive national/yearly population. If either ZIP differs from its frozen SHA/size, stop as `SOURCE_OBJECT_CHANGED`. Do not select a newer revision to improve the score.

## Two simultaneously registered candidate-key cohorts

The **literal four-field key** is exactly the unmodified 14 ASCII decimal-digit distributor CNPJ (`NumCnpjDistribuidora` / `NumCNPJDistribuidora`), the literal year `2026`, **the original unpadded month string** `1`–`12` (`NumMesCompetencia` / `MesCompetencia`), and the **complete original** code string (`CodOcorrenciaEmergencial` / `CodOcorrencia`). A delimiter U+001F separates fields and is forbidden within values. Keep leading zeroes, original case and all original code characters. Never cast CNPJ or code to integer, remove padding, trim, casefold, truncate the code, use fuzzy matching, coerce dates, join by partial code, or infer a common key from an example. Original source IDs must never leave a temporary private runner.

Both cohorts are reported, regardless of their comparative match rates:

**Cohort S — dictionary-width-limited code:** same complete key, but `1 <= len(code) <= 10`. All rows with longer codes are **ineligible**, not truncated to ten. A correct original representation can remain an unmatched textual key.

**Cohort F — full observed code:** same complete key, but `1 <= len(code) <= 1,048,576` characters (the pre-existing strict CSV field-size bound). Code must be ASCII, no leading/trailing whitespace and no internal U+001F. This **does not assert** that longer codes are semantically valid per ANEEL. It simply quantifies outcomes when preserving the publisher CSV field exactly as printed. Cohort S is a subset of cohort F; classify code strings longer than ten *only in F*.

The only other eligibility rules in each cohort: CNPJ exactly 14 ASCII digits, year exactly `2026`, month exactly one of `1`–`12`. Invalid source rows count in the original denominator and in **nonexclusive** named format-failure reasons; no record is dropped from the source counts. The D08 unpadded-month evidence motivates this **later** change; it is not an ex-ante D07 prediction.

## Frozen exact census outputs

For **each source and each cohort S/F**, report:
- total original source rows; valid source rows, invalid source rows, nonexclusive invalid reason counts (distributor/year/month/code); distinct eligible keys; distinct keys occurring exactly once; repeated distinct keys, rows on repeated keys, and surplus repeated rows beyond first;
- on a full exact four-field cross-source key, matched distinct keys, unmatched distinct occurrence and interruption keys, matched and unmatched valid source **rows** on each side; strict count of one-to-one, one-to-many, many-to-one and many-to-many **keys**, with one-to-many meaning one occurrence source row and multiple interruption rows.
- the match *fractions* may be derived **only when** the valid source-row denominator is positive, and must be labeled as **literal record-key correspondence within each selected source cohort**, never fraction of physical outage events.

For cohort F, report additionally the number of eligible source rows whose original code exceeds ten characters, their distinct keys, and matched versus unmatched long-code keys/rows, so the effect of different eligible populations can be described without choosing the favorable cohort. A long-code key is never partially matched to a short key. The F/S delta must be conserved (long rows in F = F eligible rows - S eligible rows, barring other fixed validations). Compute all totals via on-disk SQLite group tables; **never** generate a many-to-many Cartesian product of individual rows.

The following identities are mandatory: each source original rows = valid + invalid; every source eligible rows = matched + unmatched; distinct eligible keys = matched distinct + unmatched distinct; all four multiplicity groups sum to matched distinct keys; repeated-key rows and surplus rows agree with group multiplicities; F eligible rows - S eligible rows = F eligible rows with codes >10; F keys whose code length is 1–10 equal S keys; F/S short-key matched counts agree exactly. Fail as `INSTRUMENT_FAILURE` on any mismatch.

## Execution, budget, privacy and stopping

A single Ubuntu GitHub-hosted Python 3.11 job, timeout **35 minutes**, no credentials/paid APIs. Download sequentially max **240 MiB** per ZIP using D06's same-host source API, bounded file client and two fixed original source IDs, and fully decode the single member to EOF, CRC, strict UTF-8, CSV row width, required 2026 columns, max 5 GiB decoded per file and complete decoded SHA/row count equality to D06. Only after original compressed SHA/byte identity check may a ZIP's rows be grouped. Max **6 GiB SQLite main file** (on disk) with 32 MiB cache, <=20,000 batched writes, and no Python dictionary with millions of original IDs. No raw ZIP, CSV, original CNPJ/incident identifier, individual matching example or SQLite database may be committed, uploaded, printed or returned; publish **aggregated counts only**.

Preflight includes **synthetic** one-to-one, one-to-many, many-to-one, many-to-many, leading zero, cross-month/company nonmatch, repeated-key conservation, long-code S/F comparison, rejection of SHA-tampered complete original source, invalid reason overlap and `python -O` guards. The original source workflow must run these before the first original D09 data request. If synthetic tests fail, **do not** download data. Freeze first source JSON and its independent SHA, whether positive or negative; report any code defect and correction in a later commit without editing the first run.

Frozen outcomes:
- `BOTH_SOURCE_DUAL_KEY_CENSUS_AUDITED` only if both exact source bodies verify fully and every cohort/joins conservation gate passes (even zero matching keys);
- `SOURCE_OBJECT_CHANGED` if a full original compressed source SHA/byte count differs;
- `SOURCE_GATE_NOT_PASSED` for access/schema/UTF-8/CRC/row count/decompressed digest/budget failure;
- `INSTRUMENT_FAILURE` for computation, SQL, conservation, unexpected runtime or other code failure.
A successful CI **workflow exit by itself** does not imply a passing scientific verdict: inspect the emitted JSON decision.

No semantic identity, temporal consistency, feeder coincidence, incident causal linkage, contemporaneous operator information, alternative repair actions, real decision CPU costs, physically meaningful two-path F2, greedy-versus-lookahead effect, or pregeometry/persistence law is proven by a textual-key census. The **next distinct gate** would validate temporal and operational consistency, but only on evidence-backed candidate identities with a separately registered protocol.
