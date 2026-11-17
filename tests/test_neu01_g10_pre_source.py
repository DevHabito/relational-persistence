"""Synthetic only: frozen G10 manifest, provenance, IEEE and negative controls.

No test here downloads an original .eeg/.vhdr or derivative .set body.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import md5, sha256
import json

import numpy as np
import pytest

from experiments import neu01_g10_pre_source as g
from experiments import neu01_g08_fixed_pair as grid


def test_all_eight_preselected_pairs_are_unique_and_in_frozen_order():
    observed = [(p.subject, p.session, p.task) for p in g.PAIRS]
    expected = [
        ("sub-05", 2, "eyesclosed"), ("sub-05", 2, "eyesopen"),
        ("sub-05", 3, "eyesclosed"), ("sub-05", 3, "eyesopen"),
        ("sub-37", 2, "eyesclosed"), ("sub-37", 2, "eyesopen"),
        ("sub-37", 3, "eyesclosed"), ("sub-37", 3, "eyesopen"),
    ]
    assert observed == expected
    assert len({p.root_md5 for p in g.PAIRS}) == 8
    assert len({p.header_md5 for p in g.PAIRS}) == 8
    assert len({p.derivative_md5 for p in g.PAIRS}) == 8
    assert g.ROOT_BYTES == 36600000
    assert g.DERIVATIVE_BYTES == 73824136


def test_source_paths_are_pinned_to_correct_session_and_condition():
    pair = g.PAIRS[0]
    assert g.source_paths(pair) == {
        "root": "sub-05/ses-session2/eeg/sub-05_ses-session2_task-eyesclosed_eeg.eeg",
        "header": "sub-05/ses-session2/eeg/sub-05_ses-session2_task-eyesclosed_eeg.vhdr",
        "channels": "sub-05/ses-session2/eeg/sub-05_ses-session2_task-eyesclosed_channels.tsv",
        "sidecar": "sub-05/ses-session2/eeg/sub-05_ses-session2_task-eyesclosed_eeg.json",
        "derivative": "derivatives/preprocessed data/preprocessed_data/sub05_02_EC.set",
    }
    assert g.publisher_url(pair, "derivative").endswith(
        "derivatives/preprocessed%20data/preprocessed_data/sub05_02_EC.set"
    )
    assert g.publisher_url(g.PAIRS[7], "derivative").endswith("sub37_03_EO.set")
    for changed in (
        replace(pair, session=1),
        replace(pair, subject="sub-02"),
        replace(pair, task="eyesopen"),
        replace(pair, root_md5="f" * 32),
    ):
        with pytest.raises(g.GateFailure, match="UNREGISTERED"):
            g.source_paths(changed)
    with pytest.raises(g.GateFailure, match="FILE_TYPE"):
        g.publisher_url(pair, "auxiliary")


def test_original_G08_and_G09_archived_first_outcomes_unmodified():
    g.check_previous_archives()
    body = g.G09_FIRST.read_bytes()
    assert len(body) == 15338
    assert sha256(body).hexdigest() == g.G09_FIRST_SHA256
    original = json.loads(body)
    assert original["number_exact_bitwise_identical_pairs"] == 5


def test_digest_and_byte_size_fail_closed_with_synthetic_payload():
    body = b"G10 synthetic bytes without any EEG amplitudes"
    expected = md5(body).hexdigest()
    ok = g.authenticate_body(body, expected_size=len(body), expected_md5=expected)
    assert ok["actual_sha256"] == sha256(body).hexdigest()
    with pytest.raises(g.GateFailure, match="SOURCE_SIZE"):
        g.authenticate_body(body, expected_size=len(body) - 1, expected_md5=expected)
    with pytest.raises(g.GateFailure, match="PUBLISHER_MD5"):
        g.authenticate_body(body, expected_size=len(body), expected_md5="0" * 32)
    with pytest.raises(g.GateFailure, match="INVALID_PUBLISHER_MD5"):
        g.authenticate_body(body, expected_size=len(body), expected_md5="X" * 32)
    with pytest.raises(g.GateFailure, match="INVALID_SOURCE_BODY"):
        g.authenticate_body("not bytes", expected_size=len(body), expected_md5=expected)


def synthetic_header(pair):
    paths = g.source_paths(pair)
    basename = paths["root"].rsplit("/", 1)[-1]
    lines = [
        "Brain Vision Data Exchange Header File Version 1.0",
        "[Common Infos]",
        "DataFile=" + basename,
        "MarkerFile=" + basename.replace(".eeg", ".vmrk"),
        "DataFormat=BINARY",
        "DataOrientation=MULTIPLEXED",
        "NumberOfChannels=61",
        "SamplingInterval=2000",
        "[Binary Infos]",
        "BinaryFormat=IEEE_FLOAT_32",
        "[Channel Infos]",
    ]
    lines += [f"Ch{i}=C{i},,1," for i in range(1, 62)]
    return ("\n".join(lines) + "\n").encode("latin-1")


def test_header_validates_session_sensitive_filename_grid_and_channel_labels():
    p = g.PAIRS[2]
    body = synthetic_header(p)
    labels = g.header_labels(body, p)
    assert labels[0] == "c1" and labels[-1] == "c61"
    for before, after, error in (
        (b"SamplingInterval=2000", b"SamplingInterval=4000", "GRID"),
        (b"NumberOfChannels=61", b"NumberOfChannels=60", "GRID"),
        (b"IEEE_FLOAT_32", b"INT_16", "REPRESENTATION"),
        (b"Ch61=C61,,1,", b"Ch61=C1,,1,", "DUPLICATE"),
        (b"Ch61=C61,,1,", b"Ch61=C61,,2,", "RESOLUTION"),
        (b"ses-session3", b"ses-session2", "GRID"),
    ):
        with pytest.raises(g.GateFailure, match=error):
            g.header_labels(body.replace(before, after), p)
    with pytest.raises(g.GateFailure, match="GRID"):
        g.header_labels(body, g.PAIRS[0])


def test_corrupted_BIDS_tsv_bytes_rejected_before_parsing():
    valid = b"name\ttype\tunits\tsampling_frequency\n"
    with pytest.raises(g.GateFailure, match="HASH_MISMATCH"):
        g.read_pinned_channels(valid)


def test_prior_unchanged_grid_rejects_permutation_shape_and_offset():
    labels = [f"c{i}" for i in range(61)]
    kw = dict(rate=500.0, n_channels=61, n_points=150000,
              n_trials=1, data_shape=(61, 150000), reference="common")
    times = np.arange(150000, dtype="<f8") * 2.0
    ok = grid.inspect_fixed_grid(labels, labels, labels, times, 0.0, 299.998, **kw)
    assert ok["metadata_gate_passed"] is True
    wrong = labels.copy()
    wrong[0], wrong[1] = wrong[1], wrong[0]
    assert not grid.inspect_fixed_grid(
        labels, labels, wrong, times, 0.0, 299.998, **kw
    )["metadata_gate_passed"]
    assert not grid.inspect_fixed_grid(
        labels, labels, labels, times + 2.0, 0.0, 299.998, **kw
    )["metadata_gate_passed"]
    assert not grid.inspect_fixed_grid(
        labels, labels, labels, times, 0.0, 299.998,
        **(kw | {"data_shape": (150000, 61)})
    )["metadata_gate_passed"]


def test_native_fixed_500_shift_bitwise_and_numeric_negative_controls():
    raw = np.arange(601 * 61, dtype="<f4").reshape(601, 61)
    d = raw.astype("<f8")
    same = g.compare_prevalidated_arrays(raw, d.copy())
    assert same["g10_status"] == "DIRECT_ARRAYS_IDENTICAL"
    assert same["ieee_64bit_pattern_equal_count"] == raw.size
    assert same["fixed_500_frame_shift_exact_numeric_equal_count"] == 0
    assert same["fixed_reversed_61_channel_exact_numeric_equal_count"] == 601
    mutated = d.copy()
    mutated[3, 2] += .5
    diff = g.compare_prevalidated_arrays(raw, mutated)
    assert diff["g10_status"] == "AUTHENTICATED_ARRAYS_DIFFER"
    assert diff["numeric_differ_count"] == 1
    sign_root = np.array([[0, -0, 1], [2, 3, 4], [5, 6, 7]], dtype="<f4")
    sign_root[0, 1] = np.float32(-0.0)
    sign_derived = sign_root.astype("<f8")
    sign_derived[0, 1] = 0.0
    zero = g.compare_prevalidated_arrays(sign_root, sign_derived)
    assert zero["g10_status"] == "NUMERIC_EQUAL_IEEE_BITS_DIFFER"
    assert zero["numeric_equal_but_ieee_bits_differ_count"] == 1
    with pytest.raises(g.GateFailure, match="FLOAT32"):
        g.compare_prevalidated_arrays(raw.astype("<f8"), d)
    with pytest.raises(g.GateFailure, match="FLOAT64"):
        g.compare_prevalidated_arrays(raw, d.astype("<f4"))
    with pytest.raises(g.GateFailure, match="SHAPE"):
        g.compare_prevalidated_arrays(raw, d[:500, :])
    bad = d.copy()
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="NONFINITE"):
        g.compare_prevalidated_arrays(raw, bad)


def test_all_eight_required_and_failures_never_count_as_equality():
    rows = [
        {"subject": p.subject, "session": p.session, "task": p.task,
         "status": "DIRECT_ARRAYS_IDENTICAL"}
        for p in g.PAIRS
    ]
    full = g.summarize_rows(rows)
    assert full["status"] == "G10_EIGHT_PAIR_CENSUS_COMPLETE"
    assert full["count_directly_identical"] == 8
    missing = [dict(row) for row in rows]
    missing[5]["status"] = "SOURCE_METADATA_NOT_ELIGIBLE"
    assert g.summarize_rows(missing)["status"] == "G10_EIGHT_PAIR_ELIGIBILITY_INCOMPLETE"
    with pytest.raises(g.GateFailure, match="EIGHT"):
        g.summarize_rows(rows[:-1])
    reorder = [dict(row) for row in rows]
    reorder[0], reorder[1] = reorder[1], reorder[0]
    with pytest.raises(g.GateFailure, match="ORDER"):
        g.summarize_rows(reorder)
    with pytest.raises(g.GateFailure, match="OUTCOME"):
        g.summarize_rows([rows[0] | {"status": "SUCCESS"}] + rows[1:])
