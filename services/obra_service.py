from db import get_connection


def criar_obra(nome, user_id, quem_paga): # <--- Adicionado parametro quem_paga
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Verifica se obra existe
    cursor.execute("SELECT id FROM obras WHERE nome = %s", (nome,))
    existe = cursor.fetchone()
    if existe:
        cursor.close()
        conn.close()
        return None, "Obra já existe"

    # 2. Cria a Obra (Adicionado campo quem_paga)
    cursor.execute("INSERT INTO obras (nome, quem_paga) VALUES (%s, %s)", (nome, quem_paga))
    conn.commit()
    obra_id = cursor.lastrowid

    # 3. Vincula ao Usuário (APENAS SE user_id FOR VÁLIDO)
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
    
    # Retorna o objeto completo
    return {"id": obra_id, "nome": nome, "quem_paga": quem_paga}, None

def listar_obras():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM obras")
    obras = cursor.fetchall()
    cursor.close()
    conn.close()
    return obras


def atualizar_obra(obra_id, novo_nome):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM obras WHERE id = %s", (obra_id,))
    obra = cursor.fetchone()
    if not obra:
        cursor.close()
        conn.close()
        return None, "Obra não encontrada"

    cursor.execute("UPDATE obras SET nome = %s WHERE id = %s", (novo_nome, obra_id))
    conn.commit()

    cursor.execute("SELECT * FROM obras WHERE id = %s", (obra_id,))
    obra_atualizada = cursor.fetchone()

    cursor.close()
    conn.close()
    return obra_atualizada, None


def deletar_obra(obra_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM obras WHERE id = %s", (obra_id,))
    obra = cursor.fetchone()
    if not obra:
        cursor.close()
        conn.close()
        return False, "Obra não encontrada"

    # Deleta relacionamentos antes de deletar a obra
    cursor.execute("DELETE FROM users_obras WHERE obra_id = %s", (obra_id,))
    cursor.execute("DELETE FROM obras WHERE id = %s", (obra_id,))
    conn.commit()

    cursor.close()
    conn.close()
    return True, None
