# Topology Model V2 — Validation Specification

**Status:** Approved — Definitive Validation Catalog (53 Codes)  
**Scope:** JSON document validation, domain integrity, and semantic validation  
**Schema version:** 2

## 1. Purpose

This document defines the validation architecture and the definitive validation code catalog for Topology Model V2.

The validation system must identify all independently detectable problems in a topology, classify them by severity, and return a structured report rather than stopping at the first error.

Validation is divided into two public operations:

- `validate_document()`: validates the structure and field constraints of a raw Topology V2 JSON document.
- `validate_topology()`: validates the integrity and semantic consistency of an instantiated `Topology` aggregate.

Execution compatibility and network resilience analysis are separate concerns and are not part of structural topology validation.

## 2. Validation architecture

### 2.1 Document validation

```python
def validate_document(
    document: Mapping[str, object],
) -> ValidationReport:
    """Validate the structure and field constraints of a Topology V2 document."""
```

This operation validates the raw, parsed JSON document before domain deserialization.

It checks:

- Required root fields.
- `schema_version`.
- Object and array structures.
- Required and optional fields.
- Field types.
- Unknown structural fields.
- Enum values.
- Numeric constraints.
- IP address and network representations.
- Timestamp representation.
- Metadata, Policy, and Metrics structures.

A JSON syntax or decoding failure occurs before this operation and is reported by the JSON parser. It is not represented as a `ValidationIssue`.

### 2.2 Domain validation

```python
def validate_topology(
    topology: Topology,
) -> ValidationReport:
    """Validate domain integrity and semantic consistency."""
```

This operation validates an instantiated V2 aggregate.

It checks:

- Global identifier uniqueness.
- Referential integrity.
- Node and Interface relationships.
- Link endpoint constraints.
- Directional parameters.
- Static route consistency.
- Controller associations.
- Semantic warnings and informational conditions.

It must not modify the supplied topology.

### 2.3 Loading workflow

The expected document-loading workflow is:

1. Decode the JSON document.
2. Run `validate_document()`.
3. If document errors exist, stop deserialization.
4. Deserialize the valid document into the V2 domain model.
5. Run `validate_topology()`.
6. Return the resulting topology and validation report, or reject the topology if domain errors exist.

The implementation may expose a higher-level loading operation that orchestrates these steps. The two validation operations remain independently accessible.

## 3. Validation result model

### 3.1 Severity

```python
class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
```

Severity meanings:

| Severity | Meaning | Effect |
|---|---|---|
| ERROR | Structural or semantic violation | Invalid topology |
| WARNING | Potential inconsistency or condition requiring attention | Valid topology with warnings |
| INFO | Informational condition that does not violate the model | Valid topology |

The validity rule is:

`valid = (errors is empty)`

Warnings and informational issues do not invalidate a topology.

### 3.2 ValidationIssue

Each issue must contain:

| Field | Description |
|---|---|
| code | Stable validation code |
| severity | ERROR, WARNING, or INFO |
| entity_type | Type of affected entity or document |
| entity_id | Identifier of the affected entity, when available |
| field | Affected field or relationship, when applicable |
| message | Human-readable explanation |

### 3.3 ValidationReport

The report must provide:

- `valid`
- Total issue count.
- Error count.
- Warning count.
- Informational count.
- Complete issue collection.
- Convenient access to errors, warnings, and informational issues.

The validator must accumulate independent issues instead of raising an exception for the first validation failure.

### 3.4 Issue generation rules

1. Every code represents one specific validation condition.
2. A code must retain the same meaning across releases.
3. A message may be improved without changing its code.
4. Independent violations must be reported independently.
5. The same occurrence must not generate duplicate issues for the same condition.
6. A failed prerequisite must not cause cascading or misleading errors.
7. An issue must identify the entity and field whenever they can be determined.
8. Validation must not modify the input document or domain aggregate.

## 4. Definitive validation code catalog

### 4.1 DOC — Document and schema validation

These codes are produced by `validate_document()`.

| Code | Validation condition | Severity |
|---|---|---|
| DOC-001 | `schema_version` is missing | ERROR |
| DOC-002 | `schema_version` is not the integer value `2` | ERROR |
| DOC-003 | A required root field is missing | ERROR |
| DOC-004 | A field has an incompatible data type | ERROR |
| DOC-005 | A required entity field is missing | ERROR |
| DOC-006 | An unknown structural field is present | ERROR |
| DOC-007 | An enum field contains an unsupported value | ERROR |
| DOC-008 | A numeric field contains a non-finite value | ERROR |
| DOC-009 | An integer field contains a non-integer numeric value | ERROR |
| DOC-010 | A boolean field contains a non-boolean value | ERROR |
| DOC-011 | An IP address, IP interface, or network representation is invalid | ERROR |
| DOC-012 | `created_at` contains an invalid datetime representation | ERROR |
| DOC-013 | A required object or collection has an invalid structural shape | ERROR |

Additional requirements:

- The root must contain all required V2 fields, including empty arrays and empty objects.
- The root must reject schema versions other than 2.
- Unknown structural fields must be rejected recursively.
- The `attributes` mapping remains extensible and must not be treated as an unknown-field container.
- Numeric values must be finite. JSON `NaN` and infinity representations must not be accepted.
- Integer fields must not accept decimal values, even when the decimal has no fractional component.
- Boolean fields must not accept integers such as `0` and `1`.
- IP addresses and networks must use the representations specified by the V2 contract.
- Optional fields without defaults may be omitted. Fields with defined defaults must be accepted when omitted and defaulted during deserialization.

### 4.2 ID — Global identifier validation

These codes apply to `validate_document()` and `validate_topology()` whenever the relevant identifiers are available for inspection.

| Code | Validation condition | Severity |
|---|---|---|
| ID-001 | An identifier is duplicated in the global identifier namespace | ERROR |

The global namespace includes:

- `Metadata.id`
- `Node.id`
- `Interface.id`
- `Link.id`
- `Controller.id`
- `StaticRoute.id`
- `ControllerAssociation.id`
- `Policy.id`

All identifiers must be unique across these entity types.

The namespace is global, not scoped by entity type or parent Node/Router.

A duplicate must be reported with enough information to identify the conflicting entities. The validator must not silently overwrite or discard an entity.

### 4.3 REF — Referential integrity

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| REF-001 | A Link references a source or destination Interface that does not exist | ERROR |
| REF-002 | A StaticRoute references an outgoing Interface that does not exist | ERROR |
| REF-003 | A StaticRoute references an Interface that does not belong to its Router | ERROR |
| REF-004 | A ControllerAssociation references a Controller or Node that does not exist | ERROR |

Referential integrity must be checked using identifiers, not array ordering or positional assumptions.

### 4.4 NODE — Node validation

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| NODE-001 | A Node has an unsupported or invalid domain type | ERROR |
| NODE-002 | A Host or Switch contains Router-specific fields | ERROR |
| NODE-003 | A Node has no Interfaces | INFO |

Domain requirements:

- Supported Node types are HOST, SWITCH, and ROUTER.
- Host and Switch must not contain Router-specific fields.
- A Node without Interfaces is valid.
- An empty Interface collection must not be interpreted as a structural error.

### 4.5 INT — Interface validation

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| INT-001 | A MAC address is invalid | ERROR |
| INT-002 | MTU is not a positive integer | ERROR |
| INT-003 | Interface speed is not positive | ERROR |
| INT-004 | An IP address is duplicated across Interfaces | WARNING |
| INT-005 | An Interface has no IP addresses | INFO |
| INT-006 | An Interface does not participate in a Link | INFO |
| INT-007 | An IP address is duplicated within the same Interface | WARNING |

Additional requirements:

- An Interface may have no IPv4 or IPv6 addresses.
- An Interface may exist without participating in a Link.
- IPv4 and IPv6 addresses must preserve their prefix lengths.
- `INT-004` detects duplicate IP addresses across different Interfaces, including Interfaces belonging to different Nodes.
- `INT-007` detects duplicate IP addresses within the same Interface.
- For duplicate detection, two entries are considered duplicates when they represent the same IP address with the same prefix length.
- IPv4 and IPv6 address collections are checked independently.
- Each duplicate occurrence must be reported only once for the same Interface and address.
- `INT-004` and `INT-007` represent different conditions and may both be reported when both independently occur.
- Invalid IP representations must not trigger duplicate-IP warnings.
- An Interface may participate in no more than one Link.
- Interface status must be one of the defined `InterfaceStatus` values. Invalid enum values are reported as `DOC-007` during document validation.

### 4.6 LINK — Link validation

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| LINK-001 | A Link connects an Interface to itself | ERROR |
| LINK-002 | A Link connects two Interfaces belonging to the same Node | ERROR |
| LINK-003 | An Interface participates in more than one Link | ERROR |
| LINK-004 | A Link has no declared reverse direction | INFO |
| LINK-005 | A Link has status FAILED or DISABLED | INFO |

Additional requirements:

- Links connect Interfaces, not Nodes.
- A Link must reference two existing Interfaces.
- A Link cannot connect two Interfaces belonging to the same Node.
- An Interface may participate in no more than one Link.
- Parallel Links between the same Nodes are valid when they use distinct Interfaces.
- The `forward` direction is mandatory.
- The `reverse` direction is optional.
- The absence of `reverse` must not cause the validator to infer or generate a reverse direction.
- A Link with status FAILED or DISABLED remains structurally valid.

### 4.7 DIR — LinkDirection validation

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| DIR-001 | Bandwidth is not greater than zero | ERROR |
| DIR-002 | Delay is negative | ERROR |
| DIR-003 | Weight is not greater than zero | ERROR |
| DIR-004 | Packet loss is outside the inclusive range 0–100 | ERROR |
| DIR-005 | Declared bandwidth exceeds the speed of an endpoint Interface | WARNING |
| DIR-006 | A declared direction has `enabled = false` | INFO |

Additional requirements:

- Bandwidth is expressed in Mbps.
- Delay is expressed in milliseconds.
- Weight is dimensionless.
- Packet loss is expressed as a percentage.
- Bandwidth comparison must be performed independently for each declared direction.
- Each direction must be compared with both endpoint Interface speeds.
- An unspecified Interface speed must be ignored in the comparison.
- A direction with `enabled = false` remains structurally valid.
- A Link with status FAILED or DISABLED makes all its directions unavailable, regardless of their individual `enabled` values.

### 4.8 ROUTE — StaticRoute validation

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| ROUTE-001 | The destination network is invalid | ERROR |
| ROUTE-002 | The next-hop IP address is invalid | ERROR |
| ROUTE-003 | The next-hop IP family differs from the destination network family | ERROR |
| ROUTE-004 | Both `next_hop` and `outgoing_interface_id` are absent | ERROR |
| ROUTE-005 | Next-hop reachability cannot be established from available topology information | WARNING |
| ROUTE-006 | A route is declared while the corresponding IP forwarding family is disabled on the Router | WARNING |
| ROUTE-007 | The route metric is negative | ERROR |
| ROUTE-008 | A StaticRoute duplicates a directly connected network of its Router | ERROR |

Additional requirements:

- Destination must be an IPv4Network or IPv6Network.
- Next hop must be an IPv4Address or IPv6Address.
- At least one of `next_hop` or `outgoing_interface_id` must be provided.
- An outgoing Interface must belong to the Router containing the StaticRoute.
- `metric` must be an integer greater than or equal to zero. A negative integer generates `ROUTE-007`.
- A non-integer metric in the raw document generates `DOC-009`; `ROUTE-007` is evaluated only when the metric is an integer.
- Directly connected routes are inferred from Interface prefixes and must not be duplicated in `static_routes`.
- `ROUTE-008` is generated when a StaticRoute destination exactly matches a directly connected network derived from an Interface belonging to the same Router.
- The comparison must consider IP family, normalized network address, and prefix length. Overlapping but non-identical networks are not duplicates.
- Interfaces belonging to other Nodes must not be considered when determining a Router's directly connected networks.
- Invalid route destinations or invalid relevant Interface address representations must not trigger `ROUTE-008`.
- Failure to prove next-hop reachability is a warning, not an error.
- The validator must not assume that an unverified next hop is unreachable.

### 4.9 CTRL — Controller validation

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| CTRL-001 | `controller_type` or `protocol` is empty or blank | ERROR |
| CTRL-002 | Endpoint is invalid or includes an embedded port | ERROR |
| CTRL-003 | Port is outside the range 1–65535 | ERROR |

Additional requirements:

- `controller_type` and `protocol` are extensible strings.
- Endpoint contains a hostname or IP address only.
- Port is a separate integer field.
- Controller status must be a valid `ControllerStatus` value; invalid enum values are reported as `DOC-007`.
- Controller reachability is not part of structural topology validation.

### 4.10 ASSOC — ControllerAssociation validation

These codes are produced by `validate_topology()`.

| Code | Validation condition | Severity |
|---|---|---|
| ASSOC-001 | The same Controller/Node association is declared more than once | ERROR |
| ASSOC-002 | An association has no declared role | INFO |
| ASSOC-003 | A Node has more than one distinct Controller association with the MASTER role | ERROR |

Additional requirements:

- Controller and Node references must exist.
- Duplicate detection is based on the Controller/Node pair.
- Valid roles are MASTER, STANDBY, and EQUAL.
- A missing role is allowed.
- Invalid role values are reported as `DOC-007` during document validation.
- `ASSOC-003` is generated when more than one distinct Controller is assigned the MASTER role for the same Node.
- Zero or one MASTER association per Node is permitted.
- STANDBY and EQUAL associations do not contribute to `ASSOC-003`.
- Duplicate declarations of the same Controller/Node pair are handled by `ASSOC-001` and must not be counted as distinct MASTER assignments for `ASSOC-003`.
- A Node may have MASTER associations with different Controllers only if the resulting condition is reported as `ASSOC-003`; this rule does not assess Controller reachability, availability, or operational leadership.
- The validator must report at most one `ASSOC-003` issue per affected Node and identify the conflicting associations.

## 5. Validation rules for Metadata, Policy, and Metrics

These structures are validated through the general document codes and global ID validation. Separate POL and MET code families are intentionally not created because they would duplicate the DOC codes for type, required-field, numeric, and structural violations.

### 5.1 Metadata

The validator must enforce the V2 Metadata contract:

- `id` is required and participates in global ID uniqueness.
- `name` is required.
- `description` and `author` are strings when provided.
- `version` is a string.
- `created_at` must be a valid datetime representation when provided.
- `topology_source` must be a valid `TopologySource` value.
- `tags` must be a list of strings.
- Defaults must be applied according to the V2 specification.

### 5.2 Policy

The validator must enforce:

- `id` is required and globally unique.
- `name` is required.
- `description` is a string.
- `enabled` is a boolean.
- `attributes` is a mapping.
- Defaults must be applied according to the V2 specification.

### 5.3 Metrics

The validator must enforce:

- The root `metrics` object is required.
- The `values` mapping is required.
- Each metric value is numeric and finite.
- Metric names are strings.
- The serialized structure is `{"values": {}}` when no metrics are defined.

## 6. Rule precedence and duplicate reporting

To prevent ambiguous or redundant reports, the following precedence applies:

1. JSON syntax and decoding errors are handled by the parser.
2. Document shape and field validation are handled by `validate_document()`.
3. Domain-level identifiers and references are checked after successful deserialization.
4. Semantic rules are evaluated only when their prerequisites are valid.

Examples:

- An invalid enum value is reported as `DOC-007`, not as a second entity-specific enum error.
- An invalid numeric type is reported as `DOC-004`, `DOC-008`, `DOC-009`, or `DOC-010`, according to the specific failure.
- A Link referencing a missing Interface produces `REF-001`. The validator must not additionally compare bandwidth against the nonexistent Interface.
- A StaticRoute referencing an Interface that does not exist produces `REF-002`. The validator must not additionally report that the Interface belongs to another Router.
- An invalid address must not trigger duplicate-IP warnings (`INT-004` or `INT-007`).
- A malformed direction must not trigger semantic bandwidth comparisons.
- A non-integer StaticRoute metric is reported as `DOC-009`; `ROUTE-007` is evaluated only for integer metrics.
- `ROUTE-008` is evaluated only when the StaticRoute destination and the relevant Router Interface network representations are valid.
- `INT-004` applies to duplicates across different Interfaces; `INT-007` applies to duplicates within one Interface. Both may be reported when their respective conditions independently occur.
- `ASSOC-003` is evaluated using distinct Controller/Node pairs with the MASTER role. Duplicate declarations of the same pair are handled by `ASSOC-001`.
- Missing association roles are handled by `ASSOC-002` and do not contribute to `ASSOC-003`.

A validator may report multiple independent violations on the same entity.

## 7. Execution compatibility validation

Execution compatibility is deliberately separate from topology validity.

A structurally valid topology may contain features unsupported by a particular execution adapter.

The architecture must provide a separate operation:

```python
def validate_execution_compatibility(
    topology: Topology,
    adapter: object,
    operation: object | None = None,
) -> ValidationReport:
    """Validate whether a topology can be executed by a specific adapter."""
```

The exact adapter and operation types are implementation contracts to be defined during the adapter phase.

Execution compatibility checks include:

- Router support.
- IPv6 support.
- Directional Link support.
- Unsupported Link parameters.
- Controller availability when required.
- Interface mapping or creation capability.
- Compatibility of DOWN and DISABLED states with the requested operation.

An unsupported feature must not automatically make the topology structurally invalid.

Severity depends on the requested operation:

- WARNING when the feature is unsupported but does not prevent the requested operation.
- ERROR when the feature prevents the requested operation.

## 8. Network resilience analysis

Resilience analysis is not part of structural validation or execution compatibility validation.

It must remain in dedicated services.

The resilience service layer may provide:

- Articulation point detection.
- Bridge Link detection.
- Path diversity.
- Node-disjoint paths.
- Edge-disjoint paths.
- Failure simulation.
- Recovery time measurement.
- Connectivity availability analysis.

These operations consume a validated topology and produce analytical results. They must not modify the topology or reinterpret validation codes.

## 9. Definitive code index

| Family | Codes | Purpose |
|---|---|---|
| DOC | DOC-001–DOC-013 | Document and schema |
| ID | ID-001 | Global identifiers |
| REF | REF-001–REF-004 | Referential integrity |
| NODE | NODE-001–NODE-003 | Nodes |
| INT | INT-001–INT-007 | Interfaces |
| LINK | LINK-001–LINK-005 | Links |
| DIR | DIR-001–DIR-006 | Link directions |
| ROUTE | ROUTE-001–ROUTE-008 | Static routes |
| CTRL | CTRL-001–CTRL-003 | Controllers |
| ASSOC | ASSOC-001–ASSOC-003 | Controller associations |

The catalog contains exactly **53 stable validation codes**.

No separate POL or MET families are defined. Metadata, Policy, and Metrics use the document validation codes and global identifier validation where applicable.

## 10. Testing requirements

Every validation code must have at least one test that triggers it.

The test suite must also include:

### 10.1 Positive tests

- Empty but valid topology collections.
- Nodes without Interfaces.
- Interfaces without IP addresses.
- Interfaces without Links.
- Links without reverse directions.
- Links with disabled directions.
- Links with FAILED or DISABLED status.
- Routers with no StaticRoutes.
- Controllers without associations.
- Associations without roles.
- Valid parallel Links between the same Nodes using distinct Interfaces.
- Valid IPv4 and IPv6 representations.
- Valid empty Policy and Metrics collections.

### 10.2 Negative tests

- Every DOC code.
- Global ID collision across different entity types.
- Every unresolved reference.
- Duplicate Interface participation.
- Same-Node Link endpoints.
- Invalid directional parameters.
- Invalid StaticRoute family combinations.
- Negative integer StaticRoute metric (`ROUTE-007`).
- StaticRoute destination duplicated by a directly connected Router network (`ROUTE-008`).
- Invalid Controller endpoint and port.
- Duplicate Controller/Node associations.
- Multiple distinct MASTER Controllers associated with the same Node (`ASSOC-003`).

### 10.3 Warning and informational tests

- Duplicate IP addresses across different Interfaces (`INT-004`).
- Duplicate IP addresses within the same Interface (`INT-007`).
- Interface speed exceeded by Link bandwidth.
- Unverified next-hop reachability.
- StaticRoute with disabled forwarding.
- Nodes without Interfaces.
- Interfaces without IP addresses or Links.
- Missing reverse direction.
- Disabled directions.
- Failed or disabled Links.
- Controller associations without roles.
- Multiple distinct MASTER Controllers associated with the same Node must produce `ASSOC-003` as an error.

### 10.4 Aggregation tests

- Multiple independent errors must be returned in a single report.
- Warnings and INFO issues must not invalidate a topology.
- Errors must set `valid = false`.
- The validator must not mutate the topology.
- A failed prerequisite must not produce cascading errors.
- Repeated validation of the same input must produce equivalent reports.

### 10.5 Regression tests

V1 tests must not dictate V2 semantics.

Existing tests that depend on Node-to-Node Links, `node.properties`, `bidirectional`, or exception-only validation must be rewritten for the V2 contract.

Historical V1 experiment results must be preserved and must not be overwritten by V2 test outputs.

## 11. Stability and evolution

Validation codes are part of the public V2 contract.

The following rules apply:

1. Never reuse a code for a different condition.
2. Never silently change the meaning of an existing code.
3. New validation conditions receive new codes.
4. Changes to messages do not require code changes.
5. Changes to severity require explicit documentation and tests.
6. Deprecated codes must remain documented as deprecated and must not be reassigned.
7. Document validation, domain validation, execution compatibility, and resilience analysis must remain separate responsibilities.

## 12. Architectural decisions consolidated

The following decisions are approved:

- Topology Model V2 is the only supported model.
- V1-to-V2 compatibility and translation are not implemented.
- `validate_document()` and `validate_topology()` are separate public operations.
- `Metadata.id` participates in global identifier uniqueness.
- INFO codes are retained for valid but relevant topology conditions.
- Validation returns structured reports and accumulates independent issues.
- The validator does not modify the topology.
- Execution compatibility is separate from structural validation.
- Resilience analysis is implemented through dedicated services.
- The 53-code catalog in this document is the definitive V2 validation catalog.