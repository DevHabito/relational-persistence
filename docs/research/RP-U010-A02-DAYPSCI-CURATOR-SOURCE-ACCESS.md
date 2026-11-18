# RP-U010-A02 — Independent alternate university metadata confirmation and curator outreach

**17 November 2026 — post-A01 source-access follow-up. This is NOT a preregistered original empirical experiment, a source-file verification, or an amendment to the original A01 outcome.**

## Verified additional official institutional evidence

The original [RP-U010-A01](RP-U010-A01.md) source-discovery attempt authenticated the DAYPSCI dataset DOI via DataCite but all three attempts to retrieve RIUBU/Handle item metadata timed out. Its original archival decision **remains** `RP_U010_A01_METADATA_ONLY_SOURCE_FILES_NOT_RESOLVED`, backed by first-run immutable audit SHA256 `f8434c0e57f3ba38a3a5a19f5c317d1147df4b5babdc09d0480b732a167b3612`. No later source search should rebrand A01 as a success.

An independently accessible **University of Burgos institutional research catalog (CRIS)** also lists the dataset:

- Official university research data browse page: https://investigacion.ubu.es/datos?lang=en&personaId=35325
- DAYPSCI v1 catalog record: https://investigacion.ubu.es/documentos/6a0f3d1b88a62d224222b247
- The record identifies 2026, University of Burgos, dataset type, CC BY 4.0, four authors (Juan Vicente Martín-Fraile, Nuño Basurto Hornillos, Jesús Enrique Sierra-García, Álvaro Herrero), dataset DOI **10.71486/2DRF-1G53**, Handle **10259/11686**.
- It describes processed event CSV, PCAPNG traces, per-batch supporting documentation, Siemens S7-1200/S7-1500, and per-scan `scan_id`/`event_order`. **These are a catalog's descriptions, not inspected original experimental rows**.
- **CRITICAL:** CRIS record lists "Version: 0", whereas the dataset title is "DAYPSCI v1". Do not infer these represent two verified actual file revisions, or ignore version ambiguity in a later source request. Ask the curator whether they refer to the same archived file version.
- This CRIS catalog record provides **no authenticated batch file UUIDs, per-file sizes, publisher checksums, direct experimental downloads, or per-instrument synchronization evidence**.

Thus this post-A01 discovery corroborates that the dataset and licensing metadata exist, but does **not** change the A01 source-file gate. No data observations or fault/recovery statistics have been generated.

## Institutional contact points, confirmed from the university itself

- Juan Vicente Martín-Fraile, published email **jvmartin@ubu.es**; source https://investigacion.ubu.es/investigadores/35325/detalle?lang=en .
- Nuño Basurto Hornillos, published email **nbasurto@ubu.es**; source https://investigacion.ubu.es/investigadores/131529/detalle?lang=es .

Only these two email addresses were positively checked against university researcher profiles in this follow-up. Do not fabricate additional recipients.

## Minimal source and measurement questions to the dataset authors

1. **Reproducible access:** Is there an institutional URL listing *each specific batch* (processed CSV, PCAPNG, README) with file UUID, byte length and preferably SHA-256? If the RIUBU Handle is intermittent, is there an officially controlled alternative? How does the catalog "Version: 0" relate to the dataset title "v1"?
2. **Fault onset/removal:** Which CSV field or README note identifies experimentally triggered fault activation, and **explicit removal or reset**, with time/PLC-scan coordinate? Do independent fault batches contain post-removal observation, or only baseline versus persistent fault cases?
3. **Real independent function:** Which separate sensor/actuator/event proves actual *completed marking/part cycle* after deactivation, rather than controller intention, a `part_id` increment or fault flag?
4. **Clocks:** Are `ts_plc`, `delta_time_ms`, `scan_id`, `event_order` and PCAPNG wall-clock timestamps synchronized/calibrated? If not, what strictly order-preserving linkage is supported?
5. **Unit of analysis:** Are repeated batches from the same rig independent trials or shared setup/temporal clusters? What event identifiers distinguish truly separate injections?

No raw files, large attachments, or unpublished privileged data are requested: an official manifest and a brief technical clarification are sufficient. The same questions should be sent once, respectfully, with no implied request for research collaboration, reviewer endorsement or paper approval.

## Communication workflow

The Spanish email below is a **draft prepared for user review**, not sent by this research workflow. Do not claim contact or a response until Gmail or another delivery source confirms it. Keep source-access/contact outcomes in a separate archive from any future RP-U010 functional results.

**Subject:** Consulta técnica sobre acceso a DAYPSCI v1 y trazabilidad de los eventos

> Estimados profesores Martín-Fraile y Basurto:
>
> He estado leyendo su trabajo sobre DAYPSCI y me interesa utilizarlo en una investigación independiente sobre la recuperación funcional de sistemas tras una perturbación.
>
> He podido comprobar la referencia del conjunto de datos (DOI 10.71486/2drf-1g53), pero no he conseguido acceder al listado de archivos del repositorio RIUBU. ¿Podrían indicarme una vía oficial para obtener el inventario de los lotes experimentales, idealmente con identificadores, tamaños y sumas de verificación?
>
> También quisiera aclarar tres cuestiones antes de plantear un análisis: ¿los registros incluyen el momento de retirada de cada fallo, además de su activación? ¿Qué variable o evento permite confirmar que una pieza o un ciclo se completó correctamente después? ¿Existe sincronización comprobada entre las marcas temporales del PLC y las capturas PCAPNG, o recomiendan comparar únicamente el orden lógico de los eventos?
>
> No necesito que preparen un análisis adicional: una referencia al README o a la documentación donde se expliquen estos puntos sería suficiente.
>
> Muchas gracias por su tiempo y por compartir el conjunto de datos.
>
> Felipe Gianini Romero
> Investigador independiente

## Exact decision to resume empirical work

Do **not** open a new positive/negative functional-recovery experiment until an authentic publisher file index, precise fault-off semantics, an independently recorded functional completion condition and a valid clock/order argument are available. The next stage is evidence acquisition, not hypothesis vindication.

**A01 stays metadata-only; this follow-up adds publicly corroborated catalog/contact information, no original dataset-file access and no new empirical result.**
