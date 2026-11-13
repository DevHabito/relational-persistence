"""Adversarial G08 fixed-grid and zero-lag synthetic tests (no source I/O)."""
from __future__ import annotations
from hashlib import sha1
from io import BytesIO
import numpy as np
import pytest
from experiments import neu01_g08_fixed_pair as g


def valid_labels():
    return [f"e{i}" for i in range(g.N_CHANNELS)]


def test_label_casefold_only_and_no_fuzzy_maps():
    assert g.label(" Fp1 ") == "fp1"
    assert g.label("FCZ") == "fcz"
    assert g.label("F-P1") != g.label("Fp1")
    with pytest.raises(g.SourceNotEligible):
        g.label("")
    with pytest.raises(g.SourceNotEligible):
        g.label(123)


def test_brainvision_and_bids_channel_parsers_on_exactly_61_rows(monkeypatch):
    from experiments import neu01_g04_independent_replay as root
    # Dedicated synthetic header permitted; do not assert it is a source header.
    fields = "\n".join(f"Ch{i}=E{i-1},,1," for i in range(1,62))
    header = (
        "Brain Vision Data Exchange Header File Version 1.0\n"
        "[Common Infos]\n"
        "DataFile=sub-02_ses-session1_task-eyesclosed_eeg.eeg\n"
        "MarkerFile=sub-02_ses-session1_task-eyesclosed_eeg.vmrk\n"
        "DataFormat=BINARY\nDataOrientation=MULTIPLEXED\n"
        "NumberOfChannels=61\nSamplingInterval=2000\n"
        "[Binary Infos]\nBinaryFormat=IEEE_FLOAT_32\n"
        "[Channel Infos]\n" + fields + "\n"
    ).encode("latin1")
    monkeypatch.setattr(root,"header_audit",lambda content,s,t:{"channels":61})
    assert g.parse_brainvision_header(header) == valid_labels()
    text = "name\ttype\tunits\tsampling_frequency\n" + "".join(
        f"E{i}\tEEG\tuV\t500\n" for i in range(61))
    names, info = g.parse_bids_channel_labels(text.encode())
    assert names == valid_labels()
    assert info["units_declared_in_bids_channels_tsv"] == "uV"
    with pytest.raises(g.SourceNotEligible,match="BIDS_CHANNEL_UNITS"):
        g.parse_bids_channel_labels(text.replace("\tuV\t", "\tnV\t",1).encode())


def test_malformed_or_substituted_original_source_archive_fails(monkeypatch,tmp_path):
    g.check_prior_source_evidence()
    p=tmp_path/"fake.json"
    p.write_bytes(b"corrupted")
    with pytest.raises(g.SourceNotEligible,match="IMMUTABLE"):
        g.hash_archive(p, 6022, g.ORIGINAL_G04_SHA)


def test_bids_original_git_sha1_authentication_synthetic(monkeypatch):
    raw=b"sample text"
    monkeypatch.setattr(g,"ROOT_SIDECAR_BYTES",len(raw))
    monkeypatch.setattr(g,"ROOT_SIDECAR_SHA1",g._git_blob_sha1(raw))
    class Fake(BytesIO):
        def __init__(self,url):
            super().__init__(raw);self.url=url
        def geturl(self):return self.url
    result = g.acquire_pinned_channel_tsv(opener=lambda req,timeout=45:Fake(req.full_url))
    assert result==raw
    with pytest.raises(g.SourceNotEligible,match="WRONG_BIDS"):
        g.acquire_pinned_channel_tsv(opener=lambda req,timeout=45:Fake("https://other.example.com"))


def aligned(**updates):
    names=valid_labels()
    args=dict(
        labels_root=names,labels_bids=list(names),labels_derived=list(names),
        times=np.arange(g.N_FRAMES)*2.,
        xmin=0.,xmax=299.998,rate=500.,
        n_channels=61,n_points=150000,n_trials=1,
        data_shape=(61,150000),reference="common",
    )
    args.update(updates)
    return g.inspect_fixed_grid(**args)


def test_strict_order_and_grid_gate_accepts_valid_metadata_without_claiming_absolute_time():
    r=aligned()
    assert r["metadata_gate_passed"] is True
    assert r["channel_order_identical"] is True
    assert r["relative_time_grid_zero_anchored_2ms_eligible"] is True
    assert r["absolute_acquisition_onset_aligned"] is False
    assert len(r["original_ordered_labels_sha256"])==64


def test_channel_permutation_without_heuristics_rejected():
    names=valid_labels()
    names[0],names[1]=names[1],names[0]
    r=aligned(labels_derived=names)
    assert r["metadata_gate_passed"] is False
    assert r["channel_sets_identical"] is True
    assert r["matched_channel_labels_same_positions"]==59
    assert "DERIVATIVE_LABEL_ORDER_NOT_IDENTICAL" in r["metadata_rejection_reasons"]


def test_fixed_time_offset_and_drift_are_rejected():
    assert not aligned(times=np.arange(g.N_FRAMES)*2.+2.)["metadata_gate_passed"]
    drift=np.arange(g.N_FRAMES)*2. + np.arange(g.N_FRAMES)*0.00001
    assert not aligned(times=drift)["metadata_gate_passed"]
    assert not aligned(times=np.full(g.N_FRAMES,np.nan))["metadata_gate_passed"]
    assert not aligned(xmax=300.)["metadata_gate_passed"]
    assert not aligned(n_channels=60)["metadata_gate_passed"]


def test_declarative_unit_of_channels_even_if_header_has_missing_units():
    names=valid_labels()
    r=aligned(labels_bids=names[::-1])
    assert r["metadata_gate_passed"] is False
    assert "ROOT_BRAINVISION_VERSUS_BIDS_LABEL_ORDER_DIFFER" in r["metadata_rejection_reasons"]


def slow_pearson(x,y):
    xs=[float(z) for z in x];ys=[float(z) for z in y]
    a=sum(xs)/len(xs);b=sum(ys)/len(ys)
    dx=[z-a for z in xs];dy=[z-b for z in ys]
    numerator=sum(s*t for s,t in zip(dx,dy))
    return numerator / (sum(z*z for z in dx)*sum(z*z for z in dy))**0.5


def test_zero_lag_pearson_matches_independent_nested_loop_oracle():
    a=np.array([[1.,2.],[2.,3.],[3.,5.],[7.,4.],[4.,8.]],dtype=float)
    b=np.array([[3.,4.],[1.,7.],[5.,6.],[9.,2.],[4.,5.]],dtype=float)
    c=g.channel_corr(a,b)
    assert np.allclose(c,[slow_pearson(a[:,i],b[:,i]) for i in range(2)],atol=1e-12)
    assert np.allclose(g.channel_corr(a,-a),[-1.,-1.],atol=1e-12)


def test_per_frame_common_projection_and_fixed_shift_are_not_fit():
    a=np.array([[1.,2.],[2.,5.],[3.,2.],[8.,1.],[7.,3.]],dtype=float)
    projected=a-a.mean(axis=1,keepdims=True)
    assert np.allclose(projected.sum(axis=1),0.)
    assert np.allclose(np.roll(projected,2,axis=0)[0],projected[-2])
    with pytest.raises(g.SignalNotEligible,match="ZERO_VARIANCE"):
        g.channel_corr(a,np.ones_like(a))
    with pytest.raises(g.SignalNotEligible,match="NONFINITE"):
        g.channel_corr(a,np.full_like(a,np.nan))


def test_derivative_label_types_and_duplicate_fail_without_names_logged():
    from types import SimpleNamespace
    names=[SimpleNamespace(labels=f"E{i}") for i in range(61)]
    assert g.extract_derivative_labels(np.array(names,dtype=object)) == valid_labels()
    names[-1].labels="E0"
    with pytest.raises(g.SourceNotEligible,match="NOT_UNIQUE"):
        g.extract_derivative_labels(np.array(names,dtype=object))
