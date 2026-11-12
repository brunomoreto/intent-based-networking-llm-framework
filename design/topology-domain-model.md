# Topology Domain Model V2

**Projeto:** Intent-Based Networking LLM Framework  
**Documento:** `design/topology-domain-model.md`  
**Versão:** 2.0  
**Status:** Aprovado para implementação após congelamento da especificação

## 1. Objetivo

Definir o modelo de domínio da Topology V2, estabelecendo entidades, responsabilidades, relacionamentos, tipos e invariantes necessários para representar topologias de redes de forma independente de tecnologias específicas.

A versão V2 substitui integralmente o modelo V1. Não haverá conversão, fallback ou compatibilidade retroativa com V1.

## 2. Princípios arquiteturais

- A topologia é representada por um agregado cujo root é `Topology`.
- Links conectam interfaces, e não diretamente Nodes.
- Interfaces pertencem a Nodes.
- Controllers são entidades independentes dos Nodes.
- StaticRoutes pertencem a Routers.
- A direção dos links é explicitamente representada.
- Identificadores possuem unicidade global dentro da topologia.
- O domínio não depende de Mininet, ONOS ou outras tecnologias de infraestrutura.
- A validação não modifica o estado da topologia.
- O agregado deve oferecer cópia defensiva por meio de `snapshot()`.

## 3. Topology Aggregate

O agregado `Topology` contém:

- `metadata`
- `nodes`
- `links`
- `controllers`
- `controller_associations`
- `policies`
- `metrics`

O agregado é responsável por preservar a integridade das entidades e suas referências.

Interfaces são aninhadas em Nodes. StaticRoutes são aninhadas em Routers.

## 4. Entidades do domínio

### 4.1 Metadata

| Campo | Tipo | Obrigatório | Default |
|---|---|---|---|
| id | TopologyId | Sim | — |
| name | str | Sim | — |
| description | str | Não | `""` |
| author | str | Não | `""` |
| version | str | Não | `"1.0"` |
| created_at | datetime ou None | Não | `None` |
| topology_source | TopologySource | Não | `CUSTOM` |
| tags | list[str] | Não | `[]` |

### 4.2 NetworkElement

Classe-base dos elementos do plano de dados:

- `id: NodeId`
- `name: str`
- `attributes: Attributes = {}`

### 4.3 Node

Especialização de NetworkElement:

- `node_type: NodeType`
- `interfaces: list[Interface] = []`

Tipos de Node:

- `Host`
- `Switch`
- `Router`

Nodes podem existir sem interfaces e sem links.

### 4.4 Router

Além dos campos herdados de Node:

- `ipv4_forwarding: bool = false`
- `ipv6_forwarding: bool = false`
- `static_routes: list[StaticRoute] = []`

### 4.5 Interface

Representa uma interface de rede pertencente a um Node.

| Campo | Tipo | Default |
|---|---|---|
| id | InterfaceId | Obrigatório |
| name | str | Obrigatório |
| mac_address | str ou None | Ausente |
| ipv4_addresses | list[IPv4Interface] | `[]` |
| ipv6_addresses | list[IPv6Interface] | `[]` |
| mtu | int ou None | Ausente |
| speed | Bandwidth ou None | Ausente |
| status | InterfaceStatus | `UP` |
| attributes | Attributes | `{}` |

A propriedade da interface é determinada pelo seu aninhamento em `Node.interfaces`. Não haverá duplicação de `node_id`.

Uma interface poderá existir sem endereço IP e sem participação em um Link.

Uma interface poderá participar de, no máximo, um Link.

### 4.6 StaticRoute

Representa uma rota estática pertencente a um Router.

- `id: RouteId`
- `destination: IPv4Network | IPv6Network`
- `next_hop: IPv4Address | IPv6Address | None`
- `outgoing_interface_id: InterfaceId | None`
- `metric: int = 0`

Invariantes:

- Pelo menos um entre `next_hop` e `outgoing_interface_id` deve estar presente.
- A família IP do next hop deve corresponder à família do destino.
- A interface de saída deve pertencer ao mesmo Router.
- Rotas diretamente conectadas são inferidas a partir dos prefixos das interfaces e não devem ser duplicadas em `static_routes`.

### 4.7 LinkDirection

Representa os parâmetros de uma direção de um enlace.

- `bandwidth: Bandwidth`
- `delay: Delay`
- `weight: Weight`
- `packet_loss: PacketLoss`
- `enabled: bool`

Unidades e limites:

| Campo | Unidade | Restrição |
|---|---|---|
| bandwidth | Mbps | Maior que zero |
| delay | ms | Maior ou igual a zero |
| weight | Adimensional | Maior que zero |
| packet_loss | % | Entre 0 e 100 |

### 4.8 Link

Representa a conexão entre duas interfaces.

- `id: LinkId`
- `source_interface_id: InterfaceId`
- `destination_interface_id: InterfaceId`
- `forward: LinkDirection`
- `reverse: LinkDirection | None`
- `status: LinkStatus = ACTIVE`
- `attributes: Attributes = {}`

Invariantes:

- `forward` é obrigatório.
- `reverse` é opcional.
- A ausência de `reverse` significa que não existe direção reversa declarada.
- Não se deve inferir ou gerar automaticamente a direção reversa.
- As interfaces de origem e destino devem pertencer a Nodes distintos.
- Uma interface não pode participar de mais de um Link.
- Links paralelos entre os mesmos Nodes são permitidos quando utilizam interfaces distintas.
- Links entre interfaces do mesmo Node são proibidos nesta versão.
- `FAILED` ou `DISABLED` torna indisponíveis todas as direções do Link, independentemente do atributo `enabled`.

### 4.9 Controller

Entidade independente dos Nodes:

- `id: ControllerId`
- `name: str`
- `controller_type: str`
- `endpoint: str`
- `port: int`
- `protocol: str`
- `status: ControllerStatus = UNKNOWN`
- `attributes: Attributes = {}`

`endpoint` representa hostname ou endereço IP, sem porta embutida.

`port` deve estar no intervalo de 1 a 65535.

`controller_type` e `protocol` são strings extensíveis.

### 4.10 ControllerAssociation

Representa a associação entre um Controller e um Node.

- `id: AssociationId`
- `controller_id: ControllerId`
- `node_id: NodeId`
- `role: AssociationRole | None`

Roles:

- `MASTER`
- `STANDBY`
- `EQUAL`

Controllers sem associações e Nodes sem Controllers são permitidos.

Não são permitidas associações duplicadas entre o mesmo Controller e Node.

### 4.11 Policy

- `id: PolicyId`
- `name: str`
- `description: str = ""`
- `enabled: bool = True`
- `attributes: Attributes = {}`

### 4.12 Metrics

Representação:

```python
@dataclass(slots=True, kw_only=True)
class Metrics:
    values: MetricValues = field(default_factory=dict)
```

Tipos:

- `MetricValue = float`
- `MetricValues = dict[str, MetricValue]`

## 5. Enumerations

| Enum | Valores |
|---|---|
| NodeType | HOST, SWITCH, ROUTER |
| LinkStatus | ACTIVE, FAILED, DISABLED |
| InterfaceStatus | UP, DOWN, DISABLED |
| ControllerStatus | UNKNOWN, ACTIVE, DEGRADED, UNAVAILABLE |
| AssociationRole | MASTER, STANDBY, EQUAL |
| TopologySource | CUSTOM, REFERENCE, SYNTHETIC, PRODUCTION |

`CONTROLLER` não pertence a `NodeType`.

## 6. Identificadores

Todos os identificadores pertencem a um namespace global dentro do agregado `Topology`.

A unicidade abrange:

- Metadata.id
- Node.id
- Interface.id
- Link.id
- Controller.id
- StaticRoute.id
- ControllerAssociation.id
- Policy.id

Nenhuma entidade poderá compartilhar um identificador com outra entidade, mesmo que pertençam a tipos diferentes.

## 7. Tipos fundamentais

Os identificadores são aliases de string:

- `TopologyId`
- `NodeId`
- `InterfaceId`
- `LinkId`
- `ControllerId`
- `RouteId`
- `AssociationId`
- `PolicyId`

Outros tipos:

- `Attributes = dict[str, Any]`
- `Bandwidth`
- `Delay`
- `PacketLoss`
- `Weight`

Os endereços IP utilizam os tipos nativos do módulo `ipaddress` do Python.

## 8. PathResult

O resultado de busca de caminhos deve preservar a identidade dos Nodes, Interfaces e Links percorridos.

Cada segmento identifica:

- Link utilizado;
- interface de origem do segmento;
- interface de destino do segmento;
- direção utilizada (`FORWARD` ou `REVERSE`).

O resultado completo identifica:

- Node de origem;
- Node de destino;
- sequência ordenada de Nodes;
- sequência ordenada de segmentos;
- custo calculado;
- métrica utilizada para calcular o custo.

Métricas definidas:

- `HOP_COUNT`
- `WEIGHT_SUM`
- `DELAY_SUM`

O custo e sua métrica devem ser informados conjuntamente ou permanecer ambos ausentes.

O resultado deve permitir distinguir caminhos que utilizam Links paralelos diferentes.

## 9. Responsabilidades e separação arquitetural

O domínio representa a topologia e suas invariantes.

A validação estrutural e semântica é responsabilidade do serviço de validação.

A compatibilidade de execução é responsabilidade de uma validação específica, separada da integridade estrutural.

Os adapters são responsáveis por traduzir informações de tecnologias como ONOS e Mininet para o modelo de domínio.

Serviços de resiliência devem operar sobre a topologia V2 sem incorporar suas análises à validação estrutural.

## 10. Evolução

A evolução do modelo deverá preservar os contratos explícitos desta versão.

Novos atributos específicos de tecnologias podem ser armazenados em `attributes`, desde que não substituam campos estruturais definidos pelo domínio.

A versão V1 permanece exclusivamente como histórico de desenvolvimento e experimentação.