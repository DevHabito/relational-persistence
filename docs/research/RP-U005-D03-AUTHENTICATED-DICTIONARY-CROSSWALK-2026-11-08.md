# RP-U005-D03 — After-result reading of four authenticated ANEEL dictionaries

**Date:** 8 November 2026  
**Classification:** descriptive schema reading **after** first PDF byte acquisition and outcome. Not a preregistration, not row-level validation and not an operational forecast.  
**Verified original PDF identities:** [RP-U005-D03 first original report](../results/RP-U005-D03.md), first GitHub Actions source run [#42505852818](https://github.com/DevHabito/relational-persistence/actions/runs/42505852818).

The first run authenticated four official PDF source objects and fixed whole-file hashes. After preserving the complete first JSON, I inspected all 3/4 pages of those four original PDFs, in addition to visually inspecting their first pages. The notes below are statements about what the **dictionaries say**, not about any actual record's values or completeness.

## The superficially matching 2026 schemas are not interchangeable

| Concept | Emergency occurrences 2026 dictionary, v1.1 (28 July) | Interruption 2026 dictionary, v1.0 (21 July) | Consequence |
|---|---|---|---|
| Distributor | `NumCnpjDistribuidora`, character length **14** | `NumCNPJDistribuidora`, character length **14** | Different field capitalization. A planned canonical company key requires a precise, audited conversion; preserve 14-digit leading zeroes |
| Emergency occurrence | `CodOcorrenciaEmergencial`, character length **10** (PDF p. 2) | `CodOcorrencia`, character length **10** (PDF p. 3), explicitly described as linking to the emergency-occurrence dataset | This is evidence of *intended semantic reference*, **not** proof of matching actual codes, cardinality or uniqueness |
| Feeder | `CodAlimentador`, character length **10** | `CodAlimentador`, character length **10** | Neither code establishes time-specific energized edge topology |
| Substation | `CodSubestacao`, character length **10** | `CodSubestacao`, character length **30** | **Documented field-width discrepancy**; do not truncate 30-character records to force a match |
| Consumer set | `CodConjUnidConsumidora`, character length **10** | `CodConjUnidadeConsumidora`, character length **10** | Abbreviation differs; do not assume values/crosswalk agree before a source-only row audit |
| Competence year | `NumAnoCompetencia`, character length **4** | `AnoCompetencia`, character length **4** | Candidate matching year fields have different names, and a temporal join needs an explicit policy |
| Competence month | `NumMesCompetencia`, character length **2** | `MesCompetencia`, character length **2** | Calendar/window alignment is not an innocuous syntax change |
| Start/end | `DthIniOcorrencia`, `DthFimOcorrencia` | `DatInicioInterrupcao`, `DatFimInterrupcao` | Separate event/interval concepts. Equality of timestamps is **not** guaranteed |
| Repair/response phases | `NumTempoPreparacao`, `NumTempoDeslocamento`, `NumTempoExecucao` — **minutes**, numerical `10,2` | **Not present** as these phase fields | A computed sum must not be called decision-algorithm CPU cost |
| Interruption identity | `DscInterrupcaoAssociada`: a **100-character description of whether there was an associated interruption** | `CodInterrupcao`: **30**-character field; the extracted **type cell appears blank** in this PDF | The occurrence field is **not** a directly documented `CodInterrupcao` primary key. Do not infer an ID join from it |
| Affected consumers | No directly corresponding `QtdConsumidoresAfetados` field in this occurrence dictionary | `QtdConsumidoresAfetados`, numeric **10** | Post-event quantity may be useful as an outcome, but not automatically known at decision time |

The files cited are the independently SHA-256 checked originals. The table maps their documented field descriptions and names; it does **not** authenticate even a single original ANEEL row.

## Historical version contrast

The pre-2026 occurrence PDF (v1.0, 11 October 2022) describes `NumOcorrencia` as a **30-character** occurrence order identifier, `DscNumInterrupcao` as an **80-character** description, `MdaPreparo`, `MdaDeslocamento`, and `MdaExecucao` as numeric **20,5** phase measures. The pre-2026 interruption PDF (also v1.0, 11 October 2022) instead describes `NumOrdemInterrupcao` as a **255-character** description of an interruption order, and `DscAlimentadorSubestacao` as a **255-character** description. The 2026 dictionaries introduce different, shorter identifier fields and change the precision of the response-phase measures. There is **no source evidence here** that a simple old-to-new `rename()` preserves semantics.

## Practical consequences before any observed repair investigation

1. The new dictionaries' explicit textual cross-reference justifies testing a **candidate** pair: 14-character distributor ID plus source `CodOcorrenciaEmergencial` / interruption `CodOcorrencia`, with clearly declared year/month and appropriate event-time matching.
2. That pairing must be tested on original input records for missingness, duplicates, one-to-many interruptions, inconsistent company IDs and dates, and conflicts in feeder/substation metadata. All unmatched and ambiguous records remain in reported denominators.
3. In a direct forecast, neither recorded execution duration, interruption end time nor the publisher's dataset-generation date is a valid pre-decision feature without separate evidence of causal-time release.
4. BDGD feeder/substation codes do not prove a live switching history. Distribution systems often operate radially, so installed alternative ties and simultaneously energized two-route F2 are different objectives. Physical transfer of the RP-U004 synthetic graph predicate requires an entirely new justified operational definition.
5. The next gate is **original source-file acquisition and quality**, not model training, a novel pregeometry law, or an empirical lookahead benefit.

There is no quantitative observation, policy effect, source-row pass or new Lean theorem in this after-result dictionary reading.
