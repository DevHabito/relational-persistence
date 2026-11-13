"""G07-D02: retrospective metadata-only MATLAB variable census after G07 error.

The G07 first source result is immutable; no EEG amplitude values are analyzed.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scipy.io import loadmat, whosmat

from experiments import neu01_g07_eeglab_pilot as original

PROTOCOL_COMMIT = "7bc2b1e73032a290748fdb38326974771a6f8244"
KNOWN_DERIVATIVE_SHA = "2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359"
OLD_AUDIT = Path("docs/results/NEU-01-G07-P01-first-run/audit.json")
OLD_AUDIT_SHA = "60a328cd0cbd69f41da4ffaa8b71921b96f1c0d7fd81751b63b7f126cd1481c3"
OUTPUT = Path("docs/results/NEU-01-G07-D02-first-run/audit.json")
FIELDS = frozenset({
    "EEG", "data", "nbchan", "pnts", "trials", "srate", "ref", "history",
    "chanlocs", "event", "urevent", "xmin", "xmax", "times",
    "icaweights", "icasphere", "icawinv", "icaact", "setname", "comments", "epoch"
})
SMALL_FIELDS = ("nbchan", "pnts", "trials", "srate", "ref", "history")
REQUIRED = ("data", "nbchan", "pnts", "srate")


class FieldAuditError(ValueError):
    """Missing public source identity or unreadable format data."""


def verify_old_original() -> dict:
    body = OLD_AUDIT.read_bytes()
    if len(body) != 1133 or sha256(body).hexdigest() != OLD_AUDIT_SHA:
        raise FieldAuditError("PRIOR_G07_FIRST_SOURCE_ARCHIVE_IDENTITY_FAILURE")
    data = json.loads(body)
    if (data.get("status") != "DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED"
            or data.get("source_identity", {}).get("observed_sha256") != KNOWN_DERIVATIVE_SHA
            or data.get("derivative_metadata", {}).get("metadata_parse_status") != "EEGLAB_STRUCT_MISSING"):
        raise FieldAuditError("PRIOR_G07_FIRST_SOURCE_STATUS_MISMATCH")
    return data


def inspect_mat_top_level(path: Path) -> dict:
    """whosmat reads MAT dimensions/types without loading signal values."""
    entries = whosmat(path)
    if len(entries) > 128:
        raise FieldAuditError("MATLAB_TOPLEVEL_FIELD_COUNT_EXCEEDS_BOUND")
    fields = {}
    extra = 0
    for name, shape, kind in entries:
        if name in fields:
            raise FieldAuditError("DUPLICATE_PUBLISHED_FIELD")
        if name in FIELDS:
            fields[name] = {"dimensions": [int(v) for v in shape], "matlab_class": str(kind)}
        else:
            extra += 1
    # The numeric EEG amplitude matrix 'data' is intentionally absent here.
    small = loadmat(path, variable_names=list(SMALL_FIELDS),
                    squeeze_me=True, struct_as_record=False,
                    verify_compressed_data_integrity=True)
    nbchan = original.clean_int(small.get("nbchan"))
    pnts = original.clean_int(small.get("pnts"))
    trials = original.clean_int(small.get("trials"))
    srate = original.clean_float(small.get("srate"))
    ref = small.get("ref")
    if not isinstance(ref, str) or len(ref) > 64 or not ref.isprintable():
        ref = None
    history = small.get("history")
    history_info = {"contents_published": False, "present": history is not None,
                    "characters": None, "sha256": None}
    if isinstance(history, str):
        body = history.encode("utf-8")
        history_info = {"contents_published": False, "present": bool(body),
                        "characters": len(history),
                        "sha256": sha256(body).hexdigest() if body else None}
    missing = [k for k in REQUIRED if k not in fields]
    if nbchan is None or pnts is None or srate is None or srate <= 0:
        missing.extend(k for k, v in [("nbchan", nbchan),("pnts",pnts),("srate",srate)]
                       if v is None or k == "srate" and v <= 0)
    missing = sorted(set(missing))
    return {
        "metadata_status": ("TOPLEVEL_EEGLAB_FIELD_LAYOUT_RESOLVED" if not missing
                            else "TOPLEVEL_LAYOUT_STILL_UNRESOLVED"),
        "safe_known_top_level_fields": dict(sorted(fields.items())),
        "known_field_names_published_only": True,
        "total_matlab_variables": len(entries),
        "other_unpublished_variable_names_count": extra,
        "missing_required_metadata": missing,
        "nbchan": nbchan, "pnts": pnts, "trials": trials, "srate_hz": srate,
        "reference_label": ref,
        "history_identification": history_info,
        "raw_eeg_values_loaded_by_investigation": False,
        "source_derivative_sample_alignment_verified": False,
    }


def run_source(*, opener=None) -> dict:
    verify_old_original()
    with TemporaryDirectory(prefix="neu01-g07-d02-no-output-") as d:
        source_file = Path(d) / "original.set"
        original_identity = original.acquire_verified(source_file, opener=opener)
        if original_identity["observed_sha256"] != KNOWN_DERIVATIVE_SHA:
            raise FieldAuditError("PREVIOUSLY_AUTHENTICATED_DERIVATIVE_SHA256_CHANGED")
        outcome = inspect_mat_top_level(source_file)
    return {
        "study": "NEU-01-G07-D02", "protocol_commit": PROTOCOL_COMMIT,
        "status": outcome["metadata_status"],
        "retrospective_post_g07_missing_EEG_variable": True,
        "prior_g07_original_sha256": OLD_AUDIT_SHA,
        "original_derivative_full_body_authenticated": True,
        "original_derivative_identity": original_identity,
        "original_derived_path": original.RELATIVE,
        "top_level_metadata": outcome,
        "one_same_source_file_only": True,
        "other_five_derivative_bodies_authenticated": False,
        "sample_alignment_verified": False,
        "causal_processing_stage_identified": False,
        "physiological_or_entropy_inference": False,
        "original_eeg_binary_uploaded": False,
    }


def main():
    try:
        outcome = run_source()
    except (FieldAuditError, original.SourceUnavailable, ValueError, OSError,
            TypeError, KeyError, NotImplementedError) as exc:
        outcome = {
            "study": "NEU-01-G07-D02", "status": "SOURCE_OR_METADATA_NOT_ELIGIBLE",
            "protocol_commit": PROTOCOL_COMMIT, "error_type": type(exc).__name__,
            "error_code": str(exc)[:160], "original_eeg_binary_uploaded": False,
        }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(outcome, indent=2, sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(outcome,indent=2,sort_keys=True),flush=True)
    if outcome["status"] == "SOURCE_OR_METADATA_NOT_ELIGIBLE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
