-- =====================================================
-- Migration: reestruturar_multiplos_grupo_id.sql
-- Compatível com MySQL 5.7+ / 8.0+
-- RODE CADA BLOCO SEPARADAMENTE (um por um)
-- =====================================================


-- =====================================================
-- BLOCO 1: Criar tabela de sequência
-- =====================================================
CREATE TABLE IF NOT EXISTS `grupo_lancamento_seq` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =====================================================
-- BLOCO 2: Adicionar coluna grupo_id no formulario
-- (Se já existir, ignore o erro e pule pro bloco 3)
-- =====================================================
ALTER TABLE `formulario` ADD COLUMN `grupo_id` INT DEFAULT NULL;


-- =====================================================
-- BLOCO 3: Criar index no grupo_id
-- (Se já existir, ignore o erro e pule pro bloco 4)
-- =====================================================
ALTER TABLE `formulario` ADD INDEX `idx_formulario_grupo_id` (`grupo_id`);


-- =====================================================
-- BLOCO 4: Inserir sequências para cada grupo existente
-- =====================================================
INSERT INTO `grupo_lancamento_seq` (`created_at`)
SELECT MIN(`carimbo`) 
FROM `formulario` 
WHERE `grupo_lancamento` IS NOT NULL 
  AND TRIM(`grupo_lancamento`) != ''
GROUP BY `grupo_lancamento`
ORDER BY MIN(`id`) ASC;


-- =====================================================
-- BLOCO 5: Criar tabela de mapeamento
-- =====================================================
DROP TABLE IF EXISTS `_tmp_grupo_map`;


-- =====================================================
-- BLOCO 6: Criar tabela de mapeamento (estrutura)
-- =====================================================
CREATE TABLE `_tmp_grupo_map` (
  `seq_id` INT AUTO_INCREMENT PRIMARY KEY,
  `grupo_lancamento_antigo` VARCHAR(50)
) ENGINE=InnoDB;


-- =====================================================
-- BLOCO 7: Popular mapeamento
-- =====================================================
INSERT INTO `_tmp_grupo_map` (`grupo_lancamento_antigo`)
SELECT DISTINCT `grupo_lancamento`
FROM `formulario`
WHERE `grupo_lancamento` IS NOT NULL
  AND TRIM(`grupo_lancamento`) != ''
ORDER BY (SELECT MIN(`id`) FROM `formulario` f2 WHERE f2.`grupo_lancamento` = `formulario`.`grupo_lancamento`) ASC;


-- =====================================================
-- BLOCO 8: Atualizar formulario.grupo_id com base no mapeamento
-- =====================================================
UPDATE `formulario` f
JOIN `_tmp_grupo_map` m ON f.`grupo_lancamento` = m.`grupo_lancamento_antigo`
SET f.`grupo_id` = m.`seq_id`;


-- =====================================================
-- BLOCO 9: Limpar tabela de mapeamento
-- =====================================================
DROP TABLE IF EXISTS `_tmp_grupo_map`;


-- =====================================================
-- BLOCO 10: VERIFICAÇÃO — rode para confirmar
-- =====================================================
SELECT 'Grupos migrados' AS info, COUNT(*) AS total FROM grupo_lancamento_seq;
SELECT 'Com grupo_id' AS info, COUNT(*) AS total FROM formulario WHERE grupo_id IS NOT NULL;
SELECT 'Sem grupo (simples)' AS info, COUNT(*) AS total FROM formulario WHERE grupo_id IS NULL;
SELECT 'Orfaos restantes' AS info, COUNT(*) AS total FROM formulario WHERE multiplos_lancamentos = 1 AND grupo_id IS NULL;


-- =====================================================
-- BLOCO 11: (OPCIONAL) Remover colunas antigas
-- Descomente APENAS quando tudo estiver funcionando
-- =====================================================
-- ALTER TABLE `formulario` DROP COLUMN `grupo_lancamento`;
-- ALTER TABLE `formulario` DROP COLUMN `multiplos_lancamentos`;
