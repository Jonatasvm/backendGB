import uuid
from db import get_connection

# Armazenamento simples de tokens em memória (para produção, usar Redis ou Banco)
active_tokens = {}

# ======================================================
# TOKEN GENERATOR
# ======================================================
def generate_token():
    return uuid.uuid4().hex

# ======================================================
# REGISTER USER (Criação)
# ======================================================
def register_user(username, password, role="user", obras_names=[]):
    """
    Cria usuário, define role e vincula obras (se houver).
    """
    allowed_roles = ["admin", "user"]
    if role not in allowed_roles:
        role = "user"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Verifica se usuário já existe
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return None, "Usuário já existe"

        # 2. Insere o Usuário na tabela 'users'
        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (%s, %s, %s)
        """, (username, password, role))
        
        user_id = cursor.lastrowid

        # 3. Vincula as Obras na tabela 'users_obras'
        if obras_names and len(obras_names) > 0:
            # Cria uma string segura para o IN clause: %s, %s, %s...
            format_strings = ','.join(['%s'] * len(obras_names))
            
            # Busca os IDs das obras baseados nos nomes enviados pelo front
            cursor.execute(f"SELECT id FROM obras WHERE nome IN ({format_strings})", tuple(obras_names))
            obras_encontradas = cursor.fetchall() # Retorna lista de dicionários [{'id': 1}, {'id': 5}]

            # Insere cada relacionamento
            for obra in obras_encontradas:
                cursor.execute("INSERT INTO users_obras (user_id, obra_id) VALUES (%s, %s)", (user_id, obra['id']))

        conn.commit()

        # Gera token e loga automaticamente
        token = generate_token()
        active_tokens[token] = user_id

        return {
            "id": user_id,
            "username": username,
            "role": role,
            "token": token,
            "obras": obras_names
        }, None

    except Exception as e:
        conn.rollback() # Desfaz tudo se der erro
        print("Erro no register_user:", e)
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

# ======================================================
# UPDATE USER (Edição)
# ======================================================
def update_user_service(user_id, username, role, obras_names, password=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Atualiza dados básicos (Senha é opcional)
        if password:
            cursor.execute("UPDATE users SET username=%s, role=%s, password_hash=%s WHERE id=%s", (username, role, password, user_id))
        else:
            cursor.execute("UPDATE users SET username=%s, role=%s WHERE id=%s", (username, role, user_id))

        # 2. Atualiza Obras (Estratégia: Limpar tudo e reinserir)
        cursor.execute("DELETE FROM users_obras WHERE user_id = %s", (user_id,))
        
        if obras_names and len(obras_names) > 0:
            format_strings = ','.join(['%s'] * len(obras_names))
            cursor.execute(f"SELECT id FROM obras WHERE nome IN ({format_strings})", tuple(obras_names))
            # cursor sem dictionary=True retorna tuplas: ((1,), (2,))
            obras_ids = [row[0] for row in cursor.fetchall()] 

            for oid in obras_ids:
                cursor.execute("INSERT INTO users_obras (user_id, obra_id) VALUES (%s, %s)", (user_id, oid))
        
        conn.commit()
        return True, None

    except Exception as e:
        conn.rollback()
        print("Erro no update_user:", e)
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

# ======================================================
# AUTH / LOGIN
# ======================================================
def authenticate(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, username, password_hash, role
        FROM users
        WHERE username = %s
    """, (username,))

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return None, "Usuário não encontrado"

    if password != user["password_hash"]:
        return None, "Senha incorreta"

    token = generate_token()
    active_tokens[token] = user["id"]
    
    # Injeta o token no objeto de retorno
    user["token"] = token
    return user, None

def get_user_by_token(token):
    user_id = active_tokens.get(token)
    if not user_id:
        return None
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user