"""Run one immutable RP-E004-P02 measurement set as a fresh RP-E005 replica.

This wrapper never rewrites the P02 role logs or the raw recovery stream.
A failed source experiment must remain a failed observation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

PROTOCOL_PATH = "docs/preregistration/RP-E005-P01.md"
P02_PATH = "docs/preregistration/RP-E004-P02.md"
SLOTS = ("runner-a", "runner-b")


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_replica(slot: str, output: Path, root: Path | None = None) -> dict:
    if slot not in SLOTS:
        raise ValueError("Unregistered runner slot")
    root = root or Path(__file__).resolve().parents[1]
    if output.exists() and any(output.iterdir()):
        raise ValueError("Refusing to overwrite existing run evidence")
    output.mkdir(parents=True, exist_ok=True)
    source_commit = os.environ.get("GITHUB_SHA", "")
    workflow_run = os.environ.get("GITHUB_RUN_ID", "")
    if not source_commit or not workflow_run:
        raise ValueError("GitHub source SHA and workflow run ID are required")
    measured_output = output / "p02"
    try:
        execution = subprocess.run(
            [sys.executable, "-m", "experiments.rp_e004_p02",
             "--output", str(measured_output)],
            cwd=str(root), check=False, timeout=165,
        )
        returncode = execution.returncode
    except subprocess.TimeoutExpired:
        returncode = 124
    metadata = {
        "protocol": "RP-E005-P01",
        "job_slot": slot,
        "github_run_id": workflow_run,
        "source_commit": source_commit,
        "runner_label": "ubuntu-24.04",
        "runner_name": os.getenv("RUNNER_NAME", "unknown"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "p02_execution_returncode": returncode,
        "e005_preregistration_sha256": hash_file(root / PROTOCOL_PATH),
        "p02_preregistration_sha256": hash_file(root / P02_PATH),
        "physical_instrument_independence": "NOT_ESTABLISHED",
        "predictive_index_validation": "NOT_PERFORMED",
    }
    (output / "replica-provenance.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", required=True, choices=SLOTS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_replica(args.slot, args.output)
    print(json.dumps({
        "job_slot": report["job_slot"],
        "returncode": report["p02_execution_returncode"],
        "observation_class": "hosted software instrumentation only",
    }, sort_keys=True))
    if report["p02_execution_returncode"]:
        raise SystemExit(report["p02_execution_returncode"])


if __name__ == "__main__":
    main()
