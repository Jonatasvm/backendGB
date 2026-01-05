"""
Execute este script UMA VEZ para gerar o token.json
Depois disso o backend funciona normalmente.

Este script usa OAuth 2.0 Web para autenticar com Google Drive.
"""

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']
# ✅ ALTERADO: Usar o novo client_secret.json
CREDENTIALS_FILE = 'client_secret.json'
TOKEN_FILE = 'token.json'

def gerar_token():
    creds = None

    if os.path.exists(TOKEN_FILE):
        print(f"📄 Carregando token existente de {TOKEN_FILE}...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())
        else:
            print(f"🔐 Abrindo navegador para autorizar com Google...")
            print(f"📁 Usando credenciais de: {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            # ✅ CORRIGIDO: Usar porta fixa 8080 (deve estar configurada no Google Cloud)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print("✅ token.json gerado com sucesso!")
        print(f"📍 Arquivo salvo em: {os.path.abspath(TOKEN_FILE)}")
    else:
        print("✅ token.json já existe e está válido!")

if __name__ == "__main__":
    try:
        gerar_token()
    except FileNotFoundError as e:
        print(f"❌ Erro: {e}")
        print(f"Certifique-se de que o arquivo '{CREDENTIALS_FILE}' existe no diretório atual.")
    except Exception as e:
        print(f"❌ Erro ao gerar token: {e}")
