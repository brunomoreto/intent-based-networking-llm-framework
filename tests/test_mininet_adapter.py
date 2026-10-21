
from types import SimpleNamespace

import pytest

from framework.core.topology.enums import LinkStatus
from framework.core.topology.serialization import load_topology
from framework.integrations.mininet.adapter import (
    MininetAdapterError,
    create_mininet_network,
)


DATASET = "datasets/n1/redundant_topology.json"


class FakeNetwork:
    def __init__(self, **kwargs):
        self.options = kwargs
        self.hosts = []
        self.switches = []
        self.controllers = []
        self.links = []
        self.built = False
        self.stopped = False

    def addHost(self, name, **kwargs):
        self.hosts.append((name, kwargs))

    def addSwitch(self, name, **kwargs):
        self.switches.append((name, kwargs))

    def addController(self, name, **kwargs):
        self.controllers.append((name, kwargs))

    def addLink(self, source, destination, **kwargs):
        self.links.append((source, destination, kwargs))

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
