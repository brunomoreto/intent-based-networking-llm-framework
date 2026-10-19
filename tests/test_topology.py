
import pytest
from copy import deepcopy

from pathlib import Path

from framework.core.topology.serialization import load_topology
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



def test_metadata_is_protected_from_external_mutation():
    topology = create_topology()

    metadata = topology.metadata
    metadata.name = "Changed name"
    metadata.tags.append("external-change")

    assert topology.metadata.name == "Test topology"
    assert "external-change" not in topology.metadata.tags


def test_nodes_mapping_is_read_only():
    topology = create_topology()
    topology.add_node(create_switch())

    with pytest.raises(TypeError):
        topology.nodes["h1"] = create_host()


def test_nested_node_attributes_are_defensive_copies():
    topology = create_topology()
    switch = Switch(
        id="s1",
        name="Switch s1",
        attributes={"config": {"priority": 10}},
    )
    topology.add_node(switch)

    retrieved = topology.get_node("s1")
    retrieved.attributes["config"]["priority"] = 99

    assert topology.get_node("s1").attributes["config"]["priority"] == 10


def test_link_returned_by_get_link_is_a_defensive_copy():
    topology = create_topology()
    topology.add_node(create_switch())
    topology.add_node(create_host())
    topology.add_link(
        Link(
            id="l1",
            source="s1",
            destination="h1",
            attributes={"labels": ["original"]},
        )
    )

    retrieved = topology.get_link("l1")
    retrieved.attributes["labels"].append("external")

    assert topology.get_link("l1").attributes["labels"] == ["original"]


def test_policy_returned_by_get_policy_is_a_defensive_copy():
    topology = create_topology()
    topology.add_policy(
        Policy(
            id="p1",
            name="Policy 1",
            attributes={"rules": ["allow"]},
        )
    )

    retrieved = topology.get_policy("p1")
    retrieved.attributes["rules"].append("deny")

    assert topology.get_policy("p1").attributes["rules"] == ["allow"]


def test_remove_link_allows_removing_its_endpoints():
    topology = create_topology()
    topology.add_node(create_switch())
    topology.add_node(create_host())
    topology.add_link(create_link())

    topology.remove_link("l1")

    assert not topology.has_link("l1")
    assert topology.is_structurally_valid()

    topology.remove_node("s1")

    assert not topology.has_node("s1")
    assert topology.is_structurally_valid()


def test_get_missing_node_raises_key_error():
    topology = create_topology()

    with pytest.raises(KeyError, match="does not exist"):
        topology.get_node("missing")


def test_remove_missing_link_raises_key_error():
    topology = create_topology()

    with pytest.raises(KeyError, match="does not exist"):
        topology.remove_link("missing")


def test_remove_policy():
    topology = create_topology()
    topology.add_policy(Policy(id="p1", name="Policy 1"))

    topology.remove_policy("p1")

    assert not topology.has_policy("p1")


def test_iteration_returns_nodes_without_exposing_internal_objects():
    topology = create_topology()
    topology.add_node(create_switch())
    topology.add_node(create_host())

    nodes = list(topology)
    nodes[0].name = "Changed externally"

    assert topology.get_node(nodes[0].id).name != "Changed externally"


def test_has_methods_return_false_for_missing_ids():
    topology = create_topology()

    assert not topology.has_node("missing-node")
    assert not topology.has_link("missing-link")
    assert not topology.has_policy("missing-policy")


def test_get_missing_link_raises_key_error():
    topology = create_topology()

    with pytest.raises(KeyError, match="does not exist"):
        topology.get_link("missing-link")


def test_get_missing_policy_raises_key_error():
    topology = create_topology()

    with pytest.raises(KeyError, match="does not exist"):
        topology.get_policy("missing-policy")


def test_remove_missing_node_raises_key_error():
    topology = create_topology()

    with pytest.raises(KeyError, match="does not exist"):
        topology.remove_node("missing-node")


def test_remove_missing_policy_raises_key_error():
    topology = create_topology()

    with pytest.raises(KeyError, match="does not exist"):
        topology.remove_policy("missing-policy")


def test_add_link_with_missing_source_raises_value_error():
    topology = create_topology()
    topology.add_node(create_host())

    with pytest.raises(ValueError, match="Source node"):
        topology.add_link(
            create_link(source="missing-switch", destination="h1")
        )


def test_add_non_link_raises_type_error():
    topology = create_topology()

    with pytest.raises(TypeError, match="Link"):
        topology.add_link("not-a-link")


def test_add_non_policy_raises_type_error():
    topology = create_topology()

    with pytest.raises(TypeError, match="Policy"):
        topology.add_policy("not-a-policy")


def test_remove_link_preserves_remaining_topology():
    topology = create_topology()
    topology.add_node(create_switch())
    topology.add_node(create_host())
    topology.add_link(create_link())
    topology.add_link(
        create_link(
            link_id="l2",
            source="s1",
            destination="h1",
        )
    )

    topology.remove_link("l1")

    assert not topology.has_link("l1")
    assert topology.has_link("l2")
    assert topology.has_node("s1")
    assert topology.has_node("h1")
    assert topology.is_structurally_valid()

def test_link_failure_does_not_modify_original_topology():
    dataset_path = (
        Path(__file__).resolve().parents[1]
        / "datasets"
        / "n1"
        / "redundant_topology.json"
    )

    original = load_topology(dataset_path)
    experiment = deepcopy(original)

    original_link_ids = set(original.links)

    experiment.remove_link("l2")

    assert not experiment.has_link("l2")
    assert set(original.links) == original_link_ids
    assert original.has_link("l2")
    assert experiment.is_structurally_valid()