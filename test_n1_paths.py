
import json
from pathlib import Path

from framework.core.topology.serialization import deserialize_topology
from framework.services.path_finder import find_path


dataset_path = Path("datasets/n1/redundant_topology.json")

document = json.loads(dataset_path.read_text(encoding="utf-8"))
topology = deserialize_topology(document)

# Teste 1: caminho entre h1 e h2
path = find_path(topology, "h1", "h2")

print("Path found:", path)

assert path is not None, "No path found between h1 and h2."
assert path[0] == "h1"
assert path[-1] == "h2"

# Teste 2: caminho alternativo após falha de l2
topology_without_l2 = topology.copy()
topology_without_l2.remove_link("l2")

alternative_path = find_path(
    topology_without_l2,
    "h1",
    "h2",
)

print("Alternative path:", alternative_path)

assert alternative_path is not None
assert alternative_path[0] == "h1"
assert alternative_path[-1] == "h2"
assert "s3" in alternative_path

# Teste 3: caminho alternativo após falha de l3
topology_without_l3 = topology.copy()
topology_without_l3.remove_link("l3")

alternative_path_2 = find_path(
    topology_without_l3,
    "h1",
    "h2",
)

print("Alternative path 2:", alternative_path_2)

assert alternative_path_2 is not None
assert alternative_path_2[0] == "h1"
assert alternative_path_2[-1] == "h2"
assert "s2" in alternative_path_2

print("\nAll N1 path tests passed.")
