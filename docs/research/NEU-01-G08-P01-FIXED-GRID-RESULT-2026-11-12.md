# NEU-01-G08-P01 — Fixed original/derivative EEG grid alignment and a zero-lag diagnostic

**12 November 2026; original workflow UTC 13 November.** Unblinded technical source-pair audit. The sources, previous G03–G07 results and retrospective mathematical findings were known. The G08 single-pair grid criteria and control were frozen BEFORE accessing source sample data at protocol-only commit **efdeb6651f3614735d50629cdaabcf7e29c22de2**.

## Source identification and repaired physical-unit metadata statement

One preselected root BIDS-labelled raw BrainVision record: sub-02, session1, eyesclosed, original binary 36,600,000 bytes, SHA256 **9c9f8c321482c71657047e99a1c259aaa753bb3b5fbe09e392a06b33d8d6dacd**. One matching EEGLAB derivative sub02_01_EC.set, 73,824,136 bytes, original G07 SHA256 **2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359**. The original BrainVision .vhdr and original BIDS channels.tsv were also independently authenticated by their earlier publisher version-fixed identities, including the BIDS TSV Git blob SHA1 **105960eb0ac14bae43bea73aa479a5c6d995c7a3**.

**Correction to G03–G07 shorthand:** The original BrainVision .vhdr channel unit slots were blank, but the original *BIDS channels.tsv declares uV for each of the 61 EEG channels*. It was therefore inaccurate to suggest that all publisher source files lacked an explicit physical unit declaration. However the presence of a unit declaration in a BIDS sidecar is not independent verification of the original amplifier calibration, numeric scale in every binary processing stage, or equivalence to the EEGLAB derivative numeric double representation.

## Metadata-only gate results before comparing amplitudes

The source BrainVision ordered Ch1..Ch61 labels, upstream BIDS channels.tsv ordered names, and EEGLAB derivative chanlocs labels **matched in exactly the same order for all 61/61 channels**, using only trimmed casefold canonicalization predeclared in the protocol. SHA256 of each of those three ordered canonical label lists was the identical string **0eb9d03a6f1c62af87f95e8de05d9a39632529208c4e8c1be945f809f77d9b99**. No channel names or per-channel observations were published.

The EEGLAB 150,000 time coordinates precisely equaled the fixed 2-ms relative grid: **times[0]=0 milliseconds, times[-1]=299,998 milliseconds, max absolute discrepancy=0 milliseconds**, with strictly increasing values. The original MATLAB xmin=0 seconds and xmax=299.998 seconds, rate 500 Hz, one trial, array shape 61 x 150,000. The original BrainVision multiplexed float32 file has 61 x 150,000 in corresponding original order. Thus the **relative sample grid is eligible**, but the original source file does NOT independently authenticate a shared absolute recording start timestamp.

## Predeclared descriptive signal comparison

The registered comparison uses only one pair with exact source-authenticated bodies and passes all label/time/shape gates. For every frame, it subtracts the **61-channel arithmetic mean** separately from both native original and derivative arrays. For each corresponding channel, it computes signed Pearson correlation over all 150,000 time positions **at zero lag**, without changing sample rate, interpolating or searching for time shifts. A fixed negative control circularly shifted the derivative by **500 frames = 1 second** before computing the same correlations.

| Diagnostic over 61 channels | Exact first original G08 output |
|---|---:|
| Root/derivative projected zero-lag correlation min | 1.0 (reported double precision) |
| Zero-lag median | 1.0 |
| Zero-lag max | 1.0 |
| Count with |Pearson| greater than 0.9, zero lag | 61/61 |
| Fixed one-second control median | 0.4736345115680359 |
| One-second control min | 0.16977296266245406 |
| One-second control max | 0.9565856873679349 |
| Count with |Pearson| greater than 0.9, one-second control | 1/61 |

A computed correlation of **1.0** for all channels demonstrates an extraordinarily strong same-index linear association **after this fixed cross-channel projection**. It does NOT demonstrate every sample is bit-identical, that the absolute recording start time is externally verified, that the EEG physical units are independently calibrated, or that the exact original processing algorithm is uniquely identified. Pearson can equal 1 for signals related by a nonzero gain and offset, and numerical finite precision can report 1 for almost perfectly proportional signals. A related processing pipeline may produce such a relationship.

The fixed one-second negative control greatly reduces the median correspondence but can retain strong slow components; its one high-correlation channel prevents treating it as a formal biological null. No p-value, clinical outcome, graph persistence test, LZ complexity, physical thermodynamic entropy or neural rigidity was assessed.

## Chronology and source reproducibility

The first original G08 workflow [#43335456284](https://github.com/DevHabito/relational-persistence/actions/runs/43335456284) completed successfully at implementation head **d1b34b32ed9083c406053fc7636e1e435d92cd77**, after **11 synthetic and adversarial tests passed BEFORE source access**. The full repository source-commit regression [#43335456211](https://github.com/DevHabito/relational-persistence/actions/runs/43335456211) passed **947 tests on Python 3.11 and 947 on 3.12**, per actual job logs.

The original source JSON was recovered from the **first and only** successful G08 GitHub Actions artifact **13996733831** and SHA-256 verified separately. It is **2,880 bytes**, exact SHA-256 **18950086a3e0220dfc83c82210a5a84da9ad28d00e224fcdc7ac969aa842025b**, matching the job's original sha256sum, and is archived unchanged at docs/results/NEU-01-G08-P01-first-run/audit.json with a provenance index. Neither original 36.6 MB BIDS binary nor the 73.8 MB derivative .set is committed; no actual EEG sample values or individual per-channel correlations are published.

## Prior literature and next honest question

- EEGLAB consortium, EEGLAB Data Structures guide, https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html — documents top-level field save mode, chanlocs and data/time metadata.
- Brain Products, BrainVision Core Data Format 1.0, https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/ — binary layout, per-channel scale and header sampling interval.
- Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (13 September 2022), A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states, Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9. Published acquisition and processing description; individual operation causality is still unresolved.

**Next explicitly post-result numerical check:** preregister and evaluate the **global-gain residual** under the same fixed per-time mean projection, and compare fixed unshifted residual to prechosen temporal/channel controls. A second test should evaluate whether the original native IEEE float32 integer/equality signatures change in the derived double array, but must not claim isolated ICA/quantization causality. This is essential before using the observed Pearson 1.0 as an argument for a particular source-to-derivative transform.

**G08 status:** FIXED_GRID_DESCRIPTIVE_COMPARISON_COMPLETE; zero-lag Pearson 1.0 on 61 channels after common-mode projection, exactly one source/derivative candidate. The source-to-derivative processing stage is NOT proven.
