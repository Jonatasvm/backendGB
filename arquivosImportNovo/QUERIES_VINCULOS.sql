-- =====================================================
-- QUERIES ESSENCIAIS - Tabela formulario_vinculos
-- =====================================================

-- ==========================
-- 1. CRIAR VÍNCULOS
-- ==========================

-- Criar vínculo simples entre dois lançamentos
INSERT INTO formulario_vinculos 
(formulario_id_principal, formulario_id_vinculado, tipo_vinculo, ativo, observacao)
VALUES (1, 2, 'multiple_payment', 1, 'Dividido em 2 obras');

-- Criar vários vínculos (múltiplas obras)
INSERT INTO formulario_vinculos 
(formulario_id_principal, formulario_id_vinculado, tipo_vinculo, observacao)
VALUES 
(1, 2, 'multiple_payment', 'Obra 2'),
(1, 3, 'multiple_payment', 'Obra 3'),
(1, 4, 'multiple_payment', 'Obra 4');

-- ==========================
-- 2. BUSCAR VÍNCULOS
-- ==========================

-- Buscar todos os vínculos ativos de um lançamento
SELECT 
  v.id,
  v.formulario_id_principal,
  v.formulario_id_vinculado,
  v.tipo_vinculo,
  v.ativo,
  v.observacao,
  v.created_at
FROM formulario_vinculos v
WHERE (v.formulario_id_principal = 1 OR v.formulario_id_vinculado = 1)
AND v.ativo = 1
ORDER BY v.created_at DESC;

-- Buscar vínculos com detalhes dos formulários
SELECT 
  v.id as vinculo_id,
  v.formulario_id_principal,
  v.formulario_id_vinculado,
  v.tipo_vinculo,
  v.ativo,
  f1.referente as principal_referente,
  f1.valor as principal_valor,
  f1.obra as principal_obra,
  f2.referente as vinculado_referente,
  f2.valor as vinculado_valor,
  f2.obra as vinculado_obra,
  (f1.valor + f2.valor) as valor_total
FROM formulario_vinculos v
JOIN formulario f1 ON v.formulario_id_principal = f1.id
JOIN formulario f2 ON v.formulario_id_vinculado = f2.id
WHERE (v.formulario_id_principal = 1 OR v.formulario_id_vinculado = 1)
AND v.ativo = 1
ORDER BY v.created_at DESC;

-- ==========================
-- 3. LISTAR GRUPOS COMPLETOS
-- ==========================

-- Listar todos os lançamentos que fazem parte de um "grupo"
-- (um grupo é um conjunto de lançamentos vinculados entre si)
WITH RECURSIVE grupo_lancamentos AS (
  -- Base: encontrar todos conectados a um lançamento
  SELECT 
    formulario_id_principal as primeiro_id,
    formulario_id_vinculado as segundo_id,
    1 as nivel
  FROM formulario_vinculos
  WHERE ativo = 1
  
  UNION ALL
  
  -- Recursivo: expandir para conectados aos conectados
  SELECT 
    g.primeiro_id,
    v.formulario_id_vinculado,
    g.nivel + 1
  FROM grupo_lancamentos g
  JOIN formulario_vinculos v ON (
    (g.segundo_id = v.formulario_id_principal OR g.segundo_id = v.formulario_id_vinculado)
    AND v.ativo = 1
  )
  WHERE g.nivel < 5  -- Limitar profundidade
)
SELECT DISTINCT 
  f.id,
  f.referente,
  f.valor,
  f.obra,
  f.data_pagamento,
  f.data_lancamento
FROM grupo_lancamentos g
JOIN formulario f ON (f.id = g.primeiro_id OR f.id = g.segundo_id)
WHERE g.primeiro_id = 1 OR g.segundo_id = 1
ORDER BY f.id ASC;

-- ==========================
-- 4. CALCULAR VALORES
-- ==========================

-- Calcular valor total de um grupo de lançamentos vinculados
SELECT 
  1 as formulario_id,
  COUNT(DISTINCT CASE WHEN v.formulario_id_principal = 1 THEN v.formulario_id_vinculado ELSE v.formulario_id_principal END) + 1 as total_lancamentos,
  SUM(
    CASE 
      WHEN v.formulario_id_principal = 1 THEN f2.valor
      ELSE f1.valor
    END
  ) + (SELECT valor FROM formulario WHERE id = 1) as valor_total
FROM formulario_vinculos v
LEFT JOIN formulario f1 ON v.formulario_id_principal = f1.id
LEFT JOIN formulario f2 ON v.formulario_id_vinculado = f2.id
WHERE (v.formulario_id_principal = 1 OR v.formulario_id_vinculado = 1)
AND v.ativo = 1;

-- ==========================
-- 5. CONTAR VÍNCULOS
-- ==========================

-- Contar total de vínculos por tipo
SELECT 
  tipo_vinculo,
  COUNT(*) as total,
  SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) as ativos,
  SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) as inativos
FROM formulario_vinculos
GROUP BY tipo_vinculo
ORDER BY total DESC;

-- Contar vínculos por lançamento
SELECT 
  f.id,
  f.referente,
  f.valor,
  COUNT(fv.id) as total_vinculos,
  SUM(CASE WHEN fv.ativo = 1 THEN 1 ELSE 0 END) as vinculos_ativos
FROM formulario f
LEFT JOIN formulario_vinculos fv ON (
  f.id = fv.formulario_id_principal 
  OR f.id = fv.formulario_id_vinculado
)
GROUP BY f.id, f.referente, f.valor
HAVING COUNT(fv.id) > 0
ORDER BY total_vinculos DESC;

-- ==========================
-- 6. ATUALIZAR VÍNCULOS
-- ==========================

-- Desativar um vínculo
UPDATE formulario_vinculos 
SET ativo = 0, updated_at = CURRENT_TIMESTAMP
WHERE id = 1;

-- Reativar um vínculo
UPDATE formulario_vinculos 
SET ativo = 1, updated_at = CURRENT_TIMESTAMP
WHERE id = 1;

-- Atualizar observação
UPDATE formulario_vinculos 
SET observacao = 'Nova observação', updated_at = CURRENT_TIMESTAMP
WHERE id = 1;

-- Desativar todos os vínculos de um lançamento
UPDATE formulario_vinculos 
SET ativo = 0, observacao = CONCAT(COALESCE(observacao, ''), ' [QUEBRADO]')
WHERE (formulario_id_principal = 1 OR formulario_id_vinculado = 1)
AND ativo = 1;

-- ==========================
-- 7. DELETAR VÍNCULOS
-- ==========================

-- Deletar um vínculo específico
DELETE FROM formulario_vinculos 
WHERE id = 1;

-- Deletar todos os vínculos inativos
DELETE FROM formulario_vinculos 
WHERE ativo = 0;

-- Deletar todos os vínculos de um lançamento
DELETE FROM formulario_vinculos 
WHERE formulario_id_principal = 1 OR formulario_id_vinculado = 1;

-- ==========================
-- 8. ANÁLISES E RELATÓRIOS
-- ==========================

-- Relatório: Lançamentos com vínculos múltiplos
SELECT 
  CASE 
    WHEN formulario_id_principal < formulario_id_vinculado THEN formulario_id_principal
    ELSE formulario_id_vinculado
  END as grupo_id,
  COUNT(*) as total_vinculos,
  COUNT(DISTINCT formulario_id_principal) + COUNT(DISTINCT formulario_id_vinculado) as total_formularios,
  GROUP_CONCAT(
    CASE 
      WHEN formulario_id_principal < formulario_id_vinculado 
      THEN CONCAT(formulario_id_principal, ',', formulario_id_vinculado)
      ELSE CONCAT(formulario_id_vinculado, ',', formulario_id_principal)
    END
    SEPARATOR ' | '
  ) as pares
FROM formulario_vinculos
WHERE ativo = 1
GROUP BY grupo_id
HAVING COUNT(*) >= 2
ORDER BY total_vinculos DESC;

-- Lançamentos que foram desativados (histórico)
SELECT 
  v.id,
  v.formulario_id_principal,
  v.formulario_id_vinculado,
  v.tipo_vinculo,
  v.observacao,
  v.updated_at as data_desativacao
FROM formulario_vinculos v
WHERE v.ativo = 0
ORDER BY v.updated_at DESC
LIMIT 20;

-- ==========================
-- 9. INTEGRIDADE E LIMPEZA
-- ==========================

-- Buscar vínculos órfãos (com formulário deletado)
SELECT v.id
FROM formulario_vinculos v
LEFT JOIN formulario f1 ON v.formulario_id_principal = f1.id
LEFT JOIN formulario f2 ON v.formulario_id_vinculado = f2.id
WHERE f1.id IS NULL OR f2.id IS NULL;

-- Buscar lançamentos sem vínculo
SELECT f.id, f.referente, f.valor
FROM formulario f
LEFT JOIN formulario_vinculos v ON (
  (f.id = v.formulario_id_principal OR f.id = v.formulario_id_vinculado)
  AND v.ativo = 1
)
WHERE v.id IS NULL
ORDER BY f.id DESC
LIMIT 20;

-- Verificar constraints duplicadas (não deveria ter nenhuma)
SELECT 
  v1.id as id1,
  v1.formulario_id_principal,
  v1.formulario_id_vinculado,
  v1.tipo_vinculo,
  COUNT(*) as total_duplicadas
FROM formulario_vinculos v1
JOIN formulario_vinculos v2 ON (
  (v1.formulario_id_principal = v2.formulario_id_principal AND v1.formulario_id_vinculado = v2.formulario_id_vinculado)
  OR
  (v1.formulario_id_principal = v2.formulario_id_vinculado AND v1.formulario_id_vinculado = v2.formulario_id_principal)
)
WHERE v1.id <= v2.id AND v1.id != v2.id AND v1.tipo_vinculo = v2.tipo_vinculo
GROUP BY v1.id
HAVING COUNT(*) > 1;

-- ==========================
-- 10. PERFORMANCE - ÍNDICES
-- ==========================

-- Verificar se os índices estão sendo usados
EXPLAIN
SELECT v.* FROM formulario_vinculos v
WHERE v.formulario_id_principal = 1 AND v.ativo = 1;

-- Verificar fragmentação dos índices
SELECT 
  TABLE_NAME,
  INDEX_NAME,
  SEQ_IN_INDEX,
  COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_NAME = 'formulario_vinculos'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- Estatísticas de uso
SELECT 
  OBJECT_SCHEMA,
  OBJECT_NAME,
  COUNT_READ,
  COUNT_WRITE,
  COUNT_FETCH,
  COUNT_INSERT,
  COUNT_UPDATE,
  COUNT_DELETE
FROM PERFORMANCE_SCHEMA.TABLE_IO_WAITS_SUMMARY_BY_TABLE
WHERE OBJECT_NAME = 'formulario_vinculos';

-- ==========================
-- 11. MIGRAÇÃO DADOS ANTIGOS
-- ==========================

-- Converter grupo_lancamento para novos vínculos
INSERT INTO formulario_vinculos 
  (formulario_id_principal, formulario_id_vinculado, tipo_vinculo, ativo, observacao)
SELECT 
  MIN(f1.id) as formulario_id_principal,
  f2.id as formulario_id_vinculado,
  'multiple_payment' as tipo_vinculo,
  1 as ativo,
  CONCAT('Migrado de grupo_lancamento: ', f1.grupo_lancamento) as observacao
FROM formulario f1
JOIN formulario f2 ON f1.grupo_lancamento = f2.grupo_lancamento
WHERE f1.grupo_lancamento IS NOT NULL
  AND f1.id < f2.id
  AND NOT EXISTS (
    SELECT 1 FROM formulario_vinculos v
    WHERE (v.formulario_id_principal = f1.id AND v.formulario_id_vinculado = f2.id)
       OR (v.formulario_id_principal = f2.id AND v.formulario_id_vinculado = f1.id)
  )
GROUP BY f1.grupo_lancamento, f2.id
ON DUPLICATE KEY UPDATE observacao = observacao;

-- Verificar migração
SELECT COUNT(*) as total_vinculos FROM formulario_vinculos;
SELECT COUNT(*) as com_grupo FROM formulario WHERE grupo_lancamento IS NOT NULL;
