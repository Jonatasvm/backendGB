from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection

formulario_bp = Blueprint("formulario", __name__)

# ===========================
# BUSCAR TITULARES PARA AUTOCOMPLETE (GET)
# ===========================
@formulario_bp.route("/formulario/titulares/search", methods=["GET", "OPTIONS"])
@cross_origin()
def buscar_titulares():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    query = request.args.get("q", "")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Base da consulta para buscar pares distintos de titular e cpf_cnpj
    sql_query = """
        SELECT DISTINCT titular, cpf_cnpj 
        FROM formulario
    """
    
    # 1. Se houver query (para autocomplete), aplica a condição LIKE e o LIMIT
    if query:
        sql_query += " WHERE titular LIKE %s "
        sql_query += " GROUP BY titular, cpf_cnpj LIMIT 10 "
        search_term = query + "%"
        params = (search_term,)
    # 2. Se a query estiver vazia (para filtro), traz TODOS os distintos
    else:
        sql_query += " GROUP BY titular, cpf_cnpj ORDER BY titular ASC "
        params = () # Nenhum parâmetro
    
    try:
        cursor.execute(sql_query, params)
        titulares = cursor.fetchall()
        
        # Formatando para o filtro: transforma o nome em "ID" temporário.
        # O frontend tratará o Titular como uma string de nome/cpf_cnpj
        titulares_formatados = [{
            "id": f"{t['titular']} - {t['cpf_cnpj']}", # Usamos a string completa como ID
            "nome": t['titular']
        } for t in titulares]
        
        return jsonify(titulares_formatados), 200
    except Exception as e:
        print(f"Erro ao buscar titulares: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

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
