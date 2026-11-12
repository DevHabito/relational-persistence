# NEU-01-G07-D02 — Explicitly post-result MATLAB top-level variable inventory

**12 November 2026. This follow-up is UNBLINDED and RETROSPECTIVE.** G07-P01 already authenticated one derivative EEGLAB .set body by MD5 and observed source SHA256, classified MATLAB v5, and failed to find a top-level variable named EEG. That negative parser result is preserved in its immutable first-run archive and must not be rewritten. It motivates a narrow new technical question: **which standard EEGLAB metadata variable names, shapes and MATLAB classes are actually present at top level?**

This is a source format debugging investigation. It is NOT a new EEG experiment, confirmation of an unobserved clinical finding, new theory or independent participant sample. The original G07 outcome was already seen before this protocol was registered.

## Exactly one known source, no substitution

OpenNeuro ds004148 v1.0.0, frozen publisher Git revision 0c740d838a2c33feeec0b6e514aea323d0e65ca4. Original S3: derivatives/preprocessed data/preprocessed_data/sub02_01_EC.set. Published source size 73,824,136 bytes; Git-annex MD5 2ba3c01f752799634414e2142544fd9b. Previously authenticated G07 SHA256 **2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359**. Previously archived first-run G07 aggregate JSON immutable at SHA256 60a328cd0cbd69f41da4ffaa8b71921b96f1c0d7fd81751b63b7f126cd1481c3 (1,133 bytes). Verify the original G07 archive BEFORE accessing the source. No other .set or raw BIDS file is eligible.

## Fixed metadata-only source census

First run independent synthetic and adversarial tests. Then download the original .set to an ephemeral GitHub Actions runner, bounded at the exact published byte length, validating full original MD5 AND previously known SHA256. **Do not publish or load numerical EEG amplitude matrices.**

Use SciPy whosmat only to enumerate top-level MATLAB variable names, classes and dimensions without loading data arrays. Publish only fields from this frozen, public-EEGLAB-safe allowlist: EEG, data, nbchan, pnts, trials, srate, ref, history, chanlocs, event, urevent, xmin, xmax, times, icaweights, icasphere, icawinv, icaact, setname, comments, epoch. Also report total top-level variable count and count of other unnamed variables, never their names or content. The primary diagnostic decision TOPLEVEL_EEGLAB_FIELD_LAYOUT_RESOLVED requires at least the data field and numeric scalar metadata nbchan, pnts, and srate to be present with consistent nonnegative finite scalars. Otherwise report TOPLEVEL_LAYOUT_STILL_UNRESOLVED with the exact missing allowed field names. Do not guess defaults.

Separately use scipy.io.loadmat with variable_names restricted to nbchan, pnts, trials, srate, ref and history (never data) and report only validated nonnegative scalar counts/rate, a short sanitized reference label, and presence, character length and SHA256 of any readable history text. **Never publish actual EEG.history content, patient/subject names, paths, channel labels or sample values.** Metadata dimensions may suggest how to build an alignment experiment but do not prove source-to-derivative sample correspondence.

A success establishes MATLAB field inventory for ONE derivative only. It does not establish history accuracy, channel identity, sampling time alignment, raw/processed causal effect, all six derivative validity, quantization mechanism, Lempel-Ziv complexity, neural rigidity or a biomarker.

## Negative controls and chronology

The synthetic test oracle must independently construct MATLAB v5 fixtures with top-level fields, a nested EEG struct negative fixture, missing data, malformed fields, inappropriate history types and tampered source checksum. The original first G07 status remains DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED, even if this new separate census identifies a different storage layout. No code change to the old original analyzer is permitted and no old outcome is replaced. Freeze this protocol alone before writing the new census code or source workflow. Archive original first result even if field layout is unsupported, with workflow ID, exact bytes SHA256 and negative cases.

Prior source: Wang, Y., Duan, W., Dong, D., Ding, L., Lei, X. (13 September 2022), Scientific Data 9:566, DOI https://doi.org/10.1038/s41597-022-01607-9. OpenNeuroDatasets/ds004148 pinned public Git revision listed above. The format and data are not novel inventions of this project.

Definitions: top-level MAT field means a variable visible to whosmat without loading its numeric data; scalar metadata means small, finite stored numerical descriptors; first original G07 run is the immutable prior negative parsing observation; file authentication is not signal alignment. **All conclusions remain about file structure only.**
