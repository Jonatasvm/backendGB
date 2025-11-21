from db import get_connection

def criar_obra(nome, user_id, quem_paga):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Verifica se obra existe
    cursor.execute("SELECT id FROM obras WHERE nome = %s", (nome,))
    existe = cursor.fetchone()
    if existe:
        cursor.close()
        conn.close()
        return None, "Obra já existe"

    # 2. Cria a Obra
    cursor.execute("INSERT INTO obras (nome, quem_paga) VALUES (%s, %s)", (nome, quem_paga))
    conn.commit()
    obra_id = cursor.lastrowid

    # 3. Vincula ao Usuário (se enviado)
    if user_id:
        try:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            user_exists = cursor.fetchone()
            
            if user_exists:
                cursor.execute("INSERT INTO users_obras (user_id, obra_id) VALUES (%s, %s)", (user_id, obra_id))
                conn.commit()
        except Exception as e:
            print(f"Aviso: Obra criada, mas falha ao vincular usuário: {e}")

    cursor.close()
    conn.close()
    
    return {"id": obra_id, "nome": nome, "quem_paga": quem_paga}, None

def listar_obras():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM obras")
    obras = cursor.fetchall()
    cursor.close()
    conn.close()
    return obras

def atualizar_obra(obra_id, novo_nome, novo_quem_paga):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Verifica se a obra existe
    cursor.execute("SELECT * FROM obras WHERE id = %s", (obra_id,))
    obra = cursor.fetchone()
    
    if not obra:
        cursor.close()
        conn.close()
        return None, "Obra não encontrada"

    # 2. Atualiza Nome e Quem Paga
    cursor.execute("""
        UPDATE obras 
        SET nome = %s, quem_paga = %s 
        WHERE id = %s
    """, (novo_nome, novo_quem_paga, obra_id))
    conn.commit()

    # 3. Retorna atualizado
    cursor.execute("SELECT * FROM obras WHERE id = %s", (obra_id,))
    obra_atualizada = cursor.fetchone()

    cursor.close()
    conn.close()
    return obra_atualizada, None

# === ADICIONE ESTA FUNÇÃO NO FINAL ===
def deletar_obra(obra_id):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Verifica se existe
    cursor.execute("SELECT id FROM obras WHERE id = %s", (obra_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return None, "Obra não encontrada"

    try:
        # 2. Remove vínculos na tabela users_obras (Para evitar erro de Foreign Key)
        cursor.execute("DELETE FROM users_obras WHERE obra_id = %s", (obra_id,))
        
        # Opcional: Se você quiser apagar os formulários dessa obra também, descomente a linha abaixo:
        # cursor.execute("DELETE FROM formulario WHERE obra = %s", (obra_id,))

        # 3. Deleta a Obra
        cursor.execute("DELETE FROM obras WHERE id = %s", (obra_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return None, f"Erro ao excluir obra (pode haver registros vinculados): {str(e)}"

    cursor.close()
    conn.close()
    return {"message": "Obra excluída com sucesso"}, None

# --- NOVA FUNÇÃO NECESSÁRIA ---
def listar_obras_por_usuario(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # JOIN para pegar apenas as obras vinculadas ao usuário
    query = """
        SELECT o.id, o.nome, o.quem_paga 
        FROM obras o
        INNER JOIN users_obras uo ON o.id = uo.obra_id
        WHERE uo.user_id = %s
    """
    
    cursor.execute(query, (user_id,))
    obras = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return obras