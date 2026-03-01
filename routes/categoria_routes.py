from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.categoria_service import (
    criar_categoria,
    listar_categorias,
    atualizar_categoria,
    deletar_categoria,
    buscar_categoria_por_id
)

categoria_bp = Blueprint("categoria", __name__, url_prefix="")

# =====================================================
# LISTAR (GET)
# ======================================================
@categoria_bp.route("/categoria", methods=["GET", "OPTIONS"])
@cross_origin()
def listar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        categorias = listar_categorias()
        return jsonify(categorias), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar categorias: {str(e)}"}), 500


# =====================================================
# BUSCAR POR ID (GET)
# =====================================================
@categoria_bp.route("/categoria/<int:categoria_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def buscar_por_id(categoria_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        categoria = buscar_categoria_por_id(categoria_id)
        if not categoria:
            return jsonify({"error": "Categoria não encontrada"}), 404
        return jsonify(categoria), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar categoria: {str(e)}"}), 500


# =====================================================
# CRIAR (POST)
# =====================================================
@categoria_bp.route("/categoria", methods=["POST", "OPTIONS"])
@cross_origin()
def criar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    nome = data.get("nome", "").strip()
    descricao = (data.get("descricao") or "").strip()

    if not nome:
        return jsonify({"error": "Nome da categoria é obrigatório"}), 400

    try:
        categoria_id, erro = criar_categoria(nome, descricao if descricao else None)
        
        if erro:
            return jsonify({"error": erro}), 400
        
        return jsonify({
            "message": "Categoria criada com sucesso",
            "id": categoria_id
        }), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao criar categoria: {str(e)}"}), 500


# =====================================================
# ATUALIZAR (PUT)
# =====================================================
@categoria_bp.route("/categoria/<int:categoria_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar(categoria_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    nome = (data.get("nome") or "").strip() if data.get("nome") else None
    descricao = (data.get("descricao") or "").strip() if data.get("descricao") else None

    try:
        categoria_id_result, erro = atualizar_categoria(categoria_id, nome, descricao)
        
        if erro:
            return jsonify({"error": erro}), 400
        
        return jsonify({"message": "Categoria atualizada com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao atualizar categoria: {str(e)}"}), 500


# =====================================================
# DELETAR (DELETE)
# =====================================================
@categoria_bp.route("/categoria/<int:categoria_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar(categoria_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        result, erro = deletar_categoria(categoria_id)
        
        if erro:
            return jsonify({"error": erro}), 400
        
        return jsonify({"message": "Categoria deletada com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao deletar categoria: {str(e)}"}), 500
