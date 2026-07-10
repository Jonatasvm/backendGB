"""
Serviço de Bancos
Gerencia operações de CRUD para bancos cadastrados, incluindo hierarquia (subgrupos)
"""

from db import get_connection

def criar_banco(nome, conta_filha=None, id_pai=None):
    """
    Cria um novo banco
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Validar se já existe
        cursor.execute("SELECT id FROM bancos WHERE nome = %s", (nome,))
        if cursor.fetchone():
            return (None, "Banco com este nome já existe")
            
        # Validar se id_pai existe
        if id_pai is not None:
            cursor.execute("SELECT id FROM bancos WHERE id = %s", (id_pai,))
            if not cursor.fetchone():
                return (None, "Banco pai não encontrado")
                
        # Se tem id_pai, automaticamente é conta_filha
        if id_pai is not None:
            conta_filha = True

        cursor.execute(
            "INSERT INTO bancos (nome, conta_filha, id_pai) VALUES (%s, %s, %s)",
            (nome, conta_filha or 0, id_pai)
        )
        conn.commit()
        banco_id = cursor.lastrowid
        return ({"id": banco_id, "nome": nome, "conta_filha": conta_filha, "id_pai": id_pai}, None)
    except Exception as e:
        conn.rollback()
        raise Exception(f"Erro ao criar banco: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def listar_bancos():
    """
    Lista todos os bancos cadastrados com sua hierarquia
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT c.*, 
                   p.nome AS nome_pai
            FROM bancos c
            LEFT JOIN bancos p ON c.id_pai = p.id
            ORDER BY 
                CASE WHEN c.id_pai IS NULL THEN c.id ELSE c.id_pai END,
                c.id_pai IS NOT NULL,
                c.nome ASC
        """)
        bancos = cursor.fetchall()
        return bancos
    except Exception as e:
        raise Exception(f"Erro ao listar bancos: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def listar_bancos_pai():
    """
    Lista apenas bancos que não são contas filhas
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nome 
            FROM bancos 
            WHERE (conta_filha IS NULL OR conta_filha = 0) 
              AND id_pai IS NULL
            ORDER BY nome ASC
        """)
        bancos = cursor.fetchall()
        return bancos
    except Exception as e:
        raise Exception(f"Erro ao listar bancos pai: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def atualizar_banco(banco_id, nome, conta_filha=None, id_pai=None):
    """
    Atualiza um banco existente
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Validar se banco existe
        cursor.execute("SELECT id FROM bancos WHERE id = %s", (banco_id,))
        if not cursor.fetchone():
            return (None, "Banco não encontrado")
            
        # Validar se novo nome já existe
        if nome:
            cursor.execute("SELECT id FROM bancos WHERE nome = %s AND id != %s", (nome, banco_id))
            if cursor.fetchone():
                return (None, "Banco com este nome já existe")
                
        # Validar que não está se vinculando a si mesmo
        if id_pai is not None and int(id_pai) == int(banco_id):
            return (None, "Um banco não pode ser pai de si mesmo")
            
        # Validar se id_pai existe
        if id_pai is not None:
            cursor.execute("SELECT id FROM bancos WHERE id = %s", (id_pai,))
            if not cursor.fetchone():
                return (None, "Banco pai não encontrado")

        # Se tem id_pai, automaticamente é conta_filha
        if id_pai is not None:
            conta_filha = True

        cursor.execute(
            "UPDATE bancos SET nome = %s, conta_filha = %s, id_pai = %s WHERE id = %s",
            (nome, conta_filha or 0, id_pai, banco_id)
        )
        conn.commit()
        
        return ({"id": banco_id, "nome": nome, "conta_filha": conta_filha, "id_pai": id_pai}, None)
    except Exception as e:
        conn.rollback()
        raise Exception(f"Erro ao atualizar banco: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def deletar_banco(banco_id):
    """
    Deleta um banco e desvincula os filhos
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Validar se existe
        cursor.execute("SELECT id FROM bancos WHERE id = %s", (banco_id,))
        if not cursor.fetchone():
            return (False, "Banco não encontrado")
            
        # Desvincular filhas antes de deletar
        cursor.execute("UPDATE bancos SET id_pai = NULL, conta_filha = 0 WHERE id_pai = %s", (banco_id,))
        
        # Deletar
        cursor.execute("DELETE FROM bancos WHERE id = %s", (banco_id,))
        conn.commit()
        
        return (True, None)
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
        cursor.execute("""
            SELECT c.*, p.nome AS nome_pai
            FROM bancos c
            LEFT JOIN bancos p ON c.id_pai = p.id
            WHERE c.id = %s
        """, (banco_id,))
        banco = cursor.fetchone()
        return banco
    except Exception as e:
        raise Exception(f"Erro ao buscar banco: {str(e)}")
    finally:
        cursor.close()
        conn.close()
