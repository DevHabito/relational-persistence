"""RP-U009-P01: source-free MetroPT physical pressure/maintenance audit.

No MetroPT source values or maintenance outcomes are accessed at import.
Eligibility, two selected publisher dates, negative decision and all windows
were registered before fetching original UCI data.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
from io import TextIOBase
import math
from statistics import median

PROTOCOL = "RP-U009-P01"
PROTOCOL_ONLY_COMMIT = "2c36bd9b84ac664798e544f24b3617c1f7b5a258"
OFFICIAL_UCI_URL = (
    "https://archive.ics.uci.edu/static/public/791/"
    "metropt%2B3%2Bdataset.zip"
)
ORIGINAL_EXPECTED_ROWS = 1_516_948
ORIGINAL_CSV_BASENAME = "MetroPT3(AirCompressor).csv"
CSV_MAX_BYTES = 350_000_000
ZIP_MAX_BYTES = 400_000_000
MOTOR_ACTIVE_A = 5.0
LOW_PRESSURE_BAR = 7.0
MIN_WINDOW_ROWS = 30
MIN_WINDOW_HOUR_BUCKETS = 6
PRE_START_HOURS = 24
PRE_END_HOURS = 2
POST_START_HOURS = 2
POST_END_HOURS = 24
EXPECTED_EVENTS = (
    ("2020-06-08 16:00:00", "2020-06-07 14:30:00"),
    ("2020-07-16 00:00:00", "2020-07-15 19:00:00"),
)
SOURCE_COLUMNS = ("timestamp", "Reservoirs", "Motor_current", "LPS")
NON_ELIGIBLE_PUBLIC_REPORTS = (
    "2020-04-18: no unambiguously paired post-failure maintenance timestamp",
    "2020-05-29: source row associates a post-May failure with 30Apr maintenance",
)


class InvalidEvidence(ValueError):
    pass


def date_from_source(text: str) -> datetime:
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError) as exc:
        raise InvalidEvidence("SOURCE_TIMESTAMP_UNPARSEABLE") from exc


def fixed_windows() -> tuple[dict, ...]:
    windows = []
    for index, (maintenance_text, failure_end_text) in enumerate(
        EXPECTED_EVENTS, start=1
    ):
        at = date_from_source(maintenance_text)
        fault_end = date_from_source(failure_end_text)
        if at <= fault_end:
            raise InvalidEvidence("REPORTED_MAINTENANCE_PRECEDES_FAILURE_END")
        for side, start, stop in (
            ("before", at-timedelta(hours=PRE_START_HOURS),
             at-timedelta(hours=PRE_END_HOURS)),
            ("after", at+timedelta(hours=POST_START_HOURS),
             at+timedelta(hours=POST_END_HOURS)),
        ):
            windows.append({
                "event_number": index, "maintenance_clock_label": maintenance_text,
                "side": side, "begin_clock": start, "end_clock": stop,
                "source_rows": [],
            })
    return tuple(windows)


def read_finite_nonnegative(text: str, column: str) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise InvalidEvidence(f"{column}_MISSING_OR_NOT_NUMERIC") from exc
    if not math.isfinite(value) or value < 0:
        raise InvalidEvidence(f"{column}_INVALID_NONFINITE_OR_NEGATIVE")
    return value


def safe_percentile(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values:
        raise InvalidEvidence("MISSING_SAMPLING_INTERVALS")
    point = (len(sorted_values)-1)*quantile
    lo = math.floor(point)
    high = math.ceil(point)
    return float(
        sorted_values[lo] +
        (sorted_values[high]-sorted_values[lo])*(point-lo)
    )


def summarize_window(window: dict) -> dict:
    rows = window["source_rows"]
    if len(rows) < MIN_WINDOW_ROWS:
        raise InvalidEvidence("MAINTENANCE_WINDOW_HAS_FEWER_THAN_30_OBSERVATIONS")
    hours = {r["timestamp"].replace(minute=0, second=0)
             for r in rows}
    if len(hours) < MIN_WINDOW_HOUR_BUCKETS:
        raise InvalidEvidence("MAINTENANCE_WINDOW_HAS_TOO_FEW_HOUR_BUCKETS")
    low = sum(r["reservoir_bar"] < LOW_PRESSURE_BAR for r in rows)
    active = sum(r["motor_current_a"] > MOTOR_ACTIVE_A for r in rows)
    switch = sum(r["lps"] == 1 for r in rows)
    mismatch = sum((r["lps"] == 1) != (
        r["reservoir_bar"] < LOW_PRESSURE_BAR) for r in rows)
    n = len(rows)
    return {
        "event_number": window["event_number"],
        "maintenance_clock_label": window["maintenance_clock_label"],
        "window_side": window["side"],
        "window_start_clock_label": window["begin_clock"].strftime("%Y-%m-%d %H:%M:%S"),
        "window_end_exclusive_clock_label": window["end_clock"].strftime("%Y-%m-%d %H:%M:%S"),
        "original_observation_count": n,
        "represented_distinct_hour_buckets": len(hours),
        "median_reservoir_pressure_bar": float(median(
            r["reservoir_bar"] for r in rows
        )),
        "count_reservoir_pressure_below_7bar": low,
        "fraction_reservoir_pressure_below_7bar": low/n,
        "median_motor_current_a": float(median(
            r["motor_current_a"] for r in rows
        )),
        "count_motor_current_over_5a": active,
        "fraction_motor_current_over_5a": active/n,
        "count_lps_active": switch,
        "fraction_lps_active": switch/n,
        "lps_vs_reservoir_below_7bar_disagreements": mismatch,
        "physical_pressure_measured_not_air_delivery": True,
    }


def original_csv_audit(stream: TextIOBase, *,
                       expected_census: int | None = ORIGINAL_EXPECTED_ROWS) -> dict:
    reader = csv.DictReader(stream)
    if (reader.fieldnames is None or
            len(set(reader.fieldnames)) != len(reader.fieldnames) or
            not set(SOURCE_COLUMNS) <= set(reader.fieldnames)):
        raise InvalidEvidence("ORIGINAL_COMPRESSOR_SOURCE_COLUMNS_NOT_FOUND")
    windows = fixed_windows()
    count = 0
    previous = None
    first_stamp = None
    last_stamp = None
    gaps = []
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise InvalidEvidence("MALFORMED_ORIGINAL_COMPRESSOR_CSV_ROW")
        t = date_from_source(row["timestamp"])
        if previous is not None:
            seconds = (t-previous).total_seconds()
            if seconds <= 0:
                raise InvalidEvidence("ORIGINAL_COMPRESSOR_CLOCK_NOT_STRICTLY_INCREASING")
            gaps.append(seconds)
        if first_stamp is None:
            first_stamp = t
        previous = t
        last_stamp = t
        count += 1
        for window in windows:
            if window["begin_clock"] <= t < window["end_clock"]:
                pressure = read_finite_nonnegative(
                    row["Reservoirs"], "RESERVOIRS_PRESSURE")
                motor = read_finite_nonnegative(
                    row["Motor_current"], "MOTOR_CURRENT")
                state_value = row["LPS"]
                if state_value not in ("0", "1"):
                    raise InvalidEvidence("LOW_PRESSURE_SWITCH_MUST_BE_BINARY")
                window["source_rows"].append({
                    "timestamp":t,
                    "reservoir_bar":pressure,
                    "motor_current_a":motor,
                    "lps":int(state_value),
                })
    if expected_census is not None and count != expected_census:
        raise InvalidEvidence("UCI_ORIGINAL_CSV_ROW_COUNT_CHANGED")
    if count < 2 or last_stamp is None or first_stamp is None:
        raise InvalidEvidence("EMPTY_OR_TOO_SHORT_PHYSICAL_SOURCE")
    gaps.sort()
    snapshots = [summarize_window(w) for w in windows]
    return {
        "study":PROTOCOL,
        "verified_raw_records":count,
        "first_source_clock_label":first_stamp.strftime("%Y-%m-%d %H:%M:%S"),
        "last_source_clock_label":last_stamp.strftime("%Y-%m-%d %H:%M:%S"),
        "reported_clock_utc_offset_unknown":True,
        "sampling_interval_min_seconds":gaps[0],
        "sampling_interval_median_seconds":float(median(gaps)),
        "sampling_interval_p95_seconds":safe_percentile(gaps,.95),
        "sampling_interval_max_seconds":gaps[-1],
        "duplicate_or_nonmonotonic_timestamp_count":0,
        "all_four_fixed_windows":snapshots,
        "source_maintenance_reports_are_not_independent_verified_repair_completion":True,
        "excluded_source_reports_with_inconsistent_or_missing_repair_clock":
            list(NON_ELIGIBLE_PUBLIC_REPORTS),
    }


def evaluate_summary(source: dict) -> dict:
    windows = source.get("all_four_fixed_windows")
    if not isinstance(windows,list) or len(windows)!=4:
        raise InvalidEvidence("INCOMPLETE_PREDECLARED_EVENT_WINDOW_CENSUS")
    grouped = []
    for number in (1,2):
        before, after = windows[2*(number-1):2*number]
        if ((before.get("event_number"),before.get("window_side"))!=(number,"before")
                or (after.get("event_number"),after.get("window_side"))!=(number,"after")):
            raise InvalidEvidence("PREPOST_WINDOW_CLOCK_OR_ORDER_CHANGED")
        if (before["original_observation_count"] < MIN_WINDOW_ROWS
                or after["original_observation_count"] < MIN_WINDOW_ROWS):
            raise InvalidEvidence("ORIGINAL_WINDOW_OBSERVATION_CENSUS_FAILED")
        delta=(
            before["fraction_reservoir_pressure_below_7bar"]
            - after["fraction_reservoir_pressure_below_7bar"]
        )
        grouped.append({
            "event_number":number,
            "reported_maintenance_clock_label":before["maintenance_clock_label"],
            "pre_low_pressure_fraction":
                before["fraction_reservoir_pressure_below_7bar"],
            "post_low_pressure_fraction":
                after["fraction_reservoir_pressure_below_7bar"],
            "delta_low_pressure_pre_minus_post":delta,
            "pressure_occupancy_strictly_improved":bool(delta>0),
            "pre_hour_buckets":before["represented_distinct_hour_buckets"],
            "post_hour_buckets":after["represented_distinct_hour_buckets"],
        })
    improved=sum(x["pressure_occupancy_strictly_improved"] for x in grouped)
    status=(
        "RP_U009_BOTH_REPAIRS_SHOW_LOWER_LOW_PRESSURE_OCCUPANCY"
        if improved==2 else
        "RP_U009_NO_TWO_EVENT_CONCORDANT_PRESSURE_IMPROVEMENT"
    )
    return {
        "status":status,
        "event_pairs":grouped,
        "improved_strict_event_count_of_two":improved,
        "total_reported_maintenance_anchors":2,
        "physical_pressure_observation_only_not_direct_air_delivery":True,
        "repair_events_from_publisher_report_not_independently_timed":True,
        "source_reported_timezone_unverified":True,
        "nonrandom_chronology_eligible_events_not_population_sample":True,
        "new_physical_biological_or_relational_law_proven":False,
        "no_causal_repair_claim":True,
    }
