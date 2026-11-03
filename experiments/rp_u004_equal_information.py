"""RP-U004-P01: frozen degree-matched, equal-information repair benchmark.

The prospective protocol was committed alone before this module:
docs/preregistration/RP-U004-P01.md. These are synthetic graph functions,
not field recovery, original graph theory, or an empirical physical law.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from hashlib import sha256
from itertools import combinations, permutations
from pathlib import Path
import argparse
import json
import os

PROTOCOL = "RP-U004-P01"
PREREG = "186d6fc5d8cc6451fca63abb5f6ef4f2029a3d7b"
VERTICES = frozenset(range(7))
INTERNAL = (1, 2, 3, 4, 5)
SOURCE, TARGET = 0, 6
TIMES = tuple(range(1, 7))
PAIRS = tuple((a, b) for a in range(7) for b in range(a + 1, 7)
              if (a, b) != (SOURCE, TARGET))
INNER_PAIRS = tuple(combinations(INTERNAL, 2))
POLICIES = (
    "ASC", "DEGREE", "GREEDY_F1", "GREEDY_F2",
    "LOOKAHEAD2_F1", "LOOKAHEAD2_F2",
)


def edge(a: int, b: int) -> tuple[int, int]:
    if a == b:
        raise AssertionError("Self-loop is not an admissible source edge")
    return (a, b) if a < b else (b, a)


def degrees(edges) -> tuple[int, ...]:
    counts = [0] * 7
    for a, b in edges:
        counts[a] += 1
        counts[b] += 1
    return tuple(counts)


def reachable_bfs(edges, nodes, start: int, target: int,
                  excluded: int | None = None) -> bool:
    remaining = nodes - ({excluded} if excluded is not None else set())
    if start not in remaining or target not in remaining:
        return False
    links = {node: set() for node in remaining}
    for a, b in edges:
        if a in remaining and b in remaining:
            links[a].add(b)
            links[b].add(a)
    queue = deque([start])
    seen = {start}
    while queue:
        current = queue.popleft()
        if current == target:
            return True
        for nxt in links[current]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return False


def all_simple_paths(edges, nodes) -> tuple[tuple[int, ...], ...]:
    """Independent simple-path DFS: no BFS helper or shared adjacency builder."""
    if SOURCE not in nodes or TARGET not in nodes:
        return ()
    graph = frozenset(edges)
    answer = []

    def visit(path):
        if path[-1] == TARGET:
            answer.append(tuple(path))
            return
        for nxt in sorted(nodes):
            if nxt not in path and edge(path[-1], nxt) in graph:
                visit(path + [nxt])

    visit([SOURCE])
    return tuple(answer)


def functions(edges, nodes) -> tuple[int, int]:
    if edge(SOURCE, TARGET) in edges:
        raise AssertionError("The direct terminal edge is forbidden")
    f1_a = reachable_bfs(edges, nodes, SOURCE, TARGET)
    paths = all_simple_paths(edges, nodes)
    f1_b = bool(paths)
    if f1_a != f1_b:
        raise AssertionError("F1 BFS and DFS oracles disagree")
    f2_a = any(
        set(path[1:-1]).isdisjoint(other[1:-1])
        for i, path in enumerate(paths) for other in paths[i + 1:]
    )
    f2_b = f1_a and all(
        reachable_bfs(edges, nodes, SOURCE, TARGET, excluded=v)
        for v in nodes - {SOURCE, TARGET}
    )
    if f2_a != f2_b or (f2_a and not f1_a):
        raise AssertionError("F2 disjoint-path and cut oracles disagree")
    return (int(f1_a), int(f2_a))


def connected_bfs(edges) -> bool:
    return all(reachable_bfs(edges, VERTICES, SOURCE, dest)
               for dest in VERTICES)


def connected_independent_dfs(edges) -> bool:
    """A stack-based DFS, separate from the BFS source-graph validator."""
    seen = {SOURCE}
    stack = [SOURCE]
    graph = frozenset(edges)
    while stack:
        current = stack.pop()
        for neighbor in sorted(VERTICES):
            if neighbor not in seen and edge(current, neighbor) in graph:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == VERTICES


def source_valid(edges) -> bool:
    graph = tuple(edges)
    if len(graph) != 8 or len(set(graph)) != 8:
        return False
    if any(a >= b or (a, b) not in PAIRS for a, b in graph):
        return False
    d = degrees(graph)
    return d[SOURCE] == d[TARGET] == 2 and connected_bfs(graph)


def independent_source_valid(edges) -> bool:
    graph = tuple(edges)
    if len(graph) != 8 or len(set(graph)) != 8:
        return False
    if any(a >= b or (a, b) not in PAIRS for a, b in graph):
        return False
    d = degrees(graph)
    return d[SOURCE] == 2 and d[TARGET] == 2 and connected_independent_dfs(graph)


def all_source_graphs():
    enumeration_a = tuple(
        graph for graph in combinations(PAIRS, 8)
        if source_valid(graph)
    )
    enumeration_b = tuple(sorted(
        graph for terminal_a in combinations(INTERNAL, 2)
        for terminal_b in combinations(INTERNAL, 2)
        for interior in combinations(INNER_PAIRS, 4)
        if independent_source_valid(
            graph := tuple(sorted(
                [edge(SOURCE, n) for n in terminal_a]
                + [edge(n, TARGET) for n in terminal_b]
                + list(interior)
            ))
        )
    ))
    if not enumeration_a or enumeration_a != enumeration_b:
        raise AssertionError("Independent complete source enumerators disagree")
    if len(set(enumeration_a)) != len(enumeration_a):
        raise AssertionError("Duplicated original graph")
    return enumeration_a


def matched_degree_pairs(graphs):
    groups = defaultdict(list)
    for graph in graphs:
        groups[degrees(graph)].append(graph)
    matched = []
    singletons = 0
    for degree_key, members in sorted(groups.items()):
        members.sort()
        if len(members) == 1:
            singletons += 1
            continue
        first, last = members[0], members[-1]
        if first == last or degrees(first) != degrees(last):
            raise AssertionError("Degree matching did not produce a distinct pair")
        matched.append((degree_key, first, last))
    if not matched:
        raise AssertionError("No distinct matched-degree pairs")
    return tuple(matched), singletons


def old_neighbors(graph, lost: int) -> tuple[int, ...]:
    if lost not in INTERNAL:
        raise AssertionError("Only originally internal nodes may be removed")
    return tuple(sorted(b if a == lost else a for a, b in graph
                        if lost in (a, b)))


def snapshot(graph, lost: int, restored, tick: int):
    neighbors = old_neighbors(graph, lost)
    chosen = tuple(restored)
    if not set(chosen) <= set(neighbors) or len(set(chosen)) != len(chosen):
        raise AssertionError("Repair chose an invalid or repeated old neighbor")
    if tick == 0:
        return frozenset(graph), VERTICES
    fixed = frozenset((a, b) for a, b in graph if lost not in (a, b))
    nodes = VERTICES - {lost}
    if tick == 1:
        return fixed, frozenset(nodes)
    if tick not in range(2, 7):
        raise AssertionError("Unregistered time")
    replacement = 7 + lost
    return (fixed | frozenset(edge(replacement, n) for n in chosen),
            frozenset(nodes | {replacement}))


def event_replay(graph, lost: int, order):
    current_edges, current_nodes = snapshot(graph, lost, (), 1)
    current_edges = set(current_edges)
    current_nodes = set(current_nodes)
    states = [(frozenset(current_edges), frozenset(current_nodes))]
    for tick in range(2, 7):
        if tick == 2:
            current_nodes.add(7 + lost)
        index = tick - 2
        if index < len(order):
            current_edges.add(edge(7 + lost, order[index]))
        states.append((frozenset(current_edges), frozenset(current_nodes)))
    return tuple(states)


def truth_table(graph, lost: int):
    neighbors = old_neighbors(graph, lost)
    table = {}
    for count in range(len(neighbors) + 1):
        for subset in combinations(neighbors, count):
            edges, nodes = snapshot(graph, lost, subset, 2)
            table[frozenset(subset)] = functions(edges, nodes)
    if len(table) != 2 ** len(neighbors):
        raise AssertionError("Missing truth table entry")
    return table


def _function_merit(score, objective: str):
    f1, f2 = score
    return (f1, f2) if objective == "F1" else (f2, f1)


def choose_next(policy, graph, chosen, neighbors, table, operations):
    available = [v for v in neighbors if v not in chosen]
    if not available:
        raise AssertionError("No remaining neighbor to select")
    if policy == "ASC":
        return min(available)
    if policy == "DEGREE":
        d = degrees(graph)
        return min(available, key=lambda v: (-d[v], v))
    if policy not in POLICIES:
        raise AssertionError("Unknown repair policy")
    objective = "F1" if policy.endswith("_F1") else "F2"
    ranked = []
    for candidate in available:
        current = frozenset((*chosen, candidate))
        now = table[current]
        operations["lookups"] += 1
        immediate_merit = _function_merit(now, objective)
        if policy.startswith("LOOKAHEAD2"):
            future_candidates = [v for v in available if v != candidate]
            if future_candidates:
                merits = []
                for future in future_candidates:
                    merits.append(_function_merit(table[current | {future}], objective))
                    operations["lookups"] += 1
                future_merit = max(merits)
            else:
                future_merit = immediate_merit
            merit = future_merit + immediate_merit
        else:
            merit = immediate_merit
        operations["comparisons"] += 1
        ranked.append((merit, -candidate, candidate))
    return max(ranked)[2]


def policy_trace(graph, lost: int, policy: str, table):
    neighbors = old_neighbors(graph, lost)
    order = []
    work = {"lookups": 0, "comparisons": 0}
    for _ in neighbors:
        order.append(choose_next(policy, graph, tuple(order), neighbors, table, work))
    if set(order) != set(neighbors) or len(order) != len(set(order)):
        raise AssertionError("Repair order is not a permutation of eligible neighbors")
    event_states = event_replay(graph, lost, order)
    records = []
    for tick in TIMES:
        restored = order[:min(max(tick - 1, 0), len(order))]
        edges, nodes = snapshot(graph, lost, restored, tick)
        if (edges, nodes) != event_states[tick - 1]:
            raise AssertionError("Event replay disagrees with exact snapshot")
        count = len(restored)
        expected_nodes = 6 if tick == 1 else 7
        expected_edges = 8 - len(neighbors) + count
        if (len(nodes), len(edges)) != (expected_nodes, expected_edges):
            raise AssertionError("Wrong present nodes or repaired edges")
        if lost in nodes or (tick >= 2 and (7 + lost) not in nodes):
            raise AssertionError("Lost original identity returned or replacement absent")
        score = (functions(edges, nodes) if tick == 1
                 else table[frozenset(restored)])
        if tick >= 2:
            work["lookups"] += 1
        if score[1] > score[0]:
            raise AssertionError("F2 without F1")
        records.append({
            "t": tick, "F1": score[0], "F2": score[1],
            "node_count": len(nodes), "edge_count": len(edges),
            "repaired_edges": count,
        })
    return {
        "order": order,
        "F1_uptime": sum(s["F1"] for s in records),
        "F2_uptime": sum(s["F2"] for s in records),
        "operations": work,
        "snapshots": records,
    }


def offline_optimum(graph, lost: int, table):
    neighbors = old_neighbors(graph, lost)
    initial_edges, initial_nodes = snapshot(graph, lost, (), 1)
    base_f1, base_f2 = functions(initial_edges, initial_nodes)
    scores = []
    for order in permutations(neighbors):
        f1, f2 = base_f1, base_f2
        for tick in range(2, 7):
            subset = frozenset(order[:min(tick - 1, len(order))])
            a, b = table[subset]
            f1 += a
            f2 += b
        scores.append((f1, f2, order))
    if not scores:
        raise AssertionError("No complete candidate repair permutations")
    best_f1 = max(s[0] for s in scores)
    best_f2 = max(s[1] for s in scores)
    f1_orders = tuple(s[2] for s in scores if s[0] == best_f1)
    f2_orders = tuple(s[2] for s in scores if s[1] == best_f2)
    if not f1_orders or not f2_orders:
        raise AssertionError("Missing maximizing repair order")
    return {
        "F1": best_f1,
        "F2": best_f2,
        "F1_optimal_order_first_lex": list(min(f1_orders)),
        "F2_optimal_order_first_lex": list(min(f2_orders)),
        "F1_optimal_order_count": len(f1_orders),
        "F2_optimal_order_count": len(f2_orders),
        "permutations": len(scores),
    }


def cyclic_relabel(graph, lost: int):
    mapping = {0: 0, 6: 6, 1: 2, 2: 3, 3: 4, 4: 5, 5: 1}
    relabeled = tuple(sorted(edge(mapping[a], mapping[b]) for a, b in graph))
    if degrees(relabeled)[0] != 2 or degrees(relabeled)[6] != 2:
        raise AssertionError("Relabeling violated terminal degrees")
    return relabeled, mapping[lost]


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def hash_sequence(items):
    return sha256("".join(canonical_json(item) + "\n" for item in items).encode()).hexdigest()


def audit():
    report = {
        "protocol": PROTOCOL,
        "preregistration_commit": PREREG,
        "original_run_id": os.environ.get("GITHUB_RUN_ID"),
        "original_code_commit": os.environ.get("GITHUB_SHA"),
        "verdict": "FINITE_MATCHED_DEGREE_BENCHMARK_INVALID",
        "scope": "selected exhaustive structural family, synthetic, same graph knowledge and same truth table, equal repaired edges",
        "physical_data_rows": 0,
        "new_lean_theorem_claimed": False,
        "new_physical_law_claimed": False,
        "family": {}, "aggregates": {}, "comparisons": {}, "cases": [],
        "errors": [],
    }
    try:
        sources = all_source_graphs()
        pairs, singleton_count = matched_degree_pairs(sources)
        source_degree_counts = Counter(degrees(graph) for graph in sources)
        if sum(source_degree_counts.values()) != len(sources):
            raise AssertionError("Original degree-stratum census incomplete")
        excluded_singleton_keys = sorted(
            degree_key for degree_key, count in source_degree_counts.items()
            if count == 1
        )
        if len(excluded_singleton_keys) != singleton_count:
            raise AssertionError("Singleton degree-stratum census mismatch")
        selected = tuple(graph for _key, first, last in pairs
                         for graph in (first, last))
        if len(set(selected)) != len(selected):
            raise AssertionError("Selected graphs repeated across paired strata")
        report["family"] = {
            "accepted_labeled_graphs": len(sources),
            "accepted_labeled_family_sha256": hash_sequence(sources),
            "matched_degree_pair_strata": len(pairs),
            "excluded_singleton_degree_strata": singleton_count,
            "excluded_singleton_degree_tuples": [
                list(degree_key) for degree_key in excluded_singleton_keys
            ],
            "all_degree_tuple_strata_counts": {
                canonical_json(degree_key): count
                for degree_key, count in sorted(source_degree_counts.items())
            },
            "selected_labeled_graphs": len(selected),
            "selected_labeled_family_sha256": hash_sequence(selected),
            "all_graphs_degree_matched_within_pairs": True,
            "independent_enumerators_agree": True,
            "original_terminal_degrees": [2, 2],
            "original_edges_per_graph": 8,
        }
        f1_total, f2_total = Counter(), Counter()
        lookups, comparisons = Counter(), Counter()
        pair_comparisons = Counter()
        strata = {}
        offline_f1, offline_f2 = 0, 0
        primary_table_entries = 0
        relabeled_table_entries = 0
        source_graphs_with_f2 = 0
        relabel_changes = Counter()
        for degree_key, first, last in pairs:
            stratum_id = canonical_json(degree_key)
            stratum_totals = {"scenario_count": 0, "F1": Counter(), "F2": Counter()}
            for graph in (first, last):
                original_f1, original_f2 = functions(frozenset(graph), VERTICES)
                if original_f1 != 1:
                    raise AssertionError("Connected source lacks the original F1 function")
                source_graphs_with_f2 += original_f2
                for lost in INTERNAL:
                    table = truth_table(graph, lost)
                    primary_table_entries += len(table)
                    optimal = offline_optimum(graph, lost, table)
                    offline_f1 += optimal["F1"]
                    offline_f2 += optimal["F2"]
                    case = {
                        "degree_tuple": list(degree_key),
                        "original_graph": [list(e) for e in graph],
                        "original_F1": original_f1,
                        "original_F2": original_f2,
                        "removed_vertex": lost,
                        "eligible_neighbors": list(old_neighbors(graph, lost)),
                        "truth_table_entries": len(table),
                        "offline_optimum": optimal,
                        "policies": {},
                    }
                    reference_costs = None
                    for policy in POLICIES:
                        record = policy_trace(graph, lost, policy, table)
                        costs = tuple(
                            (s["node_count"], s["edge_count"], s["repaired_edges"])
                            for s in record["snapshots"]
                        )
                        if reference_costs is None:
                            reference_costs = costs
                        elif costs != reference_costs:
                            raise AssertionError("Policies use unequal edge or node budgets")
                        if (record["F1_uptime"] > optimal["F1"]
                                or record["F2_uptime"] > optimal["F2"]):
                            raise AssertionError("Policy exceeds global offline repair bound")
                        case["policies"][policy] = record
                        f1_total[policy] += record["F1_uptime"]
                        f2_total[policy] += record["F2_uptime"]
                        lookups[policy] += record["operations"]["lookups"]
                        comparisons[policy] += record["operations"]["comparisons"]
                        stratum_totals["F1"][policy] += record["F1_uptime"]
                        stratum_totals["F2"][policy] += record["F2_uptime"]
                    stratum_totals["scenario_count"] += 1
                    for look, greedy, metric in (
                        ("LOOKAHEAD2_F2", "GREEDY_F2", "F2"),
                        ("LOOKAHEAD2_F1", "GREEDY_F1", "F1"),
                    ):
                        candidate = case["policies"][look][metric + "_uptime"]
                        baseline = case["policies"][greedy][metric + "_uptime"]
                        label = "win" if candidate > baseline else (
                            "loss" if candidate < baseline else "tie")
                        pair_comparisons[f"{look}_vs_{greedy}_{metric}_{label}"] += 1
                    # Prespecified single cyclic relabeling sensitivity audit:
                    relabeled, relost = cyclic_relabel(graph, lost)
                    if not independent_source_valid(relabeled):
                        raise AssertionError("Relabeled graph became inadmissible")
                    relabeled_table = truth_table(relabeled, relost)
                    relabeled_table_entries += len(relabeled_table)
                    deviations = {}
                    for policy in POLICIES:
                        translated = policy_trace(relabeled, relost, policy, relabeled_table)
                        original = case["policies"][policy]
                        deviations[policy] = {
                            "F1_changed": original["F1_uptime"] != translated["F1_uptime"],
                            "F2_changed": original["F2_uptime"] != translated["F2_uptime"],
                        }
                        for metric in ("F1", "F2"):
                            if deviations[policy][metric + "_changed"]:
                                relabel_changes[policy + "_" + metric] += 1
                    case["cyclic_relabeling_sensitivity"] = deviations
                    report["cases"].append(case)
            strata[stratum_id] = {
                "scenario_count": stratum_totals["scenario_count"],
                "F1_uptime": dict(sorted(stratum_totals["F1"].items())),
                "F2_uptime": dict(sorted(stratum_totals["F2"].items())),
            }
        expected_cases = 2 * len(pairs) * len(INTERNAL)
        if len(report["cases"]) != expected_cases:
            raise AssertionError("Missing cases from selected paired strata")
        denominator = len(report["cases"]) * len(TIMES)
        if not denominator:
            raise AssertionError("Empty experiment")
        report["aggregates"] = {
            "scenarios": len(report["cases"]),
            "post_failure_case_ticks_per_policy": denominator,
            "source_graphs_with_initial_F2": source_graphs_with_f2,
            "source_graphs_total": len(selected),
            "primary_truth_table_entries": primary_table_entries,
            "cyclic_relabel_truth_table_entries": relabeled_table_entries,
            "cyclic_relabel_changed_score_cases": dict(sorted(relabel_changes.items())),
            "F1_uptime": dict(sorted(f1_total.items())),
            "F2_uptime": dict(sorted(f2_total.items())),
            "offline_F1_maximum_sum": offline_f1,
            "offline_F2_maximum_sum": offline_f2,
            "regret_F1": {p: offline_f1 - f1_total[p] for p in POLICIES},
            "regret_F2": {p: offline_f2 - f2_total[p] for p in POLICIES},
            "policy_lookup_counts": dict(sorted(lookups.items())),
            "policy_comparison_counts": dict(sorted(comparisons.items())),
            "matched_degree_strata": strata,
        }
        h1 = f2_total["LOOKAHEAD2_F2"] > f2_total["GREEDY_F2"]
        h2 = f1_total["LOOKAHEAD2_F1"] > f1_total["GREEDY_F1"]
        report["comparisons"] = {
            **dict(sorted(pair_comparisons.items())),
            "H1_two_step_F2_strictly_beats_greedy_F2": h1,
            "H2_two_step_F1_strictly_beats_greedy_F1": h2,
            "edge_costs_identical_for_all_policies": True,
            "same_truth_table_for_all_policies": True,
            "decision_time_CPU_equal": False,
        }
        report["case_trace_sha256"] = hash_sequence(report["cases"])
        report["verdict"] = (
            "FINITE_MATCHED_DEGREE_F2_LOOKAHEAD_ADVANTAGE_SUPPORTED"
            if h1 else "REGISTERED_F2_LOOKAHEAD_ADVANTAGE_NOT_SUPPORTED"
        )
    except (AssertionError, ValueError, KeyError, TypeError) as exc:
        report["errors"].append(
            {"reason": f"{type(exc).__name__}: {str(exc)[:400]}"}
        )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite RP-U004's original output")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = audit()
    args.output.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(canonical_json({
        "protocol": PROTOCOL,
        "verdict": report["verdict"],
        "family": report["family"],
        "F1": report["aggregates"].get("F1_uptime"),
        "F2": report["aggregates"].get("F2_uptime"),
        "errors": report["errors"],
    }))
    if report["verdict"] == "FINITE_MATCHED_DEGREE_BENCHMARK_INVALID":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
