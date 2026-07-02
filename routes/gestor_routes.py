from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection
import sys

gestor_bp = Blueprint("gestor", __name__)


# =====================================================
# LISTAR GESTORES DISPONÍVEIS (users_fincontrol)
# =====================================================
@gestor_bp.route("/gestores/fincontrol", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_gestores_fincontrol():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, display_name, username, user_role 
            FROM users_fincontrol 
            ORDER BY display_name ASC
        """)
        gestores = cursor.fetchall()
        return jsonify(gestores), 200
    except Exception as e:
        print(f"❌ Erro ao buscar gestores fincontrol: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": f"Erro ao buscar gestores: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# =====================================================
# LISTAR TODOS OS VÍNCULOS (user_gestor)
# =====================================================
@gestor_bp.route("/user-gestor", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_vinculos():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                ug.id,
                ug.ativo,
                ug.uuid_fincontrol,
                ug.uuid_users,
                uf.display_name AS gestor_nome,
                uf.username AS gestor_username,
                u.nome AS subordinado_nome,
                u.username AS subordinado_username,
                u.id AS subordinado_id
            FROM user_gestor ug
            LEFT JOIN users_fincontrol uf ON ug.uuid_fincontrol = uf.id
            LEFT JOIN users u ON ug.uuid_users = u.uuid_id
            ORDER BY uf.display_name ASC, u.nome ASC
        """)
        vinculos = cursor.fetchall()
        return jsonify(vinculos), 200
    except Exception as e:
        print(f"❌ Erro ao listar vínculos gestor: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": f"Erro ao listar vínculos: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# =====================================================
# BUSCAR GESTOR DE UM SUBORDINADO (por uuid_users)
# =====================================================
@gestor_bp.route("/user-gestor/subordinado/<string:user_uuid>", methods=["GET", "OPTIONS"])
@cross_origin()
def buscar_gestor_por_subordinado(user_uuid):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                ug.id,
                ug.ativo,
                ug.uuid_fincontrol,
                ug.uuid_users,
                uf.display_name AS gestor_nome,
                uf.username AS gestor_username
            FROM user_gestor ug
            LEFT JOIN users_fincontrol uf ON ug.uuid_fincontrol = uf.id
            WHERE ug.uuid_users = %s
            LIMIT 1
        """, (user_uuid,))
        vinculo = cursor.fetchone()
        
        if not vinculo:
            return jsonify({"message": "Nenhum gestor vinculado"}), 404
        
        return jsonify(vinculo), 200
    except Exception as e:
        print(f"❌ Erro ao buscar gestor do subordinado: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": f"Erro ao buscar gestor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# =====================================================
# CRIAR VÍNCULO (POST)
# =====================================================
@gestor_bp.route("/user-gestor", methods=["POST", "OPTIONS"])
@cross_origin()
def criar_vinculo():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    uuid_fincontrol = data.get("uuid_fincontrol")
    uuid_users = data.get("uuid_users")

    if not uuid_fincontrol or not uuid_users:
        return jsonify({"error": "uuid_fincontrol e uuid_users são obrigatórios"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar se o subordinado já está vinculado a algum gestor
        cursor.execute("SELECT id, uuid_fincontrol FROM user_gestor WHERE uuid_users = %s", (uuid_users,))
        existing = cursor.fetchone()
        
        if existing:
            # Buscar nome do gestor atual para a mensagem
            cursor.execute("SELECT display_name FROM users_fincontrol WHERE id = %s", (existing["uuid_fincontrol"],))
            gestor_atual = cursor.fetchone()
            nome_gestor = gestor_atual["display_name"] if gestor_atual else existing["uuid_fincontrol"]
            
            cursor.close()
            conn.close()
            return jsonify({
                "error": f"Este usuário já está vinculado ao gestor '{nome_gestor}'. Remova o vínculo antes de criar um novo.",
                "vinculo_existente_id": existing["id"]
            }), 409

        # Criar vínculo
        cursor.execute("""
            INSERT INTO user_gestor (ativo, uuid_fincontrol, uuid_users)
            VALUES (TRUE, %s, %s)
        """, (uuid_fincontrol, uuid_users))
        conn.commit()
        vinculo_id = cursor.lastrowid

        return jsonify({
            "message": "Vínculo gestor criado com sucesso",
            "id": vinculo_id
        }), 201
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao criar vínculo gestor: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": f"Erro ao criar vínculo: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# =====================================================
# ATUALIZAR VÍNCULO (PUT) — trocar gestor
# =====================================================
@gestor_bp.route("/user-gestor/<int:vinculo_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar_vinculo(vinculo_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    uuid_fincontrol = data.get("uuid_fincontrol")
    ativo = data.get("ativo")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar se o vínculo existe
        cursor.execute("SELECT id FROM user_gestor WHERE id = %s", (vinculo_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Vínculo não encontrado"}), 404

        set_clauses = []
        valores = []

        if uuid_fincontrol is not None:
            set_clauses.append("uuid_fincontrol = %s")
            valores.append(uuid_fincontrol)
        
        if ativo is not None:
            set_clauses.append("ativo = %s")
            valores.append(ativo)

        if not set_clauses:
            cursor.close()
            conn.close()
            return jsonify({"error": "Nenhum campo para atualizar"}), 400

        valores.append(vinculo_id)
        query = f"UPDATE user_gestor SET {', '.join(set_clauses)} WHERE id = %s"
        cursor.execute(query, tuple(valores))
        conn.commit()

        return jsonify({"message": "Vínculo atualizado com sucesso"}), 200
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar vínculo: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": f"Erro ao atualizar vínculo: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# =====================================================
# DELETAR VÍNCULO (DELETE)
# =====================================================
@gestor_bp.route("/user-gestor/<int:vinculo_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar_vinculo(vinculo_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar se o vínculo existe
        cursor.execute("SELECT id FROM user_gestor WHERE id = %s", (vinculo_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Vínculo não encontrado"}), 404

        cursor.execute("DELETE FROM user_gestor WHERE id = %s", (vinculo_id,))
        conn.commit()

        return jsonify({"message": "Vínculo removido com sucesso"}), 200
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao deletar vínculo: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": f"Erro ao deletar vínculo: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# =====================================================
# ATUALIZAR GESTOR DE UM USUÁRIO (atalho — POST ou PUT por uuid_users)
# Usado pelo frontend ao editar usuário
# =====================================================
@gestor_bp.route("/user-gestor/atualizar-por-user", methods=["POST", "OPTIONS"])
@cross_origin()
def atualizar_gestor_por_user():
    """
    Atalho: Recebe uuid_users + uuid_fincontrol.
    - Se uuid_fincontrol é null/vazio: remove vínculo existente
    - Se já existe vínculo: atualiza
    - Se não existe: cria
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    uuid_users = data.get("uuid_users")
    uuid_fincontrol = data.get("uuid_fincontrol")

    if not uuid_users:
        return jsonify({"error": "uuid_users é obrigatório"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Buscar vínculo existente
        cursor.execute("SELECT id FROM user_gestor WHERE uuid_users = %s", (uuid_users,))
        existing = cursor.fetchone()

        if not uuid_fincontrol or uuid_fincontrol == "":
            # Remover vínculo se existir
            if existing:
                cursor.execute("DELETE FROM user_gestor WHERE id = %s", (existing["id"],))
                conn.commit()
                return jsonify({"message": "Vínculo com gestor removido"}), 200
            else:
                return jsonify({"message": "Nenhum vínculo para remover"}), 200
        else:
            if existing:
                # Atualizar gestor
                cursor.execute(
                    "UPDATE user_gestor SET uuid_fincontrol = %s, ativo = TRUE WHERE id = %s",
                    (uuid_fincontrol, existing["id"])
                )
                conn.commit()
                return jsonify({"message": "Gestor atualizado com sucesso"}), 200
            else:
                # Criar novo vínculo
                cursor.execute("""
                    INSERT INTO user_gestor (ativo, uuid_fincontrol, uuid_users)
                    VALUES (TRUE, %s, %s)
                """, (uuid_fincontrol, uuid_users))
                conn.commit()
                return jsonify({
                    "message": "Vínculo gestor criado com sucesso",
                    "id": cursor.lastrowid
                }), 201
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar gestor por user: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": f"Erro: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
