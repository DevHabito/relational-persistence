# Formal verification status

- **2026-10-23:** Initial Lean 4 proof candidates authored. Local Lean 4 toolchain was not present and network access was unavailable in the authoring environment. Machine verification must be established from the GitHub Actions run, not inferred from source inspection.
- **Scope:** Exact finite rational claims and normalized-index algebra only. Physical hypotheses and measured data remain outside kernel verification.
- **Next gate:** Check the full `Lean 4 proof checking` workflow logs and record the exact commit, run ID, and success/failure outcome. A failing workflow blocks any claim of formal verification.
