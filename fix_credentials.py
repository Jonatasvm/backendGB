#!/usr/bin/env python3
"""
Script para limpar o credentials.json e remover BOM ou caracteres inválidos
"""

import json
import sys

try:
    # Ler o arquivo como binário para detectar BOM
    with open('credentials.json', 'rb') as f:
        content = f.read()
    
    # Remover BOM se existir
    if content.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
        print("⚠️  Removendo UTF-8 BOM...")
        content = content[3:]
    
    # Decodificar como UTF-8
    text = content.decode('utf-8')
    
    # Parsear JSON
    data = json.loads(text)
    
    # Reescrever o arquivo SEM BOM
    with open('credentials.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print("✓ Arquivo credentials.json limpo com sucesso!")
    print(f"✓ Tamanho: {len(open('credentials.json', 'rb').read())} bytes")
    
    # Verificar
    with open('credentials.json', 'r', encoding='utf-8') as f:
        verify = json.load(f)
    
    key = verify['private_key']
    print(f"✓ Chave privada OK: {len(key)} caracteres")
    print(f"✓ PRONTO PARA USAR!")
    
except Exception as e:
    print(f"✗ ERRO: {e}")
    sys.exit(1)
