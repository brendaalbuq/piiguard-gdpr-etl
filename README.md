# PiiGuard — Auditoria e Anonimização de Dados Pessoais (RGPD) em Sistemas Empresariais Heterogéneos

**Trabalho Prático I — Integração de Sistemas de Informação (ISI)**
Licenciatura em Engenharia de Sistemas Informáticos (LESI-PL) — Escola Superior de Tecnologia, Universidade Politécnica do Cávado e do Ave (UPCA) — 2026/27
Docentes: Luís Ferreira e Óscar Ribeiro

| | |
|---|---|
| **Autora** | Brenda Santos de Albuquerque |
| **N.º de aluna** | 27209 |
| **Repositório** | https://github.com/brendaalbuq/piiguard-gdpr-etl |
| **Vídeo de demonstração** | [https://youtu.be/wKUmVtxbm-M](https://youtu.be/wKUmVtxbm-M) |

---

## 1. O que o projeto faz

Três empresas fictícias — uma clínica dentária, um ginásio e uma loja de informática — enviam dados em formatos e estruturas que não combinam entre si. O PiiGuard, construído em **Pentaho Data Integration (Kettle) 9.4**, recolhe esses dados, **limpa e normaliza com expressões regulares**, **põe de lado o que é inválido sem apagar nada**, **pseudonimiza e mascara dados pessoais**, **audita uma amostra de 10–20 % dos registos de cada empresa** e **avisa cada uma por email do que encontrou**. Os alertas em tempo real aparecem num **dashboard Node-RED**.

Há **três circuitos**, e cada um tem fonte, problema, operadores e destino próprios:

| | **C1 — Clientes** | **C2 — Faturas SAF-T** | **C3 — Tickets de suporte** |
|---|---|---|---|
| **Fonte / formato** | 2 ficheiros CSV com estruturas diferentes | 2 ficheiros XML (SAF-T simplificado) + PostgreSQL | Mensagens JSON via MQTT (Mosquitto) |
| **Modo** | Síncrono, por lote | Síncrono, por lote | **Assíncrono, por evento** |
| **Operadores principais** | Schema mapping, 9 regex de normalização, Data Validator, SHA-256, Mapping (sub-transformação), Sort + Unique, controlo por lote e transação | XSD, XPath, Stream lookup, Database lookup, Filter, Group by, JSON/XML output, XSLT, ZIP, Mail opcional | MQTT Consumer/Producer, JSON input, regex de deteção, amostragem aleatória, Mail por empresa |
| **Destino** | `raw` → `clean` + `quarentena` (PostgreSQL) | JSON/XML anonimizados, relatório HTML, ZIP, email | Base de auditoria, dashboard em tempo real, email a cada empresa |

**Princípios comuns aos três circuitos**

- **Não destruir dados:** o original fica sempre em `raw`, uma tabela só de inserção protegida por trigger. O que é rejeitado vai para `quarentena.registo`, com o **motivo**. Um XML inválido é copiado para `data/quarantine`.
- **Dizer para onde foram os dados:** cada lote é reconciliado — `entrada = válidos + quarentena + duplicados` — e, se a conta não fechar, o Job falha.
- **Temporalidade:** os lotes (`controlo.lote`), o log (`controlo.etl_log`), o histórico de auditorias e as notificações têm todos data.
- **Reutilização:** transformações pequenas, orquestradas por Jobs. As peças comuns (`dataintegration/transformations/comum`) servem vários circuitos.

O processamento é feito por lotes. Primeiro grava-se o `raw`, numa transformação própria, e dali em diante ele fica intocado. A carga de `clean` e `quarentena` (`c1_02`) é uma única transação: se um passo falhar, nenhuma das duas tabelas fica com dados desse lote (o rollback foi testado) e o lote passa a `FALHOU`. No fim, a reconciliação confere os destinos do lote.

---

## 2. Estrutura dos ficheiros

```
tp01-27209/
├── README.md                         este ficheiro
├── doc/
│   └── 27209_doc.pdf                 relatório final (PDF, com o QR Code do vídeo no capítulo 6)
├── dataintegration/
│   ├── jobs/                         Jobs (.kjb) — um por circuito
│   │   ├── c1_clientes.kjb
│   │   ├── c2_faturas.kjb
│   │   ├── c3_receber_tickets.kjb
│   │   └── c3_auditoria.kjb
│   └── transformations/              Transformações (.ktr)
│       ├── comum/                    peças reutilizáveis
│       │   ├── abrir_lote.ktr        cria o lote e a variável LOTE_ID
│       │   ├── fechar_lote.ktr       reconciliação do lote
│       │   ├── registar_log.ktr      log de execução
│       │   └── mascarar_pii.ktr      sub-transformação (Mapping) de deteção/mascaramento de PII
│       ├── c1_clientes/              c1_01_extrair.ktr, c1_02_validar_carregar.ktr
│       ├── c2_faturas/               c2_01_ler_saft.ktr, c2_02_exportar.ktr, c2_03_resumo_auditoria.ktr
│       └── c3_tickets/               c3_01_receber_mqtt.ktr, c3_01b_processar_ticket.ktr,
│                                     c3_02_auditar_amostra.ktr, c3_03_notificar.ktr
├── data/
│   ├── input/                        dados de entrada (fictícios, estragados de propósito)
│   ├── expected/mapa_estragos.csv    cada erro injetado e o que o ETL deve fazer com ele
│   ├── output/                       exemplos das saídas (JSON, XML, HTML, ZIP)
│   └── quarantine/                   ficheiros rejeitados (XML que falhou o XSD)
└── src/
    ├── sql/                          01_criar_estrutura.sql (base nova), 02_empresas.sql,
    │                                 03_migrar_sem_perda.sql (base existente), 04_verificar_resultados.sql
    ├── xsd/saft_simplificado.xsd     validação do SAF-T
    ├── xsl/relatorio_auditoria.xsl   XML -> HTML do relatório
    ├── nodered/                      flow_publicador_tickets.json, flow_dashboard_alertas.json
    ├── scripts/                      geradores dos dados de teste e dos fluxos Node-RED (Python)
    └── kettle.properties.exemplo     variáveis a configurar
```

---

## 3. Ferramentas necessárias

| Ferramenta | Versão usada | Para quê |
|---|---|---|
| Java (OpenJDK) | 11 | Executar o Pentaho |
| Pentaho Data Integration (Spoon / Kitchen) | 9.4.0.0-343 CE | Transformações e Jobs |
| PostgreSQL + pgAdmin | 18 | Base de dados `piiguard` |
| Mosquitto | 2.x | Broker MQTT (localhost:1883) |
| Node.js + Node-RED + node-red-dashboard | Node 24.22 / Node-RED 5.0.8 / Dashboard 3.6.6 | Publicador de tickets e dashboard |
| Conta Gmail com palavra-passe de aplicação | — | Envio de emails (opcional) |
| Python 3 | 3.x | Só para regenerar os dados de teste (opcional) |

---

## 4. Configuração (uma vez)

1. **Variáveis do Pentaho.** Copiar o conteúdo de `src/kettle.properties.exemplo` para `C:\Users\<utilizador>\.kettle\kettle.properties` e preencher os valores: a password da BD, o email e a palavra-passe de aplicação, e o `PROJ_DIR`, que aponta para a pasta deste projeto e leva barras `/`. Reiniciar o Spoon. As passwords nunca ficam nos ficheiros `.ktr`/`.kjb`, que usam `${DB_PASS}`, `${SMTP_PASS}` e afins.
2. **Base de dados.** Numa base nova e vazia, correr `src/sql/01_criar_estrutura.sql` e `src/sql/02_empresas.sql`. Numa base que já existe, fazer primeiro um backup e executar `src/sql/03_migrar_sem_perda.sql`; o script de estrutura não se volta a correr numa base já inicializada. Antes de ativar os emails, confirmar e atualizar os endereços de notificação.
3. **Mosquitto.** Instalar e arrancar o serviço (`net start mosquitto`).
4. **Node-RED.** Arrancar com `node-red`, abrir http://localhost:1880 e importar os dois fluxos de `src/nodered/` se ainda não estiverem lá. Se o nó de dashboard não aparecer, instalar `node-red-dashboard`; depois, clicar em **Implementar**. A página visual fica em http://localhost:1880/ui.

---

## 5. Como executar

Há duas maneiras: pelo **Spoon** (abrir o Job e carregar em ▶ Run) ou pela linha de comandos, com o **Kitchen**, a partir da pasta `data-integration` do Pentaho:

```bat
set P=C:\Users\Brenda\Documents\piiguard-gdpr-etl\dataintegration\jobs

REM 1) Circuito 1 — clientes (CSV -> raw -> clean/quarentena)
Kitchen.bat /file:"%P%\c1_clientes.kjb" /level:Basic

REM 2) Circuito 2 — faturas SAF-T (XSD, XPath, exportação, relatório HTML, ZIP, email opcional)
Kitchen.bat /file:"%P%\c2_faturas.kjb" /level:Basic /param:"ENVIAR_EMAIL=N"

REM 3) Circuito 3 — receber tickets em tempo real (fica a correr; parar com Ctrl+C / Stop)
Kitchen.bat /file:"%P%\c3_receber_tickets.kjb" /level:Basic
REM    ...e no Node-RED clicar no botão do nó "a cada 5 s" do fluxo "PiiGuard - Publicador de tickets".
REM    Dashboard: http://localhost:1880/ui

REM 4) Circuito 3 — auditoria por amostragem e notificação das empresas
Kitchen.bat /file:"%P%\c3_auditoria.kjb" /level:Basic /param:"PCT=15" /param:"ENVIAR_EMAIL=N"
```

**Parâmetros**

| Job | Parâmetro | Valor por omissão | Efeito |
|---|---|---|---|
| c2_faturas, c3_auditoria | `ENVIAR_EMAIL` | `N` | `S` envia os emails; `N` deixa as notificações `PENDENTE`. Só ativar após confirmar os destinatários e testar o SMTP. |
| c3_auditoria | `PCT` | `15` | Percentagem de registos de cada empresa sorteados para auditoria (10 a 20) |

Numa instalação existente, o caminho é backup e `03_migrar_sem_perda.sql`. O script de arranque recusa schemas que já existem, justamente para não apagar nem recriar dados.

Para uma demonstração a partir do zero (por exemplo, antes de gravar o vídeo), criar uma base nova no pgAdmin (*Create > Database*, digamos `piiguard_demo`), correr nela `01_criar_estrutura.sql` e `02_empresas.sql` e mudar `DB_NAME` no `kettle.properties`. A base antiga não é tocada.

Na máquina onde o projeto foi desenvolvido, a base `piiguard` já tem execuções de validação (lotes repetidos e tentativas antigas em `FALHOU`), por isso os totais acumulados não batem com os do relatório. Para gravar o vídeo com números limpos, usa-se a base nova `piiguard_demo`. O script de estrutura não se volta a correr na `piiguard`.

---

## 6. Para onde vão os dados

| Origem | Destino quando está bem | Destino quando está mal |
|---|---|---|
| CSV de clientes | `raw.cliente` (tal como chegou) → `clean.cliente` (normalizado, NIF com hash, observações mascaradas) | `quarentena.registo` com motivo (NIF_INVALIDO, EMAIL_INVALIDO, TELEFONE_INVALIDO, CP_INVALIDO, DATA_INVALIDA, CAMPO_OBRIGATORIO_NULO, DUPLICADO) |
| XML SAF-T | `clean.fatura` (NIF do cliente só em hash) + `data/output/faturas_anonimizadas_loteN.json/.xml` + `totais_por_mes_loteN.json` | Ficheiro copiado para `data/quarantine/` + linha XSD_INVALIDO em `quarentena.registo` |
| Tickets MQTT | `raw.ticket` (mensagem original) → `auditoria.ticket` (mensagem mascarada) → alerta em `piiguard/alertas` → dashboard | `quarentena.registo` (CAMPO_OBRIGATORIO_NULO, EVENTO_REPETIDO) |
| Auditoria | `auditoria.execucao`, `auditoria.amostra`, `auditoria.constatacao`, `auditoria.notificacao` → email a cada empresa | Notificação fica `FALHOU` e é tentada de novo (até 3 vezes) |
| Controlo | `controlo.lote` (reconciliação) e `controlo.etl_log` | — |

**Consultas úteis para verificar**

```sql
SELECT * FROM controlo.v_reconciliacao;                         -- a conta fecha?
SELECT motivo_codigo, count(*) FROM quarentena.registo GROUP BY 1;
SELECT * FROM auditoria.v_resumo_empresa;
SELECT * FROM controlo.etl_log ORDER BY log_id;
SELECT * FROM auditoria.v_execucao_resumo;                      -- % pedida vs % observada
-- mais consultas em src/sql/04_verificar_resultados.sql
```

---

## 7. Dados de teste

Todos os dados são **fictícios** e saem de `src/scripts/gerar_dados.py`, com semente fixa, por isso os ficheiros são sempre os mesmos. Os erros foram injetados de propósito e cada um está em `data/expected/mapa_estragos.csv`, com o resultado que o ETL deve produzir. Foi com este mapa que se conferiram os resultados dos circuitos.

---

## 8. Declaração de uso de IA

Foram usados os assistentes Claude (Anthropic) e Codex (OpenAI) como apoio: discussão do desenho dos circuitos, geração dos dados fictícios, do script SQL, do XSD/XSL e dos fluxos Node-RED, apoio na construção das transformações e dos Jobs, revisão e melhorias (migração sem perda, amostragem rastreável), testes e revisão do relatório. O detalhe — para quê, quando e os prompts principais — está no Anexo A do relatório. A redação final do relatório e deste README foi reescrita com o Claude a 22 de outubro de 2026, sem alterar factos nem números.
