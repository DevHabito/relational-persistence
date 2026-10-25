"""Read-only replay of the FIRST RP-E010-P01 HPC observational forecast.

It fetches the SAME version-pinned external source, reproduces all original
per-job predictions in a separate temporary directory, compares their full
SHA256 and the result object with the archived FIRST run. This is never an
independent external sample, a rerun of original first-run workflow, or
a new preregistered predictive experiment.
"""

from __future__ import annotations

import argparse
from decimal import localcontext
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from experiments.rp_e010_observational_forecast import (
    evaluate_data, parse_verified_jobs,
)
from experiments.rp_e010_source_audit import fetch_exact_pinned_source

PROJECT = Path(__file__).resolve().parents[1]
ORIGINAL = PROJECT / "docs/results/RP-E010-P01-first-run"


def verify_original_archive() -> dict:
    original = json.loads((ORIGINAL / "evaluation.json").read_text("utf-8"))
    manifest = json.loads((ORIGINAL / "archive-index.json").read_text("utf-8"))
    if manifest["original_verdict"] != original["decision"]:
        raise ValueError("Archived original verdict was altered")
    if manifest["original_github_run_id"] != original["first_run_github_id"]:
        raise ValueError("Wrong original first-run identity")
    if manifest["original_source_commit"] != original["first_run_source_commit"]:
        raise ValueError("Wrong original input code revision")
    if original["decision"] == "STOP_OBSERVATIONAL_AUDIT":
        raise ValueError("Do not disguise an original STOP as replay success")
    raw = fetch_exact_pinned_source()
    jobs, source = parse_verified_jobs(raw)
    with TemporaryDirectory(prefix="rp-e010-original-verified-") as name:
        with localcontext() as context:
            context.prec = 45
            replay = evaluate_data(jobs, source, Path(name))
        if replay != original["original_results"]:
            raise ValueError("Original numerical forecast results do not replay")
        for split in ("diagnostic", "holdout"):
            filename = f"{split}-original-predictions.jsonl"
            replay_file = replay["original_prediction_files"][split]
            first_file = manifest["original_per_job_files"][filename]
            if (replay_file["sha256"] != first_file["sha256"]
                    or replay_file["original_bytes"] != first_file["bytes"]):
                raise ValueError(f"Original per-job prediction bytes differ: {split}")
    return {
        "protocol": original["protocol"],
        "first_run_id": manifest["original_github_run_id"],
        "reproduced_original_decision": original["decision"],
        "original_per_job_sha256_equal": True,
        "original_first_run_changed": False,
        "second_observational_sample": False,
        "physical_law_validated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_original_archive()
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.output is not None:
        if args.output.exists():
            raise ValueError("Read-only replay output cannot overwrite existing file")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
