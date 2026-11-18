# RP-U010-A01 — DAYPSCI source-access, chronology and functional-endpoint feasibility

**Registered 17 November 2026, before obtaining or inspecting any DAYPSCI original CSV, PCAPNG or batch README content in this research.** This is a strict **source-access and capability audit**, not an outcome trial and not an original recovery result.

## Motivation and external source identity

Previous original studies remain intact: RP-U007 did not confirm incremental informational value from a live backlog; RP-U008 described two of four already-known single-vantage network outages with sampled HTTP lag; RP-U009's original physical compressor study was invalid and the separate decimal-LPS reanalysis failed a preregistered temporal-coverage gate. A fourth artificial queue would not address these limitations.

The external DAYPSCI study is Juan Vicente Martín-Fraile, Nuño Basurto Hornillos, Jesús Enrique Sierra-García and Álvaro Herrero (2026), *DAYPSCI: Event-based dataset for anomaly detection through fault injection in PLC-controlled industrial cyber-physical systems*, **Data in Brief 68:113146**, DOI **10.1016/j.dib.2026.113146**. The authors' **dataset** is **DAYPSCI v1**, Universidad de Burgos RIUBU, DOI **10.71486/2drf-1g53**, official Handle **10259/11686** (https://hdl.handle.net/10259/11686). Its described PLC-based industrial part-marking testbed uses Siemens S7-1200 and S7-1500, with controlled fault injection targeting sensors, solenoid valves and combinations. Each experimental batch is described as a processed CSV, PROFINET packet capture (PCAPNG), and a textual README. The publication lists `ts_plc`, `delta_time_ms`, `scan_id`, `event_order`, `event_id`, `part_id`, `Gemma`, `Anomaly`, `Fault`, fault-channel descriptors and sensor transitions.

**Already known from paper before this protocol:** fault labels may be a mixture of externally configured experiment metadata and runtime-derived Gemma-state annotations. A label indicating an injected fault does **not automatically certify** an independently timestamped start/end or separate physical outcome. `part_id` identifies a part/sequence, not an independently validated successful completion. PCAP timestamps may not be synchronized with PLC source times: mere presence of both modalities is NOT evidence of independent clock calibration. The paper describes experiments under separate baseline/fault configurations but does NOT establish that each fault run contains a deactivation interval and post-fault full functional recovery. No such interval or recovery claim may be assumed.

## Scope of A01

A01 asks only whether **publicly retrievable official publisher metadata** and a **bounded downloadable source manifest** can be authenticated sufficiently to design a new, independently registered A02 or P01 analysis. This is a source feasibility check; **there is no predictive model, outcome variable, effect size, hypothesis significance threshold or physical persistence claim in A01**.

Retrieve metadata, with no credentials, from:
- `https://api.datacite.org/dois/10.71486/2drf-1g53` (record linked to exact dataset DOI);
- `https://hdl.handle.net/10259/11686` and/or `https://riubu.ubu.es/handle/10259/11686` (official handle landing);
- `https://riubu.ubu.es/server/api/core/handles/10259/11686` (possible DSpace REST handle resolution);
- only explicitly returned official repository JSON links such as the item/bundle/bitstream manifests. Do **not** fabricate a bitstream UUID or infer a file identity from an example filename in the article.

A bounded source discovery process must report every attempt's HTTP status, final URL, content type, exact bytes read (capped at 2 MiB per resource), SHA256 of the response body, response parser decision, safely selected title and number of returned item/file listings when applicable. A redirect to an unrecognized host or HTTP authentication requirements must be reported as a **blocker**, not silently followed. Only official `doi.org`, `api.datacite.org`, `hdl.handle.net`, `riubu.ubu.es` and any university dataset-storage host explicitly linked from an authenticated official manifest may be accepted; unexpected hosts must not be fetched.

Do **not** download any original experimental PCAPNG, CSV, all-batch ZIP, HTML attachment or large dataset at A01. Link file **names, declared sizes, and provider-described checksums** only if actually present in authenticated metadata; record unknown as unknown. A sample author-chosen path such as `pn_sensor_T1_batch02.csv` in a paper is not proof of a downloadable file. Do not invent a list of accessible batches, count of injected interventions, or total sensor observations.

## Predeclared capability gates (fail closed)

A candidate A02 original-source protocol is **possible** only if an authenticated original provider manifest exposes:
1. an actual reachable/downloadable versioned dataset file or batch index, with concrete file descriptors and enough source identity (stable URL/UUID and byte counts or publisher checksum) to independently hash the later download;
2. the actual files can later be inspected for `ts_plc`, `scan_id`, `event_order`, `part_id`, and explicit injected-fault timing metadata; the *paper's field descriptions alone are insufficient*;
3. there is a defensible **functional restoration endpoint** such as a recorded completed part/cycle and explicit fault deactivation, and a time ordering between external injection and endpoint. Mere `Fault:1 -> Fault:0` labels or a nominal baseline batch alone do not establish a complete perturbation/recovery within the same physical system.
4. If merging PROFINET PCAP timestamps with PLC timestamps, a recorded/verified clock alignment or defensible clock-independent ordinal comparison must be supplied.

A01 can only establish **gate 1 metadata discoverability**. Even if gate 1 passes, gates 2–4 remain **UNVERIFIED** until later original-source work. A01 must NEVER mark `RECOVERY_CONFIRMED`, `PERSISTENCE_SUPPORTED`, or any scientific outcome positive.

Report statuses:
- `RP_U010_A01_OFFICIAL_MANIFEST_AVAILABLE_NOT_YET_DATA_VERIFIED` if at least one official provider manifest exposes grounded file/batch index identity with stable resolved source paths and real metadata;
- `RP_U010_A01_METADATA_ONLY_SOURCE_FILES_NOT_RESOLVED` if DOI/landing metadata can be read but a concrete original provider file/batch source index cannot be resolved;
- `RP_U010_A01_SOURCE_ACCESS_BLOCKED` if all authoritative source discovery attempts fail or require auth;
- `RP_U010_A01_INVALID_DISCOVERY_EVIDENCE` if forged/untrusted redirects, contradictory dataset identifiers or malformed source manifest make the result unreliable.

**The final result is access-only**, not a positive/negative test of functional recovery. Any later A02 must be separately registered based on actual resolved files and require strict source hashes and an explicit original-data timestamp/endpoint diagnostic before predeclaring an effect-size or hypothesis test. No fabricated file names, source sizes, checksums, or repaired processes.

## Engineering and provenance

A GitHub Actions hosted runner may reach domains unavailable to the assistant's own browser. Execute pre-source **synthetic tests** of URL/host refusal, manifest identity and no-data-download behavior; use only 2 MiB body cap, max 12 metadata requests, finite timeouts and **no large source files**. Preserve failure attempts and hashes in a compact JSON `docs/results/RP-U010-A01-first-source/audit.json`, via non-overwriting Actions artifact on the very first run. Preserve all previous P01/U009 original artifacts and do not merge to `main`. Source code and documentation in English, no result fitting or invented theorem, no Lean proof claimed.

## Literature (verified before registration)

- Martín-Fraile, J.V., Basurto Hornillos, N., Sierra-García, J.E., Herrero, Á. (2026), *DAYPSCI*, Data in Brief 68:113146, https://doi.org/10.1016/j.dib.2026.113146.
- Original data: Universidad de Burgos RIUBU, DAYPSCI v1, https://doi.org/10.71486/2drf-1g53, https://hdl.handle.net/10259/11686.
- The preceding RP-U007, RP-U008, RP-U009 evidence and invalid-source findings are retained in their respective archives.

**Status at registration:** DOI and handle confirmed from original publication; repository bitstream file list and physical recovery endpoint unverified; no DAYPSCI original data yet downloaded or analyzed.
