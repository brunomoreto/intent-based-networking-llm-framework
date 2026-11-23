"""Translate a Topology Model V2 aggregate into a Mininet network."""

from __future__ import annotations

import re
import shlex
from ipaddress import IPv4Network, IPv6Network
from typing import Any

from framework.core.topology.enums import (
    InterfaceStatus,
    LinkStatus,
    NodeType,
)
from framework.core.topology.topology import Topology


class MininetAdapterError(ValueError):
    """Raised when a V2 topology cannot be represented faithfully in Mininet."""


_INTERFACE_PATTERN = re.compile(r"^eth(\d+)$")
_COMMAND_RC_MARKER = "__MININET_ADAPTER_RC__"


def _interface_port(interface: Any, node: Any) -> int:
    """Map a V2 ethN interface name to a Mininet port number."""
    match = _INTERFACE_PATTERN.fullmatch(interface.name)
    if match is None:
        raise MininetAdapterError(
            f"Interface '{interface.id}' has unsupported name "
            f"'{interface.name}'. Expected ethN."
        )

    logical_port = int(match.group(1))
    return logical_port + 1 if node.node_type == NodeType.SWITCH else logical_port


def _mininet_interface_name(node: Any, interface: Any) -> str:
    """Return the Linux interface name generated for a V2 interface."""
    return f"{node.id}-eth{_interface_port(interface, node)}"


def _build_interface_index(topology: Topology) -> dict[str, tuple[Any, Any]]:
    """Index Interface IDs and retain their owning Node."""
    index: dict[str, tuple[Any, Any]] = {}
    for node in topology.nodes.values():
        for interface in node.interfaces:
            if interface.id in index:
                raise MininetAdapterError(
                    f"Duplicate interface ID '{interface.id}'."
                )
            index[interface.id] = (node, interface)
    return index


def _validate_interface_ports(nodes: list[Any]) -> None:
    """Reject duplicate Mininet port mappings within a Node."""
    for node in nodes:
        used_ports: dict[int, str] = {}
        for interface in node.interfaces:
            port = _interface_port(interface, node)
            if port in used_ports:
                raise MininetAdapterError(
                    f"Node '{node.id}' maps Interfaces '{used_ports[port]}' "
                    f"and '{interface.id}' to the same Mininet port {port}."
                )
            used_ports[port] = interface.id


def _direction_params(direction: Any) -> dict[str, Any]:
    """Translate one V2 link direction into Mininet TCLink parameters."""
    params: dict[str, Any] = {"bw": direction.bandwidth}
    if direction.delay > 0:
        params["delay"] = f"{direction.delay}ms"
    if direction.packet_loss > 0:
        params["loss"] = direction.packet_loss
    return params


def _active_links(
    links: list[Any],
    interface_index: dict[str, tuple[Any, Any]],
) -> tuple[list[Any], set[str]]:
    """Validate link semantics and return links Mininet can materialize."""
    active: list[Any] = []
    materialized_interface_ids: set[str] = set()

    for link in links:
        if link.status != LinkStatus.UP:
            continue

        source_entry = interface_index.get(link.source_interface_id)
        destination_entry = interface_index.get(link.destination_interface_id)
        if source_entry is None or destination_entry is None:
            raise MininetAdapterError(
                f"Link '{link.id}' references an unknown interface."
            )

        source_node, source_interface = source_entry
        destination_node, destination_interface = destination_entry

        if source_node.id == destination_node.id:
            raise MininetAdapterError(
                f"Link '{link.id}' connects interfaces belonging to the same node."
            )

        if (
            source_interface.status != InterfaceStatus.UP
            or destination_interface.status != InterfaceStatus.UP
        ):
            continue

        if link.reverse is None:
            raise MininetAdapterError(
                f"Link '{link.id}' has no declared reverse direction. "
                "Mininet TCLink cannot represent this configuration faithfully."
            )

        if link.forward.enabled != link.reverse.enabled:
            raise MininetAdapterError(
                f"Link '{link.id}' has only one enabled direction."
            )

        if link.forward.enabled:
            active.append(link)
            materialized_interface_ids.update(
                (link.source_interface_id, link.destination_interface_id)
            )

    return active, materialized_interface_ids


def _validate_node_types(nodes: list[Any]) -> None:
    supported = {NodeType.HOST, NodeType.SWITCH, NodeType.ROUTER}
    for node in nodes:
        if node.node_type not in supported:
            raise MininetAdapterError(
                f"Unsupported node type '{node.node_type}' for node '{node.id}'."
            )
        for interface in node.interfaces:
            _interface_port(interface, node)


def _validate_routes(
    nodes: list[Any],
    interface_index: dict[str, tuple[Any, Any]],
    materialized_interface_ids: set[str],
) -> None:
    """Check that route egress references can be represented in Mininet."""
    for node in nodes:
        if node.node_type not in (NodeType.HOST, NodeType.ROUTER):
            continue

        for route in node.static_routes:
            if route.outgoing_interface_id is not None:
                entry = interface_index.get(route.outgoing_interface_id)
                if entry is None or entry[0].id != node.id:
                    raise MininetAdapterError(
                        f"Static route '{route.id}' on node '{node.id}' "
                        "references an interface that does not belong to that node."
                    )
                if route.outgoing_interface_id not in materialized_interface_ids:
                    raise MininetAdapterError(
                        f"Static route '{route.id}' on node '{node.id}' "
                        "uses an interface that is not connected by an active link."
                    )

            if route.next_hop is None and route.outgoing_interface_id is None:
                raise MininetAdapterError(
                    f"Static route '{route.id}' on node '{node.id}' "
                    "requires a next hop or an outgoing interface."
                )

            destination_is_v4 = isinstance(route.destination, IPv4Network)
            if route.next_hop is not None:
                next_hop_is_v4 = route.next_hop.version == 4
                if destination_is_v4 != next_hop_is_v4:
                    raise MininetAdapterError(
                        f"Static route '{route.id}' on node '{node.id}' "
                        "has incompatible destination and next-hop IP families."
                    )


def _run_checked(node: Any, command: str, *, context: str) -> None:
    """Run a command in a Mininet namespace and check its exit status."""
    wrapped = (
        f"{command} 2>&1; rc=$?; "
        f"printf '\\n{_COMMAND_RC_MARKER}%s' \"$rc\""
    )
    output = node.cmd(wrapped)
    if not isinstance(output, str):
        return

    marker_position = output.rfind(_COMMAND_RC_MARKER)
    if marker_position < 0:
        # Lightweight fake Mininet nodes used by unit tests may not emulate a shell.
        return

    status_text = output[marker_position + len(_COMMAND_RC_MARKER):].strip()
    try:
        return_code = int(status_text)
    except ValueError as exc:
        raise MininetAdapterError(
            f"Could not determine command status while {context}: {output}"
        ) from exc

    if return_code != 0:
        command_output = output[:marker_position].strip()
        raise MininetAdapterError(
            f"Failed while {context} (exit {return_code}): {command_output}"
        )


def _configure_node_interfaces(
    nodes: list[Any],
    net: Any,
    materialized_interface_ids: set[str],
) -> None:
    """Apply V2 IPv4/IPv6 addresses to connected Host and Router interfaces."""
    for domain_node in nodes:
        if domain_node.node_type not in (NodeType.HOST, NodeType.ROUTER):
            continue

        mininet_node = net.get(domain_node.id)
        for interface in domain_node.interfaces:
            if interface.id not in materialized_interface_ids:
                if interface.status == InterfaceStatus.UP and (
                    interface.ipv4_addresses or interface.ipv6_addresses
                ):
                    raise MininetAdapterError(
                        f"Interface '{interface.id}' on node '{domain_node.id}' "
                        "has IP addresses but is not connected by an active link."
                    )
                continue

            mininet_name = shlex.quote(
                _mininet_interface_name(domain_node, interface)
            )
            for address in interface.ipv4_addresses:
                _run_checked(
                    mininet_node,
                    f"ip -4 addr replace {shlex.quote(str(address))} dev {mininet_name}",
                    context=(
                        f"configuring IPv4 address {address} on "
                        f"{domain_node.id}/{interface.name}"
                    ),
                )

            for address in interface.ipv6_addresses:
                _run_checked(
                    mininet_node,
                    f"ip -6 addr replace {shlex.quote(str(address))} dev {mininet_name}",
                    context=(
                        f"configuring IPv6 address {address} on "
                        f"{domain_node.id}/{interface.name}"
                    ),
                )


def _install_static_routes(
    nodes: list[Any],
    interface_index: dict[str, tuple[Any, Any]],
    net: Any,
) -> None:
    """Install V2 static routes on Hosts and Linux Routers."""
    for domain_node in nodes:
        if domain_node.node_type not in (NodeType.HOST, NodeType.ROUTER):
            continue

        mininet_node = net.get(domain_node.id)
        for route in domain_node.static_routes:
            family = 4 if isinstance(route.destination, IPv4Network) else 6
            command = f"ip -{family} route replace {shlex.quote(str(route.destination))}"

            if route.next_hop is not None:
                command += f" via {shlex.quote(str(route.next_hop))}"

            if route.outgoing_interface_id is not None:
                _, outgoing_interface = interface_index[route.outgoing_interface_id]
                mininet_name = _mininet_interface_name(
                    domain_node,
                    outgoing_interface,
                )
                command += f" dev {shlex.quote(mininet_name)}"

            command += f" metric {int(route.metric)}"
            _run_checked(
                mininet_node,
                command,
                context=f"installing static route '{route.id}' on '{domain_node.id}'",
            )


def _load_linux_router(mininet_api: Any | None) -> Any:
    """Load LinuxRouter lazily so non-Mininet tests can run on Windows."""
    if mininet_api is not None:
        injected = getattr(mininet_api, "LinuxRouter", None)
        if injected is not None:
            return injected

    try:
        from .linux_router import LinuxRouter
    except ImportError as exc:
        raise RuntimeError(
            "Mininet is required to materialize Router nodes. "
            "Run this function on the Mininet Linux host."
        ) from exc
    return LinuxRouter


def create_mininet_network(
    topology: Topology,
    controller_ip: str,
    controller_port: int = 6653,
    *,
    mininet_api: Any | None = None,
) -> Any:
    """Build, but do not start, a Mininet network from a V2 topology.

    Hosts and Routers receive their declared IPv4/IPv6 interface addresses and
    static routes. Routers use Linux namespaces with configurable IP forwarding.
    Switches remain Open vSwitch instances using OpenFlow 1.3.
    """
    if not isinstance(topology, Topology):
        raise TypeError("topology must be a Topology instance.")
    if not isinstance(controller_ip, str) or not controller_ip.strip():
        raise ValueError("controller_ip must not be empty.")
    if isinstance(controller_port, bool) or not isinstance(controller_port, int):
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

    _validate_node_types(nodes)
    _validate_interface_ports(nodes)
    active_links, materialized_interface_ids = _active_links(
        links,
        interface_index,
    )
    _validate_routes(nodes, interface_index, materialized_interface_ids)

    has_routers = any(node.node_type == NodeType.ROUTER for node in nodes)
    LinuxRouter = _load_linux_router(mininet_api) if has_routers else None

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
                # V2 is authoritative; do not inject Mininet's default 10.0.0.0/8.
                net.addHost(node.id, ip=None)
            elif node.node_type == NodeType.SWITCH:
                net.addSwitch(node.id, protocols="OpenFlow13")
            elif node.node_type == NodeType.ROUTER:
                net.addHost(
                    node.id,
                    cls=LinuxRouter,
                    ip=None,
                    ipv4_forwarding=node.ipv4_forwarding,
                    ipv6_forwarding=node.ipv6_forwarding,
                )

        net.addController(
            "c0",
            controller=RemoteController,
            ip=controller_ip,
            port=controller_port,
        )

        for link in active_links:
            source_node, source_interface = interface_index[link.source_interface_id]
            destination_node, destination_interface = interface_index[
                link.destination_interface_id
            ]
            net.addLink(
                source_node.id,
                destination_node.id,
                port1=_interface_port(source_interface, source_node),
                port2=_interface_port(destination_interface, destination_node),
                params1=_direction_params(link.forward),
                params2=_direction_params(link.reverse),
            )

        net.build()
        _configure_node_interfaces(
            nodes,
            net,
            materialized_interface_ids,
        )
        _install_static_routes(nodes, interface_index, net)
        return net

    except Exception:
        try:
            net.stop()
        except Exception:
            pass
        raise
