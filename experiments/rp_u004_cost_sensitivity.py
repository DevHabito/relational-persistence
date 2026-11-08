"""Retrospective RP-U004 additive lookup-price accounting (not empirical cost).

Archive data remain immutable. The policy outcome was already known.
No computation here estimates real decision duration, energy, or repair cost.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path


ARCHIVE_DIR = Path("docs/results/RP-U004-P01-first-run")


@dataclass(frozen=True)
class Contrast:
    greedy_ticks: int
    lookahead_ticks: int
    greedy_lookups: int
    lookahead_lookups: int

    def lookup_delta(self) -> int:
        return self.lookahead_lookups - self.greedy_lookups

    def tick_delta(self) -> int:
        return self.lookahead_ticks - self.greedy_ticks

    def net_difference(self, lookup_price: Fraction) -> Fraction:
        """Lookahead minus greedy, in synthetic successful tick equivalents."""
        return Fraction(self.tick_delta()) - lookup_price * self.lookup_delta()

    def break_even_price(self) -> Fraction:
        """Defined only when the strategies have distinct lookup totals."""
        extra = self.lookup_delta()
        if extra == 0:
            raise ValueError("No finite break-even price when lookup counts tie")
        return Fraction(self.tick_delta(), extra)


def read_original_contrasts(archive_dir: Path = ARCHIVE_DIR) -> dict[str, Contrast]:
    """Read published first-run metrics only after a byte-level hash check."""
    index = json.loads((archive_dir / "archive-index.json").read_text(encoding="utf-8"))
    original_bytes = (archive_dir / "audit.json").read_bytes()
    if sha256(original_bytes).hexdigest() != index["original_audit_sha256"]:
        raise ValueError("Original RP-U004 audit JSON does not match its archive SHA-256")

    source = json.loads(original_bytes)
    if (source["protocol"] != index["protocol"] or
            source["verdict"] != index["first_verdict"] or
            str(source["original_run_id"]) != index["first_run_id"] or
            source["errors"] or source["physical_data_rows"] != 0 or
            len(source["cases"]) != 2850):
        raise ValueError("Original RP-U004 manifest or scope invariants disagree")

    totals = source["aggregates"]
    lookups = totals["policy_lookup_counts"]
    contrasts = {}
    for metric in ("F1", "F2"):
        greedy = f"GREEDY_{metric}"
        lookahead = f"LOOKAHEAD2_{metric}"
        ticks = totals[f"{metric}_uptime"]
        observed = (ticks[greedy], ticks[lookahead], lookups[greedy], lookups[lookahead])
        if not all(isinstance(value, int) and value >= 0 for value in observed):
            raise ValueError(f"Invalid numeric RP-U004 {metric} source count")
        contrasts[metric] = Contrast(*observed)
    return contrasts


def main() -> None:
    data = read_original_contrasts()
    output = {
        metric: {
            "original_greedy_ticks": case.greedy_ticks,
            "original_lookahead_ticks": case.lookahead_ticks,
            "original_greedy_lookups": case.greedy_lookups,
            "original_lookahead_lookups": case.lookahead_lookups,
            "tick_delta": case.tick_delta(),
            "lookup_delta": case.lookup_delta(),
            "rational_break_even_price": str(case.break_even_price()),
            "interpretation": "retrospective synthetic additive accounting only",
        }
        for metric, case in data.items()
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
