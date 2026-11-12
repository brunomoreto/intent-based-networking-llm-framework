
from framework.core.topology.entities import (
    Host,
    Interface,
    Link,
    LinkDirection,
    Metadata,
    Switch,
)
from framework.core.topology.enums import LinkStatus
from framework.core.topology.topology import Topology
from framework.services.path_finder import find_path


def create_topology() -> Topology:
    """Create a minimal V2 topology for path-finding tests."""

    topology = Topology(
        metadata=Metadata(
            id="topology-test",
            name="Path Finder V2 Test",
        )
    )

    topology.add_node(
        Host(
            id="h1",
            name="Host 1",
            interfaces=[
                Interface(id="h1-eth0", name="eth0"),
                Interface(id="h1-eth1", name="eth1"),
            ],
        )
    )

    topology.add_node(
        Switch(
            id="s1",
            name="Switch 1",
            interfaces=[
                Interface(id="s1-eth0", name="eth0"),
                Interface(id="s1-eth1", name="eth1"),
            ],
        )
    )

    topology.add_node(
        Host(
            id="h2",
            name="Host 2",
            interfaces=[
                Interface(id="h2-eth0", name="eth0"),
                Interface(id="h2-eth1", name="eth1"),
            ],
        )
    )

    return topology


def create_direction(enabled: bool = True) -> LinkDirection:
    return LinkDirection(
        bandwidth=1000,
        delay=1,
        weight=1,
        packet_loss=0,
        enabled=enabled,
    )


def test_active_enabled_direction():
    """An active Link with enabled forward direction must be usable."""

    topology = create_topology()

    topology.add_link(
        Link(
            id="l1",
            source_interface_id="h1-eth0",
            destination_interface_id="s1-eth0",
            forward=create_direction(enabled=True),
        )
    )

    topology.add_link(
        Link(
            id="l2",
            source_interface_id="s1-eth1",
            destination_interface_id="h2-eth0",
            forward=create_direction(enabled=True),
        )
    )

    path = find_path(topology, "h1", "h2")

    assert path == ["h1", "s1", "h2"]


def test_disabled_direction():
    """A disabled forward direction must not be used."""

    topology = create_topology()

    topology.add_link(
        Link(
            id="l1",
            source_interface_id="h1-eth0",
            destination_interface_id="s1-eth0",
            forward=create_direction(enabled=False),
        )
    )

    path = find_path(topology, "h1", "s1")

    assert path is None


def test_reverse_direction_not_inferred():
    """A missing reverse direction must not be inferred."""

    topology = create_topology()

    topology.add_link(
        Link(
            id="l1",
            source_interface_id="h1-eth0",
            destination_interface_id="s1-eth0",
            forward=create_direction(enabled=True),
            reverse=None,
        )
    )

    path = find_path(topology, "s1", "h1")

    assert path is None


def test_parallel_links():
    """A usable parallel Link must preserve connectivity."""

    topology = create_topology()

    topology.add_link(
        Link(
            id="l1",
            source_interface_id="h1-eth0",
            destination_interface_id="s1-eth0",
            forward=create_direction(enabled=False),
        )
    )

    topology.add_link(
        Link(
            id="l2",
            source_interface_id="h1-eth1",
            destination_interface_id="s1-eth1",
            forward=create_direction(enabled=True),
        )
    )

    path = find_path(topology, "h1", "s1")

    assert path == ["h1", "s1"]


def test_failed_link():
    """A FAILED Link must not be used."""

    topology = create_topology()

    topology.add_link(
        Link(
            id="l1",
            source_interface_id="h1-eth0",
            destination_interface_id="s1-eth0",
            forward=create_direction(enabled=True),
            status=LinkStatus.FAILED,
        )
    )

    path = find_path(topology, "h1", "s1")

    assert path is None


def test_no_available_path():
    """The function must return None when no path exists."""

    topology = create_topology()

    path = find_path(topology, "h1", "h2")

    assert path is None


if __name__ == "__main__":
    tests = [
        test_active_enabled_direction,
        test_disabled_direction,
        test_reverse_direction_not_inferred,
        test_parallel_links,
        test_failed_link,
        test_no_available_path,
    ]

    for test in tests:
        test()
        print(f"{test.__name__}: OK")

    print("\nAll Path Finder V2 tests passed.")
