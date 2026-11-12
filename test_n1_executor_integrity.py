
import json

from framework.core.topology.serialization import load_topology
from framework.services.executor.experiment_executor import run_experiment


dataset_path = "datasets/n1/redundant_topology.json"

# Load the original topology.
original_topology = load_topology(dataset_path)

# Capture the original aggregate state.
original_node_ids = set(original_topology.nodes.keys())
original_link_ids = set(original_topology.links.keys())
original_controller_ids = set(original_topology.controllers.keys())
original_association_ids = set(
    original_topology.controller_associations.keys()
)
original_policy_ids = set(original_topology.policies.keys())
original_metrics = original_topology.metrics

# Execute an experiment with failure of l2.
result = run_experiment(
    topology_path=dataset_path,
    source="h1",
    destination="h2",
    failed_link_id="l2",
)

# Verify that the original aggregate remains unchanged.
assert set(original_topology.nodes.keys()) == original_node_ids
assert set(original_topology.links.keys()) == original_link_ids
assert set(original_topology.controllers.keys()) == original_controller_ids
assert (
    set(original_topology.controller_associations.keys())
    == original_association_ids
)
assert set(original_topology.policies.keys()) == original_policy_ids
assert original_topology.metrics == original_metrics

# The original link must still exist.
assert original_topology.has_link("l2")

# The experiment must have succeeded.
assert result.success

print("Original topology integrity: OK")
print("Original link l2 preserved: OK")
print("Experiment execution: OK")
print("\nAll N1 aggregate integrity tests passed.")
