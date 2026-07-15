# Coding Standards

**Document Version:** 1.0

**Status:** Draft

---

# 1. Purpose

This document defines the implementation standards adopted by the Intent-Based Networking LLM Framework.

The objective is to guarantee consistency, readability, maintainability, and reproducibility throughout the entire project.

Every module implemented in the framework shall follow the conventions defined in this specification.

---

# 2. General Principles

The implementation follows the same architectural principles adopted by the framework.

- Single Responsibility Principle
- Technology Independence
- Loose Coupling
- Explicit Typing
- Deterministic Behavior
- Reproducibility

---

# 3. Programming Language

The framework is implemented using Python.

Only stable language features supported by the selected Python version shall be used.

---

# 4. Project Organization

Every source file belongs to one of the following architectural layers.

```text
Framework

├── Core
├── Services
├── Adapters
└── Utils
```

No source code shall exist outside these layers.

---

# 5. Core Domain

The Core Domain contains only domain objects.

Domain objects shall not contain implementation-specific dependencies.

The Core Domain shall never depend on:

- Mininet
- ONOS
- Neo4j
- Docker
- OpenStack
- NetworkX
- Large Language Models

The Core Domain depends only on the Python Standard Library.

---

# 6. Data Representation

Every domain entity shall be implemented using Python dataclasses.

Example domain entities include:

- Topology
- Metadata
- NetworkElement
- Node
- Link
- Policy
- Metrics
- Recommendation
- ValidationReport
- Experiment

Domain entities represent data only.

Business logic shall remain outside these classes.

---

# 7. Type Hints

Every function, method, attribute, and return value shall use explicit type hints.

Examples:

```python
list[Node]

dict[str, str]

Optional[Metadata]
```

Implicit typing should be avoided whenever possible.

---

# 8. Enumerations

Finite sets of values shall be represented using Enum.

Examples include:

- NodeType
- LinkStatus
- ValidationStatus
- RecommendationType
- TopologyType

String literals should not be used to represent enumerated values.

---

# 9. Naming Conventions

## Classes

PascalCase

Examples:

- Topology
- Metadata
- Recommendation

---

## Methods

snake_case

Examples:

- add_node()
- remove_node()
- validate()

---

## Variables

snake_case

Examples:

- node_id
- topology_name
- validation_report

---

## Constants

UPPER_CASE

Examples:

- DEFAULT_DELAY
- MAX_LINKS

---

## Files

snake_case

Examples:

- serialization.py
- validator.py
- recommendation.py

---

# 10. Module Responsibilities

Every module shall have a single responsibility.

## schema.py

Defines domain entities.

Contains no business logic.

---

## topology.py

Manipulates topology objects.

Contains the public API of the topology module.

---

## serialization.py

Converts domain objects to and from the Network Description Language (NDL).

---

## validator.py

Implements structural validation rules.

---

## exceptions.py

Defines framework-specific exceptions.

---

# 11. Error Handling

Framework modules shall raise explicit exceptions.

Generic exceptions should be avoided.

Examples include:

- TopologyError
- NodeError
- LinkError
- ValidationError

---

# 12. Documentation

Every public class shall contain a descriptive docstring.

Every public method shall document:

- Purpose
- Parameters
- Return value
- Raised exceptions

Complex implementation details should be documented when necessary.

---

# 13. Testing

Every module shall be accompanied by unit tests.

Implementation is considered complete only when corresponding unit tests are available.

Tests shall remain independent from external infrastructure whenever possible.

---

# 14. Dependencies

The framework adopts a dependency inversion strategy.

Higher-level modules shall never depend directly on infrastructure technologies.

Infrastructure-specific implementations belong exclusively to the Adapter layer.

---

# 15. Serialization

The Network Description Language (NDL) is the only supported exchange format between framework modules.

No module shall exchange implementation-specific objects.

Every communication must occur through domain objects or their serialized NDL representation.

---

# 16. Code Review Checklist

Before merging any new module, verify the following:

- Architecture is respected.
- Type hints are complete.
- Dataclasses are used when appropriate.
- Unit tests are implemented.
- Documentation is updated.
- No technology-specific dependency exists inside the Core Domain.
- Interfaces remain compatible with the module specifications.

---

# 17. Future Evolution

These standards are expected to evolve together with the framework.

Any modification affecting the architecture or coding conventions shall be documented before implementation.