from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection

fornecedor_bp = Blueprint("fornecedor", __name__)

# ===========================
# LISTAR TODOS OS FORNECEDORES (GET)
# ===========================
@fornecedor_bp.route("/fornecedor", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_fornecedores():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fornecedor ORDER BY titular ASC")
    fornecedores = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(fornecedores), 200


# ===========================
# BUSCAR FORNECEDOR POR ID (GET)
# ===========================
@fornecedor_bp.route("/fornecedor/<int:fornecedor_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def obter_fornecedor(fornecedor_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fornecedor WHERE id = %s", (fornecedor_id,))
    fornecedor = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not fornecedor:
        return jsonify({"error": "Fornecedor não encontrado"}), 404
    
    return jsonify(fornecedor), 200


# ===========================
# CRIAR FORNECEDOR (POST)
# ===========================
@fornecedor_bp.route("/fornecedor", methods=["POST", "OPTIONS"])
@cross_origin()
def criar_fornecedor():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    
    # Validação
    if not data.get("titular") or not data.get("cpf_cnpj"):
        return jsonify({"error": "Campos 'titular' e 'cpf_cnpj' são obrigatórios"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO fornecedor (titular, cpf_cnpj, chave_pix, banco_padrao)
            VALUES (%s, %s, %s, %s)
        """, (
            data["titular"],
            data["cpf_cnpj"],
            data.get("chave_pix"),
            data.get("banco_padrao")
        ))
        conn.commit()
        fornecedor_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Fornecedor criado com sucesso",
            "id": fornecedor_id
        }), 201
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        
        if "Duplicate entry" in str(e):
            return jsonify({"error": "CPF/CNPJ já cadastrado"}), 409
        
        print(f"Erro ao criar fornecedor: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


# ===========================
# ATUALIZAR FORNECEDOR (PUT)
# ===========================
@fornecedor_bp.route("/fornecedor/<int:fornecedor_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar_fornecedor(fornecedor_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    campos = ["titular", "cpf_cnpj", "chave_pix", "banco_padrao"]
    
    # Atualiza apenas os campos enviados
    set_clauses = []
    valores = []
    for campo in campos:
        if campo in data:
            set_clauses.append(f"{campo} = %s")
            valores.append(data[campo])

    if not set_clauses:
        return jsonify({"error": "Nenhum campo para atualizar"}), 400

    valores.append(fornecedor_id)
    query = f"UPDATE fornecedor SET {', '.join(set_clauses)} WHERE id = %s"

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, tuple(valores))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Fornecedor atualizado com sucesso"}), 200
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        
        if "Duplicate entry" in str(e):
            return jsonify({"error": "CPF/CNPJ já cadastrado"}), 409
        
        print(f"Erro ao atualizar fornecedor: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


# ===========================
# DELETAR FORNECEDOR (DELETE)
# ===========================
@fornecedor_bp.route("/fornecedor/<int:fornecedor_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar_fornecedor(fornecedor_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM fornecedor WHERE id = %s", (fornecedor_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Fornecedor deletado com sucesso"}), 200
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Erro ao deletar fornecedor: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500
