#!/usr/bin/env python3
"""
Script para criar o credentials.json com a chave privada corretamente formatada
Execute no servidor Linux e ele criará o arquivo correto
"""

import json
import os

# Construir a chave privada com quebras de linha reais
private_key_lines = [
    "-----BEGIN PRIVATE KEY-----",
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7hmmBOEWgRLim",
    "WzZatCQ+4WGE84U1lzQ82vOWyZcDhK4IhA/PnjUd6H0RSbZT6n6i9NmhKMyH0HfL",
    "2Xz+7APDuWAW7qTMo+Y5opbAhcm3eSy5kWDtVV85Hnyc1Q3TpSnhFI5uiZdonUI2",
    "LQ4wg24y14RnkQD/zJArKjzV26b3Evm4KD82rsRyRLTIGLz1/ziyYUY3KmAjwAyZ",
    "K0qROjDC2cB1mRpZVa2s3DdlEUJLkgbPihZW5Ld+AZwBDqpAdwf0JB8NJL5aWmYv",
    "R8zug40HPmAbqaP6U1nnh7mg6TC7MjCi/57Smltpn91jaWuxS5vgWOij7uXkII/n",
    "+QCZVXBhAgMBAAECggEASiKQUUKi3AJvEW1b5q3y6l0FxZ7UWeRmBWz2AfW+Wui4",
    "OKuk6Ip+K02/K/d9Ol2pJNkxtHHBsiurQI7ByLIbpuQBZe+AfVqKaNyrRn9dyMgB",
    "83bS3+DxXU59Ky9bYQGZtd7/lBmXHweUpoBXbLx482aadKsxvu7rS/VNyaolruVF",
    "ZIq/e0ybhjitBF3gp7052cmJ2ix9zdqdjPPEJ6NGaFubvaSedVpd9X+vGa/VhFQ4",
    "irDsK+/EFWi+cnVjEUuOsc80YJ8RFS8vB3MPHHF+GaBMIdAj6uLqBBcxlQ/l5GPx",
    "4+dRq8A6dB6UXqVOZch72UMrpBlWagdNz2sZ5bOopQKBgQD+QawiH5HUgSGXLgI7",
    "JYJ6kiTTmh1DXdFiCuasG+wcd95i94RefHdZUgzI66lo07CAkSl7wgueu0ZUezma",
    "M1t0C3vR+PUCAQeSiFgTEMM4LroD50MxgfRRbtGLCCcTprLELi17jW0oRvdTUnmp",
    "c55Fl/HehJdv1Y4gg/BgHRr46wKBgQC8z5kIyO+OihG5IlglBLA5sbxqrBYYHa3Q",
    "oWdl6qoE4fCLeZdx8fw+y9l0Xo9zEA6ITLq/RR75HGakdYBFWd1wG3cVUtX44DZ1",
    "AhXZqtb7iuFSDltN6UUqkeVEV3izPqF9WphmIenIDe2hZvipLrgFkdDxNd60H8Rs",
    "YT+KeRIo4wKBgBlfXFobZGYcbMm1YaudVqP8qYgkPP9YAWkTRWmvb6R3oc2mfaMg",
    "MJjNQ1FZkxJO7bImykj7WEWC0sXjdiAZN+sgqj6N5YVJrQPGb2OXrKOSpiV1kpMC",
    "MOtfb7G8IoonfHdvVEKcHmSCkHPUKyfpzcWMICrgeGxEl2ZPRFGTFfn5AoGBAJjp",
    "9MH1onYpggMTOpn4exSuyq8F4fr0BnJiVdBnxfygU+VRu4Kv/Z+KDvo9HyaMCYj/",
    "w3rm6xfLlaF5/EGubzW9OKuPY/Xk+JW486NOxkAAkU2YjP/DfZ3lfO3lfb6FadqR",
    "Bb4plyHLjfna4GZ8jNMN7k98VnpBBB7Wf9SRC1ELAoGAc8AXfRt9khn/gujiDfTb",
    "d1BsZr2bk2jjR+Ch4H3D47UjfE04uApShrhPV6zIo6gEZscye44u1p3rgZveDSy6",
    "ZhKalcHWjgkzmSEuryahA2SXN5musc79C9fgLEUk6R5MuM1/HSj2+9escvJsiU7b",
    "sagaEHL1LxNGm/NRW0LTMivg=",
    "-----END PRIVATE KEY-----"
]

private_key = "\n".join(private_key_lines)

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

# Escrever o arquivo com UTF-8 encoding
output_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(credentials_data, f, indent=2)

print(f"✓ Arquivo credentials.json criado com sucesso!")
print(f"✓ Tamanho: {os.path.getsize(output_path)} bytes")

# Verificar se está OK
try:
    with open(output_path, 'r', encoding='utf-8') as f:
        check = json.load(f)
    
    key = check['private_key']
    if key.startswith('-----BEGIN PRIVATE KEY-----') and key.endswith('-----END PRIVATE KEY-----'):
        print(f"✓ Chave privada tem formato correto")
        lines = key.split('\n')
        print(f"✓ Chave privada tem {len(lines)} linhas")
        print(f"✓ PRONTO PARA USAR!")
    else:
        print(f"✗ ERRO: Chave tem formato incorreto")
except Exception as e:
    print(f"✗ ERRO: {e}")
