
import pytest

from framework.core.topology.enums import TopologySource
from framework.core.topology.exceptions import TopologyValidationError
from framework.core.topology.models import (
    Host,
    Link,
    Metadata,
    Metrics,
    Policy,
    Switch,
)
from framework.core.topology.topology import Topology
from framework.core.topology.validator import validate_topology


def create_topology() -> Topology:
    """Create a small synthetic topology for domain tests."""
    metadata = Metadata(
        id="topology-test",
        name="Test topology",
        topology_source=TopologySource.SYNTHETIC,
    )
    return Topology(metadata=metadata)


def create_switch(node_id: str = "s1") -> Switch:
    return Switch(id=node_id, name=f"Switch {node_id}")


def create_host(node_id: str = "h1") -> Host:
    return Host(id=node_id, name=f"Host {node_id}")


def create_link(
    link_id: str = "l1",
    source: str = "s1",
    destination: str = "h1",
) -> Link:
    return Link(
        id=link_id,
        source=source,
        destination=destination,
    )


def test_add_and_get_node():
    topology = create_topology()
    switch = create_switch()

    topology.add_node(switch)

    assert topology.has_node("s1")
    assert topology.get_node("s1").id == "s1"
    assert len(topology) == 1


def test_add_duplicate_node_raises_value_error():
    topology = create_topology()
    topology.add_node(create_switch())

    with pytest.raises(ValueError, match="already exists"):
        topology.add_node(create_switch())


def test_add_non_node_raises_type_error():
    topology = create_topology()

    with pytest.raises(TypeError, match="Node"):
        topology.add_node("not-a-node")


def test_add_link_requires_existing_endpoints():
    topology = create_topology()
    topology.add_node(create_switch())

    with pytest.raises(ValueError, match="Destination node"):
        topology.add_link(create_link(destination="missing-host"))


def test_add_self_link_raises_value_error():
    topology = create_topology()
    topology.add_node(create_switch())

    with pytest.raises(ValueError, match="itself"):
        topology.add_link(create_link(source="s1", destination="s1"))


def test_remove_node_referenced_by_link_raises_value_error():
    topology = create_topology()
    topology.add_node(create_switch())
    topology.add_node(create_host())
    topology.add_link(create_link())

    with pytest.raises(ValueError, match="referenced by link"):
        topology.remove_node("s1")

    assert topology.has_node("s1")
    assert topology.has_link("l1")


def test_add_duplicate_link_raises_value_error():
    topology = create_topology()
    topology.add_node(create_switch())
    topology.add_node(create_host())
    topology.add_link(create_link())

    with pytest.raises(ValueError, match="already exists"):
        topology.add_link(create_link())


def test_add_duplicate_policy_raises_value_error():
    topology = create_topology()
    policy = Policy(id="p1", name="Policy 1")
    topology.add_policy(policy)

    with pytest.raises(ValueError, match="already exists"):
        topology.add_policy(policy)


def test_node_returned_by_get_node_is_a_defensive_copy():
    topology = create_topology()
    topology.add_node(create_switch())

    retrieved = topology.get_node("s1")
    retrieved.name = "Modified outside the topology"

    assert topology.get_node("s1").name == "Switch s1"


def test_metrics_are_copied_when_set_and_retrieved():
    topology = create_topology()
    metrics = Metrics(values={"latency_ms": 2.5})

    topology.set_metrics(metrics)
    metrics.values["latency_ms"] = 99.0

    retrieved = topology.metrics
    assert retrieved.values["latency_ms"] == 2.5

    retrieved.values["latency_ms"] = 50.0
    assert topology.metrics.values["latency_ms"] == 2.5


def test_set_metrics_rejects_invalid_type():
    topology = create_topology()

    with pytest.raises(TypeError, match="Metrics"):
        topology.set_metrics({"latency_ms": 2.5})


def test_validate_topology_accepts_valid_topology():
    topology = create_topology()
    topology.add_node(create_switch())
    topology.add_node(create_host())
    topology.add_link(create_link())

    assert validate_topology(topology) is None
    assert topology.is_structurally_valid()


def test_validate_topology_rejects_invalid_object():
    with pytest.raises(TypeError, match="Topology"):
        validate_topology("not-a-topology")
