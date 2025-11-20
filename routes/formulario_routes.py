from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection

formulario_bp = Blueprint("formulario", __name__)

# ===========================
# LISTAR TODOS OS FORMULÁRIOS (GET)
# ===========================
@formulario_bp.route("/formulario", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_formularios():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM formulario ORDER BY id DESC")
    formularios = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(formularios), 200

# ===========================
# CRIAR FORMULÁRIO (POST)
# ===========================
@formulario_bp.route("/formulario", methods=["POST", "OPTIONS"])
@cross_origin()
def criar_formulario():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()

    campos = [
        "data_lancamento", "solicitante", "titular", "referente",
        "valor", "obra", "data_pagamento", "forma_pagamento",
        "lancado", "cpf_cnpj", "chave_pix", "data_competencia",
        "observacao"
    ]

    # Validação simples
    for campo in campos:
        if campo not in data:
            return jsonify({"error": f"Campo '{campo}' é obrigatório"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO formulario (
            data_lancamento, solicitante, titular, referente, valor, obra, 
            data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
            data_competencia, carimbo, observacao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
    """, (
        data["data_lancamento"], data["solicitante"], data["titular"], data["referente"],
        data["valor"], data["obra"], data["data_pagamento"], data["forma_pagamento"],
        data["lancado"], data["cpf_cnpj"], data["chave_pix"], data["data_competencia"],
        data["observacao"]
    ))
    conn.commit()
    formulario_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Formulário criado", "id": formulario_id}), 201

# ===========================
# ATUALIZAR FORMULÁRIO (PUT)
# ===========================
@formulario_bp.route("/formulario/<int:form_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar_formulario(form_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    campos = [
        "data_lancamento", "solicitante", "titular", "referente",
        "valor", "obra", "data_pagamento", "forma_pagamento",
        "lancado", "cpf_cnpj", "chave_pix", "data_competencia",
        "observacao"
    ]

    # Atualiza apenas os campos enviados
    set_clauses = []
    valores = []
    for campo in campos:
        if campo in data:
            set_clauses.append(f"{campo} = %s")
            valores.append(data[campo])

    if not set_clauses:
        return jsonify({"error": "Nenhum campo para atualizar"}), 400

    query = f"UPDATE formulario SET {', '.join(set_clauses)} WHERE id = %s"
    valores.append(form_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(valores))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Formulário atualizado"}), 200

# ===========================
# DELETAR FORMULÁRIO (DELETE)
# ===========================
@formulario_bp.route("/formulario/<int:form_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar_formulario(form_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM formulario WHERE id = %s", (form_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Formulário deletado"}), 200
