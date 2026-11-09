"""RP-H001-G0G1 source eligibility: strict negative controls and positive fixture.

The expected positive fixture is explicitly invented, NOT a factual claim
about any actual data source. Real source fields are documentation judgments.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys

import pytest

from experiments import rp_h001_source_eligibility as h


def actual():
    return json.loads(h.EVIDENCE_FILE.read_text(encoding="utf-8"))


def modified_record(record, **attrs):
    x=deepcopy(record)
    x.update(attrs)
    return x


def test_fixed_source_evidence_is_structurally_complete_not_a_data_measurement():
    evidence=actual()
    h.check_evidence(evidence)
    assert evidence["rubric_protocol_only_commit"]==h.PROTOCOL_COMMIT
    assert len(evidence["records"])==8
    assert set(r["id"] for r in evidence["records"])==h.FIXED_SOURCE_IDS
    assert evidence["original_joint_data_processed_in_this_study"] is False
    assert set(evidence["criteria"])==set(h.CRITERIA)


def test_original_metadata_gate_makes_no_unsupported_real_causal_claim():
    result=h.evaluate(actual())
    assert result["source_count"]==8
    assert result["observed_source_count"]==5
    assert result["eligible_real_source_ids"]==[]
    assert result["decision"]=="NO_END_TO_END_REAL_WORLD_CAUSAL_SOURCE_IDENTIFIED"
    assert result["candidate_simulator_ids"]==["SMART-DS"]
    assert result["joint_source_data_audited_in_this_review"] is False
    assert result["prediction_or_repair_policy_compared"] is False
    assert result["physical_time_emergence_tested"] is False
    assert result["external_unreviewed_source_existence_not_refuted"] is True
    assert result["gaps_counted_across_reviewed_sources"]["observed_action_sequence"]==8
    assert result["gaps_counted_across_reviewed_sources"]["cost_measurements"]==8


def test_invented_complete_joint_real_source_can_pass_gate_not_hardcoded_to_reject():
    artificial=actual()
    candidate=next(r for r in artificial["records"] if r["id"]=="ANEEL-2026")
    candidate["kind"]="OBSERVED"
    candidate["evidence_level"]="COMPLETE_JOINT_ORIGINAL_AUDIT"
    candidate["criteria"]={key:"EVIDENCED" for key in h.CRITERIA}
    # Synthetic laboratory-only fixture. DOES NOT assert ANEEL has these fields.
    result=h.evaluate(artificial)
    assert result["eligible_real_source_ids"]==["ANEEL-2026"]
    assert result["decision"]=="AT_LEAST_ONE_RECORDED_REAL_WORLD_CAUSAL_SOURCE_ELIGIBLE"


def test_one_missing_requirement_blocks_even_if_all_seven_other_requirements_pass():
    artificial=actual()
    candidate=next(r for r in artificial["records"] if r["id"]=="ANEEL-2026")
    candidate["kind"]="OBSERVED"
    candidate["evidence_level"]="COMPLETE_JOINT_ORIGINAL_AUDIT"
    candidate["criteria"]={key:"EVIDENCED" for key in h.CRITERIA}
    candidate["criteria"]["observed_action_sequence"]="NOT_ESTABLISHED"
    out=h.evaluate(artificial)
    assert "ANEEL-2026" not in out["eligible_real_source_ids"]
    assert out["source_assessments"][0]["gaps_by_criterion"]=={
        "observed_action_sequence":"NOT_ESTABLISHED"
    }


@pytest.mark.parametrize("level", [
    "PRIMARY_SOURCE_DESCRIPTION_ONLY",
    "PARTIAL_ORIGINAL_SOURCE_AUDIT",
])
def test_publisher_description_or_partial_original_audit_cannot_be_promoted(level):
    artificial=actual()
    item=next(r for r in artificial["records"] if r["id"]=="ANEEL-2026")
    item["evidence_level"]=level
    item["criteria"]={key:"EVIDENCED" for key in h.CRITERIA}
    assert "ANEEL-2026" not in h.evaluate(artificial)["eligible_real_source_ids"]


def test_synthetic_data_do_not_count_as_real_even_with_all_eight_checkboxes():
    artificial=actual()
    item=next(r for r in artificial["records"] if r["id"]=="SMART-DS")
    item["kind"]="SYNTHETIC"
    item["evidence_level"]="COMPLETE_JOINT_ORIGINAL_AUDIT"
    item["criteria"]={key:"EVIDENCED" for key in h.CRITERIA}
    result=h.evaluate(artificial)
    assert result["eligible_real_source_ids"]==[]
    assert "SMART-DS" in result["candidate_simulator_ids"]


def test_proxy_is_never_identical_to_actual_evidence():
    artificial=actual()
    item=next(r for r in artificial["records"] if r["id"]=="METR-LA")
    item["evidence_level"]="COMPLETE_JOINT_ORIGINAL_AUDIT"
    item["criteria"]={key:"EVIDENCED" for key in h.CRITERIA}
    item["criteria"]["predecision_topology"]="PROXY_ONLY"
    assert "METR-LA" not in h.evaluate(artificial)["eligible_real_source_ids"]


@pytest.mark.parametrize("corruption,message", [
    (lambda x: x["records"].pop(),"FROZEN_REVIEWED_SOURCE_SET_CHANGED"),
    (lambda x: x["records"].append(deepcopy(x["records"][0])),"DUPLICATE_OR_EMPTY_SOURCE_ID"),
    (lambda x: x["records"][0]["criteria"].pop("cost_measurements"),"SOURCE_CRITERIA_INCOMPLETE"),
    (lambda x: x["records"][0]["criteria"].update(cost_measurements="UNKNOWN"),"SOURCE_HAS_UNKNOWN_STATUS"),
    (lambda x: x["records"][0].update(evidence_level="TRUST_ME"),"UNKNOWN_EVIDENCE_LEVEL"),
    (lambda x: x["records"][0].update(kind="REAL_MAGIC"),"UNKNOWN_SOURCE_KIND"),
    (lambda x: x["records"][0].update(references=[]),"EVIDENCE_URL_MISSING_OR_UNSAFE"),
    (lambda x: x["records"][0].update(references=["http://example.com"]),"EVIDENCE_URL_MISSING_OR_UNSAFE"),
    (lambda x: x["records"][0].update(documented_network_topology="true"),"SOURCE_FLAGS_NOT_BOOLEAN"),
    (lambda x: x.update(original_joint_data_processed_in_this_study=True),"THIS_STUDY_CANNOT_CLAIM_RAW_DATA_ACCESS"),
    (lambda x: x.update(rubric_protocol_only_commit="0"*40),"FROZEN_PROTOCOL_COMMIT_MISMATCH"),
    (lambda x: x["records"][0].update(reason="x"),"SOURCE_RATIONALE_MISSING"),
])
def test_corrupted_or_incomplete_source_evidence_fails_closed(corruption,message):
    evidence=actual()
    corruption(evidence)
    with pytest.raises(h.GateError,match=message):
        h.evaluate(evidence)


def test_candidate_simulator_requires_publisher_scenario_flag_and_topology():
    evidence=actual()
    item=next(r for r in evidence["records"] if r["id"]=="SMART-DS")
    item["documented_outage_scenarios"]=False
    assert h.evaluate(evidence)["candidate_simulator_ids"]==[]
    item["documented_outage_scenarios"]=True
    item["criteria"]["predecision_topology"]="PROXY_ONLY"
    assert h.evaluate(evidence)["candidate_simulator_ids"]==[]


def test_original_source_is_not_conflated_with_verified_historical_action_log():
    evidence=actual()
    by_id={r["id"]:r for r in evidence["records"]}
    assert by_id["ANEEL-2026"]["criteria"]["observed_action_sequence"]=="NOT_ESTABLISHED"
    assert by_id["GOOGLE-BORG-2019"]["evidence_level"]=="PARTIAL_ORIGINAL_SOURCE_AUDIT"
    assert by_id["NASA-CMAPSS"]["kind"]=="SYNTHETIC"
    assert by_id["METR-LA"]["criteria"]["predecision_topology"]=="PROXY_ONLY"


def test_cli_report_is_stable_and_consistent_with_frozen_evidence():
    import subprocess
    p=subprocess.run([sys.executable,"-m","experiments.rp_h001_source_eligibility"],
                     capture_output=True,text=True,timeout=30,check=False)
    assert p.returncode==0,p.stderr
    recorded=json.loads(h.OUTPUT_FILE.read_text(encoding="utf-8"))
    expected=h.evaluate(actual())
    assert recorded==expected
    assert json.loads(p.stdout)==expected


def test_validation_does_not_disappear_with_python_optimization():
    code=(
        "from experiments.rp_h001_source_eligibility import GateError,evaluate;"
        "import json;from pathlib import Path;"
        "x=json.loads(Path('docs/research/RP-H001-G0G1-SOURCE-EVIDENCE.json').read_text());"
        "x['records'][0]['criteria']['observed_action_sequence']='MAGIC';"
        "\ntry:\n evaluate(x);print('BROKEN')"
        "\nexcept GateError:\n print('VALIDATED')"
    )
    x=subprocess.run([sys.executable,"-O","-c",code],
                     capture_output=True,text=True,timeout=30,check=False)
    assert x.returncode==0,x.stderr
    assert x.stdout.strip()=="VALIDATED"
