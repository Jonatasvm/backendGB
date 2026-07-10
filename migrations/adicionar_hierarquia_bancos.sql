-- =====================================================
-- Adicionar suporte a subgrupos (hierarquia) na tabela de bancos
-- =====================================================

-- Adiciona a coluna para identificar se é uma conta filha
ALTER TABLE `bancos` ADD COLUMN `conta_filha` TINYINT(1) DEFAULT 0;

-- Adiciona a coluna para referenciar o ID do banco pai
ALTER TABLE `bancos` ADD COLUMN `id_pai` INT DEFAULT NULL;

-- Opcional: Adiciona chave estrangeira para garantir a integridade (se necessário)
-- ALTER TABLE `bancos` ADD CONSTRAINT `fk_banco_pai` FOREIGN KEY (`id_pai`) REFERENCES `bancos`(`id`) ON DELETE SET NULL;
