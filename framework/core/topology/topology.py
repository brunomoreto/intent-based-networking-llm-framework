"""
Topology Domain - Aggregate Root

This module defines the Topology aggregate root.

The Topology class is responsible for managing the lifecycle of domain
entities while maintaining the structural consistency of the network.

It is intentionally independent of ONOS, Mininet, Neo4j, Docker,
OpenStack and Large Language Models.
"""

from __future__ import annotations

# =============================================================================
# Standard Library
# =============================================================================

from collections.abc import Iterator, Mapping
from copy import deepcopy
from types import MappingProxyType

# =============================================================================
# Local Imports
# =============================================================================

from .models import (
    Link,
    Metadata,
    Metrics,
    Node,
    Policy,
)

from .types import (
    LinkId,
    NodeId,
    PolicyId,
)


class Topology:
    """
    Aggregate Root of the Topology Domain.
    """

    def __init__(
        self,
        metadata: Metadata,
    ) -> None:
        """
        Initialize a new topology.
        """

        self._metadata = deepcopy(metadata)

        self._nodes: dict[NodeId, Node] = {}

        self._links: dict[LinkId, Link] = {}

        self._policies: dict[PolicyId, Policy] = {}

        self._metrics = Metrics()

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def metadata(self) -> Metadata:
        """
        Return a defensive copy of the topology metadata.
        """
        return deepcopy(self._metadata)

    @property
    def nodes(self) -> Mapping[NodeId, Node]:
        """
        Return a read-only snapshot of the topology nodes.
        """
        return MappingProxyType(deepcopy(self._nodes))

    @property
    def links(self) -> Mapping[LinkId, Link]:
        """
        Return a read-only snapshot of the topology links.
        """
        return MappingProxyType(deepcopy(self._links))

    @property
    def policies(self) -> Mapping[PolicyId, Policy]:
        """
        Return a read-only snapshot of the topology policies.
        """
        return MappingProxyType(deepcopy(self._policies))

    @property
    def metrics(self) -> Metrics:
        """
        Return a defensive copy of the topology metrics.
        """
        return deepcopy(self._metrics)

    def set_metrics(self, metrics: Metrics) -> None:
            """
            Replace the topology metrics with a defensive copy.

            Raises:
                TypeError: If the provided object is not a Metrics instance.
            """
            if not isinstance(metrics, Metrics):
                raise TypeError("metrics must be an instance of Metrics.")

            self._metrics = deepcopy(metrics)


    # =========================================================================
    # Python Protocols
    # =========================================================================

    def __len__(self) -> int:
        """
        Return the number of nodes in the topology.
        """
        return len(self._nodes)

    def __iter__(self) -> Iterator[Node]:
        """Iterate over a snapshot of the topology nodes."""
        return iter(deepcopy(tuple(self._nodes.values())))

    def __contains__(self, item: object) -> bool:
        """
        Return True if a node identifier exists in the topology.
        """
        if not isinstance(item, str):
            return False

        return item in self._nodes

    def __repr__(self) -> str:
        """
        Return a concise string representation of the topology.
        """
        return (
            f"{self.__class__.__name__}("
            f"name={self._metadata.name!r}, "
            f"nodes={len(self._nodes)}, "
            f"links={len(self._links)}, "
            f"policies={len(self._policies)})"
        )

    # =========================================================================
    # Node Operations
    # =========================================================================

    def add_node(self, node: Node) -> None:
        """
        Add a node to the topology.

        Raises:
            TypeError: If the provided object is not a Node.
            ValueError: If a node with the same identifier already exists.
        """
        if not isinstance(node, Node):
            raise TypeError("node must be an instance of Node.")

        if node.id in self._nodes:
            raise ValueError(f"Node with ID '{node.id}' already exists.")

        self._nodes[node.id] = deepcopy(node)

    def get_node(self, node_id: NodeId) -> Node:
        """
        Return a defensive copy of a node.

        Raises:
            KeyError: If the node identifier does not exist.
        """
        try:
            node = self._nodes[node_id]
        except KeyError:
            raise KeyError(
                f"Node with ID '{node_id}' does not exist."
            ) from None

        return deepcopy(node)

    def has_node(self, node_id: NodeId) -> bool:
        """
        Return True if a node with the given identifier exists.
        """
        return node_id in self._nodes

    def remove_node(self, node_id: NodeId) -> None:
        """
        Remove a node from the topology.

        Raises:
            KeyError: If the node identifier does not exist.
            ValueError: If the node is referenced by existing links.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node with ID '{node_id}' does not exist.")

        for link in self._links.values():
            if link.source == node_id or link.destination == node_id:
                raise ValueError(
                    f"Cannot remove node '{node_id}': "
                    f"it is referenced by link '{link.id}'."
                )

        del self._nodes[node_id]

    # =========================================================================
    # Link Operations
    # =========================================================================

    def add_link(self, link: Link) -> None:
        """
        Add a link to the topology.

        Raises:
            TypeError: If the provided object is not a Link.
            ValueError: If the link identifier already exists, either endpoint
                does not exist, or the link connects a node to itself.
        """
        if not isinstance(link, Link):
            raise TypeError("link must be an instance of Link.")

        if link.id in self._links:
            raise ValueError(
                f"Link with ID '{link.id}' already exists."
            )

        if link.source not in self._nodes:
            raise ValueError(
                f"Source node '{link.source}' does not exist."
            )

        if link.destination not in self._nodes:
            raise ValueError(
                f"Destination node '{link.destination}' does not exist."
            )

        if link.source == link.destination:
            raise ValueError(
                f"Link '{link.id}' cannot connect a node to itself."
            )

        self._links[link.id] = deepcopy(link)

    def get_link(self, link_id: LinkId) -> Link:
        """
        Return a defensive copy of a link.

        Raises:
            KeyError: If the link identifier does not exist.
        """
        try:
            link = self._links[link_id]
        except KeyError:
            raise KeyError(
                f"Link with ID '{link_id}' does not exist."
            ) from None

        return deepcopy(link)

    def has_link(self, link_id: LinkId) -> bool:
        """
        Return True if a link with the given identifier exists.
        """
        return link_id in self._links

    def remove_link(self, link_id: LinkId) -> None:
        """
        Remove a link from the topology.

        Raises:
            KeyError: If the link identifier does not exist.
        """
        if link_id not in self._links:
            raise KeyError(
                f"Link with ID '{link_id}' does not exist."
            )

        del self._links[link_id]

    # =========================================================================
    # Policy Operations
    # =========================================================================

    def add_policy(self, policy: Policy) -> None:
        """
        Add a policy to the topology.

        Raises:
            TypeError: If the provided object is not a Policy.
            ValueError: If a policy with the same identifier already exists.
        """
        if not isinstance(policy, Policy):
            raise TypeError("policy must be an instance of Policy.")

        if policy.id in self._policies:
            raise ValueError(
                f"Policy with ID '{policy.id}' already exists."
            )

        self._policies[policy.id] = deepcopy(policy)


    def get_policy(self, policy_id: PolicyId) -> Policy:
        """
        Return a defensive copy of a policy.

        Raises:
            KeyError: If the policy identifier does not exist.
        """
        try:
            policy = self._policies[policy_id]
        except KeyError:
            raise KeyError(
                f"Policy with ID '{policy_id}' does not exist."
            ) from None

        return deepcopy(policy)


    def has_policy(self, policy_id: PolicyId) -> bool:
        """
        Return True if a policy with the given identifier exists.
        """
        return policy_id in self._policies


    def remove_policy(self, policy_id: PolicyId) -> None:
        """
        Remove a policy from the topology.

        Raises:
            KeyError: If the policy identifier does not exist.
        """
        if policy_id not in self._policies:
            raise KeyError(
                f"Policy with ID '{policy_id}' does not exist."
            )

        del self._policies[policy_id]

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def is_structurally_valid(self) -> bool:
        """
        Return True if the topology satisfies basic structural constraints.

        Checks that every link references existing nodes and that no link
        connects a node to itself.
        """
        for link in self._links.values():
            if link.source not in self._nodes:
                return False

            if link.destination not in self._nodes:
                return False

            if link.source == link.destination:
                return False

        return True
