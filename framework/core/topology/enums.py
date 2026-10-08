"""
Topology Domain - Enumerations

This module defines the enumerations used by the Topology Domain.

Enumerations represent finite sets of valid values shared across the
framework.

This module intentionally contains no business logic.
"""

from enum import StrEnum


# =============================================================================
# Nodes
# =============================================================================

class NodeType(StrEnum):
    """Supported network node types."""

    SWITCH = "switch"
    HOST = "host"
    ROUTER = "router"
    CONTROLLER = "controller"


# =============================================================================
# Links
# =============================================================================

class LinkStatus(StrEnum):
    """Operational status of a network link."""

    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"


# =============================================================================
# Topologies
# =============================================================================

class TopologyType(StrEnum):
    """Classification of a topology."""

    CUSTOM = "custom"
    REFERENCE = "reference"
    SYNTHETIC = "synthetic"
    PRODUCTION = "production"


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    "NodeType",
    "LinkStatus",
    "TopologyType",
]