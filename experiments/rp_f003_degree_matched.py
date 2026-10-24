"""Exhaustive, exact integer-matrix test for preregistered RP-F003-A01."""

from __future__ import annotations

from fractions import Fraction
import json

N = 6
T = 20
SCALE = 10
DENOMINATOR = (N - 1) * SCALE ** (2 * T)
EDGES = tuple((i, j) for i in range(N) for j in range(i + 1, N))


def edges_of(mask: int) -> tuple[tuple[int, int], ...]:
    if not isinstance(mask, int) or not (0 <= mask < (1 << len(EDGES))):
        raise ValueError("Six-vertex edge mask required")
    return tuple(edge for bit, edge in enumerate(EDGES) if mask & (1 << bit))


def graph_data(mask: int, vertex_count: int = N) -> tuple[bool, tuple[int, ...], tuple[tuple[int, ...], ...]]:
    if vertex_count != N:
        raise ValueError("Only the preregistered six-vertex domain is supported")
    adjacency = [[0] * N for _ in range(N)]
    for i, j in edges_of(mask):
        adjacency[i][j] = adjacency[j][i] = 1
    degrees = tuple(sum(row) for row in adjacency)
    seen = {0}
    stack = [0]
    while stack:
        vertex = stack.pop()
        for neighbor in range(N):
            if adjacency[vertex][neighbor] and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    matrix = tuple(
        tuple((SCALE - degrees[i] if i == j else adjacency[i][j]) for j in range(N))
        for i in range(N)
    )
    return len(seen) == N, tuple(sorted(degrees)), matrix


def audit_matrix(
    matrix: tuple[tuple[int, ...], ...], edges: tuple[tuple[int, int], ...]
) -> None:
    if len(matrix) != N or any(len(row) != N for row in matrix):
        raise ValueError("Malformed matrix dimension")
    for i in range(N):
        if sum(matrix[i]) != SCALE:
            raise ValueError("Row-sum conservation violated")
        if matrix[i][i] != SCALE - sum(i in edge for edge in edges):
            raise ValueError("Incorrect degree or diagonal")
        for j in range(N):
            if matrix[i][j] != matrix[j][i]:
                raise ValueError("Matrix is not symmetric")
            if i != j and matrix[i][j] != int(tuple(sorted((i, j))) in edges):
                raise ValueError("Adjacency does not match edge mask")


def require_matched_degrees(first: int, second: int) -> None:
    first_connected, first_signature, _ = graph_data(first)
    second_connected, second_signature, _ = graph_data(second)
    if not first_connected or not second_connected or first_signature != second_signature:
        raise ValueError("Connected graphs with the same sorted degree sequence are required")


def multiply(
    a: tuple[tuple[int, ...], ...], b: tuple[tuple[int, ...], ...]
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(N)) for j in range(N))
        for i in range(N)
    )


def energy_numerator(matrix: tuple[tuple[int, ...], ...]) -> int:
    m2 = multiply(matrix, matrix)
    m4 = multiply(m2, m2)
    m8 = multiply(m4, m4)
    m16 = multiply(m8, m8)
    m20 = multiply(m16, m4)
    numerator = sum(value * value for row in m20 for value in row) - SCALE ** (2 * T)
    if numerator < 0:
        raise AssertionError("Nonnegative disagreement energy violated")
    return numerator


def independently_multiply(
    a: tuple[tuple[int, ...], ...], b: tuple[tuple[int, ...], ...]
) -> tuple[tuple[int, ...], ...]:
    output = [[0] * N for _ in range(N)]
    for i in range(N):
        for k in range(N):
            for j in range(N):
                output[i][j] += a[i][k] * b[k][j]
    return tuple(tuple(row) for row in output)


def trace_power_40(matrix: tuple[tuple[int, ...], ...]) -> int:
    result = tuple(tuple(int(i == j) for j in range(N)) for i in range(N))
    remaining = 2 * T
    power = matrix
    while remaining:
        if remaining & 1:
            result = independently_multiply(result, power)
        remaining >>= 1
        if remaining:
            power = independently_multiply(power, power)
    return sum(result[i][i] for i in range(N))


def relabel_reverse(mask: int) -> int:
    lookup = {edge: bit for bit, edge in enumerate(EDGES)}
    new_mask = 0
    for i, j in edges_of(mask):
        new_mask |= 1 << lookup[tuple(sorted((N - 1 - i, N - 1 - j)))]
    return new_mask


def compute() -> dict:
    groups: dict[tuple[int, ...], dict] = {}
    connected_count = 0
    for mask in range(1 << len(EDGES)):
        connected, signature, matrix = graph_data(mask)
        if not connected:
            continue
        connected_count += 1
        audit_matrix(matrix, edges_of(mask))
        numerator = energy_numerator(matrix)
        state = groups.get(signature)
        if state is None:
            groups[signature] = dict(
                count=1, min_num=numerator, min_mask=mask,
                max_num=numerator, max_mask=mask
            )
        else:
            state["count"] += 1
            if numerator < state["min_num"]:
                state["min_num"], state["min_mask"] = numerator, mask
            if numerator > state["max_num"]:
                state["max_num"], state["max_mask"] = numerator, mask

    best = None
    for signature, state in groups.items():
        if state["count"] < 2:
            continue
        delta = state["max_num"] - state["min_num"]
        masks = tuple(sorted((state["min_mask"], state["max_mask"])))
        if best is None or delta > best[0] or (delta == best[0] and masks < best[1]):
            best = (delta, masks, signature)
    if best is None:
        raise AssertionError("No candidate degree-sequence group")
    delta, masks, signature = best
    require_matched_degrees(*masks)

    measurements = []
    for mask in masks:
        _, found_signature, matrix = graph_data(mask)
        assert found_signature == signature
        numerator = energy_numerator(matrix)
        assert numerator + SCALE ** (2 * T) == trace_power_40(matrix)
        reversed_mask = relabel_reverse(mask)
        _, reversed_signature, reversed_matrix = graph_data(reversed_mask)
        assert reversed_signature == signature
        assert energy_numerator(reversed_matrix) == numerator
        frac = Fraction(numerator, DENOMINATOR)
        measurements.append(dict(
            mask=mask, edges=edges_of(mask), numerator=numerator,
            q20=f"{frac.numerator}/{frac.denominator}",
            approximation=float(frac), reversed_mask=reversed_mask
        ))

    exact_delta = Fraction(delta, DENOMINATOR)
    complete_mask = (1 << len(EDGES)) - 1
    assert Fraction(energy_numerator(graph_data(complete_mask)[2]), DENOMINATOR) == Fraction(2, 5) ** (2 * T)
    assert Fraction(energy_numerator(graph_data(0)[2]), DENOMINATOR) == 1
    assert connected_count > 0
    return dict(
        protocol="RP-F003-A01", vertex_count=N,
        edge_masks_evaluated=(1 << len(EDGES)),
        connected_masks=connected_count,
        degree_signature_count=len(groups),
        candidate_groups=sum(s["count"] >= 2 for s in groups.values()),
        degree_group_sizes={
            ",".join(map(str, sig)): v["count"] for sig, v in sorted(groups.items())
        },
        exact_denominator=DENOMINATOR,
        chosen_degree_sequence=signature,
        selected_graphs=measurements,
        delta_numerator=delta,
        delta_fraction=f"{exact_delta.numerator}/{exact_delta.denominator}",
        delta_approximation=float(exact_delta),
        declared_threshold="1/100",
        decision=("PASS_EQUAL_DEGREES_INSUFFICIENT"
                  if delta * 100 >= DENOMINATOR
                  else "NO_REGISTERED_SEPARATION_AT_N6"),
        non_empirical=True
    )


if __name__ == "__main__":
    print(json.dumps(compute(), indent=2))
