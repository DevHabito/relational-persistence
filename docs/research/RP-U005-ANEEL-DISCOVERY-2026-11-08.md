# RP-U005-D02 — An official Brazilian source worth investigating, with unresolved boundaries

**Research lead:** Felipe Gianini Romero  
**Source investigation:** 8 November 2026  
**Repository baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`  
**Classification:** retrospective publisher-catalog/schema discovery and fixture-only gate preparation. Neither a new outcome study nor a fresh blinded test.

## Why I followed this source

The RP-U004 graph experiment made a useful distinction between surviving connectivity and a specific declared network function. It did not demonstrate that a real repair dispatcher would benefit from a two-step policy: the test was synthetic, and even its extra truth-table lookup cost was modeled rather than measured in operational units.

The earlier Google Borg source audit authenticated a machine-event shard, but did not certify observed link-repair actions or their resource costs. I therefore looked for an official source whose **own record-keeping** already distinguishes failures, restoration, and how much time crews spend responding, rather than mapping those categories onto unrelated machine events.

A catalog search led to the Brazilian energy regulator ANEEL. These source descriptions are primary publisher evidence. Their existence is not proof that the real files are complete, that a field is filled, or that a proposed multi-table join works.

## What I located and checked

**ANEEL — Emergency occurrences in distribution networks.** The [catalog](https://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao) advertises annual original records from 2017 onward, with updates at monthly cadence. Its 2026 dictionary *text extraction* lists occurrence start/end, company-assigned occurrence code, feeder and substation identifiers, how the incident was learned, and preparation, travel and execution durations in minutes. The [regulator's quality-of-service explanation](https://www.gov.br/aneel/pt-br/assuntos/distribuicao/qualidade-do-fornecimento-de-energia-eletrica) separately defines the three emergency-response phases in terms of real field operations; this is a stronger operational starting point than the synthetic U004 lookup cost.

**ANEEL — Electricity interruptions.** The [catalog](https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao) advertises interruption start/end, affected consumer counts and distributor/feeder/substation references. Its 2026 dictionary text contains `CodOcorrencia`, which *may* refer to an emergency occurrence. Whether that code has the same scope and meaning as `CodOcorrenciaEmergencial` in the other table remains unverified.

**ANEEL — BDGD network geodatabase.** The [catalog](https://dadosabertos.aneel.gov.br/dataset/base-de-dados-geografica-da-distribuidora-bdgd) describes an annual geographic model of distributor assets, distributed per company as geodatabases. It is explicitly a simplified representation of the distribution network. Its identity and network geometry must be checked against the event time before any topological interpretation; there is no warrant to assume an annual map records the live state of every switch or line during a fault.

These ANEEL data products exclude cooperatives/permissionárias, so even a complete audit would not represent every distribution-area operator in Brazil. The portal declares ODbL licensing.

## Public inventory snapshot, 8 November 2026

The official 2026 resource pages list the following independent objects. Sizes are the site's approximate metadata, not bytes I measured:

| 2026 source | Resource ID | Advertised size | Status |
|---|---|---:|---|
| Emergency-occurrence ZIP | `040c840a-b9fa-4c63-bd3c-f1a99640366b` | 167.9 MiB | Catalog only; source bytes absent |
| Interruption ZIP | `33a21bd6-4893-42fc-bc05-888154f7511e` | 193.5 MiB | Catalog only; source bytes absent |
| Emergency-occurrence Parquet | `d0669ad0-24a2-4f34-85cc-1b08e82d7ad2` | 185.5 MiB | Catalog only; source bytes absent |
| Interruption Parquet | `cf722d0b-aa04-4681-bcd9-8a737e857182` | 195.2 MiB | Catalog only; source bytes absent |

The occurrence resources were recorded on the portal as updated 10 September 2026, and interruption resources 4 September 2026, even though the collection-level pages carry later dates. Neither is a proven complete calendar-year 2026 population.

The site's optional `Hash` field for each ZIP is a 32-character hexadecimal string. It has **not** been recomputed or verified here, and its algorithm must not be assumed. Direct access from this execution container to the PDF URL failed at DNS resolution; no original ANEEL rows or PDF bytes were downloaded. None of the listed resources was independently SHA-256 authenticated.

## A genuine document-level ambiguity

The official publisher provides dictionaries for **pre-2026** and **2026 onward** in separate links. I compared the extracted field names.

- Older occurrence dictionary: `NumOcorrencia`, `DscNumInterrupcao`, `MdaPreparo`, `MdaDeslocamento`, `MdaExecucao`.
- Newer occurrence dictionary text: `CodOcorrenciaEmergencial`, `NumTempoPreparacao`, `NumTempoDeslocamento`, `NumTempoExecucao`, plus feeder and substation codes.
- Older interruption dictionary: `NumOrdemInterrupcao` and `DscAlimentadorSubestacao`.
- Newer interruption dictionary text: `CodOcorrencia`, `CodAlimentador`, `CodSubestacao` and `CodInterrupcao`.

The textual extraction of the nominal 2026 occurrence PDF reported version 1.1 and 28 July 2026. However, the screenshot tool displayed a 2022 version-1.0 document **even when asked to render the nominal 2026 resource**, matching the separately linked old dictionary. A similar issue appeared when checking the interruption PDF. I have not resolved whether this comes from caching, an asset routing bug or another cause. I will not label these dictionaries as *original-byte authenticated* without a separate download, SHA-256 and render inspection. This matters: a supposed schema update might otherwise be treated as a proven mapping and silently create invalid joins.

## Other original sources screened on the same date

I did not select the ANEEL catalog merely because it seemed convenient. I also inspected these **publisher-documented** alternatives; their data rows were not downloaded and none is a proven U004 policy dataset.

| Primary source | What is actually published | Why it is not a direct U004 edge-repair evaluation |
|---|---|---|
| [ONS — interruption of load](https://dados.ons.org.br/dataset/interrupcao_carga) | Official Brazilian system-operator dataset for forced transmission-network outages and distribution-only interruptions exceeding **100 MW for 10 minutes** | Selection threshold excludes smaller events; the catalog does not establish chosen link-repair alternatives or dispatcher compute costs |
| [E-REDES — scheduled distribution maintenance](https://e-redes.opendatasoft.com/explore/dataset/network-scheduling-work/information/) | Planned interventions by geographic area and period, supplied by the Portuguese distribution operator | **Plans and notices**, not certified realized action sequences and their counterfactual outcomes |
| [E-REDES — number of remote work orders](https://e-redes.huwise.com/explore/dataset/15-ordens-de-servico/api/) | Monthly work-order counts by service type and locality, history after 2020 | Aggregates are not time-ordered decisions for individual network-edge repairs |
| [US ORNL EAGLE-I outage data](https://smc-datachallenge.ornl.gov/eagle/) | Historical county-level outage counts at 15-minute intervals, 2014–2022 | Genuine regional restoration patterns may be studied, but customer counts do not reveal physical link-action choices or their costs |
| [California Office of Emergency Services outage incidents](https://publish.data.ca.gov/dataset/power-outage-incidents) | A map-derived operational incident feed, refreshed around 15-minute intervals | Publisher explicitly says it contains only **most recent incidents, not historical data**; current availability cannot be mistaken for archived trajectories |
| [PowerBench](https://doi.org/10.5281/zenodo.15400564) (Jacob, Uddin, Olojede, Coskunuzer and Zhang, 14 May 2025) | OpenDSS-generated line-outage and state-estimation benchmark using standard feeders and graph exports | Explicitly **simulated**, not recorded natural grid repair actions. Potential software baseline, not independent field evidence |

These distinctions do not establish that the underlying publisher source lacks unpublished data. They concern only the public material actually inspected.

## What could be asked once the source passes a separate gate?

A limited observational question might ask whether specific **pre-existing** incident/context variables are associated with later recorded response or outage duration. Before attempting this, I would have to prove that the variables were available at the time a dispatcher made a decision. For example, **execution time and final interruption time are outcomes**, not valid features in a forecast made earlier; this is a common and potentially fatal source of leakage.

Even the apparent identity of two occurrence codes requires original-row checks: distributor-assigned IDs can collide across companies or calendar periods, and a single emergency occurrence might have several affected interruption records. A blind one-to-one inner join would discard precisely the cases most likely to make a model look cleaner than the source. The planned gate reports unmatched, duplicated and one-to-many matches without deleting them.

A feeder ID is not an observed set of restored graph edges. A snapshot from BDGD may be a legitimate structural covariate if the correct time-specific source can be established, but it cannot be presented as the observed action/state history. A real comparison of greedy and lookahead repairs requires actual intervention decisions, alternatives, timing, assignment assumptions and a declared independent functional outcome. I have **not** located such complete evidence in these catalogs.

## Previously published research matters

**Alex B. Tronchoni, Carlos O. Pretto, Mauro A. da Rosa and Flávio A. Becon Lemos (April 2010)**, [“Descoberta de conhecimento em base de dados de eventos de desligamentos de empresas de distribuição”](https://doi.org/10.1590/S0103-17592010000200007), *SBA Controle & Automação* 21(2), studied knowledge discovery and Bayesian-network diagnosis for distribution-utility forced outages. They discuss incomplete, subjective and conflicting outage-cause reports and a 570,000-event case. Their methods and much of the data-quality problem long predate this project's work. This source was read on 8 November 2026; it is not an endorsement of RP-U004.

**ANEEL, [Quality of Electricity Supply](https://www.gov.br/aneel/pt-br/assuntos/distribuicao/qualidade-do-fornecimento-de-energia-eletrica)** provides the already established regulatory definitions of preparation/travel/execution time, monthly means and energy-interruption measures. I should not present these definitions as an original formulation.

The new gate does not reproduce either source's empirical findings. It registers what would have to be verified before using the public source for a different question.

## Engineering controls implemented with no real rows

The new `experiments/rp_u005_aneel_schema_preflight.py` is explicitly a **fixture-only** source-control module:

- It distinguishes the 2026 candidate field names from old unverified aliases.
- It preserves leading-zero occurrence IDs and distributor/year boundaries.
- It exposes one-to-many and unmatched candidate links instead of silently choosing one.
- It rejects missing historical receipt time, equal-time or future inputs, known outcome fields and publication-only fields as predecision features.
- It rejects negative/naive timestamp intervals and keeps its scientific guards active under `python -O`.
- It always reports original rows read as zero and real policy-comparison eligibility as unverified.

Its tests in `tests/test_rp_u005_aneel_schema_preflight.py` construct invented examples only; **the fixture CNPJ values are not evidence of real Brazilian distributors**. Software CI can validate the consistency of the gates. It cannot validate the proposed crosswalk or measure a real-world effect.

## Outcome and next study boundary

**Source-review status:** `CANDIDATE_FOR_SEPARATE_SOURCE_ONLY_AUDIT` for observed emergency-response and outage-duration data.

**Strictly excluded conclusion:** **NO_DIRECT_REAL_U004_POLICY_VALIDATION**. No published original rows have been checked, no two-table match rate measured, no contemporaneous dynamic graph reconstructed, no actual edge-repair actions observed and no counterfactual advantage estimated.

A next independent source study must specify a limited original publisher file, timestamp range, dataset revision, full-download/decompression/row budgets, content identity requirements, versioned schema dictionaries and a frozen *source-eligibility* stopping decision. Only after that study passes should a **separate** preregistered observational outcome analysis be considered. Reusing already inspected synthetic U004 outcomes or altering earlier negative evidence cannot substitute for that process.

**CI evidence and exact PR head:** to be inserted after GitHub Actions completes. Until then, do not infer tests passed merely because scripts exist.
