"""
Serviço para gerenciar vínculos entre lançamentos (formularios)
Responsável por criar, atualizar, deletar e listar vínculos
"""

from db import get_connection
from datetime import datetime, timezone, timedelta

# Timezone: UTC-3 (Brasília)
BRASILIA_TZ = timezone(timedelta(hours=-3))

class VinculoService:
    """Gerencia vínculos entre múltiplos lançamentos"""
    
    @staticmethod
    def criar_vinculo(formulario_id_principal, formulario_id_vinculado, tipo_vinculo='multiple_payment', observacao=None):
        """
        Criar um novo vínculo entre dois lançamentos
        
        Args:
            formulario_id_principal: ID do lançamento principal
            formulario_id_vinculado: ID do lançamento vinculado
            tipo_vinculo: Tipo de vínculo (multiple_payment, adjustment, reversal, split, other)
            observacao: Observação opcional sobre o vínculo
            
        Returns:
            dict com ID do vínculo criado ou erro
        """
        
        # Validações
        if formulario_id_principal == formulario_id_vinculado:
            return {"error": "Um lançamento não pode estar vinculado a si mesmo"}, 400
        
        if not tipo_vinculo in ['multiple_payment', 'adjustment', 'reversal', 'split', 'other']:
            return {"error": "Tipo de vínculo inválido"}, 400
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Verificar se ambos formulários existem
            cursor.execute("SELECT id FROM formulario WHERE id IN (%s, %s)", (formulario_id_principal, formulario_id_vinculado))
            if len(cursor.fetchall()) != 2:
                return {"error": "Um ou ambos os lançamentos não existem"}, 404
            
            # Inserir vínculo (usar LEAST/GREATEST para evitar duplicatas)
            sql = """
            INSERT INTO formulario_vinculos 
            (formulario_id_principal, formulario_id_vinculado, tipo_vinculo, ativo, observacao)
            VALUES (%s, %s, %s, 1, %s)
            """
            
            cursor.execute(sql, (formulario_id_principal, formulario_id_vinculado, tipo_vinculo, observacao))
            conn.commit()
            
            vinculo_id = cursor.lastrowid
            return {"id": vinculo_id, "message": "Vínculo criado com sucesso"}, 201
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao criar vínculo: {e}")
            return {"error": f"Erro ao criar vínculo: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def obter_vinculos_por_formulario(formulario_id, apenas_ativos=True):
        """
        Obter todos os vínculos de um lançamento
        
        Args:
            formulario_id: ID do formulário
            apenas_ativos: Se True, retorna apenas vínculos ativos
            
        Returns:
            Lista de vínculos relacionados
        """
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            condicao_ativo = "AND v.ativo = 1" if apenas_ativos else ""
            
            # Buscar vínculos onde é principal ou vinculado
            sql = f"""
            SELECT 
                v.id,
                v.formulario_id_principal,
                v.formulario_id_vinculado,
                v.tipo_vinculo,
                v.ativo,
                v.observacao,
                v.created_at,
                v.updated_at,
                -- Identificar qual é o "outro" lançamento
                CASE 
                    WHEN v.formulario_id_principal = %s THEN v.formulario_id_vinculado
                    ELSE v.formulario_id_principal
                END as formulario_id_outro,
                -- Dados do "outro" lançamento
                f.referente,
                f.valor,
                f.obra,
                f.data_pagamento,
                f.status
            FROM formulario_vinculos v
            JOIN formulario f ON (
                (v.formulario_id_principal = %s AND f.id = v.formulario_id_vinculado)
                OR
                (v.formulario_id_vinculado = %s AND f.id = v.formulario_id_principal)
            )
            WHERE (v.formulario_id_principal = %s OR v.formulario_id_vinculado = %s)
            {condicao_ativo}
            ORDER BY v.created_at DESC
            """
            
            cursor.execute(sql, (formulario_id, formulario_id, formulario_id, formulario_id, formulario_id))
            vinculos = cursor.fetchall()
            
            # Converter Decimals para float
            for vinculo in vinculos:
                if 'valor' in vinculo and vinculo['valor'] is not None:
                    vinculo['valor'] = float(vinculo['valor'])
            
            return vinculos, 200
            
        except Exception as e:
            print(f"Erro ao buscar vínculos: {e}")
            return {"error": f"Erro ao buscar vínculos: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def desativar_vinculo(vinculo_id):
        """
        Desativar um vínculo (soft delete)
        
        Args:
            vinculo_id: ID do vínculo
            
        Returns:
            Status da operação
        """
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = "UPDATE formulario_vinculos SET ativo = 0 WHERE id = %s"
            cursor.execute(sql, (vinculo_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"error": "Vínculo não encontrado"}, 404
            
            return {"message": "Vínculo desativado com sucesso"}, 200
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao desativar vínculo: {e}")
            return {"error": f"Erro ao desativar vínculo: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def ativar_vinculo(vinculo_id):
        """
        Reativar um vínculo que foi desativado
        
        Args:
            vinculo_id: ID do vínculo
            
        Returns:
            Status da operação
        """
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = "UPDATE formulario_vinculos SET ativo = 1 WHERE id = %s"
            cursor.execute(sql, (vinculo_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"error": "Vínculo não encontrado"}, 404
            
            return {"message": "Vínculo reativado com sucesso"}, 200
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao reativar vínculo: {e}")
            return {"error": f"Erro ao reativar vínculo: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def deletar_vinculo(vinculo_id):
        """
        Deletar permanentemente um vínculo (hard delete)
        
        Args:
            vinculo_id: ID do vínculo
            
        Returns:
            Status da operação
        """
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = "DELETE FROM formulario_vinculos WHERE id = %s"
            cursor.execute(sql, (vinculo_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"error": "Vínculo não encontrado"}, 404
            
            return {"message": "Vínculo deletado com sucesso"}, 200
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao deletar vínculo: {e}")
            return {"error": f"Erro ao deletar vínculo: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def atualizar_observacao_vinculo(vinculo_id, observacao):
        """
        Atualizar observação de um vínculo
        
        Args:
            vinculo_id: ID do vínculo
            observacao: Nova observação
            
        Returns:
            Status da operação
        """
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
            UPDATE formulario_vinculos 
            SET observacao = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            cursor.execute(sql, (observacao, vinculo_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"error": "Vínculo não encontrado"}, 404
            
            return {"message": "Observação atualizada com sucesso"}, 200
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao atualizar observação: {e}")
            return {"error": f"Erro ao atualizar observação: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def quebrar_todos_vinculos_formulario(formulario_id):
        """
        Desativar TODOS os vínculos de um formulário
        Usado quando um lançamento é deletado ou necessita isolamento
        
        Args:
            formulario_id: ID do formulário
            
        Returns:
            Quantidade de vínculos desativados
        """
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
            UPDATE formulario_vinculos 
            SET ativo = 0, observacao = CONCAT(COALESCE(observacao, ''), ' [QUEBRADO - Lançamento deletado]')
            WHERE (formulario_id_principal = %s OR formulario_id_vinculado = %s)
            AND ativo = 1
            """
            cursor.execute(sql, (formulario_id, formulario_id))
            conn.commit()
            
            return {"quebrados": cursor.rowcount}, 200
            
        except Exception as e:
            conn.rollback()
            print(f"Erro ao quebrar vínculos: {e}")
            return {"error": f"Erro ao quebrar vínculos: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def listar_grupo_vinculo(formulario_id):
        """
        Listar TODO o grupo de lançamentos vinculados (recursivo)
        Retorna o lançamento principal + todos os vinculados
        
        Args:
            formulario_id: ID de qualquer lançamento do grupo
            
        Returns:
            Lista com todos os lançamentos do grupo
        """
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Usar WITH RECURSIVE para pegar o grupo completo
            sql = """
            WITH RECURSIVE grupo AS (
                -- Caso base: encontrar o lançamento inicial
                SELECT 
                    id,
                    formulario_id_principal,
                    formulario_id_vinculado,
                    ativo
                FROM formulario_vinculos
                WHERE (formulario_id_principal = %s OR formulario_id_vinculado = %s)
                
                UNION ALL
                
                -- Recursivo: encontrar todos os conectados
                SELECT 
                    fv.id,
                    fv.formulario_id_principal,
                    fv.formulario_id_vinculado,
                    fv.ativo
                FROM formulario_vinculos fv
                JOIN grupo g ON (
                    (fv.formulario_id_principal = g.formulario_id_principal OR fv.formulario_id_principal = g.formulario_id_vinculado)
                    OR
                    (fv.formulario_id_vinculado = g.formulario_id_principal OR fv.formulario_id_vinculado = g.formulario_id_vinculado)
                )
                WHERE fv.ativo = 1 AND g.ativo = 1
            )
            SELECT DISTINCT 
                f.id,
                f.referente,
                f.valor,
                f.obra,
                f.data_pagamento,
                f.data_lancamento,
                f.solicitante,
                f.titular,
                f.status
            FROM formulario f
            WHERE f.id IN (
                SELECT DISTINCT CASE 
                    WHEN formulario_id_principal = %s THEN formulario_id_principal
                    ELSE formulario_id_vinculado
                END
                FROM formulario_vinculos
                WHERE ativo = 1 AND (formulario_id_principal = %s OR formulario_id_vinculado = %s)
                
                UNION
                
                SELECT DISTINCT formulario_id_principal
                FROM formulario_vinculos
                WHERE ativo = 1 AND (formulario_id_principal = %s OR formulario_id_vinculado = %s)
                
                UNION
                
                SELECT DISTINCT formulario_id_vinculado
                FROM formulario_vinculos
                WHERE ativo = 1 AND (formulario_id_principal = %s OR formulario_id_vinculado = %s)
            )
            ORDER BY f.id ASC
            """
            
            cursor.execute(sql, (
                formulario_id, formulario_id,  # Caso base
                formulario_id, formulario_id, formulario_id,  # Primeira UNION
                formulario_id, formulario_id,  # Segunda UNION
                formulario_id, formulario_id  # Terceira UNION
            ))
            
            grupo = cursor.fetchall()
            
            # Converter Decimals para float
            for item in grupo:
                if 'valor' in item and item['valor'] is not None:
                    item['valor'] = float(item['valor'])
            
            return grupo, 200
            
        except Exception as e:
            print(f"Erro ao listar grupo: {e}")
            return {"error": f"Erro ao listar grupo: {str(e)}"}, 500
        finally:
            cursor.close()
            conn.close()
