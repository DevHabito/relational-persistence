"""RP-U003-A01: exhaustive labeled six-vertex equal-edge-budget repair policies.

Frozen original protocol on main at 5cb8d3a BEFORE source implementation.
Every graph within a fixed 7-edge and terminal-degree-two family is included.
No field observations, adaptive policy training, stochastic sampling or law.
"""

from __future__ import annotations

from collections import Counter, deque
from hashlib import sha256
from itertools import combinations
import argparse
import json
import os
from pathlib import Path

PROTOCOL = "RP-U003-A01"
PREREG = "5cb8d3af473aa95848ab22d5ecc591c5a1567a00"
BASE_NODES = frozenset(range(6))
INTERNAL = (1, 2, 3, 4)
SOURCE, TARGET = 0, 5
TIMES = tuple(range(7))
POLICIES = ("ASC", "DEGREE", "GREEDY1", "LOOKAHEAD2")
PAIRS = tuple((u, v) for u in range(6) for v in range(u + 1, 6)
              if (u, v) != (SOURCE, TARGET))


def edge(u: int, v: int) -> tuple[int, int]:
    if u == v:
        raise AssertionError("Source is a simple graph: no self loops")
    return (u, v) if u < v else (v, u)


def adjacency(edges: frozenset[tuple[int, int]], nodes: frozenset[int]):
    links = {node: set() for node in nodes}
    for a, b in edges:
        if a not in nodes or b not in nodes:
            raise AssertionError("Dangling edge in current network")
        links[a].add(b)
        links[b].add(a)
    return links


def connected_bfs(edges, nodes, start: int, destination: int,
                  excluded: int | None = None) -> bool:
    available = nodes - ({excluded} if excluded is not None else set())
    if start not in available or destination not in available:
        return False
    links = adjacency(
        frozenset((u, v) for u, v in edges if u in available and v in available),
        frozenset(available),
    )
    pending = deque([start])
    seen = {start}
    while pending:
        current = pending.popleft()
        if current == destination:
            return True
        for nxt in links[current]:
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return False


def all_simple_paths(edges, nodes, start=SOURCE, target=TARGET):
    """Independent DFS: does not call BFS or shared adjacency builder."""
    if start not in nodes or target not in nodes:
        return ()
    result = []
    def visit(path):
        last = path[-1]
        if last == target:
            result.append(tuple(path))
            return
        for possible in sorted(nodes):
            if possible in path:
                continue
            if edge(last, possible) in edges:
                visit(path + [possible])
    visit([start])
    return tuple(result)


def functions(edges, nodes):
    """Two separate exact oracles EACH for F1 and F2."""
    if edge(SOURCE, TARGET) in edges:
        raise AssertionError("Direct terminal link is forbidden by source filter")
    f1_bfs = connected_bfs(edges, nodes, SOURCE, TARGET)
    paths = all_simple_paths(edges, nodes)
    f1_dfs = bool(paths)
    if f1_bfs != f1_dfs:
        raise AssertionError("Independent BFS and simple DFS disagree")
    f2_paths = any(
        set(first[1:-1]).isdisjoint(second[1:-1])
        for i, first in enumerate(paths) for second in paths[i + 1:]
    )
    f2_cuts = (f1_bfs and all(
        connected_bfs(edges, nodes, SOURCE, TARGET, excluded=internal)
        for internal in nodes - {SOURCE, TARGET}
    ))
    if f2_paths != f2_cuts or (f2_paths and not f1_bfs):
        raise AssertionError("Independent disjoint paths and vertex-cut check disagree")
    return int(f1_bfs), int(f2_paths)


def source_valid(edges) -> bool:
    graph = frozenset(edges)
    if (len(graph) != 7 or edge(SOURCE, TARGET) in graph
            or sum(SOURCE in e for e in graph) != 2
            or sum(TARGET in e for e in graph) != 2):
        return False
    return all(connected_bfs(graph, BASE_NODES, SOURCE, v)
               for v in BASE_NODES)


def independent_source_valid(edges) -> bool:
    """Different source-family validator, uses DFS and degree count."""
    if len(edges) != 7 or edge(SOURCE, TARGET) in edges:
        return False
    degrees = {node: 0 for node in BASE_NODES}
    for u, v in edges:
        degrees[u] += 1
        degrees[v] += 1
    if degrees[SOURCE] != 2 or degrees[TARGET] != 2:
        return False
    if not all(degrees[v] > 0 for v in BASE_NODES):
        return False
    # Original topology must be connected across ALL nodes, not only s->t.
    frontier = {SOURCE}
    while True:
        expanded = frontier | {
            v for u, v in edges if u in frontier
        } | {
            u for u, v in edges if v in frontier
        }
        if expanded == frontier:
            return expanded == BASE_NODES
        frontier = expanded


def all_registered_graphs():
    method_a = tuple(
        tuple(graph) for graph in combinations(PAIRS, 7)
        if source_valid(graph)
    )
    method_b = tuple(sorted(
        tuple(PAIRS[index] for index in range(len(PAIRS))
              if mask & (1 << index))
        for mask in range(1 << len(PAIRS))
        if mask.bit_count() == 7
        and independent_source_valid(tuple(
            PAIRS[index] for index in range(len(PAIRS))
            if mask & (1 << index)
        ))
    ))
    if not method_a or method_a != method_b:
        raise AssertionError("Two independent graph enumerations disagree or are empty")
    if len(method_a) != len(set(method_a)):
        raise AssertionError("Labeled graph duplicated by generator")
    return method_a


def original_degrees(base):
    return {v: sum(v in e for e in base) for v in BASE_NODES}


def old_neighbors(base, lost):
    if lost not in INTERNAL:
        raise AssertionError("Unregistered failed component")
    return tuple(sorted(other for u, v in base if lost in (u, v)
                        for other in (u, v) if other != lost))


def direct_snapshot(base, lost, restored):
    """Builder A: original edge filtering, then repaired neighbor subset."""
    old = set(old_neighbors(base, lost))
    if not set(restored) <= old or len(restored) != len(set(restored)):
        raise AssertionError("Unregistered edge or duplicate repaired neighbor")
    remaining = frozenset(e for e in base if lost not in e)
    nodes = BASE_NODES - {lost}
    if restored:
        nodes = nodes | {6 + lost}
    added = frozenset(edge(6 + lost, node) for node in restored)
    return remaining | added, frozenset(nodes)


def snapshot(base, lost, restored, *, t):
    """t2 has a NEW node even if no source edge is attached (impossible if d>=1)."""
    fixed_edges = frozenset(e for e in base if lost not in e)
    nodes = BASE_NODES - {lost}
    if t == 0:
        return frozenset(base), BASE_NODES
    if t == 1:
        return fixed_edges, frozenset(nodes)
    if t < 2 or t > 6:
        raise AssertionError("Time not part of registered horizon")
    nodes |= {6 + lost}
    return fixed_edges | frozenset(edge(6 + lost, v) for v in restored), frozenset(nodes)


def build_by_events(base, lost, sequence):
    """Builder B: event replay, distinct from filtering a chosen prefix."""
    current_nodes = set(BASE_NODES)
    current_edges = set(base)
    steps = [(frozenset(current_edges), frozenset(current_nodes))]
    current_nodes.remove(lost)
    current_edges = {e for e in current_edges if lost not in e}
    steps.append((frozenset(current_edges), frozenset(current_nodes)))
    for t in range(2, 7):
        if t == 2:
            current_nodes.add(6 + lost)
        if t-2 < len(sequence):
            current_edges.add(edge(6 + lost, sequence[t-2]))
        steps.append((frozenset(current_edges), frozenset(current_nodes)))
    return steps


def evaluate_current(base, lost, restored):
    """Connected-function evaluation with replacement node now present."""
    fixed = frozenset(e for e in base if lost not in e)
    edges = fixed | frozenset(edge(6 + lost, v) for v in restored)
    return functions(edges, frozenset(BASE_NODES - {lost} | {6 + lost}))


def policy_order(base, lost, policy):
    """Actions planned sequentially. Only known ORIGINAL topology is read."""
    neighbors = old_neighbors(base, lost)
    degrees = original_degrees(base)
    evaluations = 0
    if policy == "ASC":
        return neighbors, evaluations
    if policy == "DEGREE":
        return tuple(sorted(neighbors, key=lambda v: (-degrees[v], v))), evaluations
    if policy not in ("GREEDY1", "LOOKAHEAD2"):
        raise AssertionError("Unknown policy name")
    chosen = []
    while len(chosen) < len(neighbors):
        available = [v for v in neighbors if v not in chosen]
        candidates = []
        for candidate in available:
            possible = tuple(chosen + [candidate])
            now = evaluate_current(base, lost, possible)
            evaluations += 1
            if policy == "GREEDY1":
                merit = now
            else:
                remaining = [v for v in available if v != candidate]
                if remaining:
                    alternatives = []
                    for future in remaining:
                        alternatives.append(
                            evaluate_current(base, lost, possible + (future,))
                        )
                        evaluations += 1
                    future_merit = max(alternatives)
                else:
                    future_merit = now
                merit = future_merit + now
            candidates.append((merit, -candidate, candidate))
        chosen.append(max(candidates)[2])
    return tuple(chosen), evaluations


def trace_for_policy(base, lost, policy):
    order, evaluations = policy_order(base, lost, policy)
    known = old_neighbors(base, lost)
    if len(order) != len(known) or set(order) != set(known):
        raise AssertionError("Policy did not restore precisely original neighbors")
    replay = build_by_events(base, lost, order)
    records = []
    for t in TIMES:
        expected_restored = order[:min(max(t - 1, 0), len(known))]
        if t == 0:
            direct = frozenset(base), BASE_NODES
        elif t == 1:
            direct = frozenset(e for e in base if lost not in e), frozenset(BASE_NODES - {lost})
        else:
            direct = snapshot(base, lost, expected_restored, t=t)
        if replay[t] != direct:
            raise AssertionError("Event replay and direct snapshot disagree")
        edges, nodes = replay[t]
        if any(u not in nodes or v not in nodes for u, v in edges):
            raise AssertionError("Dangling edge attached to a nonpresent node")
        if t >= 1 and lost in nodes:
            raise AssertionError("Old failed identity unexpectedly returned")
        if t >= 2 and (6 + lost) not in nodes:
            raise AssertionError("Replacement identity never appeared")
        expected_nodes = 6 if t == 0 or t >= 2 else 5
        expected_edges = 7 if t == 0 else 7 - len(known) + len(expected_restored)
        if len(nodes) != expected_nodes or len(edges) != expected_edges:
            raise AssertionError("Cost/time/state budget violated")
        f1, f2 = functions(edges, nodes)
        records.append({
            "t": t, "node_count": len(nodes), "edge_count": len(edges),
            "cumulative_repaired_edges": len(expected_restored),
            "F1": f1, "F2": f2,
        })
    return {
        "order": list(order),
        "candidate_function_evaluations": evaluations,
        "post_failure_F1": sum(s["F1"] for s in records[1:]),
        "post_failure_F2": sum(s["F2"] for s in records[1:]),
        "snapshots": records,
    }


def offline_envelope(base, lost):
    neighbors = old_neighbors(base, lost)
    values = []
    for t in TIMES:
        budget = min(max(t - 1, 0), len(neighbors))
        if t == 0:
            f1, f2 = functions(frozenset(base), BASE_NODES)
        elif t == 1:
            remaining = frozenset(e for e in base if lost not in e)
            f1, f2 = functions(remaining, frozenset(BASE_NODES - {lost}))
        else:
            scores = [
                evaluate_current(base, lost, subset)
                for subset in combinations(neighbors, budget)
            ]
            if not scores:
                raise AssertionError("Missing offline subset")
            f1 = max(row[0] for row in scores)
            f2 = max(row[1] for row in scores)
        values.append({"t": t, "F1": f1, "F2": f2})
    return values


def _normal_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def audit():
    report = {
        "protocol": PROTOCOL,
        "preregistration_commit": PREREG,
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "original_code_commit": os.environ.get("GITHUB_SHA"),
        "verdict": "FINITE_BENCHMARK_INVALID",
        "scope": "complete finite labeled graph ensemble, synthetic fixed repair and equal edge budget",
        "real_domain_records_used": 0,
        "new_lean_theorem_or_universal_law_claimed": False,
        "all_case_records": [],
        "family": {},
        "aggregates": {},
        "comparisons": {},
        "errors": [],
    }
    try:
        networks = all_registered_graphs()
        family_blob = "".join(_normal_json(graph) + "\n" for graph in networks).encode()
        report["family"] = {
            "accepted_labeled_graphs": len(networks),
            "all_14_candidate_edges_choose_seven_covered": True,
            "labeled_family_sha256": sha256(family_blob).hexdigest(),
            "degree_multiset_counts": dict(sorted(Counter(
                str(tuple(sorted(original_degrees(graph).values())))
                for graph in networks
            ).items())),
            "terminal_degree_two_and_no_direct_edge": True,
            "all_six_vertices_source_connected": True,
            "independent_enumerators_agree": True,
        }
        uptime_f1 = Counter()
        uptime_f2 = Counter()
        computations = Counter()
        comparisons = Counter()
        degree_strata = {}
        totals_offline_f1 = 0
        totals_offline_f2 = 0
        loss_examples = []
        for graph_index, graph in enumerate(networks):
            for lost in INTERNAL:
                scenario = {
                    "graph_index": graph_index,
                    "original_graph_edges": [list(e) for e in graph],
                    "lost_vertex": lost,
                    "original_degree_of_lost_vertex": len(old_neighbors(graph, lost)),
                    "policies": {},
                }
                offline = offline_envelope(graph, lost)
                scenario["offline_F1_by_t"] = [row["F1"] for row in offline]
                scenario["offline_F2_by_t"] = [row["F2"] for row in offline]
                totals_offline_f1 += sum(row["F1"] for row in offline[1:])
                totals_offline_f2 += sum(row["F2"] for row in offline[1:])
                base_costs = None
                for policy in POLICIES:
                    record = trace_for_policy(graph, lost, policy)
                    current_costs = [
                        (s["node_count"], s["edge_count"],
                         s["cumulative_repaired_edges"])
                        for s in record["snapshots"]
                    ]
                    if base_costs is None:
                        base_costs = current_costs
                    elif base_costs != current_costs:
                        raise AssertionError("Policies do not use same time/edge/node budget")
                    for actual, bound in zip(record["snapshots"], offline):
                        if actual["F1"] > bound["F1"] or actual["F2"] > bound["F2"]:
                            raise AssertionError("Deployable rule exceeds exhaustive upper bound")
                    scenario["policies"][policy] = record
                    uptime_f1[policy] += record["post_failure_F1"]
                    uptime_f2[policy] += record["post_failure_F2"]
                    computations[policy] += record["candidate_function_evaluations"]
                lookahead = scenario["policies"]["LOOKAHEAD2"]["post_failure_F1"]
                for simpler in ("ASC", "DEGREE", "GREEDY1"):
                    baseline = scenario["policies"][simpler]["post_failure_F1"]
                    comparisons[f"lookahead_{'win' if lookahead > baseline else 'loss' if lookahead < baseline else 'tie'}_vs_{simpler}"] += 1
                if any(lookahead < scenario["policies"][rule]["post_failure_F1"]
                       for rule in ("ASC", "DEGREE", "GREEDY1")):
                    comparisons["lookahead_any_case_loss"] += 1
                    if len(loss_examples) < 5:
                        loss_examples.append({
                            "graph_index": graph_index, "lost": lost,
                            "F1_score_by_policy": {
                                p: r["post_failure_F1"]
                                for p, r in scenario["policies"].items()
                            },
                        })
                stratum = str(tuple(sorted(original_degrees(graph).values())))
                if stratum not in degree_strata:
                    degree_strata[stratum] = Counter()
                for p in POLICIES:
                    degree_strata[stratum][f"F1_{p}"] += scenario["policies"][p]["post_failure_F1"]
                degree_strata[stratum]["cases"] += 1
                report["all_case_records"].append(scenario)
        if len(report["all_case_records"]) != 4 * len(networks):
            raise AssertionError("Not all 4N graph/failed-vertex scenarios were evaluated")
        denominator = 6 * len(report["all_case_records"])
        report["aggregates"] = {
            "post_failure_model_time_steps_per_policy": denominator,
            "F1_uptime_case_ticks": dict(sorted(uptime_f1.items())),
            "F2_uptime_case_ticks": dict(sorted(uptime_f2.items())),
            "F1_offline_optimal_envelope_case_ticks": totals_offline_f1,
            "F2_offline_optimal_envelope_case_ticks": totals_offline_f2,
            "F1_regret_to_offline_envelope": {
                p: totals_offline_f1 - uptime_f1[p] for p in POLICIES
            },
            "F2_regret_to_offline_envelope": {
                p: totals_offline_f2 - uptime_f2[p] for p in POLICIES
            },
            "total_candidate_function_evaluations_not_equivalent_CPU_cost": dict(
                sorted(computations.items())),
            "degree_sequence_strata": {
                name: dict(sorted(counts.items()))
                for name, counts in sorted(degree_strata.items())
            },
        }
        report["comparisons"] = {
            **dict(sorted(comparisons.items())),
            "first_five_synthetic_losses_deterministic_order": loss_examples,
            "directional_H1_strict_gain_over_ASC": uptime_f1["LOOKAHEAD2"] > uptime_f1["ASC"],
            "directional_H1_strict_gain_over_DEGREE": uptime_f1["LOOKAHEAD2"] > uptime_f1["DEGREE"],
            "equal_repair_budget_verified_for_all_policy_scenario_times": True,
        }
        report["all_cases_json_sha256"] = sha256(
            "".join(_normal_json(row) + "\n"
                    for row in report["all_case_records"]).encode()
        ).hexdigest()
        report["verdict"] = (
            "FINITE_BENCHMARK_LOOKAHEAD_F1_ADVANTAGE_SUPPORTED"
            if (report["comparisons"]["directional_H1_strict_gain_over_ASC"]
                and report["comparisons"]["directional_H1_strict_gain_over_DEGREE"])
            else "REGISTERED_LOOKAHEAD_F1_ADVANTAGE_NOT_SUPPORTED"
        )
    except (AssertionError, ValueError, TypeError) as exc:
        report["errors"].append({"reason": f"{type(exc).__name__}: {str(exc)[:400]}"})
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing overwrite of RP-U003 first original result")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    original = audit()
    args.output.write_text(
        json.dumps(original, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "protocol": PROTOCOL, "decision": original["verdict"],
        "N": original["family"].get("accepted_labeled_graphs"),
        "F1": original["aggregates"].get("F1_uptime_case_ticks"),
        "F2": original["aggregates"].get("F2_uptime_case_ticks"),
        "errors": original["errors"]
    }, sort_keys=True))
    if original["verdict"] == "FINITE_BENCHMARK_INVALID":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
