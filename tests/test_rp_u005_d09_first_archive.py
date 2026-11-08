"""RP-U005-D09 first original dual-cohort result is SHA-pinned, never recomputed.

These regression tests read *numeric source audit metadata only*; no original
CNPJ, incident ID, ZIP, CSV, or temporary SQL key store is present in Git.
"""
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest


ROOT = Path("docs/results/RP-U005-D09-first-run")
ORIGINAL_JSON_SHA = "24b869d0f9c85783ced0d42161cf645b25d07f704d5874538cb0eb9b885fbf3e"
EXPECTED_ROWS = {"occ_2026": 6789484, "int_2026": 6078331}
EXPECTED_ELIGIBLE_S = {"occ_2026": 4860213, "int_2026": 4784823}
EXPECTED_LONG = {"occ_2026": 1929271, "int_2026": 1293508}
EXPECTED_SOURCE_ZIPS = {
    "occ_2026": "7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c",
    "int_2026": "87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d",
}


def first(root=ROOT):
    original = (root / "audit.json").read_bytes()
    index = json.loads((root / "archive-index.json").read_text(encoding="utf-8"))
    if sha256(original).hexdigest() != ORIGINAL_JSON_SHA:
        raise ValueError("Original D09 source report SHA-256 changed")
    if index["first_json_sha256"] != ORIGINAL_JSON_SHA:
        raise ValueError("Original D09 archive index differs from pinned digest")
    return json.loads(original), index


def test_first_source_chronology_and_no_physical_claim():
    doc, index = first()
    assert index["protocol_only_commit"] == (
        "ae9e00e0e0ca2fcd5b08da286923f54f02a6e71c"
    )
    assert index["first_source_code_workflow_commit"] == (
        "b4c3678f597d749e5ace16a36c9217a7b9ce3972"
    )
    assert index["first_source_workflow_run_id"] == "42520496111"
    assert doc["decision"] == "BOTH_SOURCE_DUAL_KEY_CENSUS_AUDITED"
    assert doc["protocol_commit"] == index["protocol_only_commit"]
    assert doc["identifiable_source_rows_or_keys_uploaded"] is False
    assert doc["causal_effect_computed"] is False
    assert doc["semantic_incident_identity_proven"] is False
    assert doc["census"]["repair_policy_or_causal_effect_tested"] is False
    assert doc["census"]["event_time_or_feeder_consistency_verified"] is False


def test_original_source_bytes_count_and_dual_cohort_denominators():
    doc, index = first()
    source_rows = {x["source_id"]: x for x in doc["original_source_aggregates"]}
    assert set(source_rows) == set(EXPECTED_ROWS)
    assert set(index["source_snapshots"]) == set(source_rows)
    for source_id, row in source_rows.items():
        total = EXPECTED_ROWS[source_id]
        long = EXPECTED_LONG[source_id]
        assert row["original_csv_data_rows"] == total
        assert row["original_zip_sha256"] == EXPECTED_SOURCE_ZIPS[source_id]
        assert row["original_zip_sha256"] == index["source_snapshots"][source_id]["compressed_sha256"]
        assert row["original_decompressed_sha256"] == index["source_snapshots"][source_id]["decoded_sha256"]
        assert row["zip_crc_eof_verified"] is True
        assert row["full_key_eligible_rows"] == total
        assert row["full_key_ineligible_rows"] == 0
        assert row["short_key_eligible_rows"] == EXPECTED_ELIGIBLE_S[source_id]
        assert row["short_key_ineligible_rows"] == long
        assert row["long_code_rows_in_original"] == long
        assert row["full_eligible_long_code_rows"] == long
        assert all(x == 0 for x in row["invalid_reason_counts_full_nonexclusive"].values())
        assert row["invalid_reason_counts_short_nonexclusive"]["code_longer_than_10"] == long
        assert row["identifiers_or_source_rows_emitted"] is False


@pytest.mark.parametrize("cohort,matched,one,one_many,many_one,many_many,occr,intp", [
    ("cohort_S_documented_width_at_most_10", 2968556, 2716202, 252093, 0, 261, 2968817, 3863579),
    ("cohort_F_full_original_code", 3609614, 3307396, 301957, 0, 261, 3609875, 4651463),
])
def test_key_cardinalities_and_source_row_conservation(cohort, matched, one, one_many,
                                                        many_one, many_many, occr, intp):
    doc, _ = first()
    result = doc["census"][cohort]
    links = result["literal_cross_source_key_counts"]
    assert links["matched_distinct_keys"] == matched
    assert links["one_to_one_keys"] == one
    assert links["one_to_many_keys"] == one_many
    assert links["many_to_one_keys"] == many_one
    assert links["many_to_many_keys"] == many_many
    assert sum(links[k] for k in (
        "one_to_one_keys", "one_to_many_keys",
        "many_to_one_keys", "many_to_many_keys"
    )) == matched
    assert links["matched_occurrence_source_rows"] == occr
    assert links["matched_interruption_source_rows"] == intp
    assert links["same_key_short_flag_disagreements"] == 0
    eligible_field = ("short_key_eligible_rows" if cohort.startswith("cohort_S")
                      else "full_key_eligible_rows")
    by_id = {x["source_id"]: x for x in doc["original_source_aggregates"]}
    for dataset, matched_field in (
        ("occ_2026", "matched_occurrence_source_rows"),
        ("int_2026", "matched_interruption_source_rows"),
    ):
        src = result["source_group_counts"][dataset]
        assert (src["matched_valid_source_rows"] + src["unmatched_valid_source_rows"]
                == by_id[dataset][eligible_field])
        assert (src["distinct_candidate_keys"] ==
                src["unmatched_distinct_keys"] + matched)
        assert (src["keys_occurring_once"] + src["repeated_distinct_keys"]
                == src["distinct_candidate_keys"])
        assert (src["source_rows_on_repeated_keys"]
                == src["surplus_rows_beyond_first"] + src["repeated_distinct_keys"])
        assert src["matched_valid_source_rows"] == links[matched_field]


def test_long_code_match_increment_is_frozen_and_never_truncation():
    doc, index = first()
    cohorts = doc["census"]
    small = cohorts["cohort_S_documented_width_at_most_10"]["literal_cross_source_key_counts"]
    whole = cohorts["cohort_F_full_original_code"]["literal_cross_source_key_counts"]
    assert whole["matched_distinct_keys"] - small["matched_distinct_keys"] == 641058
    assert whole["matched_long_code_distinct_keys"] == 641058
    assert whole["matched_long_code_occurrence_rows"] == 641058
    assert whole["matched_long_code_interruption_rows"] == 787884
    assert whole["matched_occurrence_source_rows"] - small["matched_occurrence_source_rows"] == 641058
    assert whole["matched_interruption_source_rows"] - small["matched_interruption_source_rows"] == 787884
    assert index["first_matched_literal_distinct_key_totals"]["additional_in_F"] == 641058


def test_mutated_original_json_not_accepted_even_if_manifest_is_changed(tmp_path):
    for filename in ("audit.json", "archive-index.json"):
        copyfile(ROOT / filename, tmp_path / filename)
    altered = (tmp_path / "audit.json").read_bytes() + b" "
    (tmp_path / "audit.json").write_bytes(altered)
    index_file = tmp_path / "archive-index.json"
    manifest = json.loads(index_file.read_text(encoding="utf-8"))
    manifest["first_json_sha256"] = sha256(altered).hexdigest()
    index_file.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Original D09 source report SHA-256 changed"):
        first(tmp_path)
