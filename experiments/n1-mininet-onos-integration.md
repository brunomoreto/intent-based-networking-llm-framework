# N1 — Integração Mininet–ONOS

## 1. Objetivo

Validar a execução da topologia N1 Redundant Topology no Mininet, sob controle do ONOS, como etapa inicial da avaliação experimental do framework de Intent-Based Networking.

## 2. Ambiente experimental

O ambiente utilizado no experimento foi composto pelos seguintes elementos:

Sistema operacional da VM Mininet: Ubuntu Server 24.04.5.

Python: 3.12.3.

Mininet: 2.3.1b4.

Open vSwitch: 3.3.9.

Controlador SDN: ONOS 2.7.0.

Endereço IP da VM Mininet: 10.145.83.63.

Endereço IP da VM ONOS: 10.145.83.64.

Protocolo de controle: OpenFlow.

Porta OpenFlow: 6653.

## 3. Topologia utilizada

Arquivo de referência: `datasets/n1/redundant_topology.json`.

A topologia contém dois hosts (`h1` e `h2`), quatro switches (`s1`, `s2`, `s3` e `s4`) e seis enlaces:

- `l1`: h1–s1
- `l2`: s1–s2
- `l3`: s1–s3
- `l4`: s2–s4
- `l5`: s3–s4
- `l6`: s4–h2

A existência de caminhos alternativos permite investigar a continuidade da comunicação após falhas de enlace.

## 4. Procedimento executado

1. Verificação do ambiente Mininet, Open vSwitch e Python.
2. Inicialização da topologia por meio do script de integração.
3. Conexão dos switches ao controlador ONOS.
4. Consulta dos dispositivos, enlaces, hosts e fluxos por meio da API REST do ONOS.
5. Execução de ping explícito entre h1 e h2.
6. Execução do teste global `pingAll`.
7. Encerramento da topologia e limpeza do ambiente Mininet.

As aplicações ONOS `org.onosproject.fwd`, `org.onosproject.lldpprovider`, `org.onosproject.hostprovider` e `org.onosproject.proxyarp` estavam ativas.

## 5. Resultados observados

- Os quatro switches foram identificados pelo ONOS como disponíveis e com papel `MASTER`.
- Os quatro enlaces físicos entre switches foram representados por oito registros direcionados na descoberta de enlaces do ONOS.
- Os dois hosts foram descobertos após a geração de tráfego.
- O host h1 utilizou o endereço IP `10.0.0.1`.
- O host h2 utilizou o endereço IP `10.0.0.2`.
- O ONOS instalou fluxos associados ao encaminhamento de tráfego.
- O ping explícito entre h1 e h2 apresentou 3 pacotes transmitidos, 3 recebidos e 0% de perda.
- O `pingAll` apresentou 0% de perda, com 2 de 2 pares de comunicação testados com sucesso.

Foi observado que a primeira execução do `pingAll`, antes do tráfego explícito entre os hosts, apresentou falhas. Após o tráfego inicial, a descoberta dos hosts e a instalação dos fluxos foram observadas, e o teste global foi bem-sucedido. A causa exata da falha inicial ainda não foi isolada.

Também foram exibidos avisos do HTB relacionados ao tamanho do quantum das classes de tráfego. Esses avisos não impediram a conectividade observada.

## 6. Conclusão

A integração básica entre o framework, o Mininet e o ONOS foi validada para a topologia N1. A comunicação entre h1 e h2 foi estabelecida, e o controlador reconheceu os dispositivos, descobriu os hosts e instalou fluxos de encaminhamento.

Esse resultado confirma a operação básica do cenário, mas ainda não demonstra recuperação automática diante de falhas.

## 7. Próximas etapas

1. Repetir o experimento com desativação do enlace `l2` (s1–s2).
2. Verificar a continuidade da comunicação pelo caminho alternativo h1–s1–s3–s4–h2.
3. Registrar tempos de convergência e resultados de conectividade.
4. Investigar a falha observada na primeira execução do `pingAll`.
5. Integrar o cenário de falha ao executor de experimentos e à validação independente do framework.
