"""Exploratory real observed network topology; dynamics are synthetic."""

import json
from pathlib import Path

import networkx as nx

from relational_persistence.consensus import evaluate_consensus


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "results" / "KARATE-EXPLORATORY.json"


def main() -> None:
    observed_graph = nx.karate_club_graph()
    # Unweighted, synthetic linear dynamics, not observed participant behavior.
    evaluation = evaluate_consensus(
        observed_graph, alpha=0.04, horizon=20, noise_variance=0.01
    )
    result = {
        "name": "Zachary karate club (observed network topology)",
        "source": "Zachary (1977), DOI: 10.1086/jar.33.4.3629752",
        "source_implementation": "networkx.karate_club_graph() (built-in dataset)",
        "experimental_status": "exploratory; not preregistered",
        "measurement_boundary": "Real observed ties; consensus dynamics/noise hypothetical.",
        "weights": "Ignored; adjacency is unweighted.",
        "results": evaluation.to_dict(),
        "physical_validation": False,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"observed_nodes": evaluation.nodes, "observed_edges": evaluation.edges, "result_path": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
