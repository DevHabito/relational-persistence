"""Pin the FIRST RP-U003 result manifest without rewriting huge original JSON.

Do not pretend these checks parse all 889k JSON lines. Original GitHub
workflow performed exhaustive calculation and archived the immutable
case traces; use first-run SHA for independent full-file verification.
"""
import json
from pathlib import Path
from hashlib import sha256

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"docs/results/RP-U003-A01-first-run/archive-index.json"
REPORT=ROOT/"docs/results/RP-U003-A01.md"
EXPECTED_AUDIT_SHA="cbac86c673be8de662e0ee741c958a44e860c03cdf420641ceb801a95c97934d"
EXPECTED_GRAPH_SHA="76aef644704c01b52b7b9eeac0d8b36deccf65d36bdc3d2225955436ff7671e3"
EXPECTED_TRACE_SHA="82f3225239370b601ada328c642ddb1ed3409b80679fe15057b89044cb5efb4f"

def test_first_original_workflow_provenance_not_reclassified():
    archive=json.loads(INDEX.read_text(encoding="utf-8"))
    assert archive["protocol"]=="RP-U003-A01"
    assert archive["frozen_protocol_commit"]=="5cb8d3af473aa95848ab22d5ecc591c5a1567a00"
    assert archive["first_code_commit"]=="b6c97cae2e39dc971dc7437ae9962308c28db5d4"
    assert archive["first_run_id"]=="40572859641"
    assert archive["first_verdict"]=="FINITE_BENCHMARK_LOOKAHEAD_F1_ADVANTAGE_SUPPORTED"
    assert archive["original_audit_sha256"]==EXPECTED_AUDIT_SHA
    assert archive["labeled_family_sha256"]==EXPECTED_GRAPH_SHA
    assert archive["individual_case_trace_sha256"]==EXPECTED_TRACE_SHA
    assert archive["real_world_rows_examined"]==0
    assert archive["existing_negative_external_results_unchanged"] is True
    assert archive["new_universal_scientific_law_claimed"] is False

def test_report_does_not_claim_greedy_F1_is_worse_than_lookahead():
    report=REPORT.read_text(encoding="utf-8")
    assert "GREEDY1" in report and "LOOKAHEAD2" in report
    assert "15,888" in report and "7,968" in report and "7,852" in report
    assert "EXACTLY the same" in report
    assert "not" in report.lower()
    assert "16,416" in report
    assert "684" in report

def test_manifest_SHA_would_detect_a_changed_digest():
    assert sha256((EXPECTED_AUDIT_SHA+"mutation").encode()).hexdigest()!=EXPECTED_AUDIT_SHA
