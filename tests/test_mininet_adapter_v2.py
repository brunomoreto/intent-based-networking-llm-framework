import importlib.util
import os
import sys
from ipaddress import ip_address, ip_interface, ip_network
from types import SimpleNamespace

import pytest

from framework.core.topology.entities import (
    Host,
    Interface,
    Link,
    LinkDirection,
    Metadata,
    Router,
    StaticRoute,
    Switch,
)
from framework.core.topology.enums import InterfaceStatus, LinkStatus
from framework.core.topology.topology import Topology
from framework.integrations.mininet.adapter import (
    MininetAdapterError,
    create_mininet_network,
)


class FakeNode:
    def __init__(self, name):
        self.name = name
        self.commands = []

    def cmd(self, command):
        self.commands.append(command)
        return ""


class FakeNetwork:
    def __init__(self, **kwargs):
        self.options = kwargs
        self.nodes = {}
        self.hosts = []
        self.switches = []
        self.links = []
        self.controllers = []
        self.built = False
        self.stopped = False

    def addHost(self, name, **kwargs):
        self.hosts.append((name, kwargs))
        node = FakeNode(name)
        self.nodes[name] = node
        return node

    def addSwitch(self, name, **kwargs):
        self.switches.append((name, kwargs))
        node = FakeNode(name)
        self.nodes[name] = node
        return node

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


class FakeLinuxRouter:
    pass


class FakeOVSSwitch:
    pass


class FakeRemoteController:
    pass


class FakeTCLink:
    pass


@pytest.fixture

def mininet_api():
    return SimpleNamespace(
        Mininet=FakeNetwork,
        OVSSwitch=FakeOVSSwitch,
        RemoteController=FakeRemoteController,
        TCLink=FakeTCLink,
        LinuxRouter=FakeLinuxRouter,
    )


def make_direction(*, enabled=True, bandwidth=100, delay=1, loss=0):
    return LinkDirection(
        bandwidth=bandwidth,
        delay=delay,
        weight=1,
        packet_loss=loss,
        enabled=enabled,
    )


def make_topology(*, with_host_route=True):
    topology = Topology(
        Metadata(id="router-test", name="Router Adapter Test")
    )

    host = Host(
        id="h1",
        name="Host 1",
        interfaces=[
            Interface(
                id="h1-eth0",
                name="eth0",
                ipv4_addresses=[ip_interface("192.0.2.10/24")],
                ipv6_addresses=[ip_interface("2001:db8:1::10/64")],
            )
        ],
        static_routes=(
            [
                StaticRoute(
                    id="host-route-v4",
                    destination=ip_network("198.51.100.0/24"),
                    next_hop=ip_address("192.0.2.1"),
                    outgoing_interface_id="h1-eth0",
                    metric=20,
                ),
                StaticRoute(
                    id="host-route-v6",
                    destination=ip_network("2001:db8:2::/64"),
                    next_hop=ip_address("2001:db8:1::1"),
                    outgoing_interface_id="h1-eth0",
                    metric=30,
                ),
            ] if with_host_route else []
        ),
    )
    router = Router(
        id="r1",
        name="Router 1",
        ipv4_forwarding=True,
        ipv6_forwarding=True,
        interfaces=[
            Interface(
                id="r1-eth0",
                name="eth0",
                ipv4_addresses=[ip_interface("192.0.2.1/24")],
                ipv6_addresses=[ip_interface("2001:db8:1::1/64")],
            ),
            Interface(
                id="r1-eth1",
                name="eth1",
                ipv4_addresses=[ip_interface("198.51.100.1/24")],
                ipv6_addresses=[ip_interface("2001:db8:2::1/64")],
            ),
        ],
        static_routes=[
            StaticRoute(
                id="router-route-v4",
                destination=ip_network("203.0.113.0/24"),
                next_hop=ip_address("198.51.100.254"),
                outgoing_interface_id="r1-eth1",
                metric=10,
            )
        ],
    )
    switch = Switch(
        id="s1",
        name="Switch 1",
        interfaces=[Interface(id="s1-eth1", name="eth0")],
    )

    topology.add_node(host)
    topology.add_node(router)
    topology.add_node(switch)
    topology.add_link(
        Link(
            id="h1-r1",
            source_interface_id="h1-eth0",
            destination_interface_id="r1-eth0",
            forward=make_direction(),
            reverse=make_direction(),
        )
    )
    topology.add_link(
        Link(
            id="r1-s1",
            source_interface_id="r1-eth1",
            destination_interface_id="s1-eth1",
            forward=make_direction(),
            reverse=make_direction(),
        )
    )
    return topology


def test_materializes_host_router_and_switch_with_openflow13(mininet_api):
    net = create_mininet_network(
        make_topology(),
        controller_ip="127.0.0.1",
        mininet_api=mininet_api,
    )

    assert net.built
    assert {name for name, _ in net.hosts} == {"h1", "r1"}
    assert net.hosts[1][1]["cls"] is FakeLinuxRouter
    assert net.hosts[1][1]["ipv4_forwarding"] is True
    assert net.hosts[1][1]["ipv6_forwarding"] is True
    assert net.switches == [("s1", {"protocols": "OpenFlow13"})]
    assert len(net.links) == 2


def test_configures_ipv4_ipv6_and_static_routes_on_host_and_router(mininet_api):
    net = create_mininet_network(
        make_topology(),
        controller_ip="127.0.0.1",
        mininet_api=mininet_api,
    )

    host_commands = "\n".join(net.get("h1").commands)
    router_commands = "\n".join(net.get("r1").commands)

    assert "ip -4 addr replace 192.0.2.10/24 dev h1-eth0" in host_commands
    assert "ip -6 addr replace 2001:db8:1::10/64 dev h1-eth0" in host_commands
    assert "ip -4 route replace 198.51.100.0/24 via 192.0.2.1 dev h1-eth0 metric 20" in host_commands
    assert "ip -6 route replace 2001:db8:2::/64 via 2001:db8:1::1 dev h1-eth0 metric 30" in host_commands

    assert "ip -4 addr replace 192.0.2.1/24 dev r1-eth0" in router_commands
    assert "ip -6 addr replace 2001:db8:1::1/64 dev r1-eth0" in router_commands
    assert "ip -4 addr replace 198.51.100.1/24 dev r1-eth1" in router_commands
    assert "ip -6 addr replace 2001:db8:2::1/64 dev r1-eth1" in router_commands
    assert "ip -4 route replace 203.0.113.0/24 via 198.51.100.254 dev r1-eth1 metric 10" in router_commands


def test_router_without_mininet_injected_class_raises_clear_error(monkeypatch):
    topology = make_topology()
    api_without_router_class = SimpleNamespace(
        Mininet=FakeNetwork,
        OVSSwitch=FakeOVSSwitch,
        RemoteController=FakeRemoteController,
        TCLink=FakeTCLink,
    )

    # This test exercises the lazy import failure on environments without Mininet.
    import builtins
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "mininet.node":
            raise ImportError("Mininet not installed in test environment")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(RuntimeError, match="Mininet is required to materialize Router"):
        create_mininet_network(
            topology,
            controller_ip="127.0.0.1",
            mininet_api=api_without_router_class,
        )


def test_rejects_route_interface_not_owned_by_node(mininet_api):
    topology = make_topology()
    router = topology.get_node("r1")
    router.static_routes[0].outgoing_interface_id = "h1-eth0"
    # Rebuild the aggregate because getters return defensive copies.
    rebuilt = Topology(topology.metadata)
    for node in topology.nodes.values():
        if node.id == "r1":
            node.static_routes[0].outgoing_interface_id = "h1-eth0"
        rebuilt.add_node(node)
    for link in topology.links.values():
        rebuilt.add_link(link)

    with pytest.raises(MininetAdapterError, match="does not belong to that node"):
        create_mininet_network(
            rebuilt,
            controller_ip="127.0.0.1",
            mininet_api=mininet_api,
        )


def test_rejects_address_on_unmaterialized_interface(mininet_api):
    topology = make_topology(with_host_route=False)
    rebuilt = Topology(topology.metadata)
    for node in topology.nodes.values():
        if node.id == "h1":
            node.interfaces.append(
                Interface(
                    id="h1-eth1",
                    name="eth1",
                    ipv4_addresses=[ip_interface("203.0.113.10/24")],
                )
            )
        rebuilt.add_node(node)
    for link in topology.links.values():
        rebuilt.add_link(link)

    with pytest.raises(MininetAdapterError, match="not connected by an active link"):
        create_mininet_network(
            rebuilt,
            controller_ip="127.0.0.1",
            mininet_api=mininet_api,
        )


def make_link_topology(
    *,
    link_status=LinkStatus.UP,
    source_status=InterfaceStatus.UP,
    destination_status=InterfaceStatus.UP,
    forward_enabled=True,
    reverse_enabled=True,
    reverse_exists=True,
    forward_bandwidth=100,
    forward_delay=2,
    forward_loss=1,
    reverse_bandwidth=200,
    reverse_delay=5,
    reverse_loss=3,
):
    """Build a minimal Host-Switch topology for link behavior tests."""
    topology = Topology(Metadata(id="link-test", name="Link Adapter Test"))

    host = Host(
        id="h1",
        name="Host 1",
        interfaces=[
            Interface(id="h1-eth0", name="eth0", status=source_status)
        ],
    )
    switch = Switch(
        id="s1",
        name="Switch 1",
        interfaces=[
            Interface(id="s1-eth1", name="eth0", status=destination_status)
        ],
    )

    topology.add_node(host)
    topology.add_node(switch)
    topology.add_link(
        Link(
            id="h1-s1",
            source_interface_id="h1-eth0",
            destination_interface_id="s1-eth1",
            status=link_status,
            forward=make_direction(
                enabled=forward_enabled,
                bandwidth=forward_bandwidth,
                delay=forward_delay,
                loss=forward_loss,
            ),
            reverse=(
                make_direction(
                    enabled=reverse_enabled,
                    bandwidth=reverse_bandwidth,
                    delay=reverse_delay,
                    loss=reverse_loss,
                )
                if reverse_exists
                else None
            ),
        )
    )
    return topology


def test_does_not_materialize_link_with_down_status(mininet_api):
    topology = make_link_topology(link_status=LinkStatus.DOWN)
    net = create_mininet_network(
        topology, controller_ip="127.0.0.1", mininet_api=mininet_api
    )
    assert net.built
    assert net.links == []


def test_does_not_materialize_link_with_down_source_interface(mininet_api):
    topology = make_link_topology(source_status=InterfaceStatus.DOWN)
    net = create_mininet_network(
        topology, controller_ip="127.0.0.1", mininet_api=mininet_api
    )
    assert net.built
    assert net.links == []


def test_does_not_materialize_link_with_down_destination_interface(mininet_api):
    topology = make_link_topology(destination_status=InterfaceStatus.DOWN)
    net = create_mininet_network(
        topology, controller_ip="127.0.0.1", mininet_api=mininet_api
    )
    assert net.built
    assert net.links == []


def test_does_not_materialize_link_when_both_directions_disabled(mininet_api):
    topology = make_link_topology(
        forward_enabled=False, reverse_enabled=False
    )
    net = create_mininet_network(
        topology, controller_ip="127.0.0.1", mininet_api=mininet_api
    )
    assert net.built
    assert net.links == []


def test_rejects_link_with_only_one_enabled_direction(mininet_api):
    topology = make_link_topology(
        forward_enabled=True, reverse_enabled=False
    )
    with pytest.raises(
        MininetAdapterError, match="only one enabled direction"
    ):
        create_mininet_network(
            topology, controller_ip="127.0.0.1", mininet_api=mininet_api
        )


def test_rejects_link_without_reverse_direction(mininet_api):
    topology = make_link_topology(reverse_exists=False)
    with pytest.raises(
        MininetAdapterError, match="no declared reverse direction"
    ):
        create_mininet_network(
            topology, controller_ip="127.0.0.1", mininet_api=mininet_api
        )


def test_preserves_asymmetric_link_parameters(mininet_api):
    topology = make_link_topology(
        forward_bandwidth=100,
        forward_delay=2,
        forward_loss=1,
        reverse_bandwidth=200,
        reverse_delay=5,
        reverse_loss=3,
    )
    net = create_mininet_network(
        topology, controller_ip="127.0.0.1", mininet_api=mininet_api
    )

    assert len(net.links) == 1
    source, destination, params = net.links[0]
    assert source == "h1"
    assert destination == "s1"
    assert params["params1"] == {
        "bw": 100,
        "delay": "2ms",
        "loss": 1,
    }
    assert params["params2"] == {
        "bw": 200,
        "delay": "5ms",
        "loss": 3,
    }


def make_port_topology(
    *,
    host_interface_names=("eth0", "eth1"),
    switch_interface_names=("eth0", "eth1"),
    links=((0, 0), (1, 1)),
):
    """Build a topology with multiple interfaces to verify Mininet port mapping."""
    topology = Topology(
        Metadata(id="port-test", name="Port Mapping Test")
    )

    host = Host(
        id="h1",
        name="Host 1",
        interfaces=[
            Interface(
                id=f"h1-if-{index}",
                name=name,
            )
            for index, name in enumerate(host_interface_names)
        ],
    )
    switch = Switch(
        id="s1",
        name="Switch 1",
        interfaces=[
            Interface(
                id=f"s1-if-{index}",
                name=name,
            )
            for index, name in enumerate(switch_interface_names)
        ],
    )

    topology.add_node(host)
    topology.add_node(switch)

    for host_index, switch_index in links:
        topology.add_link(
            Link(
                id=f"link-{host_index}-{switch_index}",
                source_interface_id=f"h1-if-{host_index}",
                destination_interface_id=f"s1-if-{switch_index}",
                forward=make_direction(),
                reverse=make_direction(),
            )
        )

    return topology


def test_maps_host_and_switch_interfaces_to_mininet_ports(mininet_api):
    topology = make_port_topology()

    net = create_mininet_network(
        topology,
        controller_ip="127.0.0.1",
        mininet_api=mininet_api,
    )

    assert len(net.links) == 2

    first_link = net.links[0][2]
    second_link = net.links[1][2]

    # Host eth0/eth1 map to ports 0/1; Switch eth0/eth1 map to 1/2.
    assert first_link["port1"] == 0
    assert first_link["port2"] == 1
    assert second_link["port1"] == 1
    assert second_link["port2"] == 2


@pytest.mark.parametrize(
    ("host_names", "switch_names"),
    [
        (("ens3", "eth1"), ("eth0", "eth1")),
        (("eth0", "eth1"), ("port1", "eth1")),
    ],
)
def test_rejects_interface_names_outside_eth_number_pattern(
    mininet_api, host_names, switch_names
):
    topology = make_port_topology(
        host_interface_names=host_names,
        switch_interface_names=switch_names,
        links=(),
    )

    with pytest.raises(
        MininetAdapterError,
        match="Expected ethN",
    ):
        create_mininet_network(
            topology,
            controller_ip="127.0.0.1",
            mininet_api=mininet_api,
        )


@pytest.mark.parametrize(
    ("host_names", "switch_names", "expected_node"),
    [
        (("eth0", "eth00"), ("eth0", "eth1"), "h1"),
        (("eth0", "eth1"), ("eth0", "eth00"), "s1"),
    ],
)
def test_rejects_colliding_mininet_port_mappings(
    mininet_api, host_names, switch_names, expected_node
):
    topology = make_port_topology(
        host_interface_names=host_names,
        switch_interface_names=switch_names,
        links=(),
    )

    with pytest.raises(
        MininetAdapterError,
        match=f"Node '{expected_node}'.*same Mininet port",
    ):
        create_mininet_network(
            topology,
            controller_ip="127.0.0.1",
            mininet_api=mininet_api,
        )


def test_preserves_explicit_port_numbers_when_materializing_links(mininet_api):
    topology = make_port_topology(
        host_interface_names=("eth2", "eth4"),
        switch_interface_names=("eth2", "eth4"),
        links=((0, 1), (1, 0)),
    )

    net = create_mininet_network(
        topology,
        controller_ip="127.0.0.1",
        mininet_api=mininet_api,
    )

    assert len(net.links) == 2
    assert net.links[0][2]["port1"] == 2
    assert net.links[0][2]["port2"] == 5
    assert net.links[1][2]["port1"] == 4
    assert net.links[1][2]["port2"] == 3



def make_fault_injection_api(*, fail_at=None, fail_stop=False, fail_command=None):
    """Create a Mininet API fake that can fail at a selected construction step."""

    class FaultInjectingNode(FakeNode):
        def cmd(self, command):
            self.commands.append(command)
            if fail_command and fail_command in command:
                return f"simulated command failure\n__MININET_ADAPTER_RC__7"
            return ""

    class FaultInjectingNetwork(FakeNetwork):
        instance = None

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.__class__.instance = self

        def _maybe_fail(self, operation):
            if fail_at == operation:
                raise RuntimeError(f"injected {operation} failure")

        def addHost(self, name, **kwargs):
            self._maybe_fail("addHost")
            self.hosts.append((name, kwargs))
            node = FaultInjectingNode(name)
            self.nodes[name] = node
            return node

        def addSwitch(self, name, **kwargs):
            self._maybe_fail("addSwitch")
            self.switches.append((name, kwargs))
            node = FaultInjectingNode(name)
            self.nodes[name] = node
            return node

        def addController(self, name, **kwargs):
            self._maybe_fail("addController")
            self.controllers.append((name, kwargs))

        def addLink(self, source, destination, **kwargs):
            self._maybe_fail("addLink")
            self.links.append((source, destination, kwargs))

        def build(self):
            self._maybe_fail("build")
            self.built = True

        def stop(self):
            self.stopped = True
            if fail_stop:
                raise RuntimeError("injected stop failure")

    api = SimpleNamespace(
        Mininet=FaultInjectingNetwork,
        OVSSwitch=FakeOVSSwitch,
        RemoteController=FakeRemoteController,
        TCLink=FakeTCLink,
        LinuxRouter=FakeLinuxRouter,
    )
    return api, FaultInjectingNetwork


@pytest.mark.parametrize(
    "failure_stage",
    ["addHost", "addSwitch", "addController", "addLink", "build"],
)
def test_stops_network_when_mininet_construction_step_fails(failure_stage):
    api, network_class = make_fault_injection_api(fail_at=failure_stage)

    with pytest.raises(
        RuntimeError,
        match=f"injected {failure_stage} failure",
    ):
        create_mininet_network(
            make_link_topology(),
            controller_ip="127.0.0.1",
            mininet_api=api,
        )

    assert network_class.instance is not None
    assert network_class.instance.stopped is True


def test_stops_network_when_interface_configuration_command_fails():
    api, network_class = make_fault_injection_api(
        fail_command="ip -4 addr replace",
    )

    with pytest.raises(
        MininetAdapterError,
        match="Failed while configuring IPv4 address",
    ):
        create_mininet_network(
            make_topology(),
            controller_ip="127.0.0.1",
            mininet_api=api,
        )

    assert network_class.instance.stopped is True


def test_stops_network_when_static_route_installation_fails():
    api, network_class = make_fault_injection_api(
        fail_command="ip -4 route replace",
    )

    with pytest.raises(
        MininetAdapterError,
        match="Failed while installing static route",
    ):
        create_mininet_network(
            make_topology(),
            controller_ip="127.0.0.1",
            mininet_api=api,
        )

    assert network_class.instance.stopped is True


def test_preserves_original_exception_when_network_cleanup_also_fails():
    api, network_class = make_fault_injection_api(
        fail_at="build",
        fail_stop=True,
    )

    with pytest.raises(
        RuntimeError,
        match="injected build failure",
    ):
        create_mininet_network(
            make_link_topology(),
            controller_ip="127.0.0.1",
            mininet_api=api,
        )

    assert network_class.instance.stopped is True


# Real Mininet integration test:
# runs only on Linux, as root, with the Mininet Python package installed.
_REAL_MININET_AVAILABLE = (
    sys.platform.startswith("linux")
    and hasattr(os, "geteuid")
    and os.geteuid() == 0
    and importlib.util.find_spec("mininet") is not None
)


@pytest.mark.skipif(
    not _REAL_MININET_AVAILABLE,
    reason="Requires Linux, root privileges, and an installed Mininet package.",
)
def test_real_mininet_builds_host_link_and_reaches_peer():
    """Exercise actual Linux namespaces, veth interfaces, and host connectivity."""
    topology = Topology(
        Metadata(id="real-mininet-smoke", name="Real Mininet Smoke Test")
    )

    host1 = Host(
        id="h1",
        name="Host 1",
        interfaces=[
            Interface(
                id="h1-eth0",
                name="eth0",
                ipv4_addresses=[ip_interface("192.0.2.1/24")],
            )
        ],
    )
    host2 = Host(
        id="h2",
        name="Host 2",
        interfaces=[
            Interface(
                id="h2-eth0",
                name="eth0",
                ipv4_addresses=[ip_interface("192.0.2.2/24")],
            )
        ],
    )

    topology.add_node(host1)
    topology.add_node(host2)
    topology.add_link(
        Link(
            id="h1-h2",
            source_interface_id="h1-eth0",
            destination_interface_id="h2-eth0",
            forward=make_direction(),
            reverse=make_direction(),
        )
    )

    net = create_mininet_network(
        topology,
        controller_ip="127.0.0.1",
    )

    try:
        net.start()

        h1 = net.get("h1")
        h2 = net.get("h2")

        assert "192.0.2.1/24" in h1.cmd("ip -4 -o addr show dev h1-eth0")
        assert "192.0.2.2/24" in h2.cmd("ip -4 -o addr show dev h2-eth0")

        ping_status = h1.cmd(
            "ping -c 1 -W 2 -n 192.0.2.2 >/dev/null 2>&1; "
            "printf '%s' $?"
        ).strip()

        assert ping_status == "0", (
            f"Host h1 could not reach 192.0.2.2. "
            f"Ping exit status: {ping_status}"
        )
    finally:
        net.stop()

