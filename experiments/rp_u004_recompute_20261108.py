"""Independent, retrospective RP-U004 source and policy reconstruction.

No imports from the research package's scorer or archived outcome files.
The published synthetic model and decision policies are known in advance of
this retrospective audit. This is not a blinded, physical, or new experiment.
"""
from collections import Counter, defaultdict, deque
from hashlib import sha256
from itertools import combinations, permutations
import json
import time

INNER = (1, 2, 3, 4, 5)
TERMINALS = (0, 6)
MIDDLE_EDGES = tuple(combinations(INNER, 2))


def source_graphs():
    graphs = []
    for src in combinations(INNER, 2):
        for dst in combinations(INNER, 2):
            for middle in combinations(MIDDLE_EDGES, 4):
                edges = tuple(sorted(
                    [(0, v) for v in src]
                    + [(v, 6) for v in dst] + list(middle)
                ))
                parent = list(range(7))

                def root(vertex):
                    while parent[vertex] != vertex:
                        vertex = parent[vertex]
                    return vertex

                for a, b in edges:
                    parent[root(a)] = root(b)
                if len({root(v) for v in range(7)}) == 1:
                    graphs.append(edges)
    return tuple(sorted(graphs))


def degree_vector(edges):
    result = [0] * 7
    for a, b in edges:
        result[a] += 1
        result[b] += 1
    return tuple(result)


def family_digest(graphs):
    digest = sha256()
    for graph in graphs:
        digest.update((json.dumps(graph, separators=(",", ":")) + "\n").encode())
    return digest.hexdigest()


def reaches(adjacency, excluded=None):
    queue = deque([0])
    visited = {0}
    while queue:
        current = queue.popleft()
        if current == 6:
            return True
        for other in adjacency[current]:
            if other != excluded and other not in visited:
                visited.add(other)
                queue.append(other)
    return False


def path_masks(adjacency):
    stack = [(0, (0,), 0)]
    while stack:
        current, visited, mask = stack.pop()
        if current == 6:
            yield mask
            continue
        for next_node in adjacency[current]:
            if next_node not in visited:
                next_mask = mask | (1 << next_node if next_node != 6 else 0)
                stack.append((next_node, visited + (next_node,), next_mask))


def function_pair(edges, active_nodes):
    adjacency = {vertex: set() for vertex in active_nodes}
    for a, b in edges:
        assert a in adjacency and b in adjacency
        adjacency[a].add(b)
        adjacency[b].add(a)
    one_route_bfs = reaches(adjacency)
    paths = tuple(path_masks(adjacency))
    assert one_route_bfs == bool(paths), "Independent F1 oracles differ"
    two_routes_paths = any(
        not (first & second)
        for index, first in enumerate(paths)
        for second in paths[index + 1:]
    )
    two_routes_cut = one_route_bfs and all(
        reaches(adjacency, removed)
        for removed in active_nodes if removed not in TERMINALS
    )
    assert two_routes_paths == two_routes_cut, "Independent F2 oracles differ"
    return int(one_route_bfs), int(two_routes_paths)


def case_function_table(graph, lost):
    neighbors = tuple(sorted(
        b if a == lost else a for a, b in graph if lost in (a, b)
    ))
    remaining_edges = tuple(edge for edge in graph if lost not in edge)
    remaining_nodes = set(range(7)) - {lost}
    initial_score = function_pair(remaining_edges, remaining_nodes)
    replacement = 7 + lost
    table = {}
    for length in range(len(neighbors) + 1):
        for subset in combinations(neighbors, length):
            additions = tuple(
                (min(replacement, v), max(replacement, v)) for v in subset
            )
            table[frozenset(subset)] = function_pair(
                remaining_edges + additions, remaining_nodes | {replacement}
            )
    assert table[frozenset()] == initial_score
    assert len(table) == 2 ** len(neighbors)
    return neighbors, table, initial_score


def priority(score, policy):
    return score if policy.endswith("F1") else score[::-1]


def repair_order(policy, graph, neighbors, table):
    degrees = degree_vector(graph)
    restored = []
    lookups = 5  # Recorded outcome reads at post-failure ticks 2..6.
    comparisons = 0
    while len(restored) < len(neighbors):
        choices = [v for v in neighbors if v not in restored]
        if policy == "ASC":
            winner = min(choices)
        elif policy == "DEGREE":
            winner = min(choices, key=lambda v: (-degrees[v], v))
        else:
            ranked = []
            for candidate in choices:
                subset = frozenset(restored + [candidate])
                immediate = priority(table[subset], policy)
                lookups += 1
                if policy.startswith("LOOKAHEAD2"):
                    future_choices = [v for v in choices if v != candidate]
                    if future_choices:
                        future = max(
                            priority(table[subset | {v}], policy)
                            for v in future_choices
                        )
                        lookups += len(future_choices)
                    else:
                        future = immediate
                    merit = future + immediate
                else:
                    merit = immediate
                comparisons += 1
                ranked.append((merit, -candidate, candidate))
            winner = max(ranked)[-1]
        restored.append(winner)
    return tuple(restored), lookups, comparisons


def uptime(order, table, initial):
    first, second = initial
    for tick in range(2, 7):
        state = table[frozenset(order[:min(len(order), tick - 1)])]
        first += state[0]
        second += state[1]
    return first, second


def recompute():
    graphs = source_graphs()
    by_degree = defaultdict(list)
    for graph in graphs:
        by_degree[degree_vector(graph)].append(graph)
    chosen = tuple(
        graph for _, members in sorted(by_degree.items())
        if len(members) > 1
        for graph in (min(members), max(members))
    )
    policies = (
        "ASC", "DEGREE", "GREEDY_F1", "GREEDY_F2",
        "LOOKAHEAD2_F1", "LOOKAHEAD2_F2",
    )
    totals = {policy: [0, 0, 0, 0] for policy in policies}
    differences = Counter()
    winnings_by_degree = Counter()
    offline_f1 = offline_f2 = table_entries = 0
    original_f2_graphs = 0

    for graph in chosen:
        original_f2 = function_pair(graph, set(range(7)))[1]
        original_f2_graphs += original_f2
        for lost in INNER:
            neighbors, table, initial = case_function_table(graph, lost)
            table_entries += len(table)
            offline_scores = [
                uptime(order, table, initial)
                for order in permutations(neighbors)
            ]
            offline_f1 += max(score[0] for score in offline_scores)
            offline_f2 += max(score[1] for score in offline_scores)
            outcomes = {}
            for policy in policies:
                order, lookups, comparisons = repair_order(
                    policy, graph, neighbors, table
                )
                f1, f2 = uptime(order, table, initial)
                outcomes[policy] = (order, f1, f2)
                sums = totals[policy]
                sums[0] += f1
                sums[1] += f2
                sums[2] += lookups
                sums[3] += comparisons

            assert outcomes["GREEDY_F1"][0] == outcomes["GREEDY_F2"][0]
            assert outcomes["LOOKAHEAD2_F1"][0] == outcomes["LOOKAHEAD2_F2"][0]
            delta_f2 = outcomes["LOOKAHEAD2_F2"][2] - outcomes["GREEDY_F2"][2]
            delta_f1 = outcomes["LOOKAHEAD2_F1"][1] - outcomes["GREEDY_F1"][1]
            differences[("F2", delta_f2)] += 1
            differences[("F1", delta_f1)] += 1
            if delta_f2 > 0:
                winnings_by_degree[degree_vector(graph)[lost]] += 1
            assert original_f2 or delta_f2 == 0

    return {
        "source_count": len(graphs),
        "strata_count": len(by_degree),
        "singleton_strata": sum(len(v) == 1 for v in by_degree.values()),
        "paired_strata": sum(len(v) > 1 for v in by_degree.values()),
        "source_digest": family_digest(graphs),
        "chosen_digest": family_digest(chosen),
        "chosen_graphs": len(chosen),
        "failure_cases": len(chosen) * len(INNER),
        "original_F2_graphs": original_f2_graphs,
        "subset_function_table_entries": table_entries,
        "policies": totals,
        "offline_F1_sum": offline_f1,
        "offline_F2_sum": offline_f2,
        "case_differences": {
            f"{metric}_{delta}": count
            for (metric, delta), count in sorted(differences.items())
        },
        "F2_winning_cases_by_degree": dict(winnings_by_degree),
    }


def main():
    started = time.perf_counter()
    report = recompute()
    report["local_elapsed_seconds"] = round(time.perf_counter() - started, 3)
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
