-- Consultas de verificação sem alterações à base de dados.
-- Executar depois de c1_clientes, c2_faturas, c3_receber_tickets e c3_auditoria.

-- Comparação entre percentagem pedida e efetivamente selecionada.
SELECT auditoria_id, empresa_id, empresa, percentagem_pedida,
       percentagem_observada, registos_amostra, total_registos,
       total_constatacoes
FROM auditoria.v_execucao_resumo
ORDER BY auditoria_id DESC, empresa_id;

-- Contagens que permitem confirmar a seleção e o encaminhamento.
SELECT a.auditoria_id, a.empresa_id,
       count(*) AS candidatos,
       count(*) FILTER (WHERE a.selecionado) AS selecionados,
       count(*) FILTER (WHERE NOT a.selecionado) AS excluidos
FROM auditoria.amostra a
GROUP BY a.auditoria_id, a.empresa_id
ORDER BY a.auditoria_id DESC, a.empresa_id;

-- Estados de envio e número de tentativas; o limite do circuito é 3.
SELECT estado, tentativas, count(*) AS notificacoes
FROM auditoria.notificacao
GROUP BY estado, tentativas
ORDER BY estado, tentativas;

-- Deve devolver zero linhas: uma notificação persistente por empresa e execução.
SELECT auditoria_id, empresa_id, count(*) AS duplicados
FROM auditoria.notificacao
GROUP BY auditoria_id, empresa_id
HAVING count(*) > 1;

-- Verificação da reconciliação dos lotes.
SELECT * FROM controlo.v_reconciliacao ORDER BY lote_id DESC;
