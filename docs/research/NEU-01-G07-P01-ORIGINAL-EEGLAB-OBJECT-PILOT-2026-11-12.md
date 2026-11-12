# NEU-01-G07-P01 — First full original EEGLAB derivative authentication, with a retained metadata parsing obstacle

**12 November 2026. Unblinded original-source technical pilot, not new EEG discovery.** The fixed source was selected and its published Git-annex MD5/length were known before source access; the G07 protocol was independently committed beforehand at 6a0e0bd96fd5c8f4d4823c7c02fec0128c8c9d6e.

## What was tested and what actually happened

G06 found that the source dataset contains BIDS-labelled raw and a separately labelled preprocessed EEGLAB .set collection; the exact original derivative bytes and their processing history had not been examined. To avoid uncontrolled data fishing, G07 fixed precisely ONE candidate object: sub02_01_EC.set for sub-02, session1, eyesclosed. The original publisher Git-annex pointer said the file should contain 73,824,136 bytes, MD5 2ba3c01f752799634414e2142544fd9b.

The first actual G07 original-source workflow #43332821093 at implementation commit a3e8698dba9c4441552253a1b4d82d83a1e91866 passed **8 dedicated synthetic/adversarial tests** before downloading source data. It downloaded the complete original derivative temporarily on the GitHub Actions runner, verified **exactly 73,824,136 bytes and the exact published MD5**, and independently measured the following previously unknown derivative SHA-256:

**2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359**

The binary signature identified a **MATLAB v5 container**. The predeclared SciPy decoder then looked specifically for a top-level MATLAB variable named EEG, expecting an EEGLAB EEG structure. **No such variable was returned by that named-variable read.** It therefore recorded:

DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED
metadata_parse_status = EEGLAB_STRUCT_MISSING

This is a **parsing/layout obstacle, not a failed source file**. The verified original derivative body exists and matches the publisher's Git-annex MD5. The simple first-pass expectation about variable naming was wrong or insufficient. We must **not** infer that this file contains no EEG, is corrupted, or that its actual signal layout has been identified.

The source downloader removed the temporary 73.8 MB derivative file at the end of the run. No derivative EEG binary, signal array, actual amplitude, channel names or raw processing-history string was printed or uploaded. The safe aggregate-only original first-run JSON is preserved exactly at docs/results/NEU-01-G07-P01-first-run/audit.json.

## Boundary of interpretation

| Claim | Result |
|---|---|
| This one original sub02_01_EC.set file has exact publisher byte size and MD5 | YES |
| Its previously unrecorded source SHA-256 was obtained | YES |
| It carries MATLAB v5 header signature | YES |
| The first parser found a top-level EEG struct | NO; EEG_STRUCT_MISSING |
| File is scientifically invalid or contains no EEG | NOT ESTABLISHED |
| Its samples align channel/time-wise with BIDS .eeg | UNVERIFIED |
| All other five derivatives authenticated | NO |
| Processing history, ICA or quantization origin identified | NO |
| Biological rigidity or EEG complexity inferred | NO |

## Chronology, literature, and next gate

The exact original first-run aggregate artifact #13995293239 was independently downloaded, extracted and SHA-256 verified. It is **1,133 bytes**, SHA-256 **60a328cd0cbd69f41da4ffaa8b71921b96f1c0d7fd81751b63b7f126cd1481c3**, matching the original workflow log. The archive index records the true first outcome and the prior protocol-only freeze, not a retrospective success interpretation.

Original first pilot: https://github.com/DevHabito/relational-persistence/actions/runs/43332821093
Public publisher frozen repository: https://github.com/OpenNeuroDatasets/ds004148/tree/0c740d838a2c33feeec0b6e514aea323d0e65ca4
Source paper: Yulin Wang, Wei Duan, Debo Dong, Lihong Ding, Xu Lei, 13 September 2022, Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9.

Next research task, explicitly post-result: **separately register a metadata-only MATLAB variable census** that lists only top-level variable names, dimensions and classes (not original contents), independently authenticated against the now-known SHA-256. Do not silently modify this first-run decoder or overwrite the original record. After structural identification, an additional frozen experiment may test channel/time/sample matching with the original root BrainVision file. Until then, causal pipeline attribution remains blocked.

**G07-P01 status: DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED.** This mixed integrity-success/metadata-parser-limit result is a scientific audit outcome and must be retained verbatim.
