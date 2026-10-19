
from pathlib import Path

import pytest

from framework.core.topology.enums import LinkStatus
from framework.core.topology.models import Link
from framework.core.topology.serialization import load_topology
from framework.services.path_finder import find_path


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "n1"
    / "redundant_topology.json"
)


def test_finds_path_in_redundant_topology():
    topology = load_topology(DATASET_PATH)

    path = find_path(topology, "h1", "h2")

    assert path is not None
    assert path[0] == "h1"
    assert path[-1] == "h2"
    assert len(path) == 5


def test_finds_alternative_path_after_link_failure():
    topology = load_topology(DATASET_PATH)
    topology.remove_link("l2")

    path = find_path(topology, "h1", "h2")

    assert path == ["h1", "s1", "s3", "s4", "h2"]


def test_returns_none_when_no_path_exists():
    topology = load_topology(DATASET_PATH)

    topology.remove_link("l1")

    assert find_path(topology, "h1", "h2") is None


def test_rejects_unknown_source_node():
    topology = load_topology(DATASET_PATH)

    with pytest.raises(KeyError):
        find_path(topology, "unknown", "h2")


def test_ignores_failed_links():
    topology = load_topology(DATASET_PATH)

    link = topology.get_link("l2")
    link.status = LinkStatus.FAILED

    # get_link returns a defensive copy; the stored link is unchanged.
    # Rebuild the topology with the failed link to test its status.
    topology.remove_link("l2")
    topology.add_link(
        Link(
            id="l2",
            source="s1",
            destination="s2",
            status=LinkStatus.FAILED,
        )
    )

    assert find_path(topology, "h1", "h2") == [
        "h1", "s1", "s3", "s4", "h2"
    ]


def test_respects_unidirectional_links():
    topology = load_topology(DATASET_PATH)

    # Replace l1 with a one-way link from h1 to s1.
    original_link = topology.get_link("l1")
    topology.remove_link("l1")
    topology.add_link(
        Link(
            id=original_link.id,
            source="h1",
            destination="s1",
            bidirectional=False,
        )
    )

    assert find_path(topology, "h1", "h2") is not None
    assert find_path(topology, "h2", "h1") is None
