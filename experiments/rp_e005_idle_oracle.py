"""A separately implemented sampled-idle witness from archived status rows.

This implementation intentionally does not import or call P02's
replay_monitor. It independently groups consecutive idle observations
and checks the dwell interval with integer timestamps. Same original
status observations: this does NOT establish continuous-time idleness
between probes or independent hardware instrumentation.
"""

from __future__ import annotations

from itertools import groupby

DWELL_NS = 500_000_000
MAX_GAP_NS = 150_000_000


def replay_idle_groups(
    records: list[dict], intervention_end_ns: int,
    *, dwell_ns: int = DWELL_NS, gap_limit_ns: int = MAX_GAP_NS,
) -> dict:
    if type(intervention_end_ns) is not int:
        raise ValueError("The intervention end marker must be integral")
    if type(dwell_ns) is not int or dwell_ns <= 0:
        raise ValueError("Invalid sustained recovery interval")
    if type(gap_limit_ns) is not int or gap_limit_ns <= 0:
        raise ValueError("Invalid sampling gap threshold")
    if not records:
        raise ValueError("No timestamped observations")

    previous_time: int | None = None
    previous_server_time: int | None = None
    previous_completed: int | None = None
    after: list[dict] = []
    maximum_gap = 0
    for sample in records:
        values = (
            sample["observed_ns"], sample["server_snapshot_ns"],
            sample["queued"], sample["active"], sample["completed"],
        )
        if any(type(value) is not int for value in values):
            raise ValueError("Invalid timestamp or count")
        observed, service_time, queued, active, completed = values
        if (service_time > observed or queued < 0 or active < 0
                or completed < 0):
            raise ValueError("Invalid sampled status")
        if previous_time is not None:
            if observed <= previous_time:
                raise ValueError("Backwards or duplicate sample")
            if observed >= intervention_end_ns:
                gap = observed - previous_time
                if gap > gap_limit_ns:
                    raise ValueError("Missing sample interval")
                maximum_gap = max(maximum_gap, gap)
        if previous_server_time is not None and service_time <= previous_server_time:
            raise ValueError("Nonmonotonic service clock")
        if previous_completed is not None and completed < previous_completed:
            raise ValueError("Regressing completion counter")
        previous_time, previous_server_time, previous_completed = (
            observed, service_time, completed,
        )
        if observed >= intervention_end_ns:
            after.append(sample)

    if not after:
        raise ValueError("Missing postintervention samples")

    recovered = None
    confirmed = None
    def idle(row: dict) -> bool:
        return row["queued"] == row["active"] == 0

    # Grouping is intentionally different from P02's streaming
    # first_idle/confirm state machine.
    groups = [
        (status, list(group))
        for status, group in groupby(after, key=idle)
    ]
    for index, (status, group) in enumerate(groups):
        if not status:
            continue
        first_time = group[0]["observed_ns"]
        eligible = [
            row["observed_ns"] for row in group
            if row["observed_ns"] - first_time >= dwell_ns
        ]
        if not eligible:
            continue
        if any(not future_status for future_status, _ in groups[index + 1:]):
            raise ValueError("Busy sample after confirmed recovery")
        recovered = first_time
        confirmed = eligible[0]
        break

    return {
        "recovered_at_ns": recovered,
        "confirmed_at_ns": confirmed,
        "sample_count": len(records),
        "after_end_samples": len(after),
        "maximum_post_end_gap_ns": maximum_gap,
    }
