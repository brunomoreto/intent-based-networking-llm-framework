
import pytest

from framework.core.topology.enums import NodeType, TopologySource
from framework.services.collector.onos_topology_adapter import (
    OnosTopologyAdapterError,
    topology_from_onos,
)


def device(device_id):
    return {
        "id": device_id,
        "available": True,
        "type": "SWITCH",
        "mfr": "Open vSwitch",
        "hw": "Open vSwitch",
        "sw": "2.17.12",
        "humanReadableName": device_id,
    }


def link(source, source_port, destination, destination_port):
    return {
        "src": {"device": source, "port": source_port},
        "dst": {"device": destination, "port": destination_port},
        "type": "DIRECT",
        "state": "ACTIVE",
    }


def test_converts_devices_and_links():
    topology = topology_from_onos(
        devices=[device("of:1"), device("of:2")],
        links=[link("of:1", "1", "of:2", "2")],
    )

    assert len(topology.nodes) == 2
    assert len(topology.links) == 1
    assert topology.metadata.topology_source == TopologySource.PRODUCTION
    assert topology.get_node("of:1").node_type == NodeType.SWITCH


def test_empty_response_produces_empty_topology():
    topology = topology_from_onos(devices=[], links=[])

    assert len(topology.nodes) == 0
    assert len(topology.links) == 0


def test_rejects_duplicate_device_ids():
    with pytest.raises(OnosTopologyAdapterError, match="Duplicate"):
        topology_from_onos(
            devices=[device("of:1"), device("of:1")],
            links=[],
        )


def test_rejects_link_with_unknown_device():
    with pytest.raises(OnosTopologyAdapterError, match="unknown device"):
        topology_from_onos(
            devices=[device("of:1")],
            links=[link("of:1", "1", "of:2", "2")],
        )


def test_rejects_link_without_port():
    invalid_link = {
        "src": {"device": "of:1"},
        "dst": {"device": "of:2", "port": "2"},
    }

    with pytest.raises(OnosTopologyAdapterError, match="port"):
        topology_from_onos(
            devices=[device("of:1"), device("of:2")],
            links=[invalid_link],
        )


def test_rejects_malformed_device():
    with pytest.raises(OnosTopologyAdapterError, match="device.id"):
        topology_from_onos(
            devices=[{"available": True}],
            links=[],
        )
