"""
Database Migration Script
Executes SQL migrations to set up the database schema
"""

import mysql.connector
from config import DB_CONFIG

def run_migrations():
    """
    Execute the migration SQL script to create necessary tables
    """
    conn = None
    cursor = None
    
    try:
        # Connect to the database
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        
        cursor = conn.cursor()
        
        # Read the migrations file
        with open("migrations.sql", "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        # Split by semicolon to execute individual statements
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
        
        for statement in statements:
            if statement:
                print(f"Executing: {statement[:80]}...")
                cursor.execute(statement)
        
        conn.commit()
        print("✓ All migrations executed successfully!")
        
    except Exception as e:
        print(f"✗ Error executing migrations: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    print("Starting database migrations...")
    success = run_migrations()
    exit(0 if success else 1)
