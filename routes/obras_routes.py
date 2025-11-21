from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.obra_service import (
    criar_obra,
    listar_obras,
    atualizar_obra,
    deletar_obra,
    listar_obras_por_usuario # <--- Importante: Importando a nova função
)

obras_bp = Blueprint("obras", __name__)

# =====================================================
# LISTAR (GET) - COM FILTRO DE USUÁRIO
# =====================================================
@obras_bp.route("/obras", methods=["GET", "OPTIONS"])
@cross_origin()
def listar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    # Verifica se veio um user_id na URL (ex: /obras?user_id=1)
    user_id = request.args.get("user_id")

    if user_id:
        # Se tem ID, busca filtrado (apenas obras desse usuário)
        obras = listar_obras_por_usuario(user_id)
    else:
        # Se não tem ID, busca tudo (comportamento padrão/admin)
        obras = listar_obras()
        
    return jsonify(obras), 200


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

    if not nome or not quem_paga:
        return jsonify({"error": "Nome e o campo 'Quem Paga' são obrigatórios"}), 400

    obra, error = criar_obra(nome, user_id, quem_paga)
    
    if error:
        return jsonify({"error": error}), 409

    return jsonify(obra), 201


# ... (Mantenha os imports e as rotas GET e POST iguais)

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

    if not novo_nome or not novo_quem_paga:
        return jsonify({"error": "Campos obrigatórios faltando"}), 400

    obra, error = atualizar_obra(obra_id, novo_nome, novo_quem_paga)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(obra), 200

# === ADICIONE ESTA ROTA NO FINAL ===
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