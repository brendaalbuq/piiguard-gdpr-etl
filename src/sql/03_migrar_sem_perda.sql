-- Migração aditiva do PiiGuard; não remove nem reescreve registos existentes.
-- Executar na base piiguard já inicializada quando se atualiza de uma versão
-- anterior à auditoria C1+C2+C3.
BEGIN;

-- Colunas introduzidas nas transformações atuais. ADD COLUMN IF NOT EXISTS
-- preserva todas as linhas e valores da versão anterior.
ALTER TABLE clean.cliente
    ADD COLUMN IF NOT EXISTS tipos_pii VARCHAR(100),
    ADD COLUMN IF NOT EXISTS gravidade VARCHAR(10);

ALTER TABLE clean.fatura
    ADD COLUMN IF NOT EXISTS ficheiro_origem VARCHAR(200);

ALTER TABLE auditoria.ticket
    ADD COLUMN IF NOT EXISTS gravidade VARCHAR(10);

CREATE TABLE IF NOT EXISTS auditoria.amostra (
    amostra_id BIGSERIAL PRIMARY KEY,
    auditoria_id BIGINT REFERENCES auditoria.execucao(auditoria_id),
    empresa_id CHAR(1),
    circuito VARCHAR(10),
    referencia VARCHAR(60),
    tipos_pii VARCHAR(100),
    gravidade VARCHAR(10),
    selecionado BOOLEAN NOT NULL DEFAULT TRUE
);

ALTER TABLE auditoria.amostra
    ADD COLUMN IF NOT EXISTS selecionado BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE auditoria.execucao
    ADD COLUMN IF NOT EXISTS percentagem_observada NUMERIC(5,2);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_auditoria_execucao_pct_10_20'
          AND conrelid = 'auditoria.execucao'::regclass
    ) THEN
        ALTER TABLE auditoria.execucao
            ADD CONSTRAINT ck_auditoria_execucao_pct_10_20
            CHECK (percentagem_amostra BETWEEN 10 AND 20) NOT VALID;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'auditoria'
          AND indexname = 'uq_auditoria_notificacao_exec_empresa'
    ) THEN
        IF EXISTS (
            SELECT 1 FROM auditoria.notificacao
            GROUP BY auditoria_id, empresa_id HAVING count(*) > 1
        ) THEN
            RAISE NOTICE 'Índice de unicidade de notificações omitido: existem duplicados históricos; nenhum registo foi eliminado.';
        ELSE
            EXECUTE 'CREATE UNIQUE INDEX uq_auditoria_notificacao_exec_empresa ON auditoria.notificacao (auditoria_id, empresa_id)';
        END IF;
    END IF;
END $$;

CREATE OR REPLACE VIEW auditoria.v_execucao_resumo AS
SELECT e.auditoria_id, e.empresa_id, r.nome AS empresa, e.executada_em,
       e.percentagem_amostra AS percentagem_pedida, e.percentagem_observada,
       e.registos_amostra, e.total_registos, e.total_constatacoes
FROM auditoria.execucao e
JOIN ref.empresa r ON r.empresa_id = e.empresa_id;

COMMIT;
