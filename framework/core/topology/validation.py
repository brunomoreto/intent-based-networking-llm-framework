"""Validation services for Topology Model V2."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import StrEnum
from ipaddress import (
    IPv4Address, IPv4Interface, IPv4Network,
    IPv6Address, IPv6Interface, IPv6Network,
    ip_address, ip_interface, ip_network,
)
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .enums import (
    AssociationRole, ControllerStatus, InterfaceStatus, LinkStatus,
    NodeType, TopologySource,
)
from .entities import (
    Controller, ControllerAssociation, Host, Interface, Link,
    LinkDirection, Metadata, Metrics, Node, Policy, Router,
    StaticRoute, Switch,
)
from .topology import Topology


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    code: str
    severity: ValidationSeverity
    entity_type: str
    entity_id: str | None
    field: str | None
    message: str


@dataclass(slots=True)
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def total_count(self) -> int:
        return len(self.issues)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def info_count(self) -> int:
        return len(self.infos)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [
            issue for issue in self.issues
            if issue.severity == ValidationSeverity.ERROR
        ]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [
            issue for issue in self.issues
            if issue.severity == ValidationSeverity.WARNING
        ]

    @property
    def infos(self) -> list[ValidationIssue]:
        return [
            issue for issue in self.issues
            if issue.severity == ValidationSeverity.INFO
        ]

    @property
    def informational(self) -> list[ValidationIssue]:
        return self.infos

    def add(
        self,
        code: str,
        severity: ValidationSeverity,
        entity_type: str,
        entity_id: str | None,
        field_name: str | None,
        message: str,
    ) -> None:
        issue = ValidationIssue(
            code,
            severity,
            entity_type,
            entity_id,
            field_name,
            message,
        )
        if issue not in self.issues:
            self.issues.append(issue)

    def extend(self, issues: list[ValidationIssue]) -> None:
        for issue in issues:
            if issue not in self.issues:
                self.issues.append(issue)


_ERROR = ValidationSeverity.ERROR
_WARNING = ValidationSeverity.WARNING
_INFO = ValidationSeverity.INFO


def _issue(
    report,
    code,
    entity,
    entity_id,
    field_name,
    message,
    severity=_ERROR,
):
    report.add(
        code,
        severity,
        entity,
        entity_id,
        field_name,
        message,
    )


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def _finite(value: Any) -> bool:
    return _is_number(value) and math.isfinite(value)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _valid_ip_interface(value: Any, version: int) -> bool:
    try:
        parsed = ip_interface(value) if isinstance(value, str) else value
        expected = IPv4Interface if version == 4 else IPv6Interface
        return isinstance(parsed, expected)
    except (ValueError, TypeError):
        return False


def _valid_ip_network(value: Any) -> bool:
    try:
        parsed = (
            ip_network(value, strict=False)
            if isinstance(value, str)
            else value
        )
        return isinstance(parsed, (IPv4Network, IPv6Network))
    except (ValueError, TypeError):
        return False


def _valid_ip_address(value: Any) -> bool:
    try:
        parsed = ip_address(value) if isinstance(value, str) else value
        return isinstance(parsed, (IPv4Address, IPv6Address))
    except (ValueError, TypeError):
        return False


# Document schema mirrors serialization.py (SCHEMA_VERSION = 2).
_ROOT = {
    "schema_version",
    "metadata",
    "nodes",
    "links",
    "controllers",
    "controller_associations",
    "policies",
    "metrics",
}

_META = {
    "id",
    "name",
    "description",
    "author",
    "version",
    "created_at",
    "topology_source",
    "tags",
}

_NODE_COMMON = {
    "id",
    "name",
    "node_type",
    "attributes",
    "interfaces",
}

_ROUTER_EXTRA = {
    "ipv4_forwarding",
    "ipv6_forwarding",
    "static_routes",
}

_INTERFACE = {
    "id",
    "name",
    "mac_address",
    "ipv4_addresses",
    "ipv6_addresses",
    "mtu",
    "speed",
    "status",
    "attributes",
}

_ROUTE = {
    "id",
    "destination",
    "next_hop",
    "outgoing_interface_id",
    "metric",
}

_DIRECTION = {
    "bandwidth",
    "delay",
    "weight",
    "packet_loss",
    "enabled",
}

_LINK = {
    "id",
    "source_interface_id",
    "destination_interface_id",
    "forward",
    "reverse",
    "status",
    "attributes",
}

_CONTROLLER = {
    "id",
    "name",
    "controller_type",
    "endpoint",
    "port",
    "protocol",
    "status",
    "attributes",
}

_ASSOC = {
    "id",
    "controller_id",
    "node_id",
    "role",
}

_POLICY = {
    "id",
    "name",
    "description",
    "enabled",
    "attributes",
}

_METRICS = {"values"}


def _check_object(
    value,
    path,
    report,
    *,
    required=(),
    allowed=None,
    entity="document",
    entity_id=None,
):
    if not isinstance(value, Mapping):
        _issue(
            report,
            "DOC-013",
            entity,
            entity_id,
            path,
            f"{path} must be a JSON object.",
        )
        return False

    for key in required:
        if key not in value:
            _issue(
                report,
                "DOC-005" if path != "root" else "DOC-003",
                entity,
                entity_id,
                f"{path}.{key}",
                f"Required field '{path}.{key}' is missing.",
            )

    if allowed is not None:
        for key in value:
            if key not in allowed:
                _issue(
                    report,
                    "DOC-006",
                    entity,
                    entity_id,
                    f"{path}.{key}",
                    f"Unknown structural field '{path}.{key}'.",
                )

    return True


def _check_string(
    data,
    key,
    path,
    report,
    *,
    required=False,
    nonblank=False,
    allow_none=False,
):
    if key not in data:
        if required:
            _issue(
                report,
                "DOC-005",
                path,
                None,
                key,
                f"Required string field '{key}' is missing.",
            )
        return

    value = data[key]

    if value is None and allow_none:
        return

    if not isinstance(value, str):
        _issue(
            report,
            "DOC-004",
            path,
            None,
            key,
            f"'{key}' must be a string.",
        )
    elif nonblank and not value.strip():
        _issue(
            report,
            "DOC-004",
            path,
            None,
            key,
            f"'{key}' must not be blank.",
        )


def _check_bool(data, key, path, report, required=False):
    if key not in data:
        if required:
            _issue(
                report,
                "DOC-005",
                path,
                None,
                key,
                f"Required boolean field '{key}' is missing.",
            )
    elif not isinstance(data[key], bool):
        _issue(
            report,
            "DOC-010",
            path,
            None,
            key,
            f"'{key}' must be a boolean.",
        )


def _check_enum(
    data,
    key,
    enum_type,
    path,
    report,
    required=False,
    allow_none=False,
):
    if key not in data:
        if required:
            _issue(
                report,
                "DOC-005",
                path,
                None,
                key,
                f"Required enum field '{key}' is missing.",
            )
    elif data[key] is None and allow_none:
        return
    elif (
        not isinstance(data[key], str)
        or data[key] not in {item.value for item in enum_type}
    ):
        _issue(
            report,
            "DOC-007",
            path,
            None,
            key,
            f"'{key}' contains an unsupported enum value.",
        )


def _check_number(
    data,
    key,
    path,
    report,
    *,
    required=False,
    integer=False,
    allow_none=False,
):
    if key not in data:
        if required:
            _issue(
                report,
                "DOC-005",
                path,
                None,
                key,
                f"Required numeric field '{key}' is missing.",
            )
        return

    value = data[key]

    if value is None and allow_none:
        return

    if not _is_number(value):
        _issue(
            report,
            "DOC-004",
            path,
            None,
            key,
            f"'{key}' must be numeric.",
        )
    elif not math.isfinite(value):
        _issue(
            report,
            "DOC-008",
            path,
            None,
            key,
            f"'{key}' must be finite.",
        )
    elif integer and not _is_int(value):
        _issue(
            report,
            "DOC-009",
            path,
            None,
            key,
            f"'{key}' must be an integer.",
        )


def _check_attributes(data, key, path, report):
    if key in data and not _mapping(data[key]):
        _issue(
            report,
            "DOC-004",
            path,
            None,
            key,
            f"'{key}' must be an object/mapping.",
        )


def _check_array(data, key, path, report, required=False):
    if key not in data:
        if required:
            _issue(
                report,
                "DOC-013",
                path,
                None,
                key,
                f"Required collection '{key}' is missing.",
            )
        return None

    if not isinstance(data[key], list):
        _issue(
            report,
            "DOC-013",
            path,
            None,
            key,
            f"'{key}' must be an array.",
        )
        return None

    return data[key]


def _validate_document_ids(document, report):
    seen = {}

    def add(identifier, entity, location):
        if isinstance(identifier, str):
            if identifier in seen:
                previous_entity, previous_location = seen[identifier]
                _issue(
                    report,
                    "ID-001",
                    entity,
                    identifier,
                    "id",
                    f"Identifier '{identifier}' duplicates "
                    f"{previous_entity} at {previous_location}; "
                    "global IDs must be unique.",
                )
            else:
                seen[identifier] = (entity, location)

    meta = document.get("metadata")
    if isinstance(meta, Mapping):
        add(meta.get("id"), "Metadata", "metadata")

    for collection, entity in (
        ("nodes", "Node"),
        ("links", "Link"),
        ("controllers", "Controller"),
        ("controller_associations", "ControllerAssociation"),
        ("policies", "Policy"),
    ):
        items = document.get(collection)

        if not isinstance(items, list):
            continue

        for idx, item in enumerate(items):
            if not isinstance(item, Mapping):
                continue

            add(item.get("id"), entity, f"{collection}[{idx}]")

            if collection == "nodes":
                interfaces = item.get("interfaces")

                if isinstance(interfaces, list):
                    for j, interface in enumerate(interfaces):
                        if isinstance(interface, Mapping):
                            add(
                                interface.get("id"),
                                "Interface",
                                f"nodes[{idx}].interfaces[{j}]",
                            )

                routes = item.get("static_routes")

                if isinstance(routes, list):
                    for j, route in enumerate(routes):
                        if isinstance(route, Mapping):
                            add(
                                route.get("id"),
                                "StaticRoute",
                                f"nodes[{idx}].static_routes[{j}]",
                            )

    return seen


def validate_document(document: Mapping[str, object]) -> ValidationReport:
    """Validate a parsed Topology V2 JSON document without mutating it."""
    report = ValidationReport()

    if not _mapping(document):
        _issue(
            report,
            "DOC-013",
            "document",
            None,
            None,
            "The topology document root must be an object.",
        )
        return report

    _check_object(
        document,
        "root",
        report,
        required=_ROOT - {"schema_version"},
        allowed=_ROOT,
    )

    if "schema_version" not in document:
        _issue(
            report,
            "DOC-001",
            "document",
            None,
            "schema_version",
            "schema_version is missing.",
        )
    elif (
        not _is_int(document["schema_version"])
        or document["schema_version"] != 2
    ):
        _issue(
            report,
            "DOC-002",
            "document",
            None,
            "schema_version",
            "schema_version must be the integer value 2.",
        )

    meta = document.get("metadata")

    if (
        "metadata" in document
        and _check_object(
            meta,
            "metadata",
            report,
            required={"id", "name"},
            allowed=_META,
            entity="Metadata",
        )
    ):
        _check_string(meta, "id", "Metadata", report, required=True)
        _check_string(meta, "name", "Metadata", report, required=True)

        for key in ("description", "author", "version"):
            _check_string(meta, key, "Metadata", report)

        if "created_at" in meta and meta["created_at"] is not None:
            value = meta["created_at"]

            try:
                if not isinstance(value, str):
                    raise ValueError
                datetime.fromisoformat(value)
            except (ValueError, TypeError):
                _issue(
                    report,
                    "DOC-012",
                    "Metadata",
                    meta.get("id"),
                    "created_at",
                    "created_at must be a valid ISO 8601 datetime string or null.",
                )

        _check_enum(
            meta,
            "topology_source",
            TopologySource,
            "Metadata",
            report,
        )

        if "tags" in meta and (
            not isinstance(meta["tags"], list)
            or any(not isinstance(tag, str) for tag in meta["tags"])
        ):
            _issue(
                report,
                "DOC-004",
                "Metadata",
                meta.get("id"),
                "tags",
                "tags must be an array of strings.",
            )

    nodes = _check_array(document, "nodes", "root", report)

    if nodes is not None:
        for i, node in enumerate(nodes):
            path = f"nodes[{i}]"

            if not _check_object(
                node,
                path,
                report,
                required={"id", "name", "node_type"},
                allowed=_NODE_COMMON | _ROUTER_EXTRA,
                entity="Node",
            ):
                continue

            _check_string(node, "id", "Node", report, required=True)
            _check_string(node, "name", "Node", report, required=True)
            _check_enum(
                node,
                "node_type",
                NodeType,
                "Node",
                report,
                required=True,
            )
            _check_attributes(node, "attributes", "Node", report)

            interfaces = _check_array(
                node,
                "interfaces",
                path,
                report,
                required=True,
            )

            if interfaces is not None:
                for j, interface in enumerate(interfaces):
                    ipath = f"{path}.interfaces[{j}]"

                    if not _check_object(
                        interface,
                        ipath,
                        report,
                        required={"id", "name"},
                        allowed=_INTERFACE,
                        entity="Interface",
                    ):
                        continue

                    _check_string(
                        interface,
                        "id",
                        "Interface",
                        report,
                        required=True,
                    )
                    _check_string(
                        interface,
                        "name",
                        "Interface",
                        report,
                        required=True,
                    )
                    _check_string(
                        interface,
                        "mac_address",
                        "Interface",
                        report,
                        allow_none=True,
                    )
                    _check_number(
                        interface,
                        "mtu",
                        "Interface",
                        report,
                        integer=True,
                        allow_none=True,
                    )
                    _check_number(
                        interface,
                        "speed",
                        "Interface",
                        report,
                        allow_none=True,
                    )
                    _check_enum(
                        interface,
                        "status",
                        InterfaceStatus,
                        "Interface",
                        report,
                    )
                    _check_attributes(
                        interface,
                        "attributes",
                        "Interface",
                        report,
                    )

                    for key, version in (
                        ("ipv4_addresses", 4),
                        ("ipv6_addresses", 6),
                    ):
                        values = _check_array(
                            interface,
                            key,
                            ipath,
                            report,
                        )

                        if values is not None:
                            for address in values:
                                if not _valid_ip_interface(address, version):
                                    _issue(
                                        report,
                                        "DOC-011",
                                        "Interface",
                                        interface.get("id"),
                                        key,
                                        f"Invalid IPv{version} interface "
                                        f"representation: {address!r}.",
                                    )

            node_type = node.get("node_type")

            if node_type == NodeType.ROUTER.value:
                for key in ("ipv4_forwarding", "ipv6_forwarding"):
                    _check_bool(node, key, "Router", report)

                routes = _check_array(
                    node,
                    "static_routes",
                    path,
                    report,
                )

                if routes is not None:
                    for j, route in enumerate(routes):
                        rpath = f"{path}.static_routes[{j}]"

                        if not _check_object(
                            route,
                            rpath,
                            report,
                            required={"id", "destination"},
                            allowed=_ROUTE,
                            entity="StaticRoute",
                        ):
                            continue

                        _check_string(
                            route,
                            "id",
                            "StaticRoute",
                            report,
                            required=True,
                        )

                        if (
                            "destination" in route
                            and not _valid_ip_network(route["destination"])
                        ):
                            _issue(
                                report,
                                "DOC-011",
                                "StaticRoute",
                                route.get("id"),
                                "destination",
                                "Invalid destination network.",
                            )

                        if (
                            route.get("next_hop") is not None
                            and not _valid_ip_address(route["next_hop"])
                        ):
                            _issue(
                                report,
                                "DOC-011",
                                "StaticRoute",
                                route.get("id"),
                                "next_hop",
                                "Invalid next-hop IP address.",
                            )

                        _check_string(
                            route,
                            "outgoing_interface_id",
                            "StaticRoute",
                            report,
                            allow_none=True,
                        )
                        _check_number(
                            route,
                            "metric",
                            "StaticRoute",
                            report,
                            integer=True,
                        )

            elif node_type in (
                NodeType.HOST.value,
                NodeType.SWITCH.value,
            ):
                for key in _ROUTER_EXTRA:
                    if key in node:
                        _issue(
                            report,
                            "DOC-006",
                            "Node",
                            node.get("id"),
                            key,
                            f"Router-specific field '{key}' is not valid "
                            f"for {node_type}.",
                        )

    links = _check_array(document, "links", "root", report)

    if links is not None:
        for i, link in enumerate(links):
            if not _check_object(
                link,
                f"links[{i}]",
                report,
                required={
                    "id",
                    "source_interface_id",
                    "destination_interface_id",
                    "forward",
                },
                allowed=_LINK,
                entity="Link",
            ):
                continue

            _check_string(link, "id", "Link", report, required=True)

            for key in (
                "source_interface_id",
                "destination_interface_id",
            ):
                _check_string(
                    link,
                    key,
                    "Link",
                    report,
                    required=True,
                )

            _check_enum(link, "status", LinkStatus, "Link", report)
            _check_attributes(link, "attributes", "Link", report)

            for key in ("forward", "reverse"):
                if key not in link or link[key] is None:
                    if key == "forward":
                        _issue(
                            report,
                            "DOC-005",
                            "Link",
                            link.get("id"),
                            key,
                            "Required forward direction is missing.",
                        )
                    continue

                direction = link[key]

                if not _check_object(
                    direction,
                    f"links[{i}].{key}",
                    report,
                    required=_DIRECTION,
                    allowed=_DIRECTION,
                    entity="LinkDirection",
                    entity_id=link.get("id"),
                ):
                    continue

                for numeric in (
                    "bandwidth",
                    "delay",
                    "weight",
                    "packet_loss",
                ):
                    _check_number(
                        direction,
                        numeric,
                        "LinkDirection",
                        report,
                        required=True,
                    )

                _check_bool(
                    direction,
                    "enabled",
                    "LinkDirection",
                    report,
                    required=True,
                )

    controllers = _check_array(
        document,
        "controllers",
        "root",
        report,
    )

    if controllers is not None:
        for controller in controllers:
            if not _check_object(
                controller,
                "Controller",
                report,
                required={
                    "id",
                    "name",
                    "controller_type",
                    "endpoint",
                    "port",
                    "protocol",
                },
                allowed=_CONTROLLER,
                entity="Controller",
            ):
                continue

            for key in (
                "id",
                "name",
                "controller_type",
                "endpoint",
                "protocol",
            ):
                _check_string(
                    controller,
                    key,
                    "Controller",
                    report,
                    required=True,
                )

            _check_number(
                controller,
                "port",
                "Controller",
                report,
                required=True,
                integer=True,
            )
            _check_enum(
                controller,
                "status",
                ControllerStatus,
                "Controller",
                report,
            )
            _check_attributes(
                controller,
                "attributes",
                "Controller",
                report,
            )

    associations = _check_array(
        document,
        "controller_associations",
        "root",
        report,
    )

    if associations is not None:
        for association in associations:
            if not _check_object(
                association,
                "ControllerAssociation",
                report,
                required={"id", "controller_id", "node_id"},
                allowed=_ASSOC,
                entity="ControllerAssociation",
            ):
                continue

            for key in ("id", "controller_id", "node_id"):
                _check_string(
                    association,
                    key,
                    "ControllerAssociation",
                    report,
                    required=True,
                )

            _check_enum(
                association,
                "role",
                AssociationRole,
                "ControllerAssociation",
                report,
                allow_none=True,
            )

    policies = _check_array(
        document,
        "policies",
        "root",
        report,
    )

    if policies is not None:
        for policy in policies:
            if not _check_object(
                policy,
                "Policy",
                report,
                required={"id", "name"},
                allowed=_POLICY,
                entity="Policy",
            ):
                continue

            _check_string(
                policy,
                "id",
                "Policy",
                report,
                required=True,
            )
            _check_string(
                policy,
                "name",
                "Policy",
                report,
                required=True,
            )
            _check_string(
                policy,
                "description",
                "Policy",
                report,
            )
            _check_bool(
                policy,
                "enabled",
                "Policy",
                report,
            )
            _check_attributes(
                policy,
                "attributes",
                "Policy",
                report,
            )

    metrics = document.get("metrics")

    if (
        "metrics" in document
        and _check_object(
            metrics,
            "metrics",
            report,
            required={"values"},
            allowed=_METRICS,
            entity="Metrics",
        )
    ):
        values = metrics.get("values")

        if not _mapping(values):
            _issue(
                report,
                "DOC-013",
                "Metrics",
                None,
                "values",
                "metrics.values must be an object.",
            )
        else:
            for name, value in values.items():
                if not isinstance(name, str):
                    _issue(
                        report,
                        "DOC-004",
                        "Metrics",
                        None,
                        "values",
                        "Metric names must be strings.",
                    )
                elif not _is_number(value):
                    _issue(
                        report,
                        "DOC-004",
                        "Metrics",
                        None,
                        f"values.{name}",
                        "Metric values must be numeric.",
                    )
                elif not math.isfinite(value):
                    _issue(
                        report,
                        "DOC-008",
                        "Metrics",
                        None,
                        f"values.{name}",
                        "Metric values must be finite.",
                    )

    _validate_document_ids(document, report)

    return report


def _all_interfaces(topology):
    result = {}
    owners = {}

    for node in topology.nodes.values():
        for interface in node.interfaces:
            result[interface.id] = interface
            owners[interface.id] = node

    return result, owners


def _valid_mac(value):
    if not isinstance(value, str):
        return False

    return (
        re.fullmatch(
            r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}",
            value,
        )
        is not None
    )


def _valid_endpoint(value):
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        return False

    if "://" in value or any(char.isspace() for char in value):
        return False

    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]

    try:
        ip_address(value)
        return True
    except ValueError:
        if ":" in value or "/" in value or "@" in value:
            return False

        labels = value.rstrip(".").split(".")

        return all(
            len(label) <= 63
            and re.fullmatch(
                r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?",
                label,
            )
            for label in labels
        )


def validate_topology(topology: Topology) -> ValidationReport:
    """Validate integrity and semantic consistency of a Topology V2 aggregate."""
    report = ValidationReport()

    if not isinstance(topology, Topology):
        _issue(
            report,
            "NODE-001",
            "Topology",
            None,
            None,
            "Expected a Topology V2 aggregate.",
        )
        return report

    nodes = topology.nodes
    links = topology.links
    controllers = topology.controllers
    associations = topology.controller_associations
    policies = topology.policies
    metadata = topology.metadata

    interfaces, owners = _all_interfaces(topology)

    # Global identifiers.
    identifiers = [(metadata.id, "Metadata")]

    for node in nodes.values():
        identifiers.append((node.id, "Node"))
        identifiers.extend(
            (interface.id, "Interface")
            for interface in node.interfaces
        )

        if isinstance(node, Router):
            identifiers.extend(
                (route.id, "StaticRoute")
                for route in node.static_routes
            )

    identifiers.extend(
        (link.id, "Link")
        for link in links.values()
    )
    identifiers.extend(
        (controller.id, "Controller")
        for controller in controllers.values()
    )
    identifiers.extend(
        (association.id, "ControllerAssociation")
        for association in associations.values()
    )
    identifiers.extend(
        (policy.id, "Policy")
        for policy in policies.values()
    )

    seen = {}

    for identifier, entity in identifiers:
        if identifier in seen:
            _issue(
                report,
                "ID-001",
                entity,
                str(identifier),
                "id",
                f"Identifier '{identifier}' is duplicated by "
                f"{seen[identifier]} and {entity}.",
            )
        else:
            seen[identifier] = entity

    # Node and Interface validation.
    all_ip_entries = {}
    link_interface_counts = {}

    for link in links.values():
        for interface_id in (
            link.source_interface_id,
            link.destination_interface_id,
        ):
            link_interface_counts[interface_id] = (
                link_interface_counts.get(interface_id, 0) + 1
            )

    for node in nodes.values():
        if not isinstance(node, (Host, Switch, Router)):
            _issue(
                report,
                "NODE-001",
                "Node",
                str(node.id),
                "node_type",
                "Node has an unsupported domain type.",
            )

        if isinstance(node, (Host, Switch)) and (
            hasattr(node, "ipv4_forwarding")
            or hasattr(node, "static_routes")
        ):
            _issue(
                report,
                "NODE-002",
                "Node",
                str(node.id),
                None,
                "Host or Switch contains Router-specific fields.",
            )

        if not node.interfaces:
            _issue(
                report,
                "NODE-003",
                "Node",
                str(node.id),
                "interfaces",
                "Node has no Interfaces.",
                _INFO,
            )

        for interface in node.interfaces:
            if (
                interface.mac_address is not None
                and not _valid_mac(interface.mac_address)
            ):
                _issue(
                    report,
                    "INT-001",
                    "Interface",
                    str(interface.id),
                    "mac_address",
                    "MAC address is invalid.",
                )

            if interface.mtu is not None and (
                not _is_int(interface.mtu)
                or interface.mtu <= 0
            ):
                _issue(
                    report,
                    "INT-002",
                    "Interface",
                    str(interface.id),
                    "mtu",
                    "MTU must be a positive integer.",
                )

            if interface.speed is not None and (
                not _finite(interface.speed)
                or interface.speed <= 0
            ):
                _issue(
                    report,
                    "INT-003",
                    "Interface",
                    str(interface.id),
                    "speed",
                    "Interface speed must be positive and finite.",
                )

            if (
                not interface.ipv4_addresses
                and not interface.ipv6_addresses
            ):
                _issue(
                    report,
                    "INT-005",
                    "Interface",
                    str(interface.id),
                    "ipv4_addresses/ipv6_addresses",
                    "Interface has no IP addresses.",
                    _INFO,
                )

            if link_interface_counts.get(interface.id, 0) == 0:
                _issue(
                    report,
                    "INT-006",
                    "Interface",
                    str(interface.id),
                    "links",
                    "Interface does not participate in a Link.",
                    _INFO,
                )

            for family, values in (
                (4, interface.ipv4_addresses),
                (6, interface.ipv6_addresses),
            ):
                local_seen = set()

                for value in values:
                    if not _valid_ip_interface(value, family):
                        continue

                    key = (
                        family,
                        str(value.ip),
                        value.network.prefixlen,
                    )

                    if key in local_seen:
                        _issue(
                            report,
                            "INT-007",
                            "Interface",
                            str(interface.id),
                            f"ipv{family}_addresses",
                            f"Duplicate IPv{family} address {value} "
                            "within the same Interface.",
                            _WARNING,
                        )

                    local_seen.add(key)

                    all_ip_entries.setdefault(key, []).append(
                        (interface.id, node.id)
                    )

    for key, entries in all_ip_entries.items():
        distinct_interfaces = {
            entry[0] for entry in entries
        }

        if len(distinct_interfaces) > 1:
            family, address, prefix = key

            _issue(
                report,
                "INT-004",
                "Interface",
                str(entries[-1][0]),
                f"ipv{family}_addresses",
                f"IPv{family} address {address}/{prefix} is "
                "duplicated across different Interfaces.",
                _WARNING,
            )

    # Link endpoint references, topology constraints, and directions.
    for link in links.values():
        source = interfaces.get(link.source_interface_id)
        destination = interfaces.get(link.destination_interface_id)

        if source is None or destination is None:
            _issue(
                report,
                "REF-001",
                "Link",
                str(link.id),
                "source_interface_id/destination_interface_id",
                "Link references a source or destination Interface "
                "that does not exist.",
            )
            continue

        if link.source_interface_id == link.destination_interface_id:
            _issue(
                report,
                "LINK-001",
                "Link",
                str(link.id),
                "source_interface_id/destination_interface_id",
                "Link connects an Interface to itself.",
            )

        source_owner = owners.get(link.source_interface_id)
        destination_owner = owners.get(link.destination_interface_id)

        if (
            source_owner is not None
            and destination_owner is not None
            and source_owner.id == destination_owner.id
        ):
            _issue(
                report,
                "LINK-002",
                "Link",
                str(link.id),
                "source_interface_id/destination_interface_id",
                "Link connects two Interfaces belonging to the same Node.",
            )

        if link_interface_counts.get(link.source_interface_id, 0) > 1:
            _issue(
                report,
                "LINK-003",
                "Link",
                str(link.id),
                "source_interface_id",
                "An Interface participates in more than one Link.",
            )

        if link_interface_counts.get(link.destination_interface_id, 0) > 1:
            _issue(
                report,
                "LINK-003",
                "Link",
                str(link.id),
                "destination_interface_id",
                "An Interface participates in more than one Link.",
            )

        if link.reverse is None:
            _issue(
                report,
                "LINK-004",
                "Link",
                str(link.id),
                "reverse",
                "Link has no declared reverse direction.",
                _INFO,
            )

        if link.status in (
            LinkStatus.FAILED,
            LinkStatus.DISABLED,
        ):
            _issue(
                report,
                "LINK-005",
                "Link",
                str(link.id),
                "status",
                f"Link status is {link.status.value}.",
                _INFO,
            )

        for direction_name, direction in (
            ("forward", link.forward),
            ("reverse", link.reverse),
        ):
            if direction is None:
                continue

            malformed = False

            for attr, code, predicate, explanation in (
                (
                    "bandwidth",
                    "DIR-001",
                    lambda value: _finite(value) and value > 0,
                    "Bandwidth must be greater than zero.",
                ),
                (
                    "delay",
                    "DIR-002",
                    lambda value: _finite(value) and value >= 0,
                    "Delay must not be negative.",
                ),
                (
                    "weight",
                    "DIR-003",
                    lambda value: _finite(value) and value > 0,
                    "Weight must be greater than zero.",
                ),
                (
                    "packet_loss",
                    "DIR-004",
                    lambda value: (
                        _finite(value) and 0 <= value <= 100
                    ),
                    "Packet loss must be between 0 and 100.",
                ),
            ):
                value = getattr(direction, attr, None)

                if not predicate(value):
                    malformed = True
                    _issue(
                        report,
                        code,
                        "LinkDirection",
                        str(link.id),
                        f"{direction_name}.{attr}",
                        explanation,
                    )

            if not isinstance(
                getattr(direction, "enabled", None),
                bool,
            ):
                malformed = True

            if (
                not malformed
                and source is not None
                and destination is not None
            ):
                for endpoint in (source, destination):
                    speed = endpoint.speed

                    if (
                        speed is not None
                        and direction.bandwidth > speed
                    ):
                        _issue(
                            report,
                            "DIR-005",
                            "LinkDirection",
                            str(link.id),
                            f"{direction_name}.bandwidth",
                            f"{direction_name} bandwidth exceeds "
                            f"endpoint Interface {endpoint.id} speed.",
                            _WARNING,
                        )

            if getattr(direction, "enabled", None) is False:
                _issue(
                    report,
                    "DIR-006",
                    "LinkDirection",
                    str(link.id),
                    f"{direction_name}.enabled",
                    f"{direction_name} direction is disabled.",
                    _INFO,
                )

    # Router routes.
    for node in nodes.values():
        if not isinstance(node, Router):
            continue

        for route in node.static_routes:
            if not isinstance(
                route.destination,
                (IPv4Network, IPv6Network),
            ):
                _issue(
                    report,
                    "ROUTE-001",
                    "StaticRoute",
                    str(route.id),
                    "destination",
                    "Destination network is invalid.",
                )
                destination_valid = False
            else:
                destination_valid = True

            if (
                route.next_hop is not None
                and not isinstance(
                    route.next_hop,
                    (IPv4Address, IPv6Address),
                )
            ):
                _issue(
                    report,
                    "ROUTE-002",
                    "StaticRoute",
                    str(route.id),
                    "next_hop",
                    "Next-hop IP address is invalid.",
                )

            if (
                destination_valid
                and route.next_hop is not None
                and isinstance(
                    route.next_hop,
                    (IPv4Address, IPv6Address),
                )
                and route.destination.version != route.next_hop.version
            ):
                _issue(
                    report,
                    "ROUTE-003",
                    "StaticRoute",
                    str(route.id),
                    "next_hop",
                    "Next-hop IP family differs from destination "
                    "network family.",
                )

            if (
                route.next_hop is None
                and route.outgoing_interface_id is None
            ):
                _issue(
                    report,
                    "ROUTE-004",
                    "StaticRoute",
                    str(route.id),
                    "next_hop/outgoing_interface_id",
                    "At least one of next_hop or outgoing_interface_id "
                    "must be provided.",
                )

            outgoing = route.outgoing_interface_id

            if outgoing is not None:
                if outgoing not in interfaces:
                    _issue(
                        report,
                        "REF-002",
                        "StaticRoute",
                        str(route.id),
                        "outgoing_interface_id",
                        "StaticRoute references an outgoing Interface "
                        "that does not exist.",
                    )
                elif outgoing not in {
                    interface.id for interface in node.interfaces
                }:
                    _issue(
                        report,
                        "REF-003",
                        "StaticRoute",
                        str(route.id),
                        "outgoing_interface_id",
                        "Outgoing Interface does not belong to this Router.",
                    )

            if _is_int(route.metric) and route.metric < 0:
                _issue(
                    report,
                    "ROUTE-007",
                    "StaticRoute",
                    str(route.id),
                    "metric",
                    "StaticRoute metric must not be negative.",
                )

            if destination_valid:
                direct_networks = set()
                direct_valid = True

                for interface in node.interfaces:
                    for address in (
                        interface.ipv4_addresses
                        + interface.ipv6_addresses
                    ):
                        if not isinstance(
                            address,
                            (IPv4Interface, IPv6Interface),
                        ):
                            direct_valid = False
                            continue

                        direct_networks.add(address.network)

                if (
                    direct_valid
                    and route.destination in direct_networks
                ):
                    _issue(
                        report,
                        "ROUTE-008",
                        "StaticRoute",
                        str(route.id),
                        "destination",
                        "StaticRoute duplicates a directly connected "
                        "network of this Router.",
                    )

                if (
                    route.next_hop is not None
                    and isinstance(
                        route.next_hop,
                        (IPv4Address, IPv6Address),
                    )
                ):
                    reachable = False

                    for interface in node.interfaces:
                        for address in (
                            interface.ipv4_addresses
                            + interface.ipv6_addresses
                        ):
                            if (
                                isinstance(
                                    address,
                                    (IPv4Interface, IPv6Interface),
                                )
                                and address.version == route.next_hop.version
                                and route.next_hop in address.network
                            ):
                                reachable = True

                    if not reachable:
                        _issue(
                            report,
                            "ROUTE-005",
                            "StaticRoute",
                            str(route.id),
                            "next_hop",
                            "Next-hop reachability cannot be established "
                            "from available topology information.",
                            _WARNING,
                        )

                if (
                    isinstance(route.destination, IPv4Network)
                    and not node.ipv4_forwarding
                ) or (
                    isinstance(route.destination, IPv6Network)
                    and not node.ipv6_forwarding
                ):
                    _issue(
                        report,
                        "ROUTE-006",
                        "StaticRoute",
                        str(route.id),
                        "destination",
                        "Corresponding IP forwarding family is disabled "
                        "on the Router.",
                        _WARNING,
                    )

    # Controllers.
    for controller in controllers.values():
        if (
            not isinstance(controller.controller_type, str)
            or not controller.controller_type.strip()
        ):
            _issue(
                report,
                "CTRL-001",
                "Controller",
                str(controller.id),
                "controller_type",
                "controller_type must not be empty or blank.",
            )

        if (
            not isinstance(controller.protocol, str)
            or not controller.protocol.strip()
        ):
            _issue(
                report,
                "CTRL-001",
                "Controller",
                str(controller.id),
                "protocol",
                "protocol must not be empty or blank.",
            )

        if not _valid_endpoint(controller.endpoint):
            _issue(
                report,
                "CTRL-002",
                "Controller",
                str(controller.id),
                "endpoint",
                "Endpoint is invalid or includes an embedded port.",
            )

        if (
            not _is_int(controller.port)
            or not 1 <= controller.port <= 65535
        ):
            _issue(
                report,
                "CTRL-003",
                "Controller",
                str(controller.id),
                "port",
                "Port must be an integer in the range 1–65535.",
            )

    # Controller associations.
    pairs = {}
    master_controllers = {}

    for association in associations.values():
        if (
            association.controller_id not in controllers
            or association.node_id not in nodes
        ):
            _issue(
                report,
                "REF-004",
                "ControllerAssociation",
                str(association.id),
                "controller_id/node_id",
                "ControllerAssociation references a Controller or Node "
                "that does not exist.",
            )

        pair = (
            association.controller_id,
            association.node_id,
        )

        if pair in pairs:
            _issue(
                report,
                "ASSOC-001",
                "ControllerAssociation",
                str(association.id),
                "controller_id/node_id",
                "The same Controller/Node association is declared "
                "more than once.",
            )
        else:
            pairs[pair] = association

        if association.role is None:
            _issue(
                report,
                "ASSOC-002",
                "ControllerAssociation",
                str(association.id),
                "role",
                "Controller association has no declared role.",
                _INFO,
            )
        elif association.role == AssociationRole.MASTER:
            master_controllers.setdefault(
                association.node_id,
                set(),
            ).add(association.controller_id)

    for node_id, controller_ids in master_controllers.items():
        if len(controller_ids) > 1:
            assoc_ids = [
                str(association.id)
                for association in associations.values()
                if (
                    association.node_id == node_id
                    and association.role == AssociationRole.MASTER
                    and association.controller_id in controller_ids
                )
            ]

            _issue(
                report,
                "ASSOC-003",
                "Node",
                str(node_id),
                "controller_associations",
                "Node has multiple distinct MASTER Controllers; "
                f"conflicting associations: {', '.join(assoc_ids)}.",
            )

    return report


__all__ = [
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationReport",
    "validate_document",
    "validate_topology",
]