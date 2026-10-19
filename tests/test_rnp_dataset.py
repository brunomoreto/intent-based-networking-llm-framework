
import json
from collections import Counter
from pathlib import Path

from framework.core.topology.serialization import load_topology


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "rnp"
    / "rnp_topology.json"
)


def read_dataset():
    with DATASET_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def test_rnp_dataset_loads_and_is_structurally_valid():
    topology = load_topology(str(DATASET_PATH))

    assert len(topology.nodes) == 34
    assert len(topology.links) == 114
    assert topology.is_structurally_valid()


def test_rnp_dataset_has_unique_link_ids():
    data = read_dataset()
    link_ids = [link["id"] for link in data["links"]]

    assert len(link_ids) == len(set(link_ids))
    assert len(link_ids) == 114


def test_all_link_endpoints_exist():
    data = read_dataset()
    node_ids = {node["id"] for node in data["nodes"]}

    for link in data["links"]:
        assert link["source"] in node_ids
        assert link["destination"] in node_ids
        assert link["source"] != link["destination"]


def test_campo_grande_name_is_normalized():
    data = read_dataset()
    node_names = {node["name"] for node in data["nodes"]}

    assert "Campo Grande" in node_names
    assert "Compo Grande" not in node_names


def test_links_preserve_explicit_directions():
    data = read_dataset()

    assert all(link["bidirectional"] is True for link in data["links"])


def test_link_capacities_are_expressed_in_gbps():
    data = read_dataset()

    expected_capacities = {1, 3, 6, 10, 20, 100, 200, 300}

    for link in data["links"]:
        assert link["bandwidth"] in expected_capacities
        assert link["attributes"]["capacity_unit"] == "Gb/s"


def test_repeated_connections_are_preserved():
    data = read_dataset()

    names_by_id = {
        node["id"]: node["name"]
        for node in data["nodes"]
    }

    directed_connections = Counter(
        (
            names_by_id[link["source"]],
            names_by_id[link["destination"]],
            link["bandwidth"],
        )
        for link in data["links"]
    )

    assert directed_connections[
        ("São Paulo", "Curitiba", 300)
    ] == 2

    assert directed_connections[
        ("Curitiba", "São Paulo", 300)
    ] == 2

    assert directed_connections[
        ("Brasília", "Goiânia", 20)
    ] == 3

    assert directed_connections[
        ("Goiânia", "Brasília", 20)
    ] == 3

    assert directed_connections[
        ("Rio de Janeiro", "Vitória", 100)
    ] == 2

    assert directed_connections[
        ("Vitória", "Rio de Janeiro", 100)
    ] == 2
