
from pathlib import Path
import math

import matplotlib.pyplot as plt


def _validate_columns(dataset, required_columns, dataset_name):
    """
    Validate that the dataset contains all required columns.
    """

    columns = dataset.get("columns", [])

    missing_columns = [
        column
        for column in required_columns
        if column not in columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in {dataset_name} dataset: "
            f"{missing_columns}"
        )


def _to_float(value, column_name):
    """
    Convert a value to float and provide a descriptive error.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid numeric value in column "
            f"'{column_name}': {value!r}"
        )


def _save_figure(fig, output_path):
    """
    Save the figure and close it.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    return output_path


def plot_icmp_timeline(
    dataset,
    output_path,
    title="N1-FR01 V2 - ICMP Timeline",
    zoom_before=2.0,
    zoom_after=3.0,
):
    """
    Generate a two-panel ICMP timeline.

    Panel A: Complete experiment overview.
    Panel B: Detailed view around link failure.

    Expected dataset format: icmp_v2.

    All timestamps must use the monotonic_seconds column.
    """

    if dataset.get("format") != "icmp_v2":
        raise ValueError(
            "Dataset must use the icmp_v2 format."
        )

    rows = dataset.get("rows", [])

    if not rows:
        raise ValueError("No ICMP records found.")

    required_columns = [
        "monotonic_seconds",
        "phase",
        "event",
        "icmp_sequence",
    ]

    _validate_columns(
        dataset,
        required_columns,
        "ICMP",
    )

    if zoom_before < 0 or zoom_after < 0:
        raise ValueError(
            "Zoom intervals must be non-negative."
        )

    events = []

    for row in rows:
        event = row["event"]

        if event not in ("icmp_reply", "icmp_no_answer"):
            continue

        events.append({
            "time": _to_float(
                row["monotonic_seconds"],
                "monotonic_seconds",
            ),
            "event": event,
            "phase": row["phase"],
            "sequence": row["icmp_sequence"],
        })

    if not events:
        raise ValueError("No ICMP events found.")

    # Reference timestamp
    start_time = min(
        item["time"]
        for item in events
    )

    # Convert timestamps to elapsed seconds
    for item in events:
        item["elapsed"] = item["time"] - start_time

    # Failure injection timestamps.
    # Both events use monotonic_seconds from the ICMP CSV.
    failure_started = [
        _to_float(
            row["monotonic_seconds"],
            "monotonic_seconds",
        ) - start_time
        for row in rows
        if row["event"] == "link_failure_injection_started"
    ]

    failure_completed = [
        _to_float(
            row["monotonic_seconds"],
            "monotonic_seconds",
        ) - start_time
        for row in rows
        if row["event"] == "link_failure_injection_completed"
    ]

    if not failure_started:
        raise ValueError(
            "Link failure injection event not found."
        )

    failure_time = failure_started[0]

    # Identify relevant ICMP events
    baseline_replies = [
        item for item in events
        if item["event"] == "icmp_reply"
        and item["phase"] == "baseline"
    ]

    post_failure_replies = [
        item for item in events
        if item["event"] == "icmp_reply"
        and item["phase"] == "post_failure"
    ]

    no_answers = [
        item for item in events
        if item["event"] == "icmp_no_answer"
    ]

    last_baseline = (
        max(
            baseline_replies,
            key=lambda item: item["time"],
        )
        if baseline_replies
        else None
    )

    first_post_failure = (
        min(
            post_failure_replies,
            key=lambda item: item["time"],
        )
        if post_failure_replies
        else None
    )

    first_no_answer = (
        min(
            no_answers,
            key=lambda item: item["time"],
        )
        if no_answers
        else None
    )

    # Create two synchronized panels
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(13, 8),
        gridspec_kw={"height_ratios": [1, 1.2]},
    )

    fig.suptitle(
        title,
        fontsize=15,
        fontweight="bold",
    )

    def draw_events(ax):
        if baseline_replies:
            ax.scatter(
                [item["elapsed"] for item in baseline_replies],
                [1] * len(baseline_replies),
                label="Baseline ICMP reply",
                marker="o",
                s=20,
            )

        if post_failure_replies:
            ax.scatter(
                [item["elapsed"] for item in post_failure_replies],
                [1] * len(post_failure_replies),
                label="Post-failure ICMP reply",
                marker="o",
                s=20,
            )

        if no_answers:
            ax.scatter(
                [item["elapsed"] for item in no_answers],
                [0] * len(no_answers),
                label="ICMP no answer",
                marker="x",
                s=90,
            )

        ax.axvline(
            x=failure_time,
            linestyle="--",
            label="Failure injection started",
        )

        for index, completed_time in enumerate(failure_completed):
            ax.axvline(
                x=completed_time,
                linestyle=":",
                label=(
                    "Failure injection completed"
                    if index == 0
                    else None
                ),
            )

        ax.set_yticks([0, 1])
        ax.set_yticklabels([
            "No answer",
            "Reply",
        ])

        ax.set_ylabel("ICMP event")
        ax.grid(True, alpha=0.3)

    # Panel A: Complete experiment
    draw_events(ax1)

    ax1.set_title(
        "(A) Complete experiment overview"
    )

    ax1.set_xlabel("Elapsed time (seconds)")

    # Panel B: Zoom around failure
    draw_events(ax2)

    zoom_start = max(
        0,
        failure_time - zoom_before,
    )

    zoom_end = failure_time + zoom_after

    ax2.set_xlim(
        zoom_start,
        zoom_end,
    )

    ax2.set_title(
        "(B) Detailed view around link failure"
    )

    ax2.set_xlabel("Elapsed time (seconds)")

    # Highlight relevant events in the zoom panel
    if last_baseline:
        ax2.annotate(
            "Last baseline reply",
            xy=(last_baseline["elapsed"], 1),
            xytext=(-10, 35),
            textcoords="offset points",
            ha="right",
            arrowprops={"arrowstyle": "->"},
        )

    if first_no_answer:
        ax2.annotate(
            "No answer",
            xy=(first_no_answer["elapsed"], 0),
            xytext=(20, 20),
            textcoords="offset points",
            ha="left",
            arrowprops={"arrowstyle": "->"},
        )

    if first_post_failure:
        ax2.annotate(
            "First post-failure reply",
            xy=(first_post_failure["elapsed"], 1),
            xytext=(15, 35),
            textcoords="offset points",
            arrowprops={"arrowstyle": "->"},
        )

    # Use one shared legend
    handles, labels = ax2.get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.5, 0.005),
    )

    fig.tight_layout(
        rect=[0, 0.08, 1, 0.95]
    )

    return _save_figure(
        fig,
        output_path,
    )


def plot_onos_link_timeline(
    dataset,
    output_path,
    failure_time=None,
    title="N1-FR01 V1 - ONOS Link Monitoring",
):
    """
    Generate a two-panel timeline of ONOS link observations.

    Panel A: Total directional links observed.
    Panel B: Forward and reverse states of link s1-s2.

    Only records with api_status == "OK" are plotted.

    Unknown link states are represented as missing values,
    not automatically interpreted as NOT_PRESENT.

    failure_time must use the same monotonic clock as the CSV.
    """

    if dataset.get("format") != "onos_links":
        raise ValueError(
            "Dataset must use the onos_links format."
        )

    rows = dataset.get("rows", [])

    if not rows:
        raise ValueError("No ONOS records found.")

    required_columns = [
        "monotonic_time",
        "total_directional_links",
        "s1_s2_forward_state",
        "s2_s1_reverse_state",
        "api_status",
    ]

    _validate_columns(
        dataset,
        required_columns,
        "ONOS",
    )

    # Separate successful API observations from failed requests.
    valid_records = [
        row for row in rows
        if row["api_status"] == "OK"
    ]

    api_error_count = len(rows) - len(valid_records)

    if not valid_records:
        raise ValueError(
            "No successful ONOS API observations found."
        )

    # Sort successful records by monotonic timestamp
    records = sorted(
        valid_records,
        key=lambda row: _to_float(
            row["monotonic_time"],
            "monotonic_time",
        ),
    )

    start_time = _to_float(
        records[0]["monotonic_time"],
        "monotonic_time",
    )

    elapsed = [
        _to_float(
            row["monotonic_time"],
            "monotonic_time",
        ) - start_time
        for row in records
    ]

    directional_counts = [
        int(
            _to_float(
                row["total_directional_links"],
                "total_directional_links",
            )
        )
        for row in records
    ]

    forward_states = [
        row["s1_s2_forward_state"]
        for row in records
    ]

    reverse_states = [
        row["s2_s1_reverse_state"]
        for row in records
    ]

    # Locate relevant transitions
    first_zero_index = next(
        (
            i
            for i, count in enumerate(directional_counts)
            if count == 0
        ),
        None,
    )

    first_absence_index = next(
        (
            i
            for i, (forward, reverse) in enumerate(
                zip(forward_states, reverse_states)
            )
            if forward == "NOT_PRESENT"
            and reverse == "NOT_PRESENT"
        ),
        None,
    )

    # Convert failure timestamp to elapsed time
    failure_elapsed = None

    if failure_time is not None:
        failure_elapsed = (
            float(failure_time) - start_time
        )

    # Map link states without treating unknown states
    # as equivalent to NOT_PRESENT.
    def state_to_numeric(state):
        if state == "ACTIVE":
            return 1.0

        if state == "NOT_PRESENT":
            return 0.0

        return math.nan

    forward_values = [
        state_to_numeric(state)
        for state in forward_states
    ]

    reverse_values = [
        state_to_numeric(state)
        for state in reverse_states
    ]

    # Create figure
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(13, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [1, 1.2]},
    )

    fig.suptitle(
        title,
        fontsize=15,
        fontweight="bold",
    )

    # --------------------------------------------------
    # Panel A: Total directional links
    # --------------------------------------------------

    ax1.step(
        elapsed,
        directional_counts,
        where="post",
        label="Observed directional links",
    )

    ax1.set_title(
        "(A) Total directional links observed"
    )

    ax1.set_ylabel("Directional links")

    ax1.set_yticks([
        0,
        6,
        8,
    ])

    ax1.set_ylim(
        -0.5,
        9,
    )

    ax1.grid(
        True,
        alpha=0.3,
    )

    if failure_elapsed is not None:
        ax1.axvline(
            failure_elapsed,
            linestyle="--",
            label="Failure injection requested",
        )

    if first_absence_index is not None:
        absence_time = elapsed[first_absence_index]

        ax1.axvline(
            absence_time,
            linestyle=":",
            label="First observed absence of s1-s2",
        )

    if first_zero_index is not None:
        zero_time = elapsed[first_zero_index]

        ax1.axvline(
            zero_time,
            linestyle="-.",
            label="Mininet topology teardown",
        )

    if api_error_count > 0:
        ax1.text(
            0.99,
            0.95,
            f"API errors excluded: {api_error_count}",
            transform=ax1.transAxes,
            ha="right",
            va="top",
        )

    # --------------------------------------------------
    # Panel B: Target link states
    # --------------------------------------------------

    ax2.step(
        elapsed,
        forward_values,
        where="post",
        label="s1 -> s2",
    )

    ax2.step(
        elapsed,
        reverse_values,
        where="post",
        label="s2 -> s1",
        linestyle="--",
    )

    ax2.set_title(
        "(B) Target link s1-s2 directional states"
    )

    ax2.set_xlabel("Elapsed time (seconds)")
    ax2.set_ylabel("Link state")

    ax2.set_yticks([
        0,
        1,
    ])

    ax2.set_yticklabels([
        "NOT_PRESENT",
        "ACTIVE",
    ])

    ax2.set_ylim(
        -0.2,
        1.2,
    )

    ax2.grid(
        True,
        alpha=0.3,
    )

    if failure_elapsed is not None:
        ax2.axvline(
            failure_elapsed,
            linestyle="--",
            label="Failure injection requested",
        )

    if first_absence_index is not None:
        ax2.axvline(
            elapsed[first_absence_index],
            linestyle=":",
            label="First observed absence of s1-s2",
        )

    # Shared legend
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    # Combine legends and remove duplicate labels
    legend_items = {}

    for handle, label in zip(
        handles1 + handles2,
        labels1 + labels2,
    ):
        if label not in legend_items:
            legend_items[label] = handle

    fig.legend(
        legend_items.values(),
        legend_items.keys(),
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.5, 0.005),
    )

    fig.tight_layout(
        rect=[0, 0.10, 1, 0.95]
    )

    return _save_figure(
        fig,
        output_path,
    )
