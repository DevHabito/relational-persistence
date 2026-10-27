"""Original RP-U002-A01 irreversible source-result evidence and scope pins.

Original GitHub run already occurred. These tests never replace or re-run
its frozen result, and no ecological rows or future model outcomes are used.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ORIGINAL = Path(__file__).resolve().parents[1] / "docs/results/RP-U002-A01-first-run"
EXPECTED_SHA = "67b6f1df8bac52aa48c507f31e5b93486fb23bcffcbd849d42c72b14a4fec3a9"
PREREG = "fa7f9d0133370b0e8a769d0b7d95759e402a2dc8"
CODE = "e0929d6f554dffadabb19d932409e8ab84055b0f"
RUN = "40499618845"


def load_original():
    raw = (ORIGINAL / "audit.json").read_bytes()
    report = json.loads(raw)
    manifest = json.loads((ORIGINAL / "archive-index.json").read_text("utf-8"))
    return raw, report, manifest


def test_original_byte_sha_git_preregistered_identity_and_no_reclassification():
    raw, report, manifest = load_original()
    assert sha256(raw).hexdigest() == EXPECTED_SHA
    assert manifest["first_report_sha256"] == EXPECTED_SHA
    assert report["protocol"] == manifest["protocol"] == "RP-U002-A01"
    assert report["preregistration_commit"] == manifest["frozen_protocol_commit"] == PREREG
    assert report["original_code_commit"] == manifest["original_code_commit"] == CODE
    assert report["first_run_id"] == manifest["original_run_id"] == RUN
    assert report["verdict"] == manifest["first_original_verdict"] == (
        "FINITE_TURNOVER_REPAIR_CONTRAST_VERIFIED"
    )
    assert report["errors"] == []
    assert sorted(p.name for p in ORIGINAL.iterdir()) == [
        "archive-index.json", "audit.json"
    ]


def test_all_original_F1_and_F2_at_every_fixed_time_are_preserved():
    _, report, _ = load_original()
    expected = {
        "repair": {
            "A": ([4,4,4,4,4,4], [4,0,0,3,4,4], 20, 11),
            "B": ([4,3,3,3,4,4], [0,0,0,0,0,0], 17, 0),
        },
        "no_repair": {
            "A": ([4,4,4,4,4,4], [4,0,0,0,0,0], 20, 0),
            "B": ([4,3,3,3,3,3], [0,0,0,0,0,0], 15, 0),
        },
    }
    for policy, graphs in expected.items():
        for graph, (f1, f2, uptime1, uptime2) in graphs.items():
            actual = report["result"][policy][graph]
            assert actual["per_time_F1_count_out_of_four"] == f1
            assert actual["per_time_F2_count_out_of_four"] == f2
            assert actual["uptime_F1_exact_count_out_of_20"] == uptime1
            assert actual["uptime_F2_exact_count_out_of_20"] == uptime2
            assert sum(f1[1:]) == uptime1
            assert sum(f2[1:]) == uptime2


def test_first_original_has_all_fixed_32_histories_not_selected_for_success():
    _, report, _ = load_original()
    n = 0
    for policy in ("repair", "no_repair"):
        for graph in ("A", "B"):
            cases = report["result"][policy][graph]["original_single_failure_scenarios"]
            assert [case["loss"] for case in cases] == [1,2,3,4]
            for case in cases:
                assert [step["time"] for step in case["snapshots"]] == list(range(6))
                assert all("F1" in step and "F2" in step for step in case["snapshots"])
                n += 1
    assert n == 16  # 2 policies × 2 graphs × 4 original single-node failures.


def test_original_B_center_six_nodes_but_function_lost_then_restored():
    _, report, _ = load_original()
    cases = report["result"]["repair"]["B"]["original_single_failure_scenarios"]
    center = next(x for x in cases if x["loss"] == 2)["snapshots"]
    assert len(center) == 6
    assert center[0]["present_component_count"] == 6
    assert center[1]["present_component_count"] == 5
    assert center[2]["present_component_count"] == 6
    assert center[3]["present_component_count"] == 6
    assert center[4]["present_component_count"] == 6
    assert center[0]["F1"] is True
    assert center[2]["F1"] is False
    assert center[3]["F1"] is False
    assert center[4]["F1"] is True
    assert center[1]["old_component_lost"] is True
    assert center[2]["new_component_present"] is True


def test_negative_controls_cannot_be_suppressed_or_called_instant_repair():
    _, report, _ = load_original()
    assert report["negative_controls"] == {
        "B_F2_never_established_by_repair": True,
        "B_bottleneck_F1_not_restored_by_new_node_alone": True,
        "no_repair_A_F1_equal_to_repair_A_F1": True,
        "repair_and_no_repair_B_F1_gain_only_two_out_of_20": True,
        "repair_restores_A_F2_after_delay_not_instantly": True,
    }


def test_no_forest_biology_stochastic_sampling_or_new_physics_claimed():
    _, report, manifest = load_original()
    assert report["all_real_domain_observations"] == 0
    assert manifest["real_observations_used"] == 0
    assert report["measurements_of_recovery_or_biological_growth"] is False
    assert report["forecast_or_physical_scalar_estimated"] is False
    assert report["new_universal_law_claimed"] is False
    assert manifest["new_mathematical_or_physical_law_claimed"] is False
    assert manifest["original_U001_and_external_HPC_negatives_untouched"] is True


def test_original_hash_mutation_control_is_negative():
    raw, _, _ = load_original()
    assert sha256(raw + b"\n").hexdigest() != EXPECTED_SHA
