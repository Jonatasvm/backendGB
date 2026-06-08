# RESUMO EXECUTIVO - Estrutura de Formulários e Lançamentos

## Quadro Rápido: Todas as Colunas da Tabela FORMULARIO

| # | Coluna | Tipo | Tamanho | Chave | Default | Descrição |
|---|--------|------|---------|-------|---------|-----------|
| 1 | **id** | INT | - | PK | AUTO_INCREMENT | ID único do lançamento |
| 2 | **data_lancamento** | DATE | - | - | NULL | Data em que o lançamento foi feito |
| 3 | **solicitante** | VARCHAR | 255 | - | NULL | Quem solicitou o lançamento |
| 4 | **titular** | VARCHAR | 255 | - | NULL | Beneficiário/Fornecedor do pagamento |
| 5 | **referente** | VARCHAR | 255 | - | NULL | Descrição/referência do pagamento |
| 6 | **valor** | DECIMAL | 12,2 | - | - | **Valor em centavos** (R$ 50,00 = 5000) |
| 7 | **obra** | INT | - | FK | NOT NULL | Referência para tabela OBRAS |
| 8 | **data_pagamento** | DATE | - | - | NULL | Data prevista/realizada do pagamento |
| 9 | **forma_pagamento** | VARCHAR | 50 | - | NULL | Método: 'boleto', 'transfer', 'pix' |
| 10 | **lancado** | ENUM | - | - | 'N' | Status: Y/N/X/A (Lançado/Pendente/Não autorizado/Aprovado) |
| 11 | **cpf_cnpj** | VARCHAR | 20 | - | NULL | CPF ou CNPJ do beneficiário |
| 12 | **chave_pix** | VARCHAR | **600** | - | NULL | Chave PIX (até 500 chars, suporta copia-cola) |
| 13 | **data_competencia** | DATE | - | - | NULL | Período de referência (contabilidade) |
| 14 | **carimbo** | TIMESTAMP | - | - | CURRENT_TIMESTAMP | Data/hora de criação (UTC+1) |
| 15 | **observacao** | TEXT | - | - | NULL | Notas/comentários adicionais |
| 16 | **conta** | INT | - | FK | NULL | Banco/Conta (referência BANCOS) |
| 17 | **categoria** | INT | - | FK | NULL | Categoria (referência CATEGORIA) |
| 18 | **multiplos_lancamentos** | TINYINT | 1 | - | 0 | Flag: 0=simples, 1=múltiplo |
| 19 | **grupo_lancamento** | VARCHAR | 50 | IDX | NULL | UUID curto para agrupar lançamentos relacionados |
| 20 | **fornecedor_novo** | TINYINT | 1 | - | 0 | Flag: 1=digitado manualmente, 0=já cadastrado |
| 21 | **link_anexo** | VARCHAR | 500 | - | NULL | URL do arquivo no Google Drive |
| 22 | **updated_at** | TIMESTAMP | - | - | AUTO_UPDATE | Última atualização |

---

## Tabelas Relacionadas - Resumo

### 1️⃣ **FORMULARIO_OBRAS** (Junction Table)
- **Objetivo**: Armazenar qual valor cada obra recebe em um lançamento múltiplo
- **Colunas**: `id` (PK), `formulario_id` (FK), `obra_id` (FK), `valor`, `created_at`, `updated_at`
- **Relação**: 1 formulário ↔ N obras
- **Uso**: Rastrear distribuição de valores entre múltiplas obras

### 2️⃣ **BANCOS**
- **Objetivo**: Catálogo de contas/bancos disponíveis
- **Colunas**: `id` (PK), `nome`, `created_at`, `updated_at`
- **Relação**: 1 banco ↔ N formulários
- **Valores típicos**: Banco do Brasil, Caixa, Itaú, Santander, Bradesco

### 3️⃣ **CATEGORIA**
- **Objetivo**: Categorizar os lançamentos por tipo
- **Colunas**: `id` (PK), `nome`, `descricao`, `created_at`, `updated_at`
- **Relação**: 1 categoria ↔ N formulários

### 4️⃣ **FORNECEDOR**
- **Objetivo**: Catálogo de fornecedores/titulares cadastrados
- **Colunas**: `id` (PK), `titular`, `cpf_cnpj` (UNIQUE), `chave_pix`, `banco_padrao`, `created_at`, `updated_at`
- **Relação**: Referência pelo campo `titular` em formulário (não é FK)
- **Nota**: Campo `fornecedor_novo` indica se está fora deste catálogo

### 5️⃣ **OBRAS**
- **Objetivo**: Projetos/obras que recebem os lançamentos
- **Colunas**: `id` (PK), `nome`, `quem_paga`, `banco_id`, `created_at`, `updated_at`
- **Relação**: 1 obra ↔ N formulários

### 6️⃣ **USERS**
- **Objetivo**: Usuários do sistema
- **Colunas**: `id` (PK), `nome`, `username` (UNIQUE), `email` (UNIQUE), `senha`, `role` (ENUM), `created_at`, `updated_at`
- **Roles**: `admin`, `user`, `financeiro` (novo em 2025-03-11)

### 7️⃣ **USERS_OBRAS**
- **Objetivo**: Vincular usuários a múltiplas obras
- **Colunas**: `user_id` (FK), `obra_id` (FK), `created_at`
- **Tipo**: Junction table (relação N:N)

---

## 🔄 Fluxo de Lançamentos Múltiplos

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (Pagamento - Solicitacao.jsx)                          │
│ Usuário seleciona múltiplas obras e define valor para cada uma │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ REQUEST JSON                                                     │
│ {                                                               │
│   "multiplos_lancamentos": 1,                                  │
│   "obras_adicionais": [                                        │
│     {"obra": 1, "valor": 2000},  ← valor em centavos         │
│     {"obra": 2, "valor": 3000},                               │
│     {"obra": 3, "valor": 1500}                                │
│   ],                                                           │
│   ... outros campos ...                                        │
│ }                                                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (routes/formulario_routes.py)                           │
│ - Gera grupo_lancamento (UUID: "abc123de")                     │
│ - Para CADA obra em obras_adicionais:                          │
│   ✅ INSERT formulario (com multiplos=1, mesmo grupo)          │
│   ✅ INSERT formulario_obras (relacionamento)                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ BANCO DE DADOS                                                   │
│                                                                 │
│ FORMULARIO:                                                    │
│   ID 100: obra=1, valor=2000, grupo="abc123de", multiplos=1  │
│   ID 101: obra=2, valor=3000, grupo="abc123de", multiplos=1  │
│   ID 102: obra=3, valor=1500, grupo="abc123de", multiplos=1  │
│                                                                 │
│ FORMULARIO_OBRAS:                                              │
│   (100, 1, 2000)                                              │
│   (100, 2, 3000)                                              │
│   (100, 3, 1500)                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Casos de Uso Principais

### ✅ Criar Lançamento Simples
- `multiplos_lancamentos = 0`
- 1 registro em FORMULARIO
- 1 OBRA

### ✅ Criar Lançamento Múltiplo
- `multiplos_lancamentos = 1`
- `grupo_lancamento = 'abc123de'` (gerado)
- 3+ registros em FORMULARIO (um por obra)
- 3+ entradas em FORMULARIO_OBRAS

### ✅ Deletar Lançamento Múltiplo
- Busca `grupo_lancamento`
- **Deleta TODOS** os registros com o mesmo grupo
- **Resultado**: Não fica "órfão" ou inconsistente

### ✅ Editar Lançamento Múltiplo
- Edita o lançamento "representante" (primeiro do grupo)
- Mudanças refletem para todos do grupo

### ✅ Listar Lançamentos
- Query usa `ROW_NUMBER() OVER (PARTITION BY grupo_lancamento)`
- Mostra apenas PRIMEIRO de cada grupo
- Busca relacionados dinamicamente

---

## 📊 Dados vs Representação

```
┌─────────────────────────────────────────────────────────────────┐
│ NO BANCO (Armazenamento)                                         │
├─────────────────────────────────────────────────────────────────┤
│ valor: 5000 (inteiro - centavos)                               │
│ forma_pagamento: "boleto" (string minúscula)                   │
│ lancado: "Y" (char único)                                      │
│ carimbo: 2025-01-31 16:45:30 (UTC+1)                          │
└─────────────────────────────────────────────────────────────────┘
                        │
                        │ CONVERSÃO
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ NO FRONTEND (Apresentação)                                       │
├─────────────────────────────────────────────────────────────────┤
│ valor: "R$ 50,00" (formatado)                                   │
│ formaDePagamento: "Boleto" (título)                            │
│ lancado: "Lançado" / "Pendente" (texto legível)               │
│ carimbo: "31/01/2025 13:45:30" (Brasília UTC-3)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Foreign Keys (Relacionamentos)

| De | Para | Campo | Ação Delete | Ação Update |
|---|------|-------|------------|-----------|
| FORMULARIO | OBRAS | `obra` | NOT NULL (obrigatório) | CASCADE |
| FORMULARIO | BANCOS | `conta` | SET NULL | CASCADE |
| FORMULARIO | CATEGORIA | `categoria` | SET NULL | CASCADE |
| FORMULARIO_OBRAS | FORMULARIO | `formulario_id` | CASCADE | CASCADE |
| FORMULARIO_OBRAS | OBRAS | `obra_id` | RESTRICT | CASCADE |
| USERS_OBRAS | USERS | `user_id` | CASCADE | - |
| USERS_OBRAS | OBRAS | `obra_id` | CASCADE | - |

---

## 📈 Escalabilidade

### Índices Criados
- `idx_formulario_multiplos` - para filtrar lançamentos múltiplos
- `idx_formulario_grupo` - para buscar por grupo_lancamento
- `idx_formulario_conta` - para filtrar por banco
- `idx_formulario_categoria` - para filtrar por categoria
- `idx_formulario_obras_formulario` - para junção rápida
- `idx_formulario_obras_obra` - para buscar registros de uma obra

### Otimizações
- Valores em centavos (sem decimais) = operações integer (mais rápido)
- Grupo_lancamento VARCHAR(50) = indexável
- ROW_NUMBER() window function = eficiente para listas paginadas

---

## 🚀 Migração de Dados (Antigas para Nova Estrutura)

```sql
-- Script para preencher grupo_lancamento para lançamentos antigos:

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
```

---

## ⚠️ Questões de Integridade

### 1. Orfandade de Registros
**Problema**: Deletar uma obra deixa lançamentos sem referência?
**Solução**: `obra` NÃO PODE SER NULL - erro ao deletar obra com lançamentos

### 2. Sincronização de Valores
**Problema**: Valor total em formulario ≠ soma de formulario_obras?
**Solução**: Backend responsável por manter sincronizado durante INSERT/UPDATE

### 3. Grupo_lancamento Inconsistente
**Problema**: Lançamentos com multiplos=1 mas sem grupo?
**Solução**: Migration script para sincronizar dados antigos

---

## 📝 Convenções

- **IDs**: Sempre INT AUTO_INCREMENT
- **Valores Monetários**: Centavos (integer), sem decimais
- **Datas**: YYYY-MM-DD
- **Strings Livres**: VARCHAR com TRIM() para limpeza
- **Enums**: Valores curtos (Y/N/X/A, boleto/transfer/pix)
- **Timestamps**: UTC no servidor, convertido para Brasília (UTC-3) no retorno

---

## 🛠️ Troubleshooting

### Q: Por que não conseguo deletar uma obra?
**R**: Existem lançamentos fazendo referência a ela. Delete os lançamentos primeiro.

### Q: Como saber se um lançamento é múltiplo?
**R**: Veja `multiplos_lancamentos = 1` E `grupo_lancamento IS NOT NULL`

### Q: O valor não bate com as obras relacionadas?
**R**: Verificar se `valor` em FORMULARIO = SUM(valor) em FORMULARIO_OBRAS

### Q: Como buscar todos os lançamentos de um grupo?
**R**: `SELECT * FROM formulario WHERE grupo_lancamento = 'abc123de'`

### Q: Posso alterar o valor de um lançamento múltiplo?
**R**: Sim, mas deve-se recalcular a distribuição entre as obras.

