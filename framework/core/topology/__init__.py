
"""
Topology Domain - Public API

This package exposes the public interface of the Topology V2 domain.
"""
from .topology import Topology

from .enums import (
    NodeType,
    LinkStatus,
    InterfaceStatus,
    ControllerStatus,
    AssociationRole,
    TopologySource,
)

from .types import (
    TopologyId,
    NodeId,
    InterfaceId,
    LinkId,
    ControllerId,
    RouteId,
    AssociationId,
    PolicyId,
    Attributes,
    Tags,
    Timestamp,
    Bandwidth,
    Delay,
    PacketLoss,
    Weight,
    MetricValue,
    MetricValues,
)

from .entities import (
    Metadata,
    Interface,
    NetworkElement,
    Node,
    Host,
    Switch,
    Router,
    StaticRoute,
    LinkDirection,
    Link,
    Controller,
    ControllerAssociation,
    Policy,
    Metrics,
)

from .serialization import (
    SCHEMA_VERSION,
    serialize_topology,
    deserialize_topology,
    save_topology,
    load_topology,
)

__all__ = [
    # Enumerations
    "NodeType",
    "LinkStatus",
    "InterfaceStatus",
    "ControllerStatus",
    "AssociationRole",
    "TopologySource",

    # Types
    "TopologyId",
    "NodeId",
    "InterfaceId",
    "LinkId",
    "ControllerId",
    "RouteId",
    "AssociationId",
    "PolicyId",
    "Attributes",
    "Tags",
    "Timestamp",
    "Bandwidth",
    "Delay",
    "PacketLoss",
    "Weight",
    "MetricValue",
    "MetricValues",

    # Entities
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
    
    #Aggregate
    "Topology",
    "SCHEMA_VERSION",
    "serialize_topology",
    "deserialize_topology",
    "save_topology",
    "load_topology",
]
