
from collections import deque

from framework.core.topology.enums import LinkStatus
from framework.core.topology.topology import Topology


def find_path(
    topology: Topology,
    source: str,
    destination: str,
) -> list[str] | None:
    """
    Find a shortest-hop path between two Nodes using BFS.

    Only active Links and enabled directions are considered.

    A Link connects Interfaces rather than Nodes. Therefore, each
    Interface is resolved to its owning Node before building the
    adjacency graph.

    Parallel Links are supported. A connection between two Nodes
    is considered available when at least one Link provides a
    valid direction between them.

    Returns:
        A list of Node IDs representing the shortest-hop path,
        or None when no path exists.
    """

    if not isinstance(topology, Topology):
        raise TypeError("topology must be a Topology instance.")

    if not topology.has_node(source):
        raise KeyError(f"Source node '{source}' does not exist.")

    if not topology.has_node(destination):
        raise KeyError(
            f"Destination node '{destination}' does not exist."
        )

    if source == destination:
        return [source]

    # Map each Interface ID to its owning Node ID.
    interface_to_node: dict[str, str] = {}

    for node in topology.nodes.values():
        for interface in node.interfaces:
            interface_to_node[interface.id] = node.id

    # Initialize the adjacency list using Node IDs.
    adjacency: dict[str, list[str]] = {
        node_id: [] for node_id in topology.nodes
    }

    # Build the directed graph from active Links.
    for link in topology.links.values():

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

        # Links between Interfaces of the same Node are not
        # considered valid network connections.
        if source_node == destination_node:
            continue

        # Forward direction: source Node -> destination Node.
        if link.forward.enabled:
            adjacency[source_node].append(destination_node)

        # Reverse direction: destination Node -> source Node.
        # No reverse direction is inferred when reverse is None.
        if link.reverse is not None and link.reverse.enabled:
            adjacency[destination_node].append(source_node)

    # Breadth-First Search.
    queue = deque([source])

    predecessor: dict[str, str | None] = {
        source: None
    }

    while queue:
        current = queue.popleft()

        for neighbor in adjacency[current]:

            if neighbor in predecessor:
                continue

            predecessor[neighbor] = current

            if neighbor == destination:
                path = []
                node = destination

                while node is not None:
                    path.append(node)
                    node = predecessor[node]

                return list(reversed(path))

            queue.append(neighbor)

    return None
