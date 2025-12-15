"""
Execute este script UMA VEZ para gerar o token.json
Depois disso o backend funciona normalmente.
"""

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credencials.json'
TOKEN_FILE = 'token.json'

def gerar_token():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print("✅ token.json gerado com sucesso!")
    else:
        print("✅ token.json já existe e está válido!")

if __name__ == "__main__":
    gerar_token()
