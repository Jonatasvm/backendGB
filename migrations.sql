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
