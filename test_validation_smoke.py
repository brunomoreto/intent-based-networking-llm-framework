from ipaddress import IPv4Interface

from framework.core.topology.entities import Host, Interface, Metadata
from framework.core.topology.topology import Topology
from framework.core.topology.serialization import serialize_topology
from framework.core.topology.validation import validate_document, validate_topology


topology = Topology(metadata=Metadata(id="topology-01", name="Validation smoke test"))

host_a = Host(
    id="host-a",
    name="Host A",
    interfaces=[
        Interface(
            id="if-a",
            name="eth0",
            ipv4_addresses=[
                IPv4Interface("192.0.2.10/24"),
                IPv4Interface("192.0.2.10/24"),
            ],
        )
    ],
)

host_b = Host(
    id="host-b",
    name="Host B",
    interfaces=[
        Interface(
            id="if-b",
            name="eth0",
            ipv4_addresses=[IPv4Interface("192.0.2.10/24")],
        )
    ],
)

topology.add_node(host_a)
topology.add_node(host_b)

document = serialize_topology(topology)
document_report = validate_document(document)
domain_report = validate_topology(topology)

assert document_report.valid, document_report.issues
assert domain_report.valid, domain_report.issues
assert any(issue.code == "INT-007" for issue in domain_report.issues)
assert any(issue.code == "INT-004" for issue in domain_report.issues)

print("Document validation: OK")
print("Domain validation: OK")
print(f"Document issues: {document_report.total_count}")
print(f"Domain issues: {domain_report.total_count}")
print("INT-004 and INT-007: OK")
