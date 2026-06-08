# Diagrama ER - Relacionamentos Completos

## 🗂️ Estrutura Visual Completa

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                          BANCO DE DADOS: GERENCIAOBRA                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────────────────┐
│                                    USERS                                    │
├────────────────────────────────────────────────────────────────────────────┤
│ PK  id            INT AUTO_INCREMENT                                       │
│     nome          VARCHAR(255)                                             │
│     username      VARCHAR(255) UNIQUE                                      │
│     email         VARCHAR(255) UNIQUE                                      │
│     senha         VARCHAR(255)                                             │
│     role          ENUM('admin', 'user', 'financeiro') DEFAULT 'user'      │
│     created_at    TIMESTAMP                                                │
│     updated_at    TIMESTAMP AUTO_UPDATE                                    │
└────────────────────────────────────────────────────────────────────────────┘
                                      ▲
                                      │ (N:N Junction)
                                      │
                  ┌───────────────────┴───────────────────┐
                  │                                       │
┌────────────────────────────────────────┐  ┌─────────────────────────────────┐
│        USERS_OBRAS (Junction)          │  │           OBRAS                 │
├────────────────────────────────────────┤  ├─────────────────────────────────┤
│ FK  user_id      INT                   │  │ PK  id          INT              │
│ FK  obra_id      INT                   │  │     nome        VARCHAR(255)    │
│     created_at   TIMESTAMP             │  │     quem_paga   VARCHAR(255)    │
│                                        │  │     banco_id    INT (FK optional)
│ PK  (user_id, obra_id)                │  │     created_at  TIMESTAMP       │
│                                        │  │     updated_at  TIMESTAMP       │
└────────────────────────────────────────┘  └────────┬────────────────────────┘
                                                     │
                                                     │ 1:N
                                                     │
                                ┌────────────────────┴──────────────────────┐
                                │                                           │
┌───────────────────────────────▼────────────────────────────────┐          │
│                          FORMULARIO                             │          │
├────────────────────────────────────────────────────────────────┤          │
│ PK  id                    INT AUTO_INCREMENT                   │          │
│     data_lancamento       DATE                                 │          │
│     solicitante           VARCHAR(255)                         │          │
│     titular               VARCHAR(255)                         │          │
│     referente             VARCHAR(255)                         │          │
│     valor                 DECIMAL(12,2)  ◄─── CENTAVOS        │          │
│ FK  obra                  INT NOT NULL   ─────────────────────┼──────────┘
│     data_pagamento        DATE                                 │
│     forma_pagamento       VARCHAR(50)                          │
│     lancado               ENUM('Y','N','X','A')               │
│     cpf_cnpj              VARCHAR(20)                          │
│     chave_pix             VARCHAR(600)  ◄─── PIX até 500 chars │
│     data_competencia      DATE                                 │
│     carimbo               TIMESTAMP  ◄─── UTC+1 no servidor    │
│     observacao            TEXT                                 │
│ FK  conta                 INT  ─────────────┐                 │
│ FK  categoria             INT  ─────────────┤                 │
│     multiplos_lancamentos TINYINT(1)       │                  │
│     grupo_lancamento      VARCHAR(50)      │                  │
│     fornecedor_novo       TINYINT(1)       │                  │
│     link_anexo            VARCHAR(500)     │                  │
│     updated_at            TIMESTAMP        │                  │
└────────────────────────────────────────────┼──────────────────┘
                        ▲                     │
                        │ 1:N                 │
                        │                     │
         ┌──────────────┤                     │
         │              │                     │
         │              └─────────────┬───────┘
         │                            │
    ┌────┴────────────────┐  ┌───────▼──────────────────────┐
    │     FORMULARIO_OBRAS│  │       BANCOS                 │
    ├─────────────────────┤  ├──────────────────────────────┤
    │ PK  id        INT    │  │ PK  id       INT             │
    │ FK  formulario_id    │  │     nome     VARCHAR(255)   │
    │ FK  obra_id   ◄──────┼──┤     created_at TIMESTAMP    │
    │     valor            │  │     updated_at TIMESTAMP    │
    │     created_at       │  └──────────────────────────────┘
    │     updated_at       │
    └─────────────────────┘
                            
                        ┌──────────────┐
                        │  CATEGORIA   │
                        ├──────────────┤
                        │ PK  id    INT│
                        │     nome  VAR│
                        │     descri..│
                        │     created  │
                        │     updated  │
                        └──────────────┘

                      ┌──────────────┐
                      │  FORNECEDOR  │
                      ├──────────────┤
                      │ PK  id    INT│
                      │     titular  │
                      │     cpf_cnpj │
                      │     chave_pix│
                      │     banco... │
                      │     created  │
                      │     updated  │
                      └──────────────┘
```

---

## 📊 Fluxo de Dados - Lançamento Múltiplo Detalhado

```
ENTRADA DO FRONTEND
═══════════════════════════════════════════════════════════════════════════

User clica em "Novo Lançamento"
    ↓
Preench dados:
  - Titular: "FORNECEDOR SA"
  - CPF/CNPJ: "12345678000195"
  - Referente: "Material de construção"
  - Total: R$ 65,00 (6500 centavos)
    ↓
Seleciona "Múltiplos Lançamentos"
    ↓
Adiciona obras:
  ┌─────────────────────────────┐
  │ Obra 1 (Construção A): R$ 20│
  │ Obra 2 (Construção B): R$ 30│
  │ Obra 3 (Reformas):     R$ 15│
  └─────────────────────────────┘
    ↓
Frontend envia JSON:
{
  "multiplos_lancamentos": 1,
  "obras_adicionais": [
    {"obra": 1, "valor": 2000},   ← centavos
    {"obra": 2, "valor": 3000},
    {"obra": 3, "valor": 1500}
  ],
  "titular": "FORNECEDOR SA",
  "cpf_cnpj": "12345678000195",
  "referente": "Material de construção",
  "valor": 6500,                  ← total em centavos
  "data_lancamento": "2025-01-31",
  "forma_pagamento": "boleto",
  "categoria": 2,
  "conta": 1
}


PROCESSAMENTO NO BACKEND (formulario_routes.py)
═══════════════════════════════════════════════════════════════════════════

1️⃣  Validação
    ├─ Campos obrigatórios: ✅
    ├─ Valores numéricos: ✅
    └─ Obras existem: ✅

2️⃣  Gerar grupo_lancamento
    └─ grupo_lancamento = UUID[:8] = "abc123de"

3️⃣  Para CADA obra em obras_adicionais:
    
    OBRA 1 (Construção A, valor: 2000):
    ├─ INSERT FORMULARIO:
    │  ├─ id: 100
    │  ├─ obra: 1
    │  ├─ valor: 2000
    │  ├─ grupo_lancamento: "abc123de"
    │  ├─ multiplos_lancamentos: 1
    │  ├─ ... outros campos ...
    │  └─ carimbo: NOW() (UTC+1)
    │
    └─ INSERT FORMULARIO_OBRAS:
       ├─ formulario_id: 100
       ├─ obra_id: 1
       └─ valor: 2000

    OBRA 2 (Construção B, valor: 3000):
    ├─ INSERT FORMULARIO:
    │  ├─ id: 101
    │  ├─ obra: 2
    │  ├─ valor: 3000
    │  ├─ grupo_lancamento: "abc123de"
    │  └─ ...
    │
    └─ INSERT FORMULARIO_OBRAS:
       ├─ formulario_id: 101
       ├─ obra_id: 2
       └─ valor: 3000

    OBRA 3 (Reformas, valor: 1500):
    ├─ INSERT FORMULARIO:
    │  ├─ id: 102
    │  ├─ obra: 3
    │  ├─ valor: 1500
    │  ├─ grupo_lancamento: "abc123de"
    │  └─ ...
    │
    └─ INSERT FORMULARIO_OBRAS:
       ├─ formulario_id: 102
       ├─ obra_id: 3
       └─ valor: 1500

4️⃣  COMMIT todas as transações


ESTADO FINAL NO BANCO DE DADOS
═══════════════════════════════════════════════════════════════════════════

TABLE: FORMULARIO
┌────┬──────────────────┬─────┬──────────────────────┬──────────────┐
│ id │ data_lancamento  │obra │ grupo_lancamento     │ multiplos    │
├────┼──────────────────┼─────┼──────────────────────┼──────────────┤
│100 │ 2025-01-31       │  1  │ abc123de             │  1           │
│101 │ 2025-01-31       │  2  │ abc123de             │  1           │
│102 │ 2025-01-31       │  3  │ abc123de             │  1           │
└────┴──────────────────┴─────┴──────────────────────┴──────────────┘
        (todos os outros campos iguais)

TABLE: FORMULARIO_OBRAS
┌──────────────────┬──────────┬────────┐
│ formulario_id    │ obra_id  │ valor  │
├──────────────────┼──────────┼────────┤
│      100         │    1     │ 2000   │
│      101         │    2     │ 3000   │
│      102         │    3     │ 1500   │
└──────────────────┴──────────┴────────┘


QUANDO O FRONTEND LISTA OS LANÇAMENTOS
═══════════════════════════════════════════════════════════════════════════

Query (com ROW_NUMBER):
┌──────────────────────────────────────────────────────────────┐
│ SELECT f.* FROM (                                            │
│   SELECT *,                                                  │
│          ROW_NUMBER() OVER (PARTITION BY grupo_lancamento   │
│                             ORDER BY id ASC) as rn           │
│   FROM formulario                                            │
│ ) f                                                          │
│ WHERE f.rn = 1                                              │
│ ORDER BY f.id DESC                                          │
└──────────────────────────────────────────────────────────────┘

Resultado MOSTRADO ao usuário:
┌────────────────────────────────────────────────────────────────┐
│ ID 100: Construção A                                           │
│ Data: 31/01/2025                                              │
│ Valor: R$ 20,00 (representa o grupo inteiro)                 │
│ Obras Relacionadas:                                           │
│   • Construção B: R$ 30,00 (ID 101)                          │
│   • Reformas: R$ 15,00 (ID 102)                              │
│ Valor Total do Grupo: R$ 65,00                               │
└────────────────────────────────────────────────────────────────┘

(IDs 101 e 102 não aparecem na lista, só em "Obras Relacionadas")


QUANDO DELETA UM LANÇAMENTO DO GRUPO
═══════════════════════════════════════════════════════════════════════════

User clica DELETE no ID 100
    ↓
Backend:
  1. Lê: SELECT grupo_lancamento FROM formulario WHERE id = 100
     └─ Resultado: "abc123de"
  
  2. Busca TODOS com este grupo:
     SELECT id FROM formulario WHERE grupo_lancamento = "abc123de"
     └─ Resultado: [100, 101, 102]
  
  3. Deleta TODOS:
     DELETE FROM formulario WHERE grupo_lancamento = "abc123de"
     └─ Deleta linhas 100, 101, 102
  
  4. Cascata automática:
     FORMULARIO_OBRAS: Deleta registros com formulario_id IN (100,101,102)
     └─ Remove os 3 registros de relacionamento

Resultado:
  ✅ Banco fica consistente
  ✅ Nenhum registro órfão
  ✅ Nenhuma referência perdida


QUANDO EDITA UM LANÇAMENTO DO GRUPO
═══════════════════════════════════════════════════════════════════════════

User clica EDITAR no ID 100 (representante do grupo)
    ↓
Frontend carrega dados e oferece edição
    ↓
Backend UPDATE:
  ├─ Se alterar campo comum (forma_pagamento, categoria, conta):
  │  └─ Atualiza TODOS com o mesmo grupo_lancamento
  │
  └─ Se alterar valor/obra:
     └─ Atualiza apenas o específico (ID 100)

Mantém integridade: Cada registro pode ter seu próprio valor/obra,
mas informações compartilhadas são sincronizadas no grupo.


COMPARAÇÃO: MÚLTIPLO ANTIGO (sem grupo_lancamento)
═══════════════════════════════════════════════════════════════════════════

Quando grupo_lancamento = NULL mas multiplos_lancamentos = 1:

Backend busca por:
  ├─ data_lancamento = "2025-01-31"
  ├─ solicitante = "joao"
  └─ titular = "FORNECEDOR SA"

Se encontra 3 registros com estes critérios:
  ├─ ID 50: obra=1
  ├─ ID 51: obra=2
  └─ ID 52: obra=3

Função como um "grupo dinâmico", mas RISCO:
  ❌ Se adicionar mais lançamentos com mesma data+solicitante+titular
     → Serão considerados do mesmo "grupo" (falso positivo)
  ❌ Se alterar data/solicitante
     → Perde a relação com os outros do antigo "grupo"

SOLUÇÃO: Migration script para preencher grupo_lancamento
```

---

## 🔍 Queries Correlatas - Busca de Relacionamentos

```sql
/* EXEMPLO 1: Ver um lançamento múltiplo completo */
SELECT 
    f.id as form_id,
    f.data_lancamento,
    f.titular,
    f.valor / 100 as valor_reais,
    f.forma_pagamento,
    f.grupo_lancamento,
    COUNT(*) OVER (PARTITION BY f.grupo_lancamento) as qtd_obras,
    SUM(f.valor) OVER (PARTITION BY f.grupo_lancamento) / 100 as valor_total_grupo,
    o.nome as obra
FROM formulario f
LEFT JOIN obras o ON f.obra = o.id
WHERE f.grupo_lancamento = 'abc123de'
ORDER BY f.id;

Resultado:
┌────────┬──────────────────┬────────────┬──────────┬──────────┬──────────┐
│form_id │ data_lancamento  │  titular   │  valor   │grupo_lnc │ obra     │
├────────┼──────────────────┼────────────┼──────────┼──────────┼──────────┤
│  100   │ 2025-01-31       │ FORNECEDOR │ 20,00    │abc123de  │ Const A  │
│  101   │ 2025-01-31       │ FORNECEDOR │ 30,00    │abc123de  │ Const B  │
│  102   │ 2025-01-31       │ FORNECEDOR │ 15,00    │abc123de  │ Reformas │
└────────┴──────────────────┴────────────┴──────────┴──────────┴──────────┘


/* EXEMPLO 2: Verificar valor total vs. distribuição */
SELECT 
    f.id,
    f.valor / 100 as valor_em_formulario,
    (SELECT SUM(valor) / 100 
     FROM formulario_obras 
     WHERE formulario_id = f.id) as valor_em_obras
FROM formulario
WHERE grupo_lancamento = 'abc123de';

Resultado (deve ser igual):
┌────┬──────────────────────┬────────────────────┐
│id  │ valor_em_formulario  │ valor_em_obras     │
├────┼──────────────────────┼────────────────────┤
│100 │ 20,00                │ 20,00              │
│101 │ 30,00                │ 30,00              │
│102 │ 15,00                │ 15,00              │
└────┴──────────────────────┴────────────────────┘


/* EXEMPLO 3: Rastrear distribuição de um pagamento */
SELECT 
    f.grupo_lancamento,
    o.nome as obra_recebeu,
    fo.valor / 100 as valor_recebido,
    f.titular as pagador,
    f.referente as descricao,
    f.forma_pagamento
FROM formulario_obras fo
JOIN formulario f ON fo.formulario_id = f.id
JOIN obras o ON fo.obra_id = o.id
WHERE f.grupo_lancamento = 'abc123de'
ORDER BY fo.obra_id;

Resultado:
┌──────────┬──────────┬──────────────┬──────────┬────────────────────┬──────────┐
│ grupo... │ obra...  │ valor_receb  │ pagador  │ descricao          │ forma... │
├──────────┼──────────┼──────────────┼──────────┼────────────────────┼──────────┤
│abc123de  │ Const A  │ 20,00        │FORNECEDOR│ Material construção│ boleto   │
│abc123de  │ Const B  │ 30,00        │FORNECEDOR│ Material construção│ boleto   │
│abc123de  │ Reformas │ 15,00        │FORNECEDOR│ Material construção│ boleto   │
└──────────┴──────────┴──────────────┴──────────┴────────────────────┴──────────┘
```

---

## 🎯 Matriz de Decisão: Como Usar

```
┌──────────────────────────────────────────────────────────────────┐
│ ESTOU CRIANDO UM LANÇAMENTO PARA...                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 1 OBRA ÚNICA (ex: Pagar fornecedor por reforma em uma obra)     │
│    ├─ multiplos_lancamentos: 0                                  │
│    ├─ grupo_lancamento: NULL                                    │
│    ├─ 1 registro em FORMULARIO                                  │
│    └─ 0 registros em FORMULARIO_OBRAS                           │
│                                                                  │
│ MÚLTIPLAS OBRAS (ex: Dividir pagamento de material entre 3 obras)
│    ├─ multiplos_lancamentos: 1                                  │
│    ├─ grupo_lancamento: "uuid[:8]" ← GERADO                    │
│    ├─ 3 registros em FORMULARIO (um por obra)                  │
│    └─ 3 registros em FORMULARIO_OBRAS                          │
│                                                                  │
│ OBRAS RELACIONADAS JÁ EXISTEM (lançamentos antigos)            │
│    ├─ multiplos_lancamentos: 1                                  │
│    ├─ grupo_lancamento: NULL                                    │
│    ├─ Sistema busca por data+solicitante+titular               │
│    └─ ⚠️ RISCO: Pode ter falsos positivos                      │
│       (USAR MIGRATION SCRIPT PARA POPULAR GRUPOS)              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│ ESTOU BUSCANDO LANÇAMENTOS                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ LISTAR TODOS (Dashboard)                                        │
│    └─ Query com ROW_NUMBER() → mostra 1° de cada grupo         │
│       + carrega "obras_relacionadas" dinamicamente              │
│                                                                  │
│ DETALHES DE UM LANÇAMENTO                                       │
│    ├─ Se tem grupo_lancamento:                                 │
│    │  └─ SELECT * FROM formulario WHERE grupo = ...            │
│    └─ Se não tem grupo:                                        │
│       └─ SELECT * FROM formulario WHERE id = ...               │
│                                                                  │
│ RESUMO POR OBRA                                                 │
│    └─ SELECT obra, SUM(valor), COUNT(*)                        │
│       FROM formulario GROUP BY obra                            │
│                                                                  │
│ DISTRIBUIÇÃO DE PAGAMENTO (qual obra recebeu quanto)          │
│    └─ SELECT * FROM formulario_obras WHERE formulario_id = ...│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│ ESTOU ALTERANDO UM LANÇAMENTO                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ LANÇAMENTO SIMPLES (multiplos_lancamentos = 0)                  │
│    └─ UPDATE formulario WHERE id = ...                         │
│       (afeta apenas 1 registro)                                │
│                                                                  │
│ LANÇAMENTO MÚLTIPLO (multiplos_lancamentos = 1)                │
│    ├─ Campo único do pagamento (ex: categoria, conta):        │
│    │  └─ UPDATE todos com mesmo grupo_lancamento              │
│    │     (ex: "UPDATE ... WHERE grupo_lancamento = ...")      │
│    │                                                           │
│    └─ Campo específico da obra (ex: valor, obra):             │
│       └─ UPDATE apenas o registro específico                  │
│          (ex: "UPDATE ... WHERE id = ...")                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│ ESTOU DELETANDO UM LANÇAMENTO                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ LANÇAMENTO SIMPLES                                              │
│    └─ DELETE FROM formulario WHERE id = ...                   │
│       Cascata automática: nada em FORMULARIO_OBRAS (não há)   │
│                                                                  │
│ LANÇAMENTO MÚLTIPLO (com grupo_lancamento)                     │
│    ├─ 1. SELECT grupo_lancamento FROM formulario WHERE id = ..│
│    ├─ 2. DELETE FROM formulario WHERE grupo_lancamento = ...  │
│    └─ Cascata: Deleta automaticamente de FORMULARIO_OBRAS     │
│       ✅ Resultado: grupo inteiro deletado                    │
│                                                                  │
│ LANÇAMENTO MÚLTIPLO ANTIGO (sem grupo_lancamento)             │
│    ├─ Deve-se deletar TODOS com mesma data+solicitante+titular
│    └─ ⚠️ RISCO: Pode deletar lançamentos que não queria      │
│       (usar grupo_lancamento para evitar!)                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

