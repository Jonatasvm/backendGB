"""
Migration: Adicionar role 'financeiro' na tabela users
Execute na VPS: python migration_add_financeiro.py
"""
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345678gR$",
    "database": "gerenciaobra"
}

def run_migration():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("🔄 Alterando coluna 'role' para aceitar 'financeiro'...")

    cursor.execute("""
        ALTER TABLE users 
        MODIFY COLUMN role ENUM('admin', 'user', 'financeiro') 
        NOT NULL DEFAULT 'user'
    """)

    conn.commit()
    print("✅ Coluna 'role' atualizada com sucesso!")
    print("   Valores aceitos agora: admin, user, financeiro")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_migration()
