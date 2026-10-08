"""
Topology Domain

Technology-independent representation of communication networks.

This package provides the canonical domain model used throughout the
Intent-Based Networking LLM Framework.

The Topology Domain is independent of controllers, emulators,
knowledge graphs, databases and Large Language Models.
"""

# =============================================================================
# Enumerations
# =============================================================================

from .enums import (
    LinkStatus,
    NodeType,
    TopologyType,
)

# =============================================================================
# Domain Entities
# =============================================================================

from .models import (
    Metadata,
    NetworkElement,
    Node,
    Switch,
    Host,
    Router,
    Controller,
    Link,
    Policy,
    Metrics,
)

# =============================================================================
# Aggregate Root
# =============================================================================

# Uncomment after topology.py is implemented.
#
# from .topology import Topology


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Enumerations
    "NodeType",
    "LinkStatus",
    "TopologyType",

    # Domain Model
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

    # Aggregate Root
    # "Topology",
]