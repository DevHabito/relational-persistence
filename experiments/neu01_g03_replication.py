"""NEU-01-G03: original-source native float32 repetition, NOT brain complexity.

Protocol-only commit ed0d77e5a3812ec1931ec6b7e3dbdcc0e87777b3 was
recorded before accessing any G03 participant's original EEG amplitudes.
Never print or archive individual original signal values or channel names.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from hashlib import md5, sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np

from experiments import neu01_g01_brainvision_auth as bv
from experiments import neu01_g02_original_signal_qc as qc

PROTOCOL_SHA = "ed0d77e5a3812ec1931ec6b7e3dbdcc0e87777b3"
DATASET_COMMIT = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148"
OUTPUT = Path("docs/results/NEU-01-G03-first-run/audit.json")
PARTICIPANTS = ("sub-02", "sub-03", "sub-04")
TASKS = ("eyesclosed", "eyesopen")
CHANNELS = 61
FRAMES = 150000
BYTES = 36600000
PAIRS = CHANNELS * (FRAMES - 1)
SAMPLES = CHANNELS * FRAMES
CHANNELS_TSV_BLOB = "105960eb0ac14bae43bea73aa479a5c6d995c7a3"
CHUNK = 1024 * 1024
# (actual .eeg md5, original .vhdr md5). Keys frozen in the standalone protocol.
KEYS = {
    ("sub-02", "eyesclosed"): ("afc315cd4fbd76f2788a67fe31be9d8d", "10a0033fdb6dfd1f72a6e37b8164a269"),
    ("sub-02", "eyesopen"): ("3ca243fb3ab6cabcac5a99b8939abcce", "4eb149775baddc320f39fcd4fc6f79c6"),
    ("sub-03", "eyesclosed"): ("4ca2b5bab215101621ddf023f31ba042", "98a9f2d1fbffbab2ad2636c05f340531"),
    ("sub-03", "eyesopen"): ("099a4fdb6e0e5fe105f04f4c250bc0a4", "ae548d8a0b43dfea2e28d1111d50450c"),
    ("sub-04", "eyesclosed"): ("8a7314e14dcaabc117de238ebec6841f", "f79c52b469a3845d70a7877ad18e3e43"),
    ("sub-04", "eyesopen"): ("28079903eac38f9f8670a80f0dc766f1", "7d979ba2cfa1a97b092d2782f2138c4b"),
}


class G03SourceError(ValueError):
    """A source or instrument failure, never evidence for a brain effect."""


def name(subject: str, task: str, suffix: str) -> str:
    if subject not in PARTICIPANTS or task not in TASKS or suffix not in ("eeg.eeg", "eeg.vhdr", "eeg.vmrk", "channels.tsv"):
        raise G03SourceError("UNREGISTERED_SOURCE_PATH")
    return f"{subject}_ses-session1_task-{task}_{suffix}"


def url(subject: str, task: str, suffix: str) -> str:
    return f"{ROOT}/{subject}/ses-session1/eeg/{name(subject, task, suffix)}"


def retrieve(subject: str, task: str, suffix: str, destination: Path, *, opener=urlopen) -> dict:
    """Stream only the exact publisher source, checking size and annex MD5."""
    if suffix not in ("eeg.eeg", "eeg.vhdr"):
        raise G03SourceError("UNREGISTERED_BINARY_TYPE")
    expected_size = BYTES if suffix == "eeg.eeg" else (1122 if task == "eyesclosed" else 1118)
    expected_md5 = KEYS[(subject, task)][0 if suffix == "eeg.eeg" else 1]
    hash_md5, hash_sha = md5(), sha256()
    downloaded = 0
    request = Request(url(subject, task, suffix), headers={"User-Agent": "RP-NEU01-G03-original-audit/1"})
    try:
        with opener(request, timeout=45) as response, destination.open("wb") as handle:
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > expected_size:
                    raise G03SourceError("SOURCE_BYTES_EXCEED_REGISTERED_LIMIT")
                handle.write(chunk)
                hash_md5.update(chunk)
                hash_sha.update(chunk)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise G03SourceError("PUBLIC_SOURCE_UNAVAILABLE") from exc
    if downloaded != expected_size or hash_md5.hexdigest() != expected_md5:
        raise G03SourceError("ORIGINAL_SOURCE_IDENTITY_FAILURE")
    return {"bytes": downloaded, "sha256": hash_sha.hexdigest(), "annex_md5_verified": True}


def read_tsv_names(subject: str, task: str, *, opener=urlopen) -> list[str]:
    request = Request(url(subject, task, "channels.tsv"), headers={"User-Agent": "RP-NEU01-G03-original-audit/1"})
    try:
        with opener(request, timeout=45) as response:
            content = response.read(65537)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise G03SourceError("PUBLIC_CHANNEL_TSV_UNAVAILABLE") from exc
    if len(content) > 65536 or bv.blob_sha1(content) != CHANNELS_TSV_BLOB:
        raise G03SourceError("ORIGINAL_CHANNEL_TSV_IDENTITY_FAILURE")
    try:
        rows = list(csv.DictReader(StringIO(content.decode("utf-8-sig")), delimiter="\t"))
        names = [row["name"] for row in rows]
    except (UnicodeError, KeyError, csv.Error) as exc:
        raise G03SourceError("ORIGINAL_CHANNEL_TSV_INVALID") from exc
    if len(names) != CHANNELS or any(not item for item in names) or len(set(names)) != CHANNELS:
        raise G03SourceError("ORIGINAL_CHANNEL_TSV_COUNT_OR_NAMES_INVALID")
    return names


def verify_header(subject: str, task: str, content: bytes, tsv_names: list[str]) -> dict:
    """Check the exact G03 filename/layout, preserving uncalibrated status."""
    try:
        sections = bv.parse_sections(content)
        common = sections.get("common infos", {})
        binary = sections.get("binary infos", {})
        if (common.get("DataFile") != name(subject, task, "eeg.eeg")
                or common.get("MarkerFile") != name(subject, task, "eeg.vmrk")
                or common.get("DataFormat") != "BINARY"
                or common.get("DataOrientation") != "MULTIPLEXED"
                or common.get("NumberOfChannels") != str(CHANNELS)
                or binary.get("BinaryFormat") != "IEEE_FLOAT_32"):
            raise G03SourceError("BRAINVISION_LAYOUT_MISMATCH")
        interval = Decimal(common["SamplingInterval"])
        if not interval.is_finite() or interval != Decimal(2000):
            raise G03SourceError("SOURCE_SAMPLING_INTERVAL_MISMATCH")
        ch = sections.get("channel infos", {})
        if len(ch) != CHANNELS:
            raise G03SourceError("SOURCE_CHANNEL_COUNT_MISMATCH")
        names = []
        for idx in range(1, CHANNELS + 1):
            value = ch.get(f"Ch{idx}")
            if not value:
                raise G03SourceError("SOURCE_CHANNEL_ORDINALS_MISSING")
            channel_name = value.split(",", 1)[0].strip()
            if not channel_name:
                raise G03SourceError("SOURCE_CHANNEL_NAME_EMPTY")
            names.append(channel_name)
        if len(set(names)) != CHANNELS or names != tsv_names:
            raise G03SourceError("ORIGINAL_HEADER_TSV_CHANNEL_MISMATCH")
        return qc.parse_channel_metadata(content)
    except (bv.SourceLayoutError, qc.QcInstrumentError, KeyError, InvalidOperation) as exc:
        raise G03SourceError("HEADER_PARSE_OR_CALIBRATION_FAILURE") from exc


def describe_native(data: np.ndarray, frames: int = FRAMES, channels: int = CHANNELS) -> dict:
    """Full data census; outputs only counts and channel-distribution summaries."""
    if getattr(data, "dtype", None) != np.dtype("<f4"):
        raise G03SourceError("INVALID_SOURCE_FLOAT32_DTYPE")
    if getattr(data, "shape", None) != (frames, channels) or frames < 2 or channels < 1:
        raise G03SourceError("INVALID_SOURCE_MATRIX_SHAPE")
    finite_count = int(np.count_nonzero(np.isfinite(data)))
    nan_count = int(np.count_nonzero(np.isnan(data)))
    pos_inf = int(np.count_nonzero(np.isposinf(data)))
    neg_inf = int(np.count_nonzero(np.isneginf(data)))
    if finite_count + nan_count + pos_inf + neg_inf != frames * channels:
        raise G03SourceError("FLOAT_CLASSIFICATION_NOT_CONSERVED")
    # This is deliberately fail-closed for G03, not sample-dependent exclusion.
    if nan_count or pos_inf or neg_inf:
        raise G03SourceError("ORIGINAL_NONFINITE_DATA_NOT_ELIGIBLE")
    zero = int(np.count_nonzero(data == np.float32(0)))
    each_channel_pairs = np.count_nonzero(data[1:, :] == data[:-1, :], axis=0)
    pairs = int(np.sum(each_channel_pairs, dtype=np.int64))
    if not 0 <= zero <= frames * channels or not 0 <= pairs <= (frames - 1) * channels:
        raise G03SourceError("INTEGER_COUNT_OUT_OF_BOUNDS")
    sorted_counts = np.sort(each_channel_pairs)
    return {
        "finite": finite_count, "nan": nan_count, "pos_inf": pos_inf, "neg_inf": neg_inf,
        "total_native_values": frames * channels,
        "exact_zero_values": zero,
        "within_channel_equal_adjacent": pairs,
        "within_channel_possible_adjacencies": (frames - 1) * channels,
        "channels_with_any_equal_adjacent": int(np.count_nonzero(each_channel_pairs)),
        "median_per_channel_equal_adjacent_count": int(sorted_counts[channels // 2]),
        "max_per_channel_equal_adjacent_count": int(sorted_counts[-1]),
    }


def run_source(*, opener=urlopen) -> dict:
    result = {
        "study": "NEU-01-G03", "preregistered_protocol_commit": PROTOCOL_SHA,
        "source_git_commit": DATASET_COMMIT,
        "source_version": "ds004148/1.0.0", "participants": list(PARTICIPANTS),
        "session": "session1", "condition_order": list(TASKS),
        "original_signals_published": False, "physical_amplitude_calibrated": False,
        "lzc_computed": False, "clinical_or_thermodynamic_conclusion": False,
        "decision": "SOURCE_NOT_ELIGIBLE",
    }
    detailed: dict[str, dict] = {}
    try:
        for subject in PARTICIPANTS:
            detailed[subject] = {}
            for task in TASKS:
                with TemporaryDirectory(prefix="neu01-g03-") as temp:
                    path = Path(temp)
                    header_path, eeg_path = path / "source.vhdr", path / "source.eeg"
                    header_id = retrieve(subject, task, "eeg.vhdr", header_path, opener=opener)
                    eeg_id = retrieve(subject, task, "eeg.eeg", eeg_path, opener=opener)
                    tsv = read_tsv_names(subject, task, opener=opener)
                    metadata = verify_header(subject, task, header_path.read_bytes(), tsv)
                    if eeg_path.stat().st_size != BYTES:
                        raise G03SourceError("SOURCE_EEG_BYTE_COUNT_CHANGED")
                    signal = np.memmap(eeg_path, dtype="<f4", shape=(FRAMES, CHANNELS), mode="r", order="C")
                    summary = describe_native(signal)
                    del signal
                detailed[subject][task] = {
                    "source_identity": {"vhdr": header_id, "eeg": eeg_id,
                                        "channels_tsv_git_blob_verified": True},
                    "source_unit_declarations": metadata,
                    "native_census": summary,
                }
        pair_differences = {}
        signs = {"positive": 0, "zero": 0, "negative": 0}
        zero_signs = {"positive": 0, "zero": 0, "negative": 0}
        for subject in PARTICIPANTS:
            closed = detailed[subject]["eyesclosed"]["native_census"]
            opened = detailed[subject]["eyesopen"]["native_census"]
            delta = closed["within_channel_equal_adjacent"] - opened["within_channel_equal_adjacent"]
            zero_delta = closed["exact_zero_values"] - opened["exact_zero_values"]
            pair_differences[subject] = {"paired_equal_difference_numerator": delta,
                                         "paired_equal_common_denominator": PAIRS,
                                         "paired_zero_difference_numerator": zero_delta,
                                         "paired_zero_common_denominator": SAMPLES}
            signs["positive" if delta > 0 else "negative" if delta < 0 else "zero"] += 1
            zero_signs["positive" if zero_delta > 0 else "negative" if zero_delta < 0 else "zero"] += 1
        result.update({
            "source_objects_authenticated": 12, "tsv_blobs_authenticated": 6,
            "observed_original_values": 6 * SAMPLES,
            "observed_original_adjacencies": 6 * PAIRS,
            "recordings": detailed, "pair_differences": pair_differences,
            "primary_direction_signs": signs, "secondary_zero_direction_signs": zero_signs,
            "decision": ("DESCRIPTIVE_DIRECTION_REPLICATED_IN_ALL_THREE"
                         if signs["positive"] == 3 else "DIRECTION_NOT_UNIFORMLY_REPLICATED"),
        })
    except G03SourceError as exc:
        # Partial participant results must never be presented as an eligible 3-person study.
        result["error_code"] = str(exc)
    except Exception as exc:
        result["error_code"] = f"INSTRUMENT_EXCEPTION_{type(exc).__name__}"
    return result


def main() -> None:
    outcome = run_source()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2, sort_keys=True), flush=True)
    if outcome["decision"] == "SOURCE_NOT_ELIGIBLE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
