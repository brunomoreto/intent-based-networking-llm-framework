
"""Convert ONOS REST topology data into the framework domain model."""

from typing import Any

from framework.core.topology.enums import (
    LinkStatus,
    NodeType,
    TopologySource,
)
from framework.core.topology.exceptions import TopologyValidationError
from framework.core.topology.models import Link, Metadata, Node
from framework.core.topology.topology import Topology
from framework.core.topology.validator import validate_topology


class OnosTopologyAdapterError(ValueError):
    """Raised when ONOS data cannot be converted into a valid topology."""


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OnosTopologyAdapterError(
            f"ONOS field '{field}' must be a non-empty string."
        )
    return value


def _device_id(device: dict[str, Any]) -> str:
    device_id = _required_string(device.get("id"), "device.id")
    return device_id


def _link_endpoint(link: dict[str, Any], side: str) -> str:
    endpoint = link.get(side)
    if not isinstance(endpoint, dict):
        raise OnosTopologyAdapterError(
            f"ONOS link field '{side}' must be an object."
        )

    return _required_string(
        endpoint.get("device"),
        f"link.{side}.device",
    )


def topology_from_onos(
    devices: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> Topology:
    """Convert ONOS devices and links into a validated Topology.

    ONOS does not necessarily expose end hosts as devices. Therefore,
    this adapter models discovered ONOS devices as switches and models
    links only when both endpoint devices are present in the response.
    """
    if not isinstance(devices, list) or not isinstance(links, list):
        raise OnosTopologyAdapterError(
            "devices and links must both be lists."
        )

    topology = Topology(
        Metadata(
            id="onos-live-topology",
            name="ONOS Discovered Topology",
            description="Topology imported from the ONOS REST API.",
            topology_source=TopologySource.PRODUCTION,
        )
    )

    device_ids: set[str] = set()

    for device in devices:
        if not isinstance(device, dict):
            raise OnosTopologyAdapterError(
                "Every ONOS device must be an object."
            )

        device_id = _device_id(device)
        if device_id in device_ids:
            raise OnosTopologyAdapterError(
                f"Duplicate ONOS device ID '{device_id}'."
            )

        device_ids.add(device_id)
        topology.add_node(
            Node(
                id=device_id,
                name=device.get("humanReadableName") or device_id,
                node_type=NodeType.SWITCH,
                attributes={
                    "onos_device_id": device_id,
                    "available": device.get("available"),
                    "role": device.get("role"),
                },
                properties={
                    "type": device.get("type"),
                    "manufacturer": device.get("mfr"),
                    "hardware": device.get("hw"),
                    "software": device.get("sw"),
                    "serial": device.get("serial"),
                    "protocol": device.get("protocol"),
                },
            )
        )

    seen_links: set[tuple[str, str, str, str]] = set()

    for index, link in enumerate(links):
        if not isinstance(link, dict):
            raise OnosTopologyAdapterError(
                "Every ONOS link must be an object."
            )

        source = _link_endpoint(link, "src")
        destination = _link_endpoint(link, "dst")

        if source not in device_ids or destination not in device_ids:
            raise OnosTopologyAdapterError(
                f"ONOS link references an unknown device: "
                f"{source} -> {destination}."
            )

        src_port = link["src"].get("port")
        dst_port = link["dst"].get("port")

        if src_port is None or dst_port is None:
            raise OnosTopologyAdapterError(
                "ONOS link endpoints must include port identifiers."
            )

        identity = (source, str(src_port), destination, str(dst_port))
        if identity in seen_links:
            continue
        seen_links.add(identity)

        link_id = f"onos-link-{index}"

        topology.add_link(
            Link(
                id=link_id,
                source=source,
                destination=destination,
                status=LinkStatus.ACTIVE,
                bidirectional=link.get("type") == "DIRECT",
                attributes={
                    "onos_link_type": link.get("type"),
                    "onos_state": link.get("state"),
                    "src_port": str(src_port),
                    "dst_port": str(dst_port),
                    "annotations": link.get("annotations", {}),
                },
            )
        )

    try:
        validate_topology(topology)
    except (TypeError, TopologyValidationError) as exc:
        raise OnosTopologyAdapterError(
            f"Converted ONOS topology is invalid: {exc}"
        ) from exc

    return topology


__all__ = ["OnosTopologyAdapterError", "topology_from_onos"]
