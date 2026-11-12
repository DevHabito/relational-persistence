# NEU-01-G04-P01-R02 — Post-stop checksum transcription correction

**12 November 2026.** This addendum was authored **after** the first actual G04 source attempt; it does **not** rewrite the standalone G04 preregistration at commit 6449070c5b95e1d4bbddd2243549593d4ed85f46, the original G03 audit, D01, or any observed source data.

## What actually failed

The first source-capable workflow at commit d8df3af9fc7aa6917de51e8360bd27c10736f1d4 did not run any real EEG because the hosted Python had no pytest. That attempted run is retained as #43327245478; the pre-source gate failed.

After an isolated pytest install was added at 0216077c6e8832217e742cc91e09094bf03c73c0, the next workflow #43327371558 passed 11 synthetic/adversarial checks and began authenticated real source acquisition. It then **stopped with SOURCE_SHA256_MISMATCH**, **before completing all six** originals. Do not call this source attempt a successful replay. The program may have decoded the first eligible recording in memory, but did not publish a G04 aggregate scientific result.

The failure was investigated by a **read-only literal comparison** between each SHA-256 constant in the new G04 code and the earlier immutable G03 audit.json. Exactly one manually copied literal differed:

- sub-02 eyesopen original archived, pre-existing G03 SHA-256: 0e27c11253da07a3f6e6a4eff4716327ac38fcf061e71fc16a50101cabe979ca
- erroneous new G04 source-code/protocol literal: 0e27c11253da07a3f6e6a4eff4716327ac38fcf061e71fc16a501cabe979ca

The code omitted the two hexadecimal characters **01** immediately preceding cabe. The correct hash was already known, archived and independently G03 authenticated in November 2026. The fix is not an inferred hash, new post-hoc candidate source or relaxed validation: it restores literal equality to the archived original identity. No other identity, source cohort, scientific endpoint, interpretation or decision threshold changes.

## Mandatory correction and prevention

In the next code-only change, replace **only** that G04 EEG SHA-256 constant with the exact original G03 value and add a pre-source gate verifying that **all six G04 expected SHA-256 literals equal the immutable G03 source identities**, not just that source files match the newly transcribed constants. Keep the original MD5 and SHA-256 checks; do not weaken source authentication or accept a mismatch. Then rerun **the same** synthetic controls **before** starting another hosted original-source read.

The original standalone protocol's incorrect row is historical evidence; this addendum supersedes that row for sub-02 eyesopen **only**. This is a transparent instrument/metadata correction made after a partial source attempt, not a new blinded human EEG finding. Do not suppress either failed run in the final report. Freeze this addendum before any further source read.
