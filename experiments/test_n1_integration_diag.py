#!/usr/bin/env python3

import sys
import time
import traceback
import json
import urllib.request
import urllib.error
import base64
from pathlib import Path

PROJECT_ROOT = Path.home() / "projects" / "intent-based-networking-llm-framework"
sys.path.insert(0, str(PROJECT_ROOT))

from framework.core.topology.serialization import load_topology
from framework.integrations.mininet import create_mininet_network

TOPOLOGY_FILE = PROJECT_ROOT / "datasets/n1/redundant_topology.json"
CONTROLLER_IP = "10.145.83.64"
CONTROLLER_PORT = 6653
ONOS_USER = "onos"
ONOS_PASSWORD = "rocks"
ONOS_BASE_URL = "http://10.145.83.64:8181/onos/v1"


def onos_get(endpoint):
    url = f"{ONOS_BASE_URL}/{endpoint.lstrip('/')}"
    token = base64.b64encode(
        f"{ONOS_USER}:{ONOS_PASSWORD}".encode("utf-8")
    ).decode("ascii")
    request = urllib.request.Request(
        url, headers={"Authorization": f"Basic {token}"}
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"diagnostic_error": f"HTTP {exc.code} ao consultar {url}"}
    except Exception as exc:
        return {"diagnostic_error": f"Falha ao consultar {url}: {exc}"}


def print_onos_summary(endpoint, collection_key, title):
    print(f"\n===== ONOS: {title} =====")
    result = onos_get(endpoint)
    if "diagnostic_error" in result:
        print(result["diagnostic_error"])
        return
    items = result.get(collection_key, [])
    print(f"Quantidade: {len(items)}")
    if endpoint == "devices":
        for item in items:
            print(f"{item.get('id')} | disponível={item.get('available')} | papel={item.get('role')}")
    elif endpoint == "links":
        for item in items:
            src, dst = item.get("src", {}), item.get("dst", {})
            print(f"{src.get('device')}:{src.get('port')} -> {dst.get('device')}:{dst.get('port')} | estado={item.get('state')}")
    elif endpoint == "hosts":
        for item in items:
            print(f"{item.get('id')} | MAC={item.get('mac')} | IPs={item.get('ipAddresses')} | localização={item.get('locations')}")
    elif endpoint == "flows":
        for item in items:
            print(f"switch={item.get('deviceId')} | app={item.get('appId')} | estado={item.get('state')} | prioridade={item.get('priority')} | pacotes={item.get('packets')} | tratamento={item.get('treatment')}")


def main():
    net = None
    exit_code = 1
    try:
        print("===== 1. CARREGANDO TOPOLOGIA =====")
        topology = load_topology(TOPOLOGY_FILE)
        print(f"Topologia: {topology.metadata.name}")
        print(f"Nós: {len(topology.nodes)}")
        print(f"Enlaces declarados: {len(topology.links)}")

        print("\n===== 2. CONSTRUINDO REDE MININET =====")
        net = create_mininet_network(topology, controller_ip=CONTROLLER_IP, controller_port=CONTROLLER_PORT)
        print(f"Hosts: {[host.name for host in net.hosts]}")
        print(f"Switches: {[switch.name for switch in net.switches]}")

        print("\n===== 3. INICIANDO REDE =====")
        net.start()
        time.sleep(5)
        print("Mininet iniciado.")

        print("\n===== 4. ENDEREÇOS, INTERFACES E ROTAS =====")
        for host in net.hosts:
            print(f"\n--- {host.name} ---")
            print("Endereços:")
            print(host.cmd("ip -br addr"))
            print("Interfaces:")
            print(host.cmd("ip link"))
            print("Rotas:")
            print(host.cmd("ip route"))
            print("Vizinhos ARP:")
            print(host.cmd("ip neigh"))

        print_onos_summary("devices", "devices", "DISPOSITIVOS")
        print_onos_summary("links", "links", "ENLACES")
        print_onos_summary("hosts", "hosts", "HOSTS")
        print_onos_summary("flows", "flows", "REGRAS DE FLUXO")

        print("\n===== 5. TESTE DE CONECTIVIDADE =====")
        h1, h2 = net.get("h1"), net.get("h2")
        print("Teste individual: h1 -> h2")
        print(h1.cmd(f"ping -c 3 -W 2 {h2.IP()}"))
        print("Tabela ARP de h1 após o teste:")
        print(h1.cmd("ip neigh"))
        print("Tabela ARP de h2 após o teste:")
        print(h2.cmd("ip neigh"))

        print("\n===== 6. ESTADO DO ONOS APÓS O TRÁFEGO =====")
        print_onos_summary("hosts", "hosts", "HOSTS")
        print_onos_summary("flows", "flows", "REGRAS DE FLUXO")

        print("\n===== 7. TESTE GERAL DO MININET =====")
        loss = net.pingAll(timeout=5)
        print(f"Perda de pacotes: {loss}%")
        if loss == 0:
            print("RESULTADO: APROVADO")
            exit_code = 0
        else:
            print("RESULTADO: FALHOU OU APRESENTOU PERDAS")
            exit_code = 1
    except Exception:
        print("\nFALHA NO TESTE DE INTEGRAÇÃO:")
        traceback.print_exc()
        exit_code = 1
    finally:
        if net is not None:
            print("\n===== 8. LIMPEZA DA REDE =====")
            try:
                net.stop()
                print("Mininet parado.")
            except Exception:
                traceback.print_exc()
        print("Teste encerrado.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
