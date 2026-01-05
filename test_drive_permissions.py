"""
Script de teste para verificar conexão com Google Drive
✅ ATUALIZADO: Usa API Key (simples)
"""

from services.google_drive_service import get_drive_service, ROOT_FOLDER_ID, API_KEY

def testar_conexao():
    """Testa se a API Key funciona corretamente"""
    
    try:
        print("=" * 50)
        print("🚀 Google Drive API - Teste com API Key")
        print("=" * 50)
        print()
        print(f"🔑 API Key: {API_KEY[:20]}...")
        print(f"📁 Pasta raiz: {ROOT_FOLDER_ID}")
        print()
        
        print("🔐 Conectando ao Google Drive...")
        service = get_drive_service()
        
        # Tentar acessar a pasta
        print("📂 Verificando acesso à pasta raiz...")
        folder = service.files().get(fileId=ROOT_FOLDER_ID).execute()
        print(f"✅ Pasta encontrada: {folder.get('name')}")
        
        # Tentar listar o conteúdo
        print("\n📋 Listando conteúdo da pasta...")
        results = service.files().list(
            q=f"'{ROOT_FOLDER_ID}' in parents",
            spaces='drive',
            fields='files(id, name)',
            pageSize=10
        ).execute()
        
        files = results.get('files', [])
        print(f"✅ Arquivos encontrados: {len(files)}")
        
        if files:
            print("\n📄 Primeiros arquivos:")
            for file in files:
                print(f"   • {file['name']}")
        
        # Tentar criar uma pasta de teste
        print("\n🧪 Testando criação de pasta...")
        test_folder = service.files().create(
            body={
                'name': 'TESTE_API_KEY',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [ROOT_FOLDER_ID]
            },
            fields='id'
        ).execute()
        
        test_folder_id = test_folder.get('id')
        print(f"✅ Pasta de teste criada: {test_folder_id}")
        
        # Deletar a pasta de teste
        print("🗑️ Deletando pasta de teste...")
        service.files().delete(fileId=test_folder_id).execute()
        print("✅ Pasta de teste deletada")
        
        print()
        print("=" * 50)
        print("✅✅✅ TUDO FUNCIONANDO PERFEITAMENTE! ✅✅✅")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ ERRO: {str(e)}")
        print("=" * 50)
        print()
        print("Verifique se:")
        print("  • A API Key está correta")
        print("  • Google Drive API está ativada no Google Cloud")
        print("  • O FOLDER_ID está correto")
        print("  • A pasta está compartilhada publicamente")
        
        import traceback
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    testar_conexao()
