"""Independent synthetic tests for G04 source-reader and source-failure gates."""
from __future__ import annotations
from hashlib import sha256
from io import BytesIO
from itertools import product
import json
import struct
import pytest
from experiments import neu01_g04_independent_replay as g04


def independent_oracle(channels):
    zeros = equal = zero_zero = nonzero_equal = runs = 0
    per_ch = []
    for ch in channels:
        count = 0
        for index, value in enumerate(ch):
            zeros += int(value == 0.0)
            runs += int(value == 0.0 and (index == 0 or ch[index - 1] != 0.0))
            if index and value == ch[index - 1]:
                equal += 1
                count += 1
                if value == 0.0:
                    zero_zero += 1
                else:
                    nonzero_equal += 1
        per_ch.append(count)
    return (zeros, equal, zero_zero, nonzero_equal, runs, per_ch)


def pack(channels):
    frames = len(channels[0])
    return b"".join(struct.pack("<" + "f"*len(channels),
                                *(channels[ch][t] for ch in range(len(channels))))
                    for t in range(frames))


def check_sequence(channels):
    frames = len(channels[0])
    got = g04.recount(pack(channels), channels=len(channels), frames=frames)
    z, e, e00, enn, runs, per_ch = independent_oracle(channels)
    assert got["exact_zero_values"] == z
    assert got["within_channel_equal_adjacent"] == e
    assert got["zero_zero_equal_adjacent"] == e00
    assert got["nonzero_equal_adjacent"] == enn
    assert got["zero_runs"] == runs
    assert got["median_per_channel_equal_adjacent_count"] == sorted(per_ch)[len(per_ch)//2]
    assert got["max_per_channel_equal_adjacent_count"] == max(per_ch)
    assert got["nonzero_equal_adjacent"] >= got["prior_d01_lower_bound_nonzero"]


def test_exhaustive_three_symbol_single_channel():
    for n in range(2, 7):
        for seq in product((-1.0, 0.0, 1.0), repeat=n):
            check_sequence((seq,))


def test_exhaustive_two_channels_boundary_and_run_placements():
    for seq in product((-1.0, 0.0, 1.0), repeat=6):
        check_sequence((seq[:3], seq[3:]))


def test_signed_zero_and_nonzero_equalities():
    check_sequence(((0.0, -0.0, 0.0, 3.0), (2.0, 2.0, 1.0, 1.0), (1.0, 0.0, 0.0, 0.0)))
    check_sequence(((1.0, 1.0, 1.0, 1.0),))


def test_all_zero_and_all_nonzero_plateaus():
    check_sequence(((0.0,) * 12, (0.0,) * 12, (0.0,) * 12))
    check_sequence(((7.0,) * 8,))


def test_wrong_length_and_float_class_reject():
    good = pack(((1.0, 1.0, 1.0),))
    with pytest.raises(g04.SourceFailure, match="BYTE_COUNT"):
        g04.recount(good[:-1], channels=1, frames=3)
    with pytest.raises(g04.SourceFailure, match="NONFINITE"):
        g04.recount(pack(((0.0, float("nan"), 0.0),)), channels=1, frames=3)


def fixture_header(subject="sub-02", task="eyesclosed", *, bits="IEEE_FLOAT_32", interval="2000"):
    return (
        "[Common Infos]\n"
        f"DataFile={g04.source_name(subject,task,'eeg')}\n"
        f"MarkerFile={subject}_ses-session1_task-{task}_eeg.vmrk\n"
        "DataFormat=BINARY\nDataOrientation=MULTIPLEXED\n"
        "NumberOfChannels=61\n"
        f"SamplingInterval={interval}\n"
        "[Binary Infos]\n"
        f"BinaryFormat={bits}\n"
        "[Channel Infos]\n"
        + "".join(f"Ch{i}=E{i},,1,\n" for i in range(1,62))
    ).encode("latin1")


def test_header_missing_physical_units_are_preserved_not_imputed():
    r = g04.header_audit(fixture_header(), "sub-02", "eyesclosed")
    assert r["physical_unit_missing"] == 61
    assert r["calibrated_physical_amplitude"] is False


def test_bad_header_rejected_and_not_reattributed():
    with pytest.raises(g04.SourceFailure, match="REPRESENTATION"):
        g04.header_audit(fixture_header(bits="IEEE_FLOAT_64"), "sub-02", "eyesclosed")
    with pytest.raises(g04.SourceFailure, match="LAYOUT"):
        g04.header_audit(fixture_header(interval="1000"), "sub-02", "eyesclosed")


def test_oversized_and_bad_identity_source_fails_before_decode():
    class Fixture(BytesIO):
        pass
    def bad_opener(request, timeout=45):
        return Fixture(b"bogus-header")
    with pytest.raises(g04.SourceFailure, match="SOURCE_SIZE_MISMATCH"):
        g04.authenticated_bytes("sub-02", "eyesclosed", "vhdr", opener=bad_opener)


def test_original_g03_oracle_hash_pinned_without_calling_source():
    assert sha256(g04.G03_ARCHIVE.read_bytes()).hexdigest() == g04.G03_ARCHIVE_SHA
    assert g04.original_report()["study"] == "NEU-01-G03"
    assert len(g04.IDENTITIES) == 6


def test_deliberate_comparison_mutation_fails():
    old = g04.original_report()
    # Build independent synthetic summary containing precisely the archived
    # old counts; only this fixture is retrospective, never a fresh EEG read.
    computed = {}
    for subject in g04.SUBJECTS:
        computed[subject] = {}
        for task in g04.TASKS:
            rec = old["recordings"][subject][task]
            computed[subject][task] = {
                "census": dict(rec["native_census"]),
                "eeg_sha256": rec["source_identity"]["eeg"]["sha256"],
                "unit_metadata": {"physical_unit_missing": 61},
            }
    g04.compare_original(computed, old)
    computed["sub-03"]["eyesclosed"]["census"]["within_channel_equal_adjacent"] += 1
    with pytest.raises(g04.ReplayMismatch, match="sub-03/eyesclosed"):
        g04.compare_original(computed, old)


def test_no_numpy_original_reader_dependency_in_source():
    source = g04.Path(g04.__file__).read_text(encoding="utf-8")
    assert "import numpy" not in source
    assert "from experiments import neu01_g03" not in source
    assert "import neu01_g02" not in source
