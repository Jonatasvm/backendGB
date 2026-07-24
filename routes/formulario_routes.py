from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from db import get_connection
from services.google_drive_service import upload_files_batch, create_folder
import json
import sys
from datetime import datetime, timedelta, timezone

# ✅ Timezone ajustado: servidor MySQL está em UTC+1, Brasília é UTC-3
# Diferença total = -4 horas em relação ao horário do servidor
BRASILIA_TZ = timezone(timedelta(hours=-4))

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
    
    search_term = f"%{query}%"
    
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
# MAPEAMENTO DE ORDENAÇÃO (frontend → SQL)
# ===========================
ORDER_MAP = {
    "id_asc": "id ASC",
    "id_desc": "id DESC",
    "valor_asc": "valor ASC",
    "valor_desc": "valor DESC",
    "titular_asc": "titular ASC",
    "titular_desc": "titular DESC",
    "referente_asc": "referente ASC",
    "referente_desc": "referente DESC",
    "dataLancamento_asc": "data_lancamento ASC",
    "dataLancamento_desc": "data_lancamento DESC",
    "dataPagamento_asc": "data_pagamento ASC",
    "dataPagamento_desc": "data_pagamento DESC",
}

# ===========================
# FUNÇÕES AUXILIARES (pós-processamento)
# ===========================
def _postprocess_formulario(form, brasilia_tz):
    """Converte tipos de dados de um formulário para JSON-safe."""
    # Converter Decimal para float
    if "valor" in form and form["valor"] is not None:
        form["valor"] = float(form["valor"])
    
    # Converter datas para string ISO (YYYY-MM-DD)
    for date_field in ["data_pagamento", "data_lancamento", "data_competencia"]:
        if date_field in form and form[date_field] is not None:
            try:
                if hasattr(form[date_field], 'strftime'):
                    form[date_field] = form[date_field].strftime('%Y-%m-%d')
                else:
                    form[date_field] = str(form[date_field])
            except:
                form[date_field] = str(form[date_field]) if form[date_field] else None
    
    # Carimbo: converter de UTC (servidor) para horário de Brasília
    if "carimbo" in form and form["carimbo"] is not None:
        try:
            if hasattr(form["carimbo"], 'strftime'):
                dt_utc = form["carimbo"].replace(tzinfo=timezone.utc)
                dt_brasilia = dt_utc.astimezone(brasilia_tz)
                form["carimbo"] = dt_brasilia.strftime('%Y-%m-%dT%H:%M:%S')
            else:
                dt_str = str(form["carimbo"])
                try:
                    dt_utc = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                    dt_brasilia = dt_utc.astimezone(brasilia_tz)
                    form["carimbo"] = dt_brasilia.strftime('%Y-%m-%dT%H:%M:%S')
                except:
                    form["carimbo"] = dt_str
        except:
            form["carimbo"] = str(form["carimbo"]) if form["carimbo"] else None
    
    # Remover uuid se existir
    form.pop('uuid', None)
    
    return form


def _batch_load_obras_relacionadas(cursor, formularios):
    """Carrega obras relacionadas em batch usando formulario_obras (novo formato)
       + fallback para grupo_id (formato antigo/legado)."""
    
    form_ids = [f["id"] for f in formularios if f.get("id")]
    
    if not form_ids:
        return
    
    # =========================================================
    # 1) NOVO FORMATO: buscar de formulario_obras
    # =========================================================
    obras_by_form = {}
    placeholders = ",".join(["%s"] * len(form_ids))
    try:
        cursor.execute(f"""
            SELECT fo.formulario_id, fo.obra_id AS obra, fo.valor, fo.id AS fo_id
            FROM formulario_obras fo
            WHERE fo.formulario_id IN ({placeholders})
            ORDER BY fo.id ASC
        """, tuple(form_ids))
        rows = cursor.fetchall()
        
        for r in rows:
            fid = r["formulario_id"]
            if fid not in obras_by_form:
                obras_by_form[fid] = []
            if "valor" in r and r["valor"] is not None:
                r["valor"] = float(r["valor"])
            obras_by_form[fid].append({
                "id": r.get("fo_id"),
                "obra": r.get("obra"),
                "valor": r.get("valor", 0),
            })
        
        print(f"[BATCH_LOAD] formulario_obras: {len(rows)} registros para {len(obras_by_form)} formulários", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[BATCH_LOAD] ⚠️ Erro ao buscar formulario_obras: {e}", file=sys.stderr, flush=True)
    
    # =========================================================
    # 2) FALLBACK LEGADO: buscar irmãos pelo grupo_id (antigo)
    # =========================================================
    grupo_ids = set()
    forms_sem_obras = []
    for form in formularios:
        fid = form.get("id")
        if fid not in obras_by_form:
            gid = form.get("grupo_id")
            if gid:
                grupo_ids.add(gid)
                forms_sem_obras.append(form)
    
    related_by_grupo = {}
    if grupo_ids:
        ph = ",".join(["%s"] * len(grupo_ids))
        cursor.execute(f"""
            SELECT id, obra, valor, referente, data_pagamento, forma_pagamento, grupo_id
            FROM formulario
            WHERE grupo_id IN ({ph})
            ORDER BY id ASC
        """, tuple(grupo_ids))
        all_related = cursor.fetchall()
        
        for r in all_related:
            gid = r.get("grupo_id")
            if gid not in related_by_grupo:
                related_by_grupo[gid] = []
            if "valor" in r and r["valor"] is not None:
                r["valor"] = float(r["valor"])
            related_by_grupo[gid].append(r)
        
        print(f"[BATCH_LOAD] LEGADO grupo_id: {len(all_related)} registros para {len(grupo_ids)} grupos", file=sys.stderr, flush=True)
    
    # =========================================================
    # 3) Atribuir obras_relacionadas a cada formulário
    # =========================================================
    for form in formularios:
        fid = form.get("id")
        obras_relacionadas = []
        
        # Prioridade 1: formulario_obras (novo formato)
        if fid in obras_by_form:
            obras_relacionadas = obras_by_form[fid]
            form["grupo_lancamento"] = str(fid)  # Frontend usa isso para detectar múltiplo
        else:
            # Prioridade 2: grupo_id legado
            gid = form.get("grupo_id")
            if gid:
                all_in_group = related_by_grupo.get(gid, [])
                obras_relacionadas = [r for r in all_in_group if r["id"] != fid]
                for obra in obras_relacionadas:
                    obra.pop('grupo_id', None)
                if obras_relacionadas:
                    form["grupo_lancamento"] = str(gid)  # Compatibilidade frontend
        
        if obras_relacionadas:
            form["obras_relacionadas"] = obras_relacionadas
            
            # Calcular valor total
            valor_total = float(form.get("valor") or 0)
            for obra in obras_relacionadas:
                valor_total += float(obra.get("valor") or 0)
            form["valor_total"] = valor_total
            form["valor_principal"] = float(form.get("valor") or 0)


def _check_fornecedores_novos(cursor, formularios):
    """Verifica se os titulares existem na tabela fornecedor (batch)."""
    fornecedores_nomes = set()
    try:
        cursor.execute("SELECT LOWER(TRIM(titular)) AS nome FROM fornecedor")
        rows = cursor.fetchall()
        fornecedores_nomes = set(row["nome"] for row in rows if row.get("nome"))
    except Exception as e_forn:
        print(f"⚠️ Erro ao buscar fornecedores: {e_forn}", file=sys.stderr, flush=True)
    
    for form in formularios:
        titular_raw = form.get("titular") or ""
        titular = titular_raw.strip().lower()
        if titular and titular in fornecedores_nomes:
            form["fornecedor_novo"] = False
        elif titular:
            form["fornecedor_novo"] = True
        else:
            form["fornecedor_novo"] = False


# ===========================
# LISTAR FORMULÁRIOS (GET) — com filtros server-side e paginação
# ===========================
@formulario_bp.route("/formulario", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_formularios():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    # --- Parâmetros de paginação ---
    page = request.args.get("page", type=int)  # Se ausente, retorna tudo (backward compat)
    per_page = request.args.get("per_page", 100, type=int)
    per_page = min(per_page, 500)  # Limite de segurança
    
    # --- Parâmetros de filtro ---
    status = request.args.get("status", "")
    forma_pagamento = request.args.get("forma_pagamento", "")
    data_exata = request.args.get("data", "")
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")
    obra = request.args.get("obra", "")
    titular = request.args.get("titular", "")
    solicitante = request.args.get("solicitante", "")
    referente = request.args.get("referente", "")
    busca = request.args.get("busca", "")
    multiplos = request.args.get("multiplos", "todos")
    codigo_barra_status = request.args.get("codigo_barra_status", "todos")
    ids_filter = request.args.get("ids", "")  # IDs separados por vírgula (histórico)
    ordenacao = request.args.get("ordenacao", "id_desc")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # --- Construir WHERE dinâmico ---
    where_parts = ["1=1"]
    params = []
    
    # Filtro: Status (lancado)
    if status:
        status_map = {
            "PENDENTE": ("f.lancado = %s", "N"),
            "LANCADO": ("f.lancado IN ('Y', 'S', '1')", None),
            "NAO_AUTORIZADO": ("f.lancado = %s", "X"),
            "APROVADO": ("f.lancado = %s", "A"),
            "PAGO": ("f.lancado = %s", "P"),
        }
        if status in status_map:
            sql_part, param = status_map[status]
            where_parts.append(sql_part)
            if param is not None:
                params.append(param)
    
    # Filtro: Forma de pagamento
    if forma_pagamento:
        where_parts.append("UPPER(TRIM(f.forma_pagamento)) = UPPER(TRIM(%s))")
        params.append(forma_pagamento)
    
    # Filtro: Data exata
    if data_exata:
        where_parts.append("f.data_pagamento = %s")
        params.append(data_exata)
    
    # Filtro: Data intervalo
    if data_inicio:
        where_parts.append("f.data_pagamento >= %s")
        params.append(data_inicio)
    if data_fim:
        where_parts.append("f.data_pagamento <= %s")
        params.append(data_fim)
    
    # Filtro: Obra
    if obra:
        where_parts.append("f.obra = %s")
        params.append(int(obra))
    
    # Filtro: Titular (match exato case-insensitive)
    if titular:
        where_parts.append("UPPER(TRIM(f.titular)) = UPPER(TRIM(%s))")
        params.append(titular)
    
    # Filtro: Solicitante (busca parcial)
    if solicitante:
        where_parts.append("UPPER(f.solicitante) LIKE %s")
        params.append(f"%{solicitante.upper()}%")
    
    # Filtro: Referente/Descrição (busca parcial)
    if referente:
        where_parts.append("UPPER(f.referente) LIKE %s")
        params.append(f"%{referente.upper()}%")
    
    # Filtro: Busca mista (valor, titular, referente)
    if busca:
        busca_like = f"%{busca.strip()}%"
        # Tenta converter para centavos para busca numérica
        busca_centavos = None
        try:
            busca_clean = busca.strip().replace(".", "").replace(",", ".").replace("R$", "").replace(" ", "")
            busca_float = float(busca_clean)
            busca_centavos = int(round(busca_float * 100))
        except (ValueError, TypeError):
            pass
        
        if busca_centavos is not None:
            where_parts.append("""
                (f.titular LIKE %s OR f.referente LIKE %s 
                 OR f.valor = %s OR CAST(f.valor AS CHAR) LIKE %s)
            """)
            params.extend([busca_like, busca_like, busca_centavos, busca_like])
        else:
            where_parts.append("(f.titular LIKE %s OR f.referente LIKE %s)")
            params.extend([busca_like, busca_like])
    
    # Filtro: Múltiplos lançamentos (novo: formulario_obras, legado: grupo_id)
    if multiplos == "sim":
        where_parts.append("""
            (f.id IN (SELECT DISTINCT formulario_id FROM formulario_obras)
             OR f.grupo_id IS NOT NULL)
        """)
    elif multiplos == "nao":
        where_parts.append("""
            (f.id NOT IN (SELECT DISTINCT formulario_id FROM formulario_obras)
             AND f.grupo_id IS NULL)
        """)
    
    # Filtro: Código de barras (boleto)
    if codigo_barra_status == "vazio":
        where_parts.append("""
            (LOWER(TRIM(f.forma_pagamento)) = 'boleto' 
             AND (f.chave_pix IS NULL OR TRIM(f.chave_pix) = ''))
        """)
    elif codigo_barra_status == "preenchido":
        where_parts.append("""
            (LOWER(TRIM(f.forma_pagamento)) = 'boleto' 
             AND f.chave_pix IS NOT NULL AND TRIM(f.chave_pix) != '')
        """)
    
    # Filtro: IDs específicos (histórico de exportação)
    if ids_filter:
        try:
            id_list = [int(x.strip()) for x in ids_filter.split(",") if x.strip()]
            if id_list:
                placeholders = ",".join(["%s"] * len(id_list))
                where_parts.append(f"f.id IN ({placeholders})")
                params.extend(id_list)
        except ValueError:
            pass
    
    where_sql = " AND ".join(where_parts)
    
    # --- Ordenação ---
    order_sql = ORDER_MAP.get(ordenacao, "id DESC")
    
    # --- Count total (para paginação) ---
    total = 0
    if page:
        count_sql = f"SELECT COUNT(*) as total FROM formulario f WHERE {where_sql}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]
    
    # --- Buscar dados ---
    if page:
        offset = (page - 1) * per_page
        data_sql = f"SELECT f.* FROM formulario f WHERE {where_sql} ORDER BY {order_sql} LIMIT %s OFFSET %s"
        cursor.execute(data_sql, tuple(params) + (per_page, offset))
    else:
        data_sql = f"SELECT f.* FROM formulario f WHERE {where_sql} ORDER BY {order_sql}"
        cursor.execute(data_sql, tuple(params))
    
    formularios = cursor.fetchall()
    
    # --- Pós-processamento ---
    for form in formularios:
        _postprocess_formulario(form, BRASILIA_TZ)
    
    # --- Carregar obras relacionadas em batch ---
    cursor2 = conn.cursor(dictionary=True)
    _batch_load_obras_relacionadas(cursor2, formularios)
    cursor2.close()
    
    # --- Verificar fornecedores novos ---
    cursor3 = conn.cursor(dictionary=True)
    _check_fornecedores_novos(cursor3, formularios)
    cursor3.close()
    
    cursor.close()
    conn.close()
    
    # --- Resposta ---
    if page:
        return jsonify({
            "data": formularios,
            "total": total,
            "page": page,
            "per_page": per_page,
        }), 200
    else:
        # Backward compatible: retorna array puro
        return jsonify(formularios), 200


# ===========================
# BUSCAR FORMULÁRIO POR ID (GET) — para refresh após edição
# ===========================
@formulario_bp.route("/formulario/<int:form_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def buscar_formulario(form_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM formulario WHERE id = %s", (form_id,))
    form = cursor.fetchone()
    
    if not form:
        cursor.close()
        conn.close()
        return jsonify({"error": "Formulário não encontrado"}), 404
    
    # Pós-processamento
    _postprocess_formulario(form, BRASILIA_TZ)
    
    # Carregar obras relacionadas
    _batch_load_obras_relacionadas(cursor, [form])
    
    # Verificar fornecedor novo
    _check_fornecedores_novos(cursor, [form])
    
    cursor.close()
    conn.close()
    
    return jsonify(form), 200

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

    # === NOVO: Determinar UUID e ID do solicitante para gravar na tabela formulario ===
    solicitante_uuid = None
    solicitante_id = None
    try:
        # Preferência: se frontend enviou o uuid explícito
        if data.get('uuid'):
            solicitante_uuid = data.get('uuid')
            # Buscar o id numérico pelo uuid
            cursor.execute("SELECT id FROM users WHERE uuid_id = %s LIMIT 1", (solicitante_uuid,))
            row = cursor.fetchone()
            if row and row[0]:
                solicitante_id = row[0]
        
        # Se ainda não temos o id, tentar por solicitante (nome/username)
        if solicitante_id is None:
            sol = data.get('solicitante')
            if sol is not None:
                try:
                    sol_int = int(sol)
                    # Buscar por id
                    cursor.execute("SELECT id, uuid_id FROM users WHERE id = %s", (sol_int,))
                    row = cursor.fetchone()
                    if row:
                        solicitante_id = row[0]
                        if not solicitante_uuid and row[1]:
                            solicitante_uuid = row[1]
                except (ValueError, TypeError):
                    # Buscar por username (pode estar em maiúsculas ou minúsculas)
                    cursor.execute("SELECT id, uuid_id FROM users WHERE UPPER(username) = UPPER(%s) LIMIT 1", (sol,))
                    row = cursor.fetchone()
                    if row:
                        solicitante_id = row[0]
                        if not solicitante_uuid and row[1]:
                            solicitante_uuid = row[1]
    except Exception as e:
        print(f"⚠️ Aviso: não foi possível determinar uuid/id do solicitante: {e}", file=sys.stderr, flush=True)

    # ✅ Determinar se é múltiplo lançamento
    is_multiplo = data.get("multiplos_lancamentos") and data.get("obras_adicionais") and len(data.get("obras_adicionais", [])) > 0
    
    try:
        # =====================================================
        # PASSO 1: Preparar dados — sempre cria 1 registro em formulario
        # =====================================================
        obras_adicionais = []
        
        if is_multiplo:
            obras_adicionais = data.get("obras_adicionais", [])
            if isinstance(obras_adicionais, str):
                print(f"⚠️ AVISO: obras_adicionais veio como STRING: {obras_adicionais}", file=sys.stderr, flush=True)
                obras_adicionais = []
            
            # A obra principal é o primeiro item de obras_adicionais
            # (frontend envia obra principal + adicionais no array)
            if obras_adicionais:
                obra_principal = obras_adicionais[0]
                obra_id_principal = obra_principal.get("obra_id", data.get("obra"))
                valor_principal = obra_principal.get("valor", 0)
                
                if isinstance(valor_principal, str):
                    valor_limpo = valor_principal.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    valor_principal = float(valor_limpo) if valor_limpo else 0
                else:
                    valor_principal = float(valor_principal) if valor_principal else 0
                
                valor_centavos = int(round(valor_principal))
            else:
                obra_id_principal = data.get("obra")
                valor_centavos = int(round(float(data.get("valor", 0))))
        else:
            obra_id_principal = data.get("obra")
            valor_centavos = int(round(float(data.get("valor", 0))))
        
        # =====================================================
        # PASSO 2: INSERT na tabela formulario (1 registro apenas)
        # =====================================================
        cursor.execute("""
            INSERT INTO formulario (
                data_lancamento, solicitante, titular, referente, valor, obra, 
                data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                data_competencia, carimbo, observacao, conta, categoria, 
                fornecedor_novo, uuid, id_solicitante
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
        """, (
            data["data_lancamento"], 
            data["solicitante"], 
            data["titular"], 
            data["referente"],
            valor_centavos,
            obra_id_principal,
            data["data_pagamento"], 
            data["forma_pagamento"],
            valor_lancado,
            data["cpf_cnpj"], 
            data["chave_pix"], 
            data["data_competencia"],
            data["observacao"],
            data.get("conta"),
            data.get("categoria"),
            data.get("fornecedor_novo", 0),
            solicitante_uuid,
            solicitante_id
        ))
        formulario_id = cursor.lastrowid
        print(f"✅ Formulário criado — ID {formulario_id}, obra={obra_id_principal}, valor={valor_centavos}", file=sys.stderr, flush=True)
        
        # =====================================================
        # PASSO 3: Se múltiplo, INSERT obras adicionais em formulario_obras
        # =====================================================
        if is_multiplo and len(obras_adicionais) > 1:
            # Pular o primeiro (obra principal, já está no formulario)
            for idx, obra_info in enumerate(obras_adicionais[1:], 2):
                obra_id = obra_info.get("obra_id")
                valor = obra_info.get("valor", 0)
                
                if isinstance(valor, str):
                    valor_limpo = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    valor = float(valor_limpo) if valor_limpo else 0
                else:
                    valor = float(valor) if valor else 0
                
                valor_obra_centavos = int(round(valor))
                
                if valor_obra_centavos > 0 and obra_id:
                    cursor.execute("""
                        INSERT INTO formulario_obras (formulario_id, obra_id, valor)
                        VALUES (%s, %s, %s)
                    """, (formulario_id, obra_id, valor_obra_centavos))
                    print(f"   [{idx}] formulario_obras: obra={obra_id}, valor={valor_obra_centavos} centavos", file=sys.stderr, flush=True)
            
            print(f"✅ MÚLTIPLO LANÇAMENTO COMPLETO — ID={formulario_id}, {len(obras_adicionais)-1} obras adicionais em formulario_obras", file=sys.stderr, flush=True)
        
        # COMMIT atômico — tudo ou nada
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao criar formulário: {e}", file=sys.stderr, flush=True)
        cursor.close()
        conn.close()
        return jsonify({"error": f"Erro ao criar formulário: {str(e)}"}), 500
    
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

    if not set_clauses and "obras_adicionais" not in data:
        return jsonify({"error": "Nenhum campo para atualizar"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Atualizar campos do formulario (se houver)
        if set_clauses:
            query = f"UPDATE formulario SET {', '.join(set_clauses)} WHERE id = %s"
            valores.append(form_id)
            cursor.execute(query, tuple(valores))
        
        # 2. Atualizar formulario_obras (se houver obras_adicionais no payload)
        if "obras_adicionais" in data:
            obras_adicionais = data["obras_adicionais"]
            if isinstance(obras_adicionais, list):
                # Limpar obras antigas
                cursor.execute("DELETE FROM formulario_obras WHERE formulario_id = %s", (form_id,))
                print(f"[PUT] Limpou formulario_obras para ID={form_id}", file=sys.stderr, flush=True)
                
                # Re-inserir obras adicionais (pular a primeira que é a obra principal)
                for idx, obra_info in enumerate(obras_adicionais[1:] if len(obras_adicionais) > 1 else [], 2):
                    obra_id = obra_info.get("obra_id") or obra_info.get("obra")
                    valor = obra_info.get("valor", 0)
                    
                    if isinstance(valor, str):
                        valor_limpo = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        valor = float(valor_limpo) if valor_limpo else 0
                    else:
                        valor = float(valor) if valor else 0
                    
                    valor_centavos = int(round(valor))
                    
                    if valor_centavos > 0 and obra_id:
                        cursor.execute("""
                            INSERT INTO formulario_obras (formulario_id, obra_id, valor)
                            VALUES (%s, %s, %s)
                        """, (form_id, obra_id, valor_centavos))
                        print(f"   [{idx}] formulario_obras: obra={obra_id}, valor={valor_centavos}", file=sys.stderr, flush=True)
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar formulário {form_id}: {e}", file=sys.stderr, flush=True)
        cursor.close()
        conn.close()
        return jsonify({"error": f"Erro ao atualizar: {str(e)}"}), 500
    
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
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verificar se o registro existe
        cursor.execute("SELECT id, grupo_id FROM formulario WHERE id = %s", (form_id,))
        registro = cursor.fetchone()
        
        if not registro:
            cursor.close()
            conn.close()
            return jsonify({"error": "Formulário não encontrado"}), 404
        
        grupo_id = registro.get("grupo_id")
        
        # LEGADO: Se tem grupo_id (formato antigo), deleta todo o grupo
        if grupo_id:
            cursor.execute("SELECT id FROM formulario WHERE grupo_id = %s", (grupo_id,))
            ids_deletados = [r["id"] for r in cursor.fetchall()]
            
            cursor.execute("DELETE FROM formulario WHERE grupo_id = %s", (grupo_id,))
            total_deletados = cursor.rowcount
            print(f"🗑️ DELETE LEGADO grupo_id={grupo_id}: {total_deletados} registros removidos (IDs: {ids_deletados})", file=sys.stderr, flush=True)
        else:
            # NOVO FORMATO: Deleta só o registro (CASCADE cuida de formulario_obras)
            cursor.execute("DELETE FROM formulario WHERE id = %s", (form_id,))
            total_deletados = cursor.rowcount
            ids_deletados = [form_id]
            print(f"🗑️ DELETE ID={form_id}: {total_deletados} registro removido (formulario_obras limpo por CASCADE)", file=sys.stderr, flush=True)
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ ERRO na exclusão: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": f"Erro ao deletar: {str(e)}"}), 500
    
    cursor.close()
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
    
    # Busca titulares da tabela 'fornecedor' (cadastros) + titulares usados em formulários
    sql_query = """
        SELECT DISTINCT titular
        FROM (
            SELECT TRIM(titular) AS titular FROM fornecedor WHERE TRIM(titular) != ''
            UNION
            SELECT TRIM(titular) AS titular FROM formulario WHERE titular IS NOT NULL AND TRIM(titular) != ''
        ) AS todos
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