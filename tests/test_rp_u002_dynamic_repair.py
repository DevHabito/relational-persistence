"""RP-U002-A01 synthetic adversarial node-turnover and repair regression.

All sources are fixed artificial six-node graphs. No third-party rows,
ecological inference, stochastic likelihood or unregistered graph tuning.
"""

from __future__ import annotations

import json
import sys

import pytest

from experiments import rp_u002_dynamic_repair as u


@pytest.mark.parametrize("policy,graph,expected", [
    ("repair","A",(4,4,4,4,4,4)),
    ("repair","B",(4,3,3,3,4,4)),
    ("no_repair","A",(4,4,4,4,4,4)),
    ("no_repair","B",(4,3,3,3,3,3)),
])
def test_every_registered_F1_time_count_exact(policy, graph, expected):
    repair = policy == "repair"
    histories = [u.single_history(graph, lost, repair) for lost in u.INTERNAL]
    counts = tuple(sum(h["snapshots"][t]["F1"] for h in histories)
                   for t in u.HORIZON)
    assert counts == expected


@pytest.mark.parametrize("policy,graph,expected", [
    ("repair","A",(4,0,0,3,4,4)),
    ("repair","B",(0,0,0,0,0,0)),
    ("no_repair","A",(4,0,0,0,0,0)),
    ("no_repair","B",(0,0,0,0,0,0)),
])
def test_every_registered_F2_time_count_exact(policy, graph, expected):
    repair = policy == "repair"
    histories = [u.single_history(graph, lost, repair) for lost in u.INTERNAL]
    counts = tuple(sum(h["snapshots"][t]["F2"] for h in histories)
                   for t in u.HORIZON)
    assert counts == expected


def test_frozen_preregistration_and_max_one_edge_cost_each_tick():
    assert u.PREREG == "fa7f9d0133370b0e8a769d0b7d95759e402a2dc8"
    assert u.HORIZON == (0,1,2,3,4,5)
    assert u.INTERNAL == (1,2,3,4)
    for graph in ("A", "B"):
        for lost in u.INTERNAL:
            for repair in (True, False):
                history = u.independent_event_replay(graph, lost, repair)
                u.validate_history(graph, lost, repair, history)
                for t in range(2, 6):
                    assert len(history[t].edges - history[t-1].edges) <= 1


def test_six_nodes_return_but_not_function_B_center_at_t2():
    snapshots = u.independent_event_replay("B", 2, True)
    assert len(snapshots[0].vertices) == len(snapshots[2].vertices) == 6
    assert 2 in snapshots[0].vertices and 2 not in snapshots[2].vertices
    assert 8 not in snapshots[0].vertices and 8 in snapshots[2].vertices
    assert u.connected_bfs(snapshots[0]) is True
    assert u.connected_bfs(snapshots[2]) is False
    assert u.connected_bfs(snapshots[3]) is False
    assert u.connected_bfs(snapshots[4]) is True
    assert u.connected_bfs(snapshots[5]) is True


def test_restoration_of_connection_not_persistence_of_old_identity():
    for graph in ("A", "B"):
        for lost in u.INTERNAL:
            histories = u.independent_event_replay(graph, lost, True)
            assert all(lost not in histories[t].vertices for t in range(1, 6))
            assert all(6 + lost in histories[t].vertices for t in range(2, 6))
            assert all(len(histories[t].vertices) == 6 for t in range(2, 6))


def test_preprogrammed_repair_neighbors_never_ad_hoc():
    base = u.originals("B")
    assert u.original_neighbors(base, 2) == (1,3,4,5)
    for t, expected in {
        1: set(), 2: {1}, 3: {1,3}, 4: {1,3,4}, 5: {1,3,4,5}
    }.items():
        state = u.independent_direct("B", 2, t, True)
        actual = {other for pair in state.edges for other in pair
                  if 8 in pair and other != 8}
        assert actual == expected


def test_A_stronger_function_recovery_is_not_instantaneous():
    histories = {
        failed: u.single_history("A", failed, True)["snapshots"]
        for failed in u.INTERNAL
    }
    assert sum(states[3]["F2"] for states in histories.values()) == 3
    assert not histories[3][3]["F2"]
    assert all(states[4]["F2"] for states in histories.values())
    assert all(not states[1]["F2"] and not states[2]["F2"]
               for states in histories.values())


def test_persistently_no_repair_B_central_failure_never_recovers():
    states = u.single_history("B", 2, False)["snapshots"]
    assert states[0]["F1"]
    assert all(not states[t]["F1"] for t in range(1,6))
    assert all(states[t]["present_component_count"] == 5 for t in range(1,6))


def test_equal_graph_summaries_do_not_guarantee_equal_temporal_F1():
    for graph in ("A","B"):
        base = u.originals(graph)
        assert len(base.vertices) == 6 and len(base.edges) == 7
        assert sum(0 in pair for pair in base.edges) == 2
        assert sum(5 in pair for pair in base.edges) == 2
    assert u.single_history("A",2,True)["snapshots"][2]["F1"]
    assert not u.single_history("B",2,True)["snapshots"][2]["F1"]


def test_single_bad_edge_rejects_state_constructor_oracle():
    steps = u.independent_event_replay("B",2,True)
    bad = dict(steps)
    original = bad[3]
    bad[3] = u.Snapshot(original.vertices,
                        original.edges | frozenset([u.edge(0,8)]))
    with pytest.raises(AssertionError, match="state replay"):
        u.validate_history("B",2,True,bad)


def test_extra_edge_per_time_limit_rejected():
    original = u.independent_event_replay("B",2,True)
    bad = dict(original)
    s2 = bad[2]
    bad[2] = u.Snapshot(s2.vertices,
                        s2.edges | frozenset([u.edge(8,4), u.edge(8,5)]))
    with pytest.raises(AssertionError):
        u.validate_history("B",2,True,bad)


def test_dangling_edge_to_deleted_old_component_rejected():
    original = u.independent_event_replay("B",2,True)
    bad = dict(original)
    s2 = bad[2]
    bad[2] = u.Snapshot(s2.vertices,s2.edges | frozenset([u.edge(2,8)]))
    with pytest.raises(AssertionError):
        u.validate_history("B",2,True,bad)


def test_altered_recovery_policy_cannot_pass_exact_metrics(monkeypatch):
    # Adversarial wrong fixed registered count forces a negative, not retuning.
    expected = dict(u.REGISTERED_F1)
    expected["repair"] = {**u.REGISTERED_F1["repair"],"B":(4,3,4,3,4,4)}
    monkeypatch.setattr(u,"REGISTERED_F1",expected)
    verdict = u.audit()
    assert verdict["verdict"] == "REGISTERED_TURNOVER_REPAIR_PREDICTION_FAILED"
    assert verdict["errors"]


def test_oracle_disagreement_is_a_fatal_negative(monkeypatch):
    original = u.connected_bfs
    def false_positive_bfs(state, excluded=frozenset()):
        return True if len(state.vertices) == 5 else original(state, excluded)
    monkeypatch.setattr(u,"connected_bfs",false_positive_bfs)
    data = u.audit()
    assert data["verdict"] == "REGISTERED_TURNOVER_REPAIR_PREDICTION_FAILED"
    assert data["errors"]


def test_wrong_f2_oracle_cannot_hide_failed_stronger_function(monkeypatch):
    monkeypatch.setattr(u,"two_routes_by_cut_tests",lambda state: True)
    result = u.audit()
    assert result["verdict"] == "REGISTERED_TURNOVER_REPAIR_PREDICTION_FAILED"


def test_invalid_source_vertex_or_time_fails_closed():
    for lost in (0,5,-1,6):
        with pytest.raises(ValueError):
            u.independent_direct("A",lost,2,True)
    with pytest.raises(ValueError):
        u.independent_direct("A",2,6,True)
    with pytest.raises(ValueError):
        u.originals("arbitrary")


def test_graph_A_no_F1_policy_gain_B_no_F2_policy_gain():
    result = u.audit()
    assert result["verdict"] == "FINITE_TURNOVER_REPAIR_CONTRAST_VERIFIED"
    assert result["result"]["repair"]["A"]["uptime_F1_exact_count_out_of_20"] == 20
    assert result["result"]["no_repair"]["A"]["uptime_F1_exact_count_out_of_20"] == 20
    assert result["result"]["repair"]["B"]["uptime_F2_exact_count_out_of_20"] == 0
    assert result["result"]["no_repair"]["B"]["uptime_F2_exact_count_out_of_20"] == 0


def test_original_all_16_scenarios_preserved_by_policy_and_graph():
    result = u.audit()
    assert not result["errors"]
    for policy in ("repair","no_repair"):
        for name in ("A","B"):
            entry = result["result"][policy][name]
            assert [x["loss"] for x in entry["original_single_failure_scenarios"]] == list(u.INTERNAL)
            assert all([x["time"] for x in case["snapshots"]] == list(u.HORIZON)
                       for case in entry["original_single_failure_scenarios"])
    assert result["negative_controls"]["B_bottleneck_F1_not_restored_by_new_node_alone"]
    assert result["all_real_domain_observations"] == 0
    assert result["new_universal_law_claimed"] is False
    assert result["forecast_or_physical_scalar_estimated"] is False


def test_first_result_filepath_never_overwritten(monkeypatch,tmp_path):
    old=tmp_path/"original.json"
    old.write_text("ORIGINAL",encoding="utf-8")
    monkeypatch.setattr(sys,"argv",["u002","--output",str(old)])
    with pytest.raises(SystemExit,match="refusing overwrite"):
        u.main()
    assert old.read_text(encoding="utf-8") == "ORIGINAL"


def test_never_label_original_ecology_data_as_measured():
    data=u.audit()
    assert data["measurements_of_recovery_or_biological_growth"] is False
    assert data["scope"].startswith("fixed toy graph")
    assert data["all_real_domain_observations"] == 0
