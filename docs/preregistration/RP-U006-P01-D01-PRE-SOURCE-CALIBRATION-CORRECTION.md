# RP-U006-P01-D01 — Pre-source calibration interval-count correction

**17 November 2026; before any RP-U006 service trial, calibration timestamp, or original source execution.**

The original protocol-only commit `b99e505d99d25bed57e2308029947407b2668777` specifies twelve calibration jobs, the median of consecutive completion intervals "for jobs 4..12," and nine valid intervals. That is a **pure arithmetic inconsistency**: jobs 4–12 are nine completion timestamps, so they yield only **eight** consecutive differences.

To preserve the already frozen requirement for **nine** intervals and twelve calibration jobs, the operationally authoritative index span is **completion timestamps for jobs 3–12 inclusive** (ten timestamps, nine differences). Retain all positive timestamps and calculate the median of these nine differences; do not cherry-pick or filter intervals. Every other trial, predictor, constant, threshold, role, dataset, and statistical interpretation remains unchanged.

This transparent typo correction **precedes implementation and any service observation** and does not replace or modify the original protocol. The original protocol and this addendum must remain available together. If there is a source or calibration gate failure, record the original failure rather than silently change the span again.

**At this addendum:** source observations = 0; calibration values = unknown; no result.
