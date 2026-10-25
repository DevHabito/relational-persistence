"""RP-E012-D01: byte-pinned official Google Borg v3 schema-only audit.

Predeclared in main a024612 before automated source retrieval, parsing,
tests or scoring. The publicly available documentation and proto NAMES
had been inspected BEFORE preregistration; this is informed schema triage.

NO production trace job/event rows, provider runtime enforcement settings,
empirical queue-wait scores, Lean theorem or physical inference.
"""

from __future__ import annotations

from hashlib import sha1, sha256
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import argparse
import json
import os
import re

PROTOCOL = "RP-E012-D01"
COMMIT = "48b12446464b0422abcc18e0ec5b0b13e2f3a90c"
REPO = "google/cluster-data"
SOURCE_BLOBS = {
    "clusterdata_trace_format_v3.proto": "83101ef12604a6c9ce4a44288791a17869c2caf1",
    "ClusterData2019.md": "22a38cab107ce8dedf18c86c1c2b25607980cf26",
}
MAX_SOURCE_BYTES = 100_000
REQUIRED_FIELDS = {
    "InstanceEvent": (
        "time", "type", "collection_id", "instance_index", "machine_id",
        "resource_request", "priority", "missing_type",
    ),
    "CollectionEvent": (
        "time", "type", "priority", "start_after_collection_ids",
        "missing_type",
    ),
    "MachineEvent": ("time", "machine_id", "type", "capacity"),
    "InstanceUsage": (
        "start_time", "end_time", "average_usage", "maximum_usage",
        "assigned_memory",
    ),
}
REQUIRED_ENUMS = {
    "EventType": (
        "SUBMIT", "SCHEDULE", "EVICT", "FINISH",
        "UPDATE_PENDING", "UPDATE_RUNNING",
    ),
    "MissingType": (
        "SNAPSHOT_BUT_NO_TRANSITION", "NO_SNAPSHOT_OR_TRANSITION",
        "EXISTS_BUT_NO_CREATION",
    ),
}
RUNTIME_CAP_NAMES = (
    "time_limit", "runtime_limit", "walltime", "wall_time",
    "max_runtime", "max_duration", "duration_limit",
    "hard_time_limit", "deadline", "execution_timeout", "runtime_cap",
)


class SchemaFailure(Exception):
    """Stop instead of inferring data or hard-cap evidence from absence."""


class PinnedHostRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        dest = urlsplit(newurl)
        if dest.scheme != "https" or dest.hostname != "raw.githubusercontent.com":
            raise SchemaFailure("Publisher source redirected off the allowed HTTPS host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def source_url(filename: str) -> str:
    if filename not in SOURCE_BLOBS:
        raise SchemaFailure("Unregistered source name")
    return f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{filename}"


def publisher_blob_sha(raw: bytes) -> str:
    return sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def original_source_identity(raw: bytes, filename: str) -> dict:
    return {
        "publisher_repo": REPO,
        "publisher_commit": COMMIT,
        "filename": filename,
        "url": source_url(filename),
        "bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
        "git_blob_sha1": publisher_blob_sha(raw),
        "expected_git_blob_sha1": SOURCE_BLOBS[filename],
    }


def verified_publisher_text(raw: bytes, filename: str) -> str:
    if len(raw) > MAX_SOURCE_BYTES or not raw:
        raise SchemaFailure("Pinned publisher file absent or exceeds size limit")
    actual = publisher_blob_sha(raw)
    if actual != SOURCE_BLOBS[filename]:
        raise SchemaFailure("Pinned publisher blob identity mismatch")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise SchemaFailure("Original publisher text is not strict UTF-8") from exc


def download_original(filename: str) -> bytes:
    """Read exactly the approved original Git commit via HTTPS."""
    opener = build_opener(PinnedHostRedirects())
    address = source_url(filename)
    with opener.open(Request(address, headers={
        "User-Agent": "relational-persistence-RP-E012-D01-original-source"
    }), timeout=35) as response:
        if response.status != 200:
            raise SchemaFailure("Publisher did not return HTTP 200")
        content = response.read(MAX_SOURCE_BYTES + 1)
    if len(content) > MAX_SOURCE_BYTES:
        raise SchemaFailure("Pinned original publisher file exceeded byte limit")
    return content


def _extract_regex_block(content: str, category: str, name: str) -> str:
    """Oracle A: regex identifies declaration, token braces bound the body."""
    pattern = re.compile(r"^\s*" + re.escape(category) +
                         r"\s+" + re.escape(name) + r"\s*\{",
                         re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return ""
    depth, open_index = 1, match.end()
    for position, ch in enumerate(content[open_index:], open_index):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[open_index:position]
    raise SchemaFailure("Unbalanced publisher message/enum braces")


def parse_regex_schema(content: str) -> dict:
    """Oracle A: regex field declarations within exact source blocks."""
    messages = {}
    for name in REQUIRED_FIELDS:
        body = _extract_regex_block(content, "message", name)
        messages[name] = sorted(set(re.findall(
            r"^\s*(?:optional|required|repeated)\s+\w+\s+(\w+)\s*=\s*\d+\s*;",
            body, re.MULTILINE,
        )))
    # Include ALL actual top-level message field names for runtime cap check.
    cap_fields = set()
    for match in re.finditer(r"^\s*message\s+(\w+)\s*\{", content, re.MULTILINE):
        body = _extract_regex_block(content, "message", match.group(1))
        cap_fields.update(re.findall(
            r"^\s*(?:optional|required|repeated)\s+\w+\s+(\w+)\s*=\s*\d+\s*;",
            body, re.MULTILINE,
        ))
    enums = {}
    for name in REQUIRED_ENUMS:
        body = _extract_regex_block(content, "enum", name)
        enums[name] = sorted(set(re.findall(
            r"^\s*(\w+)\s*=\s*\d+\s*;", body, re.MULTILINE
        )))
    return {"messages": messages, "enums": enums,
            "all_publisher_field_names": sorted(cap_fields)}


def parse_line_schema(content: str) -> dict:
    """Oracle B: independent linewise brace depth and token extraction.

    Top-level declarations are distinguished from nested enums.
    Results are deliberately schema-name-only, not a general protobuf parser.
    """
    messages: dict[str, set[str]] = {}
    enums: dict[str, set[str]] = {}
    all_fields: set[str] = set()
    depth = 0
    current_kind = current_name = None
    for original_line in content.splitlines():
        line = original_line.split("//", 1)[0].strip()
        if not line:
            continue
        tokens = line.replace("{", " { ").replace("}", " } ").split()
        if depth == 0 and len(tokens) >= 3 and tokens[0] in ("message", "enum") and tokens[2] == "{":
            current_kind, current_name = tokens[0], tokens[1]
            if current_kind == "message":
                messages.setdefault(current_name, set())
            else:
                enums.setdefault(current_name, set())
        elif depth == 1 and current_kind == "message":
            if "=" in line and ";" in line:
                header = line.split("=", 1)[0].split()
                if len(header) == 3 and header[0] in ("optional", "required", "repeated"):
                    field_name = header[-1]
                    messages[current_name].add(field_name)
                    all_fields.add(field_name)
        elif depth == 1 and current_kind == "enum":
            if "=" in line and ";" in line:
                header = line.split("=", 1)[0].split()
                if len(header) == 1:
                    enums[current_name].add(header[0])
        depth += line.count("{") - line.count("}")
        if depth < 0:
            raise SchemaFailure("Independent line oracle found unmatched brace")
        if depth == 0:
            current_kind = current_name = None
    if depth:
        raise SchemaFailure("Independent line oracle found unterminated declaration")
    return {
        "messages": {k: sorted(messages.get(k, set())) for k in REQUIRED_FIELDS},
        "enums": {k: sorted(enums.get(k, set())) for k in REQUIRED_ENUMS},
        "all_publisher_field_names": sorted(all_fields),
    }


def event_available_before(event_time: int, origin_time: int,
                           *, reconstructed: bool = False) -> bool:
    """Conservative gate: reconstructed missing events are not historical truth."""
    if reconstructed:
        return False
    return event_time < origin_time


def usage_window_available_before(start_time: int, end_time: int,
                                  origin_time: int) -> bool:
    """A whole-window aggregate is causally available only AFTER window end."""
    if end_time <= start_time:
        return False
    return end_time < origin_time


def audit_verified_sources(proto_raw: bytes, readme_raw: bytes) -> dict:
    source = {
        "proto": original_source_identity(proto_raw, "clusterdata_trace_format_v3.proto"),
        "readme": original_source_identity(readme_raw, "ClusterData2019.md"),
    }
    report = {
        "protocol": PROTOCOL,
        "decision": "SCHEMA_SOURCE_IDENTITY_MISMATCH",
        "source_identity": source,
        "two_independent_parsers_agree": None,
        "required_event_metadata": None,
        "runtime_cap_evidence": None,
        "causal_observation_rules": {
            "event_timestamp": "event_time < origin; reconstructed missing events excluded",
            "usage_window": "end_time < origin; cannot use future-ended aggregate",
            "schedule_event": "placement event, not guaranteed actual process start",
        },
        "raw_production_rows_examined": 0,
        "predictions_computed": False,
        "real_runtime_cap_enforcement_verified": False,
        "new_lean_theorem_claimed": False,
        "physical_law_claimed": False,
        "errors": [],
    }
    try:
        proto = verified_publisher_text(proto_raw, "clusterdata_trace_format_v3.proto")
        readme = verified_publisher_text(readme_raw, "ClusterData2019.md")
    except SchemaFailure as exc:
        report["errors"] = [{"stage": "source-identity", "reason": str(exc)}]
        return report
    if "clusterdata-2019" not in readme or "Borg" not in readme:
        report["decision"] = "SCHEMA_PARSER_DISAGREEMENT"
        report["errors"] = [{"stage": "source-description", "reason": "Official README semantics mismatch"}]
        return report
    try:
        a = parse_regex_schema(proto)
        b = parse_line_schema(proto)
    except SchemaFailure as exc:
        report["decision"] = "SCHEMA_PARSER_DISAGREEMENT"
        report["errors"] = [{"stage": "independent-schema-parse", "reason": str(exc)}]
        return report
    same = a == b
    report["two_independent_parsers_agree"] = same
    if not same:
        report["decision"] = "SCHEMA_PARSER_DISAGREEMENT"
        report["errors"] = [{"stage": "field-or-enum-oracle", "reason": "Exact source field sets disagree"}]
        return report
    missing = {
        "messages": {name: sorted(set(required) - set(a["messages"][name]))
                     for name, required in REQUIRED_FIELDS.items()},
        "enums": {name: sorted(set(required) - set(a["enums"][name]))
                  for name, required in REQUIRED_ENUMS.items()},
    }
    complete = all(not v for types in missing.values() for v in types.values())
    present_caps = sorted(set(RUNTIME_CAP_NAMES) & set(a["all_publisher_field_names"]))
    report["required_event_metadata"] = {
        "schema_fields": {name: sorted(set(a["messages"][name]) & set(fields))
                          for name, fields in REQUIRED_FIELDS.items()},
        "event_enums": {name: sorted(set(a["enums"][name]) & set(fields))
                        for name, fields in REQUIRED_ENUMS.items()},
        "missing_required": missing,
        "all_prespecified_event_gates_pass": complete,
    }
    report["runtime_cap_evidence"] = {
        "predeclared_runtime_cap_field_names": list(RUNTIME_CAP_NAMES),
        "publisher_exact_matching_fields": present_caps,
        "explicit_hard_runtime_cap_field_in_pinned_proto": bool(present_caps),
        "effective_enforcement_verified_from_schema": False,
        "assigned_memory_is_not_wallclock_runtime_cap": True,
        "no_field_does_not_imply_no_internal_enforcement": True,
    }
    if not complete:
        report["decision"] = "SCHEMA_REQUIRED_EVENT_METADATA_MISSING"
    elif present_caps:
        report["decision"] = "SCHEMA_EVENT_METADATA_PRESENT_ENFORCEMENT_UNKNOWN"
    else:
        report["decision"] = "SCHEMA_EVENT_METADATA_PRESENT_RUNTIME_CAP_UNVERIFIED"
    return report


def first_run(output: Path) -> dict:
    if output.exists():
        raise ValueError("Cannot overwrite the original RP-E012-D01 first-run report")
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "protocol": PROTOCOL,
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "original_code_commit": os.environ.get("GITHUB_SHA"),
        "decision": "SCHEMA_SOURCE_ACCESS_BLOCKED",
        "raw_production_rows_examined": 0,
        "predictions_computed": False,
        "errors": [],
    }
    try:
        proto = download_original("clusterdata_trace_format_v3.proto")
        readme = download_original("ClusterData2019.md")
        report.update(audit_verified_sources(proto, readme))
    except Exception as exc:
        # A blocked network is not evidence of any missing provider field.
        report["decision"] = "SCHEMA_SOURCE_ACCESS_BLOCKED"
        report["errors"] = [{"stage": "official-https-publisher", "reason":
                             f"{type(exc).__name__}: {str(exc)[:240]}"}]
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = first_run(args.output)
    print(json.dumps({
        "protocol": PROTOCOL, "decision": report["decision"],
        "all_event_schema_gates_pass": (
            (report.get("required_event_metadata") or {}).get("all_prespecified_event_gates_pass")),
        "runtime_cap_field": (
            (report.get("runtime_cap_evidence") or {}).get(
                "explicit_hard_runtime_cap_field_in_pinned_proto")),
    }))
    if report["decision"] in (
        "SCHEMA_SOURCE_ACCESS_BLOCKED", "SCHEMA_SOURCE_IDENTITY_MISMATCH",
        "SCHEMA_PARSER_DISAGREEMENT",
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
