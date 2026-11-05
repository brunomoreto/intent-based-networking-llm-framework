#!/usr/bin/env python3
"""N1-FR01 V2: continuous ICMP monitoring during link failure/recovery."""

import csv
import queue
import re
import subprocess
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from framework.core.topology.serialization import load_topology
from framework.integrations.mininet import create_mininet_network

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOPOLOGY_FILE = PROJECT_ROOT / "datasets/n1/redundant_topology.json"
CONTROLLER_IP = "10.145.83.64"
CONTROLLER_PORT = 6653

BASELINE_DURATION = 10.0
FAILURE_OBSERVATION_DURATION = 60.0
PING_INTERVAL = 0.2
PING_TIMEOUT = 1
FAILURE_LINK = ("s1", "s2")

REPLY_RE = re.compile(r"icmp_seq=(\d+)")
NO_ANSWER_RE = re.compile(r"no answer yet for icmp_seq=(\d+)", re.IGNORECASE)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def emit(event_queue, event_type, sequence=None, raw=""):
    event_queue.put({
        "utc_timestamp": utc_now(),
        "monotonic": time.monotonic(),
        "event": event_type,
        "icmp_seq": sequence,
        "raw": raw.strip(),
    })


def read_ping_output(process, event_queue):
    for line in process.stdout:
        line = line.rstrip()
        reply = REPLY_RE.search(line)
        no_answer = NO_ANSWER_RE.search(line)
        if reply and "bytes from" in line:
            emit(event_queue, "icmp_reply", int(reply.group(1)), line)
        elif no_answer:
            emit(event_queue, "icmp_no_answer", int(no_answer.group(1)), line)
        elif line:
            emit(event_queue, "ping_info", None, line)


def collect_events(event_queue, rows, state, phase):
    while True:
        try:
            event = event_queue.get_nowait()
        except queue.Empty:
            break

        event_phase = (
            "post_failure"
            if state["failure_time"] is not None
            and event["monotonic"] >= state["failure_time"]
            else "baseline"
        )

        rows.append([
            event["utc_timestamp"],
            f'{event["monotonic"]:.6f}',
            event_phase,
            event["event"],
            event["icmp_seq"] if event["icmp_seq"] is not None else "",
            event["raw"],
        ])

        seq = event["icmp_seq"]
        if event["event"] == "icmp_reply":
            if event_phase == "baseline":
                state["baseline_replies"] += 1
                state["last_success_before_failure"] = event["monotonic"]
            else:
                state["post_failure_replies"] += 1
                if state["first_success_after_failure"] is None:
                    state["first_success_after_failure"] = event["monotonic"]
                    state["first_success_sequence"] = seq
                state["last_success_after_failure"] = event["monotonic"]
        elif event["event"] == "icmp_no_answer":
            if event_phase == "baseline":
                state["baseline_no_answer"] += 1
            else:
                state["post_failure_no_answer"] += 1


def monitor_for(duration, event_queue, rows, state, phase):
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        collect_events(event_queue, rows, state, phase)
        time.sleep(0.02)
    collect_events(event_queue, rows, state, phase)


def save_csv(rows):
    result_dir = PROJECT_ROOT / "experiments" / "failure_recovery" / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    filename = "n1-fr01-v2-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv"
    output = result_dir / filename
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "utc_timestamp", "monotonic_seconds", "phase",
            "event", "icmp_sequence", "raw_ping_output",
        ])
        writer.writerows(rows)
    return output


def main():
    net = None
    ping_process = None
    reader_thread = None
    event_queue = queue.Queue()
    rows = []
    state = {
        "baseline_replies": 0,
        "baseline_no_answer": 0,
        "post_failure_replies": 0,
        "post_failure_no_answer": 0,
        "last_success_before_failure": None,
        "failure_time": None,
        "first_success_after_failure": None,
        "first_success_sequence": None,
        "last_success_after_failure": None,
    }
    failure_time = None
    link_down_completed = None
    error = None

    try:
        print("=" * 68)
        print("N1-FR01 V2 - MONITORAMENTO CONTINUO DE FALHA E RECUPERACAO")
        print("=" * 68)
        print(f"Intervalo ICMP: {PING_INTERVAL:.3f} s")
        print(f"Baseline: {BASELINE_DURATION:.1f} s")
        print(f"Observacao apos falha: {FAILURE_OBSERVATION_DURATION:.1f} s")
        print(f"Enlace alvo: {FAILURE_LINK[0]}-{FAILURE_LINK[1]}")

        print("\n[1] CARREGANDO TOPOLOGIA")
        topology = load_topology(TOPOLOGY_FILE)
        print(f"Topologia: {topology.metadata.name}")
        print(f"Nos: {len(topology.nodes)}")
        print(f"Enlaces: {len(topology.links)}")

        print("\n[2] CONSTRUINDO E INICIANDO MININET")
        net = create_mininet_network(
            topology,
            controller_ip=CONTROLLER_IP,
            controller_port=CONTROLLER_PORT,
        )
        net.start()
        print("Mininet iniciado.")

        print("\nAGUARDANDO VERIFICACAO DO ONOS")
        input("Consulte o ONOS e pressione ENTER para iniciar o monitoramento...")

        h1 = net.get("h1")
        h2 = net.get("h2")
        destination_ip = h2.IP()

        print("\n[3] INICIANDO SONDA ICMP CONTINUA")
        command = [
            "ping", "-n", "-D", "-O", "-i", str(PING_INTERVAL),
            "-W", str(PING_TIMEOUT), destination_ip,
        ]
        # Execute ping inside h1's network namespace, not on the Mininet host.
        ping_process = h1.popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        reader_thread = threading.Thread(
            target=read_ping_output,
            args=(ping_process, event_queue),
            daemon=True,
        )
        reader_thread.start()

        print("\n[4] BASELINE")
        monitor_for(
            BASELINE_DURATION, event_queue, rows, state, "baseline"
        )
        print(f"Respostas ICMP no baseline: {state['baseline_replies']}")
        print(f"Eventos sem resposta no baseline: {state['baseline_no_answer']}")
        if state["baseline_replies"] == 0:
            raise RuntimeError("Baseline reprovado: nenhuma resposta ICMP.")

        print("BASELINE: CONECTIVIDADE OBSERVADA")

        print("\n[5] INJETANDO FALHA NO ENLACE L2")
        failure_time = time.monotonic()
        state["failure_time"] = failure_time
        emit(event_queue, "link_failure_injection_started")
        print(f"Solicitacao de falha em monotonic={failure_time:.6f}")
        net.configLinkStatus(FAILURE_LINK[0], FAILURE_LINK[1], "down")
        link_down_completed = time.monotonic()
        emit(event_queue, "link_failure_injection_completed")
        print(f"Enlace {FAILURE_LINK[0]}-{FAILURE_LINK[1]} configurado como down.")

        print("\n[6] MONITORAMENTO CONTINUO APOS A FALHA")
        remaining = failure_time + FAILURE_OBSERVATION_DURATION - time.monotonic()
        if remaining > 0:
            monitor_for(
                remaining, event_queue, rows, state, "post_failure"
            )
        else:
            collect_events(event_queue, rows, state, "post_failure")

        print("\n[7] ENCERRANDO SONDA ICMP")
        ping_process.terminate()
        try:
            ping_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            ping_process.kill()
            ping_process.wait(timeout=3)
        reader_thread.join(timeout=2)
        collect_events(event_queue, rows, state, "post_failure")

        print("\n[8] RESULTADOS")
        print(f"Respostas no baseline: {state['baseline_replies']}")
        print(f"Sem resposta no baseline: {state['baseline_no_answer']}")
        print(f"Respostas apos a falha: {state['post_failure_replies']}")
        print(f"Sem resposta apos a falha: {state['post_failure_no_answer']}")
        print(
            "Tempo de aplicacao da falha no Mininet: "
            f"{link_down_completed - failure_time:.6f} s"
        )

        first = state["first_success_after_failure"]
        if first is None:
            print("RECUPERACAO: NAO OBSERVADA NA JANELA EXPERIMENTAL")
        else:
            print("RECUPERACAO: RESPOSTA ICMP OBSERVADA")
            print(
                "Tempo entre solicitacao de falha e primeira resposta posterior: "
                f"{first - failure_time:.6f} s"
            )
            print(f"Sequencia da primeira resposta posterior: "
                  f"{state['first_success_sequence']}")
            last_before = state["last_success_before_failure"]
            if last_before is not None:
                print(
                    "Intervalo entre ultima resposta anterior e primeira posterior: "
                    f"{first - last_before:.6f} s"
                )
            if state["last_success_after_failure"] is not None:
                window_end = failure_time + FAILURE_OBSERVATION_DURATION
                print(
                    "Observacao apos a primeira resposta de recuperacao: "
                    f"{window_end - first:.3f} s"
                )

        print(
            "\nNOTA: os tempos sao observacoes do processo ICMP, limitadas "
            "pelo intervalo de sondagem, agendamento do sistema e processamento "
            "das respostas. O primeiro sucesso delimita a recuperacao observada; "
            "nao revela o instante interno exato da convergencia do ONOS."
        )

    except Exception as exc:
        error = exc
        print("\nERRO DURANTE O EXPERIMENTO")
        traceback.print_exc()

    finally:
        if ping_process is not None and ping_process.poll() is None:
            ping_process.terminate()
            try:
                ping_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                ping_process.kill()
                ping_process.wait(timeout=3)

        if reader_thread is not None:
            reader_thread.join(timeout=2)

        collect_events(event_queue, rows, state, "final")

        if rows:
            try:
                output = save_csv(rows)
                print(f"\nCSV de eventos salvo em: {output}")
            except Exception:
                print("\nFalha ao salvar CSV.")
                traceback.print_exc()

        if net is not None:
            print("\n[9] ENCERRANDO MININET")
            try:
                net.stop()
                print("Mininet encerrado.")
            except Exception:
                traceback.print_exc()

    return 1 if error is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
