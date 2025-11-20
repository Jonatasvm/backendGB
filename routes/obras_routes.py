from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.obra_service import (
    criar_obra,
    listar_obras,
    atualizar_obra,
    deletar_obra
)

# Se precisar validar admin futuramente, importe:
# from services.user_service import get_user_by_token

obras_bp = Blueprint("obras", __name__)

# =====================================================
# LISTAR (GET)
# =====================================================
@obras_bp.route("/obras", methods=["GET", "OPTIONS"])
@cross_origin()
def listar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    # Chama o serviço (que você já criou em obra_service.py)
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
    quem_paga = data.get("quem_paga")  # <--- Captura o novo campo
    
    user_id = data.get("user_id") 

    # Validação: Agora exige nome E quem_paga
    if not nome or not quem_paga:
        return jsonify({"error": "Nome e o campo 'Quem Paga' são obrigatórios"}), 400

    # Passa o novo argumento para o serviço
    obra, error = criar_obra(nome, user_id, quem_paga)
    
    if error:
        return jsonify({"error": error}), 409

    return jsonify(obra), 201


# =====================================================
# ATUALIZAR (PUT) - Rota que estava dando erro CORS
# =====================================================
@obras_bp.route("/obras/<int:obra_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar(obra_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    novo_nome = data.get("nome")

    if not novo_nome:
        return jsonify({"error": "Nome é obrigatório"}), 400

    obra_atualizada, error = atualizar_obra(obra_id, novo_nome)

    if error:
        return jsonify({"error": error}), 404

    return jsonify(obra_atualizada), 200


# =====================================================
# DELETAR (DELETE) - Rota que estava dando erro CORS
# =====================================================
@obras_bp.route("/obras/<int:obra_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar(obra_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    # O service retorna None se sucesso, ou string se erro (mas sua implementação retornava False/None)
    # Vamos ajustar baseado no seu service:
    # seu service retorna: return False, "Erro" OU return True, None (assumindo ajuste no service)
    
    # Olhando seu service: ele retorna (False, "msg") ou (None, None) implicito.
    # Vamos assumir que se não retornar erro, deu certo.
    
    err_bool_or_none, msg = deletar_obra(obra_id)
    
    # Nota: No seu service deletar_obra, se der certo ele retorna nada (None).
    # Se der erro, retorna False, "msg". Ajuste conforme necessidade.
    
    if msg: 
        return jsonify({"error": msg}), 404

    return jsonify({"message": "Obra deletada com sucesso"}), 200