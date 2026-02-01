from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection
from services.google_drive_service import upload_files_batch, create_folder
import json

formulario_bp = Blueprint("formulario", __name__)

# BUSCAR FORNECEDORES PARA AUTOCOMPLETE (GET)
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
    
    # Consulta a tabela 'fornecedor' em vez de 'formulario'
    sql_query = """
        SELECT id, titular, cpf_cnpj 
        FROM fornecedor 
        WHERE titular LIKE %s 
        ORDER BY titular ASC
        LIMIT 10
    """
    
    search_term = query + "%"
    
    try:
        cursor.execute(sql_query, (search_term,))
        fornecedores = cursor.fetchall()
        return jsonify(fornecedores), 200
    except Exception as e:
        print(f"Erro ao buscar fornecedores: {e}")
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
    
    # ✅ NOVO: Usar ROW_NUMBER para pegar apenas o PRIMEIRO lançamento de cada grupo
    # Para lançamentos múltiplos: agrupa por grupo_lancamento ou multiplos_lancamentos
    # Para lançamentos simples: cada um é seu próprio grupo
    cursor.execute("""
        SELECT f.* FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY CASE 
                           WHEN grupo_lancamento IS NOT NULL THEN CONCAT('grupo_', grupo_lancamento)
                           WHEN multiplos_lancamentos = 1 THEN CONCAT('multi_', DATE_FORMAT(data_lancamento, '%Y%m%d'), '_', solicitante, '_', titular)
                           ELSE CONCAT('individual_', id)
                       END 
                       ORDER BY id ASC
                   ) as rn
            FROM formulario
        ) f
        WHERE f.rn = 1
        ORDER BY f.id DESC
    """)
    formularios = cursor.fetchall()
    
    # ✅ NOVO: Carregar obras relacionadas e calcular valor total para cada lançamento
    for form in formularios:
        # Converter valores Decimal para float
        if "valor" in form and form["valor"] is not None:
            form["valor"] = float(form["valor"])
        
        obras_relacionadas = []
        
        # Se tem grupo_lancamento, buscar relacionados pelo grupo
        if form.get("grupo_lancamento"):
            cursor.execute("""
                SELECT id, obra, valor, referente, data_pagamento, forma_pagamento
                FROM formulario
                WHERE grupo_lancamento = %s AND id != %s
                ORDER BY id ASC
            """, (form["grupo_lancamento"], form["id"]))
            obras_relacionadas = cursor.fetchall()
            
        # Se é múltiplo mas sem grupo_lancamento (antigo), buscar relacionados
        elif form.get("multiplos_lancamentos") == 1:
            cursor.execute("""
                SELECT id, obra, valor, referente, data_pagamento, forma_pagamento
                FROM formulario
                WHERE multiplos_lancamentos = 1 
                AND DATE_FORMAT(data_lancamento, '%Y%m%d') = DATE_FORMAT(%s, '%Y%m%d')
                AND solicitante = %s
                AND titular = %s
                AND id != %s
                ORDER BY id ASC
            """, (form["data_lancamento"], form["solicitante"], form["titular"], form["id"]))
            obras_relacionadas = cursor.fetchall()
        
        # Se tem obras relacionadas, armazenar e CALCULAR VALOR TOTAL
        if obras_relacionadas:
            # Converter Decimal para float para JSON serialization
            obras_relacionadas_clean = []
            for obra in obras_relacionadas:
                obra_clean = dict(obra)
                if "valor" in obra_clean:
                    obra_clean["valor"] = float(obra_clean["valor"]) if obra_clean["valor"] else 0
                obras_relacionadas_clean.append(obra_clean)
            
            form["obras_relacionadas"] = obras_relacionadas_clean
            
            # Calcular valor total (principal + todos os relacionados)
            valor_total = float(form.get("valor") or 0)
            for obra in obras_relacionadas_clean:
                valor_total += float(obra.get("valor") or 0)
            
            # Armazenar o valor total (para exibição na tabela)
            form["valor_total"] = valor_total
            # Manter o valor original para compatibilidade
            form["valor_principal"] = float(form.get("valor") or 0)
    
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
    
    # ✅ DEBUG: Log completo do payload recebido
    print("\n" + "="*70)
    print("📥 POST /formulario - Payload recebido:")
    print(f"  multiplos_lancamentos: {data.get('multiplos_lancamentos')}")
    print(f"  obras_adicionais: {data.get('obras_adicionais')}")
    print(f"  obra (principal): {data.get('obra')}")
    print(f"  valor (total): {data.get('valor')}")
    print("="*70)
    
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
    campos_opcionais = ["conta", "quem_paga", "categoria"]  # ✅ NOVO: Adicionados como opcionais

    # Validação simples
    for campo in campos:
        if campo not in data:
            return jsonify({"error": f"Campo '{campo}' é obrigatório"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    
    # ✅ Gerar grupo de lançamento único para múltiplas obras
    grupo_lancamento = None
    if data.get("multiplos_lancamentos") and data.get("obras_adicionais") and len(data.get("obras_adicionais", [])) > 0:
        import uuid
        grupo_lancamento = str(uuid.uuid4())[:8]  # ID curto para agrupar
        print(f"✅ Gerando grupo_lancamento: {grupo_lancamento}")
    
    try:
        # ✅ NOVO: Se for múltiplos lançamentos, criar UM registro para CADA obra no array
        if data.get("multiplos_lancamentos") and data.get("obras_adicionais"):
            obras_adicionais = data.get("obras_adicionais", [])
            
            if isinstance(obras_adicionais, str):
                print(f"⚠️ AVISO: obras_adicionais veio como STRING: {obras_adicionais}")
                obras_adicionais = []
            
            print(f"\n✅ MÚLTIPLO LANÇAMENTO DETECTADO")
            print(f"   Total de obras a criar: {len(obras_adicionais)}")
            print(f"   grupo_lancamento: {grupo_lancamento}\n")
            
            for idx, obra_info in enumerate(obras_adicionais, 1):
                obra_id = obra_info.get("obra_id")
                valor = obra_info.get("valor", 0)
                
                print(f"   [{idx}] Processando obra {obra_id} com valor {valor}")
                if isinstance(valor, str):
                    valor_limpo = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    valor = float(valor_limpo) if valor_limpo else 0
                else:
                    valor = float(valor) if valor else 0
                
                print(f"   → Obra {obra_id}: R$ {valor}")
                
                if valor > 0:
                    try:
                        cursor.execute("""
                            INSERT INTO formulario (
                                data_lancamento, solicitante, titular, referente, valor, obra, 
                                data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                                data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, grupo_lancamento
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
                        """, (
                            data["data_lancamento"], 
                            data["solicitante"], 
                            data["titular"], 
                            data["referente"],
                            valor,  # Valor específico desta obra
                            obra_id,  # ID da obra
                            data["data_pagamento"], 
                            data["forma_pagamento"],
                            valor_lancado,
                            data["cpf_cnpj"], 
                            data["chave_pix"], 
                            data["data_competencia"],
                            data["observacao"],
                            data.get("conta"),
                            data.get("categoria"),
                            data.get("multiplos_lancamentos", 0),
                            grupo_lancamento  # Mesmo grupo para todas
                        ))
                        conn.commit()
                        formulario_id = cursor.lastrowid
                        print(f"      ✅ Inserido com sucesso! ID: {formulario_id} (grupo={grupo_lancamento})")
                    except Exception as e_grupo:
                        # Se falhar com grupo_lancamento, tenta sem
                        print(f"      ⚠️ Erro com grupo_lancamento: {e_grupo}, tentando sem...")
                        try:
                            cursor.execute("""
                                INSERT INTO formulario (
                                    data_lancamento, solicitante, titular, referente, valor, obra, 
                                    data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s)
                            """, (
                                data["data_lancamento"], 
                                data["solicitante"], 
                                data["titular"], 
                                data["referente"],
                                valor,
                                obra_id,
                                data["data_pagamento"], 
                                data["forma_pagamento"],
                                valor_lancado,
                                data["cpf_cnpj"], 
                                data["chave_pix"], 
                                data["data_competencia"],
                                data["observacao"],
                                data.get("conta"),
                                data.get("categoria"),
                                data.get("multiplos_lancamentos", 0)
                            ))
                            conn.commit()
                            formulario_id = cursor.lastrowid
                            print(f"      ✅ Inserido SEM grupo com ID {formulario_id}")
                        except Exception as e:
                            print(f"      ❌ ERRO ao inserir obra {obra_id}: {e}")
                            conn.rollback()
            print("="*70)
        else:
            # Inserir o lançamento principal (para lançamentos simples, não múltiplos)
            print(f"✅ LANÇAMENTO SIMPLES (não múltiplo)")
            cursor.execute("""
                INSERT INTO formulario (
                    data_lancamento, solicitante, titular, referente, valor, obra, 
                    data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, grupo_lancamento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
            """, (
                data["data_lancamento"], 
                data["solicitante"], 
                data["titular"], 
                data["referente"],
                data["valor"], 
                data["obra"], 
                data["data_pagamento"], 
                data["forma_pagamento"],
                valor_lancado,
                data["cpf_cnpj"], 
                data["chave_pix"], 
                data["data_competencia"],
                data["observacao"],
                data.get("conta"),
                data.get("categoria"),
                data.get("multiplos_lancamentos", 0),
                grupo_lancamento
            ))
            conn.commit()
            formulario_id = cursor.lastrowid
            print(f"✅ LANÇAMENTO SIMPLES - Criado com ID {formulario_id}")
    except Exception as e:
        # Se falhar (provavelmente coluna grupo_lancamento não existe), tenta sem ela
        print(f"⚠️ Erro ao inserir com grupo_lancamento: {e}")
        if not (data.get("multiplos_lancamentos") and data.get("obras_adicionais")):
            cursor.execute("""
                INSERT INTO formulario (
                    data_lancamento, solicitante, titular, referente, valor, obra, 
                    data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s)
            """, (
                data["data_lancamento"], 
                data["solicitante"], 
                data["titular"], 
                data["referente"],
                data["valor"], 
                data["obra"], 
                data["data_pagamento"], 
                data["forma_pagamento"],
                valor_lancado,
                data["cpf_cnpj"], 
                data["chave_pix"], 
                data["data_competencia"],
                data["observacao"],
                data.get("conta"),
                data.get("categoria"),
                data.get("multiplos_lancamentos", 0)
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