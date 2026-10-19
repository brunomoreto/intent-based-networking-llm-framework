
from framework.core.topology.enums import LinkStatus
from framework.core.topology.topology import Topology


def validate_path(
    topology: Topology,
    path: list[str] | None,
    source: str,
    destination: str,
    failed_link_id: str | None = None,
) -> bool:
    """Validate a path independently of the algorithm that produced it."""

    if not isinstance(topology, Topology):
        raise TypeError("topology must be an instance of Topology.")

    if not path:
        return False

    if path[0] != source or path[-1] != destination:
        return False

    if any(not topology.has_node(node_id) for node_id in path):
        return False

    if len(path) != len(set(path)):
        return False

    links = topology.links

    for current, neighbor in zip(path, path[1:]):
        matching_link = None

        for link in links.values():
            if link.id == failed_link_id:
                continue

            if link.status != LinkStatus.ACTIVE:
                continue

            if link.source == current and link.destination == neighbor:
                matching_link = link
                break

            if (
                link.bidirectional
                and link.source == neighbor
                and link.destination == current
            ):
                matching_link = link
                break

        if matching_link is None:
            return False

    return True
