
from framework.services.executor.experiment_executor import run_experiment


dataset_path = "datasets/n1/redundant_topology.json"

# Scenario 1: failure of l2.
result_1 = run_experiment(
    topology_path=dataset_path,
    source="h1",
    destination="h2",
    failed_link_id="l2",
)

print("\nScenario 1 - Failure of l2")
print("Success:", result_1.success)
print("Path:", result_1.path)
print("Execution time (ms):", result_1.execution_time_ms)

assert result_1.success
assert result_1.path == ["h1", "s1", "s3", "s4", "h2"]


# Scenario 2: failure of l3.
result_2 = run_experiment(
    topology_path=dataset_path,
    source="h1",
    destination="h2",
    failed_link_id="l3",
)

print("\nScenario 2 - Failure of l3")
print("Success:", result_2.success)
print("Path:", result_2.path)
print("Execution time (ms):", result_2.execution_time_ms)

assert result_2.success
assert result_2.path == ["h1", "s1", "s2", "s4", "h2"]

print("\nAll N1 experiment executor tests passed.")
