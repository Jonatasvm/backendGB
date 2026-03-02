from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.historico_service import registrar_exportacao, listar_exportacoes, buscar_itens_exportacao

historico_bp = Blueprint("historico", __name__)


# ======================================================
# REGISTRAR EXPORTAÇÃO (POST)
# ======================================================
@historico_bp.route("/historico/exportacoes", methods=["POST", "OPTIONS"])
@cross_origin()
def criar_exportacao():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    usuario = data.get("usuario", "")
    formulario_ids = data.get("formulario_ids", [])

    if not formulario_ids:
        return jsonify({"error": "Nenhum formulário informado"}), 400

    exportacao_id, error = registrar_exportacao(usuario, formulario_ids)

    if error:
        return jsonify({"error": error}), 500

    return jsonify({
        "message": "Exportação registrada com sucesso",
        "id": exportacao_id
    }), 201


# ======================================================
# LISTAR EXPORTAÇÕES (GET)
# ======================================================
@historico_bp.route("/historico/exportacoes", methods=["GET", "OPTIONS"])
@cross_origin()
def listar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    exportacoes, error = listar_exportacoes()

    if error:
        return jsonify({"error": error}), 500

    return jsonify({"exportacoes": exportacoes}), 200


# ======================================================
# BUSCAR ITENS DE UMA EXPORTAÇÃO (GET)
# ======================================================
@historico_bp.route("/historico/exportacoes/<int:exportacao_id>/itens", methods=["GET", "OPTIONS"])
@cross_origin()
def buscar_itens(exportacao_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    ids, error = buscar_itens_exportacao(exportacao_id)

    if error:
        return jsonify({"error": error}), 500

    return jsonify({"formulario_ids": ids}), 200
