"""NEU-01-G08-P01: fixed one-pair source grid audit and conditional correlation.

Retrospective technical diagnostic. NO source-to-derivative causal interpretation,
statistical population replication, neural rigidity, or calibrated voltage claim.
"""
from __future__ import annotations

import csv
from hashlib import sha1, sha256
from io import StringIO
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
from scipy.io import loadmat

from experiments import neu01_g04_independent_replay as root
from experiments import neu01_g07_eeglab_pilot as derived

PROTOCOL_COMMIT = "efdeb6651f3614735d50629cdaabcf7e29c22de2"
SUBJECT, TASK = "sub-02", "eyesclosed"
N_CHANNELS, N_FRAMES, RATE = 61, 150000, 500
ROOT_HEADER_BYTES = 1122
ROOT_SIDECAR_PATH = (
    "sub-02/ses-session1/eeg/sub-02_ses-session1_task-eyesclosed_channels.tsv"
)
ROOT_SIDECAR_SHA1 = "105960eb0ac14bae43bea73aa479a5c6d995c7a3"
ROOT_SIDECAR_BYTES = 983
ORIGINAL_G04_SHA = "7b32e1e0fc31d82ec2d1a3c509b0304bbbb4219db2145788d05d90d87140dc00"
ORIGINAL_G07_SHA = "60a328cd0cbd69f41da4ffaa8b71921b96f1c0d7fd81751b63b7f126cd1481c3"
ORIGINAL_D02_SHA = "5bf3dd61678b267c4997ed56328ae1c8183389d44e1c21910b315d59f8e7cef9"
ORIGINAL_DERIVATIVE_SHA = "2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359"
OUTPUT = Path("docs/results/NEU-01-G08-P01-first-run/audit.json")


class SourceNotEligible(ValueError):
    """Source object bytes/structure do not match registered identity."""


class SignalNotEligible(ValueError):
    """Fixed-grid waveform statistic cannot be evaluated without exceptions."""


def hash_archive(path: Path, expected_size: int, expected_sha: str) -> None:
    blob = path.read_bytes()
    if len(blob) != expected_size or sha256(blob).hexdigest() != expected_sha:
        raise SourceNotEligible("IMMUTABLE_PRIOR_SOURCE_ARCHIVE_CHANGED:" + path.name)


def check_prior_source_evidence() -> None:
    hash_archive(Path("docs/results/NEU-01-G04-P01-first-run/audit.json"),
                 6022, ORIGINAL_G04_SHA)
    hash_archive(Path("docs/results/NEU-01-G07-P01-first-run/audit.json"),
                 1133, ORIGINAL_G07_SHA)
    hash_archive(Path("docs/results/NEU-01-G07-D02-first-run/audit.json"),
                 4008, ORIGINAL_D02_SHA)


def _git_blob_sha1(body: bytes) -> str:
    return sha1(b"blob " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()


def acquire_pinned_channel_tsv(*, opener=urlopen) -> bytes:
    """Official original BIDS metadata only; source SHA pinned to immutable Git."""
    address = f"{root.ROOT}/{ROOT_SIDECAR_PATH}"
    request = Request(address, headers={"User-Agent": "RelationalPersistence-G08-BIDS/1"})
    try:
        with opener(request, timeout=45) as response:
            if response.geturl() != address:
                raise SourceNotEligible("WRONG_BIDS_CHANNEL_FILE_RESPONSE_URL")
            contents = response.read(ROOT_SIDECAR_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceNotEligible("PINNED_CHANNEL_TSV_SOURCE_UNAVAILABLE") from exc
    if len(contents) != ROOT_SIDECAR_BYTES or _git_blob_sha1(contents) != ROOT_SIDECAR_SHA1:
        raise SourceNotEligible("BIDS_CHANNEL_TSV_NOT_UPSTREAM_REVISION_BYTES")
    return contents


def label(value: str) -> str:
    if not isinstance(value, str):
        raise SourceNotEligible("UNREADABLE_ELECTRODE_LABEL")
    stripped = value.strip().casefold()
    if not stripped or len(stripped) > 64:
        raise SourceNotEligible("MISSING_OR_OVERSIZED_ELECTRODE_LABEL")
    return stripped


def ordered_hash(names: list[str]) -> str:
    return sha256("\n".join(names).encode("utf-8")).hexdigest()


def parse_brainvision_header(raw_header: bytes) -> list[str]:
    root.header_audit(raw_header, SUBJECT, TASK)
    decoded = raw_header.decode("latin-1")
    section = ""
    fields = {}
    for original_line in decoded.splitlines():
        s = original_line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].strip().casefold()
        elif section == "channel infos" and "=" in s:
            key, value = s.split("=", 1)
            fields[key.strip()] = value.split(",", 1)[0].strip()
    if set(fields) != {f"Ch{i}" for i in range(1, N_CHANNELS + 1)}:
        raise SourceNotEligible("ORIGINAL_HEADER_CHANNEL_ORDER_INVALID")
    names = [label(fields[f"Ch{i}"]) for i in range(1, N_CHANNELS + 1)]
    if len(set(names)) != N_CHANNELS:
        raise SourceNotEligible("DUPLICATE_ORIGINAL_ELECTRODE_LABELS")
    return names


def parse_bids_channel_labels(tsv: bytes) -> tuple[list[str], dict]:
    try:
        contents = tsv.decode("utf-8")
        reader = csv.DictReader(StringIO(contents), delimiter="\t")
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise SourceNotEligible("UNREADABLE_BIDS_CHANNELS_TSV") from exc
    if reader.fieldnames != ["name", "type", "units", "sampling_frequency"] or len(rows) != N_CHANNELS:
        raise SourceNotEligible("BIDS_CHANNEL_TSV_LAYOUT_INVALID")
    if any(r["type"] != "EEG" or r["units"] != "uV" or r["sampling_frequency"] != "500"
           for r in rows):
        raise SourceNotEligible("BIDS_CHANNEL_UNITS_OR_RATE_CHANGED")
    names = [label(r["name"]) for r in rows]
    if len(set(names)) != N_CHANNELS:
        raise SourceNotEligible("BIDS_CHANNEL_LABELS_NOT_UNIQUE")
    return names, {"units_declared_in_bids_channels_tsv": "uV",
                   "physical_scale_independently_calibrated": False}


def extract_derivative_labels(objects) -> list[str]:
    arr = np.asarray(objects, dtype=object)
    elements = arr.reshape(-1)
    if len(elements) != N_CHANNELS:
        raise SourceNotEligible("DERIVATIVE_CHANLOCS_CARDINALITY_INVALID")
    labels = [label(getattr(entry, "labels", None)) for entry in elements]
    if len(set(labels)) != N_CHANNELS:
        raise SourceNotEligible("DERIVATIVE_CHANLOCS_LABELS_NOT_UNIQUE")
    return labels


def clean_scalar(item) -> float | None:
    try:
        ar = np.asarray(item)
        if ar.size != 1:
            return None
        f = float(ar.reshape(-1)[0])
        return f if math.isfinite(f) else None
    except (TypeError, ValueError, OverflowError):
        return None


def inspect_fixed_grid(labels_root: list[str], labels_bids: list[str],
                       labels_derived: list[str], times,
                       xmin, xmax, *, rate: float | None,
                       n_channels: int | None, n_points: int | None,
                       n_trials: int | None, data_shape: tuple[int, ...],
                       reference: str | None) -> dict:
    """Validate exact ordered names and absolute bounds on RELATIVE coordinates."""
    ordered = labels_root == labels_bids == labels_derived
    known_sets = set(labels_root) == set(labels_bids) == set(labels_derived)
    same_positions = sum(x == y for x, y in zip(labels_root, labels_derived))
    t = np.asarray(times, dtype=np.float64).reshape(-1)
    t_finite = t.size == N_FRAMES and bool(np.all(np.isfinite(t)))
    if t_finite:
        expected = np.arange(N_FRAMES, dtype=np.float64) * 2.0
        err = float(np.max(np.abs(t - expected)))
        first, last = float(t[0]), float(t[-1])
        monotone = bool(np.all(np.diff(t) > 0))
    else:
        err, first, last, monotone = None, None, None, False
    x_min, x_max = clean_scalar(xmin), clean_scalar(xmax)
    time_valid = bool(
        t_finite and monotone and err is not None and err <= 0.001
        and x_min is not None and abs(x_min - 0.0) <= 0.000001
        and x_max is not None and abs(x_max - 299.998) <= 0.000001
    )
    shape_valid = (data_shape == (N_CHANNELS, N_FRAMES)
                   and n_channels == N_CHANNELS and n_points == N_FRAMES
                   and n_trials == 1 and rate == float(RATE))
    reasons = []
    if labels_root != labels_bids:
        reasons.append("ROOT_BRAINVISION_VERSUS_BIDS_LABEL_ORDER_DIFFER")
    if not ordered:
        reasons.append("DERIVATIVE_LABEL_ORDER_NOT_IDENTICAL")
    if not time_valid:
        reasons.append("RELATIVE_TIME_GRID_NOT_IDENTICAL_TO_ZERO_ANCHORED_2MS_GRID")
    if not shape_valid:
        reasons.append("SOURCE_DERIVATIVE_METADATA_SHAPE_OR_RATE_MISMATCH")
    return {
        "metadata_gate_passed": not reasons,
        "metadata_rejection_reasons": reasons,
        "original_ordered_labels_sha256": ordered_hash(labels_root),
        "bids_ordered_labels_sha256": ordered_hash(labels_bids),
        "derivative_ordered_labels_sha256": ordered_hash(labels_derived),
        "matched_channel_labels_same_positions": same_positions,
        "channel_sets_identical": known_sets,
        "channel_order_identical": ordered,
        "time_sample_count": int(t.size),
        "time_grid_max_abs_error_ms": err,
        "first_relative_time_ms": first,
        "last_relative_time_ms": last,
        "times_strictly_increasing": monotone,
        "xmin_seconds": x_min, "xmax_seconds": x_max,
        "relative_time_grid_zero_anchored_2ms_eligible": time_valid,
        "absolute_acquisition_onset_aligned": False,
        "metadata_data_shape": list(data_shape),
        "metadata_rate_hz": rate,
        "metadata_ref_label": reference if reference == "common" else None,
        "unverified_amplitude_physical_scale": True,
    }


def load_derived_metadata(path: Path, root_labels: list[str], bids_labels: list[str]) -> dict:
    from scipy.io import whosmat
    manifest = {key: (tuple(shape), kind) for key, shape, kind in whosmat(path)}
    if "data" not in manifest:
        raise SourceNotEligible("DERIVATIVE_DATA_VARIABLE_MISSING")
    shape, klass = manifest["data"]
    if klass != "double":
        raise SourceNotEligible("DERIVATIVE_DATA_TYPE_CHANGED")
    safe = loadmat(path, variable_names=[
        "chanlocs", "times", "xmin", "xmax", "nbchan", "pnts", "trials", "srate", "ref"
    ], squeeze_me=True, struct_as_record=False, verify_compressed_data_integrity=True)
    names = extract_derivative_labels(safe.get("chanlocs"))
    def int_scalar(name):
        v = clean_scalar(safe.get(name))
        return int(v) if v is not None and v.is_integer() and v >= 0 else None
    reference = safe.get("ref")
    return inspect_fixed_grid(
        root_labels, bids_labels, names, safe.get("times"),
        safe.get("xmin"), safe.get("xmax"),
        rate=clean_scalar(safe.get("srate")),
        n_channels=int_scalar("nbchan"),
        n_points=int_scalar("pnts"),
        n_trials=int_scalar("trials"),
        data_shape=shape,
        reference=reference if isinstance(reference, str) else None,
    )


def channel_corr(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Signed Pearson for each channel at fixed zero lag; no lag fitting."""
    if a.ndim != 2 or b.shape != a.shape or a.shape[0] < 3:
        raise SignalNotEligible("INVALID_PEARSON_MATRIX_SHAPE")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise SignalNotEligible("NONFINITE_SIGNAL_SAMPLE")
    aa = a - np.mean(a, axis=0, keepdims=True)
    bb = b - np.mean(b, axis=0, keepdims=True)
    numerator = np.sum(aa * bb, axis=0, dtype=np.float64)
    denominator = np.sqrt(np.sum(aa * aa, axis=0) * np.sum(bb * bb, axis=0))
    if np.any(~np.isfinite(denominator)) or np.any(denominator == 0):
        raise SignalNotEligible("ZERO_VARIANCE_OR_NONFINITE_CHANNEL")
    result = numerator / denominator
    if np.any(~np.isfinite(result)):
        raise SignalNotEligible("NONFINITE_CHANNEL_PEARSON")
    return result


def describe_correlation(c: np.ndarray) -> dict:
    return {
        "min_signed_pearson": float(np.min(c)),
        "median_signed_pearson": float(np.median(c)),
        "max_signed_pearson": float(np.max(c)),
        "count_abs_pearson_gt_0_9": int(np.sum(np.abs(c) > 0.9)),
        "channels": int(c.size),
    }


def compare_matched_arrays(raw_bytes: bytes, derived_path: Path,
                           *, shift_frames: int = RATE) -> dict:
    """Only called following every metadata eligibility gate."""
    if len(raw_bytes) != root.RECORD_BYTES or shift_frames < 1:
        raise SignalNotEligible("ROOT_DATA_SHAPE_OR_CONTROL_LAG_INVALID")
    root_data = np.frombuffer(raw_bytes, dtype="<f4").reshape(N_FRAMES, N_CHANNELS).astype(np.float64)
    mat = loadmat(derived_path, variable_names=["data"], squeeze_me=False,
                  verify_compressed_data_integrity=True)
    derived_data = mat.get("data")
    if not isinstance(derived_data, np.ndarray) or derived_data.shape != (N_CHANNELS, N_FRAMES):
        raise SignalNotEligible("DERIVATIVE_DATA_SHAPE_MISMATCH")
    derived_data = np.asarray(derived_data.T, dtype=np.float64)
    if not np.all(np.isfinite(root_data)) or not np.all(np.isfinite(derived_data)):
        raise SignalNotEligible("NONFINITE_SOURCE_PAIR")
    # Per-time channel mean projection is prespecified, not fitted to the pair.
    root_projected = root_data - np.mean(root_data, axis=1, keepdims=True)
    derived_projected = derived_data - np.mean(derived_data, axis=1, keepdims=True)
    c0 = channel_corr(root_projected, derived_projected)
    shifted = np.roll(derived_projected, shift_frames, axis=0)
    c_control = channel_corr(root_projected, shifted)
    return {
        "root_projected_relative_unit": "native_float32_no_calibration",
        "derivative_projected_relative_unit": "matlab_double_no_calibration",
        "fixed_zero_lag_projected": describe_correlation(c0),
        "prespecified_one_second_circular_shift_control": describe_correlation(c_control),
        "control_shift_frames": shift_frames,
        "samples_per_channel": N_FRAMES,
        "channels": N_CHANNELS,
        "source_derivative_physical_calibration_verified": False,
        "causal_processing_stage_identified": False,
        "absolute_time_origin_verified": False,
        "signal_values_published": False,
    }


def run_original() -> dict:
    check_prior_source_evidence()
    header = root.authenticated_bytes(SUBJECT, TASK, "vhdr")
    root_order = parse_brainvision_header(header)
    bids_bytes = acquire_pinned_channel_tsv()
    bids_order, bids_units = parse_bids_channel_labels(bids_bytes)
    with TemporaryDirectory(prefix="neu01-g08-no-signal-archive-") as directory:
        derivative_path = Path(directory) / "derived-original.set"
        derived_id = derived.acquire_verified(derivative_path)
        if derived_id["observed_sha256"] != ORIGINAL_DERIVATIVE_SHA:
            raise SourceNotEligible("DERIVATIVE_SHA256_NOT_THE_SAME_G07_ORIGINAL")
        metadata = load_derived_metadata(derivative_path, root_order, bids_order)
        if not metadata["metadata_gate_passed"]:
            comparison = None
            status = "MATCHED_GRID_METADATA_NOT_ELIGIBLE"
            original_eeg_body_downloaded = False
        else:
            raw = root.authenticated_bytes(SUBJECT, TASK, "eeg")
            try:
                comparison = compare_matched_arrays(raw, derivative_path)
                status = "FIXED_GRID_DESCRIPTIVE_COMPARISON_COMPLETE"
            except SignalNotEligible as exc:
                comparison = {"status": "DESCRIPTIVE_SIGNAL_NOT_ELIGIBLE",
                              "error_code": str(exc)}
                status = "DESCRIPTIVE_SIGNAL_NOT_ELIGIBLE"
            original_eeg_body_downloaded = True
            del raw
    return {
        "study": "NEU-01-G08-P01",
        "status": status,
        "protocol_commit": PROTOCOL_COMMIT,
        "source_record": "sub-02/session1/eyesclosed",
        "derivative_original_sha256": derived_id["observed_sha256"],
        "raw_original_sha256_from_known_G04": root.IDENTITIES[(SUBJECT, TASK)][1],
        "bids_declared_unit_metadata": bids_units,
        "metadata_eligibility": metadata,
        "conditional_waveform_diagnostic": comparison,
        "original_root_eeg_body_downloaded": original_eeg_body_downloaded,
        "original_derived_body_authenticated": True,
        "original_binary_archived": False,
        "same_previously_seen_source_pair": True,
        "sample_level_exact_alignment_proven": False,
        "processing_stage_causally_identified": False,
        "neurophysiological_or_clinical_conclusion": False,
    }


def main() -> None:
    try:
        record = run_original()
    except (root.SourceFailure, derived.SourceUnavailable, SourceNotEligible,
            OSError, TypeError, ValueError, KeyError) as exc:
        record = {"study": "NEU-01-G08-P01", "status": "SOURCE_NOT_ELIGIBLE",
                  "protocol_commit": PROTOCOL_COMMIT,
                  "error_type": type(exc).__name__, "error_code": str(exc)[:140],
                  "original_binary_archived": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True), flush=True)
    if record["status"] == "SOURCE_NOT_ELIGIBLE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
