from db import get_connection

# ===========================
# LISTAR TODAS AS CATEGORIAS (com hierarquia)
# ===========================
def listar_categorias():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, 
               p.nome AS nome_pai
        FROM categoria c
        LEFT JOIN categoria p ON c.id_pai = p.id
        ORDER BY 
            CASE WHEN c.id_pai IS NULL THEN c.id ELSE c.id_pai END,
            c.id_pai IS NOT NULL,
            c.nome ASC
    """)
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return categorias


# ===========================
# LISTAR APENAS CATEGORIAS PAI
# ===========================
def listar_categorias_pai():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nome, descricao 
        FROM categoria 
        WHERE (conta_filha IS NULL OR conta_filha = 0) 
          AND id_pai IS NULL
        ORDER BY nome ASC
    """)
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return categorias


# ===========================
# BUSCAR CATEGORIA POR ID
# ===========================
def buscar_categoria_por_id(categoria_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, p.nome AS nome_pai
        FROM categoria c
        LEFT JOIN categoria p ON c.id_pai = p.id
        WHERE c.id = %s
    """, (categoria_id,))
    categoria = cursor.fetchone()
    cursor.close()
    conn.close()
    return categoria


# ===========================
# CRIAR CATEGORIA
# ===========================
def criar_categoria(nome, descricao=None, conta_filha=None, id_pai=None):
    # Validar se já existe
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM categoria WHERE nome = %s", (nome,))
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return (None, "Categoria com este nome já existe")
    
    # Validar se id_pai existe (se fornecido)
    if id_pai is not None:
        cursor.execute("SELECT id FROM categoria WHERE id = %s", (id_pai,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (None, "Categoria pai não encontrada")
    
    # Se tem id_pai, automaticamente é conta_filha
    if id_pai is not None:
        conta_filha = True
    
    # Inserir nova categoria
    cursor.execute(
        "INSERT INTO categoria (nome, descricao, conta_filha, id_pai) VALUES (%s, %s, %s, %s)",
        (nome, descricao or "", conta_filha, id_pai)
    )
    conn.commit()
    categoria_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return (categoria_id, None)


# ===========================
# ATUALIZAR CATEGORIA
# ===========================
def atualizar_categoria(categoria_id, nome=None, descricao=None, conta_filha=None, id_pai=None):
    # Validar se categoria existe
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM categoria WHERE id = %s", (categoria_id,))
    
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return (None, "Categoria não encontrada")
    
    # Validar se novo nome já existe (se foi fornecido)
    if nome:
        cursor.execute("SELECT id FROM categoria WHERE nome = %s AND id != %s", (nome, categoria_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return (None, "Categoria com este nome já existe")
    
    # Validar que não está se vinculando a si mesma
    if id_pai is not None and int(id_pai) == int(categoria_id):
        cursor.close()
        conn.close()
        return (None, "Uma categoria não pode ser pai de si mesma")
    
    # Validar se id_pai existe (se fornecido)
    if id_pai is not None:
        cursor.execute("SELECT id FROM categoria WHERE id = %s", (id_pai,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (None, "Categoria pai não encontrada")
    
    # Preparar UPDATE
    set_clauses = []
    valores = []
    
    if nome:
        set_clauses.append("nome = %s")
        valores.append(nome)
    
    if descricao is not None:
        set_clauses.append("descricao = %s")
        valores.append(descricao)
    
    # conta_filha e id_pai — aceitar inclusive None/0 para "remover" vínculo
    if conta_filha is not None:
        set_clauses.append("conta_filha = %s")
        valores.append(conta_filha)
    
    # id_pai pode ser enviado como None para remover o vínculo
    # Diferenciamos: "id_pai não enviado" vs "id_pai enviado como null"
    # usando um valor sentinela — se o campo existir no payload, atualizamos
    if "id_pai" in dir():  # Sempre atualizar se chamado explicitamente
        set_clauses.append("id_pai = %s")
        valores.append(id_pai)
    
    if not set_clauses:
        cursor.close()
        conn.close()
        return (None, "Nenhum campo para atualizar")
    
    valores.append(categoria_id)
    query = f"UPDATE categoria SET {', '.join(set_clauses)} WHERE id = %s"
    cursor.execute(query, tuple(valores))
    conn.commit()
    cursor.close()
    conn.close()
    
    return (categoria_id, None)


# ===========================
# DELETAR CATEGORIA
# ===========================
def deletar_categoria(categoria_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Validar se categoria existe
    cursor.execute("SELECT id FROM categoria WHERE id = %s", (categoria_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return (None, "Categoria não encontrada")
    
    # Desvincular filhas antes de deletar (set id_pai = NULL)
    cursor.execute("UPDATE categoria SET id_pai = NULL, conta_filha = NULL WHERE id_pai = %s", (categoria_id,))
    
    # Deletar categoria
    cursor.execute("DELETE FROM categoria WHERE id = %s", (categoria_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return (True, None)
