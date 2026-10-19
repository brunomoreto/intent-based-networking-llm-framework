
from collections import deque

from framework.core.topology.enums import LinkStatus
from framework.core.topology.topology import Topology


def find_path(
    topology: Topology,
    source: str,
    destination: str,
) -> list[str] | None:
    """Find a shortest-hop path using active links and BFS."""

    if not topology.has_node(source):
        raise KeyError(f"Source node '{source}' does not exist.")

    if not topology.has_node(destination):
        raise KeyError(
            f"Destination node '{destination}' does not exist."
        )

    if source == destination:
        return [source]

    adjacency: dict[str, list[str]] = {
        node_id: [] for node_id in topology.nodes
    }

    for link in topology.links.values():
        if link.status != LinkStatus.ACTIVE:
            continue

        adjacency[link.source].append(link.destination)

        if link.bidirectional:
            adjacency[link.destination].append(link.source)

    queue = deque([source])
    predecessor: dict[str, str | None] = {source: None}

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
