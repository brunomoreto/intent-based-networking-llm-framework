
"""Adapter that translates a V2 Topology into a Mininet network."""

from __future__ import annotations

import re
from typing import Any

from framework.core.topology.enums import (
    InterfaceStatus,
    LinkStatus,
    NodeType,
)
from framework.core.topology.topology import Topology


class MininetAdapterError(ValueError):
    """Raised when a topology cannot be represented by this adapter."""


_INTERFACE_PATTERN = re.compile(r"^eth(\d+)$")


def _interface_port(interface: Any, node: Any) -> int:
    """Translate a V2 interface name into a Mininet port number."""
    match = _INTERFACE_PATTERN.fullmatch(interface.name)

    if match is None:
        raise MininetAdapterError(
            f"Interface '{interface.id}' has unsupported name "
            f"'{interface.name}'. Expected ethN."
        )

    logical_port = int(match.group(1))

    # Open vSwitch reserves port 0 for its local interface.
    if node.node_type == NodeType.SWITCH:
        return logical_port + 1

    return logical_port


def _build_interface_index(topology: Topology) -> dict[str, tuple[Any, Any]]:
    """Map each Interface ID to its owning Node and Interface."""
    index: dict[str, tuple[Any, Any]] = {}

    for node in topology.nodes.values():
        for interface in node.interfaces:
            if interface.id in index:
                raise MininetAdapterError(
                    f"Duplicate interface ID '{interface.id}'."
                )

            index[interface.id] = (node, interface)

    return index


def _direction_params(direction: Any) -> dict[str, Any]:
    """Translate one V2 link direction into Mininet TCLink parameters."""
    params: dict[str, Any] = {
        "bw": direction.bandwidth,
    }

    if direction.delay > 0:
        params["delay"] = f"{direction.delay}ms"

    if direction.packet_loss > 0:
        params["loss"] = direction.packet_loss

    return params



def _configure_host_interfaces(
    topology: Topology,
    interface_index: dict[str, tuple[Any, Any]],
    net: Any,
) -> None:
    """Configure IPv4 and IPv6 addresses on Mininet Host interfaces."""
    for node in topology.nodes.values():
        if node.node_type != NodeType.HOST:
            continue

        host = net.get(node.id)

        for interface in node.interfaces:
            if interface.status != InterfaceStatus.UP:
                continue

            port = _interface_port(interface, node)

            # Interface name used by Mininet.
            mininet_interface = f"{node.id}-eth{port}"

            for address in interface.ipv4_addresses:
                host.setIP(
                    ip=str(address.ip),
                    prefixLen=address.network.prefixlen,
                    intf=mininet_interface,
                )

            for address in interface.ipv6_addresses:
                host.cmd(
                    "ip -6 addr add "
                    f"{address} dev {mininet_interface}"
                )



def create_mininet_network(
    topology: Topology,
    controller_ip: str,
    controller_port: int = 6653,
    *,
    mininet_api: Any | None = None,
) -> Any:
    """Build a Mininet network without starting it.

    V2 link directions are mapped independently to TCLink params1/params2.
    Link weight is intentionally not mapped to a traffic-control parameter.
    """
    if not isinstance(topology, Topology):
        raise TypeError("topology must be a Topology instance.")

    if not isinstance(controller_ip, str) or not controller_ip.strip():
        raise ValueError("controller_ip must not be empty.")

    if isinstance(controller_port, bool) or not isinstance(
        controller_port, int
    ):
        raise TypeError("controller_port must be an integer.")

    if not 1 <= controller_port <= 65535:
        raise ValueError("controller_port must be between 1 and 65535.")

    if mininet_api is None:
        try:
            from mininet.net import Mininet
            from mininet.node import OVSSwitch, RemoteController
            from mininet.link import TCLink
        except ImportError as exc:
            raise RuntimeError(
                "Mininet is required to build a real network. "
                "Run this function on the Mininet VM."
            ) from exc
    else:
        Mininet = mininet_api.Mininet
        OVSSwitch = mininet_api.OVSSwitch
        RemoteController = mininet_api.RemoteController
        TCLink = mininet_api.TCLink

    nodes = list(topology.nodes.values())
    links = list(topology.links.values())

    interface_index = _build_interface_index(topology)

    for node in nodes:
        if node.node_type not in (NodeType.HOST, NodeType.SWITCH):
            raise MininetAdapterError(
                f"Unsupported node type '{node.node_type.value}' "
                f"for node '{node.id}'. Only hosts and switches "
                "are supported."
            )

        for interface in node.interfaces:
            _interface_port(interface, node)

    for link in links:
        if link.status != LinkStatus.ACTIVE:
            continue

        source_entry = interface_index.get(link.source_interface_id)
        destination_entry = interface_index.get(
            link.destination_interface_id
        )

        if source_entry is None or destination_entry is None:
            raise MininetAdapterError(
                f"Link '{link.id}' references an unknown interface."
            )

        source_node, source_interface = source_entry
        destination_node, destination_interface = destination_entry

        if source_node.id == destination_node.id:
            raise MininetAdapterError(
                f"Link '{link.id}' connects interfaces belonging "
                "to the same node."
            )

        if (
            source_interface.status != InterfaceStatus.UP
            or destination_interface.status != InterfaceStatus.UP
        ):
            continue

        if link.reverse is None:
            raise MininetAdapterError(
                f"Link '{link.id}' has no declared reverse direction. "
                "Mininet TCLink cannot represent this configuration "
                "faithfully."
            )

        if link.forward.enabled != link.reverse.enabled:
            raise MininetAdapterError(
                f"Link '{link.id}' has only one enabled direction. "
                "This configuration is not supported by this adapter."
            )

    net = Mininet(
        controller=None,
        switch=OVSSwitch,
        link=TCLink,
        build=False,
        autoSetMacs=True,
    )

    try:
        for node in nodes:
            if node.node_type == NodeType.HOST:
                net.addHost(node.id)

            elif node.node_type == NodeType.SWITCH:
                net.addSwitch(node.id, protocols="OpenFlow13")

        net.addController(
            "c0",
            controller=RemoteController,
            ip=controller_ip,
            port=controller_port,
        )

        for link in links:
            if link.status != LinkStatus.ACTIVE:
                continue

            source_node, source_interface = interface_index[
                link.source_interface_id
            ]
            destination_node, destination_interface = interface_index[
                link.destination_interface_id
            ]

            if (
                source_interface.status != InterfaceStatus.UP
                or destination_interface.status != InterfaceStatus.UP
            ):
                continue

            if not link.forward.enabled and not link.reverse.enabled:
                continue

            source_port = _interface_port(source_interface, source_node)
            destination_port = _interface_port(
                destination_interface,
                destination_node,
            )

            net.addLink(
                source_node.id,
                destination_node.id,
                port1=source_port,
                port2=destination_port,
                params1=_direction_params(link.forward),
                params2=_direction_params(link.reverse),
            )

        net.build()

        _configure_host_interfaces(topology, interface_index, net)

        return net

    except Exception:
        try:
            net.stop()
        except Exception:
            pass
        raise
