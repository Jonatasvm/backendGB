from db import get_connection
from datetime import datetime


def registrar_exportacao(usuario, formulario_ids):
    """
    Registra uma exportação (geração de Excel) no histórico.
    Cria um registro pai em historico_exportacoes e os itens filhos.
    Retorna (exportacao_id, None) ou (None, erro).
    """
    if not formulario_ids or len(formulario_ids) == 0:
        return None, "Nenhum formulário informado"

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Inserir registro pai
        cursor.execute("""
            INSERT INTO historico_exportacoes (usuario, quantidade, data_geracao)
            VALUES (%s, %s, %s)
        """, (usuario, len(formulario_ids), datetime.now()))

        exportacao_id = cursor.lastrowid

        # 2. Inserir itens (cada formulário exportado)
        for fid in formulario_ids:
            cursor.execute("""
                INSERT INTO historico_exportacoes_itens (exportacao_id, formulario_id)
                VALUES (%s, %s)
            """, (exportacao_id, fid))

        conn.commit()
        return exportacao_id, None

    except Exception as e:
        conn.rollback()
        print("Erro ao registrar exportação:", e)
        return None, str(e)
    finally:
        cursor.close()
        conn.close()


def listar_exportacoes():
    """
    Retorna a lista de exportações (sem os itens), 
    ordenadas pela mais recente primeiro.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, usuario, quantidade, data_geracao
            FROM historico_exportacoes
            ORDER BY data_geracao DESC
        """)
        rows = cursor.fetchall()

        # Converter datetime para string
        for row in rows:
            if row.get("data_geracao"):
                row["data_geracao"] = row["data_geracao"].strftime("%d/%m/%Y %H:%M:%S")

        return rows, None

    except Exception as e:
        print("Erro ao listar exportações:", e)
        return None, str(e)
    finally:
        cursor.close()
        conn.close()


def buscar_itens_exportacao(exportacao_id):
    """
    Retorna os IDs dos formulários que pertencem a uma exportação.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT formulario_id
            FROM historico_exportacoes_itens
            WHERE exportacao_id = %s
        """, (exportacao_id,))
        rows = cursor.fetchall()

        ids = [row["formulario_id"] for row in rows]
        return ids, None

    except Exception as e:
        print("Erro ao buscar itens da exportação:", e)
        return None, str(e)
    finally:
        cursor.close()
        conn.close()
