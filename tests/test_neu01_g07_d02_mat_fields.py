"""G07-D02 negative and synthetic top-level MATLAB metadata census tests."""
from hashlib import sha256
import numpy as np
import pytest
from scipy.io import savemat
from experiments import neu01_g07_d02_mat_fields as d02


def standard_mat(tmp_path, include_data=True):
    path=tmp_path/"synthetic.set"
    variables={"nbchan":np.array([[2]]), "pnts":np.array([[3]]),
               "trials":np.array([[1]]), "srate":np.array([[500.0]]),
               "ref":"average", "history":"synthetic public fixture"}
    if include_data:
        variables["data"]=np.array([[1.,2.,3.],[4.,5.,6.]])
    variables["unlisted_private_variable"]="never log this"
    savemat(path,variables,do_compression=False)
    return path


def test_full_known_top_level_fields_are_resolved_without_amplitude_output(tmp_path):
    path=standard_mat(tmp_path)
    x=d02.inspect_mat_top_level(path)
    assert x["metadata_status"]=="TOPLEVEL_EEGLAB_FIELD_LAYOUT_RESOLVED"
    assert x["nbchan"]==2 and x["pnts"]==3 and x["trials"]==1
    assert x["srate_hz"]==500.0 and x["reference_label"]=="average"
    assert x["safe_known_top_level_fields"]["data"]["dimensions"]==[2,3]
    assert x["total_matlab_variables"]==8
    assert x["other_unpublished_variable_names_count"]==1
    assert "unlisted_private_variable" not in str(x)
    assert "never log this" not in str(x)
    assert "synthetic public fixture" not in str(x)
    assert x["history_identification"]["sha256"]==sha256(b"synthetic public fixture").hexdigest()
    assert x["raw_eeg_values_loaded_by_investigation"] is False
    assert x["source_derivative_sample_alignment_verified"] is False


def test_missing_data_is_not_imputed(tmp_path):
    path=standard_mat(tmp_path,include_data=False)
    x=d02.inspect_mat_top_level(path)
    assert x["metadata_status"]=="TOPLEVEL_LAYOUT_STILL_UNRESOLVED"
    assert "data" in x["missing_required_metadata"]


def test_nested_EEG_struct_only_does_not_forge_missing_data_field(tmp_path):
    path=tmp_path/"nested.set"
    savemat(path,{"EEG":{"data":np.ones((2,3)), "nbchan":2,"pnts":3,"srate":500}})
    x=d02.inspect_mat_top_level(path)
    assert x["metadata_status"]=="TOPLEVEL_LAYOUT_STILL_UNRESOLVED"
    assert "EEG" in x["safe_known_top_level_fields"]
    assert "data" in x["missing_required_metadata"]


def test_invalid_srate_never_misclassified_as_resolved(tmp_path):
    path=tmp_path/"bad.set"
    savemat(path,{"data":np.ones((2,3)),"nbchan":2,"pnts":3,"srate":float("nan")})
    x=d02.inspect_mat_top_level(path)
    assert x["metadata_status"]=="TOPLEVEL_LAYOUT_STILL_UNRESOLVED"
    assert "srate" in x["missing_required_metadata"]


def test_original_g07_status_is_immutable_and_authoritatively_prior():
    o=d02.verify_old_original()
    assert o["status"]=="DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED"
    assert o["derivative_metadata"]["metadata_parse_status"]=="EEGLAB_STRUCT_MISSING"
    assert o["source_identity"]["observed_sha256"]==d02.KNOWN_DERIVATIVE_SHA


def test_prior_g07_archive_mutation_rejected(monkeypatch,tmp_path):
    data=d02.OLD_AUDIT.read_bytes()
    assert sha256(data).hexdigest()==d02.OLD_AUDIT_SHA
    changed=data.replace(b"MATLAB_V5", b"MATLAB_V4", 1)
    assert changed!=data
    path=tmp_path/"audit.json"
    path.write_bytes(changed)
    monkeypatch.setattr(d02,"OLD_AUDIT",path)
    with pytest.raises(d02.FieldAuditError,match="IDENTITY_FAILURE"):
        d02.verify_old_original()
