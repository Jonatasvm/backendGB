from flask import Blueprint, request, jsonify,make_response
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
    
    # Consulta para buscar pares distintos de titular e cpf_cnpj que começam com a query
    # Usamos GROUP BY para obter o efeito de DISTINCT em ambas as colunas
    sql_query = """
        SELECT titular, cpf_cnpj 
        FROM formulario 
        WHERE titular LIKE %s 
        GROUP BY titular, cpf_cnpj
        LIMIT 10
    """
    
    # Adicionamos '%' ao final da query para buscar por "começa com"
    search_term = query + "%"
    
    try:
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

    # --- CORREÇÃO DE LÓGICA: Não forçar '0', mas aceitar o valor do payload ('Y') ---
    # Assume 'N' como default se o campo 'lancado' não vier no payload
    valor_lancado = data.get("lancado", "N") 
    
    campos = [
        "data_lancamento", "solicitante", "titular", "referente",
        "valor", "obra", "data_pagamento", "forma_pagamento",
        "cpf_cnpj", "chave_pix", "data_competencia", 
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
        data["data_lancamento"], 
        data["solicitante"], 
        data["titular"], 
        data["referente"],
        data["valor"], 
        data["obra"], 
        data["data_pagamento"], 
        data["forma_pagamento"],
        valor_lancado,  # <--- CORREÇÃO: Usa o valor de 'valor_lancado' (do payload ou default 'N')
        data["cpf_cnpj"], 
        data["chave_pix"], 
        data["data_competencia"],
        data["observacao"]
    ))
    conn.commit()
    formulario_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Formulário criado", "id": formulario_id}), 201

# ===========================
# ATUALIZAR FORMULÁRIO (PUT)
# Rota usada para updates completos E para o status toggle (payload parcial)
# ===========================
@formulario_bp.route("/formulario/<int:form_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar_formulario(form_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    # Adicionando campos opcionais no array para que possam ser atualizados
    campos = [
        "data_lancamento", "solicitante", "titular", "referente",
        "valor", "obra", "data_pagamento", "forma_pagamento",
        "lancado", "cpf_cnpj", "chave_pix", "data_competencia",
        "observacao", "conta", "quem_paga", "link_anexo", "categoria" # Incluídos campos opcionais
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

# =====================================================
# ✅ NOVO: EXPORTAR CSV E LANÇAR MÚLTIPLOS REGISTROS (POST)
# =====================================================
@formulario_bp.route("/formulario/exportar", methods=["POST", "OPTIONS"])
@cross_origin()
def exportar_e_lancar():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    # Esperamos uma lista de IDs [1, 5, 8, ...]
    ids = data.get("ids", []) 

    if not ids:
        return jsonify({"error": "Nenhum ID de registro fornecido."}), 400
    
    # 1. Conexão com o Banco de Dados
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Cria uma string com placeholders (%s) para a query SQL: "%s, %s, %s"
    placeholders = ', '.join(['%s'] * len(ids)) 
    
    try:
        # 2. ATUALIZAÇÃO: Muda o status de 'N' (pendente) para 'Y' (lançado)
        # O banco de dados faz isso em uma única transação, muito mais rápido!
        update_query = f"UPDATE formulario SET lancado = 'Y' WHERE id IN ({placeholders})"
        cursor.execute(update_query, ids)
        
        # 3. BUSCA: Recupera os dados completos dos registros recém-lançados
        select_query = f"SELECT * FROM formulario WHERE id IN ({placeholders}) ORDER BY id ASC"
        cursor.execute(select_query, ids)
        registros = cursor.fetchall()
        
        # Confirma as alterações no banco de dados
        conn.commit()

        # 4. GERAÇÃO do CSV
        
        # Cabeçalhos do CSV (garante que todos os campos estão inclusos)
        csv_headers = [
            "ID", "Data Lancamento", "Solicitante", "Titular", "CPF/CNPJ", 
            "Chave PIX", "Referente", "Valor", "Obra (ID)", "Data Pagamento", 
            "Forma Pagamento", "Data Competencia", "Observacao", "Status",
            "Conta", "Quem Paga", "Link Anexo", "Categoria"
        ]
        
        csv_content = [";".join(csv_headers)] # Primeira linha: cabeçalhos
        
        for r in registros:
            # Converte valores para strings compatíveis com CSV/Excel
            row = [
                str(r.get('id', '')),
                str(r.get('data_lancamento', '')),
                str(r.get('solicitante', '')),
                str(r.get('titular', '')),
                str(r.get('cpf_cnpj', '')),
                str(r.get('chave_pix', '')),
                f'"{str(r.get('referente', '')).replace("\"", "\"\"")}"', # Aspas para aceitar vírgulas internas
                str(r.get('valor', 0)).replace('.', ','), # Formato BR para o Excel
                str(r.get('obra', '')),
                str(r.get('data_pagamento', '')),
                str(r.get('forma_pagamento', '')),
                str(r.get('data_competencia', '')),
                f'"{str(r.get('observacao', '')).replace("\"", "\"\"")}"',
                "LANCADO" if r.get('lancado') == 'Y' else "PENDENTE",
                str(r.get('conta', '')),
                str(r.get('quemPaga', '')),
                str(r.get('linkAnexo', '')),
                str(r.get('categoria', '')),
            ]
            csv_content.append(";".join(row))

        csv_string = "\n".join(csv_content)
        
        # 5. RETORNO: Retorna o arquivo CSV
        response = make_response(csv_string)
        # Define o tipo de conteúdo como CSV e força o download com o nome de arquivo
        response.headers["Content-Disposition"] = "attachment; filename=lancamentos_exportados.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        
        return response, 200

    except Exception as e:
        # Se algo falhar, desfaz a alteração para não ter registros incompletos
        conn.rollback() 
        print(f"Erro ao exportar e lançar: {e}")
        return jsonify({"error": f"Erro interno ao processar a exportação: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# nova rota 
# ===========================
@formulario_bp.route("/titulares/list", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_titulares_distinct():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Busca todos os titulares distintos da tabela 'formulario'
    sql_query = """
        SELECT DISTINCT titular 
        FROM formulario
        WHERE titular IS NOT NULL AND titular != ''
        ORDER BY titular ASC
    """
    
    try:
        cursor.execute(sql_query)
        registros = cursor.fetchall()
        
        # Formata a resposta para { id: NOME, nome: NOME }
        titulares_formatados = [{
            "id": t['titular'], 
            "nome": t['titular']
        } for t in registros]
        
        return jsonify(titulares_formatados), 200
    except Exception as e:
        print(f"Erro ao buscar lista de titulares: {e}")
        return jsonify({"error": "Erro interno ao buscar titulares"}), 500
    finally:
        cursor.close()
        conn.close()