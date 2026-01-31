-- =====================================================
-- SCRIPT: Preencher grupo_lancamento para lançamentos múltiplos antigos
-- =====================================================

-- 1. Agrupar lançamentos múltiplos antigos que não têm grupo_lancamento
-- Estratégia: Agrupar por obra + data_lancamento + titular + solicitante
-- (assumindo que lançamentos múltiplos criados no mesmo dia para o mesmo titular são do mesmo grupo)

-- 2. Para cada grupo de lançamentos múltiplos, gerar um grupo_lancamento único
UPDATE formulario f1
SET grupo_lancamento = (
    SELECT CONCAT(
        DATE_FORMAT(f2.data_lancamento, '%Y%m%d'),
        '_',
        f2.solicitante,
        '_',
        SUBSTRING(MD5(CONCAT(f2.obra, f2.titular, f2.data_lancamento)), 1, 8)
    )
    FROM formulario f2
    WHERE f2.multiplos_lancamentos = 1
    AND f2.grupo_lancamento IS NULL
    AND f2.id = f1.id
    LIMIT 1
)
WHERE f1.multiplos_lancamentos = 1
AND f1.grupo_lancamento IS NULL;

-- 3. Verificar quantos registros foram atualizados
SELECT COUNT(*) as 'Lançamentos Múltiplos Atualizados com Grupo'
FROM formulario
WHERE multiplos_lancamentos = 1
AND grupo_lancamento IS NOT NULL;
