# Fase 0 — Dados de entrada e base de dados

## Empresas fictícias

| ID | Empresa | Entra em |
|---|---|---|
| A | Clínica Dentária Sorriso do Minho, Lda | C1 (CSV de clientes), C2 (SAF-T), C3 (tickets) |
| B | Ginásio Movimento Braga, Lda | C1 (CSV de clientes), C3 (tickets) |
| C | TechCávado Informática, Lda | C2 (SAF-T), C3 (tickets) |

## Ficheiros de entrada (`data/input/`)

| Ficheiro | Circuito | Formato | Particularidade |
|---|---|---|---|
| `clientes_clinica_sorriso.csv` | C1 | CSV, separador `;`, colunas em português | Datas de registo `dd/mm/aaaa` |
| `clientes_ginasio_movimento.csv` | C1 | CSV, separador `,`, **colunas em inglês** | Obriga a *schema mapping* para juntar com o da clínica |
| `saft_clinica_sorriso_2026.xml` | C2 | XML SAF-T simplificado | **Válido** no XSD; os clientes existem no CRM (CSV) → o lookup encontra-os |
| `saft_techcavado_2026.xml` | C2 | XML SAF-T simplificado | **Inválido** no XSD (1 data `dd/mm/aaaa`) → ficheiro vai para quarentena; clientes não existem no CRM |
| `tickets_exemplo.json` | C3 | JSON | 63 eventos que o Node-RED publica no MQTT, 1 a cada 5 s |

## Mapa de estragos (`data/expected/mapa_estragos.csv`)

O gerador regista **cada erro que injetou**: ficheiro, registo, campo, tipo de estrago, valor e o que o ETL deve fazer com ele (normalizar, quarentena com motivo X, mascarar…). Serve para:

- **verificar** se os circuitos apanharam tudo (comparar o mapa com `quarentena.registo` e `auditoria.constatacao`);
- **explicar na defesa** que os dados foram estragados de propósito e com que regras;
- a secção *Transformações* do relatório (cada estrago corresponde a uma regex ou regra).

Tipos de estrago nos clientes (C1): NIF com espaços/pontos/`PT`/8 dígitos/letra `O`/vazio; telefone com `+351`, `00351`, `(+351)`, hífens, espaços ou 8 dígitos; e-mail em maiúsculas, com espaços, sem domínio, com `(at)`; código postal sem hífen, com espaço, com 4 ou 6 dígitos; datas `dd/mm/aaaa`, `d-m-aa`, `dd.mm.aaaa` e 31 de fevereiro; nomes em maiúsculas/minúsculas, com espaços a mais ou acentos corrompidos; duplicados exatos e duplicados disfarçados (só detetáveis depois de normalizar o NIF); **dados pessoais escondidos nas observações**, incluindo dados de saúde (RGPD art. 9.º).

Nos tickets (C3): NIF, telefone, e-mail, IBAN, morada, cartão de cidadão e dados de saúde no meio do texto; 2 eventos repetidos; 1 evento sem mensagem.

## Base de dados (`sql/`)

1. `01_criar_estrutura.sql` — cria os schemas `ref`, `controlo`, `raw`, `clean`, `quarentena`, `auditoria`.
2. `02_empresas.sql` — insere as 3 empresas (trocar `O_TEU_EMAIL` primeiro).

Regras que a estrutura garante:

- **`raw` e `quarentena` são só de inserção.** Um trigger bloqueia `UPDATE` e `DELETE` — é a prova técnica de que nada é destruído.
- **`raw` guarda tudo em texto**, por isso nada é rejeitado à entrada; a validação acontece depois.
- **`controlo.v_reconciliacao`** mostra, por lote, se `entrada = válidas + quarentena + duplicadas`.
- **`clean.cliente`** tem `versao`, `data_inicio` e `data_fim` (histórico/temporalidade, compatível com o passo *Dimension lookup/update*).
- **`auditoria.ticket.ticket_id`** é chave primária: um evento MQTT repetido não entra duas vezes.

## Regenerar os dados

```
python scripts/gerar_dados.py
python scripts/gerar_flow_publicador.py
```
A semente é fixa, por isso gera sempre exatamente os mesmos ficheiros.

## Organização do repositório

```
data/input/        ficheiros de entrada (CSV, XML, JSON)
data/expected/     mapa de estragos (o que o ETL deve apanhar)
data/output/       saídas geradas pelos Jobs (não vão para o Git)
transformations/   .ktr — uma pasta por circuito + comum/ (peças reutilizáveis)
jobs/              .kjb — um Job por circuito
sql/               criação da base de dados
xsd/               schema de validação do SAF-T
nodered/           fluxos do Node-RED (publicador de tickets, dashboard)
scripts/           geradores dos dados de teste
logs/              logs das execuções (não vão para o Git)
docs/              relatório, diagramas, decisões, declaração de IA
```
