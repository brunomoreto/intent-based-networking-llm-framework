
"""JSON serialization and deserialization for Topology Model V2."""

from __future__ import annotations

import json
from datetime import datetime

from ipaddress import (
    IPv4Interface,
    IPv6Interface,
    ip_address,
    ip_network,
)
from pathlib import Path
from typing import Any, Mapping

from .enums import (
    AssociationRole,
    ControllerStatus,
    InterfaceStatus,
    LinkStatus,
    NodeType,
    TopologySource,
)
from .entities import (
    Controller,
    ControllerAssociation,
    Host,
    Interface,
    Link,
    LinkDirection,
    Metadata,
    Metrics,
    NetworkElement,
    Policy,
    Router,
    StaticRoute,
    Switch,
)
from .topology import Topology


SCHEMA_VERSION = 2


def _serialize_direction(direction: LinkDirection) -> dict[str, Any]:
    return {
        "bandwidth": direction.bandwidth,
        "delay": direction.delay,
        "weight": direction.weight,
        "packet_loss": direction.packet_loss,
        "enabled": direction.enabled,
    }


def _serialize_interface(interface: Interface) -> dict[str, Any]:
    return {
        "id": interface.id,
        "name": interface.name,
        "mac_address": interface.mac_address,
        "ipv4_addresses": [
            str(address) for address in interface.ipv4_addresses
        ],
        "ipv6_addresses": [
            str(address) for address in interface.ipv6_addresses
        ],
        "mtu": interface.mtu,
        "speed": interface.speed,
        "status": interface.status.value,
        "attributes": interface.attributes,
    }


def _serialize_static_route(route: StaticRoute) -> dict[str, Any]:
    return {
        "id": route.id,
        "destination": str(route.destination),
        "next_hop": (
            str(route.next_hop) if route.next_hop is not None else None
        ),
        "outgoing_interface_id": route.outgoing_interface_id,
        "metric": route.metric,
    }


def _serialize_node(node: NetworkElement) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": node.id,
        "name": node.name,
        "node_type": node.node_type.value,
        "attributes": node.attributes,
        "interfaces": [
            _serialize_interface(interface)
            for interface in node.interfaces
        ],
    }

    if isinstance(node, Router):
        data.update({
            "ipv4_forwarding": node.ipv4_forwarding,
            "ipv6_forwarding": node.ipv6_forwarding,
            "static_routes": [
                _serialize_static_route(route)
                for route in node.static_routes
            ],
        })

    return data


def serialize_topology(topology: Topology) -> dict[str, Any]:
    """Convert a Topology aggregate into a JSON-compatible dictionary."""

    metadata = topology.metadata
    metrics = topology.metrics

    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
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
            "tags": list(metadata.tags),
        },
        "nodes": [
            _serialize_node(node)
            for node in topology.nodes.values()
        ],
        "links": [
            {
                "id": link.id,
                "source_interface_id": link.source_interface_id,
                "destination_interface_id": link.destination_interface_id,
                "forward": _serialize_direction(link.forward),
                "reverse": (
                    _serialize_direction(link.reverse)
                    if link.reverse is not None
                    else None
                ),
                "status": link.status.value,
                "attributes": link.attributes,
            }
            for link in topology.links.values()
        ],
        "controllers": [
            {
                "id": controller.id,
                "name": controller.name,
                "controller_type": controller.controller_type,
                "endpoint": controller.endpoint,
                "port": controller.port,
                "protocol": controller.protocol,
                "status": controller.status.value,
                "attributes": controller.attributes,
            }
            for controller in topology.controllers.values()
        ],
        "controller_associations": [
            {
                "id": association.id,
                "controller_id": association.controller_id,
                "node_id": association.node_id,
                "role": (
                    association.role.value
                    if association.role is not None
                    else None
                ),
            }
            for association in topology.controller_associations.values()
        ],
        "policies": [
            {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "enabled": policy.enabled,
                "attributes": policy.attributes,
            }
            for policy in topology.policies.values()
        ],
        "metrics": {
            "values": dict(metrics.values),
        },
    }


def _deserialize_interface(data: Mapping[str, Any]) -> Interface:
    return Interface(
        id=data["id"],
        name=data["name"],
        mac_address=data.get("mac_address"),
        ipv4_addresses=[
            IPv4Interface(address)
            for address in data.get("ipv4_addresses", [])
        ],
        ipv6_addresses=[
            IPv6Interface(address)
            for address in data.get("ipv6_addresses", [])
        ],
        mtu=data.get("mtu"),
        speed=data.get("speed"),
        status=InterfaceStatus(data.get("status", "up")),
        attributes=dict(data.get("attributes", {})),
    )



def _deserialize_static_route(data: Mapping[str, Any]) -> StaticRoute:
    destination = ip_network(data["destination"], strict=False)
    next_hop_data = data.get("next_hop")

    return StaticRoute(
        id=data["id"],
        destination=destination,
        next_hop=(
            ip_address(next_hop_data)
            if next_hop_data is not None
            else None
        ),
        outgoing_interface_id=data.get("outgoing_interface_id"),
        metric=data.get("metric", 0),
    )


def _deserialize_node(data: Mapping[str, Any]) -> NetworkElement:
    node_type = NodeType(data["node_type"])

    common = {
        "id": data["id"],
        "name": data["name"],
        "attributes": dict(data.get("attributes", {})),
        "interfaces": [
            _deserialize_interface(interface)
            for interface in data.get("interfaces", [])
        ],
    }

    if node_type is NodeType.HOST:
        return Host(**common)

    if node_type is NodeType.SWITCH:
        return Switch(**common)

    if node_type is NodeType.ROUTER:
        return Router(
            **common,
            ipv4_forwarding=data.get("ipv4_forwarding", False),
            ipv6_forwarding=data.get("ipv6_forwarding", False),
            static_routes=[
                _deserialize_static_route(route)
                for route in data.get("static_routes", [])
            ],
        )

    raise ValueError(f"Unsupported node type: {node_type}")


def _deserialize_direction(data: Mapping[str, Any]) -> LinkDirection:
    return LinkDirection(
        bandwidth=data["bandwidth"],
        delay=data["delay"],
        weight=data["weight"],
        packet_loss=data["packet_loss"],
        enabled=data["enabled"],
    )


def deserialize_topology(document: Mapping[str, Any]) -> Topology:
    """Reconstruct a Topology aggregate from a decoded V2 document."""

    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            "Unsupported topology schema version: "
            f"{document.get('schema_version')!r}. "
            f"Expected version {SCHEMA_VERSION}."
        )

    metadata_data = document["metadata"]
    created_at_data = metadata_data.get("created_at")

    metadata = Metadata(
        id=metadata_data["id"],
        name=metadata_data["name"],
        description=metadata_data.get("description", ""),
        author=metadata_data.get("author", ""),
        version=metadata_data.get("version", "1.0"),
        created_at=(
            datetime.fromisoformat(created_at_data)
            if created_at_data is not None
            else None
        ),
        topology_source=TopologySource(
            metadata_data.get("topology_source", "custom")
        ),
        tags=list(metadata_data.get("tags", [])),
    )

    topology = Topology(metadata=metadata)

    for node_data in document.get("nodes", []):
        topology.add_node(_deserialize_node(node_data))

    for link_data in document.get("links", []):
        reverse_data = link_data.get("reverse")

        link = Link(
            id=link_data["id"],
            source_interface_id=link_data["source_interface_id"],
            destination_interface_id=link_data["destination_interface_id"],
            forward=_deserialize_direction(link_data["forward"]),
            reverse=(
                _deserialize_direction(reverse_data)
                if reverse_data is not None
                else None
            ),
            status=LinkStatus(link_data.get("status", "active")),
            attributes=dict(link_data.get("attributes", {})),
        )
        topology.add_link(link)

    for controller_data in document.get("controllers", []):
        controller = Controller(
            id=controller_data["id"],
            name=controller_data["name"],
            controller_type=controller_data["controller_type"],
            endpoint=controller_data["endpoint"],
            port=controller_data["port"],
            protocol=controller_data["protocol"],
            status=ControllerStatus(
                controller_data.get("status", "unknown")
            ),
            attributes=dict(controller_data.get("attributes", {})),
        )
        topology.add_controller(controller)

    for association_data in document.get(
        "controller_associations", []
    ):
        role_data = association_data.get("role")

        association = ControllerAssociation(
            id=association_data["id"],
            controller_id=association_data["controller_id"],
            node_id=association_data["node_id"],
            role=(
                AssociationRole(role_data)
                if role_data is not None
                else None
            ),
        )
        topology.add_controller_association(association)

    for policy_data in document.get("policies", []):
        policy = Policy(
            id=policy_data["id"],
            name=policy_data["name"],
            description=policy_data.get("description", ""),
            enabled=policy_data.get("enabled", True),
            attributes=dict(policy_data.get("attributes", {})),
        )
        topology.add_policy(policy)

    metrics_data = document.get("metrics", {})
    topology.set_metrics(
        Metrics(values=dict(metrics_data.get("values", {})))
    )

    return topology


def save_topology(
    topology: Topology,
    path: str | Path,
    *,
    indent: int = 2,
) -> None:
    """Serialize a topology and save it as a UTF-8 JSON file."""

    document = serialize_topology(topology)
    destination = Path(path)

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as file:
        json.dump(
            document,
            file,
            indent=indent,
            ensure_ascii=False,
        )
        file.write("\n")


def load_topology(path: str | Path) -> Topology:
    """Load a V2 JSON file and reconstruct its Topology aggregate."""

    source = Path(path)

    with source.open("r", encoding="utf-8") as file:
        document = json.load(file)

    if not isinstance(document, dict):
        raise ValueError("Topology JSON root must be an object.")

    return deserialize_topology(document)


__all__ = [
    "SCHEMA_VERSION",
    "serialize_topology",
    "deserialize_topology",
    "save_topology",
    "load_topology",
]
