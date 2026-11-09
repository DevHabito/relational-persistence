"""Integrity and independent decision replay for original RP-H001 metadata audit.

This audits *documentation assessments*, not any original ANEEL/EAGLE records.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest

from experiments import rp_h001_source_eligibility as gate


FIRST = Path("docs/results/RP-H001-G0G1-source-gate.json")
INDEX = Path("docs/results/RP-H001-G0G1-first-run/archive-index.json")
ORIGINAL_DIGEST = "e68eeef1d665e22c34e4adee1407a9613d707e0e1cd2313e32bd45282660c6f0"


def frozen_result(first_path=FIRST,index_path=INDEX):
    raw=first_path.read_bytes()
    index=json.loads(index_path.read_text(encoding="utf-8"))
    if sha256(raw).hexdigest()!=ORIGINAL_DIGEST:
        raise ValueError("RP-H001 original source eligibility result changed")
    if index["original_source_gate_json_sha256"]!=ORIGINAL_DIGEST:
        raise ValueError("RP-H001 index digest changed")
    return json.loads(raw),index


def test_original_first_result_matches_independent_evidence_replay():
    result,index=frozen_result()
    original=json.loads(gate.EVIDENCE_FILE.read_text(encoding="utf-8"))
    recomputed=gate.evaluate(original)
    assert recomputed==result
    assert index["first_code_test_workflow_commit"]=="98eb776f2a051baed08fcb10879382b03e1e8450"
    assert index["protocol_only_commit"]==gate.PROTOCOL_COMMIT
    assert result["eligible_real_source_ids"]==[]
    assert result["candidate_simulator_ids"]==["SMART-DS"]
    assert result["decision"]=="NO_END_TO_END_REAL_WORLD_CAUSAL_SOURCE_IDENTIFIED"
    assert index["original_third_party_rows_downloaded_or_analyzed_in_this_review"] is False
    assert result["physical_time_emergence_tested"] is False
    assert index["source_families_reviewed"]==8


def test_known_gaps_are_counts_of_unverified_documentation_not_physical_facts():
    result,index=frozen_result()
    assert result["gaps_counted_across_reviewed_sources"]=={
        "predecision_topology":6,
        "predecision_disturbance_history":8,
        "registered_functional_outcome":5,
        "feasible_action_set":8,
        "observed_action_sequence":8,
        "decision_time_availability":8,
        "cost_measurements":8,
        "joint_population_coverage":8,
    }
    assert len(result["source_assessments"])==8
    assert index["general_dataset_nonexistence_claimed"] is False
    assert all(x["original_joint_data_processed_here"] is False
               for x in result["source_assessments"])


def test_ambiguous_source_can_not_be_upgraded_by_changing_only_final_decision():
    recorded,_=frozen_result()
    manipulated=deepcopy(recorded)
    manipulated["decision"]="AT_LEAST_ONE_RECORDED_REAL_WORLD_CAUSAL_SOURCE_ELIGIBLE"
    assert manipulated!=gate.evaluate(json.loads(gate.EVIDENCE_FILE.read_text(encoding="utf-8")))


def test_source_bytes_tamper_detected_even_if_accompanying_index_rewritten(tmp_path):
    changed=tmp_path/"audit.json"
    changed.write_bytes(FIRST.read_bytes()+b" ")
    index_file=tmp_path/"archive-index.json"
    metadata=json.loads(INDEX.read_text(encoding="utf-8"))
    metadata["original_source_gate_json_sha256"]=sha256(changed.read_bytes()).hexdigest()
    index_file.write_text(json.dumps(metadata),encoding="utf-8")
    with pytest.raises(ValueError,match="original source eligibility result changed"):
        frozen_result(changed,index_file)


def test_single_source_status_change_replay_must_differ_from_original():
    original,_=frozen_result()
    evidence=json.loads(gate.EVIDENCE_FILE.read_text(encoding="utf-8"))
    item=next(x for x in evidence["records"] if x["id"]=="METR-LA")
    item["criteria"]["cost_measurements"]="EVIDENCED"
    newer=gate.evaluate(evidence)
    assert newer!=original
    assert newer["eligible_real_source_ids"]==[]
    assert newer["gaps_counted_across_reviewed_sources"]["cost_measurements"]==7
