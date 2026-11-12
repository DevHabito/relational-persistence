"""Retrospective bounds from immutable G03 EEG aggregates, not source replay."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path

REPORT = Path("docs/results/NEU-01-G03-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G03-first-run/archive-index.json")
SHA = "b142e6b0b0d03e1bd6167fba1a3d265bf3d5efd485e8389474f882955bf8195c"
SUBJECTS = ("sub-02", "sub-03", "sub-04")
VALUES, PAIRS = 9_150_000, 9_149_939


def zero_zero_upper(z: int) -> int:
    """Across finite channels with Z zeros and R>=1 zero runs: E00=Z-R."""
    if type(z) is not int or z < 0:
        raise ValueError("Invalid zero count")
    return max(0, z - 1)


def nonzero_equal_lower(e: int, z: int) -> int:
    """Guaranteed nonzero adjacent equality count from E and Z aggregates."""
    if type(e) is not int or e < 0:
        raise ValueError("Invalid equal-pair count")
    return max(0, e - zero_zero_upper(z))


def audit(report_bytes: bytes, index_bytes: bytes) -> dict:
    if len(report_bytes) != 10117 or sha256(report_bytes).hexdigest() != SHA:
        raise ValueError("Immutable original report checksum mismatch")
    index = json.loads(index_bytes)
    if (index["original_aggregate_json"]["sha256"] != SHA
            or index["original_aggregate_json"]["byte_length"] != 10117
            or index["original_hosted_run"]["run_id"] != 42657980659):
        raise ValueError("Original archive provenance mismatch")
    record = json.loads(report_bytes)
    if (record["study"] != "NEU-01-G03"
            or record["source_version"] != "ds004148/1.0.0"
            or record["participants"] != list(SUBJECTS)
            or set(record["recordings"]) != set(SUBJECTS)
            or record["observed_original_values"] != 6 * VALUES
            or record["observed_original_adjacencies"] != 6 * PAIRS
            or record["lzc_computed"] is not False
            or record["clinical_or_thermodynamic_conclusion"] is not False):
        raise ValueError("Original source scope mismatch")
    rows = {}
    for subject in SUBJECTS:
        tasks = record["recordings"][subject]
        c, o = (tasks[t]["native_census"] for t in ("eyesclosed", "eyesopen"))
        for task, counts in (("eyesclosed", c), ("eyesopen", o)):
            if (counts["total_native_values"] != VALUES
                    or counts["within_channel_possible_adjacencies"] != PAIRS
                    or counts["finite"] != VALUES
                    or any(counts[k] != 0 for k in ("nan", "pos_inf", "neg_inf"))
                    or not 0 <= counts["exact_zero_values"] <= VALUES
                    or not 0 <= counts["within_channel_equal_adjacent"] <= PAIRS
                    or tasks[task]["source_unit_declarations"]["header_calibration_complete"] is not False):
                raise ValueError("Invalid original native count or unit claim")
        if (o["exact_zero_values"] != 0 or
                record["pair_differences"][subject]["paired_equal_difference_numerator"]
                != c["within_channel_equal_adjacent"] - o["within_channel_equal_adjacent"]):
            raise ValueError("Invalid original paired summary")
        lower = nonzero_equal_lower(c["within_channel_equal_adjacent"], c["exact_zero_values"])
        open_exact = o["within_channel_equal_adjacent"]
        rows[subject] = {
            "closed_equal_pairs": c["within_channel_equal_adjacent"],
            "closed_zeros": c["exact_zero_values"],
            "closed_zero_zero_pairs_upper": zero_zero_upper(c["exact_zero_values"]),
            "closed_nonzero_equal_pairs_lower": lower,
            "open_nonzero_equal_pairs_exact": open_exact,
            "closed_minus_open_nonzero_equal_pairs_lower": lower - open_exact,
        }
    return {
        "study": "NEU-01-G03-D01",
        "decision": "RETROSPECTIVE_DETERMINISTIC_BOUND_NOT_NEW_SOURCE_EXPERIMENT",
        "original_sha256": SHA,
        "by_subject": rows,
        "closed_nonzero_equal_pairs_lower_total":
            sum(x["closed_nonzero_equal_pairs_lower"] for x in rows.values()),
        "independent_original_eeg_recount": False,
        "neural_mechanism_inferred": False,
    }


def main() -> None:
    print(json.dumps(audit(REPORT.read_bytes(), INDEX.read_bytes()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
