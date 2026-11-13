"""NEU-01-G08-D02: post-result single-pair projected shared-gain residual.

G08-P01 already found r=1.0 in 61 channels. Here the residual and native
integer/equality counts are measured after freezing a SEPARATE protocol.
No uniquely identified processing operation or physiological inference.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from scipy.io import loadmat

from experiments import neu01_g04_independent_replay as raw_source
from experiments import neu01_g07_eeglab_pilot as derivative_source
from experiments import neu01_g08_fixed_pair as prior_grid

PROTOCOL_COMMIT = "a5f5dd11d8ed95d618ca718bb7b9eec9ea32664a"
ORIGINAL_G08_SHA = "18950086a3e0220dfc83c82210a5a84da9ad28d00e224fcdc7ac969aa842025b"
ORIGINAL_G05_SHA = "9dbf40942373aa5ec3fa9f7959b4442b9da96003c01090f76d5a4507639a21d4"
ORIGINAL_DERIVATIVE_SHA = "2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359"
G08_AUDIT = Path("docs/results/NEU-01-G08-P01-first-run/audit.json")
G05_AUDIT = Path("docs/results/NEU-01-G05-P01-first-run/audit.json")
OUTPUT = Path("docs/results/NEU-01-G08-D02-first-run/audit.json")
CHANNELS = 61
FRAMES = 150000
SHIFT = 500


class SourceNotEligible(Exception):
    """Original source bytes, shape or archived preflight do not qualify."""


class ResidualNotEligible(Exception):
    """Degenerate, nonfinite or unexpected numerical representation."""


class PriorCountMismatch(Exception):
    """Already examined root counts do not reproduce original G05."""


def verified_archives() -> dict:
    prior_grid.check_prior_source_evidence()
    prior_grid.hash_archive(G08_AUDIT, 2880, ORIGINAL_G08_SHA)
    prior_grid.hash_archive(G05_AUDIT, 8559, ORIGINAL_G05_SHA)
    g08 = json.loads(G08_AUDIT.read_bytes())
    if (g08.get("status") != "FIXED_GRID_DESCRIPTIVE_COMPARISON_COMPLETE"
            or g08.get("metadata_eligibility", {}).get("metadata_gate_passed") is not True
            or g08.get("metadata_eligibility", {}).get("matched_channel_labels_same_positions") != CHANNELS
            or g08.get("metadata_eligibility", {}).get("time_grid_max_abs_error_ms") != 0):
        raise SourceNotEligible("ORIGINAL_G08_GRID_ELIGIBILITY_CHANGED")
    g05 = json.loads(G05_AUDIT.read_bytes())
    if (g05.get("study") != "NEU-01-G05-P01"
            or g05.get("status") != "G05_EXACT_SOURCE_CENSUS_COMPLETE"):
        raise SourceNotEligible("ORIGINAL_G05_SOURCE_COUNT_SCOPE_CHANGED")
    return g05["source_derived_records"]["sub-02"]["eyesclosed"]


def original_native_census(x: np.ndarray) -> dict:
    """Exact native equality before any float64 projected arithmetic."""
    if x.shape != (FRAMES, CHANNELS) or x.dtype.kind != "f":
        raise ResidualNotEligible("NATIVE_INPUT_SHAPE_OR_FLOAT_KIND_INVALID")
    if not bool(np.all(np.isfinite(x))):
        raise ResidualNotEligible("NONFINITE_NATIVE_SOURCE")
    zeros = x == 0
    equal = x[1:] == x[:-1]
    zero_equal = equal & zeros[1:]
    nonzero_equal = equal & ~zeros[1:]
    nonzero = ~zeros
    is_integer = x == np.trunc(x)
    return {
        "total_native_values": int(x.size),
        "exact_zero_values": int(np.count_nonzero(zeros)),
        "native_nonzero_samples": int(np.count_nonzero(nonzero)),
        "native_integer_nonzero_samples": int(np.count_nonzero(nonzero & is_integer)),
        "within_channel_equal_adjacent": int(np.count_nonzero(equal)),
        "zero_zero_equal_adjacent": int(np.count_nonzero(zero_equal)),
        "nonzero_equal_adjacent": int(np.count_nonzero(nonzero_equal)),
        "native_integer_nonzero_equal_pairs": int(np.count_nonzero(nonzero_equal & is_integer[1:])),
        "native_noninteger_nonzero_equal_pairs": int(np.count_nonzero(nonzero_equal & ~is_integer[1:])),
    }


def compare_original_root(census: dict, known_g05: dict) -> None:
    old = known_g05["census"]
    earlier = known_g05["diagnostic"]
    fields = {
        "total_native_values": old["total_native_values"],
        "exact_zero_values": old["exact_zero_values"],
        "within_channel_equal_adjacent": old["within_channel_equal_adjacent"],
        "zero_zero_equal_adjacent": old["zero_zero_equal_adjacent"],
        "nonzero_equal_adjacent": old["nonzero_equal_adjacent"],
        "native_nonzero_samples": earlier["native_nonzero_samples"],
        "native_integer_nonzero_samples": earlier["native_integer_nonzero_samples"],
        "native_integer_nonzero_equal_pairs": earlier["native_integer_nonzero_equal_pairs"],
        "native_noninteger_nonzero_equal_pairs": earlier["native_noninteger_nonzero_equal_pairs"],
    }
    for field, expected in fields.items():
        if census.get(field) != expected:
            raise PriorCountMismatch("ORIGINAL_ROOT_G05_COUNT_CHANGED:" + field)


def projected_global_residual(a: np.ndarray, b: np.ndarray,
                              *, shift: int = SHIFT) -> dict:
    """Single full-matrix gain after a fixed per-frame channel-mean removal."""
    if not (a.shape == b.shape and a.ndim == 2 and a.shape[0] >= 3
            and a.shape[1] >= 2 and shift >= 1):
        raise ResidualNotEligible("SHAPE_OR_FIXED_CONTROL_INVALID")
    if not bool(np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ResidualNotEligible("NONFINITE_NUMERIC_PAIR")
    a = a.astype(np.float64, copy=False)
    b = b.astype(np.float64, copy=False)
    A = a - np.mean(a, axis=1, keepdims=True)
    B = b - np.mean(b, axis=1, keepdims=True)
    denominator_A = float(np.sum(A*A, dtype=np.float64))
    denominator_B = float(np.sum(B*B, dtype=np.float64))
    if not (math.isfinite(denominator_A) and math.isfinite(denominator_B)
            and denominator_A > 0 and denominator_B > 0):
        raise ResidualNotEligible("DEGENERATE_GLOBAL_PROJECTION")
    alpha = float(np.sum(A*B, dtype=np.float64) / denominator_A)
    if not math.isfinite(alpha):
        raise ResidualNotEligible("NONFINITE_FITTED_SINGLE_GAIN")
    difference_unit = B-A
    residual = B-alpha*A
    control_shift = np.roll(B, shift, axis=0) - alpha*A
    control_reversal = B[:, ::-1] - alpha*A
    ratio = lambda t: float(np.sqrt(np.sum(t*t,dtype=np.float64)/denominator_B))
    rel = ratio(residual)
    return {
        "shared_least_squares_gain": alpha,
        "fixed_gain_one_relative_frobenius_residual": ratio(difference_unit),
        "fixed_gain_one_max_abs_projected_error_native": float(np.max(np.abs(difference_unit))),
        "fitted_gain_relative_frobenius_residual": rel,
        "fitted_gain_max_abs_projected_error_native": float(np.max(np.abs(residual))),
        "fitted_gain_explained_projected_energy": 1.0-rel*rel,
        "fixed_500_frame_shift_same_gain_residual": ratio(control_shift),
        "fixed_channel_reversal_same_gain_residual": ratio(control_reversal),
        "fit_is_single_global_scalar": True,
        "projected_source_amplitudes_published": False,
        "physical_units_calibration_verified": False,
        "source_processing_causality_established": False,
    }


def run_original() -> dict:
    known = verified_archives()
    with TemporaryDirectory(prefix="neu01-g08-d02-original-private-") as directory:
        path = Path(directory) / "original-derived.set"
        original_derivative_id = derivative_source.acquire_verified(path)
        if original_derivative_id["observed_sha256"] != ORIGINAL_DERIVATIVE_SHA:
            raise SourceNotEligible("DERIVATIVE_SHA256_NOT_IDENTICAL_TO_G07")
        eeg = raw_source.authenticated_bytes("sub-02","eyesclosed","eeg")
        raw_array = np.frombuffer(eeg, dtype="<f4").reshape(FRAMES,CHANNELS)
        matlab = loadmat(path, variable_names=["data"],
                         squeeze_me=False, verify_compressed_data_integrity=True)
        double_array = matlab.get("data")
        if (not isinstance(double_array,np.ndarray)
                or double_array.shape != (CHANNELS,FRAMES)
                or double_array.dtype.kind != "f"):
            raise SourceNotEligible("DERIVATIVE_FLOAT64_MATRIX_SHAPE_OR_CLASS_CHANGED")
        if double_array.dtype.itemsize != 8:
            raise SourceNotEligible("DERIVATIVE_DATA_NOT_FLOAT64")
        derivative_array = np.asarray(double_array.T, dtype=np.float64)
        raw_census = original_native_census(raw_array)
        compare_original_root(raw_census,known)
        derivative_census = original_native_census(derivative_array)
        residual = projected_global_residual(raw_array,derivative_array)
        del raw_array,derivative_array,double_array,matlab,eeg
    return {
        "study":"NEU-01-G08-D02",
        "status":"G08_D02_RESIDUAL_CENSUS_COMPLETE",
        "protocol_commit":PROTOCOL_COMMIT,
        "posthoc_after_original_G08_P01_pearson_one":True,
        "original_G08_archive_sha256":ORIGINAL_G08_SHA,
        "original_G05_archive_sha256":ORIGINAL_G05_SHA,
        "one_original_subject_state":"sub-02/session1/eyesclosed",
        "source_original_root_sha256":raw_source.IDENTITIES[("sub-02","eyesclosed")][1],
        "source_derivative_sha256":ORIGINAL_DERIVATIVE_SHA,
        "root_census_reconciles_with_G05":True,
        "root_native_census":raw_census,
        "derivative_native_census":derivative_census,
        "globally_projected_model":residual,
        "source_physical_gain_validated":False,
        "original_binary_uploaded":False,
        "neural_population_or_thermodynamics_claim":False,
    }


def main() -> None:
    try:
        result=run_original()
    except PriorCountMismatch as exc:
        result={"study":"NEU-01-G08-D02","status":"G08_D02_PREVIOUS_SOURCE_COUNT_MISMATCH",
                "protocol_commit":PROTOCOL_COMMIT,"error_code":str(exc)[:140]}
    except (SourceNotEligible,raw_source.SourceFailure,derivative_source.SourceUnavailable,
            OSError,KeyError,TypeError,ValueError) as exc:
        result={"study":"NEU-01-G08-D02","status":"SOURCE_NOT_ELIGIBLE",
                "protocol_commit":PROTOCOL_COMMIT,"error_type":type(exc).__name__,
                "error_code":str(exc)[:140]}
    except ResidualNotEligible as exc:
        result={"study":"NEU-01-G08-D02","status":"RESIDUAL_NOT_ELIGIBLE",
                "protocol_commit":PROTOCOL_COMMIT,"error_code":str(exc)[:140]}
    result["original_binary_uploaded"]=False
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    if result["status"]!="G08_D02_RESIDUAL_CENSUS_COMPLETE":
        raise SystemExit(2)


if __name__=="__main__":
    main()
