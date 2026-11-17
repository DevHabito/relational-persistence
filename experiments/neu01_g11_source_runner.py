"""NEU-01 G11: first authenticated eyes-closed retest on frozen public sources.

The first source run uses exactly 24 original BrainVision EEG objects and never
the numerically duplicate EEGLAB formats. Any failed row blocks the registered
cohort statistic; there are no substitute files, sensor/lag searches or fits.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5, sha256
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

import numpy as np

from experiments import neu01_g08_fixed_pair as grid
from experiments import neu01_g09_five_source_pairs as g09
from experiments import neu01_g11_alpha_core as core

PROTOCOL_COMMIT = "3c86a3b89ffacfc27c5136a5d1a696a56404733d"
SOURCE_REVISION = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
SOURCE_ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148/"
OUTPUT = Path("docs/results/NEU-01-G11-P01-first-run/audit.json")
G10_FIRST = Path("docs/results/NEU-01-G10-P01-first-run/audit.json")
G10_BYTES = 36_006
G10_SHA256 = "5d7c239260da9d9d65cda652c617fdfe906affdff88f85be1a829877f49568c5"
ROOT_BYTES = 36_600_000
HEADER_BYTES = 1_122
CHANNEL_LABELS_SHA256 = "0eb9d03a6f1c62af87f95e8de05d9a39632529208c4e8c1be945f809f77d9b99"
DOWNLOAD_BLOCK = 1_048_576


@dataclass(frozen=True)
class Source:
    subject: str
    session: int
    eeg_md5: str
    header_md5: str


SOURCES = (
    Source("sub-10", 1, "6b9da1894e9246ce2998c10e904bc14f", "bb7197d07b96ca443b866e154442290b"),
    Source("sub-10", 3, "5febbf0f7d8c15456c317ef9a20d3d83", "ed7a2d3b1668ea19d9ccb3ac7a408d23"),
    Source("sub-11", 1, "717a82a7548d09acd9cdbd83efe73160", "cfeb3b880318af39e62d5122e5fec26b"),
    Source("sub-11", 3, "2f899fd3527f9238229d4c0c271049d6", "90a1aafa9a590103f67bb440b5fd0eee"),
    Source("sub-12", 1, "1c11a62afad771f104c210041c801bbe", "6fe144389930c9ea71d6aa799aa213eb"),
    Source("sub-12", 3, "5a08adc495eb376700265cc19bf9cc73", "cf4fb77536d837570dc4e78ab6655705"),
    Source("sub-13", 1, "61c78afc952f892746c87f7d3d6d0947", "d26c2a4cb98b75c0b603346688eec734"),
    Source("sub-13", 3, "d5d2d5291bdd55cfeb0eaf280f5b1620", "e8ce7cdc00fb19740fe512a747ec4fb1"),
    Source("sub-14", 1, "711d3ca94c501898331d6553bb81fa9c", "8a674c19d6f6dfa5fa405e107e9fa9ce"),
    Source("sub-14", 3, "c0e46c2cb5036244dbc034a48b4700e1", "543597cc3bd4d79c3ea3c7e4fe4feb6c"),
    Source("sub-15", 1, "a82f3420a7a2298c8d12c3cfcb4895b9", "d7323b6025c212ff4b1ce3c93edb21ad"),
    Source("sub-15", 3, "4d94ced309530fa4ad1a472b6e618890", "d50ecbe6e2a11c68793746bd2f6cc737"),
    Source("sub-16", 1, "7bbd12e66d8820b23fac8da9bd200adc", "711ee2872336808ea13dea98a3cd6e48"),
    Source("sub-16", 3, "b1215dbebb1aa8e4a305fc8efdf16cce", "eb2dc175ce062071941a8c79897261a1"),
    Source("sub-17", 1, "404476455862074e65e72ddd3c746522", "311edadbbdb92075856848107b458acd"),
    Source("sub-17", 3, "78649972f0bcb66d1b441af040185453", "1d94e8a249a6b88def1ce318fe5eb5bb"),
    Source("sub-18", 1, "7c572bd9eb0692fd7ef684c16cc9322f", "cccb0d0a9d79a1719890ac1b20bb1da6"),
    Source("sub-18", 3, "51eda67e8e011e5c84dc94d3e133e34a", "13913715b5f5e1fe671c0974a297609b"),
    Source("sub-19", 1, "5bde6724942dfe695c974d5f987fd975", "075850b8e62a4c1e1d2d2a6a7d38c888"),
    Source("sub-19", 3, "e00faf74e8e98ee4f46df67c250f90b4", "75eec84f86a2d3ef16c924e45bf56883"),
    Source("sub-20", 1, "8207cb27f445156ad24c9e98a520386e", "3b07675b71ee970e0da20caee1ef16f7"),
    Source("sub-20", 3, "7c1aa0dd7165b9315c054b866f894aad", "e4dbffbd58b83852f419e7fa74369807"),
    Source("sub-21", 1, "fdd3cdff00b1b8b5d026e8dcabb313ba", "aa6d7e1c3a083bb488fd197419cd7153"),
    Source("sub-21", 3, "4c5f2b2aae18d426e728355dc3b24a94", "267a8e017cabb08925ee5a242b2efc73"),
)
SUBJECTS = tuple(f"sub-{n:02d}" for n in range(10, 22))


class SourceFailure(ValueError):
    """Original publisher object is missing, redirected, or cannot be authenticated."""


class HeaderFailure(ValueError):
    """An authenticated BrainVision header cannot support the fixed source grid."""


def frozen_source(source: Source) -> None:
    if source not in SOURCES:
        raise SourceFailure("UNREGISTERED_G11_SOURCE")


def relative_path(source: Source, extension: str) -> str:
    frozen_source(source)
    if extension not in ("eeg", "vhdr"):
        raise SourceFailure("UNREGISTERED_G11_FILE_EXTENSION")
    stem = f"{source.subject}_ses-session{source.session}_task-eyesclosed_eeg"
    return f"{source.subject}/ses-session{source.session}/eeg/{stem}.{extension}"


def pinned_url(source: Source, extension: str) -> str:
    return SOURCE_ROOT + relative_path(source, extension)


def authenticate_bytes(source: Source, extension: str, *, opener=None) -> tuple[bytes, dict]:
    """Bounded, single-source read, no redirects and no publisher substitutions."""
    frozen_source(source)
    if extension == "eeg":
        expected_size, expected_md5 = ROOT_BYTES, source.eeg_md5
    elif extension == "vhdr":
        expected_size, expected_md5 = HEADER_BYTES, source.header_md5
    else:
        raise SourceFailure("UNREGISTERED_G11_FILE_EXTENSION")
    url = pinned_url(source, extension)
    selected = opener if opener is not None else build_opener(g09.NoRedirects()).open
    request = Request(url, headers={"User-Agent": "RelationalPersistence-G11-OriginalEEG/1"})
    h_md5, h_sha = md5(), sha256()
    body = bytearray()
    try:
        with selected(request, timeout=45) as response:
            if response.geturl() != url:
                raise SourceFailure("G11_REDIRECT_OR_WRONG_RESPONSE_SOURCE")
            while True:
                chunk = response.read(DOWNLOAD_BLOCK)
                if not chunk:
                    break
                if len(body) + len(chunk) > expected_size:
                    raise SourceFailure("G11_EXCEEDS_SOURCE_BYTE_LIMIT")
                body.extend(chunk)
                h_md5.update(chunk)
                h_sha.update(chunk)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceFailure("G11_OFFICIAL_SOURCE_UNAVAILABLE") from exc
    if len(body) != expected_size:
        raise SourceFailure("G11_ORIGINAL_SOURCE_SIZE_MISMATCH")
    if h_md5.hexdigest() != expected_md5:
        raise SourceFailure("G11_ORIGINAL_SOURCE_MD5_MISMATCH")
    return bytes(body), {
        "publisher_pointer_md5_verified": True,
        "bytes": expected_size,
        "published_body_sha256": h_sha.hexdigest(),
    }


def original_header_labels(header: bytes, source: Source) -> list[str]:
    """Validate original session and 61 fixed labels, without channel reordering."""
    frozen_source(source)
    try:
        content = header.decode("latin-1")
    except (UnicodeError, AttributeError) as exc:
        raise HeaderFailure("G11_INVALID_ORIGINAL_HEADER_ENCODING") from exc
    section = ""
    sections: dict[str, dict[str, str]] = {}
    for raw in content.splitlines():
        s = raw.strip()
        if not s or s.startswith((";", "#")):
            continue
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].strip().lower()
            sections[section] = {}
        elif section and "=" in s:
            key, value = s.split("=", 1)
            key = key.strip()
            if key in sections[section]:
                raise HeaderFailure("G11_DUPLICATE_HEADER_FIELD")
            sections[section][key] = value.strip()
    root = relative_path(source, "eeg").rsplit("/", 1)[-1]
    expected = {
        "DataFile": root,
        "MarkerFile": root[:-4] + ".vmrk",
        "DataFormat": "BINARY",
        "DataOrientation": "MULTIPLEXED",
        "NumberOfChannels": "61",
        "SamplingInterval": "2000",
    }
    common = sections.get("common infos", {})
    binary = sections.get("binary infos", {})
    channels = sections.get("channel infos", {})
    if any(common.get(k) != v for k, v in expected.items()):
        raise HeaderFailure("G11_SOURCE_HEADER_OR_TIME_GRID_CHANGED")
    if binary.get("BinaryFormat") != "IEEE_FLOAT_32":
        raise HeaderFailure("G11_ORIGINAL_FORMAT_NOT_FLOAT32")
    if set(channels) != {f"Ch{k}" for k in range(1, 62)}:
        raise HeaderFailure("G11_ORIGINAL_CHANNEL_INDICES_CHANGED")
    labels = []
    for k in range(1, 62):
        parts = channels[f"Ch{k}"].split(",")
        if len(parts) < 3 or parts[2].strip() != "1":
            raise HeaderFailure("G11_CHANNEL_RESOLUTION_CHANGED")
        if len(parts) >= 4 and parts[3].strip():
            raise HeaderFailure("G11_PHYSICAL_UNITS_NOT_EXPECTED_IN_HEADER")
        labels.append(grid.label(parts[0]))
    if len(set(labels)) != 61 or grid.ordered_hash(labels) != CHANNEL_LABELS_SHA256:
        raise HeaderFailure("G11_ORIGINAL_CHANNEL_ORDER_OR_LABELS_CHANGED")
    return labels


def check_frozen_evidence() -> None:
    """Prior EEG file equivalence is data provenance, not a retest outcome."""
    g09.check_immutable_first_evidence()
    grid.hash_archive(G10_FIRST, G10_BYTES, G10_SHA256)
    prior = json.loads(G10_FIRST.read_bytes())
    if (prior.get("status") != "G10_EIGHT_PAIR_CENSUS_COMPLETE"
            or prior.get("count_directly_identical") != 8):
        raise SourceFailure("G11_PRIOR_G10_SOURCE_ARCHIVE_CHANGED")
    if len(SOURCES) != 24 or len(set(SOURCES)) != 24:
        raise SourceFailure("G11_FROZEN_SOURCE_COUNT_CHANGED")
    if [x.subject for x in SOURCES[::2]] != list(SUBJECTS):
        raise SourceFailure("G11_SUBJECT_ORDER_CHANGED")
    if any((x.session, y.session) != (1, 3)
           for x, y in zip(SOURCES[::2], SOURCES[1::2], strict=True)):
        raise SourceFailure("G11_SESSION_ORDER_CHANGED")


def evaluate_record(source: Source) -> tuple[dict, dict | None]:
    row = {
        "subject": source.subject,
        "session": source.session,
        "task": "eyesclosed",
        "status": "SOURCE_EXECUTION_ERROR",
        "waveform_read": False,
        "feature_extraction_complete": False,
    }
    step = "download"
    try:
        header, hid = authenticate_bytes(source, "vhdr")
        root, rid = authenticate_bytes(source, "eeg")
        row["source_authentication"] = {"vhdr": hid, "eeg": rid}
        step = "header"
        ordered = original_header_labels(header, source)
        row["normalized_ordered_61_labels_sha256"] = grid.ordered_hash(ordered)
        step = "measurement"
        data = np.frombuffer(root, dtype="<f4").reshape(core.FRAMES, core.CHANNELS)
        row["waveform_read"] = True
        coeff = core.alpha_fourier_coefficients(data)
        features = core.compute_three_features(
            coeff, participant_number=int(source.subject[-2:]), session=source.session
        )
        row["feature_extraction_complete"] = True
        row["status"] = "ELIGIBLE"
        del root, data, coeff
        return row, features
    except (SourceFailure, HeaderFailure, core.MeasurementIneligible,
            ValueError, TypeError, KeyError, OSError, MemoryError,
            NotImplementedError) as exc:
        row["status"] = {
            "download": "SOURCE_UNAVAILABLE_OR_UNAUTHENTICATED",
            "header": "SOURCE_METADATA_NOT_ELIGIBLE",
            "measurement": "SOURCE_MEASUREMENT_NOT_ELIGIBLE",
        }.get(step, "SOURCE_EXECUTION_ERROR")
        row["failure_type"] = type(exc).__name__
        row["failure_code"] = str(exc)[:145]
        return row, None


def run_original() -> dict:
    check_frozen_evidence()
    rows = []
    first: dict[str, dict] = {}
    last: dict[str, dict] = {}
    for source in SOURCES:
        outcome, features = evaluate_record(source)
        rows.append(outcome)
        if outcome["status"] == "ELIGIBLE":
            (first if source.session == 1 else last)[source.subject] = features
    complete = (len(rows) == len(SOURCES)
                and all(x["status"] == "ELIGIBLE" for x in rows))
    if complete:
        measured = core.complete_analysis(
            [first[s] for s in SUBJECTS], [last[s] for s in SUBJECTS]
        )
    else:
        measured = {
            "study": "NEU-01-G11-P01",
            "status": "G11_SOURCE_INCOMPLETE",
            "all_requested_source_records_eligible": False,
            "no_12_person_cohort_statistic_computed": True,
        }
    measured.update({
        "protocol_commit": PROTOCOL_COMMIT,
        "publisher_revision": SOURCE_REVISION,
        "source_records_requested": 24,
        "source_records_eligible": sum(r["status"] == "ELIGIBLE" for r in rows),
        "first_original_record_results": rows,
        "first_source_data_from_unique_participant_visits": True,
        "source_derivative_file_duplication_excluded": True,
        "physical_amplitude_calibration_independently_verified": False,
        "source_author_preprocessing_pipeline_known": False,
        "neuronal_persistence_or_clinical_diagnosis_proven": False,
        "source_waveforms_published": False,
    })
    return measured


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("G11_FIRST_SOURCE_ARCHIVE_EXISTS_DO_NOT_OVERWRITE")
    try:
        result = run_original()
    except (SourceFailure, HeaderFailure, core.MeasurementIneligible,
            ValueError, TypeError, KeyError, OSError, MemoryError,
            NotImplementedError) as exc:
        result = {
            "study": "NEU-01-G11-P01",
            "status": "G11_SOURCE_INCOMPLETE",
            "protocol_commit": PROTOCOL_COMMIT,
            "preflight_blocked": True,
            "error_type": type(exc).__name__,
            "error_code": str(exc)[:145],
            "source_records_requested": 24,
            "source_records_eligible": 0,
            "source_waveforms_published": False,
        }
    result["source_waveforms_published"] = False
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2), flush=True)
    if result["status"] == "G11_SOURCE_INCOMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
