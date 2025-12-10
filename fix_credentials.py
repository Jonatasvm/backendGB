#!/usr/bin/env python3
"""
Script para converter os \n literais em quebras de linha reais
"""

import json

try:
    # Ler o arquivo
    with open('credentials.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Converter os \n literais em quebras de linha reais
    if 'private_key' in data:
        # O JSON já decodificou os \n, então precisa ser direto
        key = data['private_key']
        
        # Verificar se tem os \n como string literal
        if '\\n' in key:
            print("⚠️  Convertendo \\n literais em quebras de linha...")
            key = key.replace('\\n', '\n')
            data['private_key'] = key
        
        # Reescrever
        with open('credentials.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print("✓ Arquivo convertido!")
        
        # Verificar
        with open('credentials.json', 'r', encoding='utf-8') as f:
            verify = json.load(f)
        
        final_key = verify['private_key']
        lines = final_key.split('\n')
        print(f"✓ Chave privada tem {len(lines)} linhas")
        print(f"✓ Primeira linha: {lines[0]}")
        print(f"✓ Última linha: {lines[-1]}")
        print(f"✓ PRONTO!")
    else:
        print("✗ Chave privada não encontrada")

except Exception as e:
    print(f"✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
