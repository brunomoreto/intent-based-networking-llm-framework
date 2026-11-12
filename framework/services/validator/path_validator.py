
from framework.core.topology.enums import LinkStatus
from framework.core.topology.topology import Topology


def validate_path(
    topology: Topology,
    path: list[str] | None,
    source: str,
    destination: str,
    failed_link_id: str | None = None,
) -> bool:
    """
    Validate a path independently of the algorithm that produced it.

    The path is represented as a sequence of Node IDs. Connectivity
    between consecutive Nodes is verified through active Links
    connecting their Interfaces and their enabled directions.

    Args:
        topology: Topology V2 aggregate.
        path: Sequence of Node IDs representing the path.
        source: Expected source Node ID.
        destination: Expected destination Node ID.
        failed_link_id: Optional Link ID to exclude from validation.

    Returns:
        True when the path is valid; otherwise, False.
    """

    if not isinstance(topology, Topology):
        raise TypeError("topology must be a Topology instance.")

    if not path:
        return False

    if path[0] != source or path[-1] != destination:
        return False

    # Every Node in the path must exist.
    if any(not topology.has_node(node_id) for node_id in path):
        return False

    # A path must not contain repeated Nodes.
    if len(path) != len(set(path)):
        return False

    # Map each Interface ID to its owning Node ID.
    interface_to_node: dict[str, str] = {}

    for node in topology.nodes.values():
        for interface in node.interfaces:
            interface_to_node[interface.id] = node.id

    links = topology.links

    # Validate each consecutive Node pair independently.
    for current, neighbor in zip(path, path[1:]):

        hop_is_valid = False

        for link in links.values():

            # Exclude the specified failed Link.
            if link.id == failed_link_id:
                continue

            # Only active Links can provide connectivity.
            if link.status != LinkStatus.ACTIVE:
                continue

            source_node = interface_to_node.get(
                link.source_interface_id
            )

            destination_node = interface_to_node.get(
                link.destination_interface_id
            )

            # Ignore Links whose Interfaces cannot be resolved.
            if source_node is None or destination_node is None:
                continue

            # Forward direction: source Node -> destination Node.
            if (
                source_node == current
                and destination_node == neighbor
                and link.forward.enabled
            ):
                hop_is_valid = True
                break

            # Reverse direction: destination Node -> source Node.
            # Reverse connectivity exists only when explicitly declared.
            if (
                source_node == neighbor
                and destination_node == current
                and link.reverse is not None
                and link.reverse.enabled
            ):
                hop_is_valid = True
                break

        if not hop_is_valid:
            return False

    return True
