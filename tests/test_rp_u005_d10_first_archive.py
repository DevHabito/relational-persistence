"""First RP-U005-D10 source-only temporal metadata result: immutable SHA guards.

All values are non-identifying aggregate counts from the original first JSON.
"""
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest


ROOT = Path("docs/results/RP-U005-D10-first-run")
PINNED_SHA = "75b91c94447c4da58f0f95fa785efd47a7f72c8562f0a84a48d72983c226909d"
EXPECTED_ZIPS = {
    "occ_2026": "7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c",
    "int_2026": "87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d",
}
EXPECTED_DECODED = {
    "occ_2026": "736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567",
    "int_2026": "4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce",
}
EXPECTED_PAIRS = {"F_all_full_code_unique_pairs": 3307396,
                  "S_dictionary_width_unique_pairs": 2716202,
                  "F_only_long_code_unique_pairs": 591194}
PARTITIONS = (
    ("time_overlap", "time_disjoint", "time_unknown"),
    ("feeder_equal", "feeder_different", "feeder_unknown"),
    ("substation_equal", "substation_different", "substation_unknown"),
)


def read_first(root=ROOT):
    raw = (root / "audit.json").read_bytes()
    index = json.loads((root / "archive-index.json").read_text(encoding="utf-8"))
    if sha256(raw).hexdigest() != PINNED_SHA:
        raise ValueError("D10 first source report bytes changed")
    if index["original_json_sha256"] != PINNED_SHA:
        raise ValueError("D10 first archive index differs from pinned SHA")
    return json.loads(raw), index


def test_registered_first_run_and_separate_unknowns():
    source, index = read_first()
    assert index["protocol_only_commit"] == "d0a7afed425ac7460a4e2be94a6a723869847381"
    assert index["original_code_workflow_commit"] == "c8655fc38e49954e63e17edd06281b05705232ac"
    assert index["original_run_id"] == "42522701731"
    assert source["protocol_commit"] == index["protocol_only_commit"]
    assert source["decision"] == index["original_decision"] == "SOURCE_PAIR_METADATA_CENSUS_COMPLETE"
    assert source["original_identifiers_dates_or_event_rows_uploaded"] is False
    assert source["physical_incident_identity_proven"] is False
    assert source["causal_repair_policy_tested"] is False
    assert source["one_to_one_pair_metadata"]["histories_of_actual_operator_decisions_audited"] is False


def test_original_source_shas_and_d09_multi_group_reference():
    source, index = read_first()
    rows={x["source_id"]:x for x in source["original_source_aggregates"]}
    assert set(rows) == set(EXPECTED_ZIPS)
    for key, item in rows.items():
        assert item["compressed_sha256"] == EXPECTED_ZIPS[key]
        assert item["decoded_sha256"] == EXPECTED_DECODED[key]
        assert item["compressed_sha256"] == index["sources"][key]["compressed_sha256"]
        assert item["zip_crc_eof_checked"] is True
    reference=source["reference_D09_literal_key_counts"]
    assert reference["F"] == {"all": 3609614, "one_to_one": 3307396,
                              "one_to_many": 301957, "many_to_one": 0, "many_to_many": 261}
    assert reference["S"] == {"all": 2968556, "one_to_one": 2716202,
                              "one_to_many": 252093, "many_to_one": 0, "many_to_many": 261}
    for group in (reference["S"],reference["F"]):
        assert group["all"] == sum(group[x] for x in (
            "one_to_one","one_to_many","many_to_one","many_to_many"))


@pytest.mark.parametrize("name",list(EXPECTED_PAIRS))
def test_pair_interval_and_code_denominators(name):
    source,_ = read_first()
    group=source["one_to_one_pair_metadata"][name]
    expected=EXPECTED_PAIRS[name]
    assert group["pairs"] == expected
    for cats in PARTITIONS:
        assert sum(group[x] for x in cats) == expected
    assert group["time_touching"] <= group["time_overlap"]
    assert group["both_codes_equal"] <= min(group["feeder_equal"],group["substation_equal"])
    assert group["unknown_int_missing"] <= group["time_unknown"]
    assert group["unknown_occ_missing"] <= group["time_unknown"]


def test_first_source_full_cohort_critical_observations_and_nested_conservation():
    doc,_ = read_first()
    groups=doc["one_to_one_pair_metadata"]
    f=groups["F_all_full_code_unique_pairs"]
    s=groups["S_dictionary_width_unique_pairs"]
    long=groups["F_only_long_code_unique_pairs"]
    assert (f["time_overlap"],f["time_disjoint"],f["time_unknown"]) == (3297487,668,9241)
    assert (f["feeder_equal"],f["feeder_different"],f["feeder_unknown"]) == (3288117,19279,0)
    assert (f["substation_equal"],f["substation_different"],f["substation_unknown"]) == (
        1058781,8795,2239820)
    assert (f["unknown_int_missing"],f["unknown_occ_missing"]) == (9241,5799)
    assert (long["time_overlap"],long["time_disjoint"],long["time_unknown"]) == (
        591165,29,0)
    assert long["pairs"] == f["pairs"]-s["pairs"]
    for name in f:
        assert f[name] == s[name] + long[name]


def test_altered_original_json_never_passes_even_with_forged_index(tmp_path):
    for filename in ("audit.json","archive-index.json"):
        copyfile(ROOT/filename,tmp_path/filename)
    changed=(tmp_path/"audit.json").read_bytes()+b" "
    (tmp_path/"audit.json").write_bytes(changed)
    manifest_path=tmp_path/"archive-index.json"
    index=json.loads(manifest_path.read_text(encoding="utf-8"))
    index["original_json_sha256"]=sha256(changed).hexdigest()
    manifest_path.write_text(json.dumps(index),encoding="utf-8")
    with pytest.raises(ValueError,match="first source report bytes changed"):
        read_first(tmp_path)
