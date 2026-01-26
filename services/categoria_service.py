from db import get_connection

# ===========================
# LISTAR TODAS AS CATEGORIAS
# ===========================
def listar_categorias():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categoria ORDER BY nome ASC")
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
    cursor.execute("SELECT * FROM categoria WHERE id = %s", (categoria_id,))
    categoria = cursor.fetchone()
    cursor.close()
    conn.close()
    return categoria


# ===========================
# CRIAR CATEGORIA
# ===========================
def criar_categoria(nome, descricao=None):
    # Validar se já existe
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM categoria WHERE nome = %s", (nome,))
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return (None, "Categoria com este nome já existe")
    
    # Inserir nova categoria
    cursor.execute(
        "INSERT INTO categoria (nome, descricao) VALUES (%s, %s)",
        (nome, descricao or "")
    )
    conn.commit()
    categoria_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return (categoria_id, None)


# ===========================
# ATUALIZAR CATEGORIA
# ===========================
def atualizar_categoria(categoria_id, nome=None, descricao=None):
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
    
    # Preparar UPDATE
    set_clauses = []
    valores = []
    
    if nome:
        set_clauses.append("nome = %s")
        valores.append(nome)
    
    if descricao is not None:
        set_clauses.append("descricao = %s")
        valores.append(descricao)
    
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
    
    # Deletar categoria
    cursor.execute("DELETE FROM categoria WHERE id = %s", (categoria_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return (True, None)
