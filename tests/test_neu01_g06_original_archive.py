"""Immutable original G06 GitHub Actions source audit validation."""
from hashlib import sha256
import json
from pathlib import Path

AUDIT = Path("docs/results/NEU-01-G06-P01-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G06-P01-first-run/archive-index.json")
FROZEN_SHA = "0634b51a93e93587e840190a0ab4990e18a585f91e2054c4016815f59915e962"


def test_original_g06_sha256_and_original_byte_length():
    content = AUDIT.read_bytes()
    assert len(content) == 8826
    assert sha256(content).hexdigest() == FROZEN_SHA
    assert content.endswith(b"\n")


def test_original_source_protocol_and_runner_anchor():
    idx = json.loads(INDEX.read_text())
    assert idx["protocol_only_commit"] == "4dba6178e2d2092ef15cf0f55f5641996a95896c"
    assert idx["first_source_implementation_commit"] == "bee40dbc0431da00bcb0c178988550dc1caaf3cf"
    assert idx["first_source_attempt_number"] == 1
    assert idx["first_source_workflow_run_id"] == 43331670355
    assert idx["synthetic_adversarial_tests_before_source"] == 11
    assert idx["original_artifact"]["id"] == 13994129065
    assert idx["original_audit_json"]["sha256"] == FROZEN_SHA
    assert idx["no_eeg_sample_values_read"] is True


def test_source_versus_derivative_claims_do_not_exceed_head_data():
    d = json.loads(AUDIT.read_text())
    assert d["status"] == "NAMED_SOURCE_DERIVATIVE_POINTER_PAIRS_PRESENT"
    assert d["derivative_head_decision"] == "SIX_DERIVATIVES_HEAD_SIZE_MATCHED"
    assert d["new_eeg_values_read"] == 0
    assert d["derivative_body_md5_verified"] is False
    assert d["numeric_sample_alignment_verified"] is False
    assert d["preprocessing_stage_causally_identified"] is False
    meta = d["source_metadata"]
    assert meta["dataset_type_from_json"] == "raw"
    assert meta["root_eeg_file_count"] == 900
    assert meta["derivative_set_file_count"] == 900
    assert meta["published_derivatives_code"] == [
        "derivatives/code/figure6_plotSpectrum.m",
        "derivatives/code/figure7_topo.m",
    ]
    pairs = meta["source_pairs"]
    assert len(pairs) == 6
    assert {(x["participant_id"], x["task"]) for x in pairs} == {
        (s,t) for s in ("sub-02","sub-03","sub-04")
        for t in ("eyesclosed","eyesopen")
    }
    assert all(x["source_git_pointer"]["announced_size"] == 36600000 for x in pairs)
    assert all(x["derivative_git_pointer"]["announced_size"] == 73824136 for x in pairs)
    assert all(x["source_git_pointer"]["body_downloaded"] is False for x in pairs)
    assert all(x["derivative_git_pointer"]["body_downloaded"] is False for x in pairs)
    assert all(x["sample_level_pair_alignment_verified"] is False for x in pairs)
    assert len({x["derivative_git_pointer"]["announced_md5"] for x in pairs}) == 6
    assert len(d["derivative_head_results"]) == 6
    assert all(x["outcome"] == "DERIVATIVE_HEAD_SIZE_MATCH" for x in d["derivative_head_results"])
    assert all(x["reported_size"] == 73824136 for x in d["derivative_head_results"])


def test_deliberate_archive_mutation_rejected():
    raw = AUDIT.read_bytes()
    changed = raw.replace(b"73824136", b"73824135", 1)
    assert changed != raw
    assert sha256(changed).hexdigest() != FROZEN_SHA
