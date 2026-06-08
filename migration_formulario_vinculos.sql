-- =====================================================
-- Migration: Create formulario_vinculos table
-- Database: gerenciaobra
-- Description: Junction table para vincular múltiplos lançamentos com melhor integridade
-- =====================================================

CREATE TABLE IF NOT EXISTS `formulario_vinculos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `formulario_id_principal` INT NOT NULL,
  `formulario_id_vinculado` INT NOT NULL,
  `tipo_vinculo` ENUM('multiple_payment', 'adjustment', 'reversal', 'split', 'other') DEFAULT 'multiple_payment',
  `ativo` TINYINT(1) DEFAULT 1 COMMENT 'Boolean: 1=ativo, 0=inativo/quebrado',
  `observacao` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  -- Foreign Keys com cascata apropriada
  FOREIGN KEY (`formulario_id_principal`) 
    REFERENCES `formulario`(`id`) 
    ON DELETE CASCADE 
    ON UPDATE CASCADE,
  
  FOREIGN KEY (`formulario_id_vinculado`) 
    REFERENCES `formulario`(`id`) 
    ON DELETE CASCADE 
    ON UPDATE CASCADE,
  
  -- Constraint: Um lançamento não pode estar vinculado a si mesmo
  CONSTRAINT `chk_vinculos_diferentes` CHECK (`formulario_id_principal` != `formulario_id_vinculado`),
  
  -- Evitar duplicatas (A->B e B->A devem ser a mesma relação)
  UNIQUE KEY `uq_vinculos_pair` (
    LEAST(`formulario_id_principal`, `formulario_id_vinculado`),
    GREATEST(`formulario_id_principal`, `formulario_id_vinculado`),
    `tipo_vinculo`
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Índices para Performance
-- =====================================================

-- Buscar rápido por lançamento principal
CREATE INDEX idx_vinculos_principal ON `formulario_vinculos`(`formulario_id_principal`);

-- Buscar rápido por lançamento vinculado
CREATE INDEX idx_vinculos_vinculado ON `formulario_vinculos`(`formulario_id_vinculado`);

-- Buscar vinculos ativos rapidamente
CREATE INDEX idx_vinculos_ativo ON `formulario_vinculos`(`ativo`);

-- Buscar por tipo de vínculo
CREATE INDEX idx_vinculos_tipo ON `formulario_vinculos`(`tipo_vinculo`);

-- Combo: principal + ativo (queries mais comuns)
CREATE INDEX idx_vinculos_principal_ativo ON `formulario_vinculos`(`formulario_id_principal`, `ativo`);

-- =====================================================
-- Opção 1: Adicionar coluna grupo_vinculo à formulario (OPCIONAL)
-- Caso queira manter compatibilidade com sistema antigo
-- =====================================================
-- ALTER TABLE `formulario` ADD COLUMN IF NOT EXISTS `grupo_vinculo` INT DEFAULT NULL;
-- ALTER TABLE `formulario` ADD FOREIGN KEY (`grupo_vinculo`) 
--   REFERENCES `formulario_vinculos`(`id`) 
--   ON DELETE SET NULL 
--   ON UPDATE CASCADE;
-- CREATE INDEX idx_formulario_grupo_vinculo ON `formulario`(`grupo_vinculo`);

-- =====================================================
-- Opção 2: Migrar dados existentes (OPCIONAL)
-- Converter grupo_lancamento para novos vinculos
-- =====================================================
-- INSERTAR INTO `formulario_vinculos` 
-- SELECT 
--   NULL as id,
--   MIN(f1.id) as formulario_id_principal,
--   f2.id as formulario_id_vinculado,
--   'multiple_payment' as tipo_vinculo,
--   1 as ativo,
--   NULL as observacao,
--   NOW() as created_at,
--   NOW() as updated_at
-- FROM `formulario` f1
-- JOIN `formulario` f2 ON f1.grupo_lancamento = f2.grupo_lancamento
-- WHERE f1.grupo_lancamento IS NOT NULL
--   AND f1.id < f2.id
-- GROUP BY f1.grupo_lancamento, f2.id;
