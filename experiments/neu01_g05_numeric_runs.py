"""NEU-01-G05-P01: source-level numerical run census; not a neural inference.

All six source files were already examined in G02–G04. This script only
diagnoses native IEEE float32 representation. No physical units are inferred.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from experiments import neu01_g04_independent_replay as source

PROTOCOL_COMMIT = "1702cbb602d35efe8a4bc3cdc484f2ad2e5f9f7a"
ORIGINAL_G04_SHA = "7b32e1e0fc31d82ec2d1a3c509b0304bbbb4219db2145788d05d90d87140dc00"
ORIGINAL_G04_BYTES = 6022
ORIGINAL_G04 = Path("docs/results/NEU-01-G04-P01-first-run/audit.json")
OUTPUT = Path("docs/results/NEU-01-G05-P01-first-run/audit.json")
SUBJECTS = ("sub-02", "sub-03", "sub-04")
TASKS = ("eyesclosed", "eyesopen")
CHANNELS = 61
FRAMES = 150000


class SourceNotEligible(Exception):
    """Authentication, finite-signal or instrument precondition failed."""


class RecountMismatch(Exception):
    """Recomputed native counts do not agree with frozen G04 evidence."""


def original_g04() -> dict:
    body = ORIGINAL_G04.read_bytes()
    if len(body) != ORIGINAL_G04_BYTES or sha256(body).hexdigest() != ORIGINAL_G04_SHA:
        raise SourceNotEligible("ORIGINAL_G04_ARCHIVE_DIGEST_FAILURE")
    old = json.loads(body)
    if (old.get("study") != "NEU-01-G04-P01"
            or old.get("status") != "INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH"
            or old.get("participants") != list(SUBJECTS)):
        raise SourceNotEligible("ORIGINAL_G04_ARCHIVE_SCOPE_FAILURE")
    return old


def _histogram(counter: Counter[int]) -> dict[str, int]:
    """Serialize every run length >=2 without pruning or selecting bins."""
    return {str(k): int(counter[k]) for k in sorted(counter)}


def count_native(data: bytes, *, frames: int = FRAMES, channels: int = CHANNELS) -> dict:
    """Count maximal within-channel float32 runs and integer-valued natives."""
    if (not isinstance(data, bytes) or frames < 2 or channels < 1
            or len(data) != frames * channels * 4):
        raise SourceNotEligible("SOURCE_MATRIX_SIZE_OR_TYPE_INVALID")
    matrix = np.frombuffer(data, dtype="<f4").reshape(frames, channels)
    if not bool(np.all(np.isfinite(matrix))):
        raise SourceNotEligible("SOURCE_NONFINITE_STOP")
    zero_hist: Counter[int] = Counter()
    nonzero_hist: Counter[int] = Counter()
    z = e00 = enn = r0 = integer_samples = integer_pairs = 0
    max_zero_run = max_nonzero_run = 0
    channel_pair_counts: list[int] = []
    for column in range(channels):
        x = matrix[:, column]
        is_nonzero = (x != np.float32(0))
        nonzero_samples = int(np.count_nonzero(is_nonzero))
        z += frames - nonzero_samples
        # Test numeric integrality *only* in the original, uncalibrated units.
        integer_samples += int(np.count_nonzero(
            is_nonzero & (x == np.trunc(x))
        ))
        breakpoints = np.flatnonzero(x[1:] != x[:-1]) + 1
        boundaries = np.concatenate((
            np.array([0], dtype=np.int64),
            breakpoints,
            np.array([frames], dtype=np.int64)
        ))
        lengths = np.diff(boundaries)
        values = x[boundaries[:-1]]
        is_zero = values == np.float32(0)
        is_repeated = lengths >= 2
        repeat_zeros = is_zero & is_repeated
        repeat_nonzeros = (~is_zero) & is_repeated

        r0 += int(np.count_nonzero(is_zero))
        e00 += int(np.sum(lengths[repeat_zeros] - 1, dtype=np.int64))
        enn += int(np.sum(lengths[repeat_nonzeros] - 1, dtype=np.int64))
        is_integral_run = (values == np.trunc(values))
        integer_pairs += int(np.sum(
            lengths[repeat_nonzeros & is_integral_run] - 1,
            dtype=np.int64
        ))
        channel_pair_counts.append(int(np.sum(lengths - 1, dtype=np.int64)))
        for k, n in zip(*np.unique(lengths[repeat_zeros], return_counts=True)):
            zero_hist[int(k)] += int(n)
        for k, n in zip(*np.unique(lengths[repeat_nonzeros], return_counts=True)):
            nonzero_hist[int(k)] += int(n)
        if bool(np.any(repeat_zeros)):
            max_zero_run = max(max_zero_run, int(np.max(lengths[repeat_zeros])))
        if bool(np.any(repeat_nonzeros)):
            max_nonzero_run = max(max_nonzero_run, int(np.max(lengths[repeat_nonzeros])))

    n_values = frames * channels
    n_nonzero = n_values - z
    sorted_channel_pairs = sorted(channel_pair_counts)
    e = e00 + enn
    census = {
        "total_native_values": n_values,
        "finite": n_values, "nan": 0, "pos_inf": 0, "neg_inf": 0,
        "within_channel_possible_adjacencies": (frames - 1) * channels,
        "exact_zero_values": z,
        "zero_runs": r0,
        "zero_zero_equal_adjacent": e00,
        "nonzero_equal_adjacent": enn,
        "within_channel_equal_adjacent": e,
        "channels_with_any_equal_adjacent": sum(v > 0 for v in channel_pair_counts),
        "median_per_channel_equal_adjacent_count": sorted_channel_pairs[channels // 2],
        "max_per_channel_equal_adjacent_count": sorted_channel_pairs[-1],
        "prior_d01_lower_bound_nonzero": max(0, e - max(0, z - 1)),
    }
    diagnostic = {
        "native_nonzero_samples": n_nonzero,
        "native_integer_nonzero_samples": integer_samples,
        "native_integer_nonzero_equal_pairs": integer_pairs,
        "native_noninteger_nonzero_equal_pairs": enn - integer_pairs,
        "zero_repeat_run_histogram_all_lengths": _histogram(zero_hist),
        "nonzero_repeat_run_histogram_all_lengths": _histogram(nonzero_hist),
        "max_zero_repeat_run_length": max_zero_run,
        "max_nonzero_repeat_run_length": max_nonzero_run,
    }
    if not (
        0 <= integer_samples <= n_nonzero
        and 0 <= integer_pairs <= enn
        and z == r0 + e00
        and e == sum(channel_pair_counts)
        and e00 == sum((k - 1) * v for k, v in zero_hist.items())
        and enn == sum((k - 1) * v for k, v in nonzero_hist.items())
        and n_nonzero + z == n_values
    ):
        raise SourceNotEligible("RUN_ACCOUNTING_CONSERVATION_FAILED")
    return {"census": census, "diagnostic": diagnostic}


def compare_to_g04(recounted: dict, original: dict) -> None:
    old = original["recordings"]
    for subject in SUBJECTS:
        for task in TASKS:
            actual = recounted[subject][task]
            prior = old[subject][task]
            if actual["eeg_sha256"] != prior["eeg_sha256"]:
                raise RecountMismatch(f"{subject}/{task}/source_sha256")
            for field, expected in prior["census"].items():
                if actual["census"].get(field) != expected:
                    raise RecountMismatch(f"{subject}/{task}/{field}")
            if (actual["units_missing"] != prior["unit_metadata"]["physical_unit_missing"]
                    or actual["units_missing"] != CHANNELS):
                raise RecountMismatch(f"{subject}/{task}/unit_declarations")


def run_source() -> dict:
    original = original_g04()  # Fail on changed old oracle BEFORE new source access.
    recounted: dict[str, dict] = {}
    for subject in SUBJECTS:
        recounted[subject] = {}
        for task in TASKS:
            header = source.authenticated_bytes(subject, task, "vhdr")
            info = source.header_audit(header, subject, task)
            eeg = source.authenticated_bytes(subject, task, "eeg")
            actual_digest = sha256(eeg).hexdigest()
            counts = count_native(eeg)
            del eeg
            recounted[subject][task] = {
                "eeg_sha256": actual_digest,
                "units_missing": info["physical_unit_missing"],
                **counts,
            }
    compare_to_g04(recounted, original)
    return {
        "study": "NEU-01-G05-P01",
        "status": "G05_EXACT_SOURCE_CENSUS_COMPLETE",
        "protocol_commit": PROTOCOL_COMMIT,
        "original_g04_archive_sha256": ORIGINAL_G04_SHA,
        "source_derived_records": recounted,
        "participants": list(SUBJECTS),
        "total_native_float32_values": CHANNELS * FRAMES * len(SUBJECTS) * len(TASKS),
        "same_previously_seen_processed_source": True,
        "physical_calibration_validated": False,
        "neural_causal_interpretation": False,
        "integer_occupancy_is_only_native_numeric": True,
    }


def main() -> None:
    try:
        result = run_source()
    except RecountMismatch as exc:
        result = {"study": "NEU-01-G05-P01", "status": "G05_RECOUNT_MISMATCH",
                  "error_field": str(exc), "protocol_commit": PROTOCOL_COMMIT}
    except (SourceNotEligible, source.SourceFailure, ValueError, OSError) as exc:
        result = {"study": "NEU-01-G05-P01", "status": "SOURCE_NOT_ELIGIBLE",
                  "error_type": type(exc).__name__, "error_code": str(exc)[:160],
                  "protocol_commit": PROTOCOL_COMMIT}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    if result["status"] != "G05_EXACT_SOURCE_CENSUS_COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
