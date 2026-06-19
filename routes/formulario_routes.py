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
    # Remover rn (window function helper)
    form.pop('rn', None)
    
    return form


def _batch_load_obras_relacionadas(cursor, formularios):
    """Carrega obras relacionadas em batch (1-2 queries ao invés de N)."""
    # Coletar grupos únicos
    grupos = set()
    multiplos_sem_grupo = []
    
    for form in formularios:
        g = form.get("grupo_lancamento")
        if g:
            if isinstance(g, (bytes, bytearray)):
                g = g.decode('utf-8').strip()
            grupos.add(g)
        elif form.get("multiplos_lancamentos") == 1:
            multiplos_sem_grupo.append(form)
    
    # Batch query para todos os grupos de uma vez
    related_by_grupo = {}
    if grupos:
        placeholders = ",".join(["%s"] * len(grupos))
        cursor.execute(f"""
            SELECT id, obra, valor, referente, data_pagamento, forma_pagamento, grupo_lancamento
            FROM formulario
            WHERE grupo_lancamento IN ({placeholders})
            ORDER BY id ASC
        """, tuple(grupos))
        all_related = cursor.fetchall()
        
        for r in all_related:
            g = r.get("grupo_lancamento")
            if isinstance(g, (bytes, bytearray)):
                g = g.decode('utf-8').strip()
            if g not in related_by_grupo:
                related_by_grupo[g] = []
            # Converter Decimal para float
            if "valor" in r and r["valor"] is not None:
                r["valor"] = float(r["valor"])
            related_by_grupo[g].append(r)
    
    # Batch query para múltiplos antigos (sem grupo_lancamento)
    related_by_multiplo = {}
    for form in multiplos_sem_grupo:
        key = f"{form.get('data_lancamento')}|{form.get('solicitante')}|{form.get('titular')}"
        if key not in related_by_multiplo:
            cursor.execute("""
                SELECT id, obra, valor, referente, data_pagamento, forma_pagamento
                FROM formulario
                WHERE multiplos_lancamentos = 1 
                AND DATE_FORMAT(data_lancamento, '%%Y%%m%%d') = DATE_FORMAT(%s, '%%Y%%m%%d')
                AND solicitante = %s
                AND titular = %s
                ORDER BY id ASC
            """, (form["data_lancamento"], form["solicitante"], form["titular"]))
            rows = cursor.fetchall()
            for r in rows:
                if "valor" in r and r["valor"] is not None:
                    r["valor"] = float(r["valor"])
            related_by_multiplo[key] = rows
    
    # Atribuir obras relacionadas a cada formulário
    for form in formularios:
        obras_relacionadas = []
        g = form.get("grupo_lancamento")
        
        if g:
            if isinstance(g, (bytes, bytearray)):
                g = g.decode('utf-8').strip()
            all_in_group = related_by_grupo.get(g, [])
            obras_relacionadas = [r for r in all_in_group if r["id"] != form["id"]]
        elif form.get("multiplos_lancamentos") == 1:
            key = f"{form.get('data_lancamento')}|{form.get('solicitante')}|{form.get('titular')}"
            all_in_multiplo = related_by_multiplo.get(key, [])
            obras_relacionadas = [r for r in all_in_multiplo if r["id"] != form["id"]]
        
        if obras_relacionadas:
            # Limpar campo grupo_lancamento dos relacionados (não necessário no front)
            for obra in obras_relacionadas:
                obra.pop('grupo_lancamento', None)
            
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
    ordenacao = request.args.get("ordenacao", "id_asc")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # --- Construir WHERE dinâmico ---
    where_parts = ["sub.rn = 1"]
    params = []
    
    # Filtro: Status (lancado)
    if status:
        status_map = {
            "PENDENTE": ("sub.lancado = %s", "N"),
            "LANCADO": ("sub.lancado IN ('Y', 'S', '1')", None),
            "NAO_AUTORIZADO": ("sub.lancado = %s", "X"),
            "APROVADO": ("sub.lancado = %s", "A"),
        }
        if status in status_map:
            sql_part, param = status_map[status]
            where_parts.append(sql_part)
            if param is not None:
                params.append(param)
    
    # Filtro: Forma de pagamento
    if forma_pagamento:
        where_parts.append("UPPER(TRIM(sub.forma_pagamento)) = UPPER(TRIM(%s))")
        params.append(forma_pagamento)
    
    # Filtro: Data exata
    if data_exata:
        where_parts.append("sub.data_pagamento = %s")
        params.append(data_exata)
    
    # Filtro: Data intervalo
    if data_inicio:
        where_parts.append("sub.data_pagamento >= %s")
        params.append(data_inicio)
    if data_fim:
        where_parts.append("sub.data_pagamento <= %s")
        params.append(data_fim)
    
    # Filtro: Obra
    if obra:
        where_parts.append("sub.obra = %s")
        params.append(int(obra))
    
    # Filtro: Titular (match exato case-insensitive)
    if titular:
        where_parts.append("UPPER(TRIM(sub.titular)) = UPPER(TRIM(%s))")
        params.append(titular)
    
    # Filtro: Solicitante (busca parcial)
    if solicitante:
        where_parts.append("UPPER(sub.solicitante) LIKE %s")
        params.append(f"%{solicitante.upper()}%")
    
    # Filtro: Referente/Descrição (busca parcial)
    if referente:
        where_parts.append("UPPER(sub.referente) LIKE %s")
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
                (sub.titular LIKE %s OR sub.referente LIKE %s 
                 OR sub.valor = %s OR CAST(sub.valor AS CHAR) LIKE %s)
            """)
            params.extend([busca_like, busca_like, busca_centavos, busca_like])
        else:
            where_parts.append("(sub.titular LIKE %s OR sub.referente LIKE %s)")
            params.extend([busca_like, busca_like])
    
    # Filtro: Múltiplos lançamentos
    if multiplos == "sim":
        where_parts.append("sub.grupo_lancamento IS NOT NULL")
    elif multiplos == "nao":
        where_parts.append("sub.grupo_lancamento IS NULL")
    
    # Filtro: Código de barras (boleto)
    if codigo_barra_status == "vazio":
        where_parts.append("""
            (LOWER(TRIM(sub.forma_pagamento)) = 'boleto' 
             AND (sub.chave_pix IS NULL OR TRIM(sub.chave_pix) = ''))
        """)
    elif codigo_barra_status == "preenchido":
        where_parts.append("""
            (LOWER(TRIM(sub.forma_pagamento)) = 'boleto' 
             AND sub.chave_pix IS NOT NULL AND TRIM(sub.chave_pix) != '')
        """)
    
    # Filtro: IDs específicos (histórico de exportação)
    if ids_filter:
        try:
            id_list = [int(x.strip()) for x in ids_filter.split(",") if x.strip()]
            if id_list:
                placeholders = ",".join(["%s"] * len(id_list))
                where_parts.append(f"sub.id IN ({placeholders})")
                params.extend(id_list)
        except ValueError:
            pass
    
    # --- Subquery base (mesma lógica de ROW_NUMBER) ---
    base_subquery = """
        SELECT *,
               CASE 
                   WHEN grupo_lancamento IS NOT NULL 
                   THEN ROW_NUMBER() OVER (PARTITION BY grupo_lancamento ORDER BY id ASC)
                   ELSE 1
               END as rn
        FROM formulario
    """
    
    where_sql = " AND ".join(where_parts)
    
    # --- Ordenação ---
    order_sql = ORDER_MAP.get(ordenacao, "id ASC")
    
    # --- Count total (para paginação) ---
    total = 0
    if page:
        count_sql = f"SELECT COUNT(*) as total FROM ({base_subquery}) sub WHERE {where_sql}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]
    
    # --- Buscar dados ---
    if page:
        offset = (page - 1) * per_page
        data_sql = f"SELECT sub.* FROM ({base_subquery}) sub WHERE {where_sql} ORDER BY {order_sql} LIMIT %s OFFSET %s"
        cursor.execute(data_sql, tuple(params) + (per_page, offset))
    else:
        data_sql = f"SELECT sub.* FROM ({base_subquery}) sub WHERE {where_sql} ORDER BY {order_sql}"
        cursor.execute(data_sql, tuple(params))
    
    formularios = cursor.fetchall()
    
    # --- Pós-processamento ---
    for form in formularios:
        _postprocess_formulario(form, BRASILIA_TZ)
    
    # --- Carregar obras relacionadas em batch (fix N+1) ---
    _batch_load_obras_relacionadas(cursor, formularios)
    
    # --- Verificar fornecedores novos ---
    _check_fornecedores_novos(cursor, formularios)
    
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

    # === NOVO: Determinar UUID do solicitante para gravar na tabela formulario ===
    solicitante_uuid = None
    try:
        # Preferência: se frontend enviou o uuid explícito
        if data.get('uuid'):
            solicitante_uuid = data.get('uuid')
        else:
            # Tenta buscar na tabela users pelo id (se numeric) ou pelo username
            sol = data.get('solicitante')
            if sol is not None:
                try:
                    sol_int = int(sol)
                    # Buscar por id
                    cursor.execute("SELECT uuid_id FROM users WHERE id = %s", (sol_int,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        solicitante_uuid = row[0]
                except Exception:
                    # Buscar por username (pode estar em maiúsculas ou minúsculas)
                    cursor.execute("SELECT uuid_id FROM users WHERE UPPER(username) = UPPER(%s) LIMIT 1", (sol,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        solicitante_uuid = row[0]
    except Exception as e:
        print(f"⚠️ Aviso: não foi possível determinar uuid do solicitante: {e}", file=sys.stderr, flush=True)

    # ✅ Gerar grupo de lançamento único para múltiplas obras
    grupo_lancamento = None
    if data.get("multiplos_lancamentos") and data.get("obras_adicionais") and len(data.get("obras_adicionais", [])) > 0:
        import uuid as _uuid
        grupo_lancamento = str(_uuid.uuid4())[:8]  # ID curto para agrupar
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
                                data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, grupo_lancamento, fornecedor_novo, uuid
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
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
                            data.get("fornecedor_novo", 0),
                            solicitante_uuid
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
                                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, fornecedor_novo, uuid
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
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
                                data.get("multiplos_lancamentos", 0),
                                data.get("fornecedor_novo", 0),
                                solicitante_uuid
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
            # ✅ CORREÇÃO: O frontend já envia o valor em CENTAVOS, NÃO multiplicar novamente
            valor_centavos = int(round(float(data.get("valor", 0))))
            cursor.execute("""
                INSERT INTO formulario (
                    data_lancamento, solicitante, titular, referente, valor, obra, 
                    data_pagamento, forma_pagamento, lancado, cpf_cnpj, chave_pix, 
                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, grupo_lancamento, fornecedor_novo, uuid
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
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
                data.get("fornecedor_novo", 0),
                solicitante_uuid
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
                    data_competencia, carimbo, observacao, conta, categoria, multiplos_lancamentos, fornecedor_novo, uuid
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
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
                data.get("fornecedor_novo", 0),
                solicitante_uuid
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