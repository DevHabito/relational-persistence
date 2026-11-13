"""NEU-01-G08-D03: direct IEEE numeric and bitwise source-vs-derivative check.

Known G08-D02 already showed 0 projected residual and same native counts.
This is explicitly after-result; not a new sample or a source pipeline proof.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from scipy.io import loadmat

from experiments import neu01_g04_independent_replay as root
from experiments import neu01_g07_eeglab_pilot as derivative
from experiments import neu01_g08_fixed_pair as g08
from experiments import neu01_g08_d02_global_residual as d02

PROTOCOL_COMMIT = "795f3227641e46c972ebcfaf6aedd000c667173e"
PRIOR_D02_SHA = "a0fe888346e76de66672b41aa5634d45a5798a56633f7fd551d06de5747ae0a8"
DERIVATIVE_SHA = "2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359"
OUTPUT = Path("docs/results/NEU-01-G08-D03-first-run/audit.json")
N_FRAMES, N_CHANNELS = 150000, 61
SHIFT = 500


class SourceNotEligible(ValueError):
    """Authenticated source or frozen first report does not meet requirements."""


def verify_previous_evidence() -> None:
    # D02 verifies all earlier original G04, G05, G07, and G08 sources.
    d02.verified_archives()
    g08.hash_archive(
        Path("docs/results/NEU-01-G08-D02-first-run/audit.json"),
        2332, PRIOR_D02_SHA,
    )
    original = json.loads(
        Path("docs/results/NEU-01-G08-D02-first-run/audit.json").read_bytes()
    )
    if (original.get("status") != "G08_D02_RESIDUAL_CENSUS_COMPLETE"
            or original.get("globally_projected_model", {}).get(
                "fixed_gain_one_relative_frobenius_residual"
            ) != 0):
        raise SourceNotEligible("IMMUTABLE_D02_ORIGINAL_STATUS_CHANGED")


def inspect_direct_arrays(root64: np.ndarray, derivative64: np.ndarray,
                          *, shift: int = SHIFT) -> dict:
    """Exact identity, two fixed wrong-index controls, canonical F64 hashes."""
    if (root64.shape != derivative64.shape or root64.ndim != 2
            or root64.shape[0] < 3 or root64.shape[1] < 2 or shift < 1):
        raise SourceNotEligible("DIRECT_ARRAY_SHAPE_OR_CONTROL_INVALID")
    if (root64.dtype.kind != "f" or root64.dtype.itemsize != 8
            or derivative64.dtype.kind != "f" or derivative64.dtype.itemsize != 8):
        raise SourceNotEligible("DIRECT_ARRAYS_MUST_BE_DOUBLE")
    if not (bool(np.all(np.isfinite(root64))) and
            bool(np.all(np.isfinite(derivative64)))):
        raise SourceNotEligible("DIRECT_ARRAYS_CONTAIN_NONFINITE_VALUES")

    # Canonicalize sample order and endianness for independent content digests.
    source = np.ascontiguousarray(root64, dtype="<f8")
    final = np.ascontiguousarray(derivative64, dtype="<f8")
    num_mask = source == final
    bit_mask = source.view("<u8") == final.view("<u8")
    n_total = int(source.size)
    n_numeric_equal = int(np.count_nonzero(num_mask))
    n_bitwise_equal = int(np.count_nonzero(bit_mask))
    n_sign_zero_diff = int(np.count_nonzero(num_mask & ~bit_mask))
    original_sha = sha256(source.tobytes(order="C")).hexdigest()
    derivative_sha = sha256(final.tobytes(order="C")).hexdigest()
    n_shifted = int(np.count_nonzero(
        source == np.roll(final, shift, axis=0)
    ))
    n_reversed = int(np.count_nonzero(source == final[:, ::-1]))
    max_difference = float(np.max(np.abs(source - final)))

    if n_numeric_equal == n_total and n_bitwise_equal == n_total:
        status = "EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL"
    elif n_numeric_equal == n_total:
        status = "NUMERIC_EQUAL_IEEE_BITS_DIFFER"
    else:
        status = "AUTHENTICATED_NATIVE_ARRAYS_DIFFER"
    if n_numeric_equal < n_bitwise_equal or n_sign_zero_diff != n_numeric_equal - n_bitwise_equal:
        raise SourceNotEligible("INVALID_IEEE_EQUALITY_ACCOUNTING")
    if (original_sha == derivative_sha) != (n_bitwise_equal == n_total):
        raise SourceNotEligible("CANONICAL_FLOAT64_DIGEST_CONSISTENCY_FAILURE")
    return {
        "direct_identity_status": status,
        "source_float32_exactly_widened_to_float64": True,
        "source_original_double_canonical_sha256": original_sha,
        "derivative_double_canonical_sha256": derivative_sha,
        "canonical_64bit_content_digests_identical": original_sha == derivative_sha,
        "all_aligned_numeric_values_count": n_total,
        "numeric_equal_count": n_numeric_equal,
        "numeric_differ_count": n_total - n_numeric_equal,
        "ieee_64bit_pattern_equal_count": n_bitwise_equal,
        "ieee_64bit_pattern_differ_count": n_total - n_bitwise_equal,
        "numeric_equal_but_ieee_bits_differ_count": n_sign_zero_diff,
        "maximum_absolute_native_numeric_difference": max_difference,
        "fixed_500_frame_shift_exact_numeric_equal_count": n_shifted,
        "fixed_reversed_61_channel_exact_numeric_equal_count": n_reversed,
        "no_gain_projection_lag_or_channel_relabeling_applied": True,
        "source_amplitudes_published": False,
        "processing_causality_established": False,
    }


def run_original() -> dict:
    verify_previous_evidence()
    with TemporaryDirectory(prefix="neu01-g08-d03-private-no-samples-") as directory:
        derivative_path = Path(directory) / "original-derived.set"
        published_identity = derivative.acquire_verified(derivative_path)
        if published_identity["observed_sha256"] != DERIVATIVE_SHA:
            raise SourceNotEligible("DERIVATIVE_SOURCE_IDENTITY_CHANGED")
        source_bytes = root.authenticated_bytes("sub-02", "eyesclosed", "eeg")
        if len(source_bytes) != root.RECORD_BYTES:
            raise SourceNotEligible("ORIGINAL_BRAINVISION_BYTE_COUNT_CHANGED")
        source_native = np.frombuffer(source_bytes, dtype="<f4").reshape(
            N_FRAMES, N_CHANNELS
        )
        # All finite native float32 values widen to float64 exactly.
        source_widened = source_native.astype("<f8")
        mat = loadmat(
            derivative_path, variable_names=["data"], squeeze_me=False,
            verify_compressed_data_integrity=True,
        )
        array = mat.get("data")
        if (not isinstance(array, np.ndarray)
                or array.shape != (N_CHANNELS, N_FRAMES)
                or array.dtype.kind != "f" or array.dtype.itemsize != 8):
            raise SourceNotEligible("EEGLAB_DERIVATIVE_NUMERIC_DATA_LAYOUT_CHANGED")
        derivative_reordered = np.asarray(array.T, dtype="<f8")
        inspected = inspect_direct_arrays(source_widened, derivative_reordered)
        del source_bytes,source_native,source_widened,derivative_reordered,mat,array
    return {
        "study": "NEU-01-G08-D03",
        "status": inspected["direct_identity_status"],
        "protocol_commit": PROTOCOL_COMMIT,
        "explicitly_posthoc_after_G08_P01_and_D02": True,
        "original_first_G08_D02_sha256": PRIOR_D02_SHA,
        "published_original_root_eeg_sha256": root.IDENTITIES[("sub-02","eyesclosed")][1],
        "published_original_derivative_sha256": DERIVATIVE_SHA,
        "source_subject_task": "sub-02/session1/eyesclosed",
        "original_pair_authenticated_before_comparison": True,
        "direct_IEEE_comparison": inspected,
        "other_five_derivative_arrays_compared": False,
        "exact_historical_preprocessing_operations_proven": False,
        "brain_or_thermodynamic_outcome_measured": False,
        "raw_signal_uploaded": False,
    }


def main():
    try:
        record=run_original()
    except (SourceNotEligible,root.SourceFailure,derivative.SourceUnavailable,
            OSError,ValueError,TypeError,KeyError,MemoryError) as exc:
        record={
            "study":"NEU-01-G08-D03","status":"SOURCE_NOT_ELIGIBLE",
            "protocol_commit":PROTOCOL_COMMIT,
            "error_type":type(exc).__name__,
            "error_code":str(exc)[:150],
            "raw_signal_uploaded":False,
        }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2,sort_keys=True),flush=True)
    if record["status"]=="SOURCE_NOT_ELIGIBLE":
        raise SystemExit(2)


if __name__=="__main__":
    main()
