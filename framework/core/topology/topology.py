
"""Topology Domain - Aggregate Root.

This module implements the Topology V2 aggregate.

Topology owns the domain entities and protects its internal state
through defensive copying and read-only collection views.
"""

from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Iterator, Mapping

from .entities import (
    Controller,
    ControllerAssociation,
    Link,
    Metadata,
    Metrics,
    Node,
    Policy,
)
from .types import (
    AssociationId,
    ControllerId,
    InterfaceId,
    LinkId,
    NodeId,
    PolicyId,
)


class Topology:
    """Aggregate Root for a network topology.

    Metadata, Nodes, Links, Controllers, Controller Associations,
    Policies and Metrics are owned by this aggregate.
    """

    def __init__(self, metadata: Metadata) -> None:
        self._metadata = deepcopy(metadata)

        self._nodes: dict[NodeId, Node] = {}
        self._links: dict[LinkId, Link] = {}
        self._controllers: dict[ControllerId, Controller] = {}
        self._controller_associations: dict[
            AssociationId, ControllerAssociation
        ] = {}
        self._policies: dict[PolicyId, Policy] = {}

        self._metrics = Metrics()

    # =========================================================================
    # Metadata
    # =========================================================================

    @property
    def metadata(self) -> Metadata:
        """Return a defensive copy of topology metadata."""
        return deepcopy(self._metadata)

    def set_metadata(self, metadata: Metadata) -> None:
        """Replace topology metadata using a defensive copy."""
        self._metadata = deepcopy(metadata)

    # =========================================================================
    # Nodes
    # =========================================================================

    @property
    def nodes(self) -> Mapping[NodeId, Node]:
        """Return a read-only snapshot of Nodes."""
        return MappingProxyType(deepcopy(self._nodes))

    def add_node(self, node: Node) -> None:
        """Add a Node to the aggregate."""
        if node.id in self._nodes:
            raise ValueError(f"Node already exists: {node.id}")

        self._nodes[node.id] = deepcopy(node)

    def get_node(self, node_id: NodeId) -> Node:
        """Return a defensive copy of a Node."""
        try:
            return deepcopy(self._nodes[node_id])
        except KeyError:
            raise KeyError(f"Node not found: {node_id}") from None

    def has_node(self, node_id: NodeId) -> bool:
        """Check whether a Node exists."""
        return node_id in self._nodes

    def remove_node(self, node_id: NodeId) -> Node:
        """Remove a Node from the aggregate.

        A Node referenced by a Link or ControllerAssociation
        cannot be removed until those references are removed.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node not found: {node_id}")

        incident_links = [
            link.id
            for link in self._links.values()
            if (
                self._interface_belongs_to_node(
                    link.source_interface_id,
                    node_id,
                )
                or self._interface_belongs_to_node(
                    link.destination_interface_id,
                    node_id,
                )
            )
        ]

        if incident_links:
            raise ValueError(
                f"Cannot remove Node {node_id}: "
                f"incident Links exist: {incident_links}"
            )

        associations = [
            association.id
            for association in self._controller_associations.values()
            if association.node_id == node_id
        ]

        if associations:
            raise ValueError(
                f"Cannot remove Node {node_id}: "
                f"ControllerAssociations exist: {associations}"
            )

        return deepcopy(self._nodes.pop(node_id))

    def _interface_belongs_to_node(
        self,
        interface_id: InterfaceId,
        node_id: NodeId,
    ) -> bool:
        """Check whether an Interface belongs to a Node."""
        node = self._nodes.get(node_id)

        if node is None:
            return False

        return any(
            interface.id == interface_id
            for interface in node.interfaces
        )

    # =========================================================================
    # Links
    # =========================================================================

    @property
    def links(self) -> Mapping[LinkId, Link]:
        """Return a read-only snapshot of Links."""
        return MappingProxyType(deepcopy(self._links))

    def add_link(self, link: Link) -> None:
        """Add a Link to the aggregate."""
        if link.id in self._links:
            raise ValueError(f"Link already exists: {link.id}")

        self._links[link.id] = deepcopy(link)

    def get_link(self, link_id: LinkId) -> Link:
        """Return a defensive copy of a Link."""
        try:
            return deepcopy(self._links[link_id])
        except KeyError:
            raise KeyError(f"Link not found: {link_id}") from None

    def has_link(self, link_id: LinkId) -> bool:
        """Check whether a Link exists."""
        return link_id in self._links

    def remove_link(self, link_id: LinkId) -> Link:
        """Remove a Link and return a defensive copy."""
        try:
            return deepcopy(self._links.pop(link_id))
        except KeyError:
            raise KeyError(f"Link not found: {link_id}") from None

    # =========================================================================
    # Controllers
    # =========================================================================

    @property
    def controllers(self) -> Mapping[ControllerId, Controller]:
        """Return a read-only snapshot of Controllers."""
        return MappingProxyType(deepcopy(self._controllers))

    def add_controller(self, controller: Controller) -> None:
        """Add a Controller to the aggregate."""
        if controller.id in self._controllers:
            raise ValueError(
                f"Controller already exists: {controller.id}"
            )

        self._controllers[controller.id] = deepcopy(controller)

    def get_controller(self, controller_id: ControllerId) -> Controller:
        """Return a defensive copy of a Controller."""
        try:
            return deepcopy(self._controllers[controller_id])
        except KeyError:
            raise KeyError(
                f"Controller not found: {controller_id}"
            ) from None

    def has_controller(self, controller_id: ControllerId) -> bool:
        """Check whether a Controller exists."""
        return controller_id in self._controllers

    def remove_controller(
        self,
        controller_id: ControllerId,
    ) -> Controller:
        """Remove a Controller.

        A Controller referenced by an association cannot be removed
        until its associations are removed.
        """
        if controller_id not in self._controllers:
            raise KeyError(f"Controller not found: {controller_id}")

        associations = [
            association.id
            for association in self._controller_associations.values()
            if association.controller_id == controller_id
        ]

        if associations:
            raise ValueError(
                f"Cannot remove Controller {controller_id}: "
                f"ControllerAssociations exist: {associations}"
            )

        return deepcopy(self._controllers.pop(controller_id))

    # =========================================================================
    # Controller Associations
    # =========================================================================

    @property
    def controller_associations(
        self,
    ) -> Mapping[AssociationId, ControllerAssociation]:
        """Return a read-only snapshot of ControllerAssociations."""
        return MappingProxyType(
            deepcopy(self._controller_associations)
        )

    def add_controller_association(
        self,
        association: ControllerAssociation,
    ) -> None:
        """Add a ControllerAssociation to the aggregate."""
        if association.id in self._controller_associations:
            raise ValueError(
                f"ControllerAssociation already exists: {association.id}"
            )

        self._controller_associations[association.id] = deepcopy(
            association
        )

    def get_controller_association(
        self,
        association_id: AssociationId,
    ) -> ControllerAssociation:
        """Return a defensive copy of a ControllerAssociation."""
        try:
            return deepcopy(
                self._controller_associations[association_id]
            )
        except KeyError:
            raise KeyError(
                f"ControllerAssociation not found: {association_id}"
            ) from None

    def has_controller_association(
        self,
        association_id: AssociationId,
    ) -> bool:
        """Check whether a ControllerAssociation exists."""
        return association_id in self._controller_associations

    def remove_controller_association(
        self,
        association_id: AssociationId,
    ) -> ControllerAssociation:
        """Remove a ControllerAssociation."""
        try:
            return deepcopy(
                self._controller_associations.pop(association_id)
            )
        except KeyError:
            raise KeyError(
                f"ControllerAssociation not found: {association_id}"
            ) from None

    # =========================================================================
    # Policies
    # =========================================================================

    @property
    def policies(self) -> Mapping[PolicyId, Policy]:
        """Return a read-only snapshot of Policies."""
        return MappingProxyType(deepcopy(self._policies))

    def add_policy(self, policy: Policy) -> None:
        """Add a Policy to the aggregate."""
        if policy.id in self._policies:
            raise ValueError(f"Policy already exists: {policy.id}")

        self._policies[policy.id] = deepcopy(policy)

    def get_policy(self, policy_id: PolicyId) -> Policy:
        """Return a defensive copy of a Policy."""
        try:
            return deepcopy(self._policies[policy_id])
        except KeyError:
            raise KeyError(f"Policy not found: {policy_id}") from None

    def has_policy(self, policy_id: PolicyId) -> bool:
        """Check whether a Policy exists."""
        return policy_id in self._policies

    def remove_policy(self, policy_id: PolicyId) -> Policy:
        """Remove a Policy."""
        try:
            return deepcopy(self._policies.pop(policy_id))
        except KeyError:
            raise KeyError(f"Policy not found: {policy_id}") from None

    # =========================================================================
    # Metrics
    # =========================================================================

    @property
    def metrics(self) -> Metrics:
        """Return a defensive copy of Metrics."""
        return deepcopy(self._metrics)

    def set_metrics(self, metrics: Metrics) -> None:
        """Replace Metrics using a defensive copy."""
        self._metrics = deepcopy(metrics)

    # =========================================================================
    # Collection Protocols
    # =========================================================================

    def __len__(self) -> int:
        """Return the number of Nodes."""
        return len(self._nodes)

    def __iter__(self) -> Iterator[Node]:
        """Iterate over defensive copies of Nodes."""
        return iter(deepcopy(list(self._nodes.values())))

    def __contains__(self, node_id: object) -> bool:
        """Check whether a Node ID exists."""
        return node_id in self._nodes

    def __repr__(self) -> str:
        return (
            f"Topology("
            f"name={self._metadata.name!r}, "
            f"nodes={len(self._nodes)}, "
            f"links={len(self._links)}, "
            f"policies={len(self._policies)}"
            f")"
        )

    # =========================================================================
    # Copy
    # =========================================================================

    def copy(self) -> Topology:
        """Return a fully independent copy of the aggregate."""
        copied = Topology(metadata=self._metadata)

        copied._nodes = deepcopy(self._nodes)
        copied._links = deepcopy(self._links)
        copied._controllers = deepcopy(self._controllers)
        copied._controller_associations = deepcopy(
            self._controller_associations
        )
        copied._policies = deepcopy(self._policies)
        copied._metrics = deepcopy(self._metrics)

        return copied
