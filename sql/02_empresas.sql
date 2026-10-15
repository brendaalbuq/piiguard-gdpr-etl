-- =====================================================================
-- PiiGuard - Empresas fictícias auditadas
-- ANTES DE CORRER: troque  O_TEU_EMAIL  pelo teu Gmail SEM o @gmail.com
-- (ex.: se o teu email é maria.silva@gmail.com, escreve maria.silva).
-- Com o "+empresaX", os 3 e-mails chegam à tua caixa, mas como
-- destinatários diferentes.
-- =====================================================================
DELETE FROM ref.empresa;

INSERT INTO ref.empresa (empresa_id, nome, nif, email_contacto) VALUES
 ('A', 'Clínica Dentária Sorriso do Minho, Lda', '509876543', 'O_TEU_EMAIL+clinica@gmail.com'),
 ('B', 'Ginásio Movimento Braga, Lda',           '513456782', 'O_TEU_EMAIL+ginasio@gmail.com'),
 ('C', 'TechCávado Informática, Lda',            '514567890', 'O_TEU_EMAIL+techcavado@gmail.com');
