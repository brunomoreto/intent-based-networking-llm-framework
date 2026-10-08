                           Framework
                                │
      ┌─────────────────────────┼─────────────────────────┐
      ▼                         ▼                         ▼
 Core Domain          Application Services     Infrastructure Adapters

      │                         │                         │

      ▼                         ▼                         ▼

Topology                Collector                ONOS

Recommendation          Planner                  Neo4j

ValidationReport        Validator                Mininet

Experiment              Executor                 LLM

## Architectural Decisions

### AD-001 — Technology-independent Core Domain

The Core Domain is completely independent of infrastructure technologies.

All interactions with ONOS, Mininet, Neo4j, Docker, OpenStack, and Large Language Models are performed exclusively through the Adapter layer.

This decision guarantees modularity, reproducibility, and extensibility while allowing new technologies to be incorporated without modifications to the Core Domain.