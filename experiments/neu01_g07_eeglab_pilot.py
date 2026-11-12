"""G07 single EEGLAB derivative: original byte authentication and metadata only.

No source/derivative signal alignment, numeric EEG observations or neurobiology.
All source outcomes prior to this pilot were already known.
"""
from __future__ import annotations

from hashlib import md5, sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

import numpy as np
from scipy.io import loadmat

PROTOCOL_COMMIT = "6a0e0bd96fd5c8f4d4823c7c02fec0128c8c9d6e"
UPSTREAM_COMMIT = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
RELATIVE = "derivatives/preprocessed data/preprocessed_data/sub02_01_EC.set"
SOURCE = "https://s3.amazonaws.com/openneuro.org/ds004148/" + quote(RELATIVE, safe="/")
EXPECTED_BYTES = 73824136
EXPECTED_MD5 = "2ba3c01f752799634414e2142544fd9b"
OUTPUT = Path("docs/results/NEU-01-G07-P01-first-run/audit.json")
CHUNK = 1024 * 1024


class SourceUnavailable(ValueError):
    """Original object or instrument does not match the frozen source identity."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceUnavailable("OFF_PUBLISHER_REDIRECT_BLOCKED")


def classify_mat_header(prefix: bytes) -> str:
    if prefix.startswith(b"MATLAB 5.0 MAT-file"):
        return "MATLAB_V5"
    if prefix.startswith(b"MATLAB 7.3 MAT-file"):
        return "MATLAB_V73"
    if prefix.startswith(b"\x89HDF\r\n\x1a\n") or prefix[512:520] == b"\x89HDF\r\n\x1a\n":
        return "HDF5"
    return "UNRECOGNIZED_BINARY"


def acquire_verified(destination: Path, *, opener=None) -> dict:
    """Stream only the registered publisher object; verify all bytes, never log data."""
    if destination.exists():
        raise SourceUnavailable("DESTINATION_ALREADY_EXISTS")
    request = Request(SOURCE, headers={"User-Agent": "RelationalPersistence-G07-original-EEGLAB/1"})
    chosen = opener if opener is not None else build_opener(NoRedirects()).open
    actual_md5, actual_sha = md5(), sha256()
    count = 0
    try:
        with chosen(request, timeout=45) as response, destination.open("xb") as handle:
            if response.geturl() != SOURCE:
                raise SourceUnavailable("WRONG_OBJECT_RESPONSE_URL")
            while True:
                block = response.read(CHUNK)
                if not block:
                    break
                count += len(block)
                if count > EXPECTED_BYTES:
                    raise SourceUnavailable("SOURCE_EXCEEDS_EXACT_BYTE_LIMIT")
                handle.write(block)
                actual_md5.update(block)
                actual_sha.update(block)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceUnavailable("ORIGINAL_DERIVATIVE_OBJECT_UNAVAILABLE") from exc
    if count != EXPECTED_BYTES:
        raise SourceUnavailable("ORIGINAL_DERIVATIVE_SIZE_MISMATCH")
    if actual_md5.hexdigest() != EXPECTED_MD5:
        raise SourceUnavailable("ORIGINAL_DERIVATIVE_MD5_MISMATCH")
    return {"original_bytes": count,
            "publisher_annex_md5_verified": True,
            "publisher_annex_md5": EXPECTED_MD5,
            "observed_sha256": actual_sha.hexdigest()}


def clean_int(value):
    try:
        v = np.asarray(value)
        if v.size != 1:
            return None
        f = float(v.item())
        return int(f) if math.isfinite(f) and f.is_integer() and f >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def clean_float(value):
    try:
        v = np.asarray(value)
        if v.size != 1:
            return None
        f = float(v.item())
        return f if math.isfinite(f) else None
    except (TypeError, ValueError, OverflowError):
        return None


def inspect_eeglab_metadata(path: Path) -> dict:
    """Temporary MATLAB v5 decoding; no signal statistics or original values logged."""
    with path.open("rb") as f:
        head = f.read(520)
    family = classify_mat_header(head)
    result = {
        "container_family": family,
        "metadata_parse_status": "FORMAT_NOT_PARSED",
        "original_eeg_amplitudes_reported": False,
        "raw_eeghistory_reported": False,
    }
    if family != "MATLAB_V5":
        return result
    try:
        data = loadmat(path, variable_names=["EEG"],
                       squeeze_me=True, struct_as_record=False,
                       verify_compressed_data_integrity=True)
        eeg = data.get("EEG")
        if eeg is None or not hasattr(eeg, "_fieldnames"):
            result["metadata_parse_status"] = "EEGLAB_STRUCT_MISSING"
            return result
        values = getattr(eeg, "data", None)
        shape = list(values.shape) if isinstance(values, np.ndarray) else None
        dtype = str(values.dtype) if isinstance(values, np.ndarray) else None
        history = getattr(eeg, "history", None)
        if isinstance(history, str):
            h = history.encode("utf-8")
            history_info = {"present": bool(h), "characters": len(history),
                            "sha256": sha256(h).hexdigest() if h else None,
                            "contents_published": False}
        else:
            history_info = {"present": history is not None,
                            "characters": None, "sha256": None,
                            "contents_published": False}
        reference = getattr(eeg, "ref", None)
        if not isinstance(reference, str) or len(reference) > 64 or not reference.isprintable():
            reference = None
        result.update({
            "metadata_parse_status": "EEGLAB_STRUCT_PARSED",
            "nbchan": clean_int(getattr(eeg, "nbchan", None)),
            "srate_hz": clean_float(getattr(eeg, "srate", None)),
            "pnts": clean_int(getattr(eeg, "pnts", None)),
            "trials": clean_int(getattr(eeg, "trials", None)),
            "reference_label": reference,
            "data_array_shape": shape,
            "data_array_dtype": dtype,
            "processing_history_provenance": history_info,
            "sample_alignment_with_bids_verified": False,
        })
    except (ValueError, TypeError, OSError, NotImplementedError, MemoryError) as exc:
        result["metadata_parse_status"] = "MATLAB_METADATA_DECODING_FAILED"
        result["error_type"] = type(exc).__name__
    return result


def run_original(*, opener=None) -> dict:
    with TemporaryDirectory(prefix="neu01-g07-private-") as temp:
        path = Path(temp) / "derivative.set"
        identity = acquire_verified(path, opener=opener)
        metadata = inspect_eeglab_metadata(path)
    return {
        "study": "NEU-01-G07-P01",
        "status": ("DERIVATIVE_BYTES_AUTHENTICATED_METADATA_PARSED"
                   if metadata["metadata_parse_status"] == "EEGLAB_STRUCT_PARSED"
                   else "DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED"),
        "protocol_commit": PROTOCOL_COMMIT,
        "upstream_git_revision": UPSTREAM_COMMIT,
        "publisher_source": RELATIVE,
        "one_fixed_original_derived_object_only": True,
        "source_identity": identity,
        "derivative_metadata": metadata,
        "derivative_body_authenticated": True,
        "other_five_derivative_bodies_authenticated": False,
        "matched_sample_order_or_channel_alignment_verified": False,
        "processing_stage_causally_identified": False,
        "clinical_or_thermodynamic_inference": False,
        "original_signal_body_uploaded": False,
    }


def main() -> None:
    try:
        output = run_original()
    except (SourceUnavailable, ValueError, TypeError, OSError) as exc:
        output = {"study": "NEU-01-G07-P01", "status": "SOURCE_NOT_ELIGIBLE",
                  "protocol_commit": PROTOCOL_COMMIT,
                  "error_type": type(exc).__name__, "error_code": str(exc)[:160],
                  "original_signal_body_uploaded": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True), flush=True)
    if output["status"] == "SOURCE_NOT_ELIGIBLE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
