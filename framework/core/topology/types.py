"""
Topology Domain - Shared Types

This module defines the shared type aliases used throughout the
Topology Domain.

These aliases improve readability and provide a common vocabulary for
the domain model.

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
LinkId: TypeAlias = str
PolicyId: TypeAlias = str
MetricId: TypeAlias = str


# =============================================================================
# Generic Structures
# =============================================================================

Attributes: TypeAlias = dict[str, Any]
Properties: TypeAlias = dict[str, Any]

Tags: TypeAlias = list[str]
Labels: TypeAlias = list[str]


# =============================================================================
# Network Values
# =============================================================================

Bandwidth: TypeAlias = float
Delay: TypeAlias = float
PacketLoss: TypeAlias = float
Weight: TypeAlias = float

MetricValue: TypeAlias = float
MetricValues: TypeAlias = dict[str, MetricValue]


# =============================================================================
# Generic Types
# =============================================================================

Timestamp: TypeAlias = datetime
Coordinates: TypeAlias = tuple[float, float]


__all__ = [
    "TopologyId",
    "NodeId",
    "LinkId",
    "PolicyId",
    "MetricId",
    "Attributes",
    "Properties",
    "Tags",
    "Labels",
    "Bandwidth",
    "Delay",
    "PacketLoss",
    "Weight",
    "MetricValue",
    "MetricValues",
    "Timestamp",
    "Coordinates",
]