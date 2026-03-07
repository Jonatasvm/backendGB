"""
Script para adicionar o role 'financeiro' na coluna ENUM da tabela users.
Execute este script uma única vez no servidor onde roda o banco MySQL.
"""
from db import get_connection

def run_migration():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("Alterando coluna 'role' da tabela 'users' para incluir 'financeiro'...")
        cursor.execute("""
            ALTER TABLE `users` 
            MODIFY COLUMN `role` ENUM('admin', 'user', 'financeiro') NOT NULL DEFAULT 'user'
        """)
        conn.commit()
        print("✅ Sucesso! Coluna 'role' agora aceita: admin, user, financeiro")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
