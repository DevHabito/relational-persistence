"""U010 purely synthetic publisher-source and recovery-capability safeguards."""
from __future__ import annotations

import json
import pytest

from experiments import rp_u010_daypsci_source_inventory as inv


def test_exact_publisher_identifier_and_all_four_safe_seed_urls():
    assert inv.PROTOCOL_ONLY_COMMIT == "25d1041ab086b2c19273b5e32061ed6f130df0cb"
    assert inv.DATASET_DOI == "10.71486/2drf-1g53"
    assert inv.DATASET_HANDLE == "10259/11686"
    assert len(inv.SEEDS) == 4
    assert inv.MAX_PROBES == 12
    assert inv.MAX_METADATA_BYTES == 2 * 1024 * 1024


@pytest.mark.parametrize("url", (
    "http://riubu.ubu.es/handle/10259/11686",
    "https://evil.example/handle/10259/11686",
    "https://api.datacite.org/dois/10.1234/not-original",
    "https://hdl.handle.net/10259/12345",
    "https://x:secret@riubu.ubu.es/server/api/core/items/123",
))
def test_official_source_refuses_untrusted_or_substituted_urls(url):
    with pytest.raises(inv.InvalidDiscovery):
        inv.authorize_url(url)


@pytest.mark.parametrize("url", (
    "https://riubu.ubu.es/server/api/core/bitstreams/id/content",
    "https://riubu.ubu.es/bitstreams/id/download",
    "https://riubu.ubu.es/attachments/a.csv",
    "https://riubu.ubu.es/attachments/b.pcapng",
    "https://riubu.ubu.es/attachments/c.zip",
))
def test_source_inventory_never_downloads_original_experiment_files(url):
    with pytest.raises(inv.InvalidDiscovery, match="A01_CANNOT_FETCH_EXPERIMENTAL_DATA"):
        inv.request_metadata(url)


def datacite(doi="10.71486/2drf-1g53",title="DAYPSCI v1"):
    return json.dumps({"data":{"attributes":{
        "doi":doi,"titles":[{"title":title}],
        "url":"https://riubu.ubu.es/handle/10259/11686",
    }}}).encode()


def test_doi_metadata_cannot_be_mistaken_for_downloadable_original():
    p=inv.unpack_metadata(
        datacite(),"application/json",source_url=inv.DATASET_API
    )
    assert p["identity_verified"] is True
    assert p["kind"]=="datacite_doi"
    assert p["claimed_source_files"]==[]
    assert inv.status_from_discovery([{"http_status":200,"identity_verified":True}],[])==(
        "RP_U010_A01_METADATA_ONLY_SOURCE_FILES_NOT_RESOLVED"
    )


def test_wrong_data_cite_doi_or_title_fails():
    for payload in (datacite(doi="10.1234/mirror"),datacite(title="Unrelated")):
        with pytest.raises(inv.InvalidDiscovery):
            inv.unpack_metadata(payload,"application/json",source_url=inv.DATASET_API)


def test_official_dspace_manifest_is_source_descriptor_not_source_download():
    record={
        "_embedded":{"bitstreams":[{"name":"pn_baseline_batch01.csv",
          "sizeBytes":451,
          "checkSum":{"checkSumAlgorithm":"SHA-256","value":"a"*64},
          "_links":{"content":{
              "href":"https://riubu.ubu.es/server/api/core/bitstreams/uuid/content"
          }}}]},
        "_links":{},
    }
    parsed=inv.parse_json_metadata(record,source_url=inv.DSpace_API)
    assert len(parsed["claimed_source_files"])==1
    one=parsed["claimed_source_files"][0]
    assert one["size_bytes"]==451 and one["publisher_checksum_value"]=="a"*64
    assert inv.status_from_discovery([{"http_status":200}],parsed[
        "claimed_source_files"])==inv.DISCOVERY_STATUS[0]


def test_dspace_external_file_host_and_missing_size_are_not_accepted():
    p={"_embedded":{"bitstreams":[
        {"name":"bad.csv","sizeBytes":45,"_links":{
            "content":{"href":"https://untrusted.org/fake.csv"}}},
        {"name":"missing.csv","_links":{
            "content":{"href":"https://riubu.ubu.es/anything/download"}}},
    ]}}
    parsed=inv.parse_json_metadata(p,source_url=inv.DSpace_API)
    assert parsed["claimed_source_files"] == []


def test_hosted_audit_does_not_fake_recovery_from_paper_only(monkeypatch):
    monkeypatch.setattr(inv,"request_metadata",
        lambda u: {"http_status":404,"final_url":u,"requested_url":u,
                   "content_type":None,"body_bytes":0,"sha256":None,
                   "redirect_chain":[],"body":b""})
    result=inv.live_manifest_inventory()
    assert result["status"]==inv.DISCOVERY_STATUS[2]
    assert result["file_descriptor_count"]==0
    assert result["first_source_original_csv_or_pcapng_downloaded"] is False
    assert result["independent_functional_recovery_endpoint_verified"] is False
    assert result["actual_fault_deactivation_verified"] is False


def test_body_limit_and_original_csv_path_are_disallowed_before_fetch():
    with pytest.raises(inv.InvalidDiscovery,match="BODY_EXCEEDS_BOUND"):
        inv.unpack_metadata(b"x"*(inv.MAX_METADATA_BYTES+1),
                            "text/html",source_url=inv.RIUBU_LANDING)
    assert inv.looks_like_source_attachment(
        "https://riubu.ubu.es/server/api/core/bitstreams/uuid/content")
