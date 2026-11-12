import json
from pathlib import Path

from framework.core.topology.serialization import deserialize_topology
from framework.core.topology.validation import validate_topology


dataset_path = Path("datasets/n1/redundant_topology.json")

document = json.loads(dataset_path.read_text(encoding="utf-8"))
topology = deserialize_topology(document)

report = validate_topology(topology)

print(f"Topology ID: {topology.metadata.id}")
print(f"Nodes: {len(topology.nodes)}")
print(f"Links: {len(topology.links)}")
print(f"Controllers: {len(topology.controllers)}")
print(f"Policies: {len(topology.policies)}")
print(f"Validation errors: {len(report.errors)}")
print(f"Validation warnings: {len(report.warnings)}")
print(f"Validation infos: {len(report.infos)}")

for issue in report.issues:
    print(f"{issue.severity.value}: {issue.code} - {issue.message}")

assert len(topology.nodes) == 6
assert len(topology.links) == 6
assert report.valid, "Topology validation failed."

print("\nN1 V2 dataset validation: OK")
