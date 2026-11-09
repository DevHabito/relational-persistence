"""RP-H001-G0G1: fail-closed prior-evidence source eligibility checker.

This does NOT query original source rows and is NOT a physical experiment.
The prior-source assessments are explicitly retrospective metadata judgments.
One review cannot prove that no eligible source exists outside the listed set.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path
import json

PROTOCOL_COMMIT = "2291d499583e594211e703c997ac3743f55dddcc"
EVIDENCE_FILE = Path("docs/research/RP-H001-G0G1-SOURCE-EVIDENCE.json")
OUTPUT_FILE = Path("docs/results/RP-H001-G0G1-source-gate.json")
CRITERIA = (
    "predecision_topology",
    "predecision_disturbance_history",
    "registered_functional_outcome",
    "feasible_action_set",
    "observed_action_sequence",
    "decision_time_availability",
    "cost_measurements",
    "joint_population_coverage",
)
STATUSES = frozenset({"EVIDENCED", "PROXY_ONLY", "NOT_ESTABLISHED", "CONTRADICTED"})
EVIDENCE_LEVELS = frozenset({
    "PRIMARY_SOURCE_DESCRIPTION_ONLY",
    "PARTIAL_ORIGINAL_SOURCE_AUDIT",
    "COMPLETE_JOINT_ORIGINAL_AUDIT",
})
SOURCE_KINDS = frozenset({"OBSERVED", "SYNTHETIC", "MIXED"})


class GateError(ValueError):
    pass


def check_evidence(data: dict) -> None:
    if not isinstance(data, dict):
        raise GateError("EVIDENCE_NOT_AN_OBJECT")
    if data.get("study") != "RP-H001-G0G1":
        raise GateError("STUDY_ID_MISMATCH")
    if data.get("rubric_protocol_only_commit") != PROTOCOL_COMMIT:
        raise GateError("FROZEN_PROTOCOL_COMMIT_MISMATCH")
    if data.get("original_joint_data_processed_in_this_study") is not False:
        raise GateError("THIS_STUDY_CANNOT_CLAIM_RAW_DATA_ACCESS")
    if (data.get("criteria") != list(CRITERIA)
            or data.get("status_values") != sorted(STATUSES)
            and data.get("status_values") != [
                "EVIDENCED", "PROXY_ONLY", "NOT_ESTABLISHED", "CONTRADICTED"
            ]):
        raise GateError("PREDECLARED_CRITERIA_OR_STATUS_SET_CHANGED")
    if set(data.get("evidence_levels", [])) != EVIDENCE_LEVELS:
        raise GateError("EVIDENCE_LEVEL_UNIVERSE_CHANGED")
    raw = data.get("records")
    if not isinstance(raw, list) or not raw:
        raise GateError("NO_SOURCE_RECORDS")
    seen = set()
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise GateError("MALFORMED_SOURCE")
        key = item["id"]
        if not key.strip() or key in seen:
            raise GateError("DUPLICATE_OR_EMPTY_SOURCE_ID")
        seen.add(key)
        if item.get("kind") not in SOURCE_KINDS:
            raise GateError("UNKNOWN_SOURCE_KIND")
        if item.get("evidence_level") not in EVIDENCE_LEVELS:
            raise GateError("UNKNOWN_EVIDENCE_LEVEL")
        if any(type(item.get(k)) is not bool for k in (
            "documented_network_topology", "documented_outage_scenarios"
        )):
            raise GateError("SOURCE_FLAGS_NOT_BOOLEAN")
        fields = item.get("criteria")
        if not isinstance(fields, dict) or set(fields) != set(CRITERIA):
            raise GateError("SOURCE_CRITERIA_INCOMPLETE")
        if any(v not in STATUSES for v in fields.values()):
            raise GateError("SOURCE_HAS_UNKNOWN_STATUS")
        links = item.get("references")
        if (not isinstance(links, list) or not links or
                any(not isinstance(link, str) or not link.startswith("https://")
                    or len(link) < 15 for link in links)):
            raise GateError("EVIDENCE_URL_MISSING_OR_UNSAFE")
        if not isinstance(item.get("reason"), str) or len(item["reason"]) < 40:
            raise GateError("SOURCE_RATIONALE_MISSING")


def evaluate_one(item: dict) -> dict:
    criteria = item["criteria"]
    gaps = {key: criteria[key] for key in CRITERIA
            if criteria[key] != "EVIDENCED"}
    is_real_ready = (item["kind"] == "OBSERVED"
                     and item["evidence_level"] == "COMPLETE_JOINT_ORIGINAL_AUDIT"
                     and not gaps)
    is_synthetic_candidate = (
        item["kind"] == "SYNTHETIC"
        and item["documented_network_topology"]
        and item["documented_outage_scenarios"]
        and criteria["predecision_topology"] == "EVIDENCED"
    )
    if is_real_ready:
        decision = "REAL_WORLD_CAUSAL_SOURCE_ELIGIBLE_ON_RECORDED_EVIDENCE"
    elif is_synthetic_candidate:
        decision = "SIMULATOR_CANDIDATE_NOT_YET_VALIDATED"
    else:
        decision = "NOT_ELIGIBLE_FOR_FULL_REAL_POLICY_TEST"
    return {
        "source_id": item["id"],
        "source_kind": item["kind"],
        "evidence_level": item["evidence_level"],
        "decision": decision,
        "number_of_not_evidenced_criteria": len(gaps),
        "gaps_by_criterion": gaps,
        "original_joint_data_processed_here": False,
    }


def evaluate(data: dict) -> dict:
    check_evidence(data)
    records = [evaluate_one(item) for item in data["records"]]
    gaps = Counter({key: 0 for key in CRITERIA})
    for item in records:
        gaps.update(item["gaps_by_criterion"].keys())
    ready = [item["source_id"] for item in records
             if item["decision"] == "REAL_WORLD_CAUSAL_SOURCE_ELIGIBLE_ON_RECORDED_EVIDENCE"]
    candidate_simulators = [item["source_id"] for item in records
                            if item["decision"] == "SIMULATOR_CANDIDATE_NOT_YET_VALIDATED"]
    return {
        "study": "RP-H001-G0G1",
        "protocol_commit": PROTOCOL_COMMIT,
        "date_reviewed": data["review_date"],
        "source_assessments": records,
        "source_count": len(records),
        "observed_source_count": sum(item["kind"] == "OBSERVED" for item in data["records"]),
        "joint_source_data_audited_in_this_review": False,
        "eligible_real_source_ids": ready,
        "candidate_simulator_ids": candidate_simulators,
        "gaps_counted_across_reviewed_sources": dict(gaps),
        "decision": ("AT_LEAST_ONE_RECORDED_REAL_WORLD_CAUSAL_SOURCE_ELIGIBLE"
                     if ready else "NO_END_TO_END_REAL_WORLD_CAUSAL_SOURCE_IDENTIFIED"),
        "external_unreviewed_source_existence_not_refuted": True,
        "prediction_or_repair_policy_compared": False,
        "physical_time_emergence_tested": False,
        "original_theorem_or_physical_law_claimed": False,
    }


def main() -> None:
    content = json.loads(EVIDENCE_FILE.read_text(encoding="utf-8"))
    result = evaluate(content)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
