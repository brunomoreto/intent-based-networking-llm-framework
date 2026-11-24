import json

from framework.core.topology.serialization import deserialize_topology
from framework.core.topology.validation import (
    validate_document,
    validate_topology,
)

FILE = "router_topology_v2.json"

# 1. Load JSON
with open(FILE, "r", encoding="utf-8") as f:
    document = json.load(f)

# 2. Validate JSON document
document_report = validate_document(document)

print("\n=== DOCUMENT VALIDATION ===")
print(f"Valid: {document_report.valid}")
print(f"Errors: {document_report.error_count}")
print(f"Warnings: {document_report.warning_count}")

for issue in document_report.issues:
    print(issue)

if not document_report.valid:
    raise SystemExit("Document validation failed.")

# 3. Deserialize JSON into Topology
topology = deserialize_topology(document)

# 4. Validate Topology object
topology_report = validate_topology(topology)

print("\n=== TOPOLOGY VALIDATION ===")
print(f"Valid: {topology_report.valid}")
print(f"Errors: {topology_report.error_count}")
print(f"Warnings: {topology_report.warning_count}")

for issue in topology_report.issues:
    print(issue)

if not topology_report.valid:
    raise SystemExit("Topology validation failed.")

print("\nSUCCESS: Both validations passed.")
