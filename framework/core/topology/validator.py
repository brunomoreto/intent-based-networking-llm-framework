
"""Structural validation for network topologies."""

from .exceptions import TopologyValidationError
from .topology import Topology


def validate_topology(topology: Topology) -> None:
    """Validate the structural consistency of a topology.

    Args:
        topology: The topology to validate.

    Raises:
        TypeError: If the provided object is not a Topology.
        TopologyValidationError: If structural inconsistencies are found.
    """
    if not isinstance(topology, Topology):
        raise TypeError("topology must be an instance of Topology.")

    node_ids = list(topology.nodes.keys())
    link_ids = list(topology.links.keys())

    if len(node_ids) != len(set(node_ids)):
        raise TopologyValidationError(
            "Topology contains duplicate node identifiers."
        )

    if len(link_ids) != len(set(link_ids)):
        raise TopologyValidationError(
            "Topology contains duplicate link identifiers."
        )

    existing_node_ids = set(node_ids)

    for link in topology.links.values():
        if link.source not in existing_node_ids:
            raise TopologyValidationError(
                f"Link '{link.id}' references non-existent "
                f"source node '{link.source}'."
            )

        if link.destination not in existing_node_ids:
            raise TopologyValidationError(
                f"Link '{link.id}' references non-existent "
                f"destination node '{link.destination}'."
            )

        if link.source == link.destination:
            raise TopologyValidationError(
                f"Link '{link.id}' cannot connect a node to itself."
            )


__all__ = ["validate_topology"]
