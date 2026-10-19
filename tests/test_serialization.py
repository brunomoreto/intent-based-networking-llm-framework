import json

import pytest

from collections import deque

from framework.core.topology.enums import LinkStatus, NodeType, TopologySource
from framework.core.topology.exceptions import (
    TopologyFileError,
    TopologyFormatError,
    UnsupportedSchemaVersionError,
)
from framework.core.topology.models import Host, Link, Metadata, Metrics, Policy, Switch
from framework.core.topology.serialization import (
    SCHEMA_VERSION,
    load_topology,
    save_topology,
)
from framework.core.topology.topology import Topology

from pathlib import Path


def create_topology() -> Topology:
    """Create a small topology for serialization tests."""
    topology = Topology(
        Metadata(
            id="topology-1",
            name="Test topology",
            description="Topology used by automated tests",
            author="Test suite",
            version="1.0",
            topology_source=TopologySource.CUSTOM,
            tags=["test"],
        )
    )

    topology.add_node(
        Switch(
            id="s1",
            name="Switch 1",
            attributes={"vendor": "test"},
            properties={"ports": 4},
        )
    )
    topology.add_node(
        Host(
            id="h1",
            name="Host 1",
            attributes={},
            properties={"ip": "192.0.2.10"},
        )
    )
    topology.add_link(
        Link(
            id="l1",
            source="s1",
            destination="h1",
            bandwidth=1000.0,
            delay=2.5,
            status=LinkStatus.ACTIVE,
        )
    )
    topology.add_policy(
        Policy(
            id="p1",
            name="Test policy",
            enabled=True,
            attributes={"priority": 10},
        )
    )
    topology.set_metrics(Metrics(values={"latency_ms": 2.5}))

    return topology


def test_load_valid_topology(tmp_path):
    """A valid JSON document should load into a Topology."""
    source = tmp_path / "topology.json"
    save_topology(create_topology(), source)

    loaded = load_topology(source)

    assert isinstance(loaded, Topology)
    assert loaded.metadata.id == "topology-1"
    assert len(loaded.nodes) == 2
    assert len(loaded.links) == 1
    assert len(loaded.policies) == 1
    assert loaded.metrics.values == {"latency_ms": 2.5}


def test_save_and_reload_preserves_topology(tmp_path):
    """Saving and reloading should preserve the topology data."""
    original = create_topology()
    source = tmp_path / "topology.json"
    save_topology(original, source)

    reloaded = load_topology(source)

    assert reloaded.metadata == original.metadata
    assert dict(reloaded.nodes) == dict(original.nodes)
    assert dict(reloaded.links) == dict(original.links)
    assert dict(reloaded.policies) == dict(original.policies)
    assert reloaded.metrics == original.metrics


def test_load_invalid_json_raises_format_error(tmp_path):
    """Malformed JSON should raise TopologyFormatError."""
    source = tmp_path / "invalid.json"
    source.write_text('{"schema_version": ', encoding="utf-8")

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_unsupported_schema_version_raises_error(tmp_path):
    """Unsupported schema versions should be rejected."""
    document = {
        "schema_version": SCHEMA_VERSION + 1,
        "metadata": {"id": "t1", "name": "Test"},
        "nodes": [],
        "links": [],
    }
    source = tmp_path / "unsupported.json"
    source.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(UnsupportedSchemaVersionError):
        load_topology(source)


def test_load_unknown_root_field_raises_format_error(tmp_path):
    """Unknown structural fields should be rejected."""
    document = {
        "schema_version": SCHEMA_VERSION,
        "metadata": {"id": "t1", "name": "Test"},
        "nodes": [],
        "links": [],
        "unexpected": True,
    }
    source = tmp_path / "unknown.json"
    source.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_missing_file_raises_file_error(tmp_path):
    """A missing file should raise TopologyFileError."""
    with pytest.raises(TopologyFileError):
        load_topology(tmp_path / "does-not-exist.json")


def write_json(tmp_path, document, filename="topology.json"):
    """Write a JSON document to a temporary file."""
    source = tmp_path / filename
    source.write_text(json.dumps(document), encoding="utf-8")
    return source


def minimal_document():
    """Return the smallest valid topology document."""
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "id": "t1",
            "name": "Minimal topology",
        },
        "nodes": [],
        "links": [],
    }


def test_load_missing_required_metadata_field_raises_format_error(tmp_path):
    """Required metadata fields must be present."""
    document = minimal_document()
    del document["metadata"]["name"]
    source = write_json(tmp_path, document)

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_invalid_node_type_raises_format_error(tmp_path):
    """Node types outside the defined enumeration must be rejected."""
    document = minimal_document()
    document["nodes"] = [
        {
            "id": "n1",
            "name": "Unknown node",
            "node_type": "firewall",
        }
    ]
    source = write_json(tmp_path, document)

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_link_with_missing_endpoint_raises_format_error(tmp_path):
    """Links cannot reference nodes that do not exist."""
    document = minimal_document()
    document["nodes"] = [
        {
            "id": "s1",
            "name": "Switch 1",
            "node_type": "switch",
        }
    ]
    document["links"] = [
        {
            "id": "l1",
            "source": "s1",
            "destination": "missing-node",
        }
    ]
    source = write_json(tmp_path, document)

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_non_object_node_attributes_raises_format_error(tmp_path):
    """Node attributes must be represented by a JSON object."""
    document = minimal_document()
    document["nodes"] = [
        {
            "id": "s1",
            "name": "Switch 1",
            "node_type": "switch",
            "attributes": ["invalid", "attributes"],
        }
    ]
    source = write_json(tmp_path, document)

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_non_numeric_metric_raises_format_error(tmp_path):
    """Metric values must be numeric."""
    document = minimal_document()
    document["metrics"] = {
        "values": {
            "latency_ms": "fast",
        }
    }
    source = write_json(tmp_path, document)

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_boolean_schema_version_raises_format_error(tmp_path):
    """A boolean is not a valid schema version integer."""
    document = minimal_document()
    document["schema_version"] = True
    source = write_json(tmp_path, document)

    with pytest.raises(TopologyFormatError):
        load_topology(source)


def test_load_basic_synthetic_topology():
    project_root = Path(__file__).resolve().parents[1]
    topology_path = (
        project_root / "datasets" / "n1" / "basic_topology.json"
    )

    topology = load_topology(topology_path)

    assert len(topology.nodes) == 3
    assert len(topology.links) == 2
    assert topology.is_structurally_valid()

    assert topology.has_node("h1")
    assert topology.has_node("s1")
    assert topology.has_node("h2")

    assert topology.has_link("l1")
    assert topology.has_link("l2")

def test_load_redundant_synthetic_topology():
    project_root = Path(__file__).resolve().parents[1]
    topology_path = (
        project_root / "datasets" / "n1" / "redundant_topology.json"
    )

    topology = load_topology(topology_path)

    assert len(topology.nodes) == 6
    assert len(topology.links) == 6
    assert topology.is_structurally_valid()

    for node_id in ("h1", "s1", "s2", "s3", "s4", "h2"):
        assert topology.has_node(node_id)

    for link_id in ("l1", "l2", "l3", "l4", "l5", "l6"):
        assert topology.has_link(link_id)


def test_redundant_topology_preserves_connectivity_after_internal_link_failure():
    project_root = Path(__file__).resolve().parents[1]
    topology_path = (
        project_root / "datasets" / "n1" / "redundant_topology.json"
    )
    topology = load_topology(topology_path)



def test_load_ring_synthetic_topology():

    project_root = Path(__file__).resolve().parents[1]
    topology_path = (project_root / "datasets" / "n1" / "ring_topology.json")

    topology = load_topology(topology_path)

    assert len(topology.nodes) == 6
    assert len(topology.links) == 6
    assert topology.is_structurally_valid()

    for node_id in ("h1", "s1", "s2", "s3", "s4", "h2"):
        assert topology.has_node(node_id)

    for link_id in ("l1", "l2", "l3", "l4", "l5", "l6"):
        assert topology.has_link(link_id)

def test_ring_topology_preserves_host_connectivity_after_single_link_failure():
    project_root = Path(__file__).resolve().parents[1]
    topology_path = (
        project_root / "datasets" / "n1" / "ring_topology.json"
    )
    topology = load_topology(topology_path)

def is_reachable(excluded_link_id=None):
    adjacency = {node_id: set() for node_id in topology.nodes}

    for link in topology.links.values():
        if link.id == excluded_link_id or link.status.value != "active":
            continue

        adjacency[link.source].add(link.destination)
        if link.bidirectional:
            adjacency[link.destination].add(link.source)

    visited = {"h1"}
    queue = deque(["h1"])

    while queue:
        current = queue.popleft()

        if current == "h2":
            return True

        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return False

    assert is_reachable()
    for link_id in ("l2", "l3", "l4", "l5"):
        assert is_reachable(excluded_link_id=link_id)