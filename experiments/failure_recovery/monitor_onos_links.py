
#!/usr/bin/env python3
"""
ONOS Link Monitor - N1-FR01

Monitora continuamente a topologia de enlaces do ONOS
e registra os estados em CSV para análise experimental.
"""

import csv
import os
import time
import requests

from datetime import datetime, timezone
from requests.auth import HTTPBasicAuth


# ============================================================
# CONFIGURATION
# ============================================================

ONOS_URL = "http://10.145.83.64:8181/onos/v1/links"
ONOS_USER = "onos"
ONOS_PASSWORD = "rocks"

POLL_INTERVAL = 0.2

TARGET_LINK = {
    "src": "of:0000000000000001/2",
    "dst": "of:0000000000000002/1",
}

RESULTS_DIR = "experiments/failure_recovery/results"


# ============================================================
# HELPERS
# ============================================================

def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def get_links(session):
    response = session.get(
        ONOS_URL,
        timeout=3
    )

    response.raise_for_status()

    return response.json().get("links", [])


def normalize_link(link):
    return (
        link.get("src", {}).get("device"),
        link.get("src", {}).get("port"),
        link.get("dst", {}).get("device"),
        link.get("dst", {}).get("port"),
    )


def link_status(links, src, src_port, dst, dst_port):
    for link in links:
        normalized = normalize_link(link)

        if normalized == (src, src_port, dst, dst_port):
            return link.get("state", "UNKNOWN")

    return "NOT_PRESENT"


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(RESULTS_DIR, exist_ok=True)

    filename = (
        "onos-links-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".csv"
    )

    filepath = os.path.join(RESULTS_DIR, filename)

    session = requests.Session()

    session.auth = HTTPBasicAuth(
        ONOS_USER,
        ONOS_PASSWORD
    )

    session.headers.update({
        "Accept": "application/json"
    })

    print("=" * 65)
    print("ONOS LINK MONITOR - N1-FR01")
    print("=" * 65)

    print(f"ONOS: {ONOS_URL}")
    print(f"Intervalo: {POLL_INTERVAL}s")
    print(f"Enlace monitorado: s1-s2")
    print(f"CSV: {filepath}")

    print("\nMonitoramento iniciado.")
    print("Pressione Ctrl+C para encerrar.\n")

    fields = [
        "timestamp_utc",
        "monotonic_time",
        "poll_duration_ms",
        "total_directional_links",
        "s1_s2_forward_state",
        "s2_s1_reverse_state",
        "s1_s3_state",
        "s3_s1_state",
        "s2_s4_state",
        "s4_s2_state",
        "s3_s4_state",
        "s4_s3_state",
        "api_status",
    ]

    try:

        with open(
            filepath,
            "w",
            newline="",
            encoding="utf-8"
        ) as csvfile:

            writer = csv.DictWriter(
                csvfile,
                fieldnames=fields
            )

            writer.writeheader()

            while True:

                cycle_start = time.monotonic()

                timestamp = utc_timestamp()

                api_status = "OK"

                try:

                    request_start = time.monotonic()

                    links = get_links(session)

                    request_end = time.monotonic()

                    poll_duration_ms = (
                        request_end - request_start
                    ) * 1000

                    states = {
                        "s1_s2_forward_state": link_status(
                            links,
                            "of:0000000000000001",
                            "2",
                            "of:0000000000000002",
                            "1",
                        ),

                        "s2_s1_reverse_state": link_status(
                            links,
                            "of:0000000000000002",
                            "1",
                            "of:0000000000000001",
                            "2",
                        ),

                        "s1_s3_state": link_status(
                            links,
                            "of:0000000000000001",
                            "3",
                            "of:0000000000000003",
                            "1",
                        ),

                        "s3_s1_state": link_status(
                            links,
                            "of:0000000000000003",
                            "1",
                            "of:0000000000000001",
                            "3",
                        ),

                        "s2_s4_state": link_status(
                            links,
                            "of:0000000000000002",
                            "2",
                            "of:0000000000000004",
                            "1",
                        ),

                        "s4_s2_state": link_status(
                            links,
                            "of:0000000000000004",
                            "1",
                            "of:0000000000000002",
                            "2",
                        ),

                        "s3_s4_state": link_status(
                            links,
                            "of:0000000000000003",
                            "2",
                            "of:0000000000000004",
                            "2",
                        ),

                        "s4_s3_state": link_status(
                            links,
                            "of:0000000000000004",
                            "2",
                            "of:0000000000000003",
                            "2",
                        ),
                    }

                except requests.RequestException as error:

                    api_status = "ERROR"
                    poll_duration_ms = None
                    links = []
                    states = {
                        field: "UNKNOWN"
                        for field in fields[4:12]
                    }

                    print(
                        f"[ERRO API] {error}",
                        flush=True
                    )

                row = {
                    "timestamp_utc": timestamp,
                    "monotonic_time": time.monotonic(),
                    "poll_duration_ms": poll_duration_ms,
                    "total_directional_links": len(links),
                    "api_status": api_status,
                    **states,
                }

                writer.writerow(row)

                csvfile.flush()

                target_state = states[
                    "s1_s2_forward_state"
                ]

                reverse_state = states[
                    "s2_s1_reverse_state"
                ]

                print(
                    f"{timestamp} | "
                    f"Links={len(links)} | "
                    f"s1-s2={target_state} | "
                    f"s2-s1={reverse_state} | "
                    f"API={api_status}",
                    flush=True
                )

                elapsed = time.monotonic() - cycle_start

                time.sleep(
                    max(0, POLL_INTERVAL - elapsed)
                )

    except KeyboardInterrupt:

        print("\nMonitoramento encerrado pelo usuário.")

    finally:

        session.close()

        print(f"Resultado salvo em: {filepath}")


if __name__ == "__main__":
    main()
