"""
Script para testar Google Drive API com API Key
✅ Simples e direto - sem OAuth, sem tokens!

Execute: python gerar_token.py
"""

import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ✅ SUA API KEY
API_KEY = "AIzaSyD1XxTV5p6SDm5-WkEPmh05XVtM1nEFrxY"

# ID da pasta do Google Drive
FOLDER_ID = "123C6ItHLqoRnb_hNNHRwE7FczSh9yhun"


def testar_api_key():
    """Testar se a API Key funciona"""
    
    try:
        print("=" * 50)
        print("🚀 Google Drive API - Teste com API Key")
        print("=" * 50)
        print()
        print(f"🔑 API Key: {API_KEY[:20]}...")
        print(f"📁 Pasta ID: {FOLDER_ID}")
        print()
        
        print("🔐 Conectando ao Google Drive...")
        
        # Criar cliente do Drive
        service = build('drive', 'v3', developerKey=API_KEY)
        
        # Testar listando arquivos da pasta
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            spaces='drive',
            fields='files(id, name)',
            pageSize=5
        ).execute()
        
        files = results.get('files', [])
        
        print("✅ API Key funcionando!")
        print(f"📄 Arquivos encontrados: {len(files)}")
        
        if files:
            print("\n📋 Primeiros arquivos:")
            for file in files:
                print(f"   • {file['name']} (ID: {file['id']})")
        
        print()
        print("=" * 50)
        print("✅ Conexão com Google Drive OK!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Erro: {e}")
        print("=" * 50)
        print()
        print("Verifique se:")
        print("  • A API Key está correta")
        print("  • Google Drive API está ativada")
        print("  • O FOLDER_ID está correto")
        print("  • A pasta está compartilhada publicamente")
        return False


def upload_arquivo(caminho_arquivo):
    """Fazer upload de arquivo para Google Drive"""
    
    try:
        service = build('drive', 'v3', developerKey=API_KEY)
        
        file_metadata = {
            'name': os.path.basename(caminho_arquivo),
            'parents': [FOLDER_ID]
        }
        
        media = MediaFileUpload(caminho_arquivo)
        
        # Fazer upload
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        print(f"✅ Arquivo enviado com sucesso!")
        print(f"📄 Nome: {file_metadata['name']}")
        print(f"🔗 Link: {file['webViewLink']}")
        
        return file['id']
        
    except Exception as e:
        print(f"❌ Erro ao fazer upload: {e}")
        return None


if __name__ == "__main__":
    print()
    
    # Testar conexão
    if testar_api_key():
        print("\n✅ Tudo pronto para usar!")
        print("\nPara fazer upload de um arquivo, use:")
        print("  upload_arquivo('caminho/do/arquivo.pdf')")
    else:
        print("\n❌ Erro na autenticação")
