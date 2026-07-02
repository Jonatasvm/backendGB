-- ================================================================
-- QUERIES PARA RODAR NO BANCO MySQL (gerenciaobra)
-- Execute na ordem abaixo
-- ================================================================

-- ================================================================
-- 1) FORMULÁRIO: Adicionar coluna id_solicitante
-- ================================================================
ALTER TABLE formulario ADD COLUMN id_solicitante BIGINT NULL;

-- (Opcional) Preencher id_solicitante retroativamente para registros existentes que já têm uuid
-- UPDATE formulario f
-- INNER JOIN users u ON f.uuid = u.uuid_id
-- SET f.id_solicitante = u.id
-- WHERE f.uuid IS NOT NULL AND f.id_solicitante IS NULL;


-- ================================================================
-- 2) CATEGORIA: Adicionar hierarquia pai/filha
-- ================================================================
ALTER TABLE categoria ADD COLUMN conta_filha BOOLEAN, ADD COLUMN id_pai BIGINT;


-- ================================================================
-- 3) USERS_FINCONTROL: Criar tabela se não existir
--    (Adapte conforme necessidade — a estrutura base é essa)
-- ================================================================
CREATE TABLE IF NOT EXISTS users_fincontrol (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID do gestor',
    display_name VARCHAR(255),
    username VARCHAR(255),
    password VARCHAR(255),
    user_role VARCHAR(50)
);


-- ================================================================
-- 4) USERS: Garantir que uuid_id suporta o vínculo
-- ================================================================
-- Ajustar tipo se necessário (se já for VARCHAR(36) ou similar, pule)
-- ALTER TABLE users MODIFY COLUMN uuid_id VARCHAR(36);

-- Adicionar índice único se não existir
-- (Primeiro verifique se já existe com: SHOW INDEX FROM users WHERE Key_name = 'unique_users_uuid_id';)
-- ALTER TABLE users ADD UNIQUE INDEX unique_users_uuid_id (uuid_id);


-- ================================================================
-- 5) USER_GESTOR: Criar tabela de vínculo gestor-subordinado
-- ================================================================
CREATE TABLE IF NOT EXISTS user_gestor (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ativo BOOLEAN DEFAULT TRUE,
    uuid_fincontrol VARCHAR(36) NOT NULL COMMENT 'UUID do gestor (users_fincontrol.id)',
    uuid_users VARCHAR(36) NOT NULL COMMENT 'UUID do subordinado (users.uuid_id)',
    
    UNIQUE INDEX unique_subordinado (uuid_users),
    INDEX idx_gestor (uuid_fincontrol)
);


-- ================================================================
-- FIM - Todas as queries aplicadas
-- ================================================================
