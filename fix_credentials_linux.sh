#!/bin/bash

# Fix credentials.json no Linux
# Roda: bash fix_credentials_linux.sh

cd /home/gerenciaGR/backendGB || exit 1

# Backup do arquivo atual
cp credentials.json credentials.json.backup

# Use Python para consertar
python3 << 'PYTHON_SCRIPT'
import json
import sys

# Ler o arquivo
try:
    with open('credentials.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("✓ Arquivo JSON lido com sucesso")
except Exception as e:
    print(f"✗ Erro ao ler: {e}")
    sys.exit(1)

# Garantir que a chave privada tem quebras de linha corretas
if 'private_key' in data:
    # Se as quebras forem literais (\n como string), converter
    key = data['private_key']
    
    # Contar \n literal
    literal_count = key.count('\\n')
    real_count = key.count('\n')
    
    print(f"  Quebras literais (\\n): {literal_count}")
    print(f"  Quebras reais (newline): {real_count}")
    
    if literal_count > real_count:
        print("  Convertendo \\n literal para newlines reais...")
        key = key.replace('\\n', '\n')
        data['private_key'] = key
    
    # Validar
    if key.startswith('-----BEGIN PRIVATE KEY-----\n') and key.endswith('\n-----END PRIVATE KEY-----\n'):
        print("✓ Chave privada está no formato correto")
    else:
        print("✗ Formato de chave privada pode estar errado")
        print(f"  Começa com: {key[:40]}")
        print(f"  Termina com: {key[-40:]}")

# Escrever arquivo corrigido
try:
    with open('credentials.json', 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2)
    print("✓ Arquivo corrigido e salvo")
except Exception as e:
    print(f"✗ Erro ao salvar: {e}")
    sys.exit(1)

# Validar o arquivo salvo
try:
    with open('credentials.json', 'r', encoding='utf-8') as f:
        verify = json.load(f)
    print("✓ Arquivo validado com sucesso")
except Exception as e:
    print(f"✗ Erro ao validar: {e}")
    sys.exit(1)

print("\n✓ Credenciais corrigidas com sucesso!")
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "Agora teste com:"
    echo "  python3 test_drive_permissions.py"
else
    echo ""
    echo "✗ Erro ao processar credenciais"
    echo "Restaurando backup..."
    mv credentials.json.backup credentials.json
    exit 1
fi
