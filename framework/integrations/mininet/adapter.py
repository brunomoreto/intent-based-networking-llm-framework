
"""Adapter that translates a framework Topology into a Mininet network."""

from __future__ import annotations

from typing import Any

from framework.core.topology.enums import LinkStatus, NodeType
from framework.core.topology.topology import Topology


class MininetAdapterError(ValueError):
    """Raised when a topology cannot be represented by this adapter."""


def create_mininet_network(
    topology: Topology,
    controller_ip: str,
    controller_port: int = 6653,
    *,
    mininet_api: Any | None = None,
) -> Any:
    """Build a Mininet network without starting it.

    Assumptions for link parameters:
    - bandwidth is expressed in Mbps;
    - delay is expressed in milliseconds;
    - packet_loss is expressed as a percentage.

    Only active links are created. The caller is responsible for starting,
    testing and stopping the returned network.
    """
    if not isinstance(topology, Topology):
        raise TypeError("topology must be a Topology instance.")

    if not controller_ip or not controller_ip.strip():
        raise ValueError("controller_ip must not be empty.")

    if isinstance(controller_port, bool) or not isinstance(
        controller_port, int
    ):
        raise TypeError("controller_port must be an integer.")

    if not 1 <= controller_port <= 65535:
        raise ValueError("controller_port must be between 1 and 65535.")

    # Lazy import allows the framework and its unit tests to run on systems
    # where Mininet is not installed, such as the Windows development host.
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

    # Validate supported node and link types before creating the network.
    for node in nodes:
        if node.node_type not in (NodeType.HOST, NodeType.SWITCH):
            raise MininetAdapterError(
                f"Unsupported node type '{node.node_type.value}' "
                f"for node '{node.id}'. This adapter supports hosts "
                "and switches only."
            )

    for link in links:
        if not link.bidirectional:
            raise MininetAdapterError(
                f"Link '{link.id}' is unidirectional. Mininet's ordinary "
                "point-to-point link model is bidirectional."
            )

        if link.status == LinkStatus.ACTIVE:
            for field, value in (
                ("bandwidth", link.bandwidth),
                ("delay", link.delay),
                ("packet_loss", link.packet_loss),
            ):
                if value < 0:
                    raise MininetAdapterError(
                        f"Link '{link.id}' has negative {field}: {value}."
                    )

            if link.packet_loss > 100:
                raise MininetAdapterError(
                    f"Link '{link.id}' packet_loss must not exceed 100."
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
                host_options: dict[str, Any] = {}

                ip_address = node.properties.get("ip")
                if ip_address:
                    host_options["ip"] = ip_address

                net.addHost(node.id, **host_options)

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

            link_options: dict[str, Any] = {}

            if link.bandwidth > 0:
                link_options["bw"] = link.bandwidth

            if link.delay > 0:
                link_options["delay"] = f"{link.delay}ms"

            if link.packet_loss > 0:
                link_options["loss"] = link.packet_loss

            net.addLink(
                link.source,
                link.destination,
                **link_options,
            )

        net.build()
        return net

    except Exception:
        # Best-effort cleanup if construction fails.
        try:
            net.stop()
        except Exception:
            pass
        raise
