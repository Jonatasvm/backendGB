-- ================================================================
-- QUERIES ESSENCIAIS PARA MANIPULAÇÃO DE LANÇAMENTOS
-- ================================================================

-- 1. VER ESTRUTURA COMPLETA DA TABELA FORMULARIO
-- ================================================================
DESCRIBE formulario;
SHOW CREATE TABLE formulario;

-- 2. LISTAR LANÇAMENTOS COM SEUS RELACIONADOS
-- ================================================================
-- Versão nova com grupo_lancamento (mostra apenas primeiro de cada grupo)
SELECT f.* FROM (
    SELECT *,
           CASE 
               WHEN grupo_lancamento IS NOT NULL 
               THEN ROW_NUMBER() OVER (PARTITION BY grupo_lancamento ORDER BY id ASC)
               ELSE 1
           END as rn
    FROM formulario
) f
WHERE f.rn = 1
ORDER BY f.id DESC;

-- 3. BUSCAR TODOS OS REGISTROS DE UM LANÇAMENTO MÚLTIPLO
-- ================================================================
-- Por grupo_lancamento (novo método)
SELECT 
    f.id,
    f.obra,
    f.valor,
    f.titular,
    f.data_lancamento,
    f.forma_pagamento,
    f.grupo_lancamento,
    o.nome as obra_nome
FROM formulario f
LEFT JOIN obras o ON f.obra = o.id
WHERE f.grupo_lancamento = 'abc123de'  -- Substituir pelo grupo desejado
ORDER BY f.id ASC;

-- Por data + solicitante + titular (método antigo)
SELECT 
    f.id,
    f.obra,
    f.valor,
    f.titular,
    f.multiplos_lancamentos,
    o.nome as obra_nome
FROM formulario f
LEFT JOIN obras o ON f.obra = o.id
WHERE multiplos_lancamentos = 1 
    AND DATE_FORMAT(f.data_lancamento, '%Y%m%d') = '20250131'
    AND solicitante = 'joao'
    AND titular = 'FORNECEDOR SA'
ORDER BY f.id ASC;

-- 4. CONTAR QUANTOS LANÇAMENTOS HÁ EM CADA GRUPO
-- ================================================================
SELECT 
    grupo_lancamento,
    COUNT(*) as qtd_lancamentos,
    SUM(valor) as valor_total,
    MAX(data_lancamento) as data_grupo
FROM formulario
WHERE grupo_lancamento IS NOT NULL
GROUP BY grupo_lancamento
ORDER BY qtd_lancamentos DESC;

-- 5. LISTAR LANÇAMENTOS MÚLTIPLOS (COM RESUMO)
-- ================================================================
SELECT 
    f.id as id_principal,
    f.data_lancamento,
    f.solicitante,
    f.titular,
    f.multiplos_lancamentos,
    f.grupo_lancamento,
    COUNT(DISTINCT fm.id) as total_obras,
    SUM(fm.valor) as valor_total,
    GROUP_CONCAT(DISTINCT o.nome SEPARATOR ', ') as obras
FROM formulario f
LEFT JOIN formulario fm ON f.grupo_lancamento = fm.grupo_lancamento 
                         OR (f.id = fm.id)
LEFT JOIN obras o ON fm.obra = o.id
WHERE f.multiplos_lancamentos = 1
GROUP BY f.id, f.grupo_lancamento
ORDER BY f.id DESC;

-- 6. DELETAR UM LANÇAMENTO (SIMPLES)
-- ================================================================
DELETE FROM formulario WHERE id = 100;

-- 7. DELETAR UM LANÇAMENTO MÚLTIPLO (TODO O GRUPO)
-- ================================================================
-- Passo 1: Encontrar o grupo_lancamento
SELECT grupo_lancamento FROM formulario WHERE id = 100;

-- Passo 2: Deletar todos os registros com o mesmo grupo
DELETE FROM formulario 
WHERE grupo_lancamento = 'abc123de';

-- Método alternativo (antigo): deletar por data+solicitante+titular
DELETE FROM formulario 
WHERE multiplos_lancamentos = 1 
    AND DATE_FORMAT(data_lancamento, '%Y%m%d') = '20250131'
    AND solicitante = 'joao'
    AND titular = 'FORNECEDOR SA';

-- 8. ATUALIZAR STATUS DE LANÇAMENTO
-- ================================================================
-- Marcar como Lançado
UPDATE formulario 
SET lancado = 'Y' 
WHERE id = 100;

-- Marcar como Pendente
UPDATE formulario 
SET lancado = 'N' 
WHERE id = 100;

-- Marcar como Não Autorizado
UPDATE formulario 
SET lancado = 'X' 
WHERE id = 100;

-- Marcar como Aprovado
UPDATE formulario 
SET lancado = 'A' 
WHERE id = 100;

-- 9. BUSCAR LANÇAMENTOS ORPHÃOS (SEM OBRA VÁLIDA)
-- ================================================================
SELECT 
    f.id,
    f.titular,
    f.obra,
    f.data_lancamento,
    o.nome as obra_nome
FROM formulario f
LEFT JOIN obras o ON f.obra = o.id
WHERE o.id IS NULL
ORDER BY f.id DESC;

-- 10. ESTATÍSTICAS DE LANÇAMENTOS
-- ================================================================
SELECT 
    COUNT(*) as total_lancamentos,
    COUNT(DISTINCT DATE_FORMAT(data_lancamento, '%Y%m%d')) as dias_com_lancamentos,
    COUNT(DISTINCT solicitante) as total_solicitantes,
    COUNT(DISTINCT titular) as total_titulares,
    COUNT(DISTINCT obra) as total_obras,
    SUM(valor) as valor_total_centavos,
    ROUND(SUM(valor) / 100, 2) as valor_total_reais,
    COUNT(CASE WHEN lancado = 'Y' THEN 1 END) as lancados,
    COUNT(CASE WHEN lancado = 'N' THEN 1 END) as pendentes,
    COUNT(CASE WHEN multiplos_lancamentos = 1 THEN 1 END) as multiplos
FROM formulario;

-- 11. BUSCAR FORNECEDORES NÃO CADASTRADOS
-- ================================================================
SELECT 
    f.titular,
    f.cpf_cnpj,
    COUNT(*) as qtd_lancamentos,
    SUM(f.valor) / 100 as valor_total_reais
FROM formulario f
LEFT JOIN fornecedor forn ON LOWER(TRIM(f.titular)) = LOWER(TRIM(forn.titular))
WHERE f.fornecedor_novo = 1 
   OR forn.id IS NULL
GROUP BY f.titular, f.cpf_cnpj
ORDER BY qtd_lancamentos DESC;

-- 12. RELACIONAMENTOS: LANÇAMENTOS POR OBRA
-- ================================================================
SELECT 
    o.id,
    o.nome,
    COUNT(f.id) as qtd_lancamentos,
    SUM(f.valor) / 100 as valor_total_reais,
    COUNT(DISTINCT f.data_lancamento) as dias
FROM obras o
LEFT JOIN formulario f ON o.id = f.obra
GROUP BY o.id, o.nome
ORDER BY valor_total_reais DESC;

-- 13. RELACIONAMENTOS: LANÇAMENTOS POR CATEGORIA
-- ================================================================
SELECT 
    c.id,
    c.nome,
    COUNT(f.id) as qtd_lancamentos,
    SUM(f.valor) / 100 as valor_total_reais
FROM categoria c
LEFT JOIN formulario f ON c.id = f.categoria
GROUP BY c.id, c.nome
ORDER BY valor_total_reais DESC;

-- 14. RELACIONAMENTOS: LANÇAMENTOS POR BANCO
-- ================================================================
SELECT 
    b.id,
    b.nome,
    COUNT(f.id) as qtd_lancamentos,
    SUM(f.valor) / 100 as valor_total_reais
FROM bancos b
LEFT JOIN formulario f ON b.id = f.conta
GROUP BY b.id, b.nome
ORDER BY valor_total_reais DESC;

-- 15. LANÇAMENTOS COM TODOS OS DADOS RELACIONADOS
-- ================================================================
SELECT 
    f.id,
    f.data_lancamento,
    f.solicitante,
    f.titular,
    f.referente,
    f.valor / 100 as valor_reais,
    f.forma_pagamento,
    f.lancado,
    o.nome as obra_nome,
    c.nome as categoria_nome,
    b.nome as banco_nome,
    f.grupo_lancamento,
    f.multiplos_lancamentos,
    f.fornecedor_novo,
    f.carimbo
FROM formulario f
LEFT JOIN obras o ON f.obra = o.id
LEFT JOIN categoria c ON f.categoria = c.id
LEFT JOIN bancos b ON f.conta = b.id
WHERE f.id = 100;

-- 16. SINCRONIZAR GRUPO_LANCAMENTO PARA LANÇAMENTOS ANTIGOS
-- ================================================================
-- Preench grupo_lancamento para lançamentos múltiplos sem grupo
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

-- 17. VERIFICAR INTEGRIDADE DE CHAVES ESTRANGEIRAS
-- ================================================================
-- Obras sem referência em formulário
SELECT o.id, o.nome 
FROM obras o
LEFT JOIN formulario f ON o.id = f.obra
WHERE f.id IS NULL;

-- Categorias sem referência
SELECT c.id, c.nome 
FROM categoria c
LEFT JOIN formulario f ON c.id = f.categoria
WHERE f.id IS NULL;

-- Bancos sem referência
SELECT b.id, b.nome 
FROM bancos b
LEFT JOIN formulario f ON b.id = f.conta
WHERE f.id IS NULL;

-- 18. CONVERSÃO DE VALORES (CENTAVOS ↔ REAIS)
-- ================================================================
-- Ver valores em centavos e em reais
SELECT 
    id,
    valor as centavos,
    ROUND(valor / 100, 2) as reais,
    valor / 100 as reais_decimal
FROM formulario
LIMIT 10;

-- 19. LANÇAMENTOS POR PERÍODO
-- ================================================================
SELECT 
    DATE_FORMAT(data_lancamento, '%Y-%m') as mes,
    COUNT(*) as qtd,
    SUM(valor) / 100 as valor_total_reais
FROM formulario
GROUP BY DATE_FORMAT(data_lancamento, '%Y-%m')
ORDER BY mes DESC;

-- 20. BUSCAR DUPLICATAS SUSPEITAS
-- ================================================================
-- Lançamentos com mesmo titular, obra, valor e data de lançamento
SELECT 
    titular,
    obra,
    valor,
    data_lancamento,
    COUNT(*) as qtd_duplicatas,
    GROUP_CONCAT(id SEPARATOR ', ') as ids
FROM formulario
GROUP BY titular, obra, valor, DATE_FORMAT(data_lancamento, '%Y%m%d')
HAVING COUNT(*) > 1
ORDER BY qtd_duplicatas DESC;

-- 21. ATUALIZAR LINK_ANEXO PARA MÚLTIPLOS REGISTROS
-- ================================================================
UPDATE formulario 
SET link_anexo = 'https://drive.google.com/...'
WHERE grupo_lancamento = 'abc123de';

-- 22. BUSCAR LANÇAMENTOS SEM ANEXO
-- ================================================================
SELECT 
    id,
    data_lancamento,
    titular,
    valor / 100 as valor_reais
FROM formulario
WHERE link_anexo IS NULL OR TRIM(link_anexo) = ''
ORDER BY id DESC
LIMIT 20;

-- 23. VALIDAR CAMPO CPF_CNPJ
-- ================================================================
-- CPF_CNPJ sem preenchimento
SELECT 
    id,
    titular,
    cpf_cnpj,
    COUNT(*) as qtd
FROM formulario
WHERE cpf_cnpj IS NULL OR TRIM(cpf_cnpj) = ''
GROUP BY cpf_cnpj, titular
ORDER BY qtd DESC;

-- 24. BUSCAR LANÇAMENTOS COM CHAVE_PIX INVÁLIDA
-- ================================================================
SELECT 
    id,
    titular,
    forma_pagamento,
    chave_pix,
    LENGTH(chave_pix) as tam_chave
FROM formulario
WHERE forma_pagamento = 'pix'
  AND (chave_pix IS NULL OR TRIM(chave_pix) = '')
ORDER BY id DESC;

-- 25. AUDIT: Ver histórico de alterações (se houver tabela de log)
-- ================================================================
-- Esta query depende de um sistema de auditoria (não está no schema atual)
-- Sugestão: criar tabela formulario_auditoria para rastrear mudanças


-- ================================================================
-- QUERIES DE LIMPEZA/MANUTENÇÃO
-- ================================================================

-- Recalcular AUTO_INCREMENT após muitos deletes
ALTER TABLE formulario AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM formulario);

-- Otimizar tabela
OPTIMIZE TABLE formulario;

-- Verificar integridade
CHECK TABLE formulario;

-- Reparar se necessário
REPAIR TABLE formulario;

