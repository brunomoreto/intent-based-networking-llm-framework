
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "datasets" / "rnp" / "rnp_topology_source.cypher"
DATASET_PATH = ROOT / "datasets" / "rnp" / "rnp_topology.json"


LINK_PATTERN = re.compile(
    r"MATCH\s*\(a:Cidade\s*\{nome:\s*'([^']+)'\}\)"
    r"\s*,\s*\(b:Cidade\s*\{nome:\s*'([^']+)'\}\)"
    r"\s*CREATE\s*\(a\)-\[:CONEXAO\s*"
    r"\{capacidade:\s*(\d+(?:\.\d+)?)\}\]->\(b\)\s*;",
    re.IGNORECASE,
)


def normalize_name(name):
    if name == "Compo Grande":
        return "Campo Grande"
    return name


def read_source_links():
    source = SOURCE_PATH.read_text(encoding="utf-8-sig")
    matches = LINK_PATTERN.findall(source)

    if not matches:
        raise AssertionError(
            "Nenhuma declaração de enlace foi encontrada no Cypher. "
            "Confira o formato do arquivo e a expressão de leitura."
        )

    return Counter(
        (
            normalize_name(source_name),
            normalize_name(destination_name),
            float(capacity),
        )
        for source_name, destination_name, capacity in matches
    )


def read_json_links():
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    names_by_id = {
        node["id"]: normalize_name(node["name"])
        for node in data["nodes"]
    }

    return Counter(
        (
            names_by_id[link["source"]],
            names_by_id[link["destination"]],
            float(link["bandwidth"]),
        )
        for link in data["links"]
    )


def test_source_and_json_have_same_link_declarations():
    source_links = read_source_links()
    json_links = read_json_links()

    missing = source_links - json_links
    extra = json_links - source_links

    assert not missing, f"Enlaces ausentes no JSON: {missing}"
    assert not extra, f"Enlaces extras no JSON: {extra}"


def test_source_contains_expected_number_of_link_declarations():
    source_links = read_source_links()

    assert sum(source_links.values()) == 114


def test_json_contains_expected_number_of_link_declarations():
    json_links = read_json_links()

    assert sum(json_links.values()) == 114

def read_source_nodes():
    source = SOURCE_PATH.read_text(encoding="utf-8-sig")

    # Extrai os nomes das listas UNWIND [...] AS city
    blocks = re.findall(
        r"UNWIND\s*\[(.*?)\]\s*AS\s+city",
        source,
        re.DOTALL | re.IGNORECASE,
    )

    if not blocks:
        raise AssertionError(
            "Nenhuma lista UNWIND de cidades foi encontrada no Cypher."
        )

    names = []
    for block in blocks:
        names.extend(re.findall(r"'([^']+)'", block))

    return Counter(normalize_name(name) for name in names)


def read_json_nodes():
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    return Counter(
        normalize_name(node["name"])
        for node in data["nodes"]
    )


def test_source_and_json_have_same_nodes():
    source_nodes = read_source_nodes()
    json_nodes = read_json_nodes()

    missing = source_nodes - json_nodes
    extra = json_nodes - source_nodes

    assert not missing, f"Nos ausentes no JSON: {missing}"
    assert not extra, f"Nos extras no JSON: {extra}"


def test_source_contains_expected_number_of_nodes():
    assert sum(read_source_nodes().values()) == 34


def test_json_contains_expected_number_of_nodes():
    assert sum(read_json_nodes().values()) == 34