"""NEU-01/G12 first original publisher EEG test for fixed rank-fusion increment.

Only the 24 preregistered original BrainVision objects are accessed. All source
records must be eligible before any G12 12-person outcome is computed. Published
EEG waveform samples are never retained in output archives or repository.
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
from experiments import neu01_g11_alpha_core as g11
from experiments import neu01_g11_source_runner as prior_source
from experiments import neu01_g12_rank_core as core

PROTOCOL_COMMIT = "c6787a0a3186516ba1275e0e419fcfbd5b7d4b09"
PUBLISHER_REVISION = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
SOURCE_ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148/"
OUTPUT = Path("docs/results/NEU-01-G12-P01-first-run/audit.json")
PRIOR_FIRST = Path("docs/results/NEU-01-G11-P01-first-run/audit.json")
PRIOR_BYTES = 33803
PRIOR_SHA = "0a7bc6785053c4da697f8d287245a6fa93a25ce1a69f945e447f0b3829b51537"
ROOT_BYTES = 36600000
HEADER_BYTES = 1122
EXPECTED_LABELS_SHA = prior_source.CHANNEL_LABELS_SHA256
SOURCE_BLOCK = 1048576


class SourceFailure(ValueError):
    """Publisher object unavailable, swapped, redirected or altered."""


class MetadataFailure(ValueError):
    """Authenticated source cannot pass the registered header/montage gate."""


@dataclass(frozen=True)
class Source:
    subject: str
    session: int
    root_md5: str
    header_md5: str


SOURCES = (
    Source("sub-22", 1, "f89ea26bb161ca03d869b10573fda363", "77f7941653b599ab6d482be0f70d90c5"),
    Source("sub-22", 3, "df135b5ae0d2c895c5bf23b257fddfd0", "00592256f0a3e9a1918c484052a909c1"),
    Source("sub-23", 1, "42bb7772ecc065d2e032d523e9ac83bc", "3c3466b1158957da70b8ad9d638f1111"),
    Source("sub-23", 3, "81e3a9f9a2f7b9649949912ac9f465c2", "25fba0fe9bfb6a46f4174b0313a9a75f"),
    Source("sub-24", 1, "a7106065c3adc1d1e17d0a63a32729cc", "a889320c38c1d69cb56a5e6516c6e9bb"),
    Source("sub-24", 3, "72a3a97f6cc61008d76e2bb76a96ffbf", "98719d8765f1ec913052f3befeb10457"),
    Source("sub-25", 1, "f1b709a298ae97561f82e91c68308243", "8be92f6def05b8ddc5250f25f4047daa"),
    Source("sub-25", 3, "d490023deff57a6e7621d3ba24664eee", "b75b1d06352ffb35454782e209d2dc6f"),
    Source("sub-26", 1, "d7179c72805a129a26c916e04728fb53", "42c6700ce6f848c0602932f23d5d9044"),
    Source("sub-26", 3, "32b58bc047412ad794c038b17052da09", "b4329687e7099645b498ca48119ff9b7"),
    Source("sub-27", 1, "48193873e5564fd149f2645e8f139f40", "63e3ca31aac44ba77ab69f903a425cae"),
    Source("sub-27", 3, "124c3d6fdd1f1c45b8741d2187f0a199", "93cdb6f039dc713a0ba97ced5b6688ce"),
    Source("sub-28", 1, "b6bb527ea5eab3639016c58a2ec2270a", "dc52f21e98143e196d9103248c2f6c47"),
    Source("sub-28", 3, "7623bbb4fc2598e5691ff533c8595aef", "06c5409076ea4b345884b571d90d50c6"),
    Source("sub-29", 1, "968982df0a291a522935ebd16b7c2f09", "1259d1ead25109fba8f59fe73f180d98"),
    Source("sub-29", 3, "1d8723cea510b10941230d2cebfa63f3", "49a1f166b1f7c8a4d7069e1785506754"),
    Source("sub-30", 1, "2554e778ff4891dd1d14aa23caa6adc6", "81e01326461ccedd4a89c35ff0d8a606"),
    Source("sub-30", 3, "87afe810e99bd4cf11c8e6f06438e61f", "5824fddd857c0f372435a46bad18c218"),
    Source("sub-31", 1, "bfa6bbc41205e3c99bacbdad6bbff9a6", "78a324a661797faf098386ebaa9bfe43"),
    Source("sub-31", 3, "279aabaa7d5b14daa5d9fd136b6f8b93", "2a418e2450ec83fc32d17d9cd1163653"),
    Source("sub-32", 1, "136c98ebf145aa9828e25b760252a910", "08a09c9ee8b7fa3df43c7192a2cfa41c"),
    Source("sub-32", 3, "b5e65d9ce396d14925bd52e4fb6e651b", "82a3eb15fa3e62e95a133d35be6ba3f0"),
    Source("sub-33", 1, "09f8fe16392654af50844aa0c112221a", "685452fc788735e7fe8eca8c3dba7996"),
    Source("sub-33", 3, "2b731a165c0ef7d66b6503c878cecd08", "fac66203876ae74161107ef330dbc4ca"),
)
SUBJECTS = tuple(f"sub-{i}" for i in core.SUBJECTS)


def check_registered(source: Source) -> None:
    if source not in SOURCES:
        raise SourceFailure("UNREGISTERED_G12_PUBLISHER_SOURCE")


def source_path(source: Source, suffix: str) -> str:
    check_registered(source)
    if suffix not in ("eeg", "vhdr"):
        raise SourceFailure("G12_UNREGISTERED_PUBLISHER_FORMAT")
    name = f"{source.subject}_ses-session{source.session}_task-eyesclosed_eeg.{suffix}"
    return f"{source.subject}/ses-session{source.session}/eeg/{name}"


def source_url(source: Source, suffix: str) -> str:
    return SOURCE_ROOT + source_path(source, suffix)


def authenticated_source(source: Source, suffix: str, *, opener=None) -> tuple[bytes, dict]:
    """Bounded single-source original download, no URL redirect or mirror fallback."""
    check_registered(source)
    if suffix == "eeg":
        expected_size, expected_md5 = ROOT_BYTES, source.root_md5
    elif suffix == "vhdr":
        expected_size, expected_md5 = HEADER_BYTES, source.header_md5
    else:
        raise SourceFailure("G12_UNREGISTERED_PUBLISHER_FORMAT")
    target = source_url(source, suffix)
    request = Request(target, headers={"User-Agent": "RelationalPersistence-G12-FrozenEEG/1"})
    open_url = opener if opener is not None else build_opener(g09.NoRedirects()).open
    hash_md5, hash_sha = md5(), sha256()
    body = bytearray()
    try:
        with open_url(request, timeout=45) as response:
            if response.geturl() != target:
                raise SourceFailure("G12_UNEXPECTED_SOURCE_URL_OR_REDIRECT")
            while True:
                chunk = response.read(SOURCE_BLOCK)
                if not chunk:
                    break
                if len(body) + len(chunk) > expected_size:
                    raise SourceFailure("G12_SOURCE_EXCEEDS_MAX_BYTES")
                body.extend(chunk)
                hash_md5.update(chunk)
                hash_sha.update(chunk)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceFailure("G12_PUBLISHER_SOURCE_UNAVAILABLE") from exc
    if len(body) != expected_size:
        raise SourceFailure("G12_SOURCE_SIZE_MISMATCH")
    if hash_md5.hexdigest() != expected_md5:
        raise SourceFailure("G12_PUBLISHER_SOURCE_MD5_MISMATCH")
    return bytes(body), {
        "bytes": expected_size,
        "publisher_MD5_body_verified": True,
        "actual_original_sha256": hash_sha.hexdigest(),
    }


def header_electrodes(body: bytes, source: Source) -> list[str]:
    """Validate original 61-channel montage without fitting/reordering channels."""
    check_registered(source)
    try:
        raw = body.decode("latin-1")
    except (UnicodeError, AttributeError) as exc:
        raise MetadataFailure("G12_UNREADABLE_ORIGINAL_HEADER") from exc
    sections: dict[str, dict[str, str]] = {}
    section = ""
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith((";", "#")):
            continue
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].strip().lower()
            sections[section] = {}
        elif section and "=" in s:
            key, value = s.split("=", 1)
            key = key.strip()
            if key in sections[section]:
                raise MetadataFailure("G12_DUPLICATE_BRAINVISION_HEADER_KEY")
            sections[section][key] = value.strip()

    basename = source_path(source, "eeg").rsplit("/", 1)[-1]
    common = sections.get("common infos", {})
    binary = sections.get("binary infos", {})
    channels = sections.get("channel infos", {})
    expected_common = {
        "DataFile": basename,
        "MarkerFile": basename[:-4] + ".vmrk",
        "DataFormat": "BINARY",
        "DataOrientation": "MULTIPLEXED",
        "NumberOfChannels": "61",
        "SamplingInterval": "2000",
    }
    if any(common.get(k) != v for k, v in expected_common.items()):
        raise MetadataFailure("G12_HEADER_FILE_OR_GRID_MISMATCH")
    if binary.get("BinaryFormat") != "IEEE_FLOAT_32":
        raise MetadataFailure("G12_EXPECTED_IEEE_FLOAT_32")
    if set(channels) != {f"Ch{i}" for i in range(1, 62)}:
        raise MetadataFailure("G12_WRONG_CHANNEL_INDEX_SET")
    labels = []
    for i in range(1, 62):
        parts = channels[f"Ch{i}"].split(",")
        if len(parts) < 3 or parts[2].strip() != "1":
            raise MetadataFailure("G12_BAD_CHANNEL_RESOLUTION")
        if len(parts) >= 4 and parts[3].strip():
            raise MetadataFailure("G12_UNEXPECTED_PHYSICAL_UNIT_DECLARATION")
        labels.append(grid.label(parts[0]))
    if len(set(labels)) != 61 or grid.ordered_hash(labels) != EXPECTED_LABELS_SHA:
        raise MetadataFailure("G12_ORIGINAL_CHANNEL_ORDER_MISMATCH")
    return labels


def verify_prior_and_manifest() -> None:
    """G11 original result may inform G12 design but is never a G12 observation."""
    prior_source.check_frozen_evidence()
    grid.hash_archive(PRIOR_FIRST, PRIOR_BYTES, PRIOR_SHA)
    prior = json.loads(PRIOR_FIRST.read_bytes())
    if (prior["status"] != "G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT"
            or prior["source_records_eligible"] != 24):
        raise SourceFailure("G12_PRIOR_G11_ORIGINAL_VERDICT_CHANGED")
    if len(SOURCES) != 24 or len(set(SOURCES)) != 24:
        raise SourceFailure("G12_FROZEN_TWENTY_FOUR_SOURCES_CHANGED")
    expected = [(f"sub-{i}", ses) for i in core.SUBJECTS for ses in (1, 3)]
    observed = [(row.subject, row.session) for row in SOURCES]
    if observed != expected or len({row.root_md5 for row in SOURCES}) != 24:
        raise SourceFailure("G12_FROZEN_SUBJECT_SESSION_ORDER_CHANGED")
    if any(len(row.root_md5) != 32 or len(row.header_md5) != 32 for row in SOURCES):
        raise SourceFailure("G12_MALFORMED_PUBLISHER_MD5_POINTER")


def measure_one(source: Source) -> tuple[dict, dict | None]:
    """Keep every failure as one source row; one failure blocks cohort results."""
    row = {
        "subject": source.subject,
        "session": source.session,
        "task": "eyesclosed",
        "status": "SOURCE_EXECUTION_ERROR",
        "source_signal_decoded": False,
        "features_computed": False,
    }
    stage = "authentication"
    try:
        header, header_identity = authenticated_source(source, "vhdr")
        eeg, root_identity = authenticated_source(source, "eeg")
        row["body_identity"] = {"header": header_identity, "root": root_identity}
        stage = "metadata"
        ordered = header_electrodes(header, source)
        row["ordered_labels_sha256"] = grid.ordered_hash(ordered)
        stage = "measurement"
        native = np.frombuffer(eeg, dtype="<f4").reshape(g11.FRAMES, g11.CHANNELS)
        row["source_signal_decoded"] = True
        coeff = g11.alpha_fourier_coefficients(native)
        feats = core.compute_features(
            coeff, participant=int(source.subject[-2:]), session=source.session
        )
        row["status"] = "ELIGIBLE"
        row["features_computed"] = True
        del native, eeg, coeff
        return row, feats
    except (SourceFailure, MetadataFailure, core.G12Ineligible,
            g11.MeasurementIneligible, ValueError, TypeError, IndexError,
            KeyError, OSError, MemoryError) as exc:
        row["status"] = {
            "authentication": "SOURCE_UNAVAILABLE_OR_UNAUTHENTICATED",
            "metadata": "SOURCE_METADATA_NOT_ELIGIBLE",
            "measurement": "SOURCE_MEASUREMENT_NOT_ELIGIBLE",
        }.get(stage, "SOURCE_EXECUTION_ERROR")
        row["failure_code"] = str(exc)[:160]
        row["failure_type"] = type(exc).__name__
        return row, None


def run_original() -> dict:
    verify_prior_and_manifest()
    all_rows = []
    sess1, sess3 = {}, {}
    for source in SOURCES:
        record, feats = measure_one(source)
        all_rows.append(record)
        if record["status"] == "ELIGIBLE":
            (sess1 if source.session == 1 else sess3)[source.subject] = feats
    if len(all_rows) == 24 and all(row["status"] == "ELIGIBLE" for row in all_rows):
        result = core.evaluate_retest(
            [sess1[s] for s in SUBJECTS], [sess3[s] for s in SUBJECTS]
        )
        result["all_registered_sources_eligible"] = True
    else:
        result = {
            "study": "NEU-01-G12-P01",
            "status": "G12_SOURCE_INCOMPLETE",
            "all_registered_sources_eligible": False,
            "complete_primary_statistic_computed": False,
        }
    result.update({
        "protocol_commit": PROTOCOL_COMMIT,
        "source_revision": PUBLISHER_REVISION,
        "source_records_requested": len(SOURCES),
        "source_records_eligible": sum(row["status"] == "ELIGIBLE" for row in all_rows),
        "first_original_source_rows": all_rows,
        "G11_sources_not_recounted": True,
        "cross_dataset_external_replication": False,
        "original_waveforms_published": False,
        "recovery_after_experimental_perturbation_measured": False,
    })
    return result


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("G12_FIRST_ORIGINAL_ARCHIVE_ALREADY_EXISTS")
    try:
        result = run_original()
    except (SourceFailure, MetadataFailure, core.G12Ineligible,
            g11.MeasurementIneligible, ValueError, TypeError, KeyError,
            IndexError, OSError, MemoryError) as exc:
        result = {
            "study": "NEU-01-G12-P01",
            "status": "G12_SOURCE_INCOMPLETE",
            "source_records_requested": 24,
            "source_records_eligible": 0,
            "preflight_failure": True,
            "failure_type": type(exc).__name__,
            "failure_code": str(exc)[:160],
            "protocol_commit": PROTOCOL_COMMIT,
            "original_waveforms_published": False,
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    if result["status"] == "G12_SOURCE_INCOMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
