
"""
Reusable metrics for experimental network monitoring.

Supported datasets:
- ICMP V2
- ONOS link monitoring

This module calculates descriptive metrics from collected records.
It does not modify source CSV files.
"""

from collections import Counter


def _to_float(value):
    """Convert a value to float, returning None when unavailable."""
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_icmp_metrics(dataset):
    """
    Calculate metrics from an ICMP V2 dataset.

    The function distinguishes ICMP replies from monitoring events.
    It does not infer transmitted packets from reply counts.
    """

    if dataset.get("format") != "icmp_v2":
        raise ValueError("Dataset must have format 'icmp_v2'.")

    rows = dataset["rows"]

    events = Counter(row["event"] for row in rows)
    phases = Counter(row["phase"] for row in rows)

    replies = [
        row for row in rows
        if row["event"] == "icmp_reply"
    ]

    no_answers = [
        row for row in rows
        if row["event"] == "icmp_no_answer"
    ]

    def phase_replies(phase):
        return [
            row for row in replies
            if row["phase"] == phase
        ]

    def reply_interval(phase):
        phase_rows = phase_replies(phase)

        times = [
            _to_float(row["monotonic_seconds"])
            for row in phase_rows
        ]

        times = sorted(t for t in times if t is not None)

        if len(times) < 2:
            return None

        intervals = [
            times[i] - times[i - 1]
            for i in range(1, len(times))
        ]

        return {
            "mean_seconds": sum(intervals) / len(intervals),
            "min_seconds": min(intervals),
            "max_seconds": max(intervals),
            "sample_count": len(intervals),
        }

    baseline_replies = phase_replies("baseline")
    post_failure_replies = phase_replies("post_failure")

    failure_started = next(
        (
            _to_float(row["monotonic_seconds"])
            for row in rows
            if row["event"] == "link_failure_injection_started"
        ),
        None,
    )

    failure_completed = next(
        (
            _to_float(row["monotonic_seconds"])
            for row in rows
            if row["event"] == "link_failure_injection_completed"
        ),
        None,
    )

    last_baseline_reply = max(
        (
            _to_float(row["monotonic_seconds"])
            for row in baseline_replies
            if _to_float(row["monotonic_seconds"]) is not None
        ),
        default=None,
    )

    first_post_failure_reply = min(
        (
            _to_float(row["monotonic_seconds"])
            for row in post_failure_replies
            if _to_float(row["monotonic_seconds"]) is not None
        ),
        default=None,
    )

    first_no_answer = min(
        (
            _to_float(row["monotonic_seconds"])
            for row in no_answers
            if _to_float(row["monotonic_seconds"]) is not None
        ),
        default=None,
    )

    observed_gap = None

    if (
        last_baseline_reply is not None
        and first_post_failure_reply is not None
    ):
        observed_gap = (
            first_post_failure_reply - last_baseline_reply
        )

    first_reply_after_failure = None

    if (
        failure_started is not None
        and first_post_failure_reply is not None
    ):
        first_reply_after_failure = (
            first_post_failure_reply - failure_started
        )

    return {
        "dataset_format": "icmp_v2",
        "total_records": len(rows),
        "event_counts": dict(events),
        "phase_record_counts": dict(phases),

        "icmp_reply_count": len(replies),
        "icmp_no_answer_count": len(no_answers),

        "baseline": {
            "reply_count": len(baseline_replies),
            "mean_reply_interval": reply_interval("baseline"),
        },

        "post_failure": {
            "reply_count": len(post_failure_replies),
            "mean_reply_interval": reply_interval("post_failure"),
        },

        "failure_injection": {
            "started_monotonic": failure_started,
            "completed_monotonic": failure_completed,
            "injection_duration_seconds": (
                failure_completed - failure_started
                if failure_started is not None
                and failure_completed is not None
                else None
            ),
        },

        "observed_recovery": {
            "last_baseline_reply_monotonic": last_baseline_reply,
            "first_post_failure_reply_monotonic": first_post_failure_reply,
            "first_reply_after_failure_seconds": first_reply_after_failure,
            "gap_between_successful_replies_seconds": observed_gap,
            "first_no_answer_monotonic": first_no_answer,
        },

        "limitations": [
            "Reply counts do not establish the exact number of transmitted packets.",
            "The observed gap between successful replies is not the exact outage duration.",
            "The first successful reply after failure is an observation, not necessarily the exact recovery instant.",
            "Metrics are based on timestamps recorded by the monitoring process.",
        ],
    }


def calculate_onos_metrics(dataset, failure_time=None):
    """
    Calculate topology availability metrics from an ONOS dataset.

    Args:
        dataset: Dataset returned by load_csv().
        failure_time: Optional monotonic timestamp of the failure request.
                      It must belong to the same experiment and clock.
    """

    if dataset.get("format") != "onos_links":
        raise ValueError("Dataset must have format 'onos_links'.")

    rows = dataset["rows"]

    successful_rows = [
        row for row in rows
        if row["api_status"] == "OK"
    ]

    link_counts = Counter()

    for row in successful_rows:
        count = _to_float(row["total_directional_links"])
        if count is not None:
            link_counts[int(count)] += 1

    target_states = []

    for row in successful_rows:
        timestamp = _to_float(row["monotonic_time"])

        if timestamp is None:
            continue

        target_states.append({
            "monotonic_time": timestamp,
            "forward": row["s1_s2_forward_state"],
            "reverse": row["s2_s1_reverse_state"],
            "total_links": _to_float(
                row["total_directional_links"]
            ),
        })

    first_target_absence = None

    if failure_time is not None:
        candidates = [
            item for item in target_states
            if item["monotonic_time"] >= failure_time
            and item["forward"] == "NOT_PRESENT"
            and item["reverse"] == "NOT_PRESENT"
        ]

        if candidates:
            first_target_absence = min(
                candidates,
                key=lambda item: item["monotonic_time"],
            )

    observability_delay = None

    if first_target_absence is not None:
        observability_delay = (
            first_target_absence["monotonic_time"] - failure_time
        )

    return {
        "dataset_format": "onos_links",
        "total_records": len(rows),
        "successful_api_records": len(successful_rows),
        "api_error_records": len(rows) - len(successful_rows),

        "directional_link_count_distribution": dict(link_counts),

        "target_link": {
            "name": "s1-s2",
            "first_observed_absence_monotonic": (
                first_target_absence["monotonic_time"]
                if first_target_absence else None
            ),
            "observability_delay_seconds": observability_delay,
        },

        "limitations": [
            "The API observation time is not the exact internal ONOS detection time.",
            "A NOT_PRESENT state is an observation from the API response.",
            "The failure timestamp must use the same monotonic clock and experiment.",
            "Topology teardown must not be interpreted as a link failure.",
        ],
    }
