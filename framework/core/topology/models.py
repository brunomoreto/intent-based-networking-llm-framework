"""
Topology Domain - Domain Entities

This module defines the domain entities of the Topology Domain.

The entities represent the conceptual state of a communication network,
independently of any infrastructure technology.

This module intentionally contains no business logic.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field

from .enums import (
    LinkStatus,
    NodeType,
    TopologyType,
)

from .types import (
    Attributes,
    Bandwidth,
    Delay,
    LinkId,
    MetricValues,
    NodeId,
    PacketLoss,
    PolicyId,
    Properties,
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
    """
    Represents descriptive information associated with a network topology.
    """

    id: TopologyId
    name: str

    description: str = ""
    author: str = ""
    version: str = "1.0"

    created_at: Timestamp | None = None

    topology_type: TopologyType = TopologyType.CUSTOM

    tags: Tags = field(default_factory=list)


# =============================================================================
# Base Entity
# =============================================================================

@dataclass(slots=True, kw_only=True)
class NetworkElement(ABC):
    """
    Represents the abstract base class for every network node.
    """

    id: NodeId
    name: str

    attributes: Attributes = field(default_factory=dict)


# =============================================================================
# Nodes
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Node(NetworkElement):
    """
    Represents a generic network node.
    """

    node_type: NodeType

    properties: Properties = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class Switch(Node):
    """
    Represents a network switch.
    """

    node_type: NodeType = NodeType.SWITCH


@dataclass(slots=True, kw_only=True)
class Host(Node):
    """
    Represents a network host.
    """

    node_type: NodeType = NodeType.HOST


@dataclass(slots=True, kw_only=True)
class Router(Node):
    """
    Represents a network router.
    """

    node_type: NodeType = NodeType.ROUTER


@dataclass(slots=True, kw_only=True)
class Controller(Node):
    """
    Represents an SDN controller.
    """

    node_type: NodeType = NodeType.CONTROLLER


# =============================================================================
# Links
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Link:
    """
    Represents a logical connection between two network nodes.
    """

    id: LinkId

    source: NodeId
    destination: NodeId

    bandwidth: Bandwidth = 0.0
    delay: Delay = 0.0
    weight: Weight = 1.0
    packet_loss: PacketLoss = 0.0

    status: LinkStatus = LinkStatus.ACTIVE

    bidirectional: bool = True

    attributes: Attributes = field(default_factory=dict)


# =============================================================================
# Policies
# =============================================================================

@dataclass(slots=True, kw_only=True)
class Policy:
    """
    Represents a network policy.
    """

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
    """
    Stores topology metrics.
    """

    values: MetricValues = field(default_factory=dict)


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    "Metadata",
    "NetworkElement",
    "Node",
    "Switch",
    "Host",
    "Router",
    "Controller",
    "Link",
    "Policy",
    "Metrics",
]