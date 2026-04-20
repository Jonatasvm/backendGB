from db import get_connection
from flask import jsonify # Adicionado para garantir que jsonify está disponível se necessário, embora não seja estritamente necessário aqui.

def criar_obra(nome, user_id, quem_paga, banco_id=None, user_ids=None):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Verifica se obra existe
    cursor.execute("SELECT id FROM obras WHERE nome = %s", (nome,))
    existe = cursor.fetchone()
    if existe:
        cursor.close()
        conn.close()
        return None, "Obra já existe"

    # 2. Cria a Obra (com banco_id)
    cursor.execute("INSERT INTO obras (nome, quem_paga, banco_id) VALUES (%s, %s, %s)", (nome, quem_paga, banco_id))
    conn.commit()
    obra_id = cursor.lastrowid

    # 3. Vincula múltiplos usuários (se enviado)
    ids_to_link = []
    if user_ids and isinstance(user_ids, list):
        ids_to_link = user_ids
    elif user_id:
        ids_to_link = [user_id]

    for uid in ids_to_link:
        try:
            cursor.execute("SELECT id FROM users WHERE id = %s", (uid,))
            user_exists = cursor.fetchone()
            if user_exists:
                cursor.execute("INSERT INTO users_obras (user_id, obra_id) VALUES (%s, %s)", (uid, obra_id))
        except Exception as e:
            print(f"Aviso: Obra criada, mas falha ao vincular usuário {uid}: {e}")
    conn.commit()

    cursor.close()
    conn.close()
    
    return {"id": obra_id, "nome": nome, "quem_paga": quem_paga, "banco_id": banco_id}, None

def listar_obras():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM obras")
    obras = cursor.fetchall()

    # Busca vínculos de usuários com nome para cada obra
    for obra in obras:
        cursor.execute("""
            SELECT u.id, u.nome, u.username 
            FROM users u 
            JOIN users_obras uo ON u.id = uo.user_id 
            WHERE uo.obra_id = %s
        """, (obra['id'],))
        users = cursor.fetchall()
        obra['user_ids'] = [u['id'] for u in users]
        obra['users'] = users

    cursor.close()
    conn.close()
    return obras

def atualizar_obra(obra_id, novo_nome, novo_quem_paga, banco_id=None, user_ids=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Verifica se a obra existe
    cursor.execute("SELECT * FROM obras WHERE id = %s", (obra_id,))
    obra = cursor.fetchone()
    
    if not obra:
        cursor.close()
        conn.close()
        return None, "Obra não encontrada"

    # 2. Atualiza Nome, Quem Paga e Banco
    cursor.execute("""
        UPDATE obras 
        SET nome = %s, quem_paga = %s, banco_id = %s 
        WHERE id = %s
    """, (novo_nome, novo_quem_paga, banco_id, obra_id))

    # 3. Atualiza vínculos de usuários (se enviado)
    if user_ids is not None:
        cursor.execute("DELETE FROM users_obras WHERE obra_id = %s", (obra_id,))
        for uid in user_ids:
            try:
                cursor.execute("INSERT INTO users_obras (user_id, obra_id) VALUES (%s, %s)", (uid, obra_id))
            except Exception as e:
                print(f"Aviso: Falha ao vincular usuário {uid} à obra {obra_id}: {e}")

    conn.commit()

    # 4. Retorna atualizado
    cursor.execute("SELECT * FROM obras WHERE id = %s", (obra_id,))
    obra_atualizada = cursor.fetchone()

    cursor.close()
    conn.close()
    return obra_atualizada, None

# === ADICIONE ESTA FUNÇÃO NO FINAL ===
def buscar_obra_por_id(obra_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nome, quem_paga, banco_id FROM obras WHERE id = %s", (obra_id,))
        obra = cursor.fetchone()
        return obra
    except Exception as e:
        print(f"Erro ao buscar obra por ID: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def deletar_obra(obra_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Verifica se a obra existe
        cursor.execute("SELECT id FROM obras WHERE id = %s", (obra_id,))
        if not cursor.fetchone():
            return None, "Obra não encontrada"

        # 2. Remove vínculos com usuários (users_obras) para evitar erro de chave estrangeira
        cursor.execute("DELETE FROM users_obras WHERE obra_id = %s", (obra_id,))

        # 3. Deleta a obra
        cursor.execute("DELETE FROM obras WHERE id = %s", (obra_id,))
        conn.commit()

        return {"message": "Obra deletada com sucesso"}, None
    except Exception as e:
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

# --- NOVA FUNÇÃO NECESSÁRIA ---
def listar_obras_por_usuario(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Este SQL faz a mágica: une a tabela de obras com a tabela de permissões
        query = """
            SELECT o.id, o.nome, o.quem_paga, o.banco_id
            FROM obras o
            JOIN users_obras uo ON o.id = uo.obra_id
            WHERE uo.user_id = %s
        """
        cursor.execute(query, (user_id,))
        obras = cursor.fetchall()
        return obras
    except Exception as e:
        print(f"Erro ao listar obras por usuário: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()