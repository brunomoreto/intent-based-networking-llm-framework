# Topology Model V2 — Implementation Plan

**Projeto:** Intent-Based Networking LLM Framework  
**Documento:** `Topology Model V2 — Implementation Plan`  
**Versão:** 2.0  
**Status:** Aprovado para execução após congelamento da especificação

## 1. Objetivo

Definir a estratégia de implementação do Topology Model V2, estabelecendo fases, dependências, entregáveis e critérios de aceite.

A implementação deverá substituir integralmente o modelo V1, adotando exclusivamente os contratos definidos nos seguintes documentos:

- `design/topology-domain-model.md`
- `design/topology-specification.md`
- `design/topology-validation.md`

Não haverá implementação de conversores, parsers, fallbacks ou mecanismos de compatibilidade V1.

A versão V1 permanecerá apenas no histórico do projeto e nos registros de experimentos já realizados.

## 2. Princípios de implementação

1. Implementação incremental e orientada a testes.
2. Domínio independente de tecnologias externas.
3. Separação entre entidades, serialização, validação, serviços e adapters.
4. Integridade do agregado `Topology`.
5. Unicidade global dos identificadores.
6. Representação explícita de interfaces e direcionalidade dos links.
7. Validação sem mutação do estado.
8. Cópia defensiva do agregado por meio de `snapshot()`.
9. Resultados de caminhos estruturados.
10. Preservação dos dados originais de referência e dos resultados experimentais históricos.

## 3. Organização do pacote de domínio

A implementação deverá considerar a seguinte organização:

```text
framework/
└── core/
    └── topology/
        ├── __init__.py
        ├── types.py
        ├── enums.py
        ├── exceptions.py
        ├── models.py
        ├── topology.py
        ├── serialization.py
        └── validator.py
```

Serviços relacionados:

```text
framework/
└── services/
    ├── path_finder.py
    ├── validator/
    │   └── path_validator.py
    ├── collector/
    │   └── onos_topology_adapter.py
    ├── executor/
    │   └── experiment_executor.py
    └── ...
```

A organização final deverá respeitar a estrutura existente do repositório, evitando criar módulos redundantes.

## 4. Fases de implementação

### Fase 1 — Domain Types and Enumerations

**Objetivo:** estabelecer os tipos fundamentais e os enumeradores da Topology V2.

Arquivos principais:

- `framework/core/topology/types.py`
- `framework/core/topology/enums.py`

Atividades:

1. Definir aliases de identificadores:
   - TopologyId
   - NodeId
   - InterfaceId
   - LinkId
   - ControllerId
   - RouteId
   - AssociationId
   - PolicyId

2. Definir os tipos fundamentais:
   - Attributes
   - Bandwidth
   - Delay
   - PacketLoss
   - Weight
   - MetricValue
   - MetricValues

3. Definir enumeradores:
   - NodeType
   - LinkStatus
   - InterfaceStatus
   - ControllerStatus
   - AssociationRole
   - TopologySource

4. Remover o conceito de `CONTROLLER` de NodeType.

5. Avaliar a remoção de `Properties`, migrando os usos válidos para campos explícitos ou `Attributes`.

6. Garantir que os tipos IP do domínio utilizem o módulo nativo `ipaddress`.

Testes:

- Existência dos aliases e enums.
- Valores válidos dos enumeradores.
- Ausência de `CONTROLLER` em NodeType.
- Ausência de dependências externas no módulo de domínio.

Critério de aceite:

Todos os tipos e enumeradores V2 devem estar definidos e testados, sem dependência semântica dos tipos V1.

### Fase 2 — Domain Entities

**Objetivo:** implementar as entidades e suas invariantes.

Arquivo principal:

- `framework/core/topology/models.py`

Entidades:

1. Metadata
2. NetworkElement
3. Node
4. Host
5. Switch
6. Router
7. Interface
8. StaticRoute
9. LinkDirection
10. Link
11. Controller
12. ControllerAssociation
13. Policy
14. Metrics

Atividades:

- Implementar as entidades conforme o Domain Model V2.
- Implementar os defaults definidos na especificação.
- Utilizar factories para coleções mutáveis.
- Implementar os tipos IP nativos.
- Separar Controller de Node.
- Implementar interfaces aninhadas em Nodes.
- Implementar rotas estáticas aninhadas em Routers.
- Representar Links por referências a Interfaces.
- Representar direções forward e reverse explicitamente.
- Utilizar estruturas imutáveis onde definidas pelo contrato.

Testes:

- Construção de cada entidade.
- Defaults.
- Campos obrigatórios.
- Restrições de tipos.
- Invariantes individuais.
- Separação entre Router, Host e Switch.
- Ausência de compartilhamento indevido de coleções mutáveis.

Critério de aceite:

Todas as entidades V2 devem estar implementadas e testadas independentemente do agregado.

### Fase 3 — Topology Aggregate

**Objetivo:** implementar o agregado responsável pela organização e integridade da topologia.

Arquivo principal:

- `framework/core/topology/topology.py`

Atividades:

1. Implementar o agregado `Topology`.
2. Incorporar todos os componentes da raiz V2.
3. Implementar acesso e consulta às entidades.
4. Implementar resolução de referências.
5. Implementar verificação de unicidade global dos identificadores.
6. Implementar a associação entre interfaces e seus Nodes proprietários.
7. Implementar `snapshot()`.

O método `snapshot()` deverá produzir uma cópia independente da topologia, preservando:

- Metadata
- Nodes
- Interfaces
- StaticRoutes
- Links
- Controllers
- ControllerAssociations
- Policies
- Metrics

A cópia não poderá compartilhar referências mutáveis com o agregado original.

Testes:

- Construção do agregado.
- Topologias vazias válidas quando estruturalmente permitidas.
- Inserção e consulta de entidades.
- IDs duplicados entre tipos diferentes.
- Resolução de referências.
- Snapshot independente.
- Preservação integral dos componentes durante a cópia.

Critério de aceite:

O agregado deve representar integralmente uma Topology V2 e garantir a unicidade global dos identificadores.

### Fase 4 — Serialization

**Objetivo:** implementar serialização e desserialização exclusivamente no formato V2.

Arquivo principal:

- `framework/core/topology/serialization.py`

Atividades:

1. Definir `SCHEMA_VERSION = 2`.
2. Implementar parser V2.
3. Implementar serializer V2.
4. Implementar conversão dos tipos IP.
5. Implementar conversão de datetime.
6. Aplicar defaults definidos no contrato.
7. Rejeitar campos estruturais desconhecidos.
8. Validar campos obrigatórios.
9. Preservar a ausência de campos opcionais sem defaults.
10. Preservar a ausência de `reverse` e `role` quando não declarados.

Não implementar:

- Parser V1.
- Conversor V1→V2.
- Fallback automático.
- Compatibilidade com estruturas antigas.

Testes:

- JSON V2 válido.
- JSON V2 inválido.
- Campos obrigatórios ausentes.
- Campos desconhecidos.
- Valores enum inválidos.
- Endereços IPv4 e IPv6.
- Rotas IPv4 e IPv6.
- Datas ISO 8601.
- Defaults.
- Serialização canônica.
- Round-trip de serialização e desserialização.

Critério de aceite:

Todos os datasets ativos devem ser serializados e desserializados exclusivamente no formato V2.

### Fase 5 — Validation

**Objetivo:** implementar a validação estrutural e semântica da Topology V2.

Arquivo principal:

- `framework/core/topology/validator.py`

Atividades:

1. Implementar ValidationSeverity.
2. Implementar ValidationIssue.
3. Implementar ValidationReport.
4. Implementar `validate_topology()`.
5. Implementar as quatro camadas:
   - Document Validation.
   - Domain Integrity Validation.
   - Semantic Validation.
   - Report Generation.

6. Implementar as regras de:
   - Unicidade global de IDs.
   - Referências.
   - Nodes.
   - Interfaces.
   - Links.
   - LinkDirections.
   - StaticRoutes.
   - Controllers.
   - ControllerAssociations.
   - Policies.
   - Metrics.

7. Implementar coleta de múltiplos problemas.
8. Reconciliar os códigos de validação com a matriz de testes.
9. Garantir que a validação não modifique a topologia.

A validação de compatibilidade de execução deverá ser implementada separadamente, considerando os contratos dos adapters e das operações.

Testes:

- Casos válidos.
- Casos inválidos.
- Casos WARNING.
- Casos INFO.
- Múltiplos erros simultâneos.
- IDs duplicados entre entidades diferentes.
- Referências inexistentes.
- Validação sem mutação.
- Separação entre validação estrutural e compatibilidade de execução.

Critério de aceite:

O validator deverá produzir relatórios completos e consistentes com a especificação V2.

### Fase 6 — Graph and Path Services

**Objetivo:** adaptar os serviços de grafos e busca de caminhos ao novo modelo.

Arquivos principais:

- `framework/services/path_finder.py`
- `framework/services/validator/path_validator.py`

Atividades:

1. Substituir a adjacência baseada em Nodes pela conectividade baseada em Links e Interfaces.
2. Considerar a direção declarada de cada Link.
3. Considerar o status do Link.
4. Considerar o atributo `enabled` da direção.
5. Permitir identificação de Links paralelos.
6. Implementar PathSegment.
7. Implementar PathResult.
8. Implementar LinkDirectionType.
9. Implementar PathCostMetric.
10. Atualizar a validação dos caminhos.

O resultado deverá preservar:

- source_node_id
- destination_node_id
- nodes
- segments
- cost
- cost_metric

Cada segmento deverá preservar:

- link_id
- from_interface_id
- to_interface_id
- direction

Métricas iniciais:

- HOP_COUNT
- WEIGHT_SUM
- DELAY_SUM

O BFS deverá retornar um caminho estruturado com métrica HOP_COUNT.

Algoritmos ponderados deverão calcular o custo conforme a métrica declarada.

Testes:

- Caminhos simples.
- Caminhos inexistentes.
- Caminho de um único Node.
- Links direcionais.
- Links sem direção reversa.
- Links FAILED e DISABLED.
- Direções desabilitadas.
- Links paralelos.
- Diferentes custos.
- Preservação de interfaces e Links nos resultados.

Critério de aceite:

Os serviços de caminhos devem operar integralmente sobre a Topology V2 e produzir resultados estruturados.

### Fase 7 — Technology Adapters

**Objetivo:** adaptar a integração com as tecnologias de rede.

Arquivos principais:

- `framework/integrations/mininet/adapter.py`
- `framework/services/collector/onos_topology_adapter.py`

#### 7.1 Mininet Adapter

Atividades:

- Mapear Hosts e Switches para Nodes V2.
- Representar interfaces explicitamente.
- Mapear endereços IP para Interfaces.
- Mapear conexões por meio de Links.
- Considerar as limitações do Mininet em relação a direcionalidade.
- Verificar compatibilidade de execução.
- Não utilizar `node.properties` como fonte de endereços IP.

A capacidade de representar parâmetros assimétricos deverá ser verificada por testes específicos.

#### 7.2 ONOS Topology Adapter

Atividades:

- Mapear devices para Nodes.
- Mapear portas para Interfaces.
- Mapear links para Links V2.
- Utilizar IDs de Interfaces nas conexões.
- Preservar informações originais úteis em `attributes`.
- Revisar a semântica do campo ONOS `type`, especialmente `DIRECT`.
- Não inferir automaticamente a existência de uma direção reversa.

Testes:

- Mapeamento de devices.
- Mapeamento de portas.
- Links direcionais.
- Links paralelos.
- Referências de interfaces.
- Preservação de metadados.
- Validação da topologia coletada.

Critério de aceite:

Os adapters devem produzir e consumir estruturas V2 sem depender da representação V1.

### Fase 8 — Experiment Services

**Objetivo:** adaptar os serviços de experimentação ao novo modelo.

Arquivo principal:

- `framework/services/executor/experiment_executor.py`

Atividades:

1. Atualizar ExperimentResult.
2. Substituir caminhos baseados em `list[str]` por PathResult.
3. Substituir cópias manuais da topologia por `Topology.snapshot()`.
4. Preservar todos os componentes do agregado durante experimentos.
5. Adaptar os mecanismos de falha e recuperação.
6. Atualizar os consumidores dos resultados dos experimentos.

Testes:

- Execução de experimentos com topologia V2.
- Preservação do estado original.
- Snapshot independente.
- Resultados de caminhos estruturados.
- Simulação de falhas.
- Recuperação e atualização de métricas.

Critério de aceite:

Os serviços de experimentação deverão operar sobre V2, preservando o estado e a integridade da topologia.

### Fase 9 — Datasets, Tests and Documentation

**Objetivo:** reconstruir os dados ativos, consolidar os testes e atualizar a documentação do framework.

Atividades:

1. Reconstruir os datasets ativos no formato V2.
2. Atualizar os datasets N1 Basic, Redundant e Ring.
3. Atualizar os datasets de referência.
4. Preservar os dados originais RNP.
5. Atualizar a metodologia N1-FR01 para utilizar V2.
6. Atualizar os testes de integração.
7. Atualizar os testes unitários.
8. Atualizar README e documentação de arquitetura.
9. Remover referências operacionais ao modelo V1.
10. Preservar resultados históricos de experimentos V1.

Os dados de origem RNP devem permanecer inalterados. A representação V2 deverá ser construída separadamente, mantendo a rastreabilidade da origem.

Os resultados históricos V1 não devem ser sobrescritos ou apresentados como resultados produzidos pelo modelo V2.

Critério de aceite:

Todos os datasets ativos, testes e documentos operacionais devem utilizar exclusivamente V2.

## 5. Dependências entre fases

A ordem de implementação é:

```text
Fase 1 — Domain Types and Enumerations
        |
        v
Fase 2 — Domain Entities
        |
        v
Fase 3 — Topology Aggregate
        |
        v
Fase 4 — Serialization
        |
        v
Fase 5 — Validation
        |
        v
Fase 6 — Graph and Path Services
        |
        v
Fase 7 — Technology Adapters
        |
        v
Fase 8 — Experiment Services
        |
        v
Fase 9 — Datasets, Tests and Documentation
```

As fases podem compartilhar atividades de revisão e testes, mas nenhuma fase dependente deverá ser considerada concluída antes que seus contratos predecessores estejam estáveis.

## 6. Estratégia de testes

A implementação deverá utilizar testes incrementais.

Cada fase deve:

1. Implementar as funcionalidades previstas.
2. Criar ou atualizar os testes correspondentes.
3. Executar os testes da fase.
4. Executar os testes de regressão relevantes.
5. Revisar os contratos públicos.
6. Registrar o resultado antes de avançar.

Os testes V1 não devem condicionar a implementação V2.

Testes antigos devem ser substituídos por testes que expressem a semântica V2, não por adaptações que preservem estruturas obsoletas.

## 7. Requisitos transversais

### 7.1 Independência do domínio

O pacote `framework.core.topology` não deve importar dependências de Mininet, ONOS ou outras tecnologias de execução.

### 7.2 Gerenciamento de estado

Coleções mutáveis devem utilizar factories apropriadas.

A cópia do agregado deve preservar a independência do estado.

### 7.3 Tratamento de erros

Os erros devem ser distinguíveis conforme sua origem:

- Erros de domínio.
- Erros de serialização.
- Erros de validação.
- Erros de adapter.
- Erros de execução.

### 7.4 Integridade

A unicidade global dos identificadores deve ser preservada.

Referências entre entidades devem ser resolvidas de maneira inequívoca.

### 7.5 Direcionalidade

A direcionalidade deve ser preservada desde a representação do Link até os serviços de caminhos e os adapters.

Nenhum componente deve presumir bidirecionalidade sem declaração explícita.

### 7.6 API pública

O pacote `framework.core.topology` deve disponibilizar exports explícitos e estáveis das entidades, tipos, enums, agregado e interfaces públicas de serialização e validação.

Detalhes internos de implementação não devem ser expostos desnecessariamente.

## 8. Critérios globais de conclusão

A migração para Topology V2 será considerada concluída quando:

1. Todas as entidades V2 estiverem implementadas.
2. O agregado estiver implementado e testado.
3. A unicidade global de IDs estiver garantida.
4. A serialização e desserialização V2 estiverem completas.
5. A validação estiver implementada.
6. PathResult estiver estruturado.
7. Os serviços de caminhos utilizarem Interfaces e Links.
8. Os adapters ONOS e Mininet estiverem atualizados.
9. Os serviços de experimentação utilizarem snapshots.
10. Os datasets ativos estiverem reconstruídos.
11. Os testes estiverem atualizados.
12. A documentação operacional estiver alinhada à V2.
13. Os dados RNP originais e resultados experimentais V1 estiverem preservados.
14. Não houver dependência operacional de estruturas V1.
15. A suíte de testes completa estiver aprovada.

## 9. Controle de alterações

Cada fase deverá ser registrada no histórico Git por meio de alterações isoladas e revisáveis.

Não realizar substituições indiscriminadas de arquivos ou remoções de dados históricos.

Antes de alterações estruturais:

- Revisar os arquivos envolvidos.
- Identificar dependências e consumidores.
- Definir os testes afetados.
- Preservar os dados que não fazem parte da migração.

A conclusão de cada fase deve ser documentada antes do início da próxima.

## 10. Resultado esperado

Ao final da implementação, o framework deverá possuir um modelo de topologia consistente, independente de tecnologia, extensível e adequado para experimentos de Intent-Based Networking orientados por LLMs.

A Topology V2 deverá constituir a representação única utilizada pelos serviços de domínio, validação, caminhos, adapters e experimentação.