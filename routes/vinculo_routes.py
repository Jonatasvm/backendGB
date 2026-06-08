"""
Rotas para gerenciar vínculos entre lançamentos (formularios)
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.vinculo_service import VinculoService

vinculo_bp = Blueprint("vinculo", __name__)

# ===========================
# CRIAR NOVO VÍNCULO (POST)
# ===========================
@vinculo_bp.route("/vinculo", methods=["POST", "OPTIONS"])
@cross_origin()
def criar_vinculo():
    """
    Criar um novo vínculo entre dois lançamentos
    
    Body esperado:
    {
        "formulario_id_principal": 1,
        "formulario_id_vinculado": 2,
        "tipo_vinculo": "multiple_payment",  # Opcional: multiple_payment | adjustment | reversal | split | other
        "observacao": "Lançamento dividido em 2 obras"  # Opcional
    }
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    data = request.get_json()
    
    # Validar campos obrigatórios
    if not data or not data.get("formulario_id_principal") or not data.get("formulario_id_vinculado"):
        return jsonify({"error": "formulario_id_principal e formulario_id_vinculado são obrigatórios"}), 400
    
    tipo_vinculo = data.get("tipo_vinculo", "multiple_payment")
    observacao = data.get("observacao")
    
    resultado, status = VinculoService.criar_vinculo(
        data["formulario_id_principal"],
        data["formulario_id_vinculado"],
        tipo_vinculo,
        observacao
    )
    
    return jsonify(resultado), status


# ===========================
# OBTER VÍNCULOS DE UM FORMULÁRIO (GET)
# ===========================
@vinculo_bp.route("/formulario/<int:formulario_id>/vinculos", methods=["GET", "OPTIONS"])
@cross_origin()
def obter_vinculos_formulario(formulario_id):
    """
    Obter todos os vínculos de um lançamento específico
    
    Parâmetros de query:
    - apenas_ativos: true/false (padrão: true)
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    apenas_ativos = request.args.get("apenas_ativos", "true").lower() == "true"
    
    vinculos, status = VinculoService.obter_vinculos_por_formulario(formulario_id, apenas_ativos)
    
    if status != 200:
        return jsonify(vinculos), status
    
    return jsonify({
        "formulario_id": formulario_id,
        "total_vinculos": len(vinculos),
        "vinculos": vinculos
    }), 200


# ===========================
# DESATIVAR VÍNCULO (PUT)
# ===========================
@vinculo_bp.route("/vinculo/<int:vinculo_id>/desativar", methods=["PUT", "OPTIONS"])
@cross_origin()
def desativar_vinculo(vinculo_id):
    """
    Desativar um vínculo (soft delete)
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    resultado, status = VinculoService.desativar_vinculo(vinculo_id)
    return jsonify(resultado), status


# ===========================
# REATIVAR VÍNCULO (PUT)
# ===========================
@vinculo_bp.route("/vinculo/<int:vinculo_id>/reativar", methods=["PUT", "OPTIONS"])
@cross_origin()
def reativar_vinculo(vinculo_id):
    """
    Reativar um vínculo que foi desativado
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    resultado, status = VinculoService.ativar_vinculo(vinculo_id)
    return jsonify(resultado), status


# ===========================
# DELETAR VÍNCULO (DELETE)
# ===========================
@vinculo_bp.route("/vinculo/<int:vinculo_id>", methods=["DELETE", "OPTIONS"])
@cross_origin()
def deletar_vinculo(vinculo_id):
    """
    Deletar permanentemente um vínculo
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    resultado, status = VinculoService.deletar_vinculo(vinculo_id)
    return jsonify(resultado), status


# ===========================
# ATUALIZAR OBSERVAÇÃO (PUT)
# ===========================
@vinculo_bp.route("/vinculo/<int:vinculo_id>/observacao", methods=["PUT", "OPTIONS"])
@cross_origin()
def atualizar_observacao(vinculo_id):
    """
    Atualizar observação de um vínculo
    
    Body esperado:
    {
        "observacao": "Nova observação"
    }
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    data = request.get_json()
    
    if not data or "observacao" not in data:
        return jsonify({"error": "Campo 'observacao' é obrigatório"}), 400
    
    resultado, status = VinculoService.atualizar_observacao_vinculo(vinculo_id, data["observacao"])
    return jsonify(resultado), status


# ===========================
# LISTAR GRUPO COMPLETO (GET)
# ===========================
@vinculo_bp.route("/formulario/<int:formulario_id>/grupo-vinculo", methods=["GET", "OPTIONS"])
@cross_origin()
def listar_grupo_vinculo(formulario_id):
    """
    Listar TODOS os lançamentos vinculados a um lançamento específico
    Retorna o grupo completo (principal + todos os relacionados)
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    grupo, status = VinculoService.listar_grupo_vinculo(formulario_id)
    
    if status != 200:
        return jsonify(grupo), status
    
    # Calcular valor total do grupo
    valor_total = sum(item.get("valor", 0) for item in grupo)
    
    return jsonify({
        "formulario_id": formulario_id,
        "total_lancamentos": len(grupo),
        "valor_total": valor_total,
        "lancamentos": grupo
    }), 200


# ===========================
# QUEBRAR TODOS VÍNCULOS (POST)
# ===========================
@vinculo_bp.route("/formulario/<int:formulario_id>/quebrar-vinculos", methods=["POST", "OPTIONS"])
@cross_origin()
def quebrar_vinculos_formulario(formulario_id):
    """
    Desativar TODOS os vínculos de um formulário
    Usado quando um lançamento é deletado ou necessita isolamento
    """
    
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200
    
    resultado, status = VinculoService.quebrar_todos_vinculos_formulario(formulario_id)
    return jsonify(resultado), status


# ===========================
# HEALTH CHECK (GET)
# ===========================
@vinculo_bp.route("/vinculo/health", methods=["GET"])
@cross_origin()
def vinculo_health():
    """
    Verificar se o serviço de vínculos está funcionando
    """
    return jsonify({"status": "OK", "service": "vinculo_service"}), 200
