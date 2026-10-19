
from pathlib import Path

from framework.core.topology.serialization import load_topology
from framework.services.executor.experiment_executor import run_experiment
from framework.services.validator.path_validator import validate_path


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "n1"
    / "redundant_topology.json"
)


def test_accepts_valid_alternative_path():
    topology = load_topology(DATASET_PATH)
    topology.remove_link("l2")

    path = ["h1", "s1", "s3", "s4", "h2"]

    assert validate_path(
        topology,
        path,
        source="h1",
        destination="h2",
        failed_link_id="l2",
    )


def test_rejects_path_using_failed_link():
    topology = load_topology(DATASET_PATH)

    path = ["h1", "s1", "s2", "s4", "h2"]

    assert not validate_path(
        topology,
        path,
        source="h1",
        destination="h2",
        failed_link_id="l2",
    )


def test_rejects_path_with_nonexistent_node():
    topology = load_topology(DATASET_PATH)

    path = ["h1", "s1", "missing", "h2"]

    assert not validate_path(
        topology,
        path,
        source="h1",
        destination="h2",
    )


def test_rejects_path_with_wrong_destination():
    topology = load_topology(DATASET_PATH)

    path = ["h1", "s1", "s3"]

    assert not validate_path(
        topology,
        path,
        source="h1",
        destination="h2",
    )


def test_rejects_path_that_uses_inactive_link():
    topology = load_topology(DATASET_PATH)
    topology.remove_link("l2")

    path = ["h1", "s1", "s2", "s4", "h2"]

    assert not validate_path(
        topology,
        path,
        source="h1",
        destination="h2",
    )
