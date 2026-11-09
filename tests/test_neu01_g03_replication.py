"""Synthetic and adversarial NEU-01-G03 tests, never a human EEG analysis."""
from __future__ import annotations

from io import BytesIO
import re

import numpy as np
import pytest

from experiments import neu01_g03_replication as g03


def reference_counter(data):
    """Deliberately independent simple nested-loop equality oracle."""
    frames, channels = data.shape
    zeros = 0
    per_ch = [0] * channels
    for ch in range(channels):
        for t in range(frames):
            x = float(data[t, ch])
            zeros += int(x == 0.0)
            if t and x == float(data[t - 1, ch]):
                per_ch[ch] += 1
    per_ch.sort()
    return zeros, sum(per_ch), sum(v != 0 for v in per_ch), per_ch[channels // 2], per_ch[-1]


def test_frozen_cohort_and_protocol_are_not_extended():
    assert g03.PARTICIPANTS == ("sub-02", "sub-03", "sub-04")
    assert g03.TASKS == ("eyesclosed", "eyesopen")
    assert g03.PROTOCOL_SHA == "ed0d77e5a3812ec1931ec6b7e3dbdcc0e87777b3"
    assert g03.DATASET_COMMIT == "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
    assert g03.SAMPLES == 9150000 and g03.PAIRS == 9149939
    assert len(g03.KEYS) == 6
    assert all(re.fullmatch(r"[0-9a-f]{32}", md5)
               for values in g03.KEYS.values() for md5 in values)


def test_registered_original_annex_hashes_are_immutable():
    assert g03.KEYS[("sub-02", "eyesclosed")] == (
        "afc315cd4fbd76f2788a67fe31be9d8d",
        "10a0033fdb6dfd1f72a6e37b8164a269",
    )
    assert g03.KEYS[("sub-03", "eyesopen")] == (
        "099a4fdb6e0e5fe105f04f4c250bc0a4",
        "ae548d8a0b43dfea2e28d1111d50450c",
    )
    assert g03.KEYS[("sub-04", "eyesopen")] == (
        "28079903eac38f9f8670a80f0dc766f1",
        "7d979ba2cfa1a97b092d2782f2138c4b",
    )


def test_count_matches_independent_hand_oracle():
    x = np.array([[0, 1, 3], [0, 2, 3], [0, 2, 4], [4, 2, 4]],
                 dtype="<f4")
    report = g03.describe_native(x, frames=4, channels=3)
    assert report["exact_zero_values"] == 3
    assert report["within_channel_equal_adjacent"] == 6
    assert report["within_channel_possible_adjacencies"] == 9
    assert (report["channels_with_any_equal_adjacent"],
            report["median_per_channel_equal_adjacent_count"],
            report["max_per_channel_equal_adjacent_count"]) == (3, 2, 2)
    assert reference_counter(x) == (3, 6, 3, 2, 2)


def test_no_false_pairs_when_interleaved_channels_change():
    x = np.array([[0, 1], [1, 0], [0, 1]], dtype="<f4")
    r = g03.describe_native(x, frames=3, channels=2)
    assert r["within_channel_equal_adjacent"] == 0
    assert reference_counter(x)[1] == 0
    assert np.count_nonzero(x.reshape(-1)[1:] == x.reshape(-1)[:-1]) > 0


def test_temporal_reversal_preserves_exact_counts():
    rng = np.random.default_rng(232)
    x = rng.integers(-2, 3, size=(800, 61)).astype("<f4")
    a = g03.describe_native(x, frames=800)
    b = g03.describe_native(x[::-1, :], frames=800)
    assert a == b
    assert reference_counter(x)[:2] == (
        a["exact_zero_values"], a["within_channel_equal_adjacent"])


def test_channel_permutation_preserves_aggregate_counts():
    x = np.random.default_rng(311).integers(-1, 2, size=(200, 61)).astype("<f4")
    order = np.random.default_rng(90).permutation(61)
    assert g03.describe_native(x, frames=200) == g03.describe_native(
        x[:, order], frames=200)


def test_zero_and_negative_zero_are_both_counted():
    x = np.array([[-0.0, 0.0], [0.0, -0.0], [1.0, 1.0]], dtype="<f4")
    r = g03.describe_native(x, frames=3, channels=2)
    assert r["exact_zero_values"] == 4
    assert r["within_channel_equal_adjacent"] == 2


def test_alternating_values_have_no_adjacent_equalities():
    x = np.tile(np.array([0, 1], dtype="<f4")[:, None], (5, 3))
    r = g03.describe_native(x, frames=10, channels=3)
    assert r["within_channel_equal_adjacent"] == 0


def test_all_constant_is_counted_not_interpreted_as_neural_rigidity():
    x = np.zeros((20, 61), dtype="<f4")
    r = g03.describe_native(x, frames=20)
    assert r["exact_zero_values"] == 20 * 61
    assert r["within_channel_equal_adjacent"] == 19 * 61
    assert r["channels_with_any_equal_adjacent"] == 61


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_any_nonfinite_original_value_is_a_stop_not_excluded(bad):
    x = np.zeros((8, 3), dtype="<f4")
    x[2, 1] = bad
    with pytest.raises(g03.G03SourceError, match="ORIGINAL_NONFINITE_DATA_NOT_ELIGIBLE"):
        g03.describe_native(x, frames=8, channels=3)


def test_wrong_dtype_and_shape_are_not_accepted():
    x = np.ones((4, 3), dtype="<f4")
    with pytest.raises(g03.G03SourceError, match="INVALID_SOURCE_FLOAT32_DTYPE"):
        g03.describe_native(x.astype("float64"), frames=4, channels=3)
    with pytest.raises(g03.G03SourceError, match="INVALID_SOURCE_MATRIX_SHAPE"):
        g03.describe_native(x, frames=5, channels=3)


def test_unregistered_paths_and_tasks_are_rejected():
    with pytest.raises(g03.G03SourceError, match="UNREGISTERED_SOURCE_PATH"):
        g03.name("sub-01", "eyesclosed", "eeg.eeg")
    with pytest.raises(g03.G03SourceError, match="UNREGISTERED_SOURCE_PATH"):
        g03.name("sub-02", "music", "eeg.eeg")


def test_truncated_and_corrupted_header_fail_before_amplitude(tmp_path):
    def fake_open(request, timeout=45):
        return BytesIO(b"invalid-header-source")
    path = tmp_path / "a.vhdr"
    with pytest.raises(g03.G03SourceError, match="ORIGINAL_SOURCE_IDENTITY_FAILURE"):
        g03.retrieve("sub-02", "eyesclosed", "eeg.vhdr", path, opener=fake_open)


def test_oversized_header_fails_before_amplitude(tmp_path):
    def fake_open(request, timeout=45):
        return BytesIO(b"x" * 1123)
    with pytest.raises(g03.G03SourceError, match="SOURCE_BYTES_EXCEED_REGISTERED_LIMIT"):
        g03.retrieve("sub-02", "eyesclosed", "eeg.vhdr", tmp_path / "b.vhdr", opener=fake_open)


def make_header(subject="sub-02", task="eyesclosed", *, interval="2000", unit=""):
    return (
        "[Common Infos]\n"
        f"DataFile={g03.name(subject, task, 'eeg.eeg')}\n"
        f"MarkerFile={g03.name(subject, task, 'eeg.vmrk')}\n"
        "DataFormat=BINARY\nDataOrientation=MULTIPLEXED\n"
        f"NumberOfChannels=61\nSamplingInterval={interval}\n"
        "[Binary Infos]\nBinaryFormat=IEEE_FLOAT_32\n"
        "[Channel Infos]\n" +
        "".join(f"Ch{i}=E{i},,1,{unit}\n" for i in range(1, 62))
    ).encode("latin-1")


def test_header_missing_physical_units_are_visible_not_imputed():
    header = make_header()
    info = g03.verify_header("sub-02", "eyesclosed", header,
                             [f"E{i}" for i in range(1, 62)])
    assert info["header_channels_missing_declared_unit"] == 61
    assert info["header_calibration_complete"] is False
    assert info["header_unit_counts"] == {"MISSING": 61}


def test_wrong_channel_list_and_sample_rate_fail_closed():
    header = make_header()
    with pytest.raises(g03.G03SourceError, match="ORIGINAL_HEADER_TSV_CHANNEL_MISMATCH"):
        g03.verify_header("sub-02", "eyesclosed", header,
                          [f"E{i}" for i in range(2, 63)])
    with pytest.raises(g03.G03SourceError, match="SOURCE_SAMPLING_INTERVAL_MISMATCH"):
        g03.verify_header("sub-02", "eyesclosed",
                          make_header(interval="1000"),
                          [f"E{i}" for i in range(1, 62)])


def test_original_source_access_failure_does_not_create_positive_replication(monkeypatch):
    def offline(*args, **kwargs):
        raise g03.G03SourceError("PUBLIC_SOURCE_UNAVAILABLE")
    monkeypatch.setattr(g03, "retrieve", offline)
    r = g03.run_source()
    assert r["decision"] == "SOURCE_NOT_ELIGIBLE"
    assert r["error_code"] == "PUBLIC_SOURCE_UNAVAILABLE"
    assert "recordings" not in r
    assert r["lzc_computed"] is False
