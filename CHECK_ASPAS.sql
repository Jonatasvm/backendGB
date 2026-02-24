-- ============================================
-- VERIFICAR SE HÁ ASPAS NOS DADOS DO BANCO
-- ============================================

-- 1. Verificar se há aspas nos IDs
SELECT 
    id,
    CHAR_LENGTH(id) as tamanho,
    HEX(id) as hex_value,
    IF(id LIKE "'%", 'TEM ASPA NO INÍCIO', 'OK') as status_id
FROM formulario 
LIMIT 10;

-- 2. Verificar se há aspas nos valores (valor em centavos)
SELECT 
    id,
    valor,
    CHAR_LENGTH(valor) as tamanho,
    HEX(valor) as hex_value,
    IF(valor LIKE "'%", 'TEM ASPA NO INÍCIO', 'OK') as status_valor
FROM formulario 
WHERE valor IS NOT NULL
LIMIT 10;

-- 3. Verificar se há aspas nas datas
SELECT 
    id,
    data_pagamento,
    CHAR_LENGTH(data_pagamento) as tamanho,
    HEX(data_pagamento) as hex_value,
    IF(data_pagamento LIKE "'%", 'TEM ASPA NO INÍCIO', 'OK') as status_data
FROM formulario 
WHERE data_pagamento IS NOT NULL
LIMIT 10;

-- 4. Ver exemplos brutos de registros para debug
SELECT 
    id,
    valor,
    data_pagamento
FROM formulario 
LIMIT 5;
