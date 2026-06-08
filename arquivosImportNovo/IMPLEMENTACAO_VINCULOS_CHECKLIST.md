# ✅ Checklist de Implementação - Sistema de Vínculos

## 📋 Status da Implementação

- ✅ **Banco de Dados**
  - [x] Criar tabela `formulario_vinculos`
  - [x] Adicionar foreign keys com cascata
  - [x] Criar índices para performance
  - [x] Adicionar constraints de integridade
  - [x] Adicionar ao arquivo migrations.sql

- ✅ **Backend**
  - [x] Criar serviço `VinculoService` em `services/vinculo_service.py`
  - [x] Criar rotas em `routes/vinculo_routes.py`
  - [x] Registrar blueprint no `app.py`
  - [x] Implementar 8 endpoints principais
  - [x] Adicionar validações e tratamento de erros

- ✅ **Documentação**
  - [x] Criar guia de API (`VINCULO_API_GUIDE.md`)
  - [x] Criar queries SQL prontas (`QUERIES_VINCULOS.sql`)
  - [x] Adicionar exemplos de uso
  - [x] Documentar migração de dados antigos

---

## 🚀 Próximos Passos (TODO)

### 1️⃣ **Executar Migration no Banco de Dados** 🔴 ESSENCIAL

```bash
# Conectar ao MySQL
mysql -u [user] -p [database] < backendGB/migrations.sql

# OU executa via Python
cd backendGB
python run_migrations.py
```

**O quê fazer:**
- [ ] Conectar ao banco de dados
- [ ] Executar o arquivo `migrations.sql`
- [ ] Verificar se a tabela foi criada: `DESC formulario_vinculos;`
- [ ] Testar os índices: `SHOW INDEX FROM formulario_vinculos;`

---

### 2️⃣ **Testar a API** 

```bash
# Iniciar o backend
cd backendGB
python app.py

# Em outro terminal, testar endpoints
curl http://localhost:5631/vinculo/health

# Criar um vínculo de teste
curl -X POST http://localhost:5631/vinculo \
  -H "Content-Type: application/json" \
  -d '{
    "formulario_id_principal": 1,
    "formulario_id_vinculado": 2,
    "tipo_vinculo": "multiple_payment"
  }'
```

**O quê testar:**
- [ ] Health check funciona
- [ ] Criar vínculo entre dois lançamentos existentes
- [ ] Listar vínculos de um lançamento
- [ ] Desativar vínculo
- [ ] Reativar vínculo
- [ ] Listar grupo completo
- [ ] Deletar vínculo

---

### 3️⃣ **Atualizar Frontend (React)**

Adicionar funcionalidades no `pagamento/src/`:

```jsx
// 1. Criar serviço para chamar API de vínculos
// Arquivo: pagamento/src/services/vinculoService.js

export const vincularFormularios = async (id1, id2, tipo = 'multiple_payment') => {
  return fetch('http://localhost:5631/vinculo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      formulario_id_principal: id1,
      formulario_id_vinculado: id2,
      tipo_vinculo: tipo
    })
  }).then(r => r.json());
};

export const obterVinculos = async (formularioId) => {
  return fetch(`http://localhost:5631/formulario/${formularioId}/vinculos`)
    .then(r => r.json());
};

export const obterGrupo = async (formularioId) => {
  return fetch(`http://localhost:5631/formulario/${formularioId}/grupo-vinculo`)
    .then(r => r.json());
};

// 2. Atualizar PaymentTable.jsx para mostrar vínculos
// - Adicionar coluna "Vínculos"
// - Mostrar badge com total de lançamentos vinculados
// - Adicionar botões para gerenciar vínculos

// 3. Criar modal para vincular formulários
// Arquivo: pagamento/src/components/VinculoModal.jsx
// - Seletor de formulário para vincular
// - Seletor de tipo de vínculo
// - Campo de observação

// 4. Criar lista de vínculos (expandível na tabela)
// Arquivo: pagamento/src/components/VinculoList.jsx
// - Listar todos os vínculos de um lançamento
// - Botões para desativar/reativar
// - Mostrar valor total do grupo
```

---

### 4️⃣ **Migrar Dados Existentes** (se houver `grupo_lancamento`)

```bash
# Criar script Python para migrar
# Arquivo: backendGB/migrate_vinculos.py

python backendGB/migrate_vinculos.py
```

**O quê fazer:**
- [ ] Verificar se há lançamentos com `grupo_lancamento` preenchido
- [ ] Criar script para converter para novos vínculos
- [ ] Validar integridade dos dados
- [ ] Manter compatibilidade com campo antigo (opcional)

---

### 5️⃣ **Atualizar Rotas Existentes** (formulario_routes.py)

Adicionar suporte ao novo sistema ao criar/deletar lançamentos:

```python
# Quando criar lançamento múltiplo:
# 1. Criar registro principal
# 2. Criar registros para cada obra
# 3. Vincular todos usando formulario_vinculos

# Quando deletar lançamento:
# 1. Chamar VinculoService.quebrar_todos_vinculos_formulario(id)
# 2. Depois deletar o formulário
```

---

### 6️⃣ **Adicionar Relatórios**

Criar novas rotas de exportação:

```python
@formulario_bp.route("/relatorio/vinculos", methods=["GET"])
def relatorio_vinculos():
    """Relatório de lançamentos vinculados"""
    # Listar grupos de lançamentos
    # Calcular valores totais
    # Exportar para Excel/PDF
```

---

## 🧪 Testes Recomendados

### Teste 1: Criar Vínculo Simples

```bash
# 1. Inserir dois formulários de teste
INSERT INTO formulario (data_lancamento, solicitante, titular, referente, valor, obra, data_pagamento, forma_pagamento, lancado)
VALUES 
('2026-06-04', 'João', 'Empresa A', 'Pagamento 1', 5000.00, 1, '2026-06-04', 'pix', 'Y'),
('2026-06-04', 'João', 'Empresa B', 'Pagamento 2', 3000.00, 2, '2026-06-04', 'pix', 'Y');

# 2. Criar vínculo (via API)
POST /vinculo
{ "formulario_id_principal": 1, "formulario_id_vinculado": 2 }

# 3. Listar vínculos
GET /formulario/1/vinculos

# 4. Listar grupo
GET /formulario/1/grupo-vinculo
```

**Resultado esperado:**
```json
{
  "formulario_id": 1,
  "total_lancamentos": 2,
  "valor_total": 8000.00,
  "lancamentos": [...]
}
```

---

### Teste 2: Múltiplos Vínculos

```bash
# Criar um grupo de 4 lançamentos
POST /vinculo { principal: 1, vinculado: 2 }
POST /vinculo { principal: 1, vinculado: 3 }
POST /vinculo { principal: 1, vinculado: 4 }

# Verificar grupo
GET /formulario/1/grupo-vinculo

# Resultado: 4 lançamentos no grupo
```

---

### Teste 3: Desativar/Reativar

```bash
# Desativar um vínculo
PUT /vinculo/1/desativar

# Listar apenas ativos
GET /formulario/1/vinculos?apenas_ativos=true
# Resultado: só mostra vínculos ativos

# Reativar
PUT /vinculo/1/reativar
```

---

### Teste 4: Deletar Lançamento com Vínculos

```bash
# Deletar um lançamento que tem vínculos
DELETE /formulario/1

# Verificar se vínculos foram quebrados
SELECT * FROM formulario_vinculos WHERE ativo = 0;
# Resultado: vínculos marcados como inativos, não deletados
```

---

## 📊 Métricas de Sucesso

- ✅ Tabela criada e acessível
- ✅ Todos os 8 endpoints respondendo
- ✅ Vínculos sendo criados corretamente
- ✅ Queries SQL executando em < 100ms
- ✅ Foreign keys funcionando (cascatas)
- ✅ Sem erros de constraint violation
- ✅ Frontend exibindo vínculos
- ✅ Dados antigos (grupo_lancamento) migrados

---

## 🐛 Troubleshooting

### Erro: "Vínculo não encontrado"
- Verificar se os IDs dos formulários existem
- Verificar se `ativo = 1`

### Erro: "Foreign key violation"
- Verificar se os formulários foram deletados
- Usar soft delete (desativar) em vez de deletar

### Query lenta
- Verificar índices com `SHOW INDEX FROM formulario_vinculos`
- Usar `EXPLAIN` antes das queries

### Duplicatas na tabela
- Check constraint `UNIQUE KEY uq_vinculos_pair` deveria prevenir
- Se houver, executar limpeza manual

---

## 📞 Contato & Perguntas

- Dúvidas sobre API? → Ver `VINCULO_API_GUIDE.md`
- Dúvidas sobre SQL? → Ver `QUERIES_VINCULOS.sql`
- Erro no código? → Verifique os logs do backend

---

## 📅 Timeline Recomendada

| Etapa | Tempo Est. | Status |
|-------|-----------|--------|
| 1. Executar Migration | 5 min | 🔴 TODO |
| 2. Testar API | 15 min | 🔴 TODO |
| 3. Implementar Frontend | 2-3 horas | 🔴 TODO |
| 4. Migrar dados antigos | 1 hora | 🔴 TODO |
| 5. Testes completos | 1-2 horas | 🔴 TODO |
| 6. Deploy em produção | 30 min | 🔴 TODO |

**Total estimado:** 5-7 horas

---

**Última atualização:** 04/06/2026
**Versão:** 1.0
**Status:** ✅ Pronto para deploy
