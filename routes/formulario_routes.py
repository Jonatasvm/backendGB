from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection
from services.google_drive_service import upload_files_batch, create_folder
import json
import sys

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
# ENDPOINT DE TESTE - Confirma que o código novo está rodando
# ===========================
@formulario_bp.route("/formulario/version", methods=["GET"])
@cross_origin()
def version_check():
    return jsonify({"version": "2026-03-11-stderr", "fornecedor_novo_ativo": True}), 200

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
    # Apenas agrupa registros que têm grupo_lancamento
    # Registros SEM grupo_lancamento são retornados normalmente
    cursor.execute("""
        SELECT f.* FROM (
            SELECT *,
                   CASE 
                       WHEN grupo_lancamento IS NOT NULL 
                       THEN ROW_NUMBER() OVER (PARTITION BY grupo_lancamento ORDER BY id ASC)
                       ELSE 1
                   END as rn
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
        
        # ✅ NOVO: Converter datas para string ISO (YYYY-MM-DD)
        for date_field in ["data_pagamento", "data_lancamento", "data_competencia", "carimbo"]:
            if date_field in form and form[date_field] is not None:
                try:
                    if hasattr(form[date_field], 'strftime'):
                        form[date_field] = form[date_field].strftime('%Y-%m-%d')
                    else:
                        form[date_field] = str(form[date_field])
                except:
                    form[date_field] = str(form[date_field]) if form[date_field] else None
        
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
    
    # ✅ Verificar se cada lançamento tem fornecedor cadastrado
    # Busca TODOS os titulares cadastrados na tabela fornecedor (por nome)
    fornecedores_nomes = set()
    try:
        cursor.execute("SELECT LOWER(TRIM(titular)) AS nome FROM fornecedor")
        rows = cursor.fetchall()
        fornecedores_nomes = set(row["nome"] for row in rows if row.get("nome"))
        print(f"📋 Fornecedores cadastrados ({len(fornecedores_nomes)}): {list(fornecedores_nomes)[:10]}...", file=sys.stderr, flush=True)
    except Exception as e_forn:
        print(f"⚠️ Erro ao buscar fornecedores: {e_forn}", file=sys.stderr, flush=True)
        fornecedores_nomes = set()
    
    print(f"\n{'='*70}", file=sys.stderr, flush=True)
    print(f"🔍 DEBUG FORNECEDOR_NOVO - Verificando {len(formularios)} formulários", file=sys.stderr, flush=True)
    print(f"📋 Total fornecedores na tabela: {len(fornecedores_nomes)}", file=sys.stderr, flush=True)
    print(f"📋 Nomes cadastrados: {list(fornecedores_nomes)[:20]}", file=sys.stderr, flush=True)
    print(f"{'='*70}", file=sys.stderr, flush=True)
    
    for form in formularios:
        titular_raw = form.get("titular") or ""
        titular = titular_raw.strip().lower()
        
        # Verificação simples: o titular existe na tabela de fornecedores?
        if titular and titular in fornecedores_nomes:
            form["fornecedor_novo"] = False
            print(f"  ✅ ID={form.get('id')} | titular='{titular_raw}' → ENCONTRADO na tabela fornecedor | fornecedor_novo=False", file=sys.stderr, flush=True)
        elif titular:
            form["fornecedor_novo"] = True
            print(f"  🔴 ID={form.get('id')} | titular='{titular_raw}' → NÃO ENCONTRADO | fornecedor_novo=True", file=sys.stderr, flush=True)
        else:
            form["fornecedor_novo"] = False
            print(f"  ⚪ ID={form.get('id')} | titular VAZIO | fornecedor_novo=False", file=sys.stderr, flush=True)
    
    print(f"{'='*70}\n", file=sys.stderr, flush=True)
    
    # ✅ MARCA DE VERSÃO: Se este campo aparecer no JSON, o código novo está rodando
    total_novos = sum(1 for f in formularios if f.get("fornecedor_novo") == True)
    print(f"📊 RESUMO: {total_novos} fornecedores marcados como NOVO de {len(formularios)} total", file=sys.stderr, flush=True)
    
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
    print("\n" + "="*70, file=sys.stderr, flush=True)
    print("📥 POST /formulario - Payload recebido:", file=sys.stderr, flush=True)
    print(f"  multiplos_lancamentos: {data.get('multiplos_lancamentos')}", file=sys.stderr, flush=True)
    print(f"  obras_adicionais: {data.get('obras_adicionais')}", file=sys.stderr, flush=True)
    print(f"  obra (principal): {data.get('obra')}", file=sys.stderr, flush=True)
    print(f"  valor (total): {data.get('valor')}", file=sys.stderr, flush=True)
    print("="*70, file=sys.stderr, flush=True)
    
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
    campos_opcionais = ["conta", "quem_paga", "categoria", "fornecedor_novo"]  # ✅ NOVO: Adicionados como opcionais

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
                
                # ✅ CORREÇÃO: O frontend já envia em centavos, NÃO multiplicar novamente
                valor_centavos = int(round(valor))
                
                print(f"   → Obra {obra_id}: {valor_centavos} centavos")
                
                if valor_centavos > 0:
                    try:
                        cursor.execute("""
                            INSERT INTO formulario (
                                data_lancamento, solicitante, titular, referente, valor, obra, 
                                data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                                data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, grupo_lancamento, fornecedor_novo
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
                        """, (
                            data["data_lancamento"], 
                            data["solicitante"], 
                            data["titular"], 
                            data["referente"],
                            valor_centavos,  # Valor em centavos
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
                            grupo_lancamento,  # Mesmo grupo para todas
                            data.get("fornecedor_novo", 0)
                        ))
                        conn.commit()
                        formulario_id = cursor.lastrowid
                        print(f"      ✅ Inserido com sucesso! ID: {formulario_id} (grupo={grupo_lancamento})")
                        print(f"         ✔️ COMMIT realizado para ID {formulario_id}")
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
                                valor_centavos,  # Valor em centavos
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
                            print(f"         ✔️ COMMIT realizado para ID {formulario_id}")
                        except Exception as e:
                            print(f"      ❌ ERRO ao inserir obra {obra_id}: {type(e).__name__}: {e}")
                            print(f"         Fazendo ROLLBACK...")
                            conn.rollback()
                            print(f"         ❌ ROLLBACK realizado")
            print("="*70)
            print("✅ FIM DO MÚLTIPLO LANÇAMENTO\n")
        else:
            # Inserir o lançamento principal (para lançamentos simples, não múltiplos)
            print(f"✅ LANÇAMENTO SIMPLES (não múltiplo)")
            # ✅ CORREÇÃO: Converter valor para centavos antes de armazenar
            valor_centavos = int(round(float(data.get("valor", 0)) * 100))
            cursor.execute("""
                INSERT INTO formulario (
                    data_lancamento, solicitante, titular, referente, valor, obra, 
                    data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, grupo_lancamento, fornecedor_novo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
            """, (
                data["data_lancamento"], 
                data["solicitante"], 
                data["titular"], 
                data["referente"],
                valor_centavos, 
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
                grupo_lancamento,
                data.get("fornecedor_novo", 0)
            ))
            conn.commit()
            formulario_id = cursor.lastrowid
            print(f"✅ LANÇAMENTO SIMPLES - Criado com ID {formulario_id}, fornecedor_novo={data.get('fornecedor_novo', 0)}", file=sys.stderr, flush=True)
    except Exception as e:
        # Se falhar (provavelmente coluna grupo_lancamento não existe), tenta sem ela
        print(f"⚠️ Erro ao inserir com grupo_lancamento: {e}", file=sys.stderr, flush=True)
        if not (data.get("multiplos_lancamentos") and data.get("obras_adicionais")):
            cursor.execute("""
                INSERT INTO formulario (
                    data_lancamento, solicitante, titular, referente, valor, obra, 
                    data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, fornecedor_novo
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
                data.get("fornecedor_novo", 0)
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
        "observacao", "conta", "link_anexo", "categoria", "fornecedor_novo" # Incluídos campos opcionais
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
    
    print(f"\n{'='*70}")
    print(f"🗑️ DELETE /formulario/{form_id} - INÍCIO")
    
    try:
        # =====================================================
        # PASSO 1: Ler o registro (cursor isolado, fecha logo)
        # =====================================================
        cur1 = conn.cursor(dictionary=True, buffered=True)
        cur1.execute(
            "SELECT id, grupo_lancamento, multiplos_lancamentos, solicitante, titular, data_lancamento "
            "FROM formulario WHERE id = %s", (form_id,)
        )
        registro = cur1.fetchone()
        cur1.close()  # Fecha IMEDIATAMENTE — não reutilizar
        
        if not registro:
            conn.close()
            print(f"   ❌ Registro ID {form_id} não encontrado")
            return jsonify({"error": "Formulário não encontrado"}), 404
        
        # Extrair grupo_lancamento com segurança (pode ser None, '', bytes, etc.)
        grupo_raw = registro.get("grupo_lancamento")
        # ✅ CORREÇÃO: Usar o valor raw diretamente para a query SQL (evita str(bytes) = "b'...'")
        # Apenas decodificar se for bytes, caso contrário usar como está
        if isinstance(grupo_raw, (bytes, bytearray)):
            grupo = grupo_raw.decode('utf-8').strip()
        elif grupo_raw is not None:
            grupo = str(grupo_raw).strip()
        else:
            grupo = ""
        
        mult_raw = registro.get("multiplos_lancamentos")
        is_multiplo = False
        try:
            is_multiplo = int(mult_raw) == 1 if mult_raw is not None else False
        except (ValueError, TypeError):
            is_multiplo = str(mult_raw).strip() in ('1', 'true', 'True', 'yes')
        
        print(f"   registro encontrado: ID={registro['id']}")
        print(f"   grupo_lancamento raw: {repr(grupo_raw)} (type={type(grupo_raw).__name__}) → limpo: {repr(grupo)}")
        print(f"   multiplos_lancamentos raw: {repr(mult_raw)} → is_multiplo: {is_multiplo}")
        
        # =====================================================
        # PASSO 2: Coletar TODOS os IDs a deletar (cursor isolado)
        # =====================================================
        ids_deletados = []
        modo = "SIMPLES"
        
        if grupo:
            modo = f"GRUPO ({grupo})"
            cur2 = conn.cursor(dictionary=True, buffered=True)
            cur2.execute("SELECT id FROM formulario WHERE grupo_lancamento = %s", (grupo,))
            rows = cur2.fetchall()
            ids_deletados = [r["id"] for r in rows]
            cur2.close()
            print(f"   → Modo GRUPO: SELECT WHERE grupo_lancamento='{grupo}' retornou {len(ids_deletados)} IDs: {ids_deletados}")
        
        # ✅ CORREÇÃO: Se o grupo retornou apenas 1 registro (o próprio) ou nenhum, 
        # tentar fallback por data/solicitante/titular para pegar registros órfãos
        if (not ids_deletados or (len(ids_deletados) <= 1 and is_multiplo)) and is_multiplo:
            modo = "MÚLTIPLO ANTIGO"
            cur2b = conn.cursor(dictionary=True, buffered=True)
            cur2b.execute("""
                SELECT id FROM formulario
                WHERE multiplos_lancamentos = 1 
                AND DATE_FORMAT(data_lancamento, '%%Y%%m%%d') = DATE_FORMAT(%s, '%%Y%%m%%d')
                AND solicitante = %s
                AND titular = %s
            """, (registro["data_lancamento"], registro["solicitante"], registro["titular"]))
            rows = cur2b.fetchall()
            fallback_ids = [r["id"] for r in rows]
            cur2b.close()
            print(f"   → Modo MÚLTIPLO ANTIGO: encontrou {len(fallback_ids)} IDs: {fallback_ids}")
            # Combinar IDs do grupo + fallback (sem duplicatas)
            if fallback_ids:
                combined = list(set(ids_deletados + fallback_ids))
                ids_deletados = combined
                print(f"   → IDs combinados (grupo + fallback): {ids_deletados}")
        
        # Fallback: pelo menos o próprio registro
        if not ids_deletados:
            ids_deletados = [form_id]
            print(f"   → Fallback: nenhum grupo encontrado, deletando apenas ID {form_id}")
        
        print(f"   MODO: {modo}")
        print(f"   IDs a deletar ({len(ids_deletados)}): {ids_deletados}")
        
        # =====================================================
        # PASSO 3: DELETAR todos os IDs de uma vez (cursor isolado)
        # =====================================================
        cur3 = conn.cursor(buffered=True)
        placeholders = ",".join(["%s"] * len(ids_deletados))
        sql_delete = f"DELETE FROM formulario WHERE id IN ({placeholders})"
        print(f"   SQL: {sql_delete}")
        print(f"   Params: {tuple(ids_deletados)}")
        
        cur3.execute(sql_delete, tuple(ids_deletados))
        total_deletados = cur3.rowcount
        cur3.close()
        
        conn.commit()
        
        print(f"   ✅ COMMIT OK — {total_deletados} registros efetivamente deletados")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"   ❌ ERRO na exclusão: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.rollback()
        except:
            pass
        conn.close()
        return jsonify({"error": f"Erro ao deletar: {str(e)}"}), 500
    
    conn.close()

    return jsonify({
        "message": f"Formulário deletado ({total_deletados} registro(s) removidos)",
        "ids_deletados": ids_deletados,
        "total_deletados": total_deletados
    }), 200


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