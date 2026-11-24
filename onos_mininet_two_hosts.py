import time
from ipaddress import ip_interface

from framework.core.topology.entities import (
    Host,
    Interface,
    Link,
    LinkDirection,
    Metadata,
    Switch,
)
from framework.core.topology.topology import Topology
from framework.integrations.mininet.adapter import create_mininet_network


# ============================================================
# 1. Construção da topologia V2
# ============================================================

topology = Topology(
    Metadata(
        id="onos-integration-02",
        name="Mininet ONOS Integration - Two Hosts",
    )
)

# Host 1
h1 = Host(
    id="h1",
    name="Host 1",
    interfaces=[
        Interface(
            id="h1-eth0",
            name="eth0",
            ipv4_addresses=[ip_interface("192.0.2.10/24")],
        )
    ],
)

# Host 2
h2 = Host(
    id="h2",
    name="Host 2",
    interfaces=[
        Interface(
            id="h2-eth0",
            name="eth0",
            ipv4_addresses=[ip_interface("192.0.2.20/24")],
        )
    ],
)

# Switch
s1 = Switch(
    id="s1",
    name="Switch 1",
    interfaces=[
        Interface(id="s1-eth0", name="eth0"),
        Interface(id="s1-eth1", name="eth1"),
    ],
)

topology.add_node(h1)
topology.add_node(h2)
topology.add_node(s1)


# ============================================================
# 2. Parâmetros dos enlaces
# ============================================================

def make_direction():
    return LinkDirection(
        bandwidth=1000,
        delay=1,
        weight=1,
        packet_loss=0,
        enabled=True,
    )


# h1 <-> s1
topology.add_link(
    Link(
        id="link-h1-s1",
        source_interface_id="h1-eth0",
        destination_interface_id="s1-eth0",
        forward=make_direction(),
        reverse=make_direction(),
    )
)

# h2 <-> s1
topology.add_link(
    Link(
        id="link-h2-s1",
        source_interface_id="h2-eth0",
        destination_interface_id="s1-eth1",
        forward=make_direction(),
        reverse=make_direction(),
    )
)


# ============================================================
# 3. Validação visual da topologia construída
# ============================================================

print("\nTopologia V2 construída:")
print(f"Nodes: {list(topology.nodes.keys())}")
print(f"Links: {list(topology.links.keys())}")


# ============================================================
# 4. Criação da rede pelo Adapter V2
# ============================================================

net = create_mininet_network(
    topology,
    controller_ip="10.145.83.64",
    controller_port=6653,
)

try:
    net.start()

    print("\nRede Mininet iniciada.")
    print("Hosts:", [host.name for host in net.hosts])
    print("Switches:", [switch.name for switch in net.switches])

    print("\nTopologia em execução. Pressione Ctrl+C para encerrar.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nInterrupção solicitada pelo usuário.")

finally:
    net.stop()
    print("Mininet encerrado corretamente.")
