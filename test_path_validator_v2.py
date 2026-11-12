
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
from framework.services.validator.path_validator import validate_path


def create_topology() -> Topology:
    topology = Topology(
        metadata=Metadata(
            id="topology-validator-test",
            name="Path Validator V2 Test",
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


def add_link(
    topology: Topology,
    link_id: str,
    source_interface: str,
    destination_interface: str,
    *,
    forward_enabled: bool = True,
    reverse: LinkDirection | None = None,
    status: LinkStatus = LinkStatus.ACTIVE,
) -> None:
    topology.add_link(
        Link(
            id=link_id,
            source_interface_id=source_interface,
            destination_interface_id=destination_interface,
            forward=create_direction(forward_enabled),
            reverse=reverse,
            status=status,
        )
    )


def test_valid_path():
    topology = create_topology()

    add_link(topology, "l1", "h1-eth0", "s1-eth0")
    add_link(topology, "l2", "s1-eth1", "h2-eth0")

    assert validate_path(
        topology,
        ["h1", "s1", "h2"],
        "h1",
        "h2",
    )


def test_invalid_source():
    topology = create_topology()

    assert not validate_path(
        topology,
        ["s1", "h2"],
        "h1",
        "h2",
    )


def test_nonexistent_node():
    topology = create_topology()

    assert not validate_path(
        topology,
        ["h1", "unknown", "h2"],
        "h1",
        "h2",
    )


def test_repeated_node():
    topology = create_topology()

    assert not validate_path(
        topology,
        ["h1", "s1", "h1", "h2"],
        "h1",
        "h2",
    )


def test_disabled_direction():
    topology = create_topology()

    add_link(
        topology,
        "l1",
        "h1-eth0",
        "s1-eth0",
        forward_enabled=False,
    )

    assert not validate_path(
        topology,
        ["h1", "s1"],
        "h1",
        "s1",
    )


def test_reverse_direction_not_inferred():
    topology = create_topology()

    add_link(topology, "l1", "h1-eth0", "s1-eth0")

    assert not validate_path(
        topology,
        ["s1", "h1"],
        "s1",
        "h1",
    )


def test_explicit_reverse_direction():
    topology = create_topology()

    add_link(
        topology,
        "l1",
        "h1-eth0",
        "s1-eth0",
        reverse=create_direction(enabled=True),
    )

    assert validate_path(
        topology,
        ["s1", "h1"],
        "s1",
        "h1",
    )


def test_failed_link():
    topology = create_topology()

    add_link(
        topology,
        "l1",
        "h1-eth0",
        "s1-eth0",
        status=LinkStatus.FAILED,
    )

    assert not validate_path(
        topology,
        ["h1", "s1"],
        "h1",
        "s1",
    )


def test_parallel_links():
    topology = create_topology()

    add_link(
        topology,
        "l1",
        "h1-eth0",
        "s1-eth0",
        forward_enabled=False,
    )

    add_link(
        topology,
        "l2",
        "h1-eth1",
        "s1-eth1",
        forward_enabled=True,
    )

    assert validate_path(
        topology,
        ["h1", "s1"],
        "h1",
        "s1",
    )


def test_failed_link_exclusion():
    topology = create_topology()

    add_link(topology, "l1", "h1-eth0", "s1-eth0")
    add_link(topology, "l2", "h1-eth1", "s1-eth1")

    assert validate_path(
        topology,
        ["h1", "s1"],
        "h1",
        "s1",
        failed_link_id="l1",
    )

    assert not validate_path(
        topology,
        ["h1", "s1"],
        "h1",
        "s1",
        failed_link_id="l1",
    ) is False


def test_empty_path():
    topology = create_topology()

    assert not validate_path(
        topology,
        [],
        "h1",
        "h2",
    )


def test_no_path():
    topology = create_topology()

    assert not validate_path(
        topology,
        ["h1", "s1", "h2"],
        "h1",
        "h2",
    )

def test_failed_link_exclusion_removes_only_path():
    """Excluding the only available Link must invalidate the path."""

    topology = create_topology()

    add_link(topology, "l1", "h1-eth0", "s1-eth0")

    assert not validate_path(
        topology,
        ["h1", "s1"],
        "h1",
        "s1",
        failed_link_id="l1",
    )

if __name__ == "__main__":
    tests = [
        test_valid_path,
        test_invalid_source,
        test_nonexistent_node,
        test_repeated_node,
        test_disabled_direction,
        test_reverse_direction_not_inferred,
        test_explicit_reverse_direction,
        test_failed_link,
        test_parallel_links,
        test_failed_link_exclusion,
        test_empty_path,
        test_no_path,
        test_failed_link_exclusion_removes_only_path,
    ]

    for test in tests:
        test()
        print(f"{test.__name__}: OK")

    print("\nAll Path Validator V2 tests passed.")
