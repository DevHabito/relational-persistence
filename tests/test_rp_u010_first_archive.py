"""U010 original bounded DOI-only availability audit, immutable first-source checksum."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from experiments import rp_u010_daypsci_source_inventory as source

ORIGINAL = Path("docs/results/RP-U010-A01-first-source/audit.json")
ORIGINAL_BYTES = 2000
ORIGINAL_SHA = "f8434c0e57f3ba38a3a5a19f5c317d1147df4b5babdc09d0480b732a167b3612"


def audit():
    raw = ORIGINAL.read_bytes()
    assert len(raw) == ORIGINAL_BYTES
    assert sha256(raw).hexdigest() == ORIGINAL_SHA
    return json.loads(raw)


def test_immutable_original_hash_and_registered_negative_access_decision():
    j = audit()
    assert j["study"] == "RP-U010-A01"
    assert j["status"] == "RP_U010_A01_METADATA_ONLY_SOURCE_FILES_NOT_RESOLVED"
    assert j["protocol_only_commit"] == source.PROTOCOL_ONLY_COMMIT
    assert j["first_source_runner_commit"] == (
        "073b23dd1a17905b982cebc2e4c1b5e48ce7b3d4"
    )
    assert j["first_source_workflow_id"] == "44215663536"
    assert j["metadata_requests_made"] == 4
    assert j["file_descriptor_count"] == 0
    assert j["file_descriptors_from_official_repository_json"] == []


def test_original_exact_one_datacite_200_and_three_repository_timeout_attempts():
    j = audit()
    attempts = j["publisher_metadata_attempts"]
    assert [a["requested_url"] for a in attempts] == list(source.SEEDS)
    doi = attempts[0]
    assert doi["http_status"] == 200
    assert doi["body_bytes"] == 12464
    assert doi["kind"] == "datacite_doi"
    assert doi["identity_verified"] is True
    assert doi["sha256"] == (
        "943d7af61500634fe8712b4720203c6519f85b17ffe26161963e0a81aca1afe7"
    )
    for a in attempts[1:]:
        assert a["error_type"] == "URLError"
        assert "timed out" in a["error_code"]
        assert a["integrity_violation"] is False


def test_no_raw_or_functional_evidence_claims_are_allowed():
    j = audit()
    assert j["first_source_original_csv_or_pcapng_downloaded"] is False
    assert j["actual_fault_deactivation_verified"] is False
    assert j["independent_functional_recovery_endpoint_verified"] is False
    assert j["plc_pcap_clock_alignment_verified"] is False
    assert j["all_outcome_and_population_inference_prohibited"] is True
    assert source.status_from_discovery(
        j["publisher_metadata_attempts"],
        j["file_descriptors_from_official_repository_json"]
    ) == j["status"]


def test_original_first_source_index_does_not_mislabel_source_file_as_verified():
    index = json.loads(Path(
        "docs/results/RP-U010-A01-first-source/archive-index.json"
    ).read_text(encoding="utf-8"))
    assert index["original_source_audit_sha256"] == ORIGINAL_SHA
    assert index["original_source_audit_size_bytes"] == ORIGINAL_BYTES
    assert index["original_workflow_artifact_id"] == 14388661326
    assert index["original_requests"] == 4
    assert index["original_reachable_metadata_count"] == 1
    assert index["original_reachable_source_file_manifests"] == 0
    assert index["source_library_original_csv_or_pcap_downloaded"] is False
    assert index["first_original_status"] == audit()["status"]
