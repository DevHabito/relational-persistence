"""Immutable FIRST original RP-U003 exhaustive equal-budget audit pin.

Original report was frozen automatically before this post-result review.
All negative controls and full case outcomes remain inside original Git.
This file only checks original immutable evidence, not retuning a model.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIRST = ROOT / "docs/results/RP-U003-A01-first-run"
REPORT_SHA = "cbac86c673be8de662e0ee741c958a44e860c03cdf420641ceb801a95c97934d"
CASE_SHA = "82f3225239370b601ada328c642ddb1ed3409b80679fe15057b89044cb5efb4f"
FAMILY_SHA = "76aef644704c01b52b7b9eeac0d8b36deccf65d36bdc3d2225955436ff7671e3"
PREREG = "5cb8d3af473aa95848ab22d5ecc591c5a1567a00"
CODE = "b6c97cae2e39dc971dc7437ae9962308c28db5d4"
RUN = "40572859641"


@pytest.fixture(scope="module")
def original():
    raw = (FIRST / "audit.json").read_bytes()
    report = json.loads(raw)
    index = json.loads((FIRST / "archive-index.json").read_text("utf-8"))
    return raw, report, index


def test_first_result_sha_exact_code_protocol_and_first_hypothesis(original):
    raw, r, i = original
    assert sha256(raw).hexdigest() == REPORT_SHA
    assert i["original_audit_sha256"] == REPORT_SHA
    assert r["protocol"] == i["protocol"] == "RP-U003-A01"
    assert r["preregistration_commit"] == i["frozen_protocol_commit"] == PREREG
    assert r["original_code_commit"] == i["first_code_commit"] == CODE
    assert r["first_run_id"] == i["first_run_id"] == RUN
    assert r["verdict"] == i["first_verdict"] == (
        "FINITE_BENCHMARK_LOOKAHEAD_F1_ADVANTAGE_SUPPORTED"
    )
    assert r["errors"] == []
    assert sorted(p.name for p in FIRST.iterdir()) == ["archive-index.json", "audit.json"]


def test_first_source_family_exact_n_two_generators_and_degree_strata(original):
    _, r, i = original
    family = r["family"]
    assert family["accepted_labeled_graphs"] == 684
    assert family["labeled_family_sha256"] == i["labeled_family_sha256"] == FAMILY_SHA
    assert family["all_14_candidate_edges_choose_seven_covered"] is True
    assert family["independent_enumerators_agree"] is True
    assert family["terminal_degree_two_and_no_direct_edge"] is True
    assert family["all_six_vertices_source_connected"] is True
    assert family["degree_multiset_counts"] == {
        "(1, 1, 2, 2, 3, 5)": 12,
        "(1, 1, 2, 2, 4, 4)": 12,
        "(1, 2, 2, 2, 2, 5)": 24,
        "(1, 2, 2, 2, 3, 4)": 240,
        "(1, 2, 2, 3, 3, 3)": 84,
        "(2, 2, 2, 2, 2, 4)": 84,
        "(2, 2, 2, 2, 3, 3)": 228,
    }
    assert sum(family["degree_multiset_counts"].values()) == 684


def test_first_complete_case_trace_identity_matches_untouched_bytes(original):
    _, report, index = original
    cases = report["all_case_records"]
    assert len(cases) == 684 * 4 == 2736
    encoded = "".join(
        json.dumps(case, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n" for case in cases
    ).encode("utf-8")
    assert sha256(encoded).hexdigest() == index["individual_case_trace_sha256"] == (
        report["all_cases_json_sha256"]
    ) == CASE_SHA
    assert all([case["lost_vertex"] for case in cases[i:i+4]] == [1, 2, 3, 4]
               for i in range(0, len(cases), 4))


def test_original_f1_shows_strict_primary_and_zero_increment_over_greedy(original):
    _, r, _ = original
    a = r["aggregates"]
    assert a["post_failure_model_time_steps_per_policy"] == 16416
    assert a["F1_uptime_case_ticks"] == {
        "ASC": 15736,
        "DEGREE": 15748,
        "GREEDY1": 15888,
        "LOOKAHEAD2": 15888,
    }
    assert a["F1_offline_optimal_envelope_case_ticks"] == 15888
    assert a["F1_regret_to_offline_envelope"] == {
        "ASC": 152,
        "DEGREE": 140,
        "GREEDY1": 0,
        "LOOKAHEAD2": 0,
    }
    assert r["comparisons"]["directional_H1_strict_gain_over_ASC"] is True
    assert r["comparisons"]["directional_H1_strict_gain_over_DEGREE"] is True


def test_F2_two_step_gain_is_secondary_and_with_more_computations(original):
    _, r, _ = original
    a = r["aggregates"]
    assert a["F2_uptime_case_ticks"] == {
        "ASC": 6980,
        "DEGREE": 7092,
        "GREEDY1": 7852,
        "LOOKAHEAD2": 7968,
    }
    assert a["F2_offline_optimal_envelope_case_ticks"] == 7968
    assert a["F2_regret_to_offline_envelope"] == {
        "ASC": 988,
        "DEGREE": 876,
        "GREEDY1": 116,
        "LOOKAHEAD2": 0,
    }
    assert a["total_candidate_function_evaluations_not_equivalent_CPU_cost"] == {
        "ASC": 0, "DEGREE": 0,
        "GREEDY1": 13164, "LOOKAHEAD2": 31236
    }


def test_pairwise_ties_and_all_negative_limit_controls_retained(original):
    _, r, _ = original
    c = r["comparisons"]
    assert c["lookahead_win_vs_ASC"] == 120
    assert c["lookahead_tie_vs_ASC"] == 2616
    assert c["lookahead_win_vs_DEGREE"] == 116
    assert c["lookahead_tie_vs_DEGREE"] == 2620
    assert c["lookahead_tie_vs_GREEDY1"] == 2736
    assert c.get("lookahead_loss_vs_ASC", 0) == 0
    assert c.get("lookahead_loss_vs_DEGREE", 0) == 0
    assert c.get("lookahead_win_vs_GREEDY1", 0) == 0
    assert c.get("lookahead_loss_vs_GREEDY1", 0) == 0
    assert c.get("lookahead_any_case_loss", 0) == 0
    assert c["first_five_synthetic_losses_deterministic_order"] == []
    assert c["equal_repair_budget_verified_for_all_policy_scenario_times"] is True


def test_every_original_case_matches_budget_and_two_task_oracles(original):
    _, r, _ = original
    for case in r["all_case_records"]:
        assert len(case["original_graph_edges"]) == 7
        assert [item for item in case["original_graph_edges"] if item == [0, 5]] == []
        assert case["lost_vertex"] in (1,2,3,4)
        policies = case["policies"]
        assert set(policies) == {"ASC", "DEGREE", "GREEDY1", "LOOKAHEAD2"}
        base_costs = None
        for name, record in policies.items():
            trajectory = record["snapshots"]
            assert len(trajectory) == 7
            costs = [(s["node_count"], s["edge_count"],
                      s["cumulative_repaired_edges"]) for s in trajectory]
            if base_costs is None:
                base_costs = costs
            else:
                assert costs == base_costs
            assert [s["t"] for s in trajectory] == list(range(7))
            assert all(s["F2"] <= s["F1"] for s in trajectory)
            assert record["post_failure_F1"] == sum(s["F1"] for s in trajectory[1:])
            assert record["post_failure_F2"] == sum(s["F2"] for s in trajectory[1:])
            assert all(
                s["F1"] <= case["offline_F1_by_t"][s["t"]]
                and s["F2"] <= case["offline_F2_by_t"][s["t"]]
                for s in trajectory
            )


def test_first_report_remains_artificial_and_prior_negative_unchanged(original):
    _, r, i = original
    assert r["scope"].startswith("complete finite labeled graph ensemble")
    assert r["real_domain_records_used"] == 0
    assert i["real_world_rows_examined"] == 0
    assert r["new_lean_theorem_or_universal_law_claimed"] is False
    assert i["new_universal_scientific_law_claimed"] is False
    assert i["existing_negative_external_results_unchanged"] is True


def test_mutated_original_report_fails_sha(original):
    raw, _, _ = original
    assert sha256(raw + b"\n").hexdigest() != REPORT_SHA
