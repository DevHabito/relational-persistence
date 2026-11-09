"""NEU-01-G01 strictly synthetic source transport and BrainVision reader tests.

No actual participant voltage is embedded, read or displayed here.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
from io import BytesIO
import subprocess
import sys
from urllib.error import URLError

import pytest

from experiments import neu01_g01_brainvision_auth as g


def fake_fixture(monkeypatch):
    names=[f"F{i}" for i in range(1,62)]
    text_tsv="name\ttype\tunits\tsampling_frequency\n"+ "".join(
        f"{name}\tEEG\tuV\t500\n" for name in names
    )
    tsv=text_tsv.encode("utf-8")
    monkeypatch.setattr(g,"CHANNELS_GIT_BLOB",g.blob_sha1(tsv))
    monkeypatch.setattr(g,"BIDS_DURATION_SECONDS",Decimal(1))
    original=deepcopy(g.SOURCE)
    files={}
    for task in ("eyesclosed","eyesopen"):
        header=(
            "Brain Vision Data Exchange Header File Version 1.0\n"
            "[Common Infos]\n"
            f"DataFile={g.file_name(task,'eeg')}\n"
            f"MarkerFile={g.file_name(task,'vmrk')}\n"
            "DataFormat=BINARY\nDataOrientation=MULTIPLEXED\n"
            "NumberOfChannels=61\nSamplingInterval=2000\n"
            "[Binary Infos]\nBinaryFormat=IEEE_FLOAT_32\n"
            "[Channel Infos]\n"
            + "".join(f"Ch{i}={name},,1,uV\n" for i,name in enumerate(names,1))
        ).encode("latin-1")
        marker=(
            "Brain Vision Data Exchange Marker File Version 1.0\n"
            "[Common Infos]\n"
            f"DataFile={g.file_name(task,'eeg')}\n"
            "[Marker Infos]\nMk1=New Segment,,1,1,0\n"
        ).encode("latin-1")
        # Only zero-valued invented bytes. 500 time samples, 61 channels.
        eeg=b"\x00" * (500*61*4)
        for extension,content in (("vhdr",header),("vmrk",marker),("eeg",eeg),
                                  ("channels.tsv",tsv)):
            files[g.original_https(task,extension)]=content
            if extension!="channels.tsv":
                original[task][extension]=(len(content),hashlib.md5(content).hexdigest())
    monkeypatch.setattr(g,"SOURCE",original)
    class FakeRemote:
        def __init__(self):
            self.called=[]
        def __call__(self,request,timeout=35):
            url=request.full_url
            self.called.append(url)
            return BytesIO(files[url])
    return FakeRemote(),files


def test_frozen_annex_source_keys_and_exact_public_bucket():
    assert g.SOURCE_COMMIT=="0c740d838a2c33feeec0b6e514aea323d0e65ca4"
    assert g.SOURCE["eyesclosed"]["eeg"]==(36600000,"0fceeb9eb4163b86b815061f8fff80d7")
    assert g.SOURCE["eyesopen"]["eeg"]==(36600000,"75e12c6499540e3148316ef502ad03dd")
    assert g.original_https("eyesclosed","vhdr")==(
        "https://s3.amazonaws.com/openneuro.org/ds004148/sub-01/ses-session1/eeg/"
        "sub-01_ses-session1_task-eyesclosed_eeg.vhdr"
    )
    assert g.original_https("eyesopen","channels.tsv").endswith(
        "sub-01_ses-session1_task-eyesopen_channels.tsv"
    )


def test_invented_pair_passes_bounded_complete_source_gate(monkeypatch):
    remote,_=fake_fixture(monkeypatch)
    result=g.evaluate(remote)
    assert result["decision"]=="ORIGINAL_BRAINVISION_PAIR_AUTHENTICATED"
    assert result["all_original_annex_keys_authenticated"] is True
    assert len(result["original_files"])==6
    assert result["cross_condition_exact_named_channel_intersection_count"]==61
    assert result["task_header_vs_sidecar"]["eyesclosed"]["bids_json_eeg_channel_count"]==64
    assert result["task_header_vs_sidecar"]["eyesclosed"]["bids_json_channel_count_agrees_with_vhdr"] is False
    assert result["task_header_vs_sidecar"]["eyesopen"]["bids_json_channel_count_agrees_with_vhdr"] is True
    assert result["original_eeg_samples_or_markers_published"] is False
    assert result["lzc_computed"] is False
    assert result["psychiatric_biomarker_tested"] is False
    assert len(remote.called)==8


def test_forged_source_body_hash_is_rejected(monkeypatch):
    remote,files=fake_fixture(monkeypatch)
    url=g.original_https("eyesclosed","vhdr")
    files[url]+=b" "
    result=g.evaluate(remote)
    assert result["decision"]=="ORIGINAL_SOURCE_HASH_MISMATCH"
    assert "original_files" not in result
    assert result["error_code"]=="SOURCE_BYTES_EXCEED_FROZEN_SIZE"


def test_http_or_dns_failure_is_not_relabelled_as_neural_failure():
    def offline(request,timeout=35):
        raise URLError("synthetic disconnected transport")
    result=g.evaluate(offline)
    assert result["decision"]=="SOURCE_RETRIEVAL_BLOCKED"
    assert result["error_code"]=="PUBLIC_ORIGINAL_OBJECT_NOT_RETRIEVED"
    assert result["original_eeg_samples_or_markers_published"] is False


def test_validated_source_channel_list_discrepancy_blocks_harmonization(monkeypatch):
    remote,files=fake_fixture(monkeypatch)
    url=g.original_https("eyesclosed","channels.tsv")
    tsv=files[url].replace(b"F1\tEEG",b"Q1\tEEG",1)
    files[url]=tsv
    monkeypatch.setattr(g,"CHANNELS_GIT_BLOB",g.blob_sha1(tsv))
    result=g.evaluate(remote)
    assert result["decision"]=="BRAINVISION_LAYOUT_NOT_VERIFIED"
    assert result["error_code"]=="ACTUAL_HEADER_CHANNELS_DIFFER_FROM_TSV"


def test_companion_tsv_changed_from_pinned_git_blob_is_source_integrity_failure(monkeypatch):
    remote,files=fake_fixture(monkeypatch)
    url=g.original_https("eyesclosed","channels.tsv")
    files[url]+=b"# changed\n"
    result=g.evaluate(remote)
    assert result["decision"]=="ORIGINAL_SOURCE_HASH_MISMATCH"
    assert result["error_code"]=="PUBLISHER_TSV_GIT_BLOB_DIFFERENT"


@pytest.mark.parametrize("bad", [
    "bad", "../outside.eeg", "/etc/passwd", r"C:\windows\other.eeg",
])
def test_header_does_not_accept_path_traversal_or_unregistered_names(bad):
    with pytest.raises(g.SourceLayoutError,match="BRAINVISION_FILENAME_MISMATCH"):
        g.must_exact_file(bad,"original.eeg")


def test_unregistered_source_names_rejected_in_optimized_or_normal_mode():
    with pytest.raises(g.SourceLayoutError,match="UNREGISTERED_SOURCE_OBJECT"):
        g.file_name("person-other","eeg")
    with pytest.raises(g.SourceLayoutError,match="UNREGISTERED_SOURCE_OBJECT"):
        g.file_name("eyesclosed","zip")


def test_brainvision_header_bad_channel_count_is_not_silently_normalized(monkeypatch):
    remote,files=fake_fixture(monkeypatch)
    original=files[g.original_https("eyesclosed","vhdr")]
    fake=original.replace(b"NumberOfChannels=61",b"NumberOfChannels=64")
    with pytest.raises(g.SourceLayoutError,match="BRAINVISION_EEG_BYTES_NOT_WHOLE_SAMPLES"):
        g.parse_header("eyesclosed",fake,500*61*4)


def test_strict_header_rate_rejects_one_hertz_drift(monkeypatch):
    remote,files=fake_fixture(monkeypatch)
    original=files[g.original_https("eyesclosed","vhdr")]
    changed=original.replace(b"SamplingInterval=2000",b"SamplingInterval=2001")
    with pytest.raises(g.SourceLayoutError,match="BRAINVISION_SAMPLE_RATE_NOT_500_HZ"):
        g.parse_header("eyesclosed",changed,500*61*4)


def test_marker_datafile_mismatch_fails(monkeypatch):
    _,files=fake_fixture(monkeypatch)
    wrong=files[g.original_https("eyesclosed","vmrk")].replace(
        b"task-eyesclosed_eeg.eeg",b"task-eyesopen_eeg.eeg"
    )
    with pytest.raises(g.SourceLayoutError,match="BRAINVISION_FILENAME_MISMATCH"):
        g.parse_markers("eyesclosed",wrong)


def test_duplicate_channel_names_fail_even_when_array_bytes_match(monkeypatch):
    _,files=fake_fixture(monkeypatch)
    header=files[g.original_https("eyesclosed","vhdr")].replace(
        b"Ch2=F2,",b"Ch2=F1,"
    )
    with pytest.raises(g.SourceLayoutError,match="BRAINVISION_DUPLICATE_CHANNEL_NAMES"):
        g.parse_header("eyesclosed",header,500*61*4)


def test_binary_size_duration_must_be_300_seconds_in_real_protocol(monkeypatch):
    _,files=fake_fixture(monkeypatch)
    monkeypatch.setattr(g,"BIDS_DURATION_SECONDS",Decimal(300))
    with pytest.raises(g.SourceLayoutError,match="BRAINVISION_DURATION_NOT_300_SECONDS"):
        g.parse_header("eyesclosed",files[g.original_https("eyesclosed","vhdr")],
                       500*61*4)


def test_source_validations_survive_python_O_optimization():
    script=(
        "from experiments.neu01_g01_brainvision_auth import file_name,SourceLayoutError;"
        "\ntry:\n file_name('unregistered','eeg');print('BROKEN')"
        "\nexcept SourceLayoutError:\n print('GUARDS_ACTIVE')"
    )
    process=subprocess.run([sys.executable,"-O","-c",script],capture_output=True,
                           text=True,timeout=30,check=False)
    assert process.returncode==0,process.stderr
    assert process.stdout.strip()=="GUARDS_ACTIVE"
