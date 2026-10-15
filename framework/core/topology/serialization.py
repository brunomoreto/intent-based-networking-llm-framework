
"""
Topology Domain - JSON Serialization

This module provides JSON serialization and deserialization
for network topology objects.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .enums import LinkStatus, NodeType, TopologySource
from .exceptions import (
    SerializationError,
    TopologyFileError,
    TopologyFormatError,
    TopologyValidationError,
    UnsupportedSchemaVersionError,
)
from .models import (
    Controller,
    Host,
    Link,
    Metadata,
    Metrics,
    Node,
    Policy,
    Router,
    Switch,
)
from .topology import Topology
from .validator import validate_topology


SCHEMA_VERSION = 1

_ROOT_KEYS = {
    "schema_version",
    "metadata",
    "nodes",
    "links",
    "policies",
    "metrics",
}

_METADATA_KEYS = {
    "id",
    "name",
    "description",
    "author",
    "version",
    "created_at",
    "topology_source",
    "tags",
}

_NODE_KEYS = {
    "id",
    "name",
    "node_type",
    "attributes",
    "properties",
}

_LINK_KEYS = {
    "id",
    "source",
    "destination",
    "bandwidth",
    "delay",
    "weight",
    "packet_loss",
    "status",
    "bidirectional",
    "attributes",
}

_POLICY_KEYS = {
    "id",
    "name",
    "description",
    "enabled",
    "attributes",
}

_METRICS_KEYS = {"values"}

_NODE_CLASSES = {
    NodeType.SWITCH: Switch,
    NodeType.HOST: Host,
    NodeType.ROUTER: Router,
    NodeType.CONTROLLER: Controller,
}


def _require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TopologyFormatError(
            f"'{location}' must be a JSON object."
        )
    return value


def _check_keys(
    data: dict[str, Any],
    allowed: set[str],
    required: set[str],
    location: str,
) -> None:
    unknown = set(data) - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise TopologyFormatError(
            f"Unknown field(s) in '{location}': {names}."
        )

    missing = required - set(data)
    if missing:
        names = ", ".join(sorted(missing))
        raise TopologyFormatError(
            f"Missing required field(s) in '{location}': {names}."
        )


def _require_string(value: Any, location: str) -> str:
    if not isinstance(value, str):
        raise TopologyFormatError(
            f"'{location}' must be a string."
        )
    return value


def _require_mapping(
    value: Any,
    location: str,
) -> dict[str, Any]:
    data = _require_object(value, location)

    if not all(isinstance(key, str) for key in data):
        raise TopologyFormatError(
            f"All keys in '{location}' must be strings."
        )

    return data


def _require_boolean(value: Any, location: str) -> bool:
    if not isinstance(value, bool):
        raise TopologyFormatError(
            f"'{location}' must be a boolean."
        )
    return value


def _require_number(value: Any, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TopologyFormatError(
            f"'{location}' must be a number."
        )

    return float(value)


def _require_list(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise TopologyFormatError(
            f"'{location}' must be a JSON array."
        )
    return value


def _parse_enum(enum_class: Any, value: Any, location: str) -> Any:
    if not isinstance(value, str):
        raise TopologyFormatError(
            f"'{location}' must be a string."
        )

    try:
        return enum_class(value)
    except ValueError:
        raise TopologyFormatError(
            f"Invalid value '{value}' for '{location}'."
        ) from None


def _parse_metadata(data: Any) -> Metadata:
    data = _require_object(data, "metadata")

    _check_keys(
        data,
        _METADATA_KEYS,
        {"id", "name"},
        "metadata",
    )

    created_at = data.get("created_at")
    if created_at is not None:
        if not isinstance(created_at, str):
            raise TopologyFormatError(
                "'metadata.created_at' must be an ISO 8601 string or null."
            )
        try:
            created_at = datetime.fromisoformat(created_at)
        except ValueError:
            raise TopologyFormatError(
                "'metadata.created_at' is not a valid ISO 8601 timestamp."
            ) from None

    tags = _require_list(data.get("tags", []), "metadata.tags")
    if not all(isinstance(tag, str) for tag in tags):
        raise TopologyFormatError(
            "Every item in 'metadata.tags' must be a string."
        )

    return Metadata(
        id=_require_string(data["id"], "metadata.id"),
        name=_require_string(data["name"], "metadata.name"),
        description=_require_string(
            data.get("description", ""),
            "metadata.description",
        ),
        author=_require_string(
            data.get("author", ""),
            "metadata.author",
        ),
        version=_require_string(
            data.get("version", "1.0"),
            "metadata.version",
        ),
        created_at=created_at,
        topology_source=_parse_enum(
            TopologySource,
            data.get("topology_source", TopologySource.CUSTOM.value),
            "metadata.topology_source",
        ),
        tags=tags,
    )


def _parse_node(data: Any) -> Node:
    data = _require_object(data, "node")

    _check_keys(
        data,
        _NODE_KEYS,
        {"id", "name", "node_type"},
        "node",
    )

    node_type = _parse_enum(
        NodeType,
        data["node_type"],
        "node.node_type",
    )

    node_class = _NODE_CLASSES[node_type]

    return node_class(
        id=_require_string(data["id"], "node.id"),
        name=_require_string(data["name"], "node.name"),
        attributes=_require_mapping(
            data.get("attributes", {}),
            "node.attributes",
        ),
        properties=_require_mapping(
            data.get("properties", {}),
            "node.properties",
        ),
    )


def _parse_link(data: Any) -> Link:
    data = _require_object(data, "link")

    _check_keys(
        data,
        _LINK_KEYS,
        {"id", "source", "destination"},
        "link",
    )

    return Link(
        id=_require_string(data["id"], "link.id"),
        source=_require_string(data["source"], "link.source"),
        destination=_require_string(
            data["destination"],
            "link.destination",
        ),
        bandwidth=_require_number(
            data.get("bandwidth", 0.0),
            "link.bandwidth",
        ),
        delay=_require_number(
            data.get("delay", 0.0),
            "link.delay",
        ),
        weight=_require_number(
            data.get("weight", 1.0),
            "link.weight",
        ),
        packet_loss=_require_number(
            data.get("packet_loss", 0.0),
            "link.packet_loss",
        ),
        status=_parse_enum(
            LinkStatus,
            data.get("status", LinkStatus.ACTIVE.value),
            "link.status",
        ),
        bidirectional=_require_boolean(
            data.get("bidirectional", True),
            "link.bidirectional",
        ),
        attributes=_require_mapping(
            data.get("attributes", {}),
            "link.attributes",
        ),
    )


def _parse_policy(data: Any) -> Policy:
    data = _require_object(data, "policy")

    _check_keys(
        data,
        _POLICY_KEYS,
        {"id", "name"},
        "policy",
    )

    return Policy(
        id=_require_string(data["id"], "policy.id"),
        name=_require_string(data["name"], "policy.name"),
        description=_require_string(
            data.get("description", ""),
            "policy.description",
        ),
        enabled=_require_boolean(
            data.get("enabled", True),
            "policy.enabled",
        ),
        attributes=_require_mapping(
            data.get("attributes", {}),
            "policy.attributes",
        ),
    )


def _parse_metrics(data: Any) -> Metrics:
    data = _require_object(data, "metrics")

    _check_keys(
        data,
        _METRICS_KEYS,
        {"values"},
        "metrics",
    )

    values = _require_mapping(data["values"], "metrics.values")

    parsed_values = {
        key: _require_number(value, f"metrics.values.{key}")
        for key, value in values.items()
    }

    return Metrics(values=parsed_values)


def load_topology(path: str | Path) -> Topology:
    """
    Load a topology from a JSON file.

    Raises:
        TopologyFileError: If the file cannot be read.
        TopologyFormatError: If the JSON or its structure is invalid.
        UnsupportedSchemaVersionError: If the schema version is unsupported.
        TopologyValidationError: If the topology is structurally invalid.
    """
    file_path = Path(path)

    try:
        with file_path.open("r", encoding="utf-8") as file:
            document = json.load(file)
    except OSError as exc:
        raise TopologyFileError(
            f"Could not read topology file '{file_path}': {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise TopologyFormatError(
            f"Invalid JSON in '{file_path}' at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    document = _require_object(document, "root")

    _check_keys(
        document,
        _ROOT_KEYS,
        {"schema_version", "metadata", "nodes", "links"},
        "root",
    )

    schema_version = document["schema_version"]
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
    ):
        raise TopologyFormatError(
            "'schema_version' must be an integer."
        )

    if schema_version != SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"Unsupported schema version '{schema_version}'. "
            f"Supported version: {SCHEMA_VERSION}."
        )

    metadata = _parse_metadata(document["metadata"])
    topology = Topology(metadata)

    nodes = _require_list(document["nodes"], "nodes")
    links = _require_list(document["links"], "links")
    policies = _require_list(document.get("policies", []), "policies")

    try:
        for item in nodes:
            topology.add_node(_parse_node(item))

        for item in links:
            topology.add_link(_parse_link(item))

        for item in policies:
            topology.add_policy(_parse_policy(item))

        if "metrics" in document:
            topology.set_metrics(_parse_metrics(document["metrics"]))

        validate_topology(topology)

    except (TypeError, ValueError, KeyError) as exc:
        raise TopologyFormatError(
            f"Invalid topology structure: {exc}"
        ) from exc

    return topology


def _metadata_to_dict(metadata: Metadata) -> dict[str, Any]:
    return {
        "id": metadata.id,
        "name": metadata.name,
        "description": metadata.description,
        "author": metadata.author,
        "version": metadata.version,
        "created_at": (
            metadata.created_at.isoformat()
            if metadata.created_at is not None
            else None
        ),
        "topology_source": metadata.topology_source.value,
        "tags": metadata.tags,
    }


def _node_to_dict(node: Node) -> dict[str, Any]:
    return {
        "id": node.id,
        "name": node.name,
        "node_type": node.node_type.value,
        "attributes": node.attributes,
        "properties": node.properties,
    }


def _link_to_dict(link: Link) -> dict[str, Any]:
    return {
        "id": link.id,
        "source": link.source,
        "destination": link.destination,
        "bandwidth": link.bandwidth,
        "delay": link.delay,
        "weight": link.weight,
        "packet_loss": link.packet_loss,
        "status": link.status.value,
        "bidirectional": link.bidirectional,
        "attributes": link.attributes,
    }


def _policy_to_dict(policy: Policy) -> dict[str, Any]:
    return {
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "enabled": policy.enabled,
        "attributes": policy.attributes,
    }


def save_topology(topology: Topology, path: str | Path) -> None:
    """
    Save a topology to a JSON file.

    Raises:
        TypeError: If the supplied object is not a Topology.
        TopologyFileError: If the file cannot be written.
        SerializationError: If the topology cannot be represented as JSON.
        TopologyValidationError: If the topology is structurally invalid.
    """
    if not isinstance(topology, Topology):
        raise TypeError("topology must be an instance of Topology.")

    validate_topology(topology)

    document = {
        "schema_version": SCHEMA_VERSION,
        "metadata": _metadata_to_dict(topology.metadata),
        "nodes": [
            _node_to_dict(node)
            for node in topology.nodes.values()
        ],
        "links": [
            _link_to_dict(link)
            for link in topology.links.values()
        ],
        "policies": [
            _policy_to_dict(policy)
            for policy in topology.policies.values()
        ],
        "metrics": {
            "values": topology.metrics.values,
        },
    }

    file_path = Path(path)

    try:
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(
                document,
                file,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            file.write("\n")
    except OSError as exc:
        raise TopologyFileError(
            f"Could not write topology file '{file_path}': {exc}"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise SerializationError(
            f"Could not serialize topology: {exc}"
        ) from exc


__all__ = [
    "SCHEMA_VERSION",
    "load_topology",
    "save_topology",
]
