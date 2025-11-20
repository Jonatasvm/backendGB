from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from db import get_connection
from services.user_service import get_user_by_token, update_user_service

usuarios_bp = Blueprint("usuarios", __name__)

# ======================================================
# HELPERS
# ======================================================
def extract_token():
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return auth

def require_admin():
    token = extract_token()
    if not token:
        return None, jsonify({"error": "Token faltando"}), 401

    user = get_user_by_token(token)
    if not user:
        return None, jsonify({"error": "Token inválido"}), 401

    if user["role"] != "admin":
        return None, jsonify({"error": "Apenas administradores podem acessar"}), 403

    return user, None, None


# ======================================================
# LISTAR USUÁRIOS (GET) - COM OBRAS AGRUPADAS
# ======================================================
@usuarios_bp.route("/usuarios", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_usuarios():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    # Verifica se é admin
    _, err, code = require_admin()
    if err:
        return err, code

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Query que traz Usuários + Nome da Obra (LEFT JOIN)
    cursor.execute("""
        SELECT 
            u.id AS user_id,
            u.username,
            u.password_hash,
            u.role,
            o.id AS obra_id,
            o.nome AS obra_nome
        FROM users u
        LEFT JOIN users_obras uo ON u.id = uo.user_id
        LEFT JOIN obras o ON uo.obra_id = o.id
        ORDER BY u.id
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Lógica para agrupar: Transforma linhas repetidas em um usuário com lista de obras
    usuarios_dict = {}
    for row in rows:
        uid = row["user_id"]

        if uid not in usuarios_dict:
            usuarios_dict[uid] = {
                "id": uid,
                "username": row["username"],
                "password_hash": row["password_hash"],
                "role": row["role"],
                "obras": [] # Lista vazia inicial
            }
        
        # Se tiver obra nessa linha, adiciona na lista
        if row["obra_nome"]:
            usuarios_dict[uid]["obras"].append(row["obra_nome"])

    # Converte o dicionário em lista para o JSON final
    lista_final = list(usuarios_dict.values())

    return jsonify({"usuarios": lista_final}), 200


# ======================================================
# ATUALIZAR USUÁRIO (PUT)
# ======================================================
@usuarios_bp.route("/usuarios/<int:user_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar_usuario(user_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    _, err, code = require_admin()
    if err:
        return err, code

    data = request.get_json()
    usuario = data.get("usuario")
    role = data.get("role")
    obras = data.get("obras", []) # Lista de nomes ['Obra A', 'Obra B']
    password = data.get("password") # Opcional

    # Chama o serviço atualizado
    success, msg = update_user_service(user_id, usuario, role, obras, password)
    
    if not success:
        return jsonify({"error": msg}), 500

    return jsonify({"message": "Usuário atualizado com sucesso"}), 200


# ======================================================
# DELETAR USUÁRIO (DELETE)
# ======================================================
@usuarios_bp.route("/usuarios/<int:user_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar_usuario(user_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
        
    _, err, code = require_admin()
    if err:
        return err, code

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Remove relacionamentos na users_obras
        cursor.execute("DELETE FROM users_obras WHERE user_id = %s", (user_id,))
        # 2. Remove o usuário
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Usuário removido"}), 200


# ======================================================
# ADICIONAR OBRA A UM USUÁRIO JÁ EXISTENTE
# ======================================================
@usuarios_bp.route("/usuarios/<int:user_id>/adicionar-obra", methods=["POST", "OPTIONS"])
@cross_origin()
def adicionar_obra_usuario(user_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    obra_nome = data.get("obra")

    if not obra_nome:
        return jsonify({"error": "Nome da obra é obrigatório"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Verifica se a obra existe
    cursor.execute("SELECT id FROM obras WHERE nome = %s", (obra_nome,))
    obra = cursor.fetchone()
    if not obra:
        cursor.close()
        conn.close()
        return jsonify({"error": "Obra não existe"}), 404

    obra_id = obra["id"]

    # Verifica se já está vinculado
    cursor.execute(
        "SELECT * FROM users_obras WHERE user_id = %s AND obra_id = %s",
        (user_id, obra_id)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Usuário já possui esta obra"}), 409

    # Vínculo
    cursor.execute(
        "INSERT INTO users_obras (user_id, obra_id) VALUES (%s, %s)",
        (user_id, obra_id)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Obra adicionada ao usuário com sucesso"}), 201
