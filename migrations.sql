-- Migration: Create bancos table
-- Database: gerenciaobra
-- Description: Create table for managing bank accounts

-- Create bancos table if it doesn't exist
CREATE TABLE IF NOT EXISTS `bancos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL UNIQUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create index on nome for faster searches
CREATE INDEX idx_bancos_nome ON `bancos`(`nome`);

-- Insert default banks if needed (optional)
-- INSERT INTO `bancos` (`nome`) VALUES 
-- ('Banco do Brasil'),
-- ('Caixa Econômica Federal'),
-- ('Itaú Unibanco'),
-- ('Santander'),
-- ('Bradesco')
-- ON DUPLICATE KEY UPDATE nome=nome;

-- =====================================================
-- Migration: Add conta column to formulario table
-- =====================================================
-- Add conta (bank/account) column to formulario table if it doesn't exist
-- This column will store the bank ID (foreign key to bancos table)
ALTER TABLE `formulario` ADD COLUMN IF NOT EXISTS `conta` INT DEFAULT NULL;

-- Add foreign key constraint to bancos table (optional but recommended)
-- Uncomment if you want to enforce referential integrity
-- ALTER TABLE `formulario` ADD CONSTRAINT `fk_formulario_conta` 
-- FOREIGN KEY (`conta`) REFERENCES `bancos`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- Create index on conta for faster searches
CREATE INDEX IF NOT EXISTS idx_formulario_conta ON `formulario`(`conta`);

-- =====================================================
-- Migration: Create fornecedor table
-- =====================================================    1
CREATE TABLE IF NOT EXISTS `fornecedor` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `titular` VARCHAR(255) NOT NULL,
  `cpf_cnpj` VARCHAR(20) NOT NULL UNIQUE,
  `chave_pix` VARCHAR(255),
  `banco_padrao` VARCHAR(255),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for faster searches
CREATE INDEX idx_fornecedor_titular ON `fornecedor`(`titular`);
CREATE INDEX idx_fornecedor_cpf_cnpj ON `fornecedor`(`cpf_cnpj`);

-- =====================================================
-- Migration: Create categoria table
-- =====================================================
CREATE TABLE IF NOT EXISTS `categoria` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL UNIQUE,
  `descricao` VARCHAR(500),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create index on nome for faster searches
CREATE INDEX idx_categoria_nome ON `categoria`(`nome`);

-- =====================================================
-- Migration: Add categoria column to formulario table
-- =====================================================
ALTER TABLE `formulario` ADD COLUMN IF NOT EXISTS `categoria` INT DEFAULT NULL;

-- Add foreign key constraint to categoria table (optional but recommended)
-- Uncomment if you want to enforce referential integrity
-- ALTER TABLE `formulario` ADD CONSTRAINT `fk_formulario_categoria` 
-- FOREIGN KEY (`categoria`) REFERENCES `categoria`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- Create index on categoria for faster searches
CREATE INDEX IF NOT EXISTS idx_formulario_categoria ON `formulario`(`categoria`);

-- =====================================================
-- Migration: Add multiplos_lancamentos flag to formulario
-- =====================================================
ALTER TABLE `formulario` ADD COLUMN `multiplos_lancamentos` TINYINT(1) DEFAULT 0;

-- Create index for faster filtering
CREATE INDEX idx_formulario_multiplos ON `formulario`(`multiplos_lancamentos`);

-- =====================================================
-- Migration: Create formulario_obras table (junction table)
-- =====================================================
-- This table stores the relationship between a formulario and multiple obras
-- When multiplos_lancamentos = 1, the value is split between these obras
CREATE TABLE IF NOT EXISTS `formulario_obras` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `formulario_id` INT NOT NULL,
  `obra_id` INT NOT NULL,
  `valor` DECIMAL(12, 2) NOT NULL, -- Valor atribuido a esta obra
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`formulario_id`) REFERENCES `formulario`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`obra_id`) REFERENCES `obras`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for faster searches
CREATE INDEX idx_formulario_obras_formulario ON `formulario_obras`(`formulario_id`);
CREATE INDEX idx_formulario_obras_obra ON `formulario_obras`(`obra_id`);

-- =====================================================
-- Migration: Add grupo_lancamento to formulario table
-- =====================================================
-- This column groups related lancamentos together (for multiple works)
ALTER TABLE `formulario` ADD COLUMN IF NOT EXISTS `grupo_lancamento` VARCHAR(50) DEFAULT NULL;

-- Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_formulario_grupo ON `formulario`(`grupo_lancamento`);
