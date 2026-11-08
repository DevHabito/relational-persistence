"""Independent exact result replay and immutable original archive regression."""
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest

from experiments import rp_s001_independent_union_find as replay


ROOT = Path("docs/results/RP-S001-P01-first-run")
FIRST_SHA = "6d825f055fcdc4955513218b56ec477900911f72c7e2ac7ada8f0c0cba36de19"


def first_report(root=ROOT):
    raw=(root/"audit.json").read_bytes()
    archive=json.loads((root/"archive-index.json").read_text(encoding="utf-8"))
    if sha256(raw).hexdigest()!=FIRST_SHA:
        raise ValueError("The original RP-S001 result changed")
    if archive["first_completed_source_run"]["source_json_sha256"]!=FIRST_SHA:
        raise ValueError("Original RP-S001 archive index changed")
    return json.loads(raw),archive


def test_exact_original_census_reproduces_using_independent_union_find():
    original,index=first_report()
    second=replay.verify_report()
    assert original["admissible_source_graphs"]==second["admissible_source_graphs"]==540
    assert original["degree_classes_with_nonconstant_survival"]==31
    assert second["survival_numerator_histogram"]=={"24":24,"25":204,"26":312}
    assert original["primary_decision"]=="SUMMARY_SUFFICIENCY_COUNTEREXAMPLE"
    assert index["protocol_only_commit"]==original["protocol_commit"]


def test_first_pair_has_equal_labeled_degrees_and_exact_distinct_thresholds():
    original,_=first_report()
    pair=original["first_lexicographic_primary_witness"]
    assert pair["full_labeled_degree_vector"]==[2,5,3,2,2,2]
    assert pair["shared_terminal_minimum_edge_cut"]==2
    assert pair["graph_A_surviving_two_edge_subsets"]==25
    assert pair["graph_B_surviving_two_edge_subsets"]==26
    assert Fraction(**pair["graph_A_survival_fraction"])==Fraction(25,28)
    assert Fraction(**pair["graph_B_survival_fraction"])==Fraction(13,14)


@pytest.mark.parametrize("label,k", [("graph_A",25),("graph_B",26)])
def test_temporal_correlation_exact_fraction_witness(label,k):
    original,_=first_report()
    item=original["first_lexicographic_primary_witness"][label+"_three_step_disturbance_controls"]
    assert item["strict_temporal_gap"] is True
    assert item["same_uniform_per_tick_failure_distribution"] is True
    assert item["emergent_physical_time_tested"] is False
    assert Fraction(**item["one_time_survival"])==Fraction(k,28)
    assert Fraction(**item["frozen_two_edge_failure_set_sustained_3"])==Fraction(k,28)
    assert Fraction(**item["independent_new_failure_set_each_tick_sustained_3"])==Fraction(k**3,28**3)
    assert item["three_step_independent_successful_schedules"]==k**3
    assert item["three_step_total_schedules"]==28**3


def test_initial_workflow_dependency_failure_preceded_auditable_first_source_result():
    _, index=first_report()
    assert index["first_source_job_attempt"]["run_id"]=="42532412191"
    assert index["first_source_job_attempt"]["status"]=="FAILED_BEFORE_SOURCE"
    assert index["first_completed_source_run"]["run_id"]=="42532463153"


def test_first_report_tamper_is_not_accepted_even_if_archive_index_forged(tmp_path):
    for item in ("audit.json","archive-index.json"):
        copyfile(ROOT/item,tmp_path/item)
    damaged=(tmp_path/"audit.json").read_bytes()+b" "
    (tmp_path/"audit.json").write_bytes(damaged)
    idxfile=tmp_path/"archive-index.json"
    idx=json.loads(idxfile.read_text(encoding="utf-8"))
    idx["first_completed_source_run"]["source_json_sha256"]=sha256(damaged).hexdigest()
    idxfile.write_text(json.dumps(idx),encoding="utf-8")
    with pytest.raises(ValueError,match="original RP-S001 result changed"):
        first_report(tmp_path)
