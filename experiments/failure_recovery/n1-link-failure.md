# N1-FR01 — Experimento de Falha de Enlace e Recuperação de Conectividade

## 1. Identificação do experimento

| Campo | Descrição |
|---|---|
| Identificador | N1-FR01 |
| Nome | Link Failure and Connectivity Recovery |
| Topologia | N1 — Redundant Topology |
| Ambiente de emulação | Mininet 2.3.1b4 |
| Controlador SDN | ONOS 2.7.0 |
| Protocolo de comunicação | OpenFlow 1.3 |
| Enlace submetido à falha | l2 (s1–s2) |
| Caminho alternativo | h1–s1–s3–s4–h2 |
| Script | `test_n1_link_failure.py` |

## 2. Objetivo

Avaliar o comportamento da rede diante da interrupção de um enlace pertencente ao caminho principal de comunicação, verificando a capacidade do controlador SDN de detectar a alteração da topologia e manter ou restabelecer a conectividade entre os dispositivos finais por meio de um caminho alternativo.

O experimento também busca coletar evidências do comportamento do plano de controle e do plano de dados, permitindo verificar se o tráfego efetivamente utiliza a rota alternativa após a falha.

## 3. Topologia experimental

O experimento utiliza a topologia N1 — Redundant Topology, composta por dois hosts e quatro switches.

### 3.1. Estrutura

```text
             s1 -------- s2
            /              \
          h1                s4 ---- h2
            \              /
             s3 ----------
```

### 3.2. Componentes

- Hosts: h1 e h2.
- Switches: s1, s2, s3 e s4.
- Enlaces:
  - l1: h1–s1
  - l2: s1–s2
  - l3: s1–s3
  - l4: s2–s4
  - l5: s3–s4
  - l6: s4–h2

### 3.3. Caminhos de comunicação

**Caminho principal:**

```text
h1 → s1 → s2 → s4 → h2
```

**Caminho alternativo:**

```text
h1 → s1 → s3 → s4 → h2
```

O enlace l2 (s1–s2) foi escolhido como alvo da falha por integrar o caminho principal e permitir a utilização da rota alternativa sem desconectar os hosts da infraestrutura.

## 4. Hipótese experimental

Após a interrupção do enlace l2, a rede deverá restabelecer a conectividade entre h1 e h2 utilizando o caminho alternativo, sem intervenção manual na configuração dos fluxos de encaminhamento.

A hipótese será avaliada considerando três aspectos independentes:

1. Detecção da indisponibilidade do enlace pelo controlador ONOS.
2. Continuidade ou recuperação da conectividade entre os hosts.
3. Utilização efetiva do caminho alternativo no plano de dados.

## 5. Ambiente e configuração

A topologia foi construída por meio do Mininet e conectada remotamente ao controlador ONOS.

Parâmetros de integração:

| Parâmetro | Valor |
|---|---|
| Controlador | ONOS |
| Endereço do controlador | 10.145.83.64 |
| Porta OpenFlow | 6653 |
| Versão OpenFlow | 1.3 |
| API REST | 8181 |
| Aplicação de encaminhamento | org.onosproject.fwd |

As aplicações ONOS utilizadas no ambiente incluem:

- `org.onosproject.fwd`
- `org.onosproject.lldpprovider`
- `org.onosproject.hostprovider`
- `org.onosproject.proxyarp`

## 6. Metodologia

O experimento foi executado por meio do script:

```text
experiments/failure_recovery/test_n1_link_failure.py
```

A execução foi organizada nas seguintes etapas.

### 6.1. Inicialização

O script carrega a definição da topologia N1, constrói a rede no Mininet e estabelece a conexão dos switches com o controlador ONOS.

### 6.2. Verificação inicial

Antes da injeção da falha, é verificada a conectividade entre h1 e h2 por meio de mensagens ICMP.

O teste inicial apresentou conectividade sem perda de pacotes.

### 6.3. Monitoramento pré-falha

Foi realizada uma sequência de dez verificações de conectividade, com intervalo aproximado de um segundo entre as sondagens.

Todas as dez verificações foram bem-sucedidas.

### 6.4. Injeção da falha

A interrupção foi realizada por meio da API de configuração de enlaces do Mininet:

```python
net.configLinkStatus("s1", "s2", "down")
```

O instante da injeção foi registrado utilizando `time.monotonic()`.

Após a interrupção, o script aguardou um período fixo de 20 segundos antes de iniciar o monitoramento pós-falha.

### 6.5. Monitoramento pós-falha

Após o período de espera, foi iniciado o monitoramento da conectividade entre h1 e h2 durante 40 segundos.

As sondagens ICMP foram utilizadas para verificar a disponibilidade da comunicação.

### 6.6. Verificação do plano de controle

Durante a execução, a API REST do ONOS foi consultada para acompanhar a situação dos enlaces.

A consulta utilizada foi:

```bash
curl -s -u onos:rocks \
http://10.145.83.64:8181/onos/v1/links
```

Também foram consultados os fluxos instalados no controlador:

```bash
curl -s -u onos:rocks \
http://10.145.83.64:8181/onos/v1/flows
```

### 6.7. Verificação do plano de dados

Os fluxos instalados diretamente no Open vSwitch foram consultados utilizando:

```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s3
```

Essa consulta permitiu verificar as regras de encaminhamento e seus respectivos contadores de pacotes e bytes.

## 7. Resultados experimentais

### 7.1. Conectividade inicial

O teste de conectividade inicial foi aprovado.

- Comunicação entre h1 e h2 estabelecida.
- Perda de pacotes: 0%.
- Dez verificações pré-falha concluídas com sucesso.

### 7.2. Detecção da falha pelo ONOS

Antes da interrupção, a API REST do ONOS apresentava os oito registros direcionais correspondentes aos quatro enlaces bidirecionais entre switches.

Após a falha de l2, os registros correspondentes às direções:

```text
s1 → s2
s2 → s1
```

deixaram de aparecer na consulta da topologia.

Os demais enlaces permaneceram ativos:

```text
s1 ↔ s3
s2 ↔ s4
s3 ↔ s4
```

Esse comportamento constitui evidência de que o controlador identificou a alteração da topologia após a interrupção do enlace.

Não foi possível determinar o tempo exato de detecção, pois os registros de consulta da API REST e os timestamps monotônicos do script não estavam sincronizados.

### 7.3. Recuperação da conectividade

O resultado do monitoramento pós-falha foi:

| Métrica | Resultado |
|---|---:|
| Duração da espera após a falha | 20 segundos |
| Duração do monitoramento posterior | 40 segundos |
| Sondagens bem-sucedidas | 39 |
| Conectividade observada | Restabelecida |
| Perda observada durante o monitoramento | 0% |

A primeira sondagem bem-sucedida ocorreu aproximadamente 20 segundos após a injeção da falha, conforme o registro apresentado pelo script.

Entretanto, esse valor não representa o tempo real de recuperação da rede. Como o script permaneceu 20 segundos sem executar sondagens ICMP após a falha, não foi possível identificar o instante exato em que a conectividade voltou a funcionar.

O resultado demonstra que a comunicação estava disponível na primeira sondagem realizada após o período de espera e permaneceu disponível durante a janela de monitoramento de 40 segundos.

### 7.4. Evidências dos fluxos no ONOS

A consulta à API REST de fluxos identificou regras da aplicação `org.onosproject.fwd` nos switches s1, s3 e s4.

As regras apresentaram encaminhamento nos dois sentidos:

| Switch | Direção | Porta de entrada | Porta de saída |
|---|---|---|---|
| s1 | h1 → h2 | 1 | 3 |
| s3 | h1 → h2 | 1 | 2 |
| s4 | h1 → h2 | 2 | 3 |
| s4 | h2 → h1 | 3 | 2 |
| s3 | h2 → h1 | 2 | 1 |
| s1 | h2 → h1 | 3 | 1 |

Os identificadores dos dispositivos OpenFlow foram associados aos switches da topologia:

| Switch | Device ID |
|---|---|
| s1 | of:0000000000000001 |
| s2 | of:0000000000000002 |
| s3 | of:0000000000000003 |
| s4 | of:0000000000000004 |

Os seis fluxos de encaminhamento identificados apresentaram 35 pacotes e 3430 bytes cada no momento da consulta.

Não foram identificadas regras de encaminhamento host-to-host da aplicação `org.onosproject.fwd` em s2 na captura analisada.

Essas observações são compatíveis com a utilização do caminho alternativo:

```text
h1 → s1 → s3 → s4 → h2
```

e com o caminho inverso para o tráfego de retorno.

### 7.5. Evidências no Open vSwitch

A inspeção direta do switch s3 confirmou a existência de duas regras de encaminhamento:

**Sentido h1 → h2:**

```text
in_port="s3-eth1"
dl_src=00:00:00:00:00:01
dl_dst=00:00:00:00:00:02
actions=output:"s3-eth2"
```

**Sentido h2 → h1:**

```text
in_port="s3-eth2"
dl_src=00:00:00:00:00:02
dl_dst=00:00:00:00:00:01
actions=output:"s3-eth1"
```

Os contadores das regras apresentaram a seguinte evolução nas três capturas:

| Captura | h1 → h2 | h2 → h1 |
|---|---:|---:|
| Primeira | 0 pacotes | 0 pacotes |
| Segunda | 15 pacotes | 15 pacotes |
| Terceira | 1 pacote | 1 pacote |

Na terceira captura, as regras apresentavam aproximadamente dois segundos de duração, indicando que as regras anteriores haviam sido substituídas ou expirado e novas regras estavam presentes.

A existência de contadores positivos nas regras de encaminhamento constitui evidência de que o tráfego foi efetivamente processado pelo switch s3 nos dois sentidos.

## 8. Análise dos resultados

Os resultados demonstram três comportamentos relevantes.

Primeiramente, a interrupção do enlace principal foi refletida na topologia apresentada pelo controlador ONOS, que deixou de apresentar os registros direcionais correspondentes ao enlace l2.

Em segundo lugar, a conectividade entre h1 e h2 foi observada na primeira sondagem realizada após o período de espera de 20 segundos e permaneceu disponível durante o monitoramento posterior.

Por fim, as consultas aos fluxos do ONOS e aos contadores do Open vSwitch forneceram evidências de encaminhamento pelo caminho alternativo, envolvendo s1, s3 e s4.

A combinação dessas observações é mais robusta do que avaliar exclusivamente a conectividade ICMP, pois permite analisar tanto o comportamento do controlador quanto a utilização efetiva dos recursos de encaminhamento da rede.

## 9. Limitações da primeira implementação

A primeira implementação apresentou uma limitação importante na medição temporal da recuperação.

Após a injeção da falha, o script executou uma espera fixa de 20 segundos antes de iniciar as sondagens ICMP.

Consequentemente:

- Não houve monitoramento da conectividade durante os primeiros 20 segundos após a falha.
- Não foi possível determinar o instante exato da recuperação.
- O tempo registrado corresponde ao intervalo até a primeira observação de conectividade após a espera, e não ao tempo efetivo de recuperação.
- Os registros temporais da API REST do ONOS não foram sincronizados com o relógio monotônico utilizado pelo script.
- As capturas de fluxos foram realizadas em momentos distintos e não permitem determinar, isoladamente, o instante exato de instalação das regras após a falha.

Essas limitações devem ser consideradas na interpretação dos resultados.

## 10. Conclusão

O experimento N1-FR01 apresentou evidências positivas de detecção da falha do enlace principal e de utilização do caminho alternativo para manter ou restabelecer a comunicação entre h1 e h2.

A remoção do enlace l2 da topologia apresentada pelo ONOS demonstrou a identificação da alteração topológica. As sondagens ICMP confirmaram a disponibilidade da comunicação durante a janela observada após a falha. Adicionalmente, os fluxos identificados no controlador e os contadores do Open vSwitch em s3 forneceram evidências de encaminhamento pelo caminho alternativo.

Portanto, os resultados são compatíveis com a hipótese experimental de recuperação da conectividade por meio da rota redundante.

Entretanto, a primeira implementação não permite determinar com precisão o tempo de recuperação, devido à ausência de sondagem contínua imediatamente após a injeção da falha.

## 11. Próxima implementação

A próxima versão do experimento deverá corrigir a limitação temporal identificada.

As melhorias previstas são:

1. Executar sondagens ICMP contínuas antes e depois da injeção da falha.
2. Registrar o instante exato da interrupção utilizando relógio monotônico.
3. Identificar a primeira sondagem bem-sucedida após a falha.
4. Calcular o tempo de recuperação com base nos timestamps das sondagens.
5. Registrar individualmente os pacotes enviados, recebidos e perdidos.
6. Correlacionar, quando possível, os eventos de conectividade com as alterações observadas no ONOS e nos fluxos do Open vSwitch.

Essa evolução permitirá uma avaliação temporal mais precisa e facilitará a comparação entre diferentes cenários de falha e recuperação.

---

**Identificação da versão:** N1-FR01 — Primeira implementação experimental.

**Script associado:** `test_n1_link_failure.py`.