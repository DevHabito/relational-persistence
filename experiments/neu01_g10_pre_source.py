"""G10 pre-source gates for eight fixed public EEG representation pairs.

This module intentionally performs no network I/O and reads no G10 waveform.
It freezes file identity, validates synthetic metadata, and reuses the prior
G08-D03 direct IEEE comparison without re-fitting or changing its semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5, sha256
import json
from pathlib import Path
from urllib.parse import quote

import numpy as np

from experiments import neu01_g08_d03_native_identity as ieee
from experiments import neu01_g08_fixed_pair as grid
from experiments import neu01_g09_five_source_pairs as g09

PROTOCOL_COMMIT = "9375cb3ccece0a431c136257f0feb43bd43721ab"
PUBLISHER_REVISION = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
S3_ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148/"
G09_FIRST = Path("docs/results/NEU-01-G09-P01-first-run/audit.json")
G09_FIRST_BYTES = 15338
G09_FIRST_SHA256 = "bb3350806c1b86a886f2e79a47b52f967fc34176d598c60742b4b4d1be9dfdba"
ROOT_BYTES = 36600000
DERIVATIVE_BYTES = 73824136
FRAMES = 150000
CHANNELS = 61
DIRECT_POSITIONS = FRAMES * CHANNELS


class GateFailure(ValueError):
    """Synthetic or authenticated input does not satisfy the frozen protocol."""


@dataclass(frozen=True)
class Pair:
    subject: str
    session: int
    task: str
    root_md5: str
    header_md5: str
    derivative_md5: str

    @property
    def state_code(self) -> str:
        return {"eyesclosed": "EC", "eyesopen": "EO"}[self.task]


PAIRS = (
    Pair("sub-05", 2, "eyesclosed", "ac3d71157ac00b3f60dbac2c45e48c91",
         "6d20bac1b724ea1494618348d05a9bb5", "b208c7195fc91d9e83c6dbe5db5dfa76"),
    Pair("sub-05", 2, "eyesopen", "5a612f06d5c25a6f1398b2436038fbcf",
         "9b356328ca335e2eb708006f7db88b62", "f5ae47cd57b5797741585a050c6e60ec"),
    Pair("sub-05", 3, "eyesclosed", "71f9b8aa9dd2e0341a06653c9b7701d4",
         "337c7847e8332783f2c0b3c1daa9ec2d", "a024c145499077c071aa0bc6763bcaee"),
    Pair("sub-05", 3, "eyesopen", "5567489fc66d9449eec4cbf982743ec7",
         "204f628150c80e07d124d308ddb3af2b", "772db180b5b4ba833355a8b5acb4e8f0"),
    Pair("sub-37", 2, "eyesclosed", "ecca3e6f5d73da15805837da46efbdf4",
         "b3a4469ccc11adc677748e13bef6dba2", "b396eced4f25f43fcbff08406695b749"),
    Pair("sub-37", 2, "eyesopen", "673a205c350f2f0b2df9357542e36998",
         "204d8f1ffa670447c6450d5bca8d3aec", "db6fc7bdfa73997886523a94704d0abd"),
    Pair("sub-37", 3, "eyesclosed", "eca98d3bbdec4c87ad7514c2ead3c354",
         "f535d4084878198ae53fcaea95152cc1", "9f889bde521f4cda35f3b04d2598284d"),
    Pair("sub-37", 3, "eyesopen", "a37e9beec644b0962bd36433ad70f06c",
         "5c0b9ffcef8340f35643f358bb2db1ac", "3aaf285adf403e1319dabf83900d3722"),
)

COMPLETE_STATES = frozenset((
    "DIRECT_ARRAYS_IDENTICAL",
    "NUMERIC_EQUAL_IEEE_BITS_DIFFER",
    "AUTHENTICATED_ARRAYS_DIFFER",
))
ALL_STATES = COMPLETE_STATES | frozenset((
    "SOURCE_UNAVAILABLE_OR_UNAUTHENTICATED",
    "SOURCE_METADATA_NOT_ELIGIBLE",
    "SOURCE_EXECUTION_ERROR",
))
IEEE_TO_G10 = {
    "EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL": "DIRECT_ARRAYS_IDENTICAL",
    "NUMERIC_EQUAL_IEEE_BITS_DIFFER": "NUMERIC_EQUAL_IEEE_BITS_DIFFER",
    "AUTHENTICATED_NATIVE_ARRAYS_DIFFER": "AUTHENTICATED_ARRAYS_DIFFER",
}


def require_registered(pair: Pair) -> None:
    if pair not in PAIRS:
        raise GateFailure("UNREGISTERED_G10_PAIR")


def source_paths(pair: Pair) -> dict[str, str]:
    require_registered(pair)
    directory = f"{pair.subject}/ses-session{pair.session}/eeg/"
    stem = f"{pair.subject}_ses-session{pair.session}_task-{pair.task}_"
    number = pair.subject.removeprefix("sub-")
    return {
        "root": directory + stem + "eeg.eeg",
        "header": directory + stem + "eeg.vhdr",
        "channels": directory + stem + "channels.tsv",
        "sidecar": directory + stem + "eeg.json",
        "derivative": (
            "derivatives/preprocessed data/preprocessed_data/"
            f"sub{number}_0{pair.session}_{pair.state_code}.set"
        ),
    }


def publisher_url(pair: Pair, kind: str) -> str:
    paths = source_paths(pair)
    if kind not in paths:
        raise GateFailure("UNREGISTERED_G10_FILE_TYPE")
    return S3_ROOT + quote(paths[kind], safe="/")


def authenticate_body(body: bytes, *, expected_size: int,
                      expected_md5: str) -> dict[str, str | int]:
    """Pure bounded-body oracle; the later source runner must stream and cap I/O."""
    if type(body) is not bytes or expected_size < 1:
        raise GateFailure("INVALID_SOURCE_BODY_OR_EXPECTED_SIZE")
    if len(expected_md5) != 32 or any(c not in "0123456789abcdef" for c in expected_md5):
        raise GateFailure("INVALID_PUBLISHER_MD5_IDENTITY")
    if len(body) != expected_size:
        raise GateFailure("SOURCE_SIZE_MISMATCH")
    if md5(body).hexdigest() != expected_md5:
        raise GateFailure("PUBLISHER_MD5_MISMATCH")
    return {"bytes": len(body), "md5": expected_md5,
            "actual_sha256": sha256(body).hexdigest()}


def header_labels(body: bytes, pair: Pair) -> list[str]:
    """Strict per-session BrainVision layout: no conversion or inferred units."""
    require_registered(pair)
    try:
        content = body.decode("latin-1")
    except (AttributeError, UnicodeError) as exc:
        raise GateFailure("INVALID_BRAINVISION_HEADER") from exc
    sections: dict[str, dict[str, str]] = {}
    section = ""
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().casefold()
            sections[section] = {}
        elif section and "=" in line:
            key, value = line.split("=", 1)
            if key.strip() in sections[section]:
                raise GateFailure("DUPLICATE_BRAINVISION_HEADER_FIELD")
            sections[section][key.strip()] = value.strip()

    common = sections.get("common infos", {})
    binary = sections.get("binary infos", {})
    names = sections.get("channel infos", {})
    paths = source_paths(pair)
    expected = {
        "DataFile": paths["root"].rsplit("/", 1)[-1],
        "MarkerFile": paths["root"].rsplit("/", 1)[-1].replace(".eeg", ".vmrk"),
        "DataFormat": "BINARY",
        "DataOrientation": "MULTIPLEXED",
        "NumberOfChannels": str(CHANNELS),
        "SamplingInterval": "2000",
    }
    if any(common.get(k) != v for k, v in expected.items()):
        raise GateFailure("BRAINVISION_HEADER_SOURCE_OR_GRID_MISMATCH")
    if binary.get("BinaryFormat") != "IEEE_FLOAT_32":
        raise GateFailure("BRAINVISION_BINARY_REPRESENTATION_MISMATCH")
    if set(names) != {f"Ch{i}" for i in range(1, CHANNELS + 1)}:
        raise GateFailure("BRAINVISION_CHANNEL_INDEX_SET_MISMATCH")

    ordered = []
    for n in range(1, CHANNELS + 1):
        fields = names[f"Ch{n}"].split(",")
        if len(fields) < 3 or fields[2].strip() != "1":
            raise GateFailure("BRAINVISION_CHANNEL_RESOLUTION_MISMATCH")
        if len(fields) >= 4 and fields[3].strip():
            raise GateFailure("BRAINVISION_UNEXPECTED_EXPLICIT_UNITS")
        ordered.append(grid.label(fields[0]))
    if len(set(ordered)) != CHANNELS:
        raise GateFailure("DUPLICATE_BRAINVISION_CHANNEL_LABEL")
    return ordered


def read_pinned_channels(body: bytes) -> tuple[list[str], dict]:
    """Require the source bytes already frozen and verified in G08/G09."""
    if len(body) != g09.BIDS_TSV_BYTES or grid._git_blob_sha1(body) != g09.BIDS_TSV_SHA:
        raise GateFailure("PINNED_PUBLISHER_CHANNEL_TSV_HASH_MISMATCH")
    return grid.parse_bids_channel_labels(body)


def check_previous_archives() -> None:
    """Original frozen data provenance must pass before any G10 source I/O."""
    g09.check_immutable_first_evidence()
    grid.hash_archive(G09_FIRST, G09_FIRST_BYTES, G09_FIRST_SHA256)
    previous = json.loads(G09_FIRST.read_bytes())
    if (previous.get("status") != "FIVE_PAIR_DIRECT_IDENTITY_CENSUS_COMPLETE"
            or previous.get("number_exact_bitwise_identical_pairs") != 5
            or previous.get("fixed_source_record_count") != 5):
        raise GateFailure("IMMUTABLE_G09_FIRST_OUTCOME_CHANGED")


def compare_prevalidated_arrays(root32: np.ndarray, derivative64: np.ndarray) -> dict:
    """Synthetic comparison gate; G08-D03 is the unmodified IEEE engine."""
    if (not isinstance(root32, np.ndarray)
            or root32.dtype.kind != "f" or root32.dtype.itemsize != 4):
        raise GateFailure("ORIGINAL_ROOT_MUST_BE_FLOAT32")
    if (not isinstance(derivative64, np.ndarray)
            or derivative64.dtype.kind != "f" or derivative64.dtype.itemsize != 8):
        raise GateFailure("DERIVATIVE_MUST_BE_FLOAT64")
    if root32.shape != derivative64.shape:
        raise GateFailure("DIRECT_ARRAY_GRID_SHAPE_MISMATCH")
    widened = root32.astype("<f8")
    result = ieee.inspect_direct_arrays(widened, derivative64, shift=500)
    result["g10_status"] = IEEE_TO_G10[result["direct_identity_status"]]
    return result


def summarize_rows(rows: list[dict]) -> dict:
    """A result is complete iff all eight registered pairs have a direct census."""
    if len(rows) != len(PAIRS):
        raise GateFailure("ALL_EIGHT_REGISTERED_PAIRS_REQUIRED")
    for spec, row in zip(PAIRS, rows, strict=True):
        if ((row.get("subject"), row.get("session"), row.get("task"))
                != (spec.subject, spec.session, spec.task)):
            raise GateFailure("G10_PAIR_ORDER_OR_IDENTITY_CHANGED")
        if row.get("status") not in ALL_STATES:
            raise GateFailure("UNREGISTERED_G10_PAIR_OUTCOME")
    complete = all(row["status"] in COMPLETE_STATES for row in rows)
    return {
        "study": "NEU-01-G10-P01",
        "status": ("G10_EIGHT_PAIR_CENSUS_COMPLETE" if complete
                   else "G10_EIGHT_PAIR_ELIGIBILITY_INCOMPLETE"),
        "protocol_commit": PROTOCOL_COMMIT,
        "row_statuses": [row["status"] for row in rows],
        "count_directly_identical": sum(
            row["status"] == "DIRECT_ARRAYS_IDENTICAL" for row in rows
        ),
        "count_directly_different": sum(
            row["status"] == "AUTHENTICATED_ARRAYS_DIFFER" for row in rows
        ),
        "source_amplitudes_published": False,
        "neural_or_clinical_conclusion": False,
    }
