# C:\Users\Borracharia\IdeaProjects\backendGB\routes\formulario_routes.py

## =========================================================
## 1. IMPORTS COMBINADOS
## =========================================================
from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from db import get_connection
import pandas as pd
from io import BytesIO
import json

formulario_bp = Blueprint("formulario", __name__)


## =========================================================
## 2. SUAS ROTAS EXISTENTES (CÓDIGO BASE)
## =========================================================

# ROTA BUSCAR TITULARES (AUTOCOMPLETE)
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
    sql_query = """
        SELECT titular, cpf_cnpj 
        FROM formulario 
        WHERE titular LIKE %s 
        GROUP BY titular, cpf_cnpj
        LIMIT 10
    """
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

# ROTA LISTAR TODOS OS FORMULÁRIOS (GET)
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

# ROTA CRIAR FORMULÁRIO (POST)
@formulario_bp.route("/formulario", methods=["POST", "OPTIONS"])
@cross_origin()
def criar_formulario():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    data = request.get_json()
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
    cursor.execute("""
        INSERT INTO formulario (
            data_lancamento, solicitante, titular, referente, valor, obra, 
            data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
            data_competencia, carimbo, observacao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
    """, (
        data["data_lancamento"], data["solicitante"], data["titular"], data["referente"],
        data["valor"], data["obra"], data["data_pagamento"], data["forma_pagamento"],
        valor_lancado, data["cpf_cnpj"], data["chave_pix"], data["data_competencia"],
        data["observacao"]
    ))
    conn.commit()
    formulario_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Formulário criado", "id": formulario_id}), 201

# ROTA ATUALIZAR FORMULÁRIO (PUT)
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
    cursor.execute(query, tuple(valores))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Formulário atualizado"}), 200

# ROTA DELETAR FORMULÁRIO (DELETE)
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


## =======================================================================
## 3. ✅ CÓDIGO CORRIGIDO E APRIMORADO PARA EXPORTAÇÃO
## =======================================================================

# FUNÇÃO AUXILIAR PARA BUSCAR DADOS POR IDS
def get_records_by_ids(ids):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Cria uma string com placeholders para a query SQL: "%s, %s, %s..."
    placeholders = ', '.join(['%s'] * len(ids))
    
    # Consulta SQL para buscar os registros cujos IDs estão na lista
    sql_query = f"SELECT * FROM formulario WHERE id IN ({placeholders}) ORDER BY data_lancamento DESC"
    
    try:
        # A lista de IDs é convertida para uma tupla para execução segura
        cursor.execute(sql_query, tuple(ids))
        records = cursor.fetchall()
        return records
    except Exception as e:
        print(f"Erro ao buscar registros para exportação: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# NOVA ROTA: EXPORTAR REGISTROS SELECIONADOS PARA XLSX
@formulario_bp.route('/formulario/export/xls', methods=['POST', 'OPTIONS'])
@cross_origin()
def exportar_formularios_para_xls():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
        
    try:
        data = request.get_json()
        ids = data.get('ids', [])

        if not ids:
            return jsonify({"message": "Nenhum ID de registro fornecido para exportação."}), 400

        # Busca os dados no DB usando a função auxiliar
        records = get_records_by_ids(ids)
        
        if not records:
            # Importante: O frontend está esperando ler esta mensagem em caso de 404
            return jsonify({"message": "Nenhum registro encontrado para os IDs fornecidos."}), 404
        
        df = pd.DataFrame(records)
        
        # 1. RENOMEIA COLUNAS para torná-las amigáveis no Excel
        column_rename = {
            'id': 'ID',
            'data_lancamento': 'Data Lançamento',
            'solicitante': 'Solicitante',
            'titular': 'Titular',
            'referente': 'Referente',
            'valor': 'Valor',
            'obra': 'Obra',
            'data_pagamento': 'Data Pagamento',
            'forma_pagamento': 'Forma de Pagto',
            'lancado': 'Lançado (S/N)',
            'cpf_cnpj': 'CPF/CNPJ',
            'chave_pix': 'Chave PIX',
            'data_competencia': 'Data Competência',
            'observacao': 'Observação',
            'conta': 'Conta',
            'quem_paga': 'Quem Paga',
            'link_anexo': 'Link Anexo',
            'categoria': 'Categoria',
            # 'carimbo' é removido abaixo
        }
        df.rename(columns=column_rename, inplace=True)
        
        # 2. REMOVE COLUNAS TÉCNICAS que não são necessárias no relatório
        columns_to_drop = [col for col in ['carimbo'] if col in df.columns]
        if columns_to_drop:
             df = df.drop(columns=columns_to_drop)
        
        # 3. Processo de geração do Excel
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Registros Selecionados', index=False)
        
        output.seek(0)
        
        # 4. Cria e retorna a resposta
        response = make_response(output.read())
        response.headers['Content-Disposition'] = 'attachment; filename=registros_selecionados.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        
        return response

    except Exception as e:
        print(f"Erro interno ao exportar: {e}")
        # Retorna 500 com JSON
        return jsonify({"message": f"Erro interno de servidor: {str(e)}"}), 500


## =========================================================
## 4. SUA OUTRA ROTA (CÓDIGO BASE)
## =========================================================
@formulario_bp.route("/titulares/list", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_titulares_distinct():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql_query = """
        SELECT DISTINCT titular 
        FROM formulario
        WHERE titular IS NOT NULL AND titular != ''
        ORDER BY titular ASC
    """
    try:
        cursor.execute(sql_query)
        registros = cursor.fetchall()
        titulares_formatados = [{"id": t['titular'], "nome": t['titular']} for t in registros]
        return jsonify(titulares_formatados), 200
    except Exception as e:
        print(f"Erro ao buscar lista de titulares: {e}")
        return jsonify({"error": "Erro interno ao buscar titulares"}), 500
    finally:
        cursor.close()
        conn.close()