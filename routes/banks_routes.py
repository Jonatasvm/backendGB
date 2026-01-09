from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.bank_service import (
    criar_banco,
    listar_bancos,
    atualizar_banco,
    deletar_banco,
    buscar_banco_por_id
)

bancos_bp = Blueprint("bancos", __name__)

# =====================================================
# LISTAR (GET)
# =====================================================
@bancos_bp.route("/bancos", methods=["GET", "OPTIONS"])
@cross_origin()
def listar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        bancos = listar_bancos()
        return jsonify(bancos), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar bancos: {str(e)}"}), 500


# =====================================================
# CRIAR (POST)
# =====================================================
@bancos_bp.route("/bancos", methods=["POST", "OPTIONS"])
@cross_origin()
def criar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    nome = data.get("nome", "").strip()

    if not nome:
        return jsonify({"error": "Nome do banco é obrigatório"}), 400

    try:
        novo_banco = criar_banco(nome)
        return jsonify(novo_banco), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# BUSCAR (GET por ID)
# =====================================================
@bancos_bp.route("/bancos/<int:banco_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def buscar(banco_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        banco = buscar_banco_por_id(banco_id)
        if not banco:
            return jsonify({"error": "Banco não encontrado"}), 404
        return jsonify(banco), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# ATUALIZAR (PUT)
# =====================================================
@bancos_bp.route("/bancos/<int:banco_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar(banco_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    nome = data.get("nome", "").strip()

    if not nome:
        return jsonify({"error": "Nome do banco é obrigatório"}), 400

    try:
        banco = atualizar_banco(banco_id, nome)
        return jsonify(banco), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# DELETAR (DELETE)
# =====================================================
@bancos_bp.route("/bancos/<int:banco_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar(banco_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        deletar_banco(banco_id)
        return jsonify({"message": "Banco deletado com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
