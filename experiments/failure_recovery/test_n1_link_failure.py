
#!/usr/bin/env python3

import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = (
    Path.home()
    / "projects"
    / "intent-based-networking-llm-framework"
)

sys.path.insert(0, str(PROJECT_ROOT))

from framework.core.topology.serialization import load_topology
from framework.integrations.mininet import create_mininet_network


TOPOLOGY_FILE = PROJECT_ROOT / "datasets/n1/redundant_topology.json"

CONTROLLER_IP = "10.145.83.64"
CONTROLLER_PORT = 6653

BASELINE_DURATION = 10
FAILURE_OBSERVATION_DURATION = 40
PING_INTERVAL = 1


def main():

    net = None

    try:
        print("=" * 60)
        print("N1-FR01 - FALHA DE ENLACE E RECUPERACAO")
        print("=" * 60)

        # 1. Carregar topologia
        print("\n[1] CARREGANDO TOPOLOGIA")

        topology = load_topology(TOPOLOGY_FILE)

        print(f"Topologia: {topology.metadata.name}")
        print(f"Nos: {len(topology.nodes)}")
        print(f"Enlaces: {len(topology.links)}")

        # 2. Construir rede
        print("\n[2] CONSTRUINDO REDE MININET")

        net = create_mininet_network(
            topology,
            controller_ip=CONTROLLER_IP,
            controller_port=CONTROLLER_PORT,
        )

        print("Rede construída.")

        # 3. Iniciar rede
        print("\n[3] INICIANDO MININET")

        net.start()

        print("Mininet iniciado.")
        print("\nAGUARDANDO VERIFICACAO DO ONOS")
        print("A rede permanece ativa.")
        input("Consulte o ONOS em outro terminal e pressione ENTER para continuar...")

        h1 = net.get("h1")
        h2 = net.get("h2")

        # 4. Baseline
        print("\n[4] VERIFICANDO CONECTIVIDADE INICIAL")

        baseline = h1.cmd("ping -c 5 -W 1 " + h2.IP())

        print(baseline)

        if "0% packet loss" not in baseline:
            print("ERRO: conectividade inicial não confirmada.")
            return 1

        print("BASELINE: APROVADO")

        # 5. Monitoramento antes da falha
        print("\n[5] MONITORAMENTO ANTES DA FALHA")

        print(
            f"Observando conectividade por "
            f"{BASELINE_DURATION} segundos."
        )

        start_baseline = time.monotonic()

        while time.monotonic() - start_baseline < BASELINE_DURATION:

            result = h1.cmd(
                "ping -c 1 -W 1 " + h2.IP()
            )

            timestamp = time.monotonic()

            status = (
                "OK"
                if "1 received" in result or "1 packets received" in result
                else "FALHA"
            )

            print(
                f"[{timestamp:.3f}] "
                f"Baseline: {status}"
            )

            time.sleep(PING_INTERVAL)

        # 6. Injetar falha
        print("\n[6] INJETANDO FALHA NO ENLACE L2")

        failure_time = time.monotonic()

        print("Interrompendo enlace s1-s2...")

        net.configLinkStatus("s1", "s2", "down")

        print(
            f"FALHA INJETADA: "
            f"{time.monotonic():.3f}"
        )
        print("\nENLACE L2 PERMANECERA INDISPONIVEL POR 20 SEGUNDOS")

        time.sleep(20)

        print("\nFIM DO PERIODO DE INTERRUPCAO")

        # 7. Observar recuperação
        print("\n[7] OBSERVANDO CONECTIVIDADE APOS A FALHA")

        print(
            f"Monitoramento por "
            f"{FAILURE_OBSERVATION_DURATION} segundos."
        )

        recovered = False
        recovery_time = None

        observation_start = time.monotonic()

        while (
            time.monotonic() - observation_start
            < FAILURE_OBSERVATION_DURATION
        ):

            result = h1.cmd(
                "ping -c 1 -W 1 " + h2.IP()
            )

            current_time = time.monotonic()

            success = (
                "1 received" in result
                or "1 packets received" in result
            )

            if success:
                print(
                    f"[{current_time:.3f}] "
                    "CONECTIVIDADE RESTABELECIDA"
                )

                if not recovered:
                    recovered = True
                    recovery_time = current_time

            else:
                print(
                    f"[{current_time:.3f}] "
                    "SEM CONECTIVIDADE"
                )

            time.sleep(PING_INTERVAL)

        # 8. Resultado
        print("\n[8] RESULTADO DO EXPERIMENTO")

        if recovered:
            print("RECUPERAÇÃO: OBSERVADA")
            print(
                f"Tempo até primeiro sucesso após falha: "
                f"{recovery_time - failure_time:.3f} segundos"
            )
        else:
            print("RECUPERAÇÃO: NÃO OBSERVADA")

        print("\nExperimento concluído.")

        return 0

    except Exception:

        print("\nERRO DURANTE O EXPERIMENTO")
        traceback.print_exc()

        return 1

    finally:

        if net is not None:

            print("\n[9] ENCERRANDO MININET")

            try:
                net.stop()
                print("Mininet encerrado.")

            except Exception:
                traceback.print_exc()

if __name__ == "__main__":
    raise SystemExit(main())
