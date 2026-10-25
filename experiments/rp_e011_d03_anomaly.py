"""RP-E011-D03: forensic localization of a KNOWN original-source anomaly.

The separate protocol was frozen on main at 2df3d83 BEFORE this module.
This source-only diagnostic never changes the D02 rejected verdict, deletes
rows, or evaluates a forecast.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import shlex

from experiments.rp_e011_jsspp_source import (
    SOURCE_URL,
    SourceBlocked,
    download_exact,
    parse_original,
)

PROTOCOL = "RP-E011-D03"
FROZEN_D02_RESULT = "DATASET_SCHEMA_REJECTED"
FROZEN_D02_AUDIT_SHA256 = (
    "99be405c4e88dfd3646ea1812030eb7927b0a076de808f0257cd55d6e5db11f0"
)
EXPECTED_SOURCE_BYTES = 59_430_886
EXPECTED_SOURCE_SHA256 = (
    "dd48cf7ca369d485b14add5d2baca70a1001c19d9b447688ff7639812673dc7c"
)
EXPECTED_DATA_ROWS = 472_400
EXPECTED_ELIGIBLE_ROWS = 472_399
EXPECTED_QUEUE_COUNT = 13
EXPECTED_WIDTH = 22
INTEGER_PATTERN = re.compile(r"[+-]?[0-9]+\Z")


class InvalidSourceText(Exception):
    """The original text or a standard job number cannot be read."""


class ParserDisagreement(Exception):
    """Independent readers disagree about source records or their widths."""


def read_integer_id(token: str) -> int | None:
    if not INTEGER_PATTERN.fullmatch(token):
        return None
    return int(token, 10)


def inspect_id_rows(raw: bytes) -> dict:
    """Read original physical lines through two separate tokenizers.

    Stored line SHA-256 covers original line bytes WITHOUT a trailing newline
    (CR/LF delimiters are not included). Do not retain private extended fields.
    """
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise InvalidSourceText("Source is not valid UTF-8") from exc

    rows = 0
    nonpositive = []
    seen_ids = set()
    duplicated = 0
    for physical_line, line_bytes in enumerate(raw.splitlines(), 1):
        line = line_bytes.decode("utf-8")
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        rows += 1
        # Direct whitespace path reads ONLY the first word, not shlex output.
        raw_first = stripped.split(maxsplit=1)[0]
        whitespace_id = read_integer_id(raw_first)
        try:
            quoted_fields = shlex.split(stripped, posix=True, comments=False)
        except ValueError as exc:
            raise InvalidSourceText(
                f"Unbalanced SWF extension quoting at physical line {physical_line}"
            ) from exc
        if not quoted_fields:
            raise InvalidSourceText(f"Empty job at line {physical_line}")
        quoted_id = read_integer_id(quoted_fields[0])
        if whitespace_id != quoted_id:
            raise ParserDisagreement(
                f"ID token readers differ at physical line {physical_line}"
            )
        if whitespace_id is None:
            raise InvalidSourceText(
                f"Non-integer SWF job ID at physical line {physical_line}"
            )
        if len(quoted_fields) != EXPECTED_WIDTH:
            raise ParserDisagreement(
                f"Extended field width differs at physical line {physical_line}"
            )
        if whitespace_id in seen_ids:
            duplicated += 1
        seen_ids.add(whitespace_id)
        if whitespace_id <= 0:
            nonpositive.append({
                "physical_line": physical_line,
                "data_record_ordinal": rows,
                "integer_job_id": whitespace_id,
                "original_line_without_newline_sha256": sha256(line_bytes).hexdigest(),
            })
    return {
        "data_rows": rows,
        "nonpositive_job_id_count": len(nonpositive),
        "duplicate_job_id_count": duplicated,
        "nonpositive_job_ids": nonpositive,
        "all_integer_id_readers_agree": True,
    }


def matches_original_d02_profile(ids: dict, parsed: dict) -> bool:
    counts = parsed["counts"]
    return (
        ids["data_rows"] == EXPECTED_DATA_ROWS
        and ids["duplicate_job_id_count"] == 0
        and counts.get("data_rows", 0) == EXPECTED_DATA_ROWS
        and counts.get("valid_numeric_prefix_rows", 0) == EXPECTED_DATA_ROWS
        and counts.get("prefix_oracle_valid_whitespace", 0) == EXPECTED_DATA_ROWS
        and counts.get("prefix_oracle_valid_shlex", 0) == EXPECTED_DATA_ROWS
        and counts.get("standard_eligible_rows", 0) == EXPECTED_ELIGIBLE_ROWS
        and counts.get("eligible_with_documented_extended_queue_name", 0)
        == EXPECTED_ELIGIBLE_ROWS
        and counts.get("invalid_job_id", 0) == 1
        and counts.get("duplicate_job_id", 0) == 0
        and counts.get("prefix_oracle_disagreements", 0) == 0
        and counts.get("quote_parse_failures", 0) == 0
        and counts.get("bad_18_field_swf_prefixes", 0) == 0
        and parsed["parsed_record_widths"] == {
            str(EXPECTED_WIDTH): EXPECTED_DATA_ROWS
        }
        and parsed["independent_standard_prefix_readers_agree"] is True
        and parsed["distinct_documented_extended_queue_names_on_eligible_jobs"]
        == EXPECTED_QUEUE_COUNT
    )


def audit_bytes(raw: bytes, source: dict | None = None) -> dict:
    """Never inspect rows if provider bytes differ from original D02 SHA."""
    digest = sha256(raw).hexdigest()
    info = {
        "observed_bytes": len(raw),
        "observed_sha256": digest,
        "expected_bytes": EXPECTED_SOURCE_BYTES,
        "expected_sha256": EXPECTED_SOURCE_SHA256,
    }
    if source is not None:
        info["provider"] = source

    result = {
        "decision": "SOURCE_SHA_MISMATCH",
        "source_identity": info,
        "diagnostic": None,
        "d02_first_verdict_unchanged": FROZEN_D02_RESULT,
        "predictive_scores_computed": False,
        "physical_law_tested": False,
    }
    if len(raw) != EXPECTED_SOURCE_BYTES or digest != EXPECTED_SOURCE_SHA256:
        return result

    try:
        ids = inspect_id_rows(raw)
        parsed = parse_original(raw)
    except InvalidSourceText as exc:
        result["decision"] = "INVALID_SOURCE_TEXT"
        result["diagnostic"] = {"reason": str(exc)}
        return result
    except (ParserDisagreement, ValueError) as exc:
        result["decision"] = "PARSER_DISAGREEMENT"
        result["diagnostic"] = {"reason": str(exc)}
        return result

    counts = parsed["counts"]
    result["diagnostic"] = {
        **ids,
        "d02_valid_numeric_prefix_rows": counts.get("valid_numeric_prefix_rows", 0),
        "d02_standard_eligible_rows": counts.get("standard_eligible_rows", 0),
        "d02_invalid_job_ids": counts.get("invalid_job_id", 0),
        "d02_duplicate_job_ids": counts.get("duplicate_job_id", 0),
        "d02_extended_queue_count": parsed[
            "distinct_documented_extended_queue_names_on_eligible_jobs"
        ],
        "d02_parsed_widths": parsed["parsed_record_widths"],
    }
    if ids["nonpositive_job_id_count"] != 1:
        result["decision"] = "ANOMALY_NOT_REPRODUCED"
    elif not matches_original_d02_profile(ids, parsed):
        result["decision"] = "PARSER_DISAGREEMENT"
    else:
        result["decision"] = "ANOMALY_LOCALIZED"
    return result


def first_source(output_directory: Path) -> dict:
    """Archive one source-only diagnostic, including BLOCKED outcomes."""
    if output_directory.exists() and any(output_directory.iterdir()):
        raise ValueError("Cannot overwrite the first RP-E011-D03 diagnostic")
    output_directory.mkdir(parents=True, exist_ok=True)
    result = {
        "protocol": PROTOCOL,
        "decision": "SOURCE_ACCESS_BLOCKED",
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "source_commit": os.environ.get("GITHUB_SHA"),
        "execution_environment": platform.platform(),
        "original_provider_url": SOURCE_URL,
        "frozen_d02_audit_sha256": FROZEN_D02_AUDIT_SHA256,
        "d02_first_verdict_unchanged": FROZEN_D02_RESULT,
        "source_identity": None,
        "diagnostic": None,
        "errors": [],
        "predictive_scores_computed": False,
        "physical_law_tested": False,
    }
    try:
        raw, source = download_exact()
        finding = audit_bytes(raw, source)
        result.update(finding)
    except SourceBlocked as exc:
        result["errors"].append({
            "stage": "original-provider-access", "reason": str(exc)[:450]
        })
    except (OSError, ValueError, TypeError) as exc:
        # Do not pretend unexpected execution failures are valid data findings.
        result["decision"] = "PARSER_DISAGREEMENT"
        result["errors"].append({
            "stage": "unexpected-source-audit-failure",
            "reason": f"{type(exc).__name__}: {str(exc)[:450]}",
        })
    finally:
        (output_directory / "RP-E011-D03.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    outcome = first_source(args.output)
    print(json.dumps({
        "protocol": PROTOCOL,
        "decision": outcome["decision"],
        "original_d02_verdict": outcome["d02_first_verdict_unchanged"],
        "anomaly_count": (outcome["diagnostic"] or {}).get(
            "nonpositive_job_id_count"
        ),
        "errors": outcome["errors"],
    }, sort_keys=True))
    if outcome["decision"] != "ANOMALY_LOCALIZED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
