from flask import Blueprint, request, jsonify, make_response
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
    if not query:
        return jsonify([]), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = """
            SELECT titular, cpf_cnpj 
            FROM formulario 
            WHERE titular LIKE %s 
            GROUP BY titular, cpf_cnpj
            LIMIT 10
        """
        search_term = query + "%"
        cursor.execute(sql_query, (search_term,))
        titulares = cursor.fetchall()
        return jsonify(titulares), 200
    except Exception as e:
        print(f"Erro ao buscar titulares: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500
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
    try:
        cursor.execute("SELECT * FROM formulario ORDER BY id DESC")
        formularios = cursor.fetchall()
        return jsonify(formularios), 200
    except Exception as e:
        print(f"Erro ao listar: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===========================
# CRIAR FORMULÁRIO (POST)
# ===========================
@formulario_bp.route("/formulario", methods=["POST", "OPTIONS"])
@cross_origin()
def criar_formulario():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()

    # Define 'N' (Não lançado) como default se o campo 'lancado' não vier no payload
    valor_lancado = data.get("lancado", "N") 
    
    campos = [
        "data_lancamento", "solicitante", "titular", "referente",
        "valor", "obra", "data_pagamento", "forma_pagamento",
        "cpf_cnpj", "chave_pix", "data_competencia", 
        "observacao"
    ]

    for campo in campos:
        if campo not in data:
            return jsonify({"error": f"Campo '{campo}' é obrigatório"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO formulario (
                data_lancamento, solicitante, titular, referente, valor, obra, 
                data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                data_competencia, carimbo, observacao
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (
            data["data_lancamento"], 
            data["solicitante"], 
            data["titular"], 
            data["referente"],
            data["valor"], 
            data["obra"], 
            data["data_pagamento"], 
            data["forma_pagamento"],
            valor_lancado, # Corrigido: Removido caractere invisível que existia aqui
            data["cpf_cnpj"], 
            data["chave_pix"], 
            data["data_competencia"],
            data["observacao"]
        ))
        conn.commit()
        formulario_id = cursor.lastrowid
        return jsonify({"message": "Formulário criado", "id": formulario_id}), 201
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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
        "observacao", "conta", "quem_paga", "link_anexo", "categoria"
    ]

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
    try:
        cursor.execute(query, tuple(valores))
        conn.commit()
        return jsonify({"message": "Formulário atualizado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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
    try:
        cursor.execute("DELETE FROM formulario WHERE id = %s", (form_id,))
        conn.commit()
        return jsonify({"message": "Formulário deletado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===========================
# ATUALIZAR STATUS DE LANÇAMENTO (Toggle Individual)
# ===========================
@formulario_bp.route("/formulario/<int:id>/status", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar_status_lancamento(id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    lancado_status = data.get("lancado")

    if lancado_status not in ['Y', 'N']:
        return jsonify({"error": "Status inválido."}), 400
    
    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql_query = "UPDATE formulario SET lancado = %s WHERE id = %s"
        cursor.execute(sql_query, (lancado_status, id))
        conn.commit()
        
        if cursor.rowcount == 0:
             return jsonify({"error": "Formulário não encontrado."}), 404
             
        return jsonify({"message": f"Status atualizado."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===========================
# EXPORTAR CSV E LANÇAR MÚLTIPLOS (POST)
# ===========================
@formulario_bp.route("/formulario/exportar", methods=["POST", "OPTIONS"])
@cross_origin()
def exportar_e_lancar_formularios():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    ids = data.get("ids", []) 

    if not ids:
        return jsonify({"error": "Nenhum ID fornecido."}), 400
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    placeholders = ', '.join(['%s'] * len(ids)) 
    
    try:
        update_query = f"UPDATE formulario SET lancado = 'Y' WHERE id IN ({placeholders})"
        cursor.execute(update_query, tuple(ids)) 
        
        select_query = f"""
            SELECT id, data_lancamento, solicitante, titular, cpf_cnpj, chave_pix, 
                   referente, valor, obra, data_pagamento, forma_pagamento, 
                   data_competencia, observacao, lancado, conta, quem_paga, 
                   link_anexo, categoria
            FROM formulario 
            WHERE id IN ({placeholders}) 
            ORDER BY id ASC
        """
        cursor.execute(select_query, tuple(ids)) 
        registros = cursor.fetchall()
        
        conn.commit()

        # GERAÇÃO DO CSV
        csv_headers = [
            "ID", "Data Lancamento", "Solicitante", "Titular", "CPF/CNPJ", 
            "Chave PIX", "Referente", "Valor", "Obra (ID)", "Data Pagamento", 
            "Forma Pagamento", "Data Competencia", "Observacao", "Status",
            "Conta", "Quem Paga", "Link Anexo", "Categoria"
        ]
        
        csv_content = [";".join(csv_headers)]
        
        for r in registros:
            # CORREÇÃO PRINCIPAL AQUI:
            # Tratamento das strings com aspas antes de inserir na f-string para evitar erro de sintaxe
            # O uso de 'or ""' garante que não quebre se o campo for None
            referente_clean = str(r.get('referente') or '').replace('"', '""')
            observacao_clean = str(r.get('observacao') or '').replace('"', '""')
            
            # Formatação do valor (trocando ponto por vírgula para Excel BR)
            valor_fmt = str(r.get('valor', 0)).replace('.', ',')

            row = [
                str(r.get('id', '')),
                str(r.get('data_lancamento') or ''),
                str(r.get('solicitante') or ''),
                str(r.get('titular') or ''),
                str(r.get('cpf_cnpj') or ''),
                str(r.get('chave_pix') or ''),
                f'"{referente_clean}"',  # Agora é seguro
                valor_fmt, 
                str(r.get('obra') or ''),
                str(r.get('data_pagamento') or ''),
                str(r.get('forma_pagamento') or ''),
                str(r.get('data_competencia') or ''),
                f'"{observacao_clean}"', # Agora é seguro
                "LANCADO" if r.get('lancado') == 'Y' else "PENDENTE",
                str(r.get('conta') or ''),
                str(r.get('quem_paga') or ''),
                str(r.get('link_anexo') or ''),
                str(r.get('categoria') or ''),
            ]
            csv_content.append(";".join(row))

        csv_string = "\ufeff" + "\n".join(csv_content) 
        
        response = make_response(csv_string)
        response.headers["Content-Disposition"] = "attachment; filename=lancamentos_exportados.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        
        return response, 200

    except Exception as e:
        conn.rollback() 
        print(f"Erro ao exportar e lançar: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# ===========================
# LISTAR TITULARES (NOVA ROTA)
# ===========================
@formulario_bp.route("/titulares/list", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_titulares_distinct():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = """
            SELECT DISTINCT titular 
            FROM formulario
            WHERE titular IS NOT NULL AND titular != ''
            ORDER BY titular ASC
        """
        cursor.execute(sql_query)
        registros = cursor.fetchall()
        
        titulares_formatados = [{"id": t['titular'], "nome": t['titular']} for t in registros]
        
        return jsonify(titulares_formatados), 200
    except Exception as e:
        print(f"Erro ao buscar lista: {e}")
        return jsonify({"error": "Erro interno"}), 500
    finally:
        cursor.close()
        conn.close()