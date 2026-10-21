
from pathlib import Path

from framework.services.executor.experiment_executor import run_experiment


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "n1"
    / "redundant_topology.json"
)


def test_experiment_finds_alternative_path_after_link_failure():
    result = run_experiment(
        topology_path=DATASET_PATH,
        source="h1",
        destination="h2",
        failed_link_id="l2",
    )

    assert result.success is True
    assert result.path == ["h1", "s1", "s3", "s4", "h2"]
    assert result.failed_link_id == "l2"


def test_experiment_does_not_modify_original_dataset():
    original_topology = DATASET_PATH.read_text(encoding="utf-8")

    run_experiment(
        topology_path=DATASET_PATH,
        source="h1",
        destination="h2",
        failed_link_id="l2",
    )

    assert DATASET_PATH.read_text(encoding="utf-8") == original_topology


def test_experiment_reports_failure_when_no_path_exists():
    result = run_experiment(
        topology_path=DATASET_PATH,
        source="h1",
        destination="h2",
        failed_link_id="l1",
    )

    assert result.success is False
    assert result.path is None
    assert result.failed_link_id == "l1"


def test_experiment_records_execution_time():
    result = run_experiment(
        topology_path=DATASET_PATH,
        source="h1",
        destination="h2",
        failed_link_id="l2",
    )

    assert result.execution_time_ms >= 0


def test_experiment_records_path_computation_time():
    result = run_experiment(
        topology_path=DATASET_PATH,
        source="h1",
        destination="h2",
        failed_link_id="l2",
    )

    assert result.path_computation_time_ms >= 0


def test_experiment_records_validation_time():
    result = run_experiment(
        topology_path=DATASET_PATH,
        source="h1",
        destination="h2",
        failed_link_id="l2",
    )

    assert result.validation_time_ms >= 0
