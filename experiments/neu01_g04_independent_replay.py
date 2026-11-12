"""NEU-01-G04-P01: independent IEEE float32 recount of six *known* G03 files.

Technical replay, not a new participant sample or neural interpretation.
Do not import the original NumPy reader, output samples, or infer physical units.
"""
from __future__ import annotations

from hashlib import md5, sha256
from io import BytesIO
import json
import math
from pathlib import Path
import struct
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROTOCOL_COMMIT = "6449070c5b95e1d4bbddd2243549593d4ed85f46"
ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148"
G03_ARCHIVE = Path("docs/results/NEU-01-G03-first-run/audit.json")
G03_ARCHIVE_SHA = "b142e6b0b0d03e1bd6167fba1a3d265bf3d5efd485e8389474f882955bf8195c"
OUTPUT = Path("docs/results/NEU-01-G04-P01-first-run/audit.json")
SUBJECTS = ("sub-02", "sub-03", "sub-04")
TASKS = ("eyesclosed", "eyesopen")
CHANNELS = 61
FRAMES = 150000
RECORD_BYTES = CHANNELS * FRAMES * 4
VALUE_COUNT = CHANNELS * FRAMES
PAIR_COUNT = CHANNELS * (FRAMES - 1)
# Already-known hashes frozen in protocol: (EEG MD5, EEG SHA256, header MD5)
IDENTITIES = {
    ("sub-02", "eyesclosed"): ("afc315cd4fbd76f2788a67fe31be9d8d", "9c9f8c321482c71657047e99a1c259aaa753bb3b5fbe09e392a06b33d8d6dacd", "10a0033fdb6dfd1f72a6e37b8164a269"),
    ("sub-02", "eyesopen"): ("3ca243fb3ab6cabcac5a99b8939abcce", "0e27c11253da07a3f6e6a4eff4716327ac38fcf061e71fc16a501cabe979ca", "4eb149775baddc320f39fcd4fc6f79c6"),
    ("sub-03", "eyesclosed"): ("4ca2b5bab215101621ddf023f31ba042", "cb135f4e93d2a5a76ff04c791934f9a73fe050297e8bcc49cb0f7e04f27b0eb3", "98a9f2d1fbffbab2ad2636c05f340531"),
    ("sub-03", "eyesopen"): ("099a4fdb6e0e5fe105f04f4c250bc0a4", "7099f2df02407f316a445f3fc6fbad33407b841db0fc5abb4b951c6a22f84f45", "ae548d8a0b43dfea2e28d1111d50450c"),
    ("sub-04", "eyesclosed"): ("8a7314e14dcaabc117de238ebec6841f", "eaa0cffa47243b6c121e41fa9e2bde8fa2f99439a9e57b1bf3272a05210592cb", "f79c52b469a3845d70a7877ad18e3e43"),
    ("sub-04", "eyesopen"): ("28079903eac38f9f8670a80f0dc766f1", "eb5bdd843f730e0e42d490840a542831b1c0e525cbfa2b20782f9c568c0032fd", "7d979ba2cfa1a97b092d2782f2138c4b"),
}


class SourceFailure(Exception):
    """Input, provenance or instrumentation failure."""


class ReplayMismatch(Exception):
    """Independently observed count differs from the earlier G03 archive."""


def source_name(subject: str, task: str, extension: str) -> str:
    if (subject, task) not in IDENTITIES or extension not in ("eeg", "vhdr"):
        raise SourceFailure("UNREGISTERED_SOURCE_IDENTITY")
    return f"{subject}_ses-session1_task-{task}_eeg.{extension}"


def authenticated_bytes(subject: str, task: str, extension: str, *, opener=urlopen) -> bytes:
    """Acquire one exact source; bound bytes and independently authenticate."""
    identifier = IDENTITIES.get((subject, task))
    name = source_name(subject, task, extension)
    size = RECORD_BYTES if extension == "eeg" else (1122 if task == "eyesclosed" else 1118)
    expected_md5 = identifier[0] if extension == "eeg" else identifier[2]
    target = f"{ROOT}/{subject}/ses-session1/eeg/{name}"
    request = Request(target, headers={"User-Agent": "RelationalPersistence-NEU01-G04-independent-replay/1"})
    try:
        with opener(request, timeout=45) as response:
            data = response.read(size + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceFailure("OFFICIAL_SOURCE_UNAVAILABLE") from exc
    if len(data) != size:
        raise SourceFailure("SOURCE_SIZE_MISMATCH")
    if md5(data).hexdigest() != expected_md5:
        raise SourceFailure("SOURCE_MD5_MISMATCH")
    if extension == "eeg" and sha256(data).hexdigest() != identifier[1]:
        raise SourceFailure("SOURCE_SHA256_MISMATCH")
    return data


def header_audit(header: bytes, subject: str, task: str, *, channels: int = CHANNELS) -> dict:
    """Original byte-authenticated BrainVision metadata, no unit imputation."""
    try:
        content = header.decode("latin-1")
    except UnicodeError as exc:
        raise SourceFailure("UNREADABLE_HEADER") from exc
    sections: dict[str, dict[str, str]] = {}
    section = ""
    for original_line in content.splitlines():
        line = original_line.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            sections[section] = {}
        elif "=" in line:
            if not section:
                continue
            k, v = line.split("=", 1)
            sections[section][k.strip()] = v.strip()
    common = sections.get("common infos", {})
    binary = sections.get("binary infos", {})
    declared = sections.get("channel infos", {})
    expected = {
        "DataFile": source_name(subject, task, "eeg"),
        "MarkerFile": f"{subject}_ses-session1_task-{task}_eeg.vmrk",
        "DataFormat": "BINARY",
        "DataOrientation": "MULTIPLEXED",
        "NumberOfChannels": str(channels),
        "SamplingInterval": "2000",
    }
    if any(common.get(k) != value for k, value in expected.items()):
        raise SourceFailure("BRAINVISION_HEADER_LAYOUT_MISMATCH")
    if binary.get("BinaryFormat") != "IEEE_FLOAT_32":
        raise SourceFailure("BRAINVISION_FLOAT_REPRESENTATION_MISMATCH")
    if set(declared) != {f"Ch{i}" for i in range(1, channels + 1)}:
        raise SourceFailure("BRAINVISION_CHANNEL_ORDINAL_MISMATCH")
    missing = 0
    for i in range(1, channels + 1):
        parts = declared[f"Ch{i}"].split(",")
        if len(parts) < 3 or not parts[0].strip() or parts[2].strip() != "1":
            raise SourceFailure("UNEXPECTED_OR_UNCALIBRATED_CHANNEL_LAYOUT")
        if len(parts) < 4 or not parts[3].strip():
            missing += 1
    if missing != channels:
        raise SourceFailure("ORIGINAL_UNIT_DECLARATIONS_CHANGED")
    return {"channels": channels, "physical_unit_missing": missing, "calibrated_physical_amplitude": False}


def recount(data: bytes, *, channels: int = CHANNELS, frames: int = FRAMES) -> dict:
    """Standard-library frame-major little-endian decoder; no NumPy use."""
    if not isinstance(data, bytes) or channels < 1 or frames < 2 or len(data) != channels * frames * 4:
        raise SourceFailure("INVALID_EEG_SHAPE_OR_BYTE_COUNT")
    unpack = struct.Struct("<" + "f" * channels)
    prev: list[float | None] = [None] * channels
    by_channel = [0] * channels
    values = zeros = pairs = zero_zero = nonzero_pairs = zero_runs = 0
    frame_bytes = channels * 4
    for t in range(frames):
        row = unpack.unpack_from(data, t * frame_bytes)
        for i, value in enumerate(row):
            if not math.isfinite(value):
                raise SourceFailure("NONFINITE_SAMPLE_STOP")
            values += 1
            is_zero = value == 0.0
            if is_zero:
                zeros += 1
            prior = prev[i]
            if is_zero and (t == 0 or prior != 0.0):
                zero_runs += 1
            if t != 0 and value == prior:
                pairs += 1
                by_channel[i] += 1
                if is_zero:
                    zero_zero += 1
                else:
                    nonzero_pairs += 1
            prev[i] = value
    if pairs != zero_zero + nonzero_pairs or zero_runs != zeros - zero_zero:
        raise SourceFailure("INTERNAL_COUNTING_CONSERVATION_FAILURE")
    if zero_zero > max(0, zeros - 1):
        raise SourceFailure("IMPOSSIBLE_ZERO_RUN_BOUND")
    sorted_pairs = sorted(by_channel)
    return {
        "total_native_values": values,
        "finite": values,
        "nan": 0, "pos_inf": 0, "neg_inf": 0,
        "exact_zero_values": zeros,
        "within_channel_equal_adjacent": pairs,
        "within_channel_possible_adjacencies": channels * (frames - 1),
        "channels_with_any_equal_adjacent": sum(n > 0 for n in by_channel),
        "median_per_channel_equal_adjacent_count": sorted_pairs[channels // 2],
        "max_per_channel_equal_adjacent_count": sorted_pairs[-1],
        "zero_zero_equal_adjacent": zero_zero,
        "nonzero_equal_adjacent": nonzero_pairs,
        "zero_runs": zero_runs,
        "prior_d01_lower_bound_nonzero": max(0, pairs - max(0, zeros - 1)),
    }


def original_report() -> dict:
    body = G03_ARCHIVE.read_bytes()
    if len(body) != 10117 or sha256(body).hexdigest() != G03_ARCHIVE_SHA:
        raise SourceFailure("ORIGINAL_G03_ORACLE_HASH_MISMATCH")
    record = json.loads(body)
    if record.get("study") != "NEU-01-G03" or record.get("participants") != list(SUBJECTS):
        raise SourceFailure("ORIGINAL_G03_ORACLE_SCOPE_MISMATCH")
    return record


def compare_original(computed: dict, original: dict) -> None:
    """After source decoding, verify EVERY frozen G03 summary and source SHA."""
    old = original["recordings"]
    for subject in SUBJECTS:
        for task in TASKS:
            new = computed[subject][task]
            rec = old[subject][task]
            expected_counts = rec["native_census"]
            for key, expected in expected_counts.items():
                if new["census"].get(key) != expected:
                    raise ReplayMismatch(f"{subject}/{task}/{key}")
            if new["eeg_sha256"] != rec["source_identity"]["eeg"]["sha256"]:
                raise ReplayMismatch(f"{subject}/{task}/source_sha256")
            if rec["source_unit_declarations"]["header_unit_counts"] != {"MISSING": 61}:
                raise ReplayMismatch(f"{subject}/{task}/original_units")
            if new["unit_metadata"]["physical_unit_missing"] != 61:
                raise ReplayMismatch(f"{subject}/{task}/replayed_units")
    signs = {"positive": 0, "negative": 0, "zero": 0}
    zero_signs = dict(signs)
    for subject in SUBJECTS:
        c = computed[subject]["eyesclosed"]["census"]
        o = computed[subject]["eyesopen"]["census"]
        delta = c["within_channel_equal_adjacent"] - o["within_channel_equal_adjacent"]
        zero_delta = c["exact_zero_values"] - o["exact_zero_values"]
        if (delta != original["pair_differences"][subject]["paired_equal_difference_numerator"]
                or zero_delta != original["pair_differences"][subject]["paired_zero_difference_numerator"]):
            raise ReplayMismatch(f"{subject}/paired_differences")
        signs["positive" if delta > 0 else "negative" if delta < 0 else "zero"] += 1
        zero_signs["positive" if zero_delta > 0 else "negative" if zero_delta < 0 else "zero"] += 1
    if signs != original["primary_direction_signs"] or zero_signs != original["secondary_zero_direction_signs"]:
        raise ReplayMismatch("full_paired_sign_census")


def replay(*, opener=urlopen) -> dict:
    original_counts: dict[str, dict] = {}
    for subject in SUBJECTS:
        original_counts[subject] = {}
        for task in TASKS:
            header = authenticated_bytes(subject, task, "vhdr", opener=opener)
            metadata = header_audit(header, subject, task)
            eeg = authenticated_bytes(subject, task, "eeg", opener=opener)
            actual_sha = sha256(eeg).hexdigest()
            source_counts = recount(eeg)
            del eeg
            original_counts[subject][task] = {
                "eeg_sha256": actual_sha,
                "unit_metadata": metadata,
                "census": source_counts,
            }
    # The old source outcome enters only AFTER all six independent recounts.
    original = original_report()
    compare_original(original_counts, original)
    return {
        "study": "NEU-01-G04-P01",
        "status": "INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH",
        "protocol_commit": PROTOCOL_COMMIT,
        "original_g03_oracle_sha256": G03_ARCHIVE_SHA,
        "participants": list(SUBJECTS),
        "recordings": original_counts,
        "original_values_recounted": 6 * VALUE_COUNT,
        "no_neural_or_thermodynamic_inference": True,
        "retrospective_same_processed_sources": True,
        "uses_independent_standard_library_reader": True,
    }


def main() -> None:
    try:
        result = replay()
    except ReplayMismatch as exc:
        result = {"study": "NEU-01-G04-P01", "status": "INDEPENDENT_REPLAY_MISMATCH",
                  "error_field": str(exc), "protocol_commit": PROTOCOL_COMMIT}
    except (SourceFailure, OSError, ValueError) as exc:
        result = {"study": "NEU-01-G04-P01", "status": "SOURCE_NOT_ELIGIBLE",
                  "error_type": type(exc).__name__, "error_code": str(exc)[:160],
                  "protocol_commit": PROTOCOL_COMMIT}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
