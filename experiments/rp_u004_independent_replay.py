"""Independent, standard-library-only replay of RP-U004's frozen first report.

The verifier reads the original archived output but does not import the
RP-U004 experiment. It reconstructs graphs, repair choices and both
functional outcomes from the declared rules. Failure is fatal.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from hashlib import sha256
from itertools import combinations, permutations
import json
from pathlib import Path
import sys
import zipfile

SOURCE = 0
TARGET = 6
INTERNAL = (1, 2, 3, 4, 5)
POLICIES = (
    "ASC", "DEGREE", "GREEDY_F1", "GREEDY_F2",
    "LOOKAHEAD2_F1", "LOOKAHEAD2_F2",
)
EDGES = tuple((a, b) for a in range(7) for b in range(a + 1, 7)
              if (a, b) != (SOURCE, TARGET))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stream_hash(items):
    h = sha256()
    for item in items:
        h.update((canonical(item) + "\n").encode())
    return h.hexdigest()


def degrees(edges):
    degree = [0] * 7
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    return tuple(degree)


def source_connected(edges):
    # Union-find, independent of the experiment's BFS and stack DFS.
    parent = list(range(7))

    def root(v):
        while parent[v] != v:
            v = parent[v]
        return v

    for a, b in edges:
        ra, rb = root(a), root(b)
        parent[ra] = rb
    return len({root(v) for v in range(7)}) == 1


def source_family():
    source = tuple(
        e for e in combinations(EDGES, 8)
        if degrees(e)[SOURCE] == degrees(e)[TARGET] == 2
        and source_connected(e)
    )
    assert source and source == tuple(sorted(source))
    return source


def neighbor_set(edges, removed):
    return tuple(sorted(b if a == removed else a for a, b in edges
                        if removed in (a, b)))


def two_oracles(edges, nodes):
    # Path enumeration checks the existence of one/two disjoint routes.
    # A separate vertex-deletion BFS checks the F2 result.
    links = {v: set() for v in nodes}
    for a, b in edges:
        assert a in links and b in links
        links[a].add(b)
        links[b].add(a)

    def find_paths(path):
        current = path[-1]
        if current == TARGET:
            yield path
            return
        for neighbor in sorted(links[current]):
            if neighbor not in path:
                yield from find_paths(path + (neighbor,))

    paths = tuple(find_paths((SOURCE,)))
    f1 = bool(paths)
    f2_paths = any(
        set(a[1:-1]).isdisjoint(b[1:-1])
        for i, a in enumerate(paths) for b in paths[i + 1:]
    )

    def reaches_without(removed):
        queue = deque((SOURCE,))
        seen = {SOURCE}
        while queue:
            current = queue.popleft()
            if current == TARGET:
                return True
            for nxt in links[current]:
                if nxt != removed and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return False

    f2_cuts = f1 and all(reaches_without(v)
                          for v in nodes if v not in (SOURCE, TARGET))
    assert f2_paths == f2_cuts, "Independent F2 graph oracles disagree"
    return (int(f1), int(f2_paths))


def scores_for_repair(edges, lost):
    original = tuple((a, b) for a, b in edges if lost not in (a, b))
    surviving = set(range(7)) - {lost}
    new_node = 7 + lost
    neighbors = neighbor_set(edges, lost)
    table = {}
    for size in range(len(neighbors) + 1):
        for subset in combinations(neighbors, size):
            rebuilt = tuple(tuple(sorted((new_node, n))) for n in subset)
            table[frozenset(subset)] = two_oracles(
                original + rebuilt, surviving | {new_node}
            )
    baseline = two_oracles(original, surviving)
    assert table[frozenset()] == baseline
    assert len(table) == 2 ** len(neighbors)
    return neighbors, table, baseline


def choose_order(policy, graph, neighbors, table):
    chosen = []
    lookups = comparisons = 0
    original_degree = degrees(graph)
    while len(chosen) < len(neighbors):
        available = [v for v in neighbors if v not in chosen]
        if policy == "ASC":
            winner = min(available)
        elif policy == "DEGREE":
            winner = min(available, key=lambda v: (-original_degree[v], v))
        else:
            prioritize_f2 = policy.endswith("_F2")

            def rank(score):
                return (score[1], score[0]) if prioritize_f2 else score

            merits = []
            for candidate in available:
                state = frozenset(chosen + [candidate])
                immediate = rank(table[state])
                lookups += 1
                if policy.startswith("LOOKAHEAD2"):
                    others = [v for v in available if v != candidate]
                    if others:
                        next_scores = [rank(table[state | {v}]) for v in others]
                        lookups += len(others)
                        merit = max(next_scores) + immediate
                    else:
                        merit = immediate + immediate
                else:
                    merit = immediate
                comparisons += 1
                merits.append((merit, -candidate, candidate))
            winner = max(merits)[2]
        chosen.append(winner)
    # The experiment counts five outcome-table lookups for ticks 2..6.
    return tuple(chosen), lookups + 5, comparisons


def order_uptime(order, table, baseline):
    f1, f2 = baseline
    for tick in range(2, 7):
        score = table[frozenset(order[:min(tick - 1, len(order))])]
        f1 += score[0]
        f2 += score[1]
    return f1, f2


def brute_force_optimum(neighbors, table, baseline):
    all_scores = [(order_uptime(order, table, baseline), order)
                  for order in permutations(neighbors)]
    best1 = max(score[0][0] for score in all_scores)
    best2 = max(score[0][1] for score in all_scores)
    winners1 = [order for score, order in all_scores if score[0] == best1]
    winners2 = [order for score, order in all_scores if score[1] == best2]
    return {
        "F1": best1, "F2": best2,
        "F1_optimal_order_first_lex": list(min(winners1)),
        "F2_optimal_order_first_lex": list(min(winners2)),
        "F1_optimal_order_count": len(winners1),
        "F2_optimal_order_count": len(winners2),
        "permutations": len(all_scores),
    }


def relabeled(graph, lost):
    transform = {0: 0, 6: 6, 1: 2, 2: 3, 3: 4, 4: 5, 5: 1}
    return (tuple(sorted(tuple(sorted((transform[a], transform[b])))
                         for a, b in graph)), transform[lost])


def verify(report, archive_index):
    assert report["protocol"] == archive_index["protocol"] == "RP-U004-P01"
    assert report["original_code_commit"] == archive_index["first_code_commit"]
    assert str(report["original_run_id"]) == archive_index["first_run_id"]
    assert report["errors"] == []
    assert report["verdict"] == archive_index["first_verdict"]
    assert report["case_trace_sha256"] == archive_index["case_trace_sha256"]
    assert stream_hash(report["cases"]) == report["case_trace_sha256"]

    family = source_family()
    manifest = report["family"]
    assert len(family) == manifest["accepted_labeled_graphs"]
    assert stream_hash(family) == manifest["accepted_labeled_family_sha256"]
    assert manifest["accepted_labeled_family_sha256"] == archive_index["accepted_family_sha256"]

    degree_groups = defaultdict(list)
    for graph in family:
        degree_groups[degrees(graph)].append(graph)
    assert len(degree_groups) == len(manifest["all_degree_tuple_strata_counts"])
    assert {canonical(k): len(v) for k, v in sorted(degree_groups.items())} == manifest["all_degree_tuple_strata_counts"]

    singles = tuple(sorted(k for k, v in degree_groups.items() if len(v) == 1))
    pairs = tuple((k, tuple(sorted(v))[0], tuple(sorted(v))[-1])
                  for k, v in sorted(degree_groups.items()) if len(v) > 1)
    selected = tuple(graph for _, low, high in pairs for graph in (low, high))
    assert len(pairs) == manifest["matched_degree_pair_strata"]
    assert len(singles) == manifest["excluded_singleton_degree_strata"]
    assert [list(key) for key in singles] == manifest["excluded_singleton_degree_tuples"]
    assert len(selected) == manifest["selected_labeled_graphs"]
    assert stream_hash(selected) == manifest["selected_labeled_family_sha256"]
    assert manifest["selected_labeled_family_sha256"] == archive_index["selected_family_sha256"]

    expected_case_ids = tuple((graph, lost)
                              for _, low, high in pairs for graph in (low, high)
                              for lost in INTERNAL)
    actual_case_ids = tuple((tuple(map(tuple, case["original_graph"])), case["removed_vertex"])
                            for case in report["cases"])
    assert expected_case_ids == actual_case_ids

    all_f1, all_f2 = Counter(), Counter()
    all_lookups, all_comparisons = Counter(), Counter()
    win_counts = Counter()
    relabel_changed = Counter()
    total_table_entries = relabel_entries = initial_f2_count = 0
    total_offline_f1 = total_offline_f2 = 0
    sample_wins = []

    # All recorded cases, not a sample: rebuild every possible action subset.
    for idx, case in enumerate(report["cases"]):
        graph, lost = actual_case_ids[idx]
        assert tuple(case["degree_tuple"]) == degrees(graph)
        neighbors, table, baseline = scores_for_repair(graph, lost)
        assert tuple(case["eligible_neighbors"]) == neighbors
        assert case["truth_table_entries"] == len(table)
        total_table_entries += len(table)
        assert case["original_F1"] == 1
        initial_f2 = two_oracles(graph, set(range(7)))[1]
        assert case["original_F2"] == initial_f2
        initial_f2_count += initial_f2 if lost == INTERNAL[0] else 0

        optimum = brute_force_optimum(neighbors, table, baseline)
        assert optimum == case["offline_optimum"], f"Offline optimum mismatch in case {idx}"
        total_offline_f1 += optimum["F1"]
        total_offline_f2 += optimum["F2"]

        for policy in POLICIES:
            record = case["policies"][policy]
            order, lookup, comparison = choose_order(policy, graph, neighbors, table)
            assert tuple(record["order"]) == order, (idx, policy, "repair choice mismatch")
            assert record["operations"] == {"lookups": lookup, "comparisons": comparison}
            expected_f1, expected_f2 = order_uptime(order, table, baseline)
            assert (record["F1_uptime"], record["F2_uptime"]) == (expected_f1, expected_f2)
            assert expected_f1 <= optimum["F1"] and expected_f2 <= optimum["F2"]
            assert len(record["snapshots"]) == 6
            for tick, point in enumerate(record["snapshots"], 1):
                rebuilt = min(max(tick - 1, 0), len(neighbors))
                expected = baseline if tick == 1 else table[frozenset(order[:rebuilt])]
                assert (point["t"], point["F1"], point["F2"]) == (tick, *expected)
                assert (point["node_count"], point["edge_count"], point["repaired_edges"]) == (
                    6 if tick == 1 else 7, 8 - len(neighbors) + rebuilt, rebuilt
                )
            all_f1[policy] += expected_f1
            all_f2[policy] += expected_f2
            all_lookups[policy] += lookup
            all_comparisons[policy] += comparison

        for look, greedy, metric in (
            ("LOOKAHEAD2_F2", "GREEDY_F2", "F2"),
            ("LOOKAHEAD2_F1", "GREEDY_F1", "F1"),
        ):
            a = case["policies"][look][metric + "_uptime"]
            b = case["policies"][greedy][metric + "_uptime"]
            label = "win" if a > b else "loss" if a < b else "tie"
            win_counts[f"{look}_vs_{greedy}_{metric}_{label}"] += 1
            if a > b and len(sample_wins) < 2:
                sample_wins.append({
                    "graph": [list(edge) for edge in graph],
                    "lost_vertex": lost, "metric": metric,
                    "greedy": b, "lookahead": a,
                    "greedy_order": case["policies"][greedy]["order"],
                    "lookahead_order": case["policies"][look]["order"],
                })

        mapped, mapped_loss = relabeled(graph, lost)
        mapped_neighbors, mapped_table, mapped_baseline = scores_for_repair(mapped, mapped_loss)
        relabel_entries += len(mapped_table)
        for policy in POLICIES:
            mapped_order, _, _ = choose_order(policy, mapped, mapped_neighbors, mapped_table)
            mapped_f1, mapped_f2 = order_uptime(mapped_order, mapped_table, mapped_baseline)
            record = case["policies"][policy]
            flags = {
                "F1_changed": mapped_f1 != record["F1_uptime"],
                "F2_changed": mapped_f2 != record["F2_uptime"],
            }
            assert flags == case["cyclic_relabeling_sensitivity"][policy]
            for metric in ("F1", "F2"):
                relabel_changed[f"{policy}_{metric}"] += int(flags[f"{metric}_changed"])

    agg = report["aggregates"]
    assert len(report["cases"]) == agg["scenarios"] == len(selected) * len(INTERNAL)
    assert agg["post_failure_case_ticks_per_policy"] == len(report["cases"]) * 6
    assert dict(all_f1) == agg["F1_uptime"]
    assert dict(all_f2) == agg["F2_uptime"]
    assert dict(all_lookups) == agg["policy_lookup_counts"]
    assert dict(all_comparisons) == agg["policy_comparison_counts"]
    assert total_offline_f1 == agg["offline_F1_maximum_sum"]
    assert total_offline_f2 == agg["offline_F2_maximum_sum"]
    assert total_table_entries == agg["primary_truth_table_entries"]
    assert relabel_entries == agg["cyclic_relabel_truth_table_entries"]
    assert initial_f2_count == agg["source_graphs_with_initial_F2"]
    assert agg["source_graphs_total"] == len(selected)
    assert {k: v for k, v in relabel_changed.items() if v} == agg["cyclic_relabel_changed_score_cases"]
    assert dict(win_counts) == {
        key: value for key, value in report["comparisons"].items()
        if key.startswith("LOOKAHEAD2_")
    }
    assert report["comparisons"]["H1_two_step_F2_strictly_beats_greedy_F2"] == (
        all_f2["LOOKAHEAD2_F2"] > all_f2["GREEDY_F2"]
    )
    assert report["comparisons"]["H2_two_step_F1_strictly_beats_greedy_F1"] == (
        all_f1["LOOKAHEAD2_F1"] > all_f1["GREEDY_F1"]
    )
    assert report["comparisons"]["same_truth_table_for_all_policies"] is True
    assert report["comparisons"]["edge_costs_identical_for_all_policies"] is True
    assert report["comparisons"]["decision_time_CPU_equal"] is False
    for policy in POLICIES:
        assert agg["regret_F1"][policy] == total_offline_f1 - all_f1[policy]
        assert agg["regret_F2"][policy] == total_offline_f2 - all_f2[policy]

    return {
        "verdict": report["verdict"],
        "accepted_source_graphs": len(family),
        "matched_pairs": len(pairs),
        "scenario_count": len(report["cases"]),
        "F1": dict(all_f1), "F2": dict(all_f2),
        "comparisons": dict(win_counts),
        "offline_F1": total_offline_f1, "offline_F2": total_offline_f2,
        "initial_F2_source_graphs": initial_f2_count,
        "truth_table_entries": total_table_entries,
        "relabeling_changes": {k: v for k, v in relabel_changed.items() if v},
        "example_improvements": sample_wins,
    }


def main():
    archive = Path(sys.argv[1])
    index = Path(sys.argv[2])
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            assert zf.namelist() == ["audit.json"]
            raw = zf.read("audit.json")
    else:
        raw = archive.read_bytes()
    metadata = json.loads(index.read_text(encoding="utf-8"))
    assert sha256(raw).hexdigest() == metadata["original_audit_sha256"]
    result = verify(json.loads(raw), metadata)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
