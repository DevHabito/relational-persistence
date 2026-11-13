# NEU-01-G08-D03 — Direct whole-array native-value identity after exact float32-to-float64 widening

**12 November 2026. This is explicitly AFTER G08-P01's all-channel Pearson=1 and G08-D02's zero centered residual and identical aggregate counts were already seen.** This is a post-result audit of **ONE previously observed source pair**, not blind hypothesis confirmation, a new participant, new acquisition, new EEG dataset, physiological persistence, novel mathematics, or causal identification of a publisher processing step.

## Frozen one-pair source, no selection after result

BIDS root sub-02/session1/task-eyesclosed .eeg at OpenNeuro ds004148 v1.0.0, immutable original publisher Git revision 0c740d838a2c33feeec0b6e514aea323d0e65ca4. Its original verified IEEE_FLOAT_32 body has exactly 36,600,000 bytes, MD5 afc315cd4fbd76f2788a67fe31be9d8d and SHA256 **9c9f8c321482c71657047e99a1c259aaa753bb3b5fbe09e392a06b33d8d6dacd**. One previously matched EEGLAB derivative sub02_01_EC.set has exactly 73,824,136 bytes, published MD5 2ba3c01f752799634414e2142544fd9b and previously authenticated SHA256 **2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359**.

Verify immutable G08-P01 original aggregate (2,880 bytes, SHA256 **18950086a3e0220dfc83c82210a5a84da9ad28d00e224fcdc7ac969aa842025b**) and G08-D02 original aggregate (2,332 bytes, SHA256 **a0fe888346e76de66672b41aa5634d45a5798a56633f7fd551d06de5747ae0a8**) before original source I/O. Also verify prior G04/G05/G07 archives through the registered readers. Require those prior original outputs explicitly recorded passed 61/61 ordered-channel and exact 2-ms relative-time gates; do not use matching labels to search for a better numerical permutation or shift.

## Predeclared direct equality test — no gain, reference removal or lag

Read the fully authenticated original 61-channel multiplexed float32 binary in frame-major (150000 x 61) order. Convert its 9,150,000 native float32 finite values *exactly* to IEEE754 float64, with no arithmetic transform or calibration. Load only the authenticated EEGLAB .set's top-level data matrix, stored double (61 x 150000); transpose to the already-established same frame-major channel/time order. Require all values finite and strict dimensions.

For every one of the 9,150,000 positions compute:
- IEEE **numerical equality** between source-widened-float64 and derivative-float64. Publish total matching/mismatching sample counts and maximum absolute sample difference in their **native numeric values** (unverified physical scale).
- IEEE **bit-pattern equality** of the two canonical little-endian float64 encodings, treating +0/-0 as different bits even if numerically equal. Publish count matching/mismatching bit patterns, and the number of numerically equal samples that nonetheless have different sign-of-zero/IEEE bits. Any nonfinite original/double fails source eligibility instead of quietly accepting NaN semantics.
- Two independently computed **SHA256 digests of the canonical (150000,61) little-endian float64 arrays**, one from root float32 widening and the other from the actual derivative double matrix, without publishing source contents. Hash equality is a second check on stored bit-pattern identity.
- Predeclared negative controls: on the actual derivative matrix only, (i) circular +500-frame shift (1 second) and (ii) completely reversed channel order. Compare their *unshifted source* numeric equality counts, do not fit or search offsets/gains/permutations. These are instrument sensitivity checks, not an inferential hypothesis test.

The result category is:
1. EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL if all 9,150,000 canonical 64-bit patterns match and SHA256 digests agree, with no numerical mismatch.
2. NUMERIC_EQUAL_IEEE_BITS_DIFFER if all numeric sample values match but some canonical float64 bit patterns differ (for example signed zero).
3. AUTHENTICATED_NATIVE_ARRAYS_DIFFER if at least one corresponding numeric sample differs, retaining exact counts and maximum difference.
4. SOURCE_NOT_ELIGIBLE for any source checksum, array shape, finite-value, archived evidence or IO/instrument failure. Never silently select a different participant or recast a data mismatch as corruption without evidence.

Any of the first three outcomes is a completed measurement. None licenses claiming all 900 raw/derived pairs are copies, that the publication is wrong, that the exact original amplifier bytes are known, that an EEGLAB rereference was/was not applied historically, or that cognition/clinical state/time/entropy laws were discovered. Even if the arrays are identical after widening, original and derivative **file bytes are necessarily different** (BrainVision float32 and MATLAB double), and metadata labels can differ. Matching sample arrays alone also cannot establish which intermediate processing steps happened prior to file publication.

## Tests, source protection, and chronology

Before source access, test independent synthetic float32-to-float64 conversion, exact representability of finite float32 in float64, signed-zero bit discrimination, single-frame/single-channel substitutions, no-gain/no-centering behavior, fixed temporal/channel controls, strict shape/finite rejection, canonical row-major/endian byte order and source archive mutation. Use independently written scalar struct-based test oracle, not only NumPy equality for positive controls. The run may use a temporary GitHub hosted computer with bounded exact original source bytes and no raw EEG artifact uploads. Publish ONLY aggregate counts, source identities, canonical content hashes and fixed control counts. Protect first source status, errors, original job/run and SHA256. If a correction follows an unsuccessful source access, register a dated amendment before retrying, never edit G08-P01, G08-D02 or this protocol's earlier outcome.

## Literature and exact claim boundary

Wang, Yulin; Duan, Wei; Dong, Debo; Ding, Lihong; Lei, Xu (13 September 2022), Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9. Original source publisher: OpenNeuro ds004148 v1.0.0. EEGLAB Data Structures documentation https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html (MATLAB may save individual EEG structure fields at top level). Brain Products GmbH, BrainVision Core Data Format 1.0 https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/.

Dictionary: float32 widening is an exact IEEE754 representable mapping of each finite float32 sample into float64 without rescaling; numerical equality ignores the sign bit of zero; bitwise equality is equality of canonical 64-bit representation; content hash is a checksum of canonical arrays, NOT proof of acquisition provenance; same-index correspondence was established as a previous relative-grid/label test, NOT absolute time synchronized recording. No confidence interval, neural causal mechanism, physical entropy or clinical effect follows.

**At freeze:** projected residuals and source/derived aggregate count equality were ALREADY KNOWN. The direct unprojected 9,150,000-value equality result and canonical float64 digest equality have not yet been measured in G08-D03.
