-- Estrutura da base piiguard (PostgreSQL).
-- Só para uma base vazia: se os schemas já existirem, o script pára e não apaga nada.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_namespace
        WHERE nspname = ANY (ARRAY['auditoria','quarentena','clean','raw','controlo','ref'])
    ) THEN
        RAISE EXCEPTION 'Schemas PiiGuard já existem. Este bootstrap não apaga dados; use uma base piiguard vazia ou faça backup/migração explícita.';
    END IF;
END $$;

CREATE SCHEMA ref;         -- empresas e motivos de rejeição
CREATE SCHEMA controlo;    -- lotes, reconciliação e log
CREATE SCHEMA raw;         -- dados como chegaram, tudo em texto, só insert
CREATE SCHEMA clean;       -- dados normalizados e válidos, com histórico
CREATE SCHEMA quarentena;  -- rejeitados, com o motivo, só insert
CREATE SCHEMA auditoria;   -- tickets mascarados, amostras, constatações, notificações

-- ref
CREATE TABLE ref.empresa (
    empresa_id      CHAR(1) PRIMARY KEY,
    nome            VARCHAR(120) NOT NULL,
    nif             CHAR(9),
    email_contacto  VARCHAR(150) NOT NULL       -- para onde vai a notificação
);

CREATE TABLE ref.motivo_rejeicao (
    codigo      VARCHAR(30) PRIMARY KEY,
    descricao   VARCHAR(200) NOT NULL
);

INSERT INTO ref.motivo_rejeicao VALUES
 ('NIF_INVALIDO',              'NIF não tem 9 dígitos depois de limpo'),
 ('EMAIL_INVALIDO',            'Email não respeita o formato nome@dominio.ext'),
 ('TELEFONE_INVALIDO',         'Telefone não tem 9 dígitos (com ou sem +351)'),
 ('CP_INVALIDO',               'Código postal não respeita 0000-000'),
 ('DATA_INVALIDA',             'Data impossível ou em formato desconhecido'),
 ('CAMPO_OBRIGATORIO_NULO',    'Campo obrigatório vazio'),
 ('DUPLICADO',                 'Registo repetido (mesma empresa + mesmo NIF)'),
 ('XSD_INVALIDO',              'Ficheiro XML não valida contra o XSD'),
 ('EVENTO_REPETIDO',           'Evento MQTT já recebido anteriormente');

-- controlo: lotes (reconciliação) e log
CREATE TABLE controlo.lote (
    lote_id             BIGSERIAL PRIMARY KEY,
    circuito            VARCHAR(10)  NOT NULL,      -- C1, C2, C3
    ficheiro_origem     VARCHAR(200),
    inicio              TIMESTAMP    NOT NULL DEFAULT now(),
    fim                 TIMESTAMP,
    estado              VARCHAR(15)  NOT NULL DEFAULT 'EM_CURSO', -- EM_CURSO / SUCESSO / FALHOU
    linhas_entrada      INT,
    linhas_validas      INT,
    linhas_quarentena   INT,
    linhas_duplicadas   INT
);

-- A conta tem de fechar: entrada = válidas + quarentena + duplicadas
CREATE VIEW controlo.v_reconciliacao AS
SELECT lote_id, circuito, ficheiro_origem, inicio, estado,
       linhas_entrada,
       linhas_validas, linhas_quarentena, linhas_duplicadas,
       COALESCE(linhas_validas,0) + COALESCE(linhas_quarentena,0) + COALESCE(linhas_duplicadas,0) AS soma_destinos,
       linhas_entrada = COALESCE(linhas_validas,0) + COALESCE(linhas_quarentena,0) + COALESCE(linhas_duplicadas,0) AS conta_fecha
FROM controlo.lote;

CREATE TABLE controlo.etl_log (
    log_id      BIGSERIAL PRIMARY KEY,
    lote_id     BIGINT REFERENCES controlo.lote(lote_id),
    circuito    VARCHAR(10),
    passo       VARCHAR(100),
    nivel       VARCHAR(10) DEFAULT 'INFO',  -- INFO / AVISO / ERRO
    mensagem    TEXT,
    registado_em TIMESTAMP DEFAULT now()
);

-- Tabelas só de inserção: qualquer UPDATE/DELETE é recusado
CREATE OR REPLACE FUNCTION controlo.bloquear_alteracao() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Tabela %.% é só de inserção: % não é permitido (política de não destruição de dados)',
        TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP;
END;
$$ LANGUAGE plpgsql;

-- raw: tudo em TEXT para nunca rejeitar nada à entrada
CREATE TABLE raw.cliente (
    raw_id            BIGSERIAL PRIMARY KEY,
    lote_id           BIGINT REFERENCES controlo.lote(lote_id),
    empresa_id        CHAR(1),
    ficheiro_origem   VARCHAR(200),
    linha_origem      INT,
    id_cliente        TEXT,
    nome              TEXT,
    nif               TEXT,
    email             TEXT,
    telefone          TEXT,
    codigo_postal     TEXT,
    data_nascimento   TEXT,
    data_registo      TEXT,
    observacoes       TEXT,
    carregado_em      TIMESTAMP DEFAULT now()
);
CREATE TRIGGER trg_raw_cliente_so_insert BEFORE UPDATE OR DELETE ON raw.cliente
    FOR EACH ROW EXECUTE FUNCTION controlo.bloquear_alteracao();

CREATE TABLE raw.ticket (
    raw_id          BIGSERIAL PRIMARY KEY,
    topico_mqtt     VARCHAR(100),
    payload         TEXT,                   -- mensagem MQTT original
    recebido_em     TIMESTAMP DEFAULT now()
);
CREATE TRIGGER trg_raw_ticket_so_insert BEFORE UPDATE OR DELETE ON raw.ticket
    FOR EACH ROW EXECUTE FUNCTION controlo.bloquear_alteracao();

-- clean: clientes normalizados com histórico de versões
-- (versao/data_inicio/data_fim compatíveis com o "Dimension lookup/update" do Pentaho)
CREATE TABLE clean.cliente (
    cliente_sk        BIGSERIAL PRIMARY KEY,
    versao            INT DEFAULT 1,
    data_inicio       TIMESTAMP DEFAULT now(),
    data_fim          TIMESTAMP,
    empresa_id        CHAR(1),
    id_cliente_origem VARCHAR(20),
    raw_id            BIGINT,                -- de onde veio (rastreabilidade)
    lote_id           BIGINT,
    primeiro_nome     VARCHAR(60),
    apelidos          VARCHAR(120),
    nome_completo     VARCHAR(180),
    nif               CHAR(9),
    nif_hash          CHAR(64),              -- SHA-256: pseudónimo usado nas exportações
    email             VARCHAR(150),
    telefone          VARCHAR(13),           -- formato +351XXXXXXXXX
    codigo_postal     CHAR(8),
    data_nascimento   DATE,
    data_registo      DATE,
    observacoes_mascaradas TEXT,             -- observações com PII substituída por [NIF], [TELEFONE]...
    tem_pii_em_observacoes BOOLEAN,
    tipos_pii         VARCHAR(100),          -- tipos de PII encontrados nas observações
    gravidade         VARCHAR(10)            -- ALTA / MEDIA / BAIXA
);
CREATE INDEX ix_clean_cliente_nif ON clean.cliente(nif);

-- Faturas (Circuito 2) já pseudonimizadas
CREATE TABLE clean.fatura (
    fatura_id         BIGSERIAL PRIMARY KEY,
    lote_id           BIGINT,
    empresa_id        CHAR(1),
    ficheiro_origem   VARCHAR(200),
    invoice_no        VARCHAR(30),
    invoice_date      DATE,
    cliente_nif_hash  CHAR(64),
    cliente_sk        BIGINT,                -- NULL se o cliente não existir no CRM
    cidade            VARCHAR(80),
    net_total         NUMERIC(12,2),
    tax_payable       NUMERIC(12,2),
    gross_total       NUMERIC(12,2)
);

-- quarentena: o que não passou, sempre com o motivo
CREATE TABLE quarentena.registo (
    quarentena_id     BIGSERIAL PRIMARY KEY,
    lote_id           BIGINT REFERENCES controlo.lote(lote_id),
    circuito          VARCHAR(10),
    origem            VARCHAR(200),          -- ficheiro ou tópico
    chave_origem      VARCHAR(60),           -- id do registo na origem / raw_id
    campo             VARCHAR(60),
    valor_original    TEXT,
    motivo_codigo     VARCHAR(30) REFERENCES ref.motivo_rejeicao(codigo),
    registo_completo  TEXT,                  -- linha inteira, para poder reprocessar
    enviado_em        TIMESTAMP DEFAULT now()
);
CREATE TRIGGER trg_quarentena_so_insert BEFORE UPDATE OR DELETE ON quarentena.registo
    FOR EACH ROW EXECUTE FUNCTION controlo.bloquear_alteracao();

-- auditoria (Circuito 3 + constatações dos outros)
CREATE TABLE auditoria.ticket (
    ticket_id           VARCHAR(20) PRIMARY KEY,   -- PK impede o evento repetido
    empresa_id          CHAR(1),
    canal               VARCHAR(30),
    assunto             VARCHAR(80),
    mensagem_mascarada  TEXT,
    tipos_pii           VARCHAR(100),              -- ex: NIF,TELEFONE
    tem_pii             BOOLEAN,
    gravidade           VARCHAR(10),
    recebido_em         TIMESTAMP DEFAULT now()
);

CREATE TABLE auditoria.execucao (
    auditoria_id      BIGSERIAL PRIMARY KEY,
    empresa_id        CHAR(1) REFERENCES ref.empresa(empresa_id),
    executada_em      TIMESTAMP DEFAULT now(),
    percentagem_amostra INT NOT NULL CHECK (percentagem_amostra BETWEEN 10 AND 20), -- limite da amostra
    total_registos    INT,
    registos_amostra  INT,
    percentagem_observada NUMERIC(5,2),
    total_constatacoes INT
);

-- Registos sorteados para cada auditoria (prova de quais foram auditados)
CREATE TABLE auditoria.amostra (
    amostra_id        BIGSERIAL PRIMARY KEY,
    auditoria_id      BIGINT REFERENCES auditoria.execucao(auditoria_id),
    empresa_id        CHAR(1),
    circuito          VARCHAR(10),       -- C1 (clientes) ou C3 (tickets)
    referencia        VARCHAR(60),       -- cliente_sk ou ticket_id
    tipos_pii         VARCHAR(100),
    gravidade         VARCHAR(10),
    selecionado       BOOLEAN NOT NULL DEFAULT TRUE -- FALSE: candidato fora da amostra, conservado para rastreabilidade
);

CREATE TABLE auditoria.constatacao (
    constatacao_id    BIGSERIAL PRIMARY KEY,
    auditoria_id      BIGINT REFERENCES auditoria.execucao(auditoria_id),
    empresa_id        CHAR(1),
    circuito          VARCHAR(10),
    regra             VARCHAR(60),       -- ex: PII_EM_TEXTO_LIVRE, DADO_SAUDE, CLIENTE_SEM_CRM
    gravidade         VARCHAR(10),       -- BAIXA / MEDIA / ALTA
    referencia        VARCHAR(60),       -- ticket_id, cliente_sk, invoice_no...
    detalhe           TEXT,              -- SEMPRE mascarado
    detetada_em       TIMESTAMP DEFAULT now()
);

CREATE TABLE auditoria.notificacao (
    notificacao_id    BIGSERIAL PRIMARY KEY,
    auditoria_id      BIGINT REFERENCES auditoria.execucao(auditoria_id),
    empresa_id        CHAR(1),
    email_destino     VARCHAR(150),
    estado            VARCHAR(10) DEFAULT 'PENDENTE',   -- PENDENTE / ENVIADO / FALHOU
    tentativas        INT DEFAULT 0,
    criada_em         TIMESTAMP DEFAULT now(),
    enviada_em        TIMESTAMP,
    CONSTRAINT uq_auditoria_notificacao_exec_empresa UNIQUE (auditoria_id, empresa_id)
);

-- Resumo por empresa (para o e-mail e para o dashboard)
CREATE VIEW auditoria.v_resumo_empresa AS
SELECT e.empresa_id, e.nome,
       COUNT(c.constatacao_id)                                   AS total_constatacoes,
       COUNT(*) FILTER (WHERE c.gravidade = 'ALTA')              AS graves,
       COUNT(*) FILTER (WHERE c.gravidade = 'MEDIA')             AS medias,
       COUNT(*) FILTER (WHERE c.gravidade = 'BAIXA')             AS baixas,
       MAX(c.detetada_em)                                        AS ultima_constatacao
FROM ref.empresa e
LEFT JOIN auditoria.constatacao c ON c.empresa_id = e.empresa_id
GROUP BY e.empresa_id, e.nome;


-- Resultado de cada execução, incluindo a taxa real (arredondada a 2 casas).
CREATE VIEW auditoria.v_execucao_resumo AS
SELECT e.auditoria_id, e.empresa_id, r.nome AS empresa, e.executada_em,
       e.percentagem_amostra AS percentagem_pedida, e.percentagem_observada,
       e.registos_amostra, e.total_registos, e.total_constatacoes
FROM auditoria.execucao e
JOIN ref.empresa r ON r.empresa_id = e.empresa_id;
