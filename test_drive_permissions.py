"""
Script de teste para verificar permissões no Google Drive
"""

import sys
sys.path.insert(0, '/home/gerenciaGR/backendGB')

from services.google_drive_service import get_drive_service, ROOT_FOLDER_ID

try:
    print(f"[TEST] Testando acesso à pasta raiz: {ROOT_FOLDER_ID}")
    
    service = get_drive_service()
    
    # Tentar acessar a pasta
    folder = service.files().get(fileId=ROOT_FOLDER_ID).execute()
    print(f"✓ Pasta encontrada: {folder.get('name')}")
    
    # Tentar listar o conteúdo
    results = service.files().list(
        q=f"'{ROOT_FOLDER_ID}' in parents",
        spaces='drive',
        fields='files(id, name)',
        pageSize=10
    ).execute()
    
    files = results.get('files', [])
    print(f"✓ Conteúdo da pasta ({len(files)} itens):")
    for file in files:
        print(f"  - {file['name']}")
    
    # Tentar criar uma pasta de teste
    print(f"\n[TEST] Tentando criar pasta de teste...")
    test_folder = service.files().create(
        body={
            'name': 'TESTE_PERMISSAO',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [ROOT_FOLDER_ID]
        },
        fields='id'
    ).execute()
    
    test_folder_id = test_folder.get('id')
    print(f"✓ Pasta de teste criada: {test_folder_id}")
    
    # Deletar a pasta de teste
    print(f"\n[TEST] Deletando pasta de teste...")
    service.files().delete(fileId=test_folder_id).execute()
    print(f"✓ Pasta de teste deletada")
    
    print(f"\n✓✓✓ TUDO FUNCIONANDO PERFEITAMENTE ✓✓✓")
    
except Exception as e:
    print(f"✗ ERRO: {str(e)}")
    import traceback
    traceback.print_exc()
