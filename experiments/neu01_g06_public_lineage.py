"""NEU-01-G06-P01: pinned public provenance pointers; NO original EEG reads.

Previously observed G03–G05 values were known when this protocol was frozen.
HEAD is source-object availability metadata, never MD5/EEG content evidence.
"""
from __future__ import annotations

import base64
from hashlib import sha1
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

PROTOCOL_COMMIT = "4dba6178e2d2092ef15cf0f55f5641996a95896c"
UPSTREAM = "OpenNeuroDatasets/ds004148"
UPSTREAM_REV = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
API_ROOT = "https://api.github.com/repos/" + UPSTREAM
S3_ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148/"
OUTPUT = Path("docs/results/NEU-01-G06-P01-first-run/audit.json")
SUBJECTS = ("02", "03", "04")
TASKS = (("eyesclosed", "EC"), ("eyesopen", "EO"))
RAW_BYTES = 36600000
DERIV_BYTES = 73824136
EXPECTED = {
    ("02", "eyesclosed"): ("afc315cd4fbd76f2788a67fe31be9d8d", "2ba3c01f752799634414e2142544fd9b"),
    ("02", "eyesopen"): ("3ca243fb3ab6cabcac5a99b8939abcce", "2e4f087c19643b88e59fc2f526bc12c8"),
    ("03", "eyesclosed"): ("4ca2b5bab215101621ddf023f31ba042", "d300eaa41f478a3f39c28a0d0ceb5198"),
    ("03", "eyesopen"): ("099a4fdb6e0e5fe105f04f4c250bc0a4", "b93b201815edbc5cfe1cd030aa5bbf45"),
    ("04", "eyesclosed"): ("8a7314e14dcaabc117de238ebec6841f", "fc75f8e9015290d22510067d5a8e96bf"),
    ("04", "eyesopen"): ("28079903eac38f9f8670a80f0dc766f1", "d5b765994ba96c189030d5162b151e09"),
}
BLOB_SHA = re.compile(r"^[0-9a-f]{40}$")
ANNEX_NAME = re.compile(r"MD5E-s([0-9]+)--([0-9a-f]{32})[.](eeg|set)(?:/|$)")
EXPECTED_CODE = (
    "derivatives/code/figure6_plotSpectrum.m",
    "derivatives/code/figure7_topo.m",
)


class ProvenanceStop(ValueError):
    """Public metadata unavailable or disagrees with frozen identity."""


class NoRedirects(HTTPRedirectHandler):
    """Do not send HEAD requests to a redirected/unspecified server."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProvenanceStop("HEAD_REDIRECT_BLOCKED")


def get_json(url: str) -> dict:
    if not url.startswith(API_ROOT + "/git/"):
        raise ProvenanceStop("UNREGISTERED_PUBLIC_GITHUB_REQUEST")
    request = Request(url, headers={"User-Agent": "RelationalPersistence-G06-source-audit/1",
                                    "Accept": "application/vnd.github+json"})
    try:
        with urlopen(request, timeout=45) as response:
            body = response.read(6000001)
    except (URLError, HTTPError, TimeoutError, OSError) as exc:
        raise ProvenanceStop("PUBLIC_GIT_API_UNAVAILABLE") from exc
    if len(body) > 6000000:
        raise ProvenanceStop("PUBLIC_GIT_METADATA_SIZE_LIMIT")
    try:
        return json.loads(body)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProvenanceStop("PUBLIC_GIT_JSON_INVALID") from exc


def read_verified_blob(sha: str, *, getter=get_json) -> bytes:
    """Read a tracked small metadata blob, independently checking Git SHA-1."""
    if not BLOB_SHA.fullmatch(sha):
        raise ProvenanceStop("INVALID_GIT_BLOB_SHA")
    source = getter(f"{API_ROOT}/git/blobs/{sha}")
    if source.get("sha") != sha or source.get("encoding") != "base64":
        raise ProvenanceStop("GIT_BLOB_IDENTITY_OR_ENCODING_MISMATCH")
    try:
        content = base64.b64decode(source["content"], validate=False)
    except (ValueError, KeyError) as exc:
        raise ProvenanceStop("INVALID_BLOB_BASE64") from exc
    if len(content) > 10000:
        raise ProvenanceStop("UNEXPECTED_LARGE_METADATA_BLOB")
    calculated = sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()
    if calculated != sha:
        raise ProvenanceStop("BLOB_CONTENT_HASH_MISMATCH")
    return content


def paths(subject: str, task: str, abbrev: str) -> dict:
    if subject not in SUBJECTS or (task, abbrev) not in TASKS:
        raise ProvenanceStop("UNREGISTERED_SOURCE_PAIR")
    prefix = f"sub-{subject}/ses-session1/eeg/sub-{subject}_ses-session1_task-{task}_eeg"
    derived = f"derivatives/preprocessed data/preprocessed_data/sub{subject}_01_{abbrev}.set"
    return {"raw": prefix + ".eeg", "sidecar": prefix + ".json", "derivative": derived}


def _require_entry(index: dict, path: str, mode: str) -> dict:
    entry = index.get(path)
    if (not isinstance(entry, dict) or entry.get("path") != path
            or entry.get("type") != "blob" or entry.get("mode") != mode
            or not BLOB_SHA.fullmatch(str(entry.get("sha", "")))):
        raise ProvenanceStop("SOURCE_TREE_ENTRY_IDENTITY_MISMATCH:" + path)
    return entry


def inspect_tree(tree: dict) -> dict:
    if tree.get("truncated") is not False or not isinstance(tree.get("tree"), list):
        raise ProvenanceStop("INCOMPLETE_UPSTREAM_GIT_TREE")
    index: dict[str, dict] = {}
    for row in tree["tree"]:
        key = row.get("path", "")
        if not isinstance(key, str) or key in index:
            raise ProvenanceStop("DUPLICATE_OR_INVALID_TREE_PATH")
        index[key] = row
    suffix_sets = sorted(p for p in index
                         if p.startswith("derivatives/preprocessed data/preprocessed_data/")
                         and p.endswith(".set"))
    suffix_root = sorted(p for p in index
                         if re.fullmatch(r"sub-[0-9]{2}/ses-session[123]/eeg/.*_eeg[.]eeg", p))
    code_files = sorted(p for p in index if p.startswith("derivatives/code/"))
    if len(suffix_sets) != 900 or len(suffix_root) != 900:
        raise ProvenanceStop("EXPECTED_900_RAW_AND_900_DERIVATIVE_POINTERS_MISSING")
    if code_files != list(EXPECTED_CODE):
        raise ProvenanceStop("UNEXPECTED_PUBLISHED_DERIVATIVES_CODE_INVENTORY")
    return {"index": index, "root_eeg_file_count": len(suffix_root),
            "derivative_set_file_count": len(suffix_sets), "published_derivatives_code": code_files}


def _json_blob(index: dict, path: str, reader) -> dict:
    blob = reader(_require_entry(index, path, "100644")["sha"])
    try:
        return json.loads(blob)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProvenanceStop("INVALID_PUBLIC_JSON:" + path) from exc


def parse_annex(content: bytes, *, kind: str, expected_size: int, expected_md5: str) -> dict:
    try:
        s = content.decode("ascii").strip()
    except UnicodeError as exc:
        raise ProvenanceStop("INVALID_ANNEX_POINTER_ENCODING") from exc
    match = ANNEX_NAME.search(s)
    if (not match or ".." not in s or match.group(3) != kind
            or int(match.group(1)) != expected_size or match.group(2) != expected_md5
            or len(content) > 200):
        raise ProvenanceStop("ANNEX_POINTER_IDENTITY_MISMATCH")
    # A symlink claims expected bytes; it is not those bytes.
    return {"announced_size": expected_size, "announced_md5": expected_md5,
            "identity_verified_at": "git_annex_pointer_only", "body_downloaded": False}


def examine_pair(subject: str, task: str, abbrev: str, index: dict, reader) -> dict:
    p = paths(subject, task, abbrev)
    expected_raw, expected_derived = EXPECTED[(subject, task)]
    raw_entry = _require_entry(index, p["raw"], "120000")
    derivative_entry = _require_entry(index, p["derivative"], "120000")
    desc = _json_blob(index, p["sidecar"], reader)
    required = {"EEGReference": "FCz", "SoftwareFilters": "n/a",
                "EEGChannelCount": 61, "SamplingFrequency": 500}
    if any(desc.get(k) != v for k, v in required.items()):
        raise ProvenanceStop("BIDS_SIDECAR_PROVENANCE_MISMATCH:" + p["sidecar"])
    raw = parse_annex(reader(raw_entry["sha"]), kind="eeg",
                      expected_size=RAW_BYTES, expected_md5=expected_raw)
    derived = parse_annex(reader(derivative_entry["sha"]), kind="set",
                          expected_size=DERIV_BYTES, expected_md5=expected_derived)
    return {
        "participant_id": "sub-" + subject, "task": task, "session": "session1",
        "raw_path": p["raw"], "derivative_path": p["derivative"],
        "bids_raw_label_metadata": {"reference": "FCz", "software_filters": "n/a",
                                    "eeg_channels": 61, "sampling_hz": 500},
        "source_git_pointer": {"blob_sha": raw_entry["sha"], **raw},
        "derivative_git_pointer": {"blob_sha": derivative_entry["sha"], **derived},
        "sample_level_pair_alignment_verified": False,
    }


def inspect_metadata(tree: dict, reader) -> dict:
    inventory = inspect_tree(tree)
    index = inventory["index"]
    desc = _json_blob(index, "dataset_description.json", reader)
    if (desc.get("DatasetType") != "raw"
            or desc.get("DatasetDOI") != "doi:10.18112/openneuro.ds004148.v1.0.0"):
        raise ProvenanceStop("BIDS_DATASET_VERSION_OR_LABEL_MISMATCH")
    readme = reader(_require_entry(index, "derivatives/README", "100644")["sha"])
    if not all(term in readme.lower() for term in
               [b"pre-processed data", b"figure6", b"figure7"]):
        raise ProvenanceStop("DERIVATIVE_README_SCOPE_MISMATCH")
    pairs = [examine_pair(s, task, short, index, reader)
             for s in SUBJECTS for task, short in TASKS]
    if len(pairs) != 6 or len({x["derivative_git_pointer"]["announced_md5"] for x in pairs}) != 6:
        raise ProvenanceStop("SIX_DISTINCT_DERIVATIVE_POINTERS_NOT_ESTABLISHED")
    return {
        "dataset_type_from_json": "raw",
        "dataset_version": "1.0.0",
        "upstream_git_revision": UPSTREAM_REV,
        "root_eeg_file_count": inventory["root_eeg_file_count"],
        "derivative_set_file_count": inventory["derivative_set_file_count"],
        "published_derivatives_code": inventory["published_derivatives_code"],
        "derivative_readme_identifies_preprocessed_data": True,
        "source_pairs": pairs,
        "pipeline_processing_scripts_verifiably_published_in_derivatives_code": False,
        "raw_label_does_not_prove_unprocessed_samples": True,
    }


def public_derivative_head(path: str, *, opener=None) -> dict:
    if not re.fullmatch(
        r"derivatives/preprocessed data/preprocessed_data/sub(?:02|03|04)_01_(?:EC|EO)[.]set", path
    ):
        raise ProvenanceStop("UNREGISTERED_DERIVATIVE_HEAD_PATH")
    url = S3_ROOT + quote(path, safe="/")
    request = Request(url, method="HEAD",
                      headers={"User-Agent": "RelationalPersistence-NEU01-G06-HEAD/1"})
    chosen = opener if opener is not None else build_opener(NoRedirects()).open
    try:
        with chosen(request, timeout=45) as response:
            if response.geturl() != url:
                return {"outcome": "DERIVATIVE_HEAD_NOT_VERIFIED",
                        "reason": "UNREGISTERED_RESPONSE_URL"}
            length = response.headers.get("Content-Length")
    except (HTTPError, URLError, TimeoutError, OSError, ProvenanceStop) as exc:
        return {"outcome": "DERIVATIVE_HEAD_NOT_VERIFIED",
                "reason": type(exc).__name__}
    try:
        n = int(length) if length is not None else None
    except ValueError:
        n = None
    if n is None:
        return {"outcome": "DERIVATIVE_HEAD_NOT_VERIFIED", "reason": "NO_VALID_LENGTH"}
    return {"outcome": ("DERIVATIVE_HEAD_SIZE_MATCH" if n == DERIV_BYTES
                        else "DERIVATIVE_HEAD_SIZE_MISMATCH"),
            "reported_size": n}


def run_metadata() -> dict:
    url = API_ROOT + "/git/trees/" + UPSTREAM_REV + "?recursive=1"
    tree = get_json(url)
    metadata = inspect_metadata(tree, read_verified_blob)
    all_head = []
    for pair in metadata["source_pairs"]:
        result = public_derivative_head(pair["derivative_path"])
        all_head.append({"participant_id": pair["participant_id"],
                         "task": pair["task"], **result})
    matched = all(item["outcome"] == "DERIVATIVE_HEAD_SIZE_MATCH" for item in all_head)
    return {
        "study": "NEU-01-G06-P01",
        "status": "NAMED_SOURCE_DERIVATIVE_POINTER_PAIRS_PRESENT",
        "protocol_commit": PROTOCOL_COMMIT,
        "source_metadata": metadata,
        "derivative_head_results": all_head,
        "derivative_head_decision": (
            "SIX_DERIVATIVES_HEAD_SIZE_MATCHED" if matched
            else "SOME_DERIVATIVE_OBJECTS_UNVERIFIED"),
        "derivative_body_md5_verified": False,
        "numeric_sample_alignment_verified": False,
        "preprocessing_stage_causally_identified": False,
        "new_eeg_values_read": 0,
        "neural_or_thermodynamic_conclusion": False,
    }


def main() -> None:
    try:
        result = run_metadata()
    except (ProvenanceStop, OSError, KeyError, TypeError, ValueError) as exc:
        result = {"study": "NEU-01-G06-P01",
                  "status": "UPSTREAM_METADATA_NOT_ELIGIBLE",
                  "protocol_commit": PROTOCOL_COMMIT,
                  "error_code": str(exc)[:240],
                  "new_eeg_values_read": 0}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    if result["status"] != "NAMED_SOURCE_DERIVATIVE_POINTER_PAIRS_PRESENT":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
