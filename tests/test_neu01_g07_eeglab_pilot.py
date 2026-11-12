"""G07 adversarial checks, all synthetic. No publisher data fetched in tests."""
from hashlib import md5, sha256
from io import BytesIO
from pathlib import Path
import struct
import numpy as np
import pytest
from scipy.io import savemat

from experiments import neu01_g07_eeglab_pilot as g07


def make_fixture(tmp_path):
    path = tmp_path / "synthetic.set"
    sig = np.array([[0.5,1.0,0.5],[2.0,2.5,2.0]],dtype=np.float64)
    savemat(path, {"EEG":{
        "nbchan":2,"pnts":3,"trials":1,"srate":500.0,
        "ref":"average", "data":sig, "history":"synthetic fixture only"
    }},do_compression=False)
    return path


def test_matlab_fixture_metadata_only(tmp_path):
    path=make_fixture(tmp_path)
    m=g07.inspect_eeglab_metadata(path)
    assert m["container_family"]=="MATLAB_V5"
    assert m["metadata_parse_status"]=="EEGLAB_STRUCT_PARSED"
    assert m["nbchan"]==2 and m["pnts"]==3 and m["trials"]==1
    assert m["srate_hz"]==500.0 and m["data_array_shape"]==[2,3]
    assert m["data_array_dtype"]=="float64"
    assert m["reference_label"]=="average"
    assert m["processing_history_provenance"]["contents_published"] is False
    assert m["processing_history_provenance"]["sha256"]==sha256(b"synthetic fixture only").hexdigest()
    assert "synthetic fixture only" not in str(m)
    assert m["sample_alignment_with_bids_verified"] is False
    assert "data" not in m


def test_container_header_classification_negative_cases():
    assert g07.classify_mat_header(b"MATLAB 5.0 MAT-file " + b"x"*100)=="MATLAB_V5"
    assert g07.classify_mat_header(b"MATLAB 7.3 MAT-file " + b"x"*100)=="MATLAB_V73"
    assert g07.classify_mat_header(b"\x89HDF\r\n\x1a\n")=="HDF5"
    assert g07.classify_mat_header(b"")=="UNRECOGNIZED_BINARY"
    assert g07.classify_mat_header(b"EEGLAB maybe?")=="UNRECOGNIZED_BINARY"


def test_missing_eeg_struct_cannot_be_invented(tmp_path):
    path=tmp_path/"other.mat"
    savemat(path,{"OTHER":np.array([1,2,3])})
    m=g07.inspect_eeglab_metadata(path)
    assert m["metadata_parse_status"]=="EEGLAB_STRUCT_MISSING"


def test_metadata_scalar_filters_nonfinite_bad_shapes_and_negative_values():
    assert g07.clean_int(np.array([1,2])) is None
    assert g07.clean_int(float("nan")) is None
    assert g07.clean_int(-1) is None
    assert g07.clean_int(61.0)==61
    assert g07.clean_float(float("inf")) is None
    assert g07.clean_float(500.0)==500.0


class Response(BytesIO):
    def __init__(self,b,link):
        super().__init__(b);self.url=link
    def geturl(self):return self.url


def test_exact_authentication_on_frozen_source_with_fake_bytes(tmp_path,monkeypatch):
    b=b"synthetic data payload not an EEG"
    monkeypatch.setattr(g07,"EXPECTED_BYTES",len(b))
    monkeypatch.setattr(g07,"EXPECTED_MD5",md5(b).hexdigest())
    dest=tmp_path/"copy.set"
    answer=g07.acquire_verified(dest,opener=lambda request,timeout=45:Response(b,g07.SOURCE))
    assert answer["original_bytes"]==len(b)
    assert answer["observed_sha256"]==sha256(b).hexdigest()
    assert dest.read_bytes()==b


def test_download_wrong_hash_truncation_and_redirect_never_succeed(tmp_path,monkeypatch):
    b=b"fake-original"
    monkeypatch.setattr(g07,"EXPECTED_BYTES",len(b))
    monkeypatch.setattr(g07,"EXPECTED_MD5",md5(b).hexdigest())
    def call(payload,url=g07.SOURCE):
        return g07.acquire_verified(tmp_path/"new.set",opener=lambda request,timeout=45:Response(payload,url))
    with pytest.raises(g07.SourceUnavailable,match="MD5_MISMATCH"):
        call(b"FAKE-original")
    (tmp_path/"new.set").unlink()
    with pytest.raises(g07.SourceUnavailable,match="SIZE_MISMATCH"):
        call(b[:-1])
    (tmp_path/"new.set").unlink()
    with pytest.raises(g07.SourceUnavailable,match="WRONG_OBJECT_RESPONSE_URL"):
        call(b,url="https://example.com/changed.set")


def test_more_than_expected_bytes_rejected_before_hash(tmp_path,monkeypatch):
    monkeypatch.setattr(g07,"EXPECTED_BYTES",4)
    with pytest.raises(g07.SourceUnavailable,match="EXCEEDS_EXACT_BYTE_LIMIT"):
        g07.acquire_verified(tmp_path/"excess.set",
            opener=lambda request,timeout=45:Response(b"123456",g07.SOURCE))


def test_registered_publisher_path_is_fixed_and_original_metadata_unchanged():
    assert g07.RELATIVE=="derivatives/preprocessed data/preprocessed_data/sub02_01_EC.set"
    assert g07.EXPECTED_MD5=="2ba3c01f752799634414e2142544fd9b"
    assert g07.PROTOCOL_COMMIT=="6a0e0bd96fd5c8f4d4823c7c02fec0128c8c9d6e"
    assert g07.EXPECTED_BYTES==73824136
    assert "%20" in g07.SOURCE and "s3.amazonaws.com/openneuro.org" in g07.SOURCE
