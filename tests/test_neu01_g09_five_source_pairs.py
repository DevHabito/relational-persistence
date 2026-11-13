"""No-network original G09 five source-pair gates; independent format checks."""
from __future__ import annotations
from hashlib import md5,sha256
from io import BytesIO
import numpy as np
import pytest

from experiments import neu01_g09_five_source_pairs as g


def test_exact_predeclared_five_source_pair_set_no_control_added():
    assert len(g.FIVE)==5
    assert [(p[0],p[1]) for p in g.FIVE]==[
        ("sub-02","eyesopen"),("sub-03","eyesclosed"),("sub-03","eyesopen"),
        ("sub-04","eyesclosed"),("sub-04","eyesopen")
    ]
    assert ("sub-02","eyesclosed") not in [(p[0],p[1]) for p in g.FIVE]
    assert len({p[3] for p in g.FIVE})==5
    assert g.DERIV_BYTES==73824136


def test_original_IEEE_and_prior_report_hash_gate_passes():
    g.check_immutable_first_evidence()
    assert g.G08_D03_FIRST_SHA=="0a20ff8636afd7c90057fbd852c55864fd6192b9094dc7310680f40557e54e46"


def test_registered_paths_and_no_external_sources():
    path=g.paths(*g.FIVE[0])
    assert path["header"].endswith("sub-02_ses-session1_task-eyesopen_eeg.vhdr")
    assert path["derivative"]=="derivatives/preprocessed data/preprocessed_data/sub02_01_EO.set"
    with pytest.raises(g.SourceIneligible,match="UNREGISTERED"):
        g.paths("sub-02","eyesclosed","EC","2ba3c01f752799634414e2142544fd9b")
    with pytest.raises(g.SourceIneligible,match="UNREGISTERED"):
        g.paths("sub-02","eyesopen","EO","f"*32)


class FixtureResponse(BytesIO):
    def __init__(self,data,url):
        super().__init__(data);self.url=url
    def geturl(self):return self.url


def test_download_accepts_exact_bounded_md5_and_sha256(monkeypatch,tmp_path):
    payload=b"entirely synthetic no EEG values"
    monkeypatch.setattr(g,"DERIV_BYTES",len(payload))
    spec=g.FIVE[0]
    monkeypatch.setattr(g,"FIVE",((spec[0],spec[1],spec[2],md5(payload).hexdigest()),))
    item=g.FIVE[0]
    from urllib.parse import quote
    target=g.S3_ROOT+quote(g.paths(*item)["derivative"],safe="/")
    got=g.authenticate_derivative(*item,destination=tmp_path/"fresh.set",
            opener=lambda req,timeout:FixtureResponse(payload,target))
    assert got["fully_authenticated_publisher_md5"] is True
    assert got["actual_sha256"]==sha256(payload).hexdigest()
    assert got["bytes"]==len(payload)


def test_download_rejects_changed_md5_and_redirects(monkeypatch,tmp_path):
    content=b"source-unit-tests"
    monkeypatch.setattr(g,"DERIV_BYTES",len(content))
    spec=g.FIVE[0]
    with pytest.raises(g.SourceIneligible,match="MD5_MISMATCH"):
        g.authenticate_derivative(*spec,destination=tmp_path/"wrong.set",
            opener=lambda req,timeout:FixtureResponse(content,req.full_url))
    with pytest.raises(g.SourceIneligible,match="WRONG_DERIVATIVE"):
        g.authenticate_derivative(*spec,destination=tmp_path/"redirect.set",
            opener=lambda req,timeout:FixtureResponse(content,"https://other.example.com/set"))


def test_wrong_source_channel_list_and_time_warp_are_not_accepted():
    from experiments import neu01_g08_fixed_pair as baseline
    labels=[f"ch{i}" for i in range(61)]
    wrong=labels.copy()
    wrong[0],wrong[1]=wrong[1],wrong[0]
    ok=baseline.inspect_fixed_grid(
        labels,list(labels),list(labels),np.arange(150000)*2.,
        0.,299.998,rate=500.,n_channels=61,n_points=150000,n_trials=1,
        data_shape=(61,150000),reference="common",
    )
    assert ok["metadata_gate_passed"] is True
    lost=baseline.inspect_fixed_grid(
        labels,list(labels),wrong,np.arange(150000)*2.,
        0.,299.998,rate=500.,n_channels=61,n_points=150000,n_trials=1,
        data_shape=(61,150000),reference="common",
    )
    assert lost["metadata_gate_passed"] is False
    off=baseline.inspect_fixed_grid(
        labels,list(labels),list(labels),np.arange(150000)*2.+2.,
        0.,299.998,rate=500.,n_channels=61,n_points=150000,n_trials=1,
        data_shape=(61,150000),reference="common",
    )
    assert off["metadata_gate_passed"] is False


def test_direct_source_engine_negative_original_widening_control():
    from experiments import neu01_g08_d03_native_identity as engine
    sample=np.array([[1.,2.],[3.,4.],[5.,6.]],dtype="<f4").astype("<f8")
    same=engine.inspect_direct_arrays(sample,sample.copy(),shift=1)
    assert same["direct_identity_status"]=="EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL"
    changed=sample.copy()
    changed[1,0]+=.25
    differ=engine.inspect_direct_arrays(sample,changed,shift=1)
    assert differ["numeric_differ_count"]==1
    assert differ["direct_identity_status"]=="AUTHENTICATED_NATIVE_ARRAYS_DIFFER"


def test_exact_original_BIDS_tsv_sha1_contract_is_frozen():
    assert g.BIDS_TSV_SHA=="105960eb0ac14bae43bea73aa479a5c6d995c7a3"
    assert g.BIDS_TSV_BYTES==983
