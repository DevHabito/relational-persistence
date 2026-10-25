"""First-run RP-E010-P01 external HPC negative-result integrity regression.

No hosted production workload is reacquired in ordinary Python CI;
the frozen source and all per-job outputs can be deterministically
replayed separately with experiments.rp_e010_verify_first_run.
"""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path

from experiments.rp_e010_observational_forecast import frozen_gate

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E010-P01-first-run"
ORIGINAL_WORKFLOW = "40145857634"
ORIGINAL_CODE_SHA = "c589bae80a8045be69094515c928c8d467b96dc0"
EXTERNAL_SOURCE_SHA256 = "77b8993c73ae438385f6c0015708251f52dc316267b03ac19a406fbea2802afa"


def load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj, dict)
    return obj


def original_result() -> tuple[dict, dict, dict]:
    report = load(ARCHIVE / "evaluation.json")
    index = load(ARCHIVE / "archive-index.json")
    return report, report["original_results"], index


def test_exact_first_source_identity_and_original_negative_verdict():
    record, result, index = original_result()
    assert record["protocol"] == result["protocol"] == index["protocol"] == "RP-E010-P01"
    assert record["first_run_source_commit"] == index["original_source_commit"] == ORIGINAL_CODE_SHA
    assert record["first_run_github_id"] == index["original_github_run_id"] == ORIGINAL_WORKFLOW
    assert record["decision"] == index["original_verdict"] == "NO_REGISTERED_OBSERVATIONAL_GAIN"
    assert record["errors"] == []
    assert result["decision"] == record["decision"]
    assert result["source"]["actual_external_sha256"] == EXTERNAL_SOURCE_SHA256
    assert result["source"]["actual_external_bytes"] == 19_242_100


def test_original_first_run_evaluation_cannot_be_mutated_without_hash_failure():
    index = load(ARCHIVE / "archive-index.json")
    original_bytes = (ARCHIVE / "evaluation.json").read_bytes()
    assert hashlib.sha256(original_bytes).hexdigest() == index["archived_evaluation_sha256"]
    assert hashlib.sha256(original_bytes + b"\n").hexdigest() != (
        index["archived_evaluation_sha256"]
    )


def test_original_time_boundary_and_entire_eligible_cohort_preserved():
    _, result, _ = original_result()
    split = result["split"]
    assert split["earliest_submit_seconds"] == "342072"
    assert split["latest_submit_seconds"] == "109583573"
    assert split["chronological_cutoff_seconds"] == "76811122"
    assert split["candidate_diagnostic_targets_before_past-start-eligibility"] == 146_637
    assert split["candidate_heldout_targets_before_past-start-eligibility"] == 55_352
    assert result["source_schema_eligible_targets"] == 201_992
    assert result["feature_eligible_targets"] == 137_701 + 49_995
    assert result["excluded_by_zero_prior_starts"] == 14_293
    assert result["diagnostic"]["jobs"] == 137_701
    assert result["heldout"]["jobs"] == 49_995
    assert result["distinct_prediction_origins"] == 172_503
    assert result["two_queue_oracles_agree_all_origins"] is True
    assert result["heldout"]["zero_wait_jobs"] == 1_585


def test_original_mae_fails_both_frozen_primary_classical_controls():
    record, result, _ = original_result()
    errors = {
        k: Decimal(v)
        for k, v in result["heldout"]["mae_seconds"].items()
    }
    assert frozen_gate(errors) == record["decision"]
    assert errors["trend"] > errors["static"]
    assert errors["trend"] > errors["history"]
    assert errors["diagnostic_constant"] < errors["history"]
    assert result["registered_primary_improvement_ratio"] == "0.90"


def test_all_predeclared_processor_groups_contain_unfavorable_trend_direction():
    _, result, _ = original_result()
    groups = result["heldout_by_allocated_processors"]
    assert set(groups) == {"1..2", "3..16", ">16"}
    assert groups["1..2"]["jobs"] == 31_542
    assert groups["3..16"]["jobs"] == 16_521
    assert groups[">16"]["jobs"] == 1_932
    assert sum(g["jobs"] for g in groups.values()) == result["heldout"]["jobs"]
    for group in groups.values():
        errors = group["mae_seconds"]
        assert Decimal(errors["trend"]) > Decimal(errors["static"])


def test_original_individual_prediction_artifact_digests_are_pinned():
    _, result, index = original_result()
    assert index["source_corpus_copied_to_git"] is False
    assert index["predictor_validated_as_physical_law"] is False
    by_split = index["original_per_job_files"]
    assert set(by_split) == {
        "diagnostic-original-predictions.jsonl",
        "holdout-original-predictions.jsonl",
    }
    assert by_split["diagnostic-original-predictions.jsonl"]["bytes"] == 134_578_470
    assert by_split["holdout-original-predictions.jsonl"]["bytes"] == 59_773_248
    for split in ("diagnostic", "holdout"):
        filename = f"{split}-original-predictions.jsonl"
        expected = result["original_prediction_files"][split]
        first = by_split[filename]
        assert expected["file"] == filename
        assert expected["sha256"] == first["sha256"]
        assert expected["original_bytes"] == first["bytes"]
        assert len(first["sha256"]) == 64
        assert not (ARCHIVE / filename).exists()


def test_no_physical_law_or_cross_domain_endpoint_from_archive():
    _, result, _ = original_result()
    assert result["scalar_C_physical_law_test"] == "NOT_PERFORMED"
    assert result["new_lean_theorem"] is False
    assert result["independent_physical_replication"] == "NOT_PERFORMED"
    assert result["independent_queue_identifiers"] == "UNAVAILABLE"
    assert result["source"]["unavailable_queue_id_count"] == 202_871
    assert result["one_observational_trace_upstream_cleaned"] is True
    assert result["source_mirror_equals_original_PWA_gzip"] == "NOT_ESTABLISHED"


def test_source_cannot_be_labeled_as_new_independent_replication():
    _, result, index = original_result()
    assert index["original_github_run_id"] == ORIGINAL_WORKFLOW
    assert result["decision"] == "NO_REGISTERED_OBSERVATIONAL_GAIN"
    assert index["archive_policy"].startswith("first-run")
    assert "retention" in index["original_per_job_files"][
        "holdout-original-predictions.jsonl"
    ]
