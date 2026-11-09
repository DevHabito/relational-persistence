"""Checksum-pinned original NEU-01-G01 two-condition EEG-source report.

No raw participant samples are stored or examined by these tests. They check
the exact first hosted audit JSON, which was produced after synthetic preflight.
"""
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest

from experiments import neu01_g01_brainvision_auth as g

ROOT=Path("docs/results/NEU-01-G01-first-run")
FIRST_DIGEST="e43ccdb5523bcf14b07ec52ed28ef57200ce4ec2e8268d17f011b9bcd6f0e243"
HASHES={
    ("eyesclosed","vhdr"):"b3f437f5e1cc95b3dbedb989d9c637c832ae4406b55782f8c8aeeb2fefc96061",
    ("eyesclosed","vmrk"):"c75c687404dd131319d45f76fe131af5bdbbe6d880ca2cf426a5fc1e99b5d1e4",
    ("eyesclosed","eeg"):"022b9f34914e4314f4d9e45d17bc367031c9d9d879ea983a8d6eb43f7affbc47",
    ("eyesopen","vhdr"):"7a02a0d6d25413ebc1600a737f2d30f33fc4fc608b25c03564f5918463c3845f",
    ("eyesopen","vmrk"):"d03aa7ccdd3a151ce58adbbc239be26d2dc2eb9ed3d8e134d2427b839f8e6852",
    ("eyesopen","eeg"):"d4c9357b8996fa8e989317d9c945b8e71adfe9e3564c96812689c9cf29e09ac9",
}


def first(root=ROOT):
    raw=(root/"audit.json").read_bytes()
    index=json.loads((root/"archive-index.json").read_text(encoding="utf-8"))
    if sha256(raw).hexdigest()!=FIRST_DIGEST:
        raise ValueError("NEU-01-G01 first original report has changed")
    if index["first_source_report_sha256"]!=FIRST_DIGEST:
        raise ValueError("NEU-01-G01 first index does not match pinned digest")
    return json.loads(raw),index


def test_first_source_run_identity_and_preanalysis_gate():
    report,index=first()
    assert index["first_completed_raw_source_run"]==42628788400
    assert index["first_completed_raw_source_workflow_commit"]=="1519960c8ea42692e98ac3ca3544274a27c2a19c"
    assert index["first_synthetic_tests_passed"]==17
    assert report["protocol_only_commit"]==index["frozen_raw_content_protocol_commit"]==g.PROTOCOL_SHA
    assert report["source_dataset_git_commit"]==index["tag_commit"]==g.SOURCE_COMMIT
    assert report["decision"]=="ORIGINAL_BRAINVISION_PAIR_AUTHENTICATED"
    assert report["original_eeg_samples_or_markers_published"] is False
    assert report["lzc_computed"] is False
    assert report["psychiatric_biomarker_tested"] is False
    assert index["original_signal_sample_values_exported"] is False


def test_exact_six_source_hashes_and_source_size_invariants():
    report,_=first()
    originals=report["original_files"]
    assert len(originals)==6
    assert len({(r["task"],r["source_file_type"]) for r in originals})==6
    for item in originals:
        key=(item["task"],item["source_file_type"])
        assert item["original_annex_md5_confirmed"] is True
        assert item["sha256"]==HASHES[key]
        assert item["bytes"]==g.SOURCE[key[0]][key[1]][0]
    assert sum(1 for x in originals if x["source_file_type"]=="eeg")==2


def test_original_header_and_tsv_61_channels_with_eyesclosed_json64():
    report,index=first()
    assert report["cross_condition_exact_named_channel_intersection_count"]==61
    for task in ("eyesclosed","eyesopen"):
        item=report["task_header_vs_sidecar"][task]
        assert item["source_header_number_of_channels"]==61
        assert item["tsv_channel_rows"]==61
        assert item["header_to_tsv_names_exactly_equal"] is True
        assert item["source_channels_tsv_git_blob_verified"] is True
        assert item["source_binary_samples_per_channel"]==150000
        assert item["source_header_rate_hz"]==500
        assert item["source_header_format"]=="IEEE_FLOAT_32"
        assert item["source_binary_duration_seconds"]==300
        assert item["marker_record_count"]==151
        assert item["source_header_sampling_interval_microseconds"]=="2000"
    closed=report["task_header_vs_sidecar"]["eyesclosed"]
    open_=report["task_header_vs_sidecar"]["eyesopen"]
    assert (closed["bids_json_eeg_channel_count"],
            closed["bids_json_channel_count_agrees_with_vhdr"])==(64,False)
    assert (open_["bids_json_eeg_channel_count"],
            open_["bids_json_channel_count_agrees_with_vhdr"])==(61,True)
    assert 61*150000*4==36600000
    assert index["cross_condition_common_names"]==61


def test_corrupt_original_json_detected_even_with_forged_manifest(tmp_path):
    for name in ("audit.json","archive-index.json"):
        copyfile(ROOT/name,tmp_path/name)
    path=tmp_path/"audit.json"
    replaced=path.read_bytes()+b"\n"
    path.write_bytes(replaced)
    ix=tmp_path/"archive-index.json"
    metadata=json.loads(ix.read_text(encoding="utf-8"))
    metadata["first_source_report_sha256"]=sha256(replaced).hexdigest()
    ix.write_text(json.dumps(metadata),encoding="utf-8")
    with pytest.raises(ValueError,match="first original report has changed"):
        first(tmp_path)
