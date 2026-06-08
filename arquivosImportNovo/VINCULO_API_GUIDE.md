# 🔗 API de Vínculos de Lançamentos - Documentação

## Visão Geral

Este serviço gerencia vínculos entre múltiplos lançamentos (formulários) de forma robusta e com boas práticas.

**Principais características:**
- ✅ Criar, consultar, atualizar e deletar vínculos
- ✅ Soft delete (desativar) para manter histórico
- ✅ Boolean `ativo` para queries rápidas
- ✅ Tipos de vínculo predefinidos
- ✅ Foreign keys com cascata inteligente
- ✅ Índices para performance
- ✅ Constraint para evitar duplicatas

---

## 📊 Estrutura da Tabela

```sql
CREATE TABLE formulario_vinculos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  formulario_id_principal INT NOT NULL,
  formulario_id_vinculado INT NOT NULL,
  tipo_vinculo ENUM('multiple_payment', 'adjustment', 'reversal', 'split', 'other'),
  ativo TINYINT(1) DEFAULT 1,  -- BOOLEAN: 1=ativo, 0=inativo
  observacao TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (formulario_id_principal) REFERENCES formulario(id) ON DELETE CASCADE,
  FOREIGN KEY (formulario_id_vinculado) REFERENCES formulario(id) ON DELETE CASCADE,
  
  CONSTRAINT chk_vinculos_diferentes CHECK (formulario_id_principal != formulario_id_vinculado),
  UNIQUE KEY uq_vinculos_pair (LEAST(...), GREATEST(...), tipo_vinculo)
)
```

---

## 🔌 Endpoints da API

### 1. **Criar Vínculo** `POST /vinculo`

Vincular dois lançamentos

```bash
curl -X POST http://localhost:5631/vinculo \
  -H "Content-Type: application/json" \
  -d '{
    "formulario_id_principal": 1,
    "formulario_id_vinculado": 2,
    "tipo_vinculo": "multiple_payment",
    "observacao": "Lançamento dividido em 2 obras"
  }'
```

**Response:**
```json
{
  "id": 15,
  "message": "Vínculo criado com sucesso"
}
```

**Tipos de Vínculo:**
- `multiple_payment`: Lançamento dividido em múltiplas obras
- `adjustment`: Ajuste/correção de lançamento anterior
- `reversal`: Reversão/cancelamento
- `split`: Divisão de pagamento
- `other`: Outro tipo

---

### 2. **Obter Vínculos** `GET /formulario/<id>/vinculos`

Listar todos os vínculos de um lançamento

```bash
curl http://localhost:5631/formulario/1/vinculos?apenas_ativos=true
```

**Response:**
```json
{
  "formulario_id": 1,
  "total_vinculos": 2,
  "vinculos": [
    {
      "id": 15,
      "formulario_id_principal": 1,
      "formulario_id_vinculado": 2,
      "formulario_id_outro": 2,
      "tipo_vinculo": "multiple_payment",
      "ativo": 1,
      "referente": "Pagamento Obra 2",
      "valor": 5000.50,
      "obra": 2,
      "observacao": "Lançamento dividido em 2 obras"
    }
  ]
}
```

---

### 3. **Desativar Vínculo** `PUT /vinculo/<id>/desativar`

Soft delete de um vínculo (mantém no banco, marca como inativo)

```bash
curl -X PUT http://localhost:5631/vinculo/15/desativar
```

**Response:**
```json
{
  "message": "Vínculo desativado com sucesso"
}
```

---

### 4. **Reativar Vínculo** `PUT /vinculo/<id>/reativar`

Reativar um vínculo desativado

```bash
curl -X PUT http://localhost:5631/vinculo/15/reativar
```

---

### 5. **Deletar Vínculo** `DELETE /vinculo/<id>`

Hard delete de um vínculo (remove permanentemente)

```bash
curl -X DELETE http://localhost:5631/vinculo/15
```

---

### 6. **Atualizar Observação** `PUT /vinculo/<id>/observacao`

Atualizar a observação de um vínculo

```bash
curl -X PUT http://localhost:5631/vinculo/15/observacao \
  -H "Content-Type: application/json" \
  -d '{
    "observacao": "Vínculo ajustado em 04/06/2026"
  }'
```

---

### 7. **Listar Grupo Completo** `GET /formulario/<id>/grupo-vinculo`

Listar TODOS os lançamentos vinculados a um lançamento

```bash
curl http://localhost:5631/formulario/1/grupo-vinculo
```

**Response:**
```json
{
  "formulario_id": 1,
  "total_lancamentos": 3,
  "valor_total": 15000.50,
  "lancamentos": [
    {
      "id": 1,
      "referente": "Pagamento Obra 1",
      "valor": 5000.50,
      "obra": 1,
      "data_pagamento": "2026-06-04"
    },
    {
      "id": 2,
      "referente": "Pagamento Obra 2",
      "valor": 5000.00,
      "obra": 2,
      "data_pagamento": "2026-06-04"
    },
    {
      "id": 3,
      "referente": "Pagamento Obra 3",
      "valor": 5000.00,
      "obra": 3,
      "data_pagamento": "2026-06-04"
    }
  ]
}
```

---

### 8. **Quebrar Vínculos** `POST /formulario/<id>/quebrar-vinculos`

Desativar TODOS os vínculos de um lançamento (usado quando deletando)

```bash
curl -X POST http://localhost:5631/formulario/1/quebrar-vinculos
```

**Response:**
```json
{
  "quebrados": 2
}
```

---

## 🎯 Casos de Uso

### Caso 1: Lançamento com Múltiplas Obras

**Situação:** Usuário quer dividir R$ 15.000 em 3 obras

**Fluxo:**

```python
# 1. Criar 3 lançamentos (um para cada obra)
POST /formulario com obra=1, valor=5000
POST /formulario com obra=2, valor=5000
POST /formulario com obra=3, valor=5000
# IDs retornados: 1, 2, 3

# 2. Vincular os lançamentos
POST /vinculo
{
  "formulario_id_principal": 1,
  "formulario_id_vinculado": 2,
  "tipo_vinculo": "multiple_payment",
  "observacao": "Dividido em 3 obras"
}

POST /vinculo
{
  "formulario_id_principal": 1,
  "formulario_id_vinculado": 3,
  "tipo_vinculo": "multiple_payment",
  "observacao": "Dividido em 3 obras"
}

# 3. Visualizar o grupo completo
GET /formulario/1/grupo-vinculo
# Retorna todos os 3 lançamentos com valor total
```

---

### Caso 2: Ajuste/Correção

**Situação:** Lançamento foi feito com valor errado, precisa ajustar

```python
# 1. Deletar o lançamento errado (ID 100)
DELETE /formulario/100

# 2. Criar novo lançamento com valor correto (ID 101)
POST /formulario com valor=5500

# 3. Se era múltiplo, vincular ao original
POST /vinculo
{
  "formulario_id_principal": 1,
  "formulario_id_vinculado": 101,
  "tipo_vinculo": "adjustment",
  "observacao": "Correção de valor - era 5000, agora 5500"
}
```

---

### Caso 3: Reversão/Cancelamento

**Situação:** Pagamento foi feito por engano, precisa reverter

```python
# 1. Criar lançamento de reversão (valor negativo)
POST /formulario com valor=-5000, referente="Reversão de pagamento"
# ID retornado: 102

# 2. Vincular ao lançamento original
POST /vinculo
{
  "formulario_id_principal": 1,
  "formulario_id_vinculado": 102,
  "tipo_vinculo": "reversal",
  "observacao": "Reversão de pagamento de 04/06/2026"
}
```

---

## 📋 Queries SQL Úteis

### Buscar Todas as Vinculações Ativas

```sql
SELECT 
  v.id,
  v.formulario_id_principal,
  v.formulario_id_vinculado,
  v.tipo_vinculo,
  f1.referente as principal_referente,
  f1.valor as principal_valor,
  f2.referente as vinculado_referente,
  f2.valor as vinculado_valor
FROM formulario_vinculos v
JOIN formulario f1 ON v.formulario_id_principal = f1.id
JOIN formulario f2 ON v.formulario_id_vinculado = f2.id
WHERE v.ativo = 1
ORDER BY v.created_at DESC;
```

### Contar Vinculos por Tipo

```sql
SELECT 
  tipo_vinculo,
  COUNT(*) as total,
  SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) as ativos
FROM formulario_vinculos
GROUP BY tipo_vinculo;
```

### Listar Lançamentos Órfãos (sem vínculo)

```sql
SELECT f.id, f.referente, f.valor
FROM formulario f
LEFT JOIN formulario_vinculos v ON (
  (f.id = v.formulario_id_principal OR f.id = v.formulario_id_vinculado)
  AND v.ativo = 1
)
WHERE v.id IS NULL
ORDER BY f.id DESC;
```

### Buscar Grupos de Lançamentos

```sql
SELECT 
  CASE 
    WHEN formulario_id_principal < formulario_id_vinculado 
    THEN formulario_id_principal
    ELSE formulario_id_vinculado
  END as grupo_principal,
  COUNT(*) as total_vinculos,
  GROUP_CONCAT(DISTINCT CASE WHEN formulario_id_principal = grupo_principal THEN formulario_id_principal ELSE formulario_id_vinculado END) as ids
FROM formulario_vinculos
WHERE ativo = 1
GROUP BY grupo_principal
HAVING COUNT(*) > 0
ORDER BY total_vinculos DESC;
```

---

## ⚙️ Integração no Frontend

### Exemplo React para vincular formulários

```jsx
// Vincular dois lançamentos
async function vincularFormularios(id1, id2) {
  const response = await fetch('http://localhost:5631/vinculo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      formulario_id_principal: id1,
      formulario_id_vinculado: id2,
      tipo_vinculo: 'multiple_payment',
      observacao: 'Dividido em múltiplas obras'
    })
  });
  return response.json();
}

// Obter vínculos de um lançamento
async function obterVinculos(formularioId) {
  const response = await fetch(
    `http://localhost:5631/formulario/${formularioId}/vinculos?apenas_ativos=true`
  );
  return response.json();
}

// Listar grupo completo
async function obterGrupoCompleto(formularioId) {
  const response = await fetch(
    `http://localhost:5631/formulario/${formularioId}/grupo-vinculo`
  );
  return response.json();
}
```

---

## 🚀 Migrando do Sistema Antigo

Se você tem lançamentos já vinculados via `grupo_lancamento`, pode migrar:

```sql
-- 1. Criar vínculos a partir de grupo_lancamento existentes
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
GROUP BY f1.grupo_lancamento, f2.id;

-- 2. Verificar migração
SELECT COUNT(*) as total_vinculos FROM formulario_vinculos;

-- 3. Manter grupo_lancamento para compatibilidade (opcional)
-- Depois pode dropar a coluna se não usar mais
```

---

## 📞 Suporte

Dúvidas ou bugs? Verifique:
- Logs do backend em `backendGB/`
- Status da API: `GET /vinculo/health`
- Erros de foreign key nas constraints

