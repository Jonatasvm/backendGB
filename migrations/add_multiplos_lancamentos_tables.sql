-- Migration: add_multiplos_lancamentos_tables.sql
-- Script mínimo para habilitar 'múltiplos lançamentos' conforme o backend atual
-- Executar uma vez no banco MySQL (faça backup antes)

-- 1) Adiciona colunas necessárias na tabela `formulario`
-- Obs: REMOVA o IF NOT EXISTS se sua versão do MySQL não suportar. Se as colunas já existirem, ajustar manualmente.
ALTER TABLE `formulario`
  ADD COLUMN `multiplos_lancamentos` TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN `grupo_lancamento` VARCHAR(50) DEFAULT NULL;

-- 2) Índices recomendados para desempenho nas queries existentes no backend
CREATE INDEX idx_formulario_multiplos ON `formulario`(`multiplos_lancamentos`);
CREATE INDEX idx_formulario_grupo ON `formulario`(`grupo_lancamento`);

-- 3) Backfill: popula grupo_lancamento para registros históricos onde multiplos_lancamentos = 1
-- Gera um identificador determinístico curto (8 chars) a partir de data_lancamento dia + solicitante + titular
UPDATE `formulario` f
SET f.grupo_lancamento = LEFT(MD5(CONCAT(DATE_FORMAT(f.data_lancamento, '%Y%m%d'), '-', COALESCE(f.solicitante, ''), '-', COALESCE(f.titular, ''))), 8)
WHERE f.multiplos_lancamentos = 1 AND (f.grupo_lancamento IS NULL OR f.grupo_lancamento = '');

-- Observações importantes:
-- 1) Este script adiciona apenas o que o backend atual realmente usa: a flag `multiplos_lancamentos` e o `grupo_lancamento`.
-- 2) O backend cria um registro por obra (quando `multiplos_lancamentos=1` e `obras_adicionais` é enviado) e usa `grupo_lancamento` para agrupar os registros.
-- 3) Faça backup do banco antes de executar o script. Se as colunas já existirem, o ALTER TABLE acima irá falhar — execute com cautela ou remova as linhas correspondentes.
-- 4) Se desejar eu adapto o script para verificar existência das colunas via information_schema e executar condicionalmente (mais compatível com diferentes versões do MySQL).

-- Fim da migração
