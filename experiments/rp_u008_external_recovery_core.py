"""RP-U008/P01: pre-registered external gateway versus HTTP recovery at source resolution.

Unblinded background: the original dataset author's PUBLIC card describes four
short outages; original numeric raw CSV records must not be inspected until the
source-immutable protocol and adversarial code are committed. No new outage
discovery or physical repair inference is made here.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
import math
from statistics import median
from typing import Any

STUDY = "RP-U008-P01"
SOURCE_COMMIT = "d57ca705bfd2b0340b6476a2d01553d2c967636e"
SOURCE_BLOB_SHA1 = "d3a5a90f1a21125e06f2dbc1047a082f748dac1c"
SOURCE_SIZE = 15_143_900
SOURCE_ROWS = 54_617
EXPECTED_RUN_ID = "desktop-eth_20260920_123407"
EXPECTED_OUTAGES = 4
MIN_DOWN_ROWS = 3
MAX_GAP_SECONDS = 75
PRE_ROWS = 5
POST_ROWS = 10
HTTP_USABLE_LIMIT_MS = 1_000.0
HTTP_LAG_REPETITION_THRESHOLD = 2
REQUIRED = (
    "timestamp_utc", "epoch_s", "run_id", "packets_sent",
    "packets_received", "packet_loss_pct", "gateway_packet_loss_pct",
    "gateway_rtt_avg_ms", "http_status", "http_ms",
    "tcp_connect_median_ms", "dns_resolve_ms"
)


class InvalidSource(ValueError):
    """No valid primary observational result may be reported on bad records."""


def optional_float(value: str, name: str, *, positive: bool = False) -> float | None:
    if value.strip() == "":
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise InvalidSource(f"{name}_NOT_NUMBER") from exc
    if not math.isfinite(number) or (positive and number <= 0):
        raise InvalidSource(f"{name}_NONFINITE_OR_NONPOSITIVE")
    return number


def optional_int(value: str, name: str) -> int | None:
    if value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise InvalidSource(f"{name}_NOT_INTEGER") from exc


def parse_timestamp(value: str) -> datetime:
    try:
        moment = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return moment.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise InvalidSource("INVALID_UTC_TIMESTAMP") from exc


def parse_original(csv_text: str, *, enforce_publisher_census: bool = True) -> list[dict]:
    try:
        reader = csv.DictReader(StringIO(csv_text, newline=""))
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise InvalidSource("MISSING_OR_DUPLICATED_RAW_HEADER")
        if not set(REQUIRED) <= set(reader.fieldnames):
            raise InvalidSource("MISSING_REGISTERED_RAW_COLUMNS")
        records = []
        last_timestamp = None
        for raw in reader:
            if None in raw:
                raise InvalidSource("CSV_ROW_HAS_EXCESS_COLUMNS")
            if any(v is None for v in raw.values()):
                raise InvalidSource("CSV_ROW_IS_TRUNCATED")
            stamp = parse_timestamp(raw["timestamp_utc"])
            if last_timestamp is not None and stamp <= last_timestamp:
                raise InvalidSource("RAW_SOURCE_TIMESTAMP_NOT_STRICTLY_INCREASING")
            last_timestamp = stamp
            if raw["run_id"] != EXPECTED_RUN_ID:
                raise InvalidSource("UNEXPECTED_EXTERNAL_RUN_ID")
            epoch = optional_int(raw["epoch_s"], "epoch_s")
            if epoch is None or epoch != int(stamp.timestamp()):
                raise InvalidSource("EPOCH_AND_UTC_MISMATCH")
            sent = optional_int(raw["packets_sent"], "packets_sent")
            received = optional_int(raw["packets_received"], "packets_received")
            if sent is None or received is None or sent < 0 or received < 0 or received > sent:
                raise InvalidSource("INCONSISTENT_REMOTE_PING_COUNTS")
            loss = optional_float(raw["packet_loss_pct"], "packet_loss_pct")
            gateway_loss = optional_float(
                raw["gateway_packet_loss_pct"], "gateway_packet_loss_pct"
            )
            if any(v is None or not 0 <= v <= 100 for v in (loss, gateway_loss)):
                raise InvalidSource("INVALID_REMOTE_OR_GATEWAY_PACKET_LOSS")
            computed_loss = (100 * (sent - received) / sent) if sent else None
            if computed_loss is not None and abs(loss - computed_loss) > 0.011:
                raise InvalidSource("REPORTED_PACKET_LOSS_CONFLICTS_WITH_COUNTS")
            gateway_rtt = optional_float(raw["gateway_rtt_avg_ms"], "gateway_rtt_avg_ms")
            if gateway_rtt is not None and gateway_rtt < 0:
                raise InvalidSource("NEGATIVE_GATEWAY_RESPONSE_TIME")
            http = optional_float(raw["http_ms"], "http_ms", positive=True)
            status = optional_int(raw["http_status"], "http_status")
            if status is not None and not (100 <= status <= 599):
                raise InvalidSource("INVALID_HTTP_STATUS_CODE")
            if status is not None and http is None:
                raise InvalidSource("HTTP_STATUS_WITHOUT_RESPONSE_LATENCY")
            tcp = optional_float(raw["tcp_connect_median_ms"], "tcp_connect_median_ms")
            dns = optional_float(raw["dns_resolve_ms"], "dns_resolve_ms")
            if tcp is not None and tcp <= 0:
                raise InvalidSource("NONPOSITIVE_TCP_RESPONSE_TIME")
            if dns is not None and dns <= 0:
                raise InvalidSource("NONPOSITIVE_DNS_RESPONSE_TIME")
            records.append({
                "utc": stamp.isoformat().replace("+00:00", "Z"),
                "epoch": epoch, "sent": sent, "received": received,
                "loss_pct": loss, "gateway_loss_pct": gateway_loss,
                "gateway_rtt_ms": gateway_rtt,
                "http_status": status, "http_ms": http,
                "tcp_ms": tcp, "dns_ms": dns,
            })
        if enforce_publisher_census and len(records) != SOURCE_ROWS:
            raise InvalidSource("RAW_PUBLISHER_RECORD_CENSUS_MISMATCH")
        if not records:
            raise InvalidSource("EMPTY_ORIGINAL_TRACE")
        return records
    except (UnicodeError, csv.Error) as exc:
        raise InvalidSource("RAW_CSV_DECODE_OR_PARSE_FAILURE") from exc


def is_down(row: dict) -> bool:
    return (
        row["sent"] == 10 and row["received"] == 0
        and row["loss_pct"] == 100 and row["gateway_loss_pct"] == 100
    )


def consecutive(rows: list[dict], first: int, second: int) -> bool:
    gap = rows[second]["epoch"] - rows[first]["epoch"]
    return 0 < gap <= MAX_GAP_SECONDS


def find_down_runs(rows: list[dict]) -> list[tuple[int, int]]:
    """First episode selector: streaming state machine, no publisher labels."""
    found = []
    start = None
    end = None
    for idx, row in enumerate(rows):
        if is_down(row):
            if start is None:
                start = idx
            elif end is not None and not consecutive(rows, end, idx):
                found.append((start, end))
                start = idx
            end = idx
        elif start is not None:
            found.append((start, end))
            start, end = None, None
    if start is not None:
        found.append((start, end))
    return found


def independent_down_runs(rows: list[dict]) -> list[tuple[int, int]]:
    """Independent index-first scan, unlike the streaming state machine."""
    points = [i for i in range(len(rows)) if is_down(rows[i])]
    if not points:
        return []
    groups = [[points[0]]]
    for index in points[1:]:
        previous = groups[-1][-1]
        if index == previous + 1 and consecutive(rows, previous, index):
            groups[-1].append(index)
        else:
            groups.append([index])
    return [(g[0], g[-1]) for g in groups]


def gateway_up(r: dict) -> bool:
    return (
        r["gateway_loss_pct"] < 100
        and r["gateway_rtt_ms"] is not None
        and math.isfinite(r["gateway_rtt_ms"])
        and r["gateway_rtt_ms"] >= 0
    )


def http_success(r: dict) -> bool:
    return (
        type(r["http_status"]) is int
        and 200 <= r["http_status"] <= 399
        and r["http_ms"] is not None
        and math.isfinite(r["http_ms"])
        and r["http_ms"] > 0
    )


def http_usable(r: dict) -> bool:
    return http_success(r) and r["http_ms"] <= HTTP_USABLE_LIMIT_MS


def first_pair(rows: list[dict], indices: list[int], predicate) -> int | None:
    for left, right in zip(indices, indices[1:]):
        if consecutive(rows, left, right) and predicate(rows[left]) and predicate(rows[right]):
            return right
    return None


def compact_sample(rows: list[dict], ix: int) -> dict:
    r = rows[ix]
    return {
        "utc": r["utc"], "offset_from_last_down_samples": None,
        "gateway_loss_pct": r["gateway_loss_pct"],
        "gateway_icmp_reachable": gateway_up(r),
        "remote_ping_loss_pct": r["loss_pct"],
        "http_status": r["http_status"],
        "http_ms": r["http_ms"],
        "http_success": http_success(r),
        "http_usable_le_1000ms": http_usable(r),
        "tcp_connect_observed": bool(r["tcp_ms"] is not None and r["tcp_ms"] > 0),
        "cached_dns_observed": bool(r["dns_ms"] is not None and r["dns_ms"] > 0),
    }


def event_outcome(rows: list[dict], event: tuple[int, int]) -> dict:
    start, end = event
    previous = list(range(start-PRE_ROWS, start))
    later = list(range(end+1, end+1+POST_ROWS))
    result = {
        "outage_first_utc": rows[start]["utc"],
        "outage_last_utc": rows[end]["utc"],
        "down_sample_count": end - start + 1,
        "last_down_row_index": end,
        "observational_only": True,
        "eligible": False,
        "recovery_gateway_index": None,
        "recovery_http_index": None,
        "recovery_http_quality_index": None,
        "lag_http_bins": None,
        "lag_http_quality_bins": None,
        "lag_http_timestamp_seconds": None,
        "lag_http_quality_timestamp_seconds": None,
    }
    if previous[0] < 0 or later[-1] >= len(rows):
        result["invalid_reason"] = "INSUFFICIENT_PRE_OR_POST_SOURCE_RECORDS"
        return result
    all_indices = previous + list(range(start, end+1)) + later
    if any(not consecutive(rows, a, b) for a, b in zip(all_indices, all_indices[1:])):
        result["invalid_reason"] = "GAP_OVER_75_SECONDS_IN_REQUIRED_WINDOW"
        return result
    if any(is_down(rows[i]) for i in later):
        result["invalid_reason"] = "ANOTHER_DOWN_ROW_IN_POST_WINDOW"
        return result
    result["eligible"] = True
    result["samples_pre"] = [compact_sample(rows, ix) for ix in previous]
    result["samples_post"] = [compact_sample(rows, ix) for ix in later]
    for index, value in enumerate(result["samples_post"], start=1):
        value["offset_from_last_down_samples"] = index
    gateway = first_pair(rows, later, gateway_up)
    http = first_pair(rows, later, http_success)
    usable = first_pair(rows, later, http_usable)
    result["recovery_gateway_index"] = gateway - end if gateway is not None else None
    result["recovery_http_index"] = http - end if http is not None else None
    result["recovery_http_quality_index"] = usable - end if usable is not None else None
    result["gateway_right_censored"] = gateway is None
    result["http_right_censored"] = http is None
    result["http_quality_right_censored"] = usable is None
    if gateway is not None and http is not None:
        result["lag_http_bins"] = http - gateway
        result["lag_http_timestamp_seconds"] = (
            rows[http]["epoch"] - rows[gateway]["epoch"]
        )
    if gateway is not None and usable is not None:
        result["lag_http_quality_bins"] = usable - gateway
        result["lag_http_quality_timestamp_seconds"] = (
            rows[usable]["epoch"] - rows[gateway]["epoch"]
        )
    return result


def evaluate(rows: list[dict], *, require_four: bool = True) -> dict:
    first = find_down_runs(rows)
    second = independent_down_runs(rows)
    if first != second:
        raise InvalidSource("INDEPENDENT_OUTAGE_SELECTION_ORACLES_CONFLICT")
    eligible = [r for r in first if r[1] - r[0] + 1 >= MIN_DOWN_ROWS]
    excluded = [r for r in first if r[1] - r[0] + 1 < MIN_DOWN_ROWS]
    events = [event_outcome(rows, e) for e in eligible]
    exact_four = len(eligible) == EXPECTED_OUTAGES
    complete = (
        exact_four and all(e["eligible"] for e in events)
        and all(e["lag_http_bins"] is not None for e in events)
    )
    repeated = sum(1 for e in events if e["lag_http_bins"] is not None
                   and e["lag_http_bins"] >= 1)
    status = (
        "RP_U008_TWO_OR_MORE_POSITIVE_HTTP_LAGS_OBSERVED" if (
            complete and repeated >= HTTP_LAG_REPETITION_THRESHOLD
        ) else
        "RP_U008_NO_REPEATED_POSITIVE_HTTP_LAG_AT_SOURCE_RESOLUTION" if complete else
        "RP_U008_EXTERNAL_RECOVERY_CENSORED_OR_INCOMPLETE"
    )
    result = {
        "study": STUDY,
        "status": status,
        "raw_record_count": len(rows),
        "publisher_card_outages_previously_known": True,
        "all_candidate_down_runs": len(first),
        "three_plus_row_eligible_events": len(eligible),
        "excluded_short_runs": [
            {"first_utc": rows[a]["utc"], "last_utc": rows[b]["utc"],
             "down_rows": b - a + 1}
            for a,b in excluded
        ],
        "four_original_events_required": exact_four,
        "complete_first_hop_http_recovery_census": complete,
        "gateway_and_http_positive_lag_count": repeated,
        "events": events,
        "no_p_value_or_population_claim": True,
        "no_proven_physical_repair_or_independent_hardware_measurement": True,
        "original_outage_identification_not_claimed": True,
    }
    if require_four and not exact_four:
        result["status"] = "RP_U008_SOURCE_OR_EVENT_CENSUS_INCOMPLETE"
    return result
