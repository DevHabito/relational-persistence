"""RP-U005-D01: read-only eligibility gate for the original Google Borg archive.

This checks *previously archived* source evidence. It does not access new
publisher rows, predict failures, infer physical repair decisions, or validate
a pregeometry or relational-persistence law.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


ORIGINAL = Path("docs/results/RP-E012-D03-first-run")
BLOCKED_VERDICT = "RP_U005_DIRECT_POLICY_SOURCE_BLOCKED"
SOURCE_SCOPE = "GOOGLE_BORG_2019_CELL_A_MACHINE_EVENTS_ONLY"
PINNED_FIRST_REPORT_SHA256 = "393ed949a3aec3e4cd27f6e6ca8f617102b855a5e0934021d3b6909be31b6f0a"
PINNED_MACHINE_OBJECT_SHA256 = "b04455f48e57c303fc8987b41e35911d89f3aa31e5a6d3997f07e27749dc1791"


@dataclass(frozen=True)
class HistoricalSourceEvidence:
    original_report_sha256: str
    original_machine_sha256: str
    compressed_machine_bytes: int
    machine_event_rows: int
    machine_identifiers: int
    complete_machine_object: bool
    cross_table_history_certified: bool
    event_receipt_timing_certified: bool
    instance_collection_rows_read: int
    first_page_instance_inventory_paginated: bool


def _require(condition: bool, message: str) -> None:
    """Remain active in Python's optimized (-O) execution mode."""
    if not condition:
        raise ValueError(message)


def _load_source(archive_dir: Path) -> tuple[dict, dict, bytes]:
    index = json.loads(
        (archive_dir / "archive-index.json").read_text(encoding="utf-8")
    )
    raw = (archive_dir / "audit.json").read_bytes()
    _require(
        sha256(raw).hexdigest() == index["first_report_sha256"]
        == PINNED_FIRST_REPORT_SHA256,
        "Original D03 archive bytes do not match first-run SHA-256",
    )
    report = json.loads(raw)
    return report, index, raw


def read_historical_source(
    archive_dir: Path = ORIGINAL,
) -> HistoricalSourceEvidence:
    """Authenticate, then audit the historical scope without inventing rows."""
    report, index, raw = _load_source(archive_dir)
    del raw  # No event-row bodies are included in this summary.

    _require(
        index["protocol"] == report["protocol"] == "RP-E012-D03",
        "Original D03 protocol disagrees",
    )
    for key in ("original_code_commit", "preregistration_commit"):
        _require(index[key] == report[key], f"Original D03 {key} disagrees")
    _require(
        index["first_run_id"] == report["first_run_id"] == "40425342721",
        "Original D03 run ID disagrees",
    )
    _require(
        report["errors"] == [],
        "Original D03 recorded error(s)",
    )
    _require(
        report["original_decision"]
        == index["first_original_decision"]
        == "MACHINE_EVENTS_COMPLETE_OBJECT_AUDITED_JOINT_UNCERTIFIED",
        "Original D03 first decision disagrees",
    )

    source = report["machine_source"]
    counts = report["machine_counts"]
    metadata = report["metadata_first_page"]
    total = counts["all_complete_machine_event_rows"]
    event_types = counts["event_type_counts"]
    _require(
        sum(event_types.values()) == total
        and all(isinstance(n, int) and n >= 0 for n in event_types.values())
        and set(event_types) == {"1", "2", "3"},
        "Machine event counts are internally inconsistent",
    )
    _require(
        sum(counts["missing_type_code_counts"].values()) == total,
        "Machine missing-data counts do not cover all rows",
    )
    _require(
        counts["distinct_machine_ids_aggregate_only"] > 0
        and counts["distinct_machine_ids_aggregate_only"] <= total,
        "Machine identifier count is not plausible",
    )
    for timestamp, partition in counts["snapshots_strict_before_origin"].items():
        _require(
            timestamp in ("1000000000000", "2000000000000"),
            "Unexpected retrospective snapshot origin",
        )
        _require(
            sum(partition.values())
            == counts["distinct_machine_ids_aggregate_only"]
            and set(partition)
            == {"last_event_implied_active", "last_event_implied_removed", "no_prior_event"},
            f"Machine snapshot partition incomplete at {timestamp}",
        )
    _require(
        len(counts["snapshots_strict_before_origin"]) == 2,
        "Snapshot origin coverage differs from the original",
    )
    _require(
        source["full_object_bytes_downloaded"]
        == source["advertised_full_size_bytes"]
        == int(metadata["machine_events"]["selected_first_size_bytes_metadata_only"])
        and source["full_object_bytes_downloaded"] > 0,
        "Original machine source byte lengths disagree",
    )
    _require(
        source["entire_object_authenticated_not_prefix_only"] is True
        and source["full_object_provider_md5_verified"] is True
        and source["original_full_compressed_object_sha256"]
        == index["actual_machine_object_original_sha256"]
        == PINNED_MACHINE_OBJECT_SHA256,
        "Original machine source identity is not certified",
    )
    _require(
        metadata["machine_events"]["matching_shards_on_first_page"] == 1
        and metadata["machine_events"]["inventory_incomplete_due_to_pagination"] is False,
        "The machine-table object inventory is not complete",
    )
    _require(
        report["collection_and_instance_raw_event_rows_downloaded"] == 0
        and metadata["instance_events"]["raw_event_rows_downloaded_from_this_table"] is False
        and metadata["collection_events"]["raw_event_rows_downloaded_from_this_table"] is False,
        "Cross-table raw coverage differs from first-run report",
    )
    _require(
        report["joint_causal_history"] == "JOINT_CAUSAL_HISTORY_NOT_CERTIFIED"
        and report["full_online_event_release_history_proven"] is False
        and index["all_cross_table_states_certified"] is False
        and report["machine_counts"]["timestamp_is_not_proven_online_release_time"] is True
        and report["machine_counts"]["event_implied_state_not_full_live_capacity"] is True,
        "The archived limitations were changed or contradict each other",
    )
    _require(
        report["forecast_targets_computed"] is False
        and report["real_running_job_hard_walltime_cap_verified"] is False
        and report["new_lean_theorem_or_physical_law_claimed"] is False,
        "Original study scope is not preserved",
    )
    return HistoricalSourceEvidence(
        original_report_sha256=index["first_report_sha256"],
        original_machine_sha256=index["actual_machine_object_original_sha256"],
        compressed_machine_bytes=source["full_object_bytes_downloaded"],
        machine_event_rows=total,
        machine_identifiers=counts["distinct_machine_ids_aggregate_only"],
        complete_machine_object=True,
        cross_table_history_certified=False,
        event_receipt_timing_certified=False,
        instance_collection_rows_read=0,
        first_page_instance_inventory_paginated=metadata["instance_events"][
            "inventory_incomplete_due_to_pagination"
        ],
    )


def decision(evidence: HistoricalSourceEvidence) -> dict:
    """A true partial audit never silently becomes direct-policy eligibility."""
    _require(evidence.complete_machine_object, "No complete machine evidence")
    _require(
        not evidence.cross_table_history_certified
        and not evidence.event_receipt_timing_certified
        and evidence.instance_collection_rows_read == 0,
        "Evidence scope differs from the fixed D03 audit",
    )
    return {
        "study": "RP-U005-D01",
        "kind": "RETROSPECTIVE_SOURCE_ELIGIBILITY_DESK_AUDIT",
        "source_scope": SOURCE_SCOPE,
        "decision": BLOCKED_VERDICT,
        "verified_machine_only": {
            "original_compressed_object_sha256": evidence.original_machine_sha256,
            "original_first_report_sha256": evidence.original_report_sha256,
            "original_compressed_bytes": evidence.compressed_machine_bytes,
            "machine_event_rows": evidence.machine_event_rows,
            "machine_identifiers": evidence.machine_identifiers,
        },
        "joint_history_complete": False,
        "online_event_receipt_time_certified": False,
        "actual_relation_repair_choices_observed": "NOT_ESTABLISHED_BY_PUBLISHED_TRACE_SCHEMA",
        "physical_repair_and_decision_costs_observed": "NOT_ESTABLISHED_BY_PUBLISHED_TRACE_SCHEMA",
        "independent_F2_terminal_path_outcome_observed": "NOT_ESTABLISHED_BY_PUBLISHED_TRACE_SCHEMA",
        "new_external_data_downloaded": False,
        "empirical_policy_effect_estimated": False,
        "scope_note": (
            "Direct U004 policy-comparison eligibility is blocked by the "
            "audited machine-only source and incompatible published field "
            "semantics. This does not reject Borg as a scheduler dataset."
        ),
    }


def main() -> None:
    print(json.dumps(decision(read_historical_source()), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
