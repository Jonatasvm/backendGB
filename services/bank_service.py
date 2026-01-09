"""
Serviço de Bancos
Gerencia operações de CRUD para bancos cadastrados
"""

from db import get_connection

def criar_banco(nome):
    """
    Cria um novo banco
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO bancos (nome) VALUES (%s)",
            (nome,)
        )
        conn.commit()
        banco_id = cursor.lastrowid
        return {"id": banco_id, "nome": nome}
    except Exception as e:
        conn.rollback()
        raise Exception(f"Erro ao criar banco: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def listar_bancos():
    """
    Lista todos os bancos cadastrados
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, nome FROM bancos ORDER BY nome ASC")
        bancos = cursor.fetchall()
        return bancos
    except Exception as e:
        raise Exception(f"Erro ao listar bancos: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def atualizar_banco(banco_id, nome):
    """
    Atualiza um banco existente
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE bancos SET nome = %s WHERE id = %s",
            (nome, banco_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise Exception("Banco não encontrado")
        
        return {"id": banco_id, "nome": nome}
    except Exception as e:
        conn.rollback()
        raise Exception(f"Erro ao atualizar banco: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def deletar_banco(banco_id):
    """
    Deleta um banco
    Retorna True se foi deletado, False se não existe
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM bancos WHERE id = %s", (banco_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise Exception("Banco não encontrado")
        
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Erro ao deletar banco: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def buscar_banco_por_id(banco_id):
    """
    Busca um banco específico por ID
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, nome FROM bancos WHERE id = %s", (banco_id,))
        banco = cursor.fetchone()
        return banco
    except Exception as e:
        raise Exception(f"Erro ao buscar banco: {str(e)}")
    finally:
        cursor.close()
        conn.close()
