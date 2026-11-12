
from types import SimpleNamespace

import pytest
from framework.core.topology.enums import LinkStatus, NodeType

from framework.core.topology.enums import LinkStatus
from framework.core.topology.serialization import load_topology
from framework.integrations.mininet.adapter import (
    MininetAdapterError,
    create_mininet_network,
)


DATASET = "datasets/n1/redundant_topology.json"


class FakeHost:
    def __init__(self, name):
        self.name = name
        self.ip_configurations = []
        self.commands = []

    def setIP(self, ip, prefixLen, intf):
        self.ip_configurations.append({
            "ip": ip,
            "prefixLen": prefixLen,
            "intf": intf,
        })

    def cmd(self, command):
        self.commands.append(command)
        return ""


class FakeNetwork:
    def __init__(self, **kwargs):
        self.options = kwargs
        self.hosts = []
        self.switches = []
        self.controllers = []
        self.links = []
        self.nodes = {}
        self.built = False
        self.stopped = False

    def addHost(self, name, **kwargs):
        host = FakeHost(name)
        self.hosts.append((name, kwargs))
        self.nodes[name] = host
        return host

    def addSwitch(self, name, **kwargs):
        switch = FakeHost(name)
        self.switches.append((name, kwargs))
        self.nodes[name] = switch
        return switch

    def addController(self, name, **kwargs):
        self.controllers.append((name, kwargs))

    def addLink(self, source, destination, **kwargs):
        self.links.append((source, destination, kwargs))

    def get(self, name):
        return self.nodes[name]

    def build(self):
        self.built = True

    def stop(self):
        self.stopped = True

class FakeRemoteController:
    pass


class FakeOVSSwitch:
    pass


class FakeTCLink:
    pass


@pytest.fixture
def fake_api():
    return SimpleNamespace(
        Mininet=FakeNetwork,
        OVSSwitch=FakeOVSSwitch,
        RemoteController=FakeRemoteController,
        TCLink=FakeTCLink,
    )


@pytest.fixture
def topology():
    return load_topology(DATASET)


def test_builds_n1_topology_and_does_not_start_it(topology, fake_api):
    net = create_mininet_network(
        topology,
        controller_ip="10.145.83.64",
        controller_port=6653,
        mininet_api=fake_api,
    )

    assert net.built
    assert not net.stopped
    assert len(net.hosts) == 2
    assert len(net.switches) == 4
    assert len(net.links) == 6

    assert net.controllers[0][1]["ip"] == "10.145.83.64"
    assert net.controllers[0][1]["port"] == 6653
    # Build an index of interface IDs and their owning Nodes.
    interface_index = {
        interface.id: (node, interface)
        for node in topology.nodes.values()
        for interface in node.interfaces
    }

    # Verify that each Mininet link uses the correct Nodes and ports.
    for mininet_link, domain_link in zip(
        net.links,
        topology.links.values(),
    ):
        source_name, destination_name, options = mininet_link

        source_node, source_interface = interface_index[
            domain_link.source_interface_id
        ]
        destination_node, destination_interface = interface_index[
            domain_link.destination_interface_id
        ]

        expected_source_port = int(source_interface.name[3:])
        expected_destination_port = int(destination_interface.name[3:])

        if source_node.node_type == NodeType.SWITCH:
            expected_source_port += 1

        if destination_node.node_type == NodeType.SWITCH:
            expected_destination_port += 1

        assert source_name == source_node.id
        assert destination_name == destination_node.id

        assert options["port1"] == expected_source_port
        assert options["port2"] == expected_destination_port

        assert "params1" in options
        assert "params2" in options


def test_switches_use_openflow_13(topology, fake_api):
    net = create_mininet_network(
        topology,
        controller_ip="10.145.83.64",
        mininet_api=fake_api,
    )

    assert all(
        options["protocols"] == "OpenFlow13"
        for _, options in net.switches
    )


def test_skips_inactive_links(topology, fake_api):
    link_id = next(iter(topology.links))
    link = topology.get_link(link_id)
    link.status = LinkStatus.FAILED

    # The domain aggregate stores defensive copies. Replace the original
    # link by rebuilding the topology with this one marked as failed.
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)
    for node in topology.nodes.values():
        modified.add_node(node)

    for current in topology.links.values():
        if current.id == link_id:
            current.status = LinkStatus.FAILED
        modified.add_link(current)

    net = create_mininet_network(
        modified,
        controller_ip="10.145.83.64",
        mininet_api=fake_api,
    )

    assert len(net.links) == 5


def test_rejects_invalid_controller_port(topology, fake_api):
    with pytest.raises(ValueError):
        create_mininet_network(
            topology,
            controller_ip="10.145.83.64",
            controller_port=70000,
            mininet_api=fake_api,
        )


def test_rejects_non_topology_input(fake_api):
    with pytest.raises(TypeError):
        create_mininet_network(
            {},
            controller_ip="10.145.83.64",
            mininet_api=fake_api,
        )

def test_preserves_asymmetric_link_parameters(topology, fake_api):
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)

    for node in topology.nodes.values():
        modified.add_node(node)

    first_link_id = next(iter(topology.links))

    for current in topology.links.values():
        if current.id == first_link_id:
            current.forward.bandwidth = 500
            current.forward.delay = 5
            current.forward.packet_loss = 1

            current.reverse.bandwidth = 250
            current.reverse.delay = 2
            current.reverse.packet_loss = 3

        modified.add_link(current)

    net = create_mininet_network(
        modified,
        controller_ip="10.145.83.64",
        mininet_api=fake_api,
    )

    options = net.links[0][2]

    assert options["params1"] == {
        "bw": 500,
        "delay": "5ms",
        "loss": 1,
    }

    assert options["params2"] == {
        "bw": 250,
        "delay": "2ms",
        "loss": 3,
    }

def test_rejects_link_without_reverse_direction(topology, fake_api):
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)
    first_link_id = next(iter(topology.links))

    for node in topology.nodes.values():
        modified.add_node(node)

    for current in topology.links.values():
        if current.id == first_link_id:
            current.reverse = None

        modified.add_link(current)

    with pytest.raises(
        MininetAdapterError,
        match="no declared reverse direction",
    ):
        create_mininet_network(
            modified,
            controller_ip="10.145.83.64",
            mininet_api=fake_api,
        )

def test_skips_link_with_both_directions_disabled(topology, fake_api):
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)
    first_link_id = next(iter(topology.links))

    for node in topology.nodes.values():
        modified.add_node(node)

    for current in topology.links.values():
        if current.id == first_link_id:
            current.forward.enabled = False
            current.reverse.enabled = False

        modified.add_link(current)

    net = create_mininet_network(
        modified,
        controller_ip="10.145.83.64",
        mininet_api=fake_api,
    )

    assert len(net.links) == 5


def test_rejects_link_with_only_one_enabled_direction(topology, fake_api):
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)
    first_link_id = next(iter(topology.links))

    for node in topology.nodes.values():
        modified.add_node(node)

    for current in topology.links.values():
        if current.id == first_link_id:
            current.forward.enabled = True
            current.reverse.enabled = False

        modified.add_link(current)

    with pytest.raises(
        MininetAdapterError,
        match="only one enabled direction",
    ):
        create_mininet_network(
            modified,
            controller_ip="10.145.83.64",
            mininet_api=fake_api,
        )


def test_skips_link_with_down_interface(topology, fake_api):
    from framework.core.topology.enums import InterfaceStatus
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)
    first_link = next(iter(topology.links.values()))
    target_interface_id = first_link.source_interface_id

    for node in topology.nodes.values():
        for interface in node.interfaces:
            if interface.id == target_interface_id:
                interface.status = InterfaceStatus.DOWN

        modified.add_node(node)

    for link in topology.links.values():
        modified.add_link(link)

    net = create_mininet_network(
        modified,
        controller_ip="10.145.83.64",
        mininet_api=fake_api,
    )

    assert len(net.links) == 5


def test_skips_link_with_disabled_interface(topology, fake_api):
    from framework.core.topology.enums import InterfaceStatus
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)
    first_link = next(iter(topology.links.values()))

    target_interface_id = first_link.source_interface_id

    for node in topology.nodes.values():
        for interface in node.interfaces:
            if interface.id == target_interface_id:
                interface.status = InterfaceStatus.DISABLED

        modified.add_node(node)

    for link in topology.links.values():
        modified.add_link(link)

    net = create_mininet_network(
        modified,
        controller_ip="10.145.83.64",
        mininet_api=fake_api,
    )

    assert len(net.links) == 5


def test_rejects_router_node(topology, fake_api):
    from framework.core.topology.entities import Router
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)

    for node in topology.nodes.values():
        modified.add_node(node)

    router = Router(
        id="r1",
        name="Router 1",
    )

    modified.add_node(router)

    for link in topology.links.values():
        modified.add_link(link)

    with pytest.raises(
        MininetAdapterError,
        match="Only hosts and switches are supported",
    ):
        create_mininet_network(
            modified,
            controller_ip="10.145.83.64",
            mininet_api=fake_api,
        )

def test_configures_host_ipv4_and_ipv6_addresses(topology, fake_api):
    from ipaddress import ip_interface

    from framework.core.topology.entities import Interface
    from framework.core.topology.topology import Topology

    modified = Topology(topology.metadata)

    for node in topology.nodes.values():
        if node.id == "h1":
            node.interfaces[0].ipv4_addresses = [
                ip_interface("10.0.0.1/24")
            ]
            node.interfaces[0].ipv6_addresses = [
                ip_interface("2001:db8::1/64")
            ]

        modified.add_node(node)

    for link in topology.links.values():
        modified.add_link(link)

    net = create_mininet_network(
        modified,
        controller_ip="10.145.83.64",
        mininet_api=fake_api,
    )

    host = net.get("h1")

    assert {
        "ip": "10.0.0.1",
        "prefixLen": 24,
        "intf": "h1-eth0",
    } in host.ip_configurations

    assert (
       "ip -6 addr add 2001:db8::1/64 dev h1-eth0"
        in host.commands
    )
def test_stops_network_when_build_fails(topology):
    class FailingNetwork(FakeNetwork):
        def build(self):
            raise RuntimeError("Simulated build failure")

    failing_api = SimpleNamespace(
        Mininet=FailingNetwork,
        OVSSwitch=FakeOVSSwitch,
        RemoteController=FakeRemoteController,
        TCLink=FakeTCLink,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated build failure",
    ):
        create_mininet_network(
            topology,
            controller_ip="10.145.83.64",
            mininet_api=failing_api,
        )