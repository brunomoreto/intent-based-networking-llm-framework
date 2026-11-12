
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from framework.services.validator.path_validator import validate_path
from framework.core.topology.serialization import load_topology
from framework.services.path_finder import find_path


@dataclass(frozen=True)
class ExperimentResult:
    """Result of a deterministic network recovery experiment."""

    success: bool
    path: list[str] | None
    failed_link_id: str
    execution_time_ms: float
    path_computation_time_ms: float
    validation_time_ms: float


def run_experiment(
    topology_path: str | Path,
    source: str,
    destination: str,
    failed_link_id: str,
) -> ExperimentResult:
    """Simulate a link failure and evaluate path recovery."""

    start_time = perf_counter()

    # Load the original V2 topology.
    original_topology = load_topology(topology_path)

    # Create an independent snapshot of the complete aggregate.
    experiment_topology = original_topology.copy()

    # Ensure the failed link exists before simulating its failure.
    if not experiment_topology.has_link(failed_link_id):
        raise KeyError(
            f"Link '{failed_link_id}' does not exist in the topology."
        )

    # Simulate the complete unavailability of the selected link.
    experiment_topology.remove_link(failed_link_id)

    # Compute an alternative path.
    path_start_time = perf_counter()

    path = find_path(
        experiment_topology,
        source,
        destination,
    )

    path_computation_time_ms = (
        perf_counter() - path_start_time
    ) * 1000

    # Independently validate the computed path.
    validation_start_time = perf_counter()

    success = validate_path(
        experiment_topology,
        path,
        source=source,
        destination=destination,
        failed_link_id=failed_link_id,
    )

    validation_time_ms = (
        perf_counter() - validation_start_time
    ) * 1000

    execution_time_ms = (
        perf_counter() - start_time
    ) * 1000

    return ExperimentResult(
        success=success,
        path=path,
        failed_link_id=failed_link_id,
        execution_time_ms=execution_time_ms,
        path_computation_time_ms=path_computation_time_ms,
        validation_time_ms=validation_time_ms,
    )
