# CHEAT SHEET - Estrutura BD em Uma Página

## 📊 TABELAS PRINCIPAIS

```
┌────────────────────────────────────────────────────────────────────┐
│ FORMULARIO (22 colunas)                                             │
├────────────────────────────────────────────────────────────────────┤
│ id, data_lancamento, solicitante, titular, referente               │
│ valor (CENTAVOS!), obra (FK), data_pagamento, forma_pagamento     │
│ lancado (Y/N/X/A), cpf_cnpj, chave_pix, data_competencia, carimbo │
│ observacao, conta (FK→bancos), categoria (FK),                    │
│ multiplos_lancamentos (0/1), grupo_lancamento (UUID[:8]),          │
│ fornecedor_novo (0/1), link_anexo, updated_at                      │
└────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ FORMULARIO_OBRAS (Junction)              │
├──────────────────────────────────────────┤
│ formulario_id (FK), obra_id (FK), valor  │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ BANCOS, CATEGORIA, FORNECEDOR, OBRAS     │
│ USERS, USERS_OBRAS                       │
└──────────────────────────────────────────┘
```

---

## 🔄 LANÇAMENTO MÚLTIPLO

```
Request: {"multiplos_lancamentos": 1, "obras_adicionais": [...]}
    ↓
✅ Gera grupo_lancamento (UUID[:8])
✅ Para CADA obra: INSERT formulario + INSERT formulario_obras
✅ Todos com mesmo grupo_lancamento e multiplos_lancamentos=1

Resultado:
  3 IDs em FORMULARIO (100, 101, 102) com grupo="abc123de"
  3 linhas em FORMULARIO_OBRAS
  Ao listar: mostra só 1° (ID 100) com "obras_relacionadas"
```

---

## ⚡ QUERIES ESSENCIAIS

```sql
-- Listar (mostra 1° de cada grupo)
SELECT f.* FROM (SELECT *, ROW_NUMBER() OVER 
  (PARTITION BY grupo_lancamento ORDER BY id) as rn 
  FROM formulario) f WHERE f.rn = 1;

-- Buscar grupo completo
SELECT * FROM formulario WHERE grupo_lancamento = 'abc123de';

-- Deletar grupo inteiro
DELETE FROM formulario WHERE grupo_lancamento = 'abc123de';

-- Ver todos os dados
SELECT f.*, o.nome FROM formulario f 
  LEFT JOIN obras o ON f.obra = o.id WHERE f.id = 100;

-- Valor em centavos → Reais
SELECT id, valor/100 as reais FROM formulario;
```

---

## 🎯 RELACIONAMENTOS (Foreign Keys)

| De | Para | Campo | Ação Delete |
|----|------|-------|------------|
| FORMULARIO | OBRAS | obra | NOT NULL |
| FORMULARIO | BANCOS | conta | SET NULL |
| FORMULARIO | CATEGORIA | categoria | SET NULL |
| FORMULARIO_OBRAS | FORMULARIO | formulario_id | CASCADE |
| FORMULARIO_OBRAS | OBRAS | obra_id | RESTRICT |
| USERS_OBRAS | USERS | user_id | CASCADE |
| USERS_OBRAS | OBRAS | obra_id | CASCADE |

---

## 📋 STATUS DE LANÇAMENTO

| Valor | Significado |
|-------|-------------|
| **Y** | Lançado (contabilizado) |
| **N** | Pendente (default) |
| **X** | Não autorizado (rejeitado) |
| **A** | Aprovado (não lançado) |

---

## 💰 CONVERSÃO: CENTAVOS ↔ REAIS

```
R$ 50,00 = 5000 centavos
R$ 0,10 = 10 centavos
R$ 1,00 = 100 centavos

BD: valor = 5000 (INT, sem decimais)
Frontend: valor / 100 = 50.00 (float, para exibir)
POST: valor = 5000 (já em centavos)
```

---

## 🆔 DUAS ESTRUTURAS DE MÚLTIPLO

### NOVA (Recomendada)
```
multiplos_lancamentos = 1
grupo_lancamento = "abc123de"  ← SEMPRE preenchido
Busca por grupo
✅ Seguro e determinístico
```

### ANTIGA (Legado)
```
multiplos_lancamentos = 1
grupo_lancamento = NULL
Busca por data + solicitante + titular
❌ Risco: pode encontrar lançamentos errados
```

---

## ✅ CHECKLIST: Criar Lançamento Múltiplo

- [ ] `multiplos_lancamentos = 1`
- [ ] `obras_adicionais` com lista de {obra_id, valor}
- [ ] `valor` = soma de todos os valores (em centavos)
- [ ] `grupo_lancamento` será gerado automaticamente
- [ ] Backend cria N registros em FORMULARIO
- [ ] Backend cria N registros em FORMULARIO_OBRAS
- [ ] Cascata: ao deletar, remove todos do grupo

---

## 🛑 CUIDADO!

```
❌ Deletar só 1 ID de um grupo de 3
   → Deixa lançamentos órfãos/inconsistentes

✅ Sempre deletar por grupo_lancamento
   DELETE FROM formulario WHERE grupo_lancamento = 'x'
```

---

## 📞 TROUBLESHOOTING RÁPIDO

```
"ID 100 não aparece na lista?"
→ Confira: multiplos_lancamentos=1 E grupo_lancamento='x'?
   Se sim: ID é do grupo, veja "obras_relacionadas"

"Valor não bate?"
→ Centavos! valor/100 para reais. 5000=R$50

"Não consigo deletar obra?"
→ Existem lançamentos fazendo referência (FK)

"Como encontrar lançamentos de um grupo?"
→ SELECT * FROM formulario WHERE grupo_lancamento = 'x'

"Qual é o total de um lançamento múltiplo?"
→ SUM(valor) de todos com mesmo grupo_lancamento
```

---

## 📚 DOCS COMPLETAS

1. **ESTRUTURA_BANCO_DADOS.md** → Definição SQL completa
2. **RESUMO_ESTRUTURA_BD.md** → Tabela de colunas + FAQ
3. **QUERIES_ESSENCIAIS.sql** → 25+ queries prontas
4. **DIAGRAMA_ER_DETALHADO.md** → Visualização + fluxos
5. **INDICE_COMPLETO.md** → Guia de referência

---

*Para imprimir em A4 ou guardar no celular*
*Referência rápida: estrutura do BD gerenciaobra*

