"""
Serviço para integração com Google Drive
Realiza upload de arquivos e cria pastas
✅ ATUALIZADO: Usa API Key (simples) ao invés de OAuth
"""

import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ✅ API KEY do Google Cloud
API_KEY = "AIzaSyD1XxTV5p6SDm5-WkEPmh05XVtM1nEFrxY"

# ID da pasta raiz onde salvar os lançamentos
# https://drive.google.com/drive/folders/123C6ItHLqoRnb_hNNHRwE7FczSh9yhun
ROOT_FOLDER_ID = "123C6ItHLqoRnb_hNNHRwE7FczSh9yhun"


def get_drive_service():
    """
    Retorna um cliente do Google Drive usando API Key
    ✅ Simples e direto - sem OAuth, sem tokens!
    """
    return build('drive', 'v3', developerKey=API_KEY)


def create_folder(folder_name, parent_id=ROOT_FOLDER_ID):
    """
    Cria uma pasta no Google Drive
    
    Args:
        folder_name: Nome da pasta a criar
        parent_id: ID da pasta pai (default é a raiz)
    
    Returns:
        ID da pasta criada
    """
    service = get_drive_service()
    
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    
    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()
    
    return folder.get('id')


def upload_file_to_drive(file_obj, filename, folder_id):
    """
    Faz upload de um arquivo para o Google Drive
    
    Args:
        file_obj: Objeto de arquivo (FileStorage do Flask)
        filename: Nome do arquivo
        folder_id: ID da pasta destino
    
    Returns:
        Dict com 'id' e 'webViewLink' do arquivo
    """
    from googleapiclient.http import MediaIoBaseUpload
    
    service = get_drive_service()
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    # Detectar o MIME type baseado na extensão
    import mimetypes
    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype is None:
        mimetype = 'application/octet-stream'
    
    # Usar MediaIoBaseUpload para arquivos do Flask (FileStorage)
    media = MediaIoBaseUpload(
        file_obj.stream,
        mimetype=mimetype,
        resumable=True,
        chunksize=1024 * 1024  # 1MB chunks
    )
    
    file_obj_drive = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    file_id = file_obj_drive.get('id')
    
    # Tornar o arquivo público (qualquer pessoa com o link pode ver/baixar)
    try:
        service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()
        print(f"[DEBUG] Arquivo {filename} tornado público")
    except Exception as e:
        print(f"[AVISO] Não foi possível tornar o arquivo público: {e}")
    
    return {
        'id': file_id,
        'webViewLink': file_obj_drive.get('webViewLink'),
        'name': filename
    }


def upload_files_batch(files, form_id, obra_id):
    """
    Realiza upload de múltiplos arquivos para o Google Drive
    Cria uma pasta específica para o lançamento
    
    Args:
        files: Lista de objetos FileStorage do Flask
        form_id: ID do formulário (lançamento)
        obra_id: ID da obra
    
    Returns:
        Lista de dicts com links dos arquivos upados
    """
    try:
        # Criar pasta para este lançamento
        folder_name = f"Lançamento_{form_id}_Obra_{obra_id}"
        print(f"[DEBUG] Criando pasta: {folder_name}")
        folder_id = create_folder(folder_name)
        print(f"[DEBUG] Pasta criada com ID: {folder_id}")
        
        # Upload de cada arquivo
        upload_links = []
        for idx, file in enumerate(files):
            if file and file.filename:
                print(f"[DEBUG] Fazendo upload do arquivo {idx + 1}: {file.filename}")
                result = upload_file_to_drive(file, file.filename, folder_id)
                file_id = result['id']
                upload_links.append({
                    'name': result['name'],
                    'link': result['webViewLink'],
                    'download': f"https://drive.google.com/uc?export=download&id={file_id}",
                    'drive_id': file_id
                })
                print(f"[DEBUG] Arquivo {idx + 1} upado com sucesso")
        
        print(f"[DEBUG] Total de arquivos upados: {len(upload_links)}")
        return upload_links
    
    except Exception as e:
        print(f"[ERRO] Erro ao fazer upload para Google Drive: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def get_file_link(file_id):
    """
    Retorna o link compartilhável de um arquivo
    
    Args:
        file_id: ID do arquivo no Google Drive
    
    Returns:
        Link do arquivo
    """
    return f"https://drive.google.com/file/d/{file_id}/view"


def test_connection():
    """
    Testa a conexão com o Google Drive
    
    Returns:
        True se conectado, False se falhou
    """
    try:
        service = get_drive_service()
        
        # Testar listando arquivos da pasta raiz
        results = service.files().list(
            q=f"'{ROOT_FOLDER_ID}' in parents",
            spaces='drive',
            fields='files(id, name)',
            pageSize=5
        ).execute()
        
        files = results.get('files', [])
        print(f"✅ Conexão com Google Drive OK!")
        print(f"📁 Pasta raiz: {ROOT_FOLDER_ID}")
        print(f"📄 Arquivos encontrados: {len(files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
