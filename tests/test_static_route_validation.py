from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)
from framework.core.topology.enums import NodeType
import pytest

from framework.core.topology import (
    Host,
    Interface,
    Metadata,
    Router,
    StaticRoute,
    Topology,
    serialize_topology,
)
from framework.core.topology.validation import (
    validate_document,
    validate_topology,
)

def build_topology(
    *,
    host_route=None,
    router_route=None,
    host_extra_interfaces=None,
    host_node_type=None,
):
    topology = Topology(
        metadata=Metadata(
            id="validation-topology",
            name="Static Route Validation",
        )
    )

    host = Host(
        id="host-01",
        name="Host 01",
        interfaces=[
            Interface(
                id="host-01-eth0",
                name="eth0",
                ipv4_addresses=[
                    IPv4Interface("192.168.1.10/24")
                ],
            )
        ],
        static_routes=[host_route] if host_route else [],
    )

    if host_extra_interfaces:
        host.interfaces.extend(host_extra_interfaces)

    if host_node_type is not None:
        host.node_type = host_node_type

    topology.add_node(host)

    if router_route:
        router = Router(
            id="router-01",
            name="Router 01",
            ipv4_forwarding=True,
            interfaces=[
                Interface(
                    id="router-01-eth0",
                    name="eth0",
                    ipv4_addresses=[
                        IPv4Interface("192.168.2.1/24")
                    ],
                )
            ],
            static_routes=[router_route],
        )
        topology.add_node(router)

    return topology

def make_route(
    *,
    destination="10.20.0.0/16",
    next_hop="192.168.1.1",
    outgoing_interface_id="host-01-eth0",
    metric=10,
    route_id="host-route-01",
):
    return StaticRoute(
        id=route_id,
        destination=IPv4Network(destination),
        next_hop=IPv4Address(next_hop) if next_hop is not None else None,
        outgoing_interface_id=outgoing_interface_id,
        metric=metric,
    )


def document_with_host_route(route):
    document = serialize_topology(build_topology(host_route=make_route()))
    document_host = next(
        node for node in document["nodes"] if node["id"] == "host-01"
    )
    document_host["static_routes"] = [route]
    return document


def issue_codes(report):
    return {issue.code for issue in report.issues}


def test_document_accepts_valid_host_static_route():
    document = serialize_topology(build_topology(host_route=make_route()))

    report = validate_document(document)

    assert report.valid, report.issues


def test_domain_accepts_valid_host_static_route():
    topology = build_topology(host_route=make_route())

    report = validate_topology(topology)

    assert report.valid, report.issues


@pytest.mark.parametrize(
    "route",
    [
        make_route(
            destination="0.0.0.0/0",
            route_id="host-default-route",
            metric=100,
        ),
        make_route(
            destination="10.30.0.0/16",
            outgoing_interface_id=None,
            route_id="host-route-no-interface",
        ),
        make_route(
            destination="10.40.0.0/16",
            next_hop=None,
            route_id="host-route-interface-only",
        ),
    ],
)
def test_domain_accepts_supported_host_route_combinations(route):
    report = validate_topology(build_topology(host_route=route))

    assert report.valid, report.issues


@pytest.mark.parametrize(
    "route",
    [
        {
            "id": "host-default-route",
            "destination": "0.0.0.0/0",
            "next_hop": "192.168.1.1",
            "outgoing_interface_id": "host-01-eth0",
            "metric": 100,
        },
        {
            "id": "host-route-no-interface",
            "destination": "10.30.0.0/16",
            "next_hop": "192.168.1.1",
            "outgoing_interface_id": None,
            "metric": 10,
        },
        {
            "id": "host-route-interface-only",
            "destination": "10.40.0.0/16",
            "next_hop": None,
            "outgoing_interface_id": "host-01-eth0",
            "metric": 10,
        },
    ],
)
def test_document_accepts_supported_host_route_combinations(route):
    report = validate_document(document_with_host_route(route))

    assert report.valid, report.issues


def test_document_rejects_host_route_with_incompatible_ip_families():
    route = {
        "id": "host-route-family-error",
        "destination": "2001:db8:20::/64",
        "next_hop": "192.168.1.1",
        "outgoing_interface_id": "host-01-eth0",
        "metric": 10,
    }

    report = validate_document(document_with_host_route(route))

    assert not report.valid
    assert "ROUTE-003" in issue_codes(report)


def test_domain_rejects_host_route_with_incompatible_ip_families():
    route = StaticRoute(
        id="host-route-family-error",
        destination=IPv6Network("2001:db8:20::/64"),
        next_hop=IPv4Address("192.168.1.1"),
        outgoing_interface_id="host-01-eth0",
        metric=10,
    )

    report = validate_topology(build_topology(host_route=route))

    assert not report.valid
    assert "ROUTE-003" in issue_codes(report)


def test_document_rejects_nonexistent_host_outgoing_interface():
    route = {
        "id": "host-route-bad-interface",
        "destination": "10.50.0.0/16",
        "next_hop": None,
        "outgoing_interface_id": "missing-interface",
        "metric": 10,
    }

    report = validate_document(document_with_host_route(route))

    assert not report.valid
    assert "REF-002" in issue_codes(report)


def test_domain_rejects_nonexistent_host_outgoing_interface():
    route = make_route(
        next_hop=None,
        outgoing_interface_id="missing-interface",
    )

    report = validate_topology(build_topology(host_route=route))

    assert not report.valid
    assert "REF-002" in issue_codes(report)


def test_document_rejects_negative_host_route_metric():
    route = {
        "id": "host-route-negative-metric",
        "destination": "10.70.0.0/16",
        "next_hop": "192.168.1.1",
        "outgoing_interface_id": "host-01-eth0",
        "metric": -1,
    }

    report = validate_document(document_with_host_route(route))

    assert not report.valid
    assert "ROUTE-007" in issue_codes(report)


def test_domain_rejects_negative_host_route_metric():
    route = make_route(metric=-1)

    report = validate_topology(build_topology(host_route=route))

    assert not report.valid
    assert "ROUTE-007" in issue_codes(report)


def test_document_rejects_static_routes_on_switch():
    document = serialize_topology(build_topology())
    switch = {
        "id": "switch-01",
        "name": "Switch 01",
        "node_type": "switch",
        "interfaces": [],
        "static_routes": [],
    }
    document["nodes"].append(switch)

    report = validate_document(document)

    assert not report.valid
    assert any(
        issue.code == "DOC-006"
        and issue.entity_id == "switch-01"
        and issue.field == "static_routes"
        for issue in report.issues
    )


def test_document_accepts_valid_router_static_route():
    router_route = StaticRoute(
        id="router-route-01",
        destination=IPv4Network("10.60.0.0/16"),
        next_hop=IPv4Address("192.168.2.2"),
        outgoing_interface_id="router-01-eth0",
        metric=10,
    )
    topology = build_topology(router_route=router_route)

    report = validate_document(serialize_topology(topology))

    assert report.valid, report.issues


def test_domain_accepts_valid_router_static_route():
    router_route = StaticRoute(
        id="router-route-01",
        destination=IPv4Network("10.60.0.0/16"),
        next_hop=IPv4Address("192.168.2.2"),
        outgoing_interface_id="router-01-eth0",
        metric=10,
    )
    topology = build_topology(router_route=router_route)

    report = validate_topology(topology)

    assert report.valid, report.issues


def test_document_rejects_host_route_using_another_nodes_interface():
    document = serialize_topology(build_topology(host_route=make_route()))
    other_host = {
        "id": "host-02",
        "name": "Host 02",
        "node_type": "host",
        "interfaces": [
            {
                "id": "host-02-eth0",
                "name": "eth0",
                "ipv4_addresses": ["192.168.2.10/24"],
                "ipv6_addresses": [],
                "status": "up",
            }
        ],
    }
    document["nodes"].append(other_host)
    host = next(node for node in document["nodes"] if node["id"] == "host-01")
    host["static_routes"][0]["outgoing_interface_id"] = "host-02-eth0"

    report = validate_document(document)

    assert not report.valid
    assert "REF-003" in issue_codes(report)


def test_domain_rejects_host_route_using_another_nodes_interface():
    topology = build_topology(
        host_route=make_route(outgoing_interface_id="host-02-eth0")
    )
    other_host = Host(
        id="host-02",
        name="Host 02",
        interfaces=[
            Interface(
                id="host-02-eth0",
                name="eth0",
                ipv4_addresses=[IPv4Interface("192.168.2.10/24")],
            )
        ],
    )
    topology.add_node(other_host)

    report = validate_topology(topology)

    assert not report.valid
    assert "REF-003" in issue_codes(report)


def test_domain_rejects_host_route_without_next_hop_or_interface():
    route = make_route(
        next_hop=None,
        outgoing_interface_id=None,
    )

    report = validate_topology(build_topology(host_route=route))

    assert not report.valid
    assert "ROUTE-004" in issue_codes(report)


def test_document_rejects_host_route_without_next_hop_or_interface():
    route = {
        "id": "host-route-no-egress",
        "destination": "10.80.0.0/16",
        "next_hop": None,
        "outgoing_interface_id": None,
        "metric": 10,
    }

    report = validate_document(document_with_host_route(route))

    assert not report.valid
    assert "ROUTE-004" in issue_codes(report)



# ---------------------------------------------------------
# Document validation: node-specific fields
# ---------------------------------------------------------

def test_document_rejects_ipv4_forwarding_on_host():
    document = serialize_topology(build_topology())
    host = next(node for node in document["nodes"] if node["id"] == "host-01")
    host["ipv4_forwarding"] = True

    report = validate_document(document)

    assert not report.valid
    assert "DOC-006" in issue_codes(report)


def test_document_rejects_ipv6_forwarding_on_host():
    document = serialize_topology(build_topology())
    host = next(node for node in document["nodes"] if node["id"] == "host-01")
    host["ipv6_forwarding"] = True

    report = validate_document(document)

    assert not report.valid
    assert "DOC-006" in issue_codes(report)


def test_document_accepts_router_forwarding_fields():
    router = Router(
        id="router-01",
        name="Router 01",
        ipv4_forwarding=True,
        ipv6_forwarding=True,
        interfaces=[],
    )
    topology = build_topology()
    topology.add_node(router)

    report = validate_document(serialize_topology(topology))

    assert report.valid, report.issues


# ---------------------------------------------------------
# Document validation: JSON-compatible attributes
# ---------------------------------------------------------

def test_document_accepts_nested_json_attributes():
    document = serialize_topology(build_topology())
    host = next(node for node in document["nodes"] if node["id"] == "host-01")

    host["attributes"] = {
        "vendor": "Example",
        "enabled": True,
        "config": {
            "mode": "access",
            "ports": [1, 2, 3],
            "optional": None,
        },
    }

    report = validate_document(document)

    assert report.valid, report.issues


@pytest.mark.parametrize(
    "invalid_attributes",
    [
        {"value": float("nan")},
        {"value": float("inf")},
        {"value": {1, 2, 3}},
        {"value": (1, 2, 3)},
        {1: "invalid key"},
        {"nested": {"invalid": float("-inf")}},
    ],
)
def test_document_rejects_non_json_attributes(invalid_attributes):
    document = serialize_topology(build_topology())
    host = next(node for node in document["nodes"] if node["id"] == "host-01")
    host["attributes"] = invalid_attributes

    report = validate_document(document)

    assert not report.valid
    assert "DOC-004" in issue_codes(report)

# ---------------------------------------------------------
# Contract validation: JSON IP representations
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ipv4_addresses", IPv4Interface("192.168.1.10/24")),
        ("ipv6_addresses", IPv6Interface("2001:db8::10/64")),
    ],
)
def test_document_rejects_ip_interface_objects(field, value):
    document = serialize_topology(build_topology())
    host = next(node for node in document["nodes"] if node["id"] == "host-01")
    host_interface = host["interfaces"][0]
    host_interface[field] = [value]

    report = validate_document(document)

    assert not report.valid
    assert "DOC-011" in issue_codes(report)


@pytest.mark.parametrize(
    "destination",
    [
        IPv4Network("10.20.0.0/16"),
        IPv6Network("2001:db8:20::/64"),
    ],
)
def test_document_rejects_network_objects_in_route_destination(destination):
    route = {
        "id": "host-route-invalid-destination",
        "destination": destination,
        "next_hop": "192.168.1.1",
        "outgoing_interface_id": "host-01-eth0",
        "metric": 10,
    }

    report = validate_document(document_with_host_route(route))

    assert not report.valid
    assert "DOC-011" in issue_codes(report)


@pytest.mark.parametrize(
    "next_hop",
    [
        IPv4Address("192.168.1.1"),
        IPv6Address("2001:db8::1"),
    ],
)
def test_document_rejects_address_objects_in_route_next_hop(next_hop):
    route = {
        "id": "host-route-invalid-next-hop",
        "destination": "10.20.0.0/16",
        "next_hop": next_hop,
        "outgoing_interface_id": "host-01-eth0",
        "metric": 10,
    }

    report = validate_document(document_with_host_route(route))

    assert not report.valid
    assert "DOC-011" in issue_codes(report)


def test_document_accepts_ipv6_string_representations():
    document = serialize_topology(build_topology())
    host = next(node for node in document["nodes"] if node["id"] == "host-01")
    host_interface = host["interfaces"][0]

    host_interface["ipv6_addresses"] = ["2001:db8:1::10/64"]
    host["static_routes"] = [
        {
            "id": "host-ipv6-route",
            "destination": "2001:db8:20::/64",
            "next_hop": "2001:db8:1::1",
            "outgoing_interface_id": "host-01-eth0",
            "metric": 10,
        }
    ]

    report = validate_document(document)

    assert report.valid, report.issues


# ---------------------------------------------------------
# Domain validation: native Python IP representations
# ---------------------------------------------------------

def test_domain_accepts_ipv6_interface_and_static_route():
    topology = Topology(
        metadata=Metadata(
            id="ipv6-topology",
            name="IPv6 Validation",
        )
    )

    host = Host(
        id="host-ipv6",
        name="IPv6 Host",
        interfaces=[
            Interface(
                id="host-ipv6-eth0",
                name="eth0",
                ipv6_addresses=[
                    IPv6Interface("2001:db8:1::10/64")
                ],
            )
        ],
        static_routes=[
            StaticRoute(
                id="host-ipv6-route",
                destination=IPv6Network("2001:db8:20::/64"),
                next_hop=IPv6Address("2001:db8:1::1"),
                outgoing_interface_id="host-ipv6-eth0",
                metric=10,
            )
        ],
    )

    topology.add_node(host)

    report = validate_topology(topology)

    assert report.valid, report.issues


# ---------------------------------------------------------
# Domain validation: duplicate IP addresses
# ---------------------------------------------------------

def test_domain_detects_duplicate_ip_with_different_prefixes():
    topology = build_topology(
        host_extra_interfaces=[
            Interface(
                id="host-01-eth1",
                name="eth1",
                ipv4_addresses=[
                    IPv4Interface("192.168.1.10/25")
                ],
            )
        ]
    )

    report = validate_topology(topology)

    assert "INT-004" in issue_codes(report)


# ---------------------------------------------------------
# Domain validation: Node class and node_type consistency
# ---------------------------------------------------------

def test_domain_rejects_inconsistent_node_type():
    topology = build_topology(
        host_node_type=NodeType.ROUTER
    )

    report = validate_topology(topology)

    assert "NODE-005" in issue_codes(report)
