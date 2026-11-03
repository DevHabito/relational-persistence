"""Post-result integrity and independent replay of the frozen RP-U004 archive.

These tests were added AFTER the first original run. Pinning its actual
outcome is an archive regression, not a preregistered success criterion.
The independent replay never imports the experiment being audited.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from experiments.rp_u004_independent_replay import verify, stream_hash

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-U004-P01-first-run"
FIRST_REPORT = ARCHIVE / "audit.json"
MANIFEST = ARCHIVE / "archive-index.json"


def test_first_original_archive_bytes_are_immutable_and_nonphysical():
    raw = FIRST_REPORT.read_bytes()
    metadata = json.loads(MANIFEST.read_text(encoding="utf-8"))
    original = json.loads(raw)

    assert sha256(raw).hexdigest() == metadata["original_audit_sha256"]
    assert metadata["protocol"] == original["protocol"] == "RP-U004-P01"
    assert metadata["protocol_freeze_commit"] == "186d6fc5d8cc6451fca63abb5f6ef4f2029a3d7b"
    assert metadata["first_code_commit"] == "d6f927cabdaa5f15f04cb1f0c929025879b601bf"
    assert metadata["first_run_id"] == "41721533933"
    assert metadata["first_verdict"] == original["verdict"]
    assert original["physical_data_rows"] == metadata["physical_data_rows"] == 0
    assert original["new_lean_theorem_claimed"] is False
    assert original["new_physical_law_claimed"] is False
    assert stream_hash(original["cases"]) == metadata["case_trace_sha256"]


def test_independent_finite_replay_matches_every_original_case():
    original = json.loads(FIRST_REPORT.read_bytes())
    metadata = json.loads(MANIFEST.read_text(encoding="utf-8"))
    outcome = verify(original, metadata)

    assert outcome["accepted_source_graphs"] == 18140
    assert outcome["matched_pairs"] == 285
    assert outcome["scenario_count"] == 2850
    assert outcome["initial_F2_source_graphs"] == 142
    assert outcome["truth_table_entries"] == 25040
    assert outcome["F2"]["LOOKAHEAD2_F2"] == 3386
    assert outcome["F2"]["GREEDY_F2"] == 3286
    assert outcome["F1"]["LOOKAHEAD2_F1"] == 16052
    assert outcome["F1"]["GREEDY_F1"] == 16046
    assert outcome["comparisons"]["LOOKAHEAD2_F2_vs_GREEDY_F2_F2_win"] == 66
    assert outcome["comparisons"]["LOOKAHEAD2_F2_vs_GREEDY_F2_F2_tie"] == 2784
    assert outcome["comparisons"]["LOOKAHEAD2_F1_vs_GREEDY_F1_F1_win"] == 6
    assert outcome["comparisons"]["LOOKAHEAD2_F1_vs_GREEDY_F1_F1_tie"] == 2844
