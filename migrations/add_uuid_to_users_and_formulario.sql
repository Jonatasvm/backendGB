-- Migration: add_uuid_to_users_and_formulario.sql
-- Cria coluna uuid_id na tabela users e coluna uuid na tabela formulario
-- Executar uma vez no banco de dados (MySQL)

ALTER TABLE users
ADD COLUMN IF NOT EXISTS uuid_id VARCHAR(36) NULL COMMENT 'UUID gerado automaticamente no cadastro';

ALTER TABLE formulario
ADD COLUMN IF NOT EXISTS uuid VARCHAR(36) NULL COMMENT 'UUID do solicitante (users.uuid_id)';

-- Popula uuid_id para usuários existentes (gera UUIDs novos para cada usuário sem uuid_id)
UPDATE users
SET uuid_id = (SELECT UUID())
WHERE uuid_id IS NULL OR uuid_id = '';

-- Popula formulario.uuid a partir do solicitante (se solicitante for id)
-- Se solicitante foi salvo como username/texto, esta query tenta casar por username
UPDATE formulario f
LEFT JOIN users u ON (CASE WHEN f.solicitante REGEXP '^[0-9]+$' THEN u.id = CAST(f.solicitante AS UNSIGNED) ELSE UPPER(u.username) = UPPER(f.solicitante) END)
SET f.uuid = u.uuid_id
WHERE f.uuid IS NULL OR f.uuid = ''; 

-- Índice para acelerar buscas por uuid (opcional)
CREATE INDEX IF NOT EXISTS idx_users_uuid_id ON users(uuid_id(36));
CREATE INDEX IF NOT EXISTS idx_formulario_uuid ON formulario(uuid(36));
