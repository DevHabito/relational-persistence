"""Retrospective stratification of the *frozen* RP-U004 first-run archive.

This script was written after the original study outcome was known.
It reads archived records and never imports, executes, or edits the
original benchmark implementation. The results are descriptive, not
preregistered subgroup hypotheses or population estimates.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-U004-P01-first-run"


def read_frozen_archive(directory: Path = ARCHIVE) -> dict:
    raw = (directory / "audit.json").read_bytes()
    manifest = json.loads((directory / "archive-index.json").read_text(encoding="utf-8"))
    if sha256(raw).hexdigest() != manifest["original_audit_sha256"]:
        raise ValueError("The original audit bytes differ from the frozen manifest")
    original = json.loads(raw)
    if (original.get("protocol") != "RP-U004-P01"
            or original.get("original_run_id") != manifest.get("first_run_id")
            or original.get("verdict") != manifest.get("first_verdict")):
        raise ValueError("First-run identifiers or verdict disagree with the manifest")
    return original


def analyze(original: dict) -> dict:
    """Recount existing case outcomes without any graph-policy implementation."""
    scenarios = original["cases"]
    if not scenarios:
        raise ValueError("The original case list is empty")

    f1_differences = Counter()
    f2_differences = Counter()
    by_degree = defaultdict(lambda: {
        "scenarios": 0, "initial_F2_scenarios": 0,
        "F2_wins": 0, "F2_ties": 0, "F2_losses": 0,
        "F2_total_difference": 0,
    })
    by_initial_f2 = {
        "absent": {"scenarios": 0, "F2_wins": 0, "F2_ties": 0,
                   "F2_losses": 0, "F2_total_difference": 0},
        "present": {"scenarios": 0, "F2_wins": 0, "F2_ties": 0,
                    "F2_losses": 0, "F2_total_difference": 0},
    }
    distinct_cases = set()
    same_repair_budget_cases = 0
    same_greedy_order_cases = 0
    same_lookahead_order_cases = 0
    lookahead_at_both_offline_bounds = 0
    f2_differences_total = 0
    f1_differences_total = 0

    for case in scenarios:
        graph = tuple(tuple(edge) for edge in case["original_graph"])
        removed = case["removed_vertex"]
        identity = (graph, removed)
        if identity in distinct_cases:
            raise ValueError("Repeated scenario in original archive")
        distinct_cases.add(identity)
        score = case["policies"]
        ahead = score["LOOKAHEAD2_F2"]
        greedy = score["GREEDY_F2"]
        delta_f2 = ahead["F2_uptime"] - greedy["F2_uptime"]
        delta_f1 = (score["LOOKAHEAD2_F1"]["F1_uptime"]
                    - score["GREEDY_F1"]["F1_uptime"])
        f2_differences[delta_f2] += 1
        f1_differences[delta_f1] += 1
        f2_differences_total += delta_f2
        f1_differences_total += delta_f1
        initial_f2 = case["original_F2"]
        if initial_f2 not in (0, 1):
            raise ValueError("Invalid original F2 Boolean state")
        if initial_f2 == 0 and any(
            data["F2_uptime"] != 0
            or any(snapshot["F2"] != 0 for snapshot in data["snapshots"])
            for data in score.values()
        ):
            raise ValueError("F2 appeared under subset-only repair despite absent original F2")

        group = by_initial_f2["present" if initial_f2 else "absent"]
        degree = str(case["degree_tuple"][removed])
        degree_group = by_degree[degree]
        for bucket in (group, degree_group):
            bucket["scenarios"] += 1
            bucket["F2_total_difference"] += delta_f2
            bucket["F2_wins" if delta_f2 > 0
                   else "F2_losses" if delta_f2 < 0 else "F2_ties"] += 1
        degree_group["initial_F2_scenarios"] += initial_f2

        if score["GREEDY_F1"]["order"] == score["GREEDY_F2"]["order"]:
            same_greedy_order_cases += 1
        if score["LOOKAHEAD2_F1"]["order"] == score["LOOKAHEAD2_F2"]["order"]:
            same_lookahead_order_cases += 1
        if (ahead["F2_uptime"] == case["offline_optimum"]["F2"]
                and score["LOOKAHEAD2_F1"]["F1_uptime"] == case["offline_optimum"]["F1"]):
            lookahead_at_both_offline_bounds += 1

        budget_reference = [
            (state["node_count"], state["edge_count"], state["repaired_edges"])
            for state in score["ASC"]["snapshots"]
        ]
        for name, data in score.items():
            states = data["snapshots"]
            if len(states) != 6 or any(
                state["F2"] > state["F1"] or state["t"] != i + 1
                for i, state in enumerate(states)
            ):
                raise ValueError("Invalid snapshot function/time in " + name)
            budget = [
                (state["node_count"], state["edge_count"], state["repaired_edges"])
                for state in states
            ]
            if budget != budget_reference:
                raise ValueError("Unequal repair budgets between policies")
        same_repair_budget_cases += 1

    registered = original["aggregates"]
    if (registered["scenarios"] != len(scenarios)
            or registered["F2_uptime"]["LOOKAHEAD2_F2"]
                - registered["F2_uptime"]["GREEDY_F2"] != f2_differences_total
            or registered["F1_uptime"]["LOOKAHEAD2_F1"]
                - registered["F1_uptime"]["GREEDY_F1"] != f1_differences_total):
        raise ValueError("Casewise recount differs from original published aggregates")

    return {
        "status": "RETROSPECTIVE_DESCRIPTIVE_AUDIT_NOT_PREREGISTERED_HYPOTHESIS",
        "original_run_id": original["original_run_id"],
        "original_verdict": original["verdict"],
        "scenarios": len(scenarios),
        "F1_case_differences": dict(sorted(f1_differences.items())),
        "F2_case_differences": dict(sorted(f2_differences.items())),
        "F1_total_difference": f1_differences_total,
        "F2_total_difference": f2_differences_total,
        "F2_by_original_failed_vertex_degree": dict(sorted(by_degree.items(), key=lambda kv: int(kv[0]))),
        "F2_by_initial_function": by_initial_f2,
        "equal_repair_budget_cases": same_repair_budget_cases,
        "greedy_objective_orders_identical_cases": same_greedy_order_cases,
        "lookahead_objective_orders_identical_cases": same_lookahead_order_cases,
        "lookahead_at_both_reported_offline_bounds": lookahead_at_both_offline_bounds,
        "observed_real_world_rows": original["physical_data_rows"],
        "new_preregistered_hypothesis": False,
        "new_lean_theorem_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    report = analyze(read_frozen_archive(args.archive))
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
