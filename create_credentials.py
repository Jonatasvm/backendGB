#!/usr/bin/env python3
"""
Script para criar o credentials.json com a chave privada corretamente formatada
Execute no servidor Linux e ele criará o arquivo correto
"""

import json
import os

# A chave privada - usando escape sequences corretos
# O JSON.dump vai converter \n automaticamente
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7hmmBOEWgRLim\nWzZatCQ+4WGE84U1lzQ82vOWyZcDhK4IhA/PnjUd6H0RSbZT6n6i9NmhKMyH0HfL\n2Xz+7APDuWAW7qTMo+Y5opbAhcm3eSy5kWDtVV85Hnyc1Q3TpSnhFI5uiZdonUI2\nLQ4wg24y14RnkQD/zJArKjzV26b3Evm4KD82rsRyRLTIGLz1/ziyYUY3KmAjwAyZ\nK0qROjDC2cB1mRpZVa2s3DdlEUJLkgbPihZW5Ld+AZwBDqpAdwf0JB8NJL5aWmYv\nR8zug40HPmAbqaP6U1nnh7mg6TC7MjCi/57Smltpn91jaWuxS5vgWOij7uXkII/n\n+QCZVXBhAgMBAAECggEASiKQUUKi3AJvEW1b5q3y6l0FxZ7UWeRmBWz2AfW+Wui4\nOKuk6Ip+K02/K/d9Ol2pJNkxtHHBsiurQI7ByLIbpuQBZe+AfVqKaNyrRn9dyMgB\n83bS3+DxXU59Ky9bYQGZtd7/lBmXHweUpoBXbLx482aadKsxvu7rS/VNyaolruVF\nZIq/e0ybhjitBF3gp7052cmJ2ix9zdqdjPPEJ6NGaFubvaSedVpd9X+vGa/VhFQ4\nirDsK+/EFWi+cnVjEUuOsc80YJ8RFS8vB3MPHHF+GaBMIdAj6uLqBBcxlQ/l5GPx\n4+dRq8A6dB6UXqVOZch72UMrpBlWagdNz2sZ5bOopQKBgQD+QawiH5HUgSGXLgI7\nJYJ6kiTTmh1DXdFiCuasG+wcd95i94RefHdZUgzI66lo07CAkSl7wgueu0ZUezma\nM1t0C3vR+PUCAQeSiFgTEMM4LroD50MxgfRRbtGLCCcTprLELi17jW0oRvdTUnmp\nc55Fl/HehJdv1Y4gg/BgHRr46wKBgQC8z5kIyO+OihG5IlglBLA5sbxqrBYYHa3Q\noWdl6qoE4fCLeZdx8fw+y9l0Xo9zEA6ITLq/RR75HGakdYBFWd1wG3cVUtX44DZ1\nAhXZqtb7iuFSDltN6UUqkeVEV3izPqF9WphmIenIDe2hZvipLrgFkdDxNd60H8Rs\nYT+KeRIo4wKBgBlfXFobZGYcbMm1YaudVqP8qYgkPP9YAWkTRWmvb6R3oc2mfaMg\nMJjNQ1FZkxJO7bImykj7WEWC0sXjdiAZN+sgqj6N5YVJrQPGb2OXrKOSpiV1kpMC\nMOtfb7G8IoonfHdvVEKcHmSCkHPUKyfpzcWMICrgeGxEl2ZPRFGTFfn5AoGBAJjp\n9MH1onYpggMTOpn4exSuyq8F4fr0BnJiVdBnxfygU+VRu4Kv/Z+KDvo9HyaMCYj/\nw3rm6xfLlaF5/EGubzW9OKuPY/Xk+JW486NOxkAAkU2YjP/DfZ3lfO3lfb6FadqR\nBb4plyHLjfna4GZ8jNMN7k98VnpBBB7Wf9SRC1ELAoGAc8AXfRt9khn/gujiDfTb\nd1BsZr2bk2jjR+Ch4H3D47UjfE04uApShrhPV6zIo6gEZscye44u1p3rgZveDSy6\nZhKalcHWjgkzmSEuryahA2SXN5musc79C9fgLEUk6R5MuM1/HSj2+9escvJsiU7b\nsagaEHL1LxNGm/NRW0LTMivg=\n-----END PRIVATE KEY-----"

credentials_data = {
    "type": "service_account",
    "project_id": "axiomatic-atlas-369920",
    "private_key_id": "f53a16b3702d02b6e0def2c8fbcaa90df1ffba21",
    "private_key": private_key,
    "client_email": "pagamento@axiomatic-atlas-369920.iam.gserviceaccount.com",
    "client_id": "107251519215428083258",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/pagamento%40axiomatic-atlas-369920.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Escrever o arquivo com UTF-8 encoding explícito
output_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(credentials_data, f, indent=2, ensure_ascii=False)

print(f"✓ Arquivo credentials.json criado com sucesso em: {output_path}")
print(f"✓ Tamanho: {os.path.getsize(output_path)} bytes")

# Verificar se a chave foi escrita corretamente
try:
    with open(output_path, 'r', encoding='utf-8') as f:
        check = json.load(f)
    print(f"✓ JSON é válido")
    
    # Verificar a chave privada
    key = check['private_key']
    if key.startswith('-----BEGIN PRIVATE KEY-----') and key.endswith('-----END PRIVATE KEY-----'):
        print(f"✓ Chave privada tem formato correto")
        lines = key.split('\n')
        print(f"✓ Chave privada tem {len(lines)} linhas")
    else:
        print(f"✗ ERRO: Chave privada tem formato incorreto")
        print(f"  Começa com: {key[:50]}")
        print(f"  Termina com: {key[-50:]}")
except Exception as e:
    print(f"✗ ERRO ao verificar: {e}")
