"""G06 negative metadata controls, no internet or EEG in synthetic tests."""
from __future__ import annotations

from base64 import b64encode
from hashlib import sha1
from io import BytesIO
import json

import pytest

from experiments import neu01_g06_public_lineage as g06


def mkblob(data):
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def pointer(size, md5, kind):
    return ("../../../.git/annex/objects/AB/CD/MD5E-s"
            + str(size) + "--" + md5 + "." + kind
            + "/MD5E-s" + str(size) + "--" + md5 + "." + kind).encode()


def fixture():
    records = {}
    def add(path, body, mode="100644"):
        sha = mkblob(body)
        records[path] = {"path":path, "type":"blob", "mode":mode, "sha":sha, "size":len(body)}
        blobs[sha] = body
    blobs = {}
    add("dataset_description.json", json.dumps({
        "DatasetType":"raw", "DatasetDOI":"doi:10.18112/openneuro.ds004148.v1.0.0"
    }).encode())
    add("derivatives/README", b"pre-processed data - code to reproduce figure6 and figure7")
    for script in g06.EXPECTED_CODE:
        add(script, pointer(1000, "a"*32, "set"), "120000")
    for s in range(1, 61):
        for session in range(1,4):
            for suffix in ("EC","EO","Ma","Me","Mu"):
                path = "derivatives/preprocessed data/preprocessed_data/sub" + (
                    f"{s:02d}_{session:02d}_{suffix}.set"
                )
                add(path, pointer(1000, "b"*32, "set"), "120000")
            for task in ("eyesclosed", "eyesopen", "mathematic", "memory", "music"):
                prefix=(f"sub-{s:02d}/ses-session{session}/eeg/"
                        f"sub-{s:02d}_ses-session{session}_task-{task}_eeg")
                add(prefix+".eeg", pointer(1000, "c"*32, "eeg"), "120000")
    for subject in g06.SUBJECTS:
        for task,short in g06.TASKS:
            pair=g06.paths(subject,task,short)
            a,b = g06.EXPECTED[(subject,task)]
            add(pair["raw"],pointer(g06.RAW_BYTES,a,"eeg"),"120000")
            add(pair["derivative"],pointer(g06.DERIV_BYTES,b,"set"),"120000")
            add(pair["sidecar"],json.dumps({
                "EEGReference":"FCz","SoftwareFilters":"n/a",
                "EEGChannelCount":61,"SamplingFrequency":500
            }).encode())
    return {"truncated":False,"tree":list(records.values())}, blobs


def inspect(tree, blobs):
    return g06.inspect_metadata(tree, lambda s: blobs[s])


def test_synthetic_inventory_exact_six_and_900():
    tree,blobs=fixture()
    d=inspect(tree,blobs)
    assert len(d["source_pairs"])==6
    assert d["root_eeg_file_count"]==900
    assert d["derivative_set_file_count"]==900
    assert d["dataset_type_from_json"]=="raw"
    assert all(p["sample_level_pair_alignment_verified"] is False for p in d["source_pairs"])


def test_truncated_tree_stops():
    tree,blobs=fixture()
    tree["truncated"]=True
    with pytest.raises(g06.ProvenanceStop,match="INCOMPLETE"):
        inspect(tree,blobs)


def test_missing_derivative_stops_not_silently_skipped():
    tree,blobs=fixture()
    name=g06.paths("02","eyesclosed","EC")["derivative"]
    tree["tree"]=[x for x in tree["tree"] if x["path"] != name]
    with pytest.raises(g06.ProvenanceStop,match="900"):
        inspect(tree,blobs)


def test_wrong_pointer_mode_stops():
    tree,blobs=fixture()
    path=g06.paths("03","eyesopen","EO")["derivative"]
    next(x for x in tree["tree"] if x["path"]==path)["mode"]="100644"
    with pytest.raises(g06.ProvenanceStop,match="TREE_ENTRY"):
        inspect(tree,blobs)


def test_wrong_pointer_md5_stops():
    tree,blobs=fixture()
    path=g06.paths("04","eyesclosed","EC")["derivative"]
    item=next(x for x in tree["tree"] if x["path"]==path)
    blobs[item["sha"]]=pointer(g06.DERIV_BYTES,"f"*32,"set")
    with pytest.raises(g06.ProvenanceStop,match="ANNEX_POINTER"):
        inspect(tree,blobs)


def test_wrong_pointer_size_stops():
    tree,blobs=fixture()
    path=g06.paths("02","eyesclosed","EC")["derivative"]
    item=next(x for x in tree["tree"] if x["path"]==path)
    blobs[item["sha"]]=pointer(g06.DERIV_BYTES-1,g06.EXPECTED[("02","eyesclosed")][1],"set")
    with pytest.raises(g06.ProvenanceStop,match="ANNEX_POINTER"):
        inspect(tree,blobs)


def test_mislabelled_raw_and_filter_metadata_stops():
    tree,blobs=fixture()
    path=g06.paths("03","eyesopen","EO")["sidecar"]
    item=next(x for x in tree["tree"] if x["path"]==path)
    blobs[item["sha"]]=json.dumps({
       "EEGReference":"Cz","SoftwareFilters":"Highpass 1Hz",
       "EEGChannelCount":61,"SamplingFrequency":500
    }).encode()
    with pytest.raises(g06.ProvenanceStop,match="SIDECAR"):
        inspect(tree,blobs)


def test_unexpected_pipeline_file_breaks_fixed_directory_claim():
    tree,blobs=fixture()
    tree["tree"].append({"path":"derivatives/code/preprocess.m","sha":"b"*40,
                         "type":"blob","mode":"100644"})
    with pytest.raises(g06.ProvenanceStop,match="CODE_INVENTORY"):
        inspect(tree,blobs)


def test_git_blob_digest_guards_and_unregistered_paths():
    content=b"source metadata"
    sha=mkblob(content)
    fake={"sha":sha,"encoding":"base64","content":b64encode(content).decode()}
    assert g06.read_verified_blob(sha,getter=lambda url:fake)==content
    fake["content"]=b64encode(b"tampered").decode()
    with pytest.raises(g06.ProvenanceStop,match="HASH_MISMATCH"):
        g06.read_verified_blob(sha,getter=lambda url:fake)
    with pytest.raises(g06.ProvenanceStop,match="INVALID_GIT_BLOB_SHA"):
        g06.read_verified_blob("bad", getter=lambda url:fake)
    with pytest.raises(g06.ProvenanceStop,match="UNREGISTERED"):
        g06.paths("99","eyesopen","EO")


def test_head_length_without_payload_is_not_authentication():
    class Header:
        def __init__(self,url,length):
            self.url,self.headers=url,{"Content-Length":str(length)}
        def geturl(self): return self.url
        def __enter__(self): return self
        def __exit__(self,*args): return False
    p=g06.paths("02","eyesclosed","EC")["derivative"]
    from urllib.parse import quote
    u=g06.S3_ROOT+quote(p,safe="/")
    assert g06.public_derivative_head(p,opener=lambda req,timeout:Header(u,g06.DERIV_BYTES))["outcome"]=="DERIVATIVE_HEAD_SIZE_MATCH"
    assert g06.public_derivative_head(p,opener=lambda req,timeout:Header(u,100))["outcome"]=="DERIVATIVE_HEAD_SIZE_MISMATCH"
    assert g06.public_derivative_head(p,opener=lambda req,timeout:Header("https://bad.example",g06.DERIV_BYTES))["outcome"]=="DERIVATIVE_HEAD_NOT_VERIFIED"
    with pytest.raises(g06.ProvenanceStop,match="UNREGISTERED"):
        g06.public_derivative_head("derivatives/other.set",opener=lambda req,timeout:Header(u,g06.DERIV_BYTES))


def test_duplicate_tree_entry_fails_not_replaced():
    tree,_=fixture()
    tree["tree"].append(dict(tree["tree"][0]))
    with pytest.raises(g06.ProvenanceStop,match="DUPLICATE"):
        g06.inspect_tree(tree)
