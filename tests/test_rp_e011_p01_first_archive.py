"""Permanent regressions pin the ORIGINAL, negative RP-E011-P01 first run.

The 104MB per-job predictions and 59MB third-party source are deliberately
NOT present in Git. These tests authenticate the committed original
report/manifest and pin the original artifact hash; they cannot recompute
the external per-job bytes unless the temporary original artifact is present.
"""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E011-P01-first-run"
D04 = ROOT / "docs/results/RP-E011-D04-first-run/audit.json"

FIRST_RUN = "40185076529"
FIRST_CODE = "7c556ca6f72dcc62c068c37a51efe0eba6fc6d5b"
FIRST_REPORT_SHA = "bb173096a23413f57d2eaecffbdd6d9703e88173eb3c7e5175d628460b6878d7"
FIRST_PREDICTIONS_SHA = "0c1f679e94f56abe3605ae8ff00134042a54f0e1017843849e5e0d6dfd9504ff"
SOURCE_SHA = "dd48cf7ca369d485b14add5d2baca70a1001c19d9b447688ff7639812673dc7c"
ORIGINAL_D04_SHA = "be9b871e29b2bd014d0bc365f4ae6d2f23f8ad428aa41b1932446edf173fb240"


def original() -> tuple[dict, dict]:
    return (
        json.loads((ARCHIVE / "audit.json").read_text("utf-8")),
        json.loads((ARCHIVE / "archive-index.json").read_text("utf-8")),
    )


def test_first_run_bytes_and_original_identity_are_immutable():
    report, index = original()
    assert sha256((ARCHIVE / "audit.json").read_bytes()).hexdigest() == (
        FIRST_REPORT_SHA
    )
    assert index["first_audit_sha256"] == FIRST_REPORT_SHA
    assert report["protocol"] == index["protocol"] == "RP-E011-P01"
    assert report["first_run_id"] == index["first_run_id"] == FIRST_RUN
    assert report["source_code_commit"] == index["original_code_commit"] == FIRST_CODE
    assert report["decision"] == index["first_run_decision"] == (
        "NO_REGISTERED_QUEUE_GAIN"
    )
    assert sorted(path.name for path in ARCHIVE.iterdir()) == [
        "archive-index.json", "audit.json",
    ]


def test_original_source_is_same_hash_and_prior_d04_result():
    report, _ = original()
    source = report["source"]
    assert source["sha256"] == source["source_sha256"] == SOURCE_SHA
    assert source["original_bytes"] == source["downloaded_source_bytes"] == 59_430_886
    assert source["status"] == 200
    assert source["known_ID_zero_first_line_exclusion"] == 1
    assert source["original_D02_verdict_unchanged"] == "DATASET_SCHEMA_REJECTED"
    assert sha256(D04.read_bytes()).hexdigest() == ORIGINAL_D04_SHA
    assert source["original_D04_audit_sha256"] == ORIGINAL_D04_SHA
    assert json.loads(D04.read_text())["decision"] == "TEMPORAL_SOURCE_FEASIBLE"


def test_registered_holdout_count_and_all_three_unfitted_scores():
    report, _ = original()
    result = report["forecast"]
    assert result["decision"] == "NO_REGISTERED_QUEUE_GAIN"
    assert result["split_cutoff_seconds"] == "1472994372.8"
    assert result["diagnostic_target_count"] == report["source"]["diagnostic_jobs"] == 303_210
    assert result["heldout_target_count"] == report["source"]["heldout_jobs"] == 169_189
    observed = result["heldout"]
    assert observed["jobs"] == 169_189
    assert observed["zero_waits"] == 0
    assert observed["zero_past_start_rate_fallbacks"] == 8_473
    maes = {name: Decimal(value) for name, value in observed["mae_seconds"].items()}
    assert maes["history"] == Decimal("34309.43176861379876942354408")
    assert maes["static"] == Decimal("43953.97629696434554367850910")
    assert maes["trend"] == Decimal("45328.01254257410618054824213")
    assert maes["history"] < maes["static"] < maes["trend"]
    assert not (
        maes["trend"] <= Decimal("0.90") * maes["static"]
        and maes["trend"] <= Decimal("0.90") * maes["history"]
    )


def test_independent_oracles_and_online_boundary_remain_claimed_exactly():
    report, _ = original()
    result = report["forecast"]
    assert result["independent_binary_and_sweep_oracles_agree"] is True
    assert result["all_requested_snapshots_checked"] == 212_964
    assert result["strict_pre_origin_feature_cutoff_s"] == "60"
    assert result["live_online_history_from_previously_started_jobs_only"] is True
    assert result["no_new_predictor_parameters_fit"] is True
    assert report["errors"] == []


def test_no_queue_silently_omitted_and_true_heldout_imbalance_retained():
    report, _ = original()
    queues = report["forecast"]["heldout_by_queue_sha256"]
    assert len(queues) == report["source"]["queue_count"] == 13
    counts = sorted((group["jobs"] for group in queues.values()), reverse=True)
    assert counts == [149_760, 18_880, 469, 67, 12, 1, 0, 0, 0, 0, 0, 0, 0]
    assert sum(counts) == 169_189
    assert sum(group["zero_past_start_rate_fallbacks"] for group in queues.values()) == 8_473
    assert all(group["mae_seconds"] is None for group in queues.values()
               if group["jobs"] == 0)


def test_requested_processor_groups_preserve_mixed_unfavorable_findings():
    report, _ = original()
    groups = report["forecast"]["heldout_by_requested_processor_group"]
    assert {name: group["jobs"] for name, group in groups.items()} == {
        "small": 122_474, "medium": 45_941, "large": 774,
    }
    assert sum(g["jobs"] for g in groups.values()) == 169_189
    assert (Decimal(groups["medium"]["mae_seconds"]["trend"])
            < Decimal(groups["medium"]["mae_seconds"]["static"]))
    assert (Decimal(groups["small"]["mae_seconds"]["trend"])
            > Decimal(groups["small"]["mae_seconds"]["static"]))
    assert (Decimal(groups["large"]["mae_seconds"]["trend"])
            > Decimal(groups["large"]["mae_seconds"]["static"]))


def test_first_prediction_sha_is_pinned_but_original_rows_not_republished():
    report, index = original()
    evidence = report["forecast"]["original_predictions_file"]
    assert evidence["sha256"] == index["heldout_prediction_sha256"] == FIRST_PREDICTIONS_SHA
    assert evidence["bytes"] == index["heldout_prediction_bytes"] == 104_512_786
    assert evidence["name"] == "original-heldout-predictions.jsonl"
    assert index["raw_external_source_committed_to_git"] is False
    assert index["per_job_predictions_committed_to_git"] is False
    assert index["d02_first_rejected_verdict_untouched"] is True
    assert index["e010_first_negative_verdict_untouched"] is True
    assert report["original_RP_E010_negative_unchanged"] is True
    assert report["original_D02_schema_verdict_unchanged"] == "DATASET_SCHEMA_REJECTED"
    assert report["scalar_C_validated"] is False
    assert report["physics_law_tested"] is False
    assert report["new_lean_theorem"] is False


def test_single_byte_change_breaks_original_report_identity():
    raw = (ARCHIVE / "audit.json").read_bytes()
    assert sha256(raw + b"\n").hexdigest() != FIRST_REPORT_SHA
