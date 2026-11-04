#!/usr/bin/env python3

import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path.home() / "projects" / "intent-based-networking-llm-framework"
sys.path.insert(0, str(PROJECT_ROOT))

from framework.core.topology.serialization import load_topology
from framework.integrations.mininet import create_mininet_network


TOPOLOGY_FILE = PROJECT_ROOT / "datasets/n1/redundant_topology.json"
CONTROLLER_IP = "10.145.83.64"
CONTROLLER_PORT = 6653


def main():
    net = None

    try:
        print("===== 1. CARREGANDO TOPOLOGIA =====")
        topology = load_topology(TOPOLOGY_FILE)
        print(f"Topologia: {topology.metadata.name}")
        print(f"Nos: {len(topology.nodes)}")
        print(f"Enlaces: {len(topology.links)}")

        print("\n===== 2. CONSTRUINDO REDE MININET =====")
        net = create_mininet_network(
            topology,
            controller_ip=CONTROLLER_IP,
            controller_port=CONTROLLER_PORT,
        )

        print("Rede construída.")
        print(f"Hosts: {[host.name for host in net.hosts]}")
        print(f"Switches: {[switch.name for switch in net.switches]}")

        print("\n===== 3. INICIANDO REDE =====")
        net.start()
        print("Mininet iniciado.")

        print("\n===== 4. AGUARDANDO E TESTANDO CONECTIVIDADE =====")
        print("Executando ping entre h1 e h2...")
        result = net.pingAll(timeout=5)
        print(f"Perda de pacotes reportada pelo Mininet: {result}%")

        if result == 0:
            print("RESULTADO DO PING: APROVADO")
        else:
            print("RESULTADO DO PING: FALHOU OU APRESENTOU PERDAS")

        print("\n===== 5. ESTADO DOS SWITCHES =====")
        for switch in net.switches:
            print(f"\n--- {switch.name} ---")
            print(switch.cmd("ovs-vsctl show"))

        if result != 0:
            return 1

        return 0

    except Exception:
        print("\nFALHA NO TESTE DE INTEGRACAO:")
        traceback.print_exc()
        return 1

    finally:
        if net is not None:
            print("\n===== LIMPEZA DA REDE =====")
            try:
                net.stop()
                print("Mininet parado.")
            except Exception:
                traceback.print_exc()

        print("Teste encerrado.")


if __name__ == "__main__":
    raise SystemExit(main())
