# RP-U005-D02 — ANEEL multi-source feasibility and causal-time preflight

**Research date:** 8 November 2026  
**Project baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8` (3 November 2026)  
**Classification:** retrospective public documentation review and prospective *engineering gate design*, **not** a preregistration of fresh outcome data. Public descriptions and the idea of joining these three sources were already known when this document was committed.

## Question and boundary

Can three official Brazilian electricity-distribution datasets plausibly support a *future* audit of real emergency-response and power-restoration duration, without silently treating a maintenance response as a chosen physical edge-repair intervention or a static feeder diagram as its dynamic pre-event topology?

The three sources are:

1. [ANEEL: emergency occurrences in distribution networks](https://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao), [2026 dictionary, publisher resource](https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/00ddb056-c4fd-4fad-8cce-0807c527c8ee/download/dm-ocorrencias-emergenciais-nas-redes-de-distribuicao.pdf).
2. [ANEEL: distribution electricity interruptions](https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao), [2026 dictionary, publisher resource](https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/6e5611de-948d-4473-b309-520d7523b762/download/dm-interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao.pdf).
3. [ANEEL: Geographic Distributor Database (BDGD)](https://dadosabertos.aneel.gov.br/dataset/base-de-dados-geografica-da-distribuidora-bdgd), an annual, simplified geodatabase of network assets, not a minute-resolution historical switching log.

All are published by ANEEL under the portal's stated Open Data Commons ODbL terms. Published coverage excludes service areas belonging to authorized cooperatives (`permissionárias`). The source pages describe annual interruption/occurrence files from 2017 onward with monthly updates and 2026 schema-specific dictionaries; the underlying *event records* have **not** been downloaded, counted, or verified in this audit.

## Official schema observations, not observed data rows

The publicly extracted **2026** occurrence dictionary identifies:
- `NumCnpjDistribuidora` (publisher identifier), `CodOcorrenciaEmergencial` (distributor-defined occurrence identifier);
- `CodAlimentador`, `CodSubestacao` and `CodConjUnidConsumidora` (geographic/equipment grouping identifiers);
- `DthIniOcorrencia`, `DthFimOcorrencia`, `DscFormaConhecimento`, `DscInterrupcaoAssociada`;
- `NumTempoPreparacao`, `NumTempoDeslocamento`, `NumTempoExecucao` in minutes;
- publication generation date and cause classifications.

The publicly extracted **2026** interruption dictionary identifies:
- `NumCNPJDistribuidora`, `CodOcorrencia` (distributor-defined occurrence identifier), `CodInterrupcao`;
- `CodAlimentador`, `CodSubestacao`, `CodConjUnidadeConsumidora`;
- `DatInicioInterrupcao`, `DatFimInterrupcao`, `QtdConsumidoresAfetados`, `DscTipoElementoInterrompido`;
- cause classifications and publication generation date.

**Critical caution:** the site also publishes separate **pre-2026** data dictionaries. The old occurrence dictionary uses `NumOcorrencia`, `MdaPreparo`, `MdaDeslocamento`, `MdaExecucao` and `DscNumInterrupcao`, while the old interruption dictionary uses `NumOrdemInterrupcao` and free-text `DscAlimentadorSubestacao`. Version-specific names and types cannot be substituted by a silent rename. These are not independently verified semantic equivalences.

**Independent-document check remains open:** when the official 2026 occurrence PDF was viewed through the available text parser and screenshot renderer, the parser showed `v1.1, 28/07/2026`, whereas the screenshot for that same nominal resource displayed `v1.0, 11-10-2022`, matching the separately linked older dictionary. The direct source-download attempt in the local container failed at DNS resolution. It is **unknown** whether this reflects client-side caching, resource routing, a viewer defect, or something else; it is not proof that the publisher delivered incorrect bytes. **Do not promote either parsed schema to byte-verified status until a fresh direct download, SHA-256 and page-by-page PDF rendering resolve the conflict.**

The regulator's [quality-of-service explanation](https://www.gov.br/aneel/pt-br/assuntos/distribuicao/qualidade-do-fornecimento-de-energia-eletrica) confirms the definitions of preparation (incident awareness to team authorization), travel (authorization to arrival) and execution (arrival to service restoration). These are elapsed durations, **not** the compute time of deciding whether to use greedy or lookahead. The monthly [emergency-response indicator dataset](https://dadosabertos.aneel.gov.br/dataset/atendimento-ocorrencias-emergenciais) publishes group-level means, which must not be confused with per-occurrence source rows.

## Pinned public resource inventory (metadata observed, bytes not acquired)

The year **2026** is chosen for a possible **schema-aligned, partial-year feasibility test only**, not as a complete calendar year or an unseen forecast holdout. Exact resource IDs:

| Publisher catalog resource | Resource ID | Listed size and state | What can be asserted now |
|---|---|---|---|
| Emergency occurrence 2026 ZIP | `040c840a-b9fa-4c63-bd3c-f1a99640366b` | ~167.9 MiB, updated 10 September 2026 | Resource-page inventory only; reported hash `ebbd637cc75d5b7e22a09e382344eab9` not independently verified |
| Power interruption 2026 ZIP | `33a21bd6-4893-42fc-bc05-888154f7511e` | ~193.5 MiB, updated 4 September 2026 | Resource-page inventory only; reported hash `f3f77657d08043cdcfd4afa38717a576` not independently verified |
| Emergency occurrence 2026 Parquet | `d0669ad0-24a2-4f34-85cc-1b08e82d7ad2` | ~185.5 MiB, updated 10 September 2026 | Listed alternative representation; no complete file SHA verified |
| Power interruption 2026 Parquet | `cf722d0b-aa04-4681-bcd9-8a737e857182` | ~195.2 MiB, updated 4 September 2026 | Listed alternative representation; no complete file SHA verified |

Resources named ZIP were shown on their portal pages with `text/csv` MIME types; do not infer actual on-disk encoding from the catalog label. The complete files are hundreds of MiB, so a download or first-prefix stream **must not** be called complete-source verification. A separate source-only protocol and feasible environment are needed before any full-object audit.

The 2025 full-year catalog resources are also large (approximately 335.7 MiB emergency occurrences ZIP and 257.9 MiB interruption ZIP), and their older dictionaries introduce a different, unvalidated join interpretation. A larger number of rows does not resolve that semantic discontinuity.

## Decision gates for a future row-level, source-only protocol

### Gate A — Publisher-byte and schema identity

Before reading event outcomes, preregister exact source URLs/IDs, their content-identity checks, bounded download/decompression budgets and archive location. Acquire dictionary PDFs directly, compute and record whole-object SHA-256 and render both versions; stop on unresolved conflict. Inspect ZIP/parquet magic bytes, headers and full-object hashes; catalog `Hash` may not be assumed to be SHA-256. Preserve initial published results, including rejected sources.

### Gate B — Key scope, time and linkage

Keep identifiers as strings, preserving leading zeros. Normalize the publisher/company field only with an explicit type rule and recorded transform. Test a **candidate** join on (distributor identifier, occurrence identifier, declared time scope); do not assume `CodOcorrenciaEmergencial` and `CodOcorrencia` are interchangeable solely because their descriptions resemble one another. Check uniqueness on both sides, one-to-many cases, incompatible time intervals, missing IDs, and feeder/substation inconsistencies. Report unmatched and multiply matched records without deleting them to improve apparent coverage. A join failure is a result; do not tune the key using held-out outcomes.

### Gate C — Feature availability and leakage

An incident's *end time*, service restoration time, actual execution duration, affected customers assessed at the end, and the dataset's publication generation timestamp are not pre-decision features absent a separate historical-availability argument. Event time is not necessarily operator reception time. In particular, the objective `NumTempoExecucao` must never be inserted into a forecast that purports to precede service restoration. Put feature availability at a defined origin **before** inspecting future outcomes. Reject future-information leakage.

### Gate D — Dynamic topology and interventions

`CodAlimentador` and `CodSubestacao` permit preliminary grouping but do not certify a graph's actual edge availability at incident time. The annual BDGD describes a simplified view of network assets, not a complete temporally versioned switching sequence. Without documented actual repairs, feasible alternatives and controlled action assignment, there is **no direct empirical greedy-vs-lookahead causal contrast** and no observable RP-U004 F2 restoration target.

### Gate E — Independent outcome and intended question

A possible later, *distinct* question is how **recorded emergency-response phases** relate to **recorded outage duration** in the same scope and year, using an independent, source-validated join and explicit missingness/censoring policy. It would be observational and potentially tautological if the phase durations mechanically sum to the target: test that dependency first. Any prospective predictor must use only information independently shown to exist at the declared decision cutoff, and compare against established classical baselines.

Even if Gates A–C pass, no relational-persistence law or real causal repair-policy superiority follows. Gate D requires evidence **not yet located** in these public schemas.

## Outcomes, without promoting unknowns

- **Observed public metadata:** sources, publishers, resource catalog IDs, approximate sizes and schema-dictionary descriptions were inspected on 8 November 2026.
- **Source-byte status:** `NOT_DOWNLOADED_OR_SHA256_VERIFIED`; the official PDF text/screenshot conflict is unresolved.
- **Join status:** `UNTESTED_ON_ORIGINAL_ROWS`.
- **Direct U004 repair-policy eligibility:** `NOT_ESTABLISHED`, because real chosen link actions, alternative choices, causal assignment, operational computation costs and contemporaneous F2 graph states are not certified.
- **Alternative empirical duration pilot:** `POTENTIAL_SUBJECT_TO_SOURCE_GATES`; **not** an approved experimental dataset yet.
- **No new numerical or physical effect:** `NO_OUTCOME_STUDY_PERFORMED`.

Source-quality rejection and negative controls are scientifically legitimate. Do not fill missing operational states with static topology assumptions, and do not revive the already-seen synthetic U004 family as a blind real-world holdout.

## Provenance and future work

This document is a transparent source-discovery result **after** the original U004 computation and real-data blocked Borg study. No new ANEEL data rows were read, no repair-effect forecast was evaluated and no mathematical theorem is claimed. New engineering checks may validate only explicit properties of **synthetic fixtures** representing allowed and forbidden joins; passing them cannot validate the real dataset. A true outcome-independent external-source gate must be separately frozen *before* opening the designated ANEEL source files.
