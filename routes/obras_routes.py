from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.obra_service import (
    criar_obra,
    listar_obras,
    atualizar_obra,
    deletar_obra,
    listar_obras_por_usuario,
    buscar_obra_por_id
)

obras_bp = Blueprint("obras", __name__)

# =====================================================
# LISTAR (GET)
# Aceita ?user_id=1 para filtrar ou traz tudo se for admin/sem ID
# =====================================================
@obras_bp.route("/obras", methods=["GET", "OPTIONS"])
@cross_origin()
def listar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    user_id = request.args.get("user_id")

    try:
        if user_id:
            # Busca filtrada (Usuário comum)
            obras = listar_obras_por_usuario(user_id)
        else:
            # Busca completa (Admin ou padrão)
            obras = listar_obras()
        
        return jsonify(obras), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar obras: {str(e)}"}), 500


# =====================================================
# CRIAR (POST)
# =====================================================
@obras_bp.route("/obras", methods=["POST", "OPTIONS"])
@cross_origin()
def criar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    nome = data.get("nome")
    quem_paga = data.get("quem_paga")
    user_id = data.get("user_id")
    banco_id = data.get("banco_id")  # ✅ NOVO: Aceitar banco_id

    if not nome or not quem_paga:
        return jsonify({"error": "Nome e o campo 'Quem Paga' são obrigatórios"}), 400

    obra, error = criar_obra(nome, user_id, quem_paga, banco_id)
    
    if error:
        return jsonify({"error": error}), 409

    return jsonify(obra), 201


# =====================================================
# BUSCAR OBRA POR ID (GET)
# =====================================================
@obras_bp.route("/obras/<int:obra_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def buscar_obra(obra_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        obra = buscar_obra_por_id(obra_id)
        if obra:
            return jsonify(obra), 200
        return jsonify({"error": "Obra não encontrada"}), 404
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar obra: {str(e)}"}), 500

# =====================================================
# ATUALIZAR (PUT)
# =====================================================
@obras_bp.route("/obras/<int:obra_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar(obra_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    novo_nome = data.get("nome")
    novo_quem_paga = data.get("quem_paga")
    banco_id = data.get("banco_id")  # ✅ NOVO: Aceitar banco_id

    if not novo_nome or not novo_quem_paga:
        return jsonify({"error": "Campos obrigatórios faltando"}), 400

    obra, error = atualizar_obra(obra_id, novo_nome, novo_quem_paga, banco_id)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(obra), 200


# =====================================================
# DELETAR (DELETE)
# =====================================================
@obras_bp.route("/obras/<int:obra_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar(obra_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    resultado, error = deletar_obra(obra_id)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(resultado), 200