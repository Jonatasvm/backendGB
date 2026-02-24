"""
Script para debugar onde as aspas estão vindo
"""
import mysql.connector
from config import DB_CONFIG
import json

conn = mysql.connector.connect(
    host=DB_CONFIG["host"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    database=DB_CONFIG["database"]
)

cursor = conn.cursor(dictionary=True)

# Pegar apenas 1 registro para debug
cursor.execute("""
    SELECT id, valor, data_pagamento
    FROM formulario
    LIMIT 1
""")

registro = cursor.fetchone()

if registro:
    print("\n=== RAW DATA DO BANCO ===")
    print(f"ID type: {type(registro['id'])} | value: {repr(registro['id'])}")
    print(f"Valor type: {type(registro['valor'])} | value: {repr(registro['valor'])}")
    print(f"Data type: {type(registro['data_pagamento'])} | value: {repr(registro['data_pagamento'])}")
    
    print("\n=== COMO JSON ===")
    json_str = json.dumps(registro, default=str)
    print(json_str)
    
    print("\n=== VERIFICANDO ASPAS ===")
    if isinstance(registro['id'], str) and "'" in str(registro['id']):
        print("❌ ID tem ASPAS!")
    else:
        print("✅ ID OK")
    
    if isinstance(registro['valor'], str) and "'" in str(registro['valor']):
        print("❌ VALOR tem ASPAS!")
    else:
        print("✅ VALOR OK")
        
    if isinstance(registro['data_pagamento'], str) and "'" in str(registro['data_pagamento']):
        print("❌ DATA tem ASPAS!")
    else:
        print("✅ DATA OK")
else:
    print("Nenhum registro encontrado")

cursor.close()
conn.close()
