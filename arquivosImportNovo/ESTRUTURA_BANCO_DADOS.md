# Estrutura Completa do Banco de Dados - Gerência de Obras

## Tabela Principal: FORMULARIO

```sql
CREATE TABLE formulario (
  id INT AUTO_INCREMENT PRIMARY KEY,
  data_lancamento DATE,
  solicitante VARCHAR(255),
  titular VARCHAR(255),
  referente VARCHAR(255),
  valor DECIMAL(12, 2) NOT NULL,                          -- Valor em centavos
  obra INT NOT NULL,                                      -- FK para tabela obras
  data_pagamento DATE,
  forma_pagamento VARCHAR(50),                            -- Exemplo: 'boleto', 'transfer', 'pix'
  lancado ENUM('Y', 'N', 'X', 'A') DEFAULT 'N',          -- Y=Lançado, N=Pendente, X=Não autorizado, A=Aprovado
  cpf_cnpj VARCHAR(20),
  chave_pix VARCHAR(600),                                 -- PIX - até 500 chars (hibrido/copia-cola)
  data_competencia DATE,
  carimbo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,            -- Data/hora de criação
  observacao TEXT,
  conta INT DEFAULT NULL,                                 -- FK para tabela bancos
  categoria INT DEFAULT NULL,                             -- FK para tabela categoria
  multiplos_lancamentos TINYINT(1) DEFAULT 0,            -- Flag: 0=simples, 1=múltiplo
  grupo_lancamento VARCHAR(50) DEFAULT NULL,             -- UUID curto para agrupar lançamentos relacionados
  fornecedor_novo TINYINT(1) DEFAULT 0,                  -- Flag: 1=fornecedor digitado manualmente
  link_anexo VARCHAR(500) DEFAULT NULL,                  -- Link de arquivo no Google Drive
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  -- Indexes
  KEY idx_formulario_multiplos (multiplos_lancamentos),
  KEY idx_formulario_grupo (grupo_lancamento),
  KEY idx_formulario_conta (conta),
  KEY idx_formulario_categoria (categoria),
  
  -- Foreign Keys
  FOREIGN KEY (conta) REFERENCES bancos(id) ON DELETE SET NULL ON UPDATE CASCADE,
  FOREIGN KEY (categoria) REFERENCES categoria(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Colunas Principais:

| Coluna | Tipo | Descrição | Observações |
|--------|------|-----------|-------------|
| id | INT PK | ID único do lançamento | Auto-increment |
| data_lancamento | DATE | Data do lançamento | Usado para agrupar múltiplos antigos |
| solicitante | VARCHAR(255) | Quem solicitou o lançamento | Usado para agrupar múltiplos |
| titular | VARCHAR(255) | Beneficiário/Fornecedor | Pode estar não cadastrado |
| referente | VARCHAR(255) | Descrição do pagamento | Referência do que está sendo pago |
| valor | DECIMAL(12,2) | Valor em centavos | Armazenado como centavos (multiplica por 100) |
| obra | INT (FK) | ID da obra principal | Referência para tabela obras |
| data_pagamento | DATE | Quando foi/será pago | Pode ser nula |
| forma_pagamento | VARCHAR(50) | Método de pagamento | Valores: 'boleto', 'transfer', 'pix', etc |
| lancado | ENUM | Status do lançamento | Y=Lançado, N=Pendente, X=Não autorizado, A=Aprovado |
| cpf_cnpj | VARCHAR(20) | CPF ou CNPJ do beneficiário | Único para identificação |
| chave_pix | VARCHAR(600) | Chave PIX (até 500 chars) | Suporta copia-cola (híbrido) |
| data_competencia | DATE | Período de referência | Para contabilidade |
| carimbo | TIMESTAMP | Data/hora de criação | UTC+1 (servidor) |
| observacao | TEXT | Notas adicionais | Campo livre |
| conta | INT (FK) | Banco/Conta principal | Referência para tabela bancos |
| categoria | INT (FK) | Categoria do lançamento | Referência para tabela categoria |
| multiplos_lancamentos | TINYINT(1) | Indica múltiplos lançamentos | 0=simples, 1=múltiplo |
| grupo_lancamento | VARCHAR(50) | Agrupa lançamentos relacionados | UUID curto (ex: "a1b2c3d4") |
| fornecedor_novo | TINYINT(1) | Fornecedor digitado manualmente | 1=sim, 0=não (já está cadastrado) |
| link_anexo | VARCHAR(500) | URL do arquivo no Google Drive | Pode conter múltiplos links |
| updated_at | TIMESTAMP | Última atualização | AUTO_UPDATE |

---

## Como Funcionam os Lançamentos Múltiplos

### Estrutura 1: NOVO (Com grupo_lancamento)
Quando `multiplos_lancamentos = 1` e `grupo_lancamento` está preenchido:
- **Um único lançamento principal** é criado como "representante" do grupo
- **Múltiplos registros relacionados** existem com o mesmo `grupo_lancamento`
- Ao **listar**, apenas o PRIMEIRO registro de cada grupo é exibido (usando ROW_NUMBER)
- Os demais registros são carregados sob `obras_relacionadas`

**Exemplo:**
```
Formulário ID 100 (representante):
  - grupo_lancamento: "abc123de"
  - solicitante: "joao"
  - data_lancamento: 2025-01-31
  - valor: 5000 (centavos = R$ 50,00)
  
Registros relacionados (mesma grupo):
  - ID 101: obra 2, valor 2000, forma_pagamento "boleto"
  - ID 102: obra 3, valor 1500, forma_pagamento "transfer"
  - ID 103: obra 4, valor 1500, forma_pagamento "pix"
```

### Estrutura 2: ANTIGO (Sem grupo_lancamento)
Quando `multiplos_lancamentos = 1` mas `grupo_lancamento = NULL`:
- Agrupa por: `data_lancamento` + `solicitante` + `titular`
- Busca dinamicamente todos os registros com os mesmos valores
- Útil para dados antigos que não têm grupo definido

---

## Tabela de Relacionamento: FORMULARIO_OBRAS (Junction Table)

```sql
CREATE TABLE IF NOT EXISTS `formulario_obras` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `formulario_id` INT NOT NULL,
  `obra_id` INT NOT NULL,
  `valor` DECIMAL(12, 2) NOT NULL,                        -- Valor atribuído a esta obra
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (`formulario_id`) REFERENCES `formulario`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`obra_id`) REFERENCES `obras`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  
  -- Indexes
  KEY idx_formulario_obras_formulario (formulario_id),
  KEY idx_formulario_obras_obra (obra_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Propósito:
- Armazena o relacionamento entre um formulário e múltiplas obras
- Cada linha representa uma obra que recebe uma parcela do pagamento
- Permite rastrear qual valor foi atribuído a cada obra

---

## Tabelas de Suporte

### 1. BANCOS (Contas Bancárias)

```sql
CREATE TABLE IF NOT EXISTS `bancos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL UNIQUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  KEY idx_bancos_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Exemplos de Valores:**
- Banco do Brasil
- Caixa Econômica Federal
- Itaú Unibanco
- Santander
- Bradesco

### 2. CATEGORIA (Categorias de Lançamento)

```sql
CREATE TABLE IF NOT EXISTS `categoria` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL UNIQUE,
  `descricao` VARCHAR(500),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  KEY idx_categoria_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3. FORNECEDOR (Titulares/Fornecedores)

```sql
CREATE TABLE IF NOT EXISTS `fornecedor` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `titular` VARCHAR(255) NOT NULL,
  `cpf_cnpj` VARCHAR(20) NOT NULL UNIQUE,
  `chave_pix` VARCHAR(600),
  `banco_padrao` VARCHAR(255),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  KEY idx_fornecedor_titular (titular),
  KEY idx_fornecedor_cpf_cnpj (cpf_cnpj)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 4. OBRAS (Projetos/Obras)

```sql
-- Estrutura inferida dos SELECTs:
CREATE TABLE IF NOT EXISTS `obras` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL,
  `quem_paga` VARCHAR(255),
  `banco_id` INT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 5. USERS (Usuários)

```sql
-- Estrutura inferida com base em migrations:
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255),
  `username` VARCHAR(255) UNIQUE,
  `email` VARCHAR(255) UNIQUE,
  `senha` VARCHAR(255),
  `role` ENUM('admin', 'user', 'financeiro') DEFAULT 'user',  -- Novo: 'financeiro'
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6. USERS_OBRAS (Relacionamento Usuário-Obra)

```sql
-- Junction table para vincular usuários a múltiplas obras
CREATE TABLE IF NOT EXISTS `users_obras` (
  `user_id` INT NOT NULL,
  `obra_id` INT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (user_id, obra_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## Fluxo Completo de um Lançamento Múltiplo (POST)

### Request (Frontend → Backend):
```json
{
  "multiplos_lancamentos": 1,
  "obras_adicionais": [
    { "obra": 1, "valor": 2000 },
    { "obra": 2, "valor": 3000 },
    { "obra": 3, "valor": 1500 }
  ],
  "valor": 6500,
  "data_lancamento": "2025-01-31",
  "solicitante": "joao",
  "titular": "FORNECEDOR SA",
  "referente": "Material de construção",
  "forma_pagamento": "boleto",
  "cpf_cnpj": "12345678000195",
  "chave_pix": "12345678000195@empresa.com.br",
  "categoria": 2,
  "conta": 1,
  "data_pagamento": "2025-02-15",
  "data_competencia": "2025-01-01"
}
```

### Processamento (Backend):
1. **Gera** `grupo_lancamento` (UUID curto)
2. **Para cada obra** em `obras_adicionais`:
   - Cria um registro em `formulario` com:
     - Valor próprio da obra
     - `multiplos_lancamentos = 1`
     - `grupo_lancamento` (mesmo para todos)
3. **Insere** relacionamentos em `formulario_obras`

### Resultado no BD:
```
formulario:
  ID 100: obra=1, valor=2000, grupo_lancamento="abc123de", multiplos=1
  ID 101: obra=2, valor=3000, grupo_lancamento="abc123de", multiplos=1
  ID 102: obra=3, valor=1500, grupo_lancamento="abc123de", multiplos=1

formulario_obras:
  (100, 1, 2000)
  (100, 2, 3000)
  (100, 3, 1500)
```

---

## Queries Importantes para Lançamentos Múltiplos

### 1. Listar apenas PRIMEIRO registro de cada grupo:
```sql
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
```

### 2. Buscar todos os registros de um grupo:
```sql
SELECT id, obra, valor, referente, data_pagamento, forma_pagamento
FROM formulario
WHERE grupo_lancamento = 'abc123de'
ORDER BY id ASC;
```

### 3. Buscar lançamentos múltiplos antigos (sem grupo):
```sql
SELECT id FROM formulario
WHERE multiplos_lancamentos = 1 
AND DATE_FORMAT(data_lancamento, '%Y%m%d') = '20250131'
AND solicitante = 'joao'
AND titular = 'FORNECEDOR SA'
ORDER BY id ASC;
```

### 4. Deletar lançamento múltiplo (todos do grupo):
```sql
-- 1. Encontrar grupo
SELECT grupo_lancamento FROM formulario WHERE id = 100;

-- 2. Deletar todos com o grupo
DELETE FROM formulario WHERE grupo_lancamento = 'abc123de';
```

---

## Relacionamentos: Diagrama ER

```
┌─────────────────────┐
│     FORMULARIO      │
├─────────────────────┤
│ id (PK)             │
│ data_lancamento     │
│ solicitante         │
│ titular             │
│ valor               │
│ obra (FK→obras)     │◄─────┐
│ forma_pagamento     │      │
│ lancado             │      │
│ cpf_cnpj            │      │
│ chave_pix           │      │
│ conta (FK→bancos)   │      │
│ categoria (FK)      │      │
│ multiplos_lancamentos│     │
│ grupo_lancamento    │      │
│ fornecedor_novo     │      │
└─────────────────────┘      │
         │                    │
         │ 1:N                │
         │                    │
┌────────▼──────────────────┐ │
│  FORMULARIO_OBRAS         │ │
├──────────────────────────┤ │
│ id (PK)                  │ │
│ formulario_id (FK)       │ │
│ obra_id (FK)─────────────┼─┘
│ valor                    │
└──────────────────────────┘

┌─────────────────────┐      ┌──────────────┐
│   BANCOS            │      │  CATEGORIA   │
├─────────────────────┤      ├──────────────┤
│ id (PK)             │      │ id (PK)      │
│ nome                │      │ nome         │
└─────────────────────┘      │ descricao    │
                             └──────────────┘

┌──────────────────────┐
│      OBRAS           │
├──────────────────────┤
│ id (PK)              │
│ nome                 │
│ quem_paga            │
│ banco_id             │
└──────────────────────┘
         │
         │ 1:N
         │
┌────────▼──────────────────┐
│   USERS_OBRAS (Junction)  │
├──────────────────────────┤
│ user_id (FK)             │
│ obra_id (FK)             │
└──────────────────────────┘
         │
         │ N:1
         │
    ┌────▼──────────────┐
    │     USERS         │
    ├───────────────────┤
    │ id (PK)           │
    │ nome              │
    │ username          │
    │ role              │
    │ email             │
    └───────────────────┘

┌──────────────────────┐
│     FORNECEDOR       │
├──────────────────────┤
│ id (PK)              │
│ titular              │
│ cpf_cnpj             │
│ chave_pix            │
│ banco_padrao         │
└──────────────────────┘
```

---

## Observações Importantes

### 1. **Valores em Centavos**
- O campo `valor` é armazenado em **centavos** (sem decimais)
- R$ 50,00 = 5000 centavos
- O frontend envia já convertido para centavos

### 2. **Timestamps**
- `carimbo`: Criado com `NOW()` (UTC+1 do servidor)
- Backend converte para Brasília (UTC-3)
- Diferença: -4 horas

### 3. **Status de Lançamento**
- `N` (Pendente): Padrão para novos
- `Y` (Lançado): Já foi contabilizado
- `X` (Não autorizado): Rejeitado
- `A` (Aprovado): Aprovado mas não lançado

### 4. **Fornecedor Novo**
- `fornecedor_novo = 1`: Titular digitado manualmente (não está em fornecedor)
- `fornecedor_novo = 0`: Titular já está cadastrado na tabela fornecedor

### 5. **Chave PIX**
- Expandida para **600 caracteres** (suporta até 500 chars)
- Pode conter PIX copia-cola (híbrido)

---

## Files de Migrations

1. **migrations.sql** - Script principal que cria/altera todas as tabelas
2. **migration_add_financeiro.py** - Adiciona role 'financeiro' aos usuários
3. **fix_grupo_lancamento.sql** - Popula grupo_lancamento para lançamentos antigos
4. **run_migrations.py** - Script Python que executa migrations.sql

