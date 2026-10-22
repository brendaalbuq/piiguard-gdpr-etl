-- Empresas fictícias auditadas.
-- Preencha os endereços fictícios/consentidos antes de ativar o envio.
-- O UPSERT mantém email_contacto já configurado no banco de dados.
INSERT INTO ref.empresa (empresa_id, nome, nif, email_contacto) VALUES
 ('A', 'Clínica Dentária Sorriso do Minho, Lda', '509876543', 'O_TEU_EMAIL+clinica@gmail.com'),
 ('B', 'Ginásio Movimento Braga, Lda',           '513456782', 'O_TEU_EMAIL+ginasio@gmail.com'),
 ('C', 'TechCávado Informática, Lda',            '514567890', 'O_TEU_EMAIL+techcavado@gmail.com')
ON CONFLICT (empresa_id) DO UPDATE
SET nome = EXCLUDED.nome, nif = EXCLUDED.nif;
