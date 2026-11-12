
from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Interface

from framework.core.topology import (
    Metadata,
    Host,
    Switch,
    Router,
    Interface,
    StaticRoute,
    Link,
    LinkDirection,
    Controller,
    ControllerAssociation,
    Policy,
    Metrics,
    Topology,
    TopologySource,
    LinkStatus,
    ControllerStatus,
    AssociationRole,
    serialize_topology,
    deserialize_topology,
    save_topology,
    load_topology,
)


def build_topology():
    topology = Topology(
        metadata=Metadata(
            id="topology-001",
            name="Serialization Test",
            description="Complete V2 round-trip test",
            author="Test",
            version="2.0",
            created_at=datetime.now(timezone.utc),
            topology_source=TopologySource.SYNTHETIC,
            tags=["test", "round-trip"],
        )
    )

    host = Host(
        id="host-01",
        name="Host 01",
        interfaces=[
            Interface(
                id="if-host-01",
                name="eth0",
                mac_address="02:00:00:00:00:01",
                ipv4_addresses=[IPv4Interface("192.168.1.10/24")],
                ipv6_addresses=[IPv6Interface("2001:db8:1::10/64")],
            )
        ],
    )

    switch = Switch(
        id="switch-01",
        name="Switch 01",
        interfaces=[
            Interface(
                id="if-switch-01",
                name="eth1",
                mac_address="02:00:00:00:00:02",
            )
        ],
    )

    router = Router(
        id="router-01",
        name="Router 01",
        ipv4_forwarding=True,
        static_routes=[
            StaticRoute(
                id="route-01",
                destination=IPv4Network("10.10.0.0/16"),
                next_hop=IPv4Address("192.168.1.1"),
                metric=10,
            )
        ],
    )

    topology.add_node(host)
    topology.add_node(switch)
    topology.add_node(router)

    topology.add_link(
        Link(
            id="link-01",
            source_interface_id="if-host-01",
            destination_interface_id="if-switch-01",
            forward=LinkDirection(
                bandwidth=1000,
                delay=2,
                weight=1,
                packet_loss=0,
                enabled=True,
            ),
            reverse=None,
            status=LinkStatus.ACTIVE,
        )
    )

    topology.add_controller(
        Controller(
            id="controller-01",
            name="ONOS",
            controller_type="onos",
            endpoint="192.168.1.100",
            port=6653,
            protocol="openflow",
            status=ControllerStatus.ACTIVE,
        )
    )

    topology.add_controller_association(
        ControllerAssociation(
            id="association-01",
            controller_id="controller-01",
            node_id="switch-01",
            role=AssociationRole.MASTER,
        )
    )

    topology.add_policy(
        Policy(
            id="policy-01",
            name="Test Policy",
            description="Serialization test policy",
            enabled=True,
            attributes={"priority": 100},
        )
    )

    topology.set_metrics(
        Metrics(values={
            "latency_ms": 2.5,
            "packet_loss": 0,
            "active_flows": 10,
        })
    )

    return topology


def main():
    original = build_topology()

    # Teste em memória: objeto -> documento -> objeto
    document = serialize_topology(original)
    restored = deserialize_topology(document)

    assert serialize_topology(restored) == document

    # Teste em arquivo: objeto -> JSON -> objeto
    path = "serialization_roundtrip_test.json"
    save_topology(original, path)
    loaded = load_topology(path)

    assert serialize_topology(loaded) == document

    # Verificações específicas do contrato V2
    assert isinstance(loaded.nodes["host-01"], Host)
    assert isinstance(loaded.nodes["switch-01"], Switch)
    assert isinstance(loaded.nodes["router-01"], Router)

    assert isinstance(
        loaded.nodes["host-01"].interfaces[0].ipv4_addresses[0],
        IPv4Interface,
    )
    assert isinstance(
        loaded.nodes["host-01"].interfaces[0].ipv6_addresses[0],
        IPv6Interface,
    )

    assert loaded.links["link-01"].reverse is None
    assert loaded.controllers["controller-01"].port == 6653
    assert loaded.controller_associations["association-01"].role == AssociationRole.MASTER
    assert loaded.policies["policy-01"].enabled is True
    assert loaded.metrics.values["latency_ms"] == 2.5

    print("Round-trip em memória: OK")
    print("Round-trip em arquivo JSON: OK")
    print("Preservação dos tipos e entidades V2: OK")


if __name__ == "__main__":
    main()
