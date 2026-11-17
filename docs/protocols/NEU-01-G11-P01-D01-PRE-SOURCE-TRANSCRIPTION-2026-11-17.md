# NEU-01-G11-P01-D01 — Pre-source correction of a publisher header MD5 transcription

**17 November 2026.** This is an error log and a source-identity transcription correction, **before any G11 EEG waveform body was downloaded or decoded**. The original G11 preregistration at commit `3c86a3b89ffacfc27c5136a5d1a696a56404733d` is deliberately preserved, including the incorrect text.

## What the first attempt exposed

The first implementation commit `62e8ebf7ece8f69a7f4ad5a76ced78121af268b3` represented 24 frozen publisher rows as ordinary Python tuples instead of the declared `Source` dataclass instances. The first dedicated GitHub Actions workflow, https://github.com/DevHabito/relational-persistence/actions/runs/44062472794, failed on **six pre-source synthetic tests** (15 passed, 6 failed). Because the workflow runs these tests *before* the data-acquisition step, **that step was skipped: no G11 original human EEG samples were examined**. This is a software implementation failure, not a biological result.

Review of the 24 manifest rows then exposed a separate **manual transcription error** in the protocol table. The declared `sub-18` session3 eyesclosed BrainVision `.vhdr` MD5 was `13913715b5e1fe671c0974a297609b` (**30 hexadecimal digits**, not a valid MD5). This cannot authenticate any published file. The same pre-registered subject, session, eyesclosed task, root EEG MD5 and source revision are unchanged. The immutable original OpenNeuro ds004148 v1.0.0 Git-annex pointer was fetched again from:

https://api.github.com/repos/OpenNeuroDatasets/ds004148/contents/sub-18/ses-session3/eeg/sub-18_ses-session3_task-eyesclosed_eeg.vhdr?ref=0c740d838a2c33feeec0b6e514aea323d0e65ca4

It reads `MD5E-s1122--13913715b5f5e1fe671c0974a297609b.vhdr`: **32 hexadecimal digits**. The protocol omitted exactly the adjacent `f5` substring. This is verified publisher **pointer metadata**, not an original downloaded header-body checksum at this stage.

## Repair, scope and order

The next commit changes only the implementation's 24 manifest records into typed `Source` values, corrects this one header MD5 to the exact upstream pointer identifier, and adds a pre-source synthetic regression assertion that each frozen MD5 has 32 hexadecimal digits and the corrected `sub-18` entry matches the publisher.

The original protocol and failed first workflow are not overwritten; this addendum is the authoritative narrow amendment for **one publisher header MD5**. No participant or session is replaced, no fixed alpha-band parameter, spectral baseline, 20,000-permutation null, threshold, data-exclusion rule or outcome definition is changed. The original G11 source-execution stage remains unperformed. If the next synthetic run fails, preserve its failures as a separate attempt and do not interpret them as EEG outcomes.

**Status at this addendum:** *FAIL-COMPUTATION* at pre-source gate; specific errors identified; one source pointer typo corrected using pinned public Git metadata only. No G11 signal or outcome was read to motivate any of these changes.
