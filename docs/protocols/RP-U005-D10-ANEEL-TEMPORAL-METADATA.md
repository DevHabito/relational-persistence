# RP-U005-D10 — Date-interval and feeder metadata consistency of unique ANEEL literal-key pairs

**Registered:** 8 November 2026. **Parent:** D09 reviewed head `0b862f108a2ad24ccde3d51ecb4710beafb23e62`.  
**Chronology:** This protocol commits *alone*, before D10 implementation and **before inspecting any original D10 occurrence/interruption time or feeder/substation cross-source pairs**. Previous D06-D09 source counts and original schema field names are already known. This is an informed **retrospective source-data consistency audit**, not a prospective physical intervention, blind prediction or new physics test.

## The narrow question

Among the already counted **one-occurrence-row / one-interruption-row** matches on exactly the same four literal fields (14-digit distributor CNPJ, year `2026`, unpadded month `1`–`12`, unchanged full occurrence code), how many pairs have (a) two individually parseable and non-reversed time intervals that overlap as printed, (b) disjoint valid intervals, or (c) unavailable/invalid temporal data? For the same unambiguous one-to-one pairs, what fraction of *exact nonempty feeder and substation string codes* agree or disagree? This is a **syntactic interval/metadata check**, not proof that either CSV record is an identical physical outage, an energized network edge or an action taken by any operator.

The two source ZIPs were already authenticated and their D09 candidate-key multiplicities known before registration:
- source occurrences `occ_2026`: ZIP 176,074,116 original bytes, SHA-256 `7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c`; decoded CSV 2,236,732,733 bytes, SHA-256 `736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567`; 6,789,484 source rows.
- source interruptions `int_2026`: ZIP 202,900,063 bytes, SHA-256 `87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d`; decoded CSV 2,328,209,339 bytes, SHA-256 `4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce`; 6,078,331 source rows.

The **exact original ZIP hashes must match before any row read**. Complete decoded SHA, size, original counts, 2026 header, strict UTF-8, full ZIP CRC and EOF must then match on both sources, else STOP. Never silently substitute a revised resource, an alternative annual partition, Parquet, mirror or adjusted record set.

## Fixed populations and denominator safeguards

D09 registered two nested key variants:
- **S**: only original code lengths 1–10; D09 observed **2,716,202 one-to-one matched distinct keys**.
- **F**: original complete code, including codes longer than ten; D09 observed **3,307,396 one-to-one matched distinct keys**. The remaining **591,194** one-to-one groups in F have long codes. D09 also observed **2,968,556** total S matching distinct keys and **3,609,614** F matching distinct keys, with one-to-many/many-to-many groups.

This D10's **primary comparison population is F's one-to-one group**. All four groups of D09 matched keys (one-to-one, one-to-many, many-to-one and many-to-many) and all unmatched keys **must remain in the accounting report**. The ambiguous groups are **excluded only from pairwise comparisons**, not deleted from any D09 denominator. In particular, no Cartesian explosion of one-to-many or many-to-many records is permitted.

Report all one-to-one pair counts **for both S and F**, and explicitly the separate F-only long-code partition, regardless of relative consistency. Both S and F use the same exact unmodified key syntax as D09 (including ASCII CNPJ width, original month spelling, literal code/case/zeroes). Reject/mark invalid candidate keys exactly as D09. A separate optional research question about duplicates is forbidden here: no selecting a 'best' interruption among repeated source keys.

## Frozen exact source fields

Occurrence 2026: `DthIniOcorrencia` and `DthFimOcorrencia`, `CodAlimentador`, `CodSubestacao`; interruption 2026: `DatInicioInterrupcao` and `DatFimInterrupcao`, `CodAlimentador`, `CodSubestacao`. Both original 2026 CSV header lists and the differences between their dated first-party dictionaries were inspected before this study. Other columns must not enter the pairwise outcome.

Use the original literal feeder and substation strings. No trimming, casefolding, code-width truncation, parent feeder inference, company crosswalk, topology reconstruction or replacement by missing values. **Empty on either side => UNKNOWN**; exact nonempty equality => EQUAL; two nonempty differing literal strings => DIFFERENT. Different feeder/substation labels might describe valid different levels or different observation times; `DIFFERENT` means only a metadata string disagreement.

## Frozen date/time parser and interval rule

Interpret only these exact **naïve civil datetime syntaxes**, with no implicit timezone or daylight-saving conversion:
1. `YYYY-MM-DD HH:MM:SS[.ffffff]`, or the same with `T` separator, with **one to six fractional-second digits** where present.
2. `DD/MM/YYYY HH:MM:SS[.ffffff]` with the same fractional-second limit.

Seconds are required. Dates without a time, other separators, ISO `Z`/timezone offsets, locale month names, unrecognized fractional precision, leading/trailing whitespace or nonexistent civil dates => `UNSUPPORTED_OR_INVALID`, **not** source falsification. Empty original date strings => `MISSING`. A date pair is `REVERSED` if both timestamps parse but `end < start` for that record. No imputation of unknown dates or offsets. Where both source intervals are complete and not reversed, define **closed-interval overlap**: `max(start_occ, start_int) <= min(end_occ, end_int)`. Equality at a boundary counts as `TOUCHING` and is separately reported as a subset of overlaps. Otherwise `DISJOINT`. This is an arithmetic fact about printed timestamps; it is **not a causal correspondence guarantee**.

For each one-to-one matched pair in each S/F cohort report mutually exclusive `OVERLAP`, `DISJOINT`, `UNKNOWN_TIME` counts summing to the exact one-to-one denominator. Report `TOUCHING` among overlaps, and whether interruption start precedes occurrence start, or interruption end follows occurrence end (descriptive subset counters, no physical causality). For `UNKNOWN_TIME`, report **nonexclusive** reasons per occurrence/interruption: `MISSING`, `UNSUPPORTED_OR_INVALID`, `REVERSED`; these reasons must never be added as if disjoint.

For each one-to-one cohort, report feeder `EQUAL/DIFFERENT/UNKNOWN` and substation `EQUAL/DIFFERENT/UNKNOWN`, with each three-way sum equal to one-to-one matches. Report joint `both_codes_equal`, which can only be <= min(feeder-equal, substation-equal); do **not** call it verified network identity. All counters are aggregate integers; no individual case, date, CNPJ, feeder or incident code may appear in public outputs.

## Implementation, verification and stop rules

Use a temporary SQLite database containing private per-key original start/end/feeder/substation strings, at most 6 GiB main SQLite file with bounded 32 MiB cache, batched upserts <=20,000 rows, and no in-memory per-record identifier dictionary. Upon seeing a repeated key, increment multiplicity and **erase retained representative metadata** so ambiguous groups never enter one-to-one comparisons. Source ZIPs, CSV data, source identifiers and SQLite files exist **only inside ephemeral runner storage**. No original data rows, filenames with user IDs, CNPJs, codes or example pairs in GitHub logs, repo, or Actions artifacts. Report aggregated integer outcome tables and original source SHA/CRC only.

Full source reread from the two exact first-party D06 URLs on Ubuntu Python 3.11, max 240 MiB each compressed, 5 GiB uncompressed each, 35-minute job limit, no credentials/mirrors or local machine. Before any D10 original-data request run synthetic tests for: original/S/F cohort uniqueness and long-code differences, strict timestamp syntax (including invalid calendar dates), reversed/missing intervals, touching boundaries, disjoint intervals, feeder/substation unknown/conflicts, repeated-key erasure, lossless denominator conservation, wrong original ZIP hash stop, and execution with `python -O`.

Cross-check the full local group census against **D09 first-run numeric reference** for both S/F matched keys and one-to-one/one-to-many/many-to-many cardinalities. If any reference or conservation identity fails, classify as `INSTRUMENT_FAILURE` (not a good result). Stop if either source body or parsed original stream differs. If matching identity and reference checks succeed but all timestamps are unsupported, still report `SOURCE_PAIR_METADATA_CENSUS_COMPLETE` with `UNKNOWN_TIME` and explicitly **zero temporal coverage** rather than inventing a useful overlap test.

Frozen outcomes:
- `SOURCE_PAIR_METADATA_CENSUS_COMPLETE`: exact source ZIP + decoded SHA/rows, D09 source/match group reference and every pairwise temporal/feeder/substation counter conservation pass.
- `SOURCE_OBJECT_CHANGED`: any compressed ZIP SHA/byte count mismatch.
- `SOURCE_GATE_NOT_PASSED`: source metadata, original parser, ZIP CRC, UTF-8, row count or decoded SHA fails.
- `INSTRUMENT_FAILURE`: code, SQL, RAM/disk bound, unexpected exception or conservation failure.

A successful Actions exit alone is not a positive scientific result; inspect the first JSON verdict, retain immutable first source JSON and independently verify its SHA, and document positives **and** negatives, without retroactively rewriting earlier first-run archives.

## Excluded scientific claims

No validated 1:1 real-world entity identity, true exact clock synchronization, live feeder topology, switching chronology, measured computer/crew overhead, actual alternative edge repair, physically valid two-route F2, counterfactual greedy/lookahead gain, population-wide national coverage or new physical/pregeometric persistence law. If data have timestamp/metadata contradictions, these can arise from differing definitions, collection windows, coding conventions or errors; **none** should be silently repaired in this experiment.

**External provenance:** ANEEL source collections (2026) [emergency occurrences](https://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao) and [power interruptions](https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao). Existing record-linkage methodology: Fellegi and Sunter (1969), DOI 10.1080/01621459.1969.10501049; Christen (2012), DOI 10.1007/978-3-642-31164-2. These methods precede this deterministic source-only census.
