# Topology Specification V2

**Projeto:** Intent-Based Networking LLM Framework  
**Documento:** `design/topology-specification.md`  
**Versão:** 2.0  
**Status:** Aprovado para implementação após congelamento da especificação

## 1. Objetivo

Definir o contrato JSON da Topology V2, incluindo:

- Estrutura raiz;
- Entidades e seus campos;
- Tipos de dados;
- Campos obrigatórios e opcionais;
- Valores padrão;
- Regras de serialização e desserialização;
- Restrições estruturais;
- Representação de endereços IP;
- Identificação da versão do schema.

A Topology V2 é o único formato suportado pela implementação. Não haverá parser V1, conversão V1→V2, fallback ou compatibilidade retroativa.

## 2. Identificação da versão

O documento JSON deve conter:

```json
{
  "schema_version": 2
}
```

Regras:

- `schema_version` é obrigatório.
- O valor aceito é exclusivamente o inteiro `2`.
- Valores diferentes de `2` devem ser rejeitados.
- Não deve existir detecção automática de versões anteriores.
- A implementação não deve interpretar documentos V1.

## 3. Estrutura raiz

A estrutura raiz é obrigatória e deve conter todos os campos abaixo, mesmo quando os respectivos arrays ou objetos estiverem vazios.

```json
{
  "schema_version": 2,
  "metadata": {},
  "nodes": [],
  "links": [],
  "controllers": [],
  "controller_associations": [],
  "policies": [],
  "metrics": {
    "values": {}
  }
}
```

| Campo | Tipo | Obrigatório |
|---|---|---|
| schema_version | integer | Sim |
| metadata | object | Sim |
| nodes | array | Sim |
| links | array | Sim |
| controllers | array | Sim |
| controller_associations | array | Sim |
| policies | array | Sim |
| metrics | object | Sim |

A ausência de qualquer campo da estrutura raiz constitui erro de schema.

## 4. Metadata

Estrutura:

```json
{
  "id": "topology-01",
  "name": "Network Topology",
  "description": "Example topology",
  "author": "Research Team",
  "version": "1.0",
  "created_at": "2026-01-15T10:30:00Z",
  "topology_source": "custom",
  "tags": ["research", "sdn"]
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| name | string | Sim | — |
| description | string | Não | `""` |
| author | string | Não | `""` |
| version | string | Não | `"1.0"` |
| created_at | string ISO 8601 ou null | Não | `null` |
| topology_source | string enum | Não | `"custom"` |
| tags | array de strings | Não | `[]` |

Valores aceitos para `topology_source`:

- `custom`
- `reference`
- `synthetic`
- `production`

`created_at` deve ser convertido para `datetime` durante a desserialização e serializado como ISO 8601.

## 5. Nodes

A coleção `nodes` contém objetos do tipo Host, Switch ou Router.

### 5.1 Estrutura comum

```json
{
  "id": "s1",
  "name": "Switch 1",
  "node_type": "switch",
  "interfaces": [],
  "attributes": {}
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| name | string | Sim | — |
| node_type | string enum | Sim | — |
| interfaces | array | Não | `[]` |
| attributes | object | Não | `{}` |

Valores aceitos para `node_type`:

- `host`
- `switch`
- `router`

`controller` não é um tipo válido de Node.

### 5.2 Host

Host utiliza a estrutura comum, com `node_type` igual a `host`.

Não pode conter campos específicos de Router.

Exemplo:

```json
{
  "id": "h1",
  "name": "Host 1",
  "node_type": "host",
  "interfaces": [],
  "attributes": {}
}
```

### 5.3 Switch

Switch utiliza a estrutura comum, com `node_type` igual a `switch`.

Não pode conter campos específicos de Router.

Exemplo:

```json
{
  "id": "s1",
  "name": "Switch 1",
  "node_type": "switch",
  "interfaces": [],
  "attributes": {}
}
```

### 5.4 Router

Router possui os campos adicionais:

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| ipv4_forwarding | boolean | Não | `false` |
| ipv6_forwarding | boolean | Não | `false` |
| static_routes | array | Não | `[]` |

Exemplo:

```json
{
  "id": "r1",
  "name": "Router 1",
  "node_type": "router",
  "interfaces": [],
  "ipv4_forwarding": false,
  "ipv6_forwarding": false,
  "static_routes": [],
  "attributes": {}
}
```

Os campos `ipv4_forwarding`, `ipv6_forwarding` e `static_routes` são exclusivos de Router.

Sua presença em Host ou Switch deve ser rejeitada.

## 6. Interfaces

As interfaces são representadas dentro de `Node.interfaces`.

Exemplo:

```json
{
  "id": "h1-eth0",
  "name": "eth0",
  "mac_address": "02:00:00:00:00:01",
  "ipv4_addresses": ["192.168.10.10/24"],
  "ipv6_addresses": ["2001:db8:10::10/64"],
  "mtu": 1500,
  "speed": 1000,
  "status": "up",
  "attributes": {}
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| name | string | Sim | — |
| mac_address | string | Não | Ausente |
| ipv4_addresses | array de strings | Não | `[]` |
| ipv6_addresses | array de strings | Não | `[]` |
| mtu | integer | Não | Ausente |
| speed | number | Não | Ausente |
| status | string enum | Não | `"up"` |
| attributes | object | Não | `{}` |

Valores aceitos para `status`:

- `up`
- `down`
- `disabled`

### 6.1 Endereços IPv4

Os endereços IPv4 devem ser representados com prefixo CIDR.

Exemplo:

```json
"ipv4_addresses": [
  "192.168.10.10/24",
  "10.0.0.1/30"
]
```

Conversão para o domínio:

- `IPv4Interface`

### 6.2 Endereços IPv6

Os endereços IPv6 também devem ser representados com prefixo CIDR.

Exemplo:

```json
"ipv6_addresses": [
  "2001:db8:10::10/64"
]
```

Conversão para o domínio:

- `IPv6Interface`

### 6.3 Restrições

- Endereços IP inválidos devem ser rejeitados.
- MTU deve ser um inteiro positivo.
- Speed deve ser maior que zero.
- Uma interface pode existir sem endereços IP.
- Uma interface pode existir sem participar de um Link.
- Não deve existir campo `node_id` na Interface, pois sua propriedade é definida pelo aninhamento.

## 7. StaticRoutes

As rotas estáticas são representadas dentro de `Router.static_routes`.

Exemplo:

```json
{
  "id": "route-r1-01",
  "destination": "192.168.30.0/24",
  "next_hop": "192.168.20.254",
  "metric": 10
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| destination | string CIDR | Sim | — |
| next_hop | string IP ou null | Não | `null` |
| outgoing_interface_id | string ou null | Não | `null` |
| metric | integer | Não | `0` |

Regras:

- `destination` deve ser convertido para `IPv4Network` ou `IPv6Network`.
- `next_hop` deve ser convertido para `IPv4Address` ou `IPv6Address`.
- `next_hop` não deve conter prefixo CIDR.
- Pelo menos um entre `next_hop` e `outgoing_interface_id` deve estar presente.
- A família IP de `next_hop` deve corresponder à de `destination`.
- `outgoing_interface_id`, quando presente, deve identificar uma interface pertencente ao mesmo Router.
- `metric` deve ser um inteiro maior ou igual a zero.

## 8. Links

Links conectam interfaces, não diretamente Nodes.

Exemplo:

```json
{
  "id": "l1",
  "source_interface_id": "s1-eth1",
  "destination_interface_id": "s2-eth1",
  "forward": {
    "bandwidth": 1000,
    "delay": 2,
    "weight": 1,
    "packet_loss": 0,
    "enabled": true
  },
  "reverse": {
    "bandwidth": 1000,
    "delay": 2,
    "weight": 1,
    "packet_loss": 0,
    "enabled": true
  },
  "status": "active",
  "attributes": {}
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| source_interface_id | string | Sim | — |
| destination_interface_id | string | Sim | — |
| forward | object | Sim | — |
| reverse | object | Não | Ausente |
| status | string enum | Não | `"active"` |
| attributes | object | Não | `{}` |

Valores aceitos para `status`:

- `active`
- `failed`
- `disabled`

### 8.1 LinkDirection

Estrutura:

```json
{
  "bandwidth": 1000,
  "delay": 2,
  "weight": 1,
  "packet_loss": 0,
  "enabled": true
}
```

| Campo | Tipo JSON | Obrigatório |
|---|---|---|
| bandwidth | number | Sim |
| delay | number | Sim |
| weight | number | Sim |
| packet_loss | number | Sim |
| enabled | boolean | Sim |

Restrições:

- `bandwidth > 0`, em Mbps.
- `delay >= 0`, em milissegundos.
- `weight > 0`, adimensional.
- `packet_loss` entre 0 e 100, inclusive.
- `enabled` deve ser booleano.

### 8.2 Direcionalidade

- `forward` é obrigatório.
- `reverse` é opcional.
- A ausência de `reverse` significa que a direção reversa não está declarada.
- O parser não deve criar automaticamente uma direção reversa.
- A direção efetivamente utilizável depende também do status do Link e do atributo `enabled` da respectiva direção.

### 8.3 Referências

- `source_interface_id` deve identificar uma Interface existente.
- `destination_interface_id` deve identificar uma Interface existente.
- As interfaces devem pertencer a Nodes distintos.
- Uma Interface pode participar de, no máximo, um Link.
- Links paralelos entre os mesmos Nodes são permitidos quando utilizam interfaces distintas.

## 9. Controllers

Controllers são entidades independentes dos Nodes.

Exemplo:

```json
{
  "id": "onos-01",
  "name": "ONOS Controller 01",
  "controller_type": "onos",
  "endpoint": "192.168.100.10",
  "port": 6653,
  "protocol": "openflow",
  "status": "active",
  "attributes": {}
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| name | string | Sim | — |
| controller_type | string | Sim | — |
| endpoint | string | Sim | — |
| port | integer | Sim | — |
| protocol | string | Sim | — |
| status | string enum | Não | `"unknown"` |
| attributes | object | Não | `{}` |

Valores aceitos para `status`:

- `unknown`
- `active`
- `degraded`
- `unavailable`

Regras:

- `controller_type` e `protocol` são strings extensíveis e não devem ser limitados a um conjunto fechado de tecnologias.
- `endpoint` representa hostname ou endereço IP, sem porta embutida.
- `port` deve estar entre 1 e 65535.

## 10. ControllerAssociations

Exemplo:

```json
{
  "id": "assoc-01",
  "controller_id": "onos-01",
  "node_id": "s1",
  "role": "master"
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| controller_id | string | Sim | — |
| node_id | string | Sim | — |
| role | string enum | Não | Ausente |

Valores aceitos para `role`:

- `master`
- `standby`
- `equal`

Regras:

- `controller_id` deve identificar um Controller existente.
- `node_id` deve identificar um Node existente.
- A mesma combinação Controller/Node não pode aparecer mais de uma vez.
- `role` pode ser omitido.
- Controllers sem associações e Nodes sem Controllers são permitidos.

## 11. Policies

Exemplo:

```json
{
  "id": "policy-01",
  "name": "QoS Policy",
  "description": "Example network policy",
  "enabled": true,
  "attributes": {}
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| id | string | Sim | — |
| name | string | Sim | — |
| description | string | Não | `""` |
| enabled | boolean | Não | `true` |
| attributes | object | Não | `{}` |

## 12. Metrics

Estrutura:

```json
{
  "values": {
    "latency_ms": 2.5,
    "throughput_mbps": 950.0,
    "packet_loss": 0.1
  }
}
```

| Campo | Tipo JSON | Obrigatório | Default |
|---|---|---|---|
| values | object de números | Não | `{}` |

O objeto `metrics` deve estar presente na raiz.

`values` deve ser um objeto cujas chaves são strings e cujos valores são números finitos.

Representação no domínio:

- `MetricValue = float`
- `MetricValues = dict[str, MetricValue]`

## 13. Identificadores e referências

Todos os IDs pertencem a um namespace global dentro da topologia.

A unicidade deve ser verificada entre:

- Metadata.id
- Node.id
- Interface.id
- Link.id
- Controller.id
- StaticRoute.id
- ControllerAssociation.id
- Policy.id

Não são permitidos identificadores duplicados, mesmo quando pertencem a entidades de tipos diferentes.

Todas as referências devem ser resolvidas:

- Links → Interfaces;
- StaticRoutes → Interfaces do próprio Router;
- ControllerAssociations → Controllers e Nodes.

A ordem dos elementos nos arrays não possui significado semântico. A resolução deve ocorrer por identificadores.

## 14. Campos desconhecidos

Campos estruturais desconhecidos devem ser rejeitados recursivamente.

A exceção é o campo `attributes`, que permite extensões específicas de implementação ou tecnologia.

Essa flexibilidade não permite utilizar `attributes` para substituir campos estruturais definidos pelo contrato V2.

## 15. Regras de tipos numéricos

- Inteiros e números decimais JSON são aceitos quando compatíveis com o tipo do campo.
- Campos definidos como booleanos não devem aceitar números como substitutos.
- Campos definidos como inteiros devem rejeitar valores decimais.
- Valores não finitos, como NaN e Infinity, devem ser rejeitados.
- Unidades não devem ser representadas como strings.
- Os valores numéricos devem seguir as restrições específicas de cada campo.

## 16. Defaults e serialização canônica

### 16.1 Desserialização

O parser deve:

- Aplicar os defaults definidos neste documento quando campos opcionais forem omitidos.
- Rejeitar campos obrigatórios ausentes.
- Rejeitar campos estruturalmente desconhecidos.
- Converter endereços IP para os tipos nativos do módulo `ipaddress`.
- Converter `created_at` para datetime.
- Resolver e validar as referências entre entidades.

### 16.2 Serialização

O serializer deve produzir uma representação canônica:

- Incluir todos os campos obrigatórios.
- Emitir campos que possuem defaults, mesmo quando assumiram seus valores padrão.
- Não inventar campos opcionais sem default.
- Preservar a ausência de `reverse` quando não declarado.
- Preservar a ausência de `role` quando não declarado.
- Preservar a ausência de `mac_address`, `mtu` e `speed` quando não informados.
- Serializar endereços IP com prefixo quando forem objetos de interface ou redes de destino.
- Serializar next hops como endereços IP sem prefixo.
- Serializar datas em ISO 8601.

A serialização e desserialização devem preservar o significado do modelo de domínio.

## 17. Separação entre Topology JSON e PathResult

`PathResult` é uma estrutura de resultado de execução de serviços de caminho, não uma entidade persistida na estrutura raiz da topologia.

Seu contrato é definido separadamente no modelo de domínio e nos serviços de caminhos.

A representação de um caminho deve preservar:

- IDs dos Nodes;
- IDs dos Links;
- Interfaces de origem e destino de cada segmento;
- Direção percorrida;
- Custo;
- Métrica utilizada no cálculo.

Métricas de custo definidas:

- `HOP_COUNT`
- `WEIGHT_SUM`
- `DELAY_SUM`

## 18. Conformidade

Uma implementação compatível com Topology V2 deve:

1. Aceitar exclusivamente `schema_version = 2`.
2. Implementar integralmente a estrutura raiz obrigatória.
3. Respeitar os tipos e defaults definidos.
4. Rejeitar campos estruturais desconhecidos.
5. Aplicar unicidade global dos IDs.
6. Resolver todas as referências.
7. Preservar a direcionalidade dos Links.
8. Preservar a propriedade das Interfaces e StaticRoutes.
9. Implementar serialização e desserialização canônicas.
10. Não introduzir qualquer mecanismo de compatibilidade com V1.