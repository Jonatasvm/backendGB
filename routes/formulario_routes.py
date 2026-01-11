from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection
from services.google_drive_service import upload_files_batch, create_folder
import json

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
    
    # Campos opcionais
    campos_opcionais = ["conta", "quem_paga"]  # ✅ NOVO: Adicionados como opcionais

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
            data_competencia, carimbo, observacao, conta
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
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
        data["observacao"],
        data.get("conta")  # ✅ NOVO: Adiciona conta (opcional)
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
        "observacao", "conta", "link_anexo", "categoria" # Incluídos campos opcionais
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

# ===========================
# UPLOAD DE ARQUIVOS PARA GOOGLE DRIVE (POST)
# ===========================
@formulario_bp.route("/formulario/<int:form_id>/upload-anexos", methods=["POST", "OPTIONS"])
@cross_origin()
def upload_anexos(form_id):
    """
    Realiza upload de múltiplos arquivos para Google Drive
    e salva os links no banco de dados
    
    Espera:
    - files: Múltiplos arquivos via form-data
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        print(f"[INFO] Iniciando upload para formulário ID: {form_id}")
        
        # Validar se o formulário existe
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, obra FROM formulario WHERE id = %s", (form_id,))
        formulario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not formulario:
            print(f"[ERRO] Formulário {form_id} não encontrado")
            return jsonify({"error": "Formulário não encontrado"}), 404
        
        print(f"[INFO] Formulário encontrado. Obra: {formulario.get('obra')}")
        
        # Obter arquivos do request
        files = request.files.getlist('files')
        print(f"[INFO] Total de arquivos recebidos: {len(files)}")
        
        if not files:
            print(f"[ERRO] Nenhum arquivo foi enviado")
            return jsonify({"error": "Nenhum arquivo foi enviado"}), 400
        
        obra_id = formulario.get('obra', 'sem-obra')
        
        # Fazer upload para Google Drive
        print(f"[INFO] Iniciando upload dos arquivos para Google Drive")
        upload_results = upload_files_batch(files, form_id, obra_id)
        
        if not upload_results:
            print(f"[ERRO] Falha ao fazer upload dos arquivos")
            return jsonify({"error": "Falha ao fazer upload dos arquivos"}), 500
        
        print(f"[INFO] Arquivos upados com sucesso: {len(upload_results)}")
        
        # Salvar links no banco de dados (JSON)
        conn = get_connection()
        cursor = conn.cursor()
        
        # Converter lista de links para JSON
        links_json = json.dumps(upload_results)
        print(f"[INFO] Salvando links no banco de dados")
        
        cursor.execute(
            "UPDATE formulario SET link_anexo = %s WHERE id = %s",
            (links_json, form_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[INFO] Upload completado com sucesso para formulário {form_id}")
        
        return jsonify({
            "message": "Arquivos enviados com sucesso",
            "form_id": form_id,
            "files": upload_results
        }), 200
    
    except Exception as e:
        print(f"[ERRO] Erro ao fazer upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro ao fazer upload: {str(e)}"}), 500