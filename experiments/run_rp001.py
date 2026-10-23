"""Run frozen protocol RP-001 and write results without fitting parameters."""

import json
import platform
from pathlib import Path

import networkx as nx
import numpy as np

from relational_persistence.consensus import (
    ar1_variance_state,
    evaluate_consensus,
    matrix_power_residual,
    scalar_capacity_noise_latency_index,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "results" / "RP-001.json"


def main() -> None:
    path = nx.path_graph(6)
    star = nx.star_graph(5)
    alpha = 0.1
    horizon = 20
    noise = 0.01
    common_index = scalar_capacity_noise_latency_index(1.0, noise, 1.0)

    a = evaluate_consensus(path, alpha=alpha, horizon=horizon, noise_variance=noise)
    b = evaluate_consensus(star, alpha=alpha, horizon=horizon, noise_variance=noise)
    difference = a.residual_at_horizon - b.residual_at_horizon
    independent_error = max(
        abs(a.residual_at_horizon - matrix_power_residual(path, alpha=alpha, horizon=horizon)),
        abs(b.residual_at_horizon - matrix_power_residual(star, alpha=alpha, horizon=horizon)),
    )
    if independent_error >= 1e-10:
        raise RuntimeError("Independent matrix-power check did not agree")
    if a.nodes != b.nodes or a.edges != b.edges:
        raise RuntimeError("The preregistered graph matching assumptions did not hold")

    decision = (
        "Y: scalar sufficiency fails in this declared dynamical class"
        if abs(difference) >= 0.05
        else "X: no challenge resolved at the preregistered threshold"
    )
    data = {
        "protocol": "RP-001",
        "preregistration_tag": "rp-001-preregistered",
        "method": "spectral calculation with independent matrix-power regression check",
        "index_same_on_both_graphs": common_index,
        "path": a.to_dict(),
        "star": b.to_dict(),
        "path_minus_star_residual": difference,
        "threshold": 0.05,
        "decision": decision,
        "max_independent_check_error": independent_error,
        "separate_ar1_counterexample": {
            "coefficient_0_5": ar1_variance_state(coefficient=0.5, noise_variance=noise),
            "coefficient_1_1": ar1_variance_state(coefficient=1.1, noise_variance=noise),
            "interpretation": "same external index proxies; different variance stability",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "networkx": nx.__version__,
        },
        "limitations": [
            "The networks and dynamics are constructed, not experimentally measured.",
            "The spectral calculation establishes known linear-consensus behavior, not novelty.",
            "The index is an operational proposal, not an independently calibrated stability law.",
        ],
    }
    OUTPUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "difference": difference, "result_path": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
