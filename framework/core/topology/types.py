
"""
Topology Domain - Shared Types

This module defines the shared type aliases used throughout
the Topology V2 domain.

These aliases improve readability and provide a common vocabulary
for the domain model.

This module intentionally contains no business logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypeAlias


# =============================================================================
# Domain Identifiers
# =============================================================================

TopologyId: TypeAlias = str
NodeId: TypeAlias = str
InterfaceId: TypeAlias = str
LinkId: TypeAlias = str
ControllerId: TypeAlias = str
RouteId: TypeAlias = str
AssociationId: TypeAlias = str
PolicyId: TypeAlias = str


# =============================================================================
# Generic Structures
# =============================================================================

Attributes: TypeAlias = dict[str, Any]
Tags: TypeAlias = list[str]
Timestamp: TypeAlias = datetime


# =============================================================================
# Network Values
# =============================================================================

Bandwidth: TypeAlias = int | float
Delay: TypeAlias = int | float
PacketLoss: TypeAlias = int | float
Weight: TypeAlias = int | float


# =============================================================================
# Metrics
# =============================================================================

MetricValue: TypeAlias = int | float
MetricValues: TypeAlias = dict[str, MetricValue]


# =============================================================================
# Transitional Import
# =============================================================================

# Temporary: required by the current pre-V2 models.py.
# Remove when the V2 domain entities replace Node.properties.
Properties: TypeAlias = dict[str, Any]


# =============================================================================
# Public API
# =============================================================================

__all__ = [
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
]
