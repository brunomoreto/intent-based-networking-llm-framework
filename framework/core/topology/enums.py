"""
Topology Domain - Enumerations

This module defines the enumerations used throughout
the Topology V2 domain.

Enum values are represented as lowercase strings to ensure
consistency with the JSON V2 serialization contract.

This module intentionally contains no business logic.
"""

from enum import StrEnum


# =============================================================================
# Network Node Types
# =============================================================================

class NodeType(StrEnum):
    HOST = "host"
    SWITCH = "switch"
    ROUTER = "router"


# =============================================================================
# Operational Status
# =============================================================================

class NodeStatus(StrEnum):
    UP = "up"
    DOWN = "down"
    MAINTENANCE = "maintenance"


class InterfaceStatus(StrEnum):
    UP = "up"
    DOWN = "down"
    MAINTENANCE = "maintenance"


class LinkStatus(StrEnum):
    UP = "up"
    DOWN = "down"
    MAINTENANCE = "maintenance"


# =============================================================================
# Controller Status
# =============================================================================

class ControllerStatus(StrEnum):
    UNKNOWN = "unknown"
    ACTIVE = "active"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


# =============================================================================
# Controller Association Roles
# =============================================================================

class AssociationRole(StrEnum):
    MASTER = "master"
    STANDBY = "standby"
    EQUAL = "equal"


# =============================================================================
# Topology Source
# =============================================================================

class TopologySource(StrEnum):
    CUSTOM = "custom"
    REFERENCE = "reference"
    SYNTHETIC = "synthetic"
    PRODUCTION = "production"


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    "NodeType",
    "NodeStatus",
    "InterfaceStatus",
    "LinkStatus",
    "ControllerStatus",
    "AssociationRole",
    "TopologySource",
]