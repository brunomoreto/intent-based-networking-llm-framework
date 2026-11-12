
"""
Topology Domain - Entities

This module defines all domain entities used by Topology V2.

Entities are represented as dataclasses.
Validation and business rules are handled by dedicated domain services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)

from .enums import (
    AssociationRole,
    ControllerStatus,
    InterfaceStatus,
    LinkStatus,
    NodeType,
    TopologySource,
)
from .types import (
    AssociationId,
    Attributes,
    Bandwidth,
    ControllerId,
    Delay,
    InterfaceId,
    LinkId,
    MetricValues,
    NodeId,
    PacketLoss,
    PolicyId,
    RouteId,
    Tags,
    Timestamp,
    TopologyId,
    Weight,
)


# =============================================================================
# Metadata
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Metadata:
    """Descriptive and identification information for a topology."""

    id: TopologyId
    name: str
    description: str = ""
    author: str = ""
    version: str = "1.0"
    created_at: Timestamp | None = None
    topology_source: TopologySource = TopologySource.CUSTOM
    tags: Tags = field(default_factory=list)


# =============================================================================
# Interface
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Interface:
    """Network interface belonging to a Node."""

    id: InterfaceId
    name: str
    mac_address: str | None = None
    ipv4_addresses: list[IPv4Interface] = field(default_factory=list)
    ipv6_addresses: list[IPv6Interface] = field(default_factory=list)
    mtu: int | None = None
    speed: Bandwidth | None = None
    status: InterfaceStatus = InterfaceStatus.UP
    attributes: Attributes = field(default_factory=dict)


# =============================================================================
# Network Element
# =============================================================================

@dataclass(slots=True, kw_only=True)
class NetworkElement:
    """Base entity for network elements."""

    id: NodeId
    name: str
    attributes: Attributes = field(default_factory=dict)


# =============================================================================
# Node
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Node(NetworkElement):
    """Base class for network nodes."""

    node_type: NodeType
    interfaces: list[Interface] = field(default_factory=list)


# =============================================================================
# Host
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Host(Node):
    """End-system network node."""

    node_type: NodeType = field(default=NodeType.HOST, init=False)


# =============================================================================
# Switch
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Switch(Node):
    """Network switching node."""

    node_type: NodeType = field(default=NodeType.SWITCH, init=False)


# =============================================================================
# Static Route
# =============================================================================

@dataclass(slots=True, kw_only=True)
class StaticRoute:
    """Static IPv4 or IPv6 route configured on a Router."""

    id: RouteId
    destination: IPv4Network | IPv6Network
    next_hop: IPv4Address | IPv6Address | None = None
    outgoing_interface_id: InterfaceId | None = None
    metric: int = 0


# =============================================================================
# Router
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Router(Node):
    """Network node capable of forwarding IPv4 and IPv6 traffic."""

    node_type: NodeType = field(default=NodeType.ROUTER, init=False)
    ipv4_forwarding: bool = False
    ipv6_forwarding: bool = False
    static_routes: list[StaticRoute] = field(default_factory=list)


# =============================================================================
# Link Direction
# =============================================================================

@dataclass(slots=True, kw_only=True)
class LinkDirection:
    """Directional characteristics of a network link."""

    bandwidth: Bandwidth
    delay: Delay
    weight: Weight
    packet_loss: PacketLoss
    enabled: bool


# =============================================================================
# Link
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Link:
    """Connection between two network interfaces."""

    id: LinkId
    source_interface_id: InterfaceId
    destination_interface_id: InterfaceId
    forward: LinkDirection
    reverse: LinkDirection | None = None
    status: LinkStatus = LinkStatus.ACTIVE
    attributes: Attributes = field(default_factory=dict)


# =============================================================================
# Controller
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Controller:
    """Independent SDN controller entity."""

    id: ControllerId
    name: str
    controller_type: str
    endpoint: str
    port: int
    protocol: str
    status: ControllerStatus = ControllerStatus.UNKNOWN
    attributes: Attributes = field(default_factory=dict)


# =============================================================================
# Controller Association
# =============================================================================

@dataclass(slots=True, kw_only=True)
class ControllerAssociation:
    """Association between a Controller and a Node."""

    id: AssociationId
    controller_id: ControllerId
    node_id: NodeId
    role: AssociationRole | None = None


# =============================================================================
# Policy
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Policy:
    """Policy associated with a topology."""

    id: PolicyId
    name: str
    description: str = ""
    enabled: bool = True
    attributes: Attributes = field(default_factory=dict)


# =============================================================================
# Metrics
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Metrics:
    """Collection of numeric topology metrics."""

    values: MetricValues = field(default_factory=dict)


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    "Metadata",
    "Interface",
    "NetworkElement",
    "Node",
    "Host",
    "Switch",
    "Router",
    "StaticRoute",
    "LinkDirection",
    "Link",
    "Controller",
    "ControllerAssociation",
    "Policy",
    "Metrics",
]
