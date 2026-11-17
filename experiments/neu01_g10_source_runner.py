"""G10 first-source eight-pair audit; source arrays never leave temporary storage.

Source execution is allowed only after the separate registered protocol and
synthetic tests. This study examines public numerical file provenance, not EEG
state, original acquisition samples, or any model of neural persistence.
"""
from __future__ import annotations

from hashlib import md5, sha1, sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

import numpy as np
from scipy.io import loadmat

from experiments import neu01_g09_five_source_pairs as g09
from experiments import neu01_g10_pre_source as frozen

PROTOCOL_COMMIT = frozen.PROTOCOL_COMMIT
OUTPUT = Path("docs/results/NEU-01-G10-P01-first-run/audit.json")
BLOCK = 1024 * 1024
SIDE_CARS = (
    ("01a7e6c4ffe65af3fbeee5bc32f0984a3bdef160", 593),
    ("857311c71e3844e3842ad009ea77f457226fac0e", 597),
    ("01a7e6c4ffe65af3fbeee5bc32f0984a3bdef160", 593),
    ("857311c71e3844e3842ad009ea77f457226fac0e", 597),
    ("0a616db5642e313354e310e4fe8c1be029e6a355", 593),
    ("5a9d79eeb2df07b9f6b7801e25671547b294e772", 597),
    ("01a7e6c4ffe65af3fbeee5bc32f0984a3bdef160", 593),
    ("857311c71e3844e3842ad009ea77f457226fac0e", 597),
)


class SourceUnavailable(ValueError):
    """Official bounded publisher object was missing or not authentic."""


class EligibilityFailure(ValueError):
    """Authenticated file metadata cannot support a direct IEEE comparison."""


def fetch_authenticated(pair: frozen.Pair, kind: str, *,
                        destination: Path | None = None,
                        opener=None) -> tuple[bytes | None, dict]:
    """Stream exactly one registered publisher object; never follow redirects."""
    frozen.require_registered(pair)
    if kind == "root":
        size, expected_md5, expected_git = (
            frozen.ROOT_BYTES, pair.root_md5, None
        )
    elif kind == "header":
        size, expected_md5, expected_git = (
            1122 if pair.task == "eyesclosed" else 1118,
            pair.header_md5, None
        )
    elif kind == "derivative":
        size, expected_md5, expected_git = (
            frozen.DERIVATIVE_BYTES, pair.derivative_md5, None
        )
    elif kind == "channels":
        size, expected_md5, expected_git = (
            g09.BIDS_TSV_BYTES, None, g09.BIDS_TSV_SHA
        )
    elif kind == "sidecar":
        source_sha, source_bytes = SIDE_CARS[frozen.PAIRS.index(pair)]
        size, expected_md5, expected_git = source_bytes, None, source_sha
    else:
        raise SourceUnavailable("UNREGISTERED_G10_SOURCE_KIND")

    if destination is not None and destination.exists():
        raise SourceUnavailable("OUTPUT_ALREADY_EXISTS")
    url = frozen.publisher_url(pair, kind)
    request = Request(url, headers={"User-Agent": "RelationalPersistence-NEU01-G10-FrozenSource/1"})
    chosen = opener if opener is not None else build_opener(g09.NoRedirects()).open
    actual_md5, actual_sha = md5(), sha256()
    git_blob = sha1(b"blob " + str(size).encode("ascii") + b"\0")
    body = bytearray() if destination is None else None
    observed = 0

    try:
        with chosen(request, timeout=45) as response:
            if response.geturl() != url:
                raise SourceUnavailable("UNEXPECTED_SOURCE_URL_OR_REDIRECT")
            if destination is None:
                while True:
                    chunk = response.read(BLOCK)
                    if not chunk:
                        break
                    observed += len(chunk)
                    if observed > size:
                        raise SourceUnavailable("SOURCE_EXCEEDS_PUBLISHER_LENGTH")
                    actual_md5.update(chunk)
                    actual_sha.update(chunk)
                    git_blob.update(chunk)
                    body.extend(chunk)
            else:
                with destination.open("xb") as target:
                    while True:
                        chunk = response.read(BLOCK)
                        if not chunk:
                            break
                        observed += len(chunk)
                        if observed > size:
                            raise SourceUnavailable("SOURCE_EXCEEDS_PUBLISHER_LENGTH")
                        actual_md5.update(chunk)
                        actual_sha.update(chunk)
                        git_blob.update(chunk)
                        target.write(chunk)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceUnavailable("OFFICIAL_OBJECT_DOWNLOAD_FAILED") from exc

    if observed != size:
        raise SourceUnavailable("OFFICIAL_OBJECT_SIZE_MISMATCH")
    if expected_md5 is not None and actual_md5.hexdigest() != expected_md5:
        raise SourceUnavailable("OFFICIAL_OBJECT_PUBLISHER_MD5_MISMATCH")
    if expected_git is not None and git_blob.hexdigest() != expected_git:
        raise SourceUnavailable("OFFICIAL_OBJECT_PUBLISHER_GIT_SHA1_MISMATCH")
    identity = {
        "bytes": observed,
        "publisher_pointer_md5_verified": expected_md5 is not None,
        "pinned_publisher_git_blob_sha1_verified": expected_git is not None,
        "source_body_sha256": actual_sha.hexdigest(),
    }
    return (bytes(body) if body is not None else None), identity


def inspect_sidecar(raw: bytes, pair: frozen.Pair) -> dict:
    """Report BIDS EEG/Misc channel classification without changing eligibility."""
    try:
        item = json.loads(raw)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise EligibilityFailure("UNREADABLE_BIDS_JSON") from exc
    if not isinstance(item, dict):
        raise EligibilityFailure("BIDS_JSON_NOT_OBJECT")
    if (item.get("SamplingFrequency") != 500
            or item.get("RecordingDuration") != 300):
        raise EligibilityFailure("BIDS_JSON_SAMPLE_GRID_INCONSISTENT")
    eeg, misc = item.get("EEGChannelCount"), item.get("MiscChannelCount")
    if (type(eeg) is not int or type(misc) is not int):
        raise EligibilityFailure("BIDS_JSON_CHANNEL_CLASSES_NOT_INTEGERS")
    # BIDS channel-class totals are descriptive metadata, not the registered
    # G10 numerical-alignment eligibility gate (header/TSV/chanlocs).
    return {
        "eeg_channel_count_declared": eeg,
        "misc_channel_count_declared": misc,
        "total_eeg_plus_misc": eeg + misc,
        "root_channels_tsv_declares_61_EEG": True,
        "source_sidecar_classification_disagrees_with_tsv": eeg != frozen.CHANNELS or misc != 0,
        "eeg_reference_metadata": item.get("EEGReference"),
        "amplifier_origin_or_preprocessing_history_proven": False,
    }


def evaluate_one(pair: frozen.Pair) -> dict:
    """For each of eight frozen rows, inspect metadata before root EEG samples."""
    row = {
        "subject": pair.subject, "session": pair.session, "task": pair.task,
        "status": "SOURCE_EXECUTION_ERROR",
        "root_eeg_signal_read": False,
        "derivative_waveform_read": False,
    }
    stage = "source_authentication"
    try:
        with TemporaryDirectory(prefix="neu01-g10-ephemeral-") as directory:
            derivative_path = Path(directory) / "publisher-derivative.set"
            header, header_identity = fetch_authenticated(pair, "header")
            channel_tsv, tsv_identity = fetch_authenticated(pair, "channels")
            sidecar, sidecar_identity = fetch_authenticated(pair, "sidecar")
            _, derivative_identity = fetch_authenticated(
                pair, "derivative", destination=derivative_path
            )
            row["source_identities"] = {
                "header": header_identity, "channels": tsv_identity,
                "sidecar": sidecar_identity, "derivative": derivative_identity,
            }
            stage = "metadata_eligibility"
            original_labels = frozen.header_labels(header, pair)
            bids_labels, bids_units = frozen.read_pinned_channels(channel_tsv)
            sidecar_observation = inspect_sidecar(sidecar, pair)
            row["bids_sidecar_channel_metadata"] = sidecar_observation
            row["bids_units"] = bids_units
            metadata = g09.derive_metadata(derivative_path, original_labels, bids_labels)
            row["metadata_gate"] = metadata
            if not metadata["metadata_gate_passed"]:
                row["status"] = "SOURCE_METADATA_NOT_ELIGIBLE"
                return row

            stage = "source_authentication"
            root_path = Path(directory) / "publisher-source.eeg"
            _, root_identity = fetch_authenticated(
                pair, "root", destination=root_path
            )
            row["source_identities"]["root"] = root_identity
            stage = "direct_comparison"
            root_bytes = root_path.read_bytes()
            row["root_eeg_signal_read"] = True
            root32 = np.frombuffer(root_bytes, dtype="<f4").reshape(
                frozen.FRAMES, frozen.CHANNELS
            )
            derivative = loadmat(
                derivative_path, variable_names=["data"], squeeze_me=False,
                verify_compressed_data_integrity=True,
            ).get("data")
            if (not isinstance(derivative, np.ndarray)
                    or derivative.shape != (frozen.CHANNELS, frozen.FRAMES)
                    or derivative.dtype.kind != "f" or derivative.dtype.itemsize != 8):
                raise EligibilityFailure("DERIVATIVE_NATIVE_ARRAY_NOT_61x150000_DOUBLE")
            row["derivative_waveform_read"] = True
            inspect = frozen.compare_prevalidated_arrays(
                root32, np.asarray(derivative.T, dtype="<f8")
            )
            if inspect["all_aligned_numeric_values_count"] != frozen.DIRECT_POSITIONS:
                raise EligibilityFailure("DIRECT_CENSUS_NOT_ALL_REGISTERED_POSITIONS")
            row["status"] = inspect["g10_status"]
            row["direct_IEEE_comparison"] = {
                key: value for key, value in inspect.items() if key != "g10_status"
            }
            del root_bytes, root32, derivative
    except (SourceUnavailable, frozen.GateFailure, g09.SourceIneligible,
            EligibilityFailure, ValueError, OSError, TypeError, KeyError,
            IndexError, MemoryError, NotImplementedError) as exc:
        if stage == "source_authentication":
            row["status"] = "SOURCE_UNAVAILABLE_OR_UNAUTHENTICATED"
        elif stage == "metadata_eligibility":
            row["status"] = "SOURCE_METADATA_NOT_ELIGIBLE"
        else:
            # A direct data decoding or nonfinite error is explicitly ineligible,
            # never a numerical mismatch or a successful direct comparison.
            row["status"] = "SOURCE_METADATA_NOT_ELIGIBLE"
        row["failure_type"] = type(exc).__name__
        row["failure_code"] = str(exc)[:145]
    return row


def run_original() -> dict:
    frozen.check_previous_archives()
    rows = [evaluate_one(pair) for pair in frozen.PAIRS]
    summary = frozen.summarize_rows(rows)
    summary.update({
        "publisher_revision": frozen.PUBLISHER_REVISION,
        "previous_G08_G09_six_pairs_not_new_subjects": True,
        "all_eight_purposively_preselected_pairs_included": True,
        "first_original_source_rows": rows,
        "source_author_processing_history_identified": False,
        "physical_units_independently_calibrated": False,
        "clinical_or_neural_state_outcome_tested": False,
    })
    return summary


def main() -> None:
    try:
        result = run_original()
    except (SourceUnavailable, frozen.GateFailure, ValueError, OSError,
            TypeError, KeyError, MemoryError, NotImplementedError) as exc:
        result = {
            "study": "NEU-01-G10-P01",
            "status": "G10_EIGHT_PAIR_ELIGIBILITY_INCOMPLETE",
            "protocol_commit": PROTOCOL_COMMIT,
            "preflight_blocked": True,
            "preflight_error_type": type(exc).__name__,
            "preflight_error_code": str(exc)[:145],
            "first_original_source_rows": [
                {"subject": pair.subject, "session": pair.session, "task": pair.task,
                 "status": "SOURCE_EXECUTION_ERROR", "root_eeg_signal_read": False,
                 "derivative_waveform_read": False}
                for pair in frozen.PAIRS
            ],
        }
    result["source_amplitudes_published"] = False
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        raise SystemExit("FIRST_SOURCE_ARCHIVE_ALREADY_EXISTS_DO_NOT_OVERWRITE")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    if result["status"] != "G10_EIGHT_PAIR_CENSUS_COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
