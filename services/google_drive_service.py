"""
Serviço para integração com Google Drive
✅ ATUALIZADO: Usa OAuth 2.0 (autenticação do usuário)

O token.json deve estar na pasta para funcionar!
Execute gerar_token.py uma única vez para gerar o token.
"""

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json

# ✅ CONFIGURAÇÕES
TOKEN_FILE = 'token.json'
FOLDER_ID = "1dq7j5MgtyXToCTnQ3F6WeSRhRLuH1W7K"

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_credentials():
    """Carrega credenciais do arquivo token.json"""
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(
            f"❌ Arquivo {TOKEN_FILE} não encontrado!\n"
            f"Execute: python gerar_token.py"
        )
    
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Refresh se expirado
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return creds


def get_drive_service():
    """Retorna cliente do Google Drive autenticado com OAuth"""
    credentials = get_credentials()
    return build('drive', 'v3', credentials=credentials)


def create_folder(folder_name, parent_id=FOLDER_ID):
    """
    Cria uma pasta no Google Drive
    
    Args:
        folder_name: Nome da pasta
        parent_id: ID da pasta pai
    
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
    Faz upload de um arquivo para Google Drive
    
    Args:
        file_obj: Objeto de arquivo (FileStorage do Flask)
        filename: Nome do arquivo
        folder_id: ID da pasta destino
    
    Returns:
        Dict com 'id', 'webViewLink' e 'name'
    """
    service = get_drive_service()
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    # Detectar MIME type
    import mimetypes
    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype is None:
        mimetype = 'application/octet-stream'
    
    # Upload com MediaIoBaseUpload para arquivos do Flask
    media = MediaIoBaseUpload(
        file_obj.stream,
        mimetype=mimetype,
        resumable=True,
        chunksize=1024 * 1024
    )
    
    file_obj_drive = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    file_id = file_obj_drive.get('id')
    
    # Tornar público
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
        print(f"[AVISO] Não foi possível tornar público: {e}")
    
    return {
        'id': file_id,
        'webViewLink': file_obj_drive.get('webViewLink'),
        'name': filename
    }


def upload_files_batch(files, form_id, obra_id):
    """
    Realiza upload de múltiplos arquivos para Google Drive
    
    Args:
        files: Lista de objetos FileStorage
        form_id: ID do formulário
        obra_id: ID da obra
    
    Returns:
        Lista de dicts com links dos arquivos
    """
    try:
        # Criar pasta para o lançamento
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
        print(f"[ERRO] Erro ao fazer upload: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def test_connection():
    """Testa a conexão com Google Drive"""
    try:
        service = get_drive_service()
        
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            spaces='drive',
            fields='files(id, name)',
            pageSize=5
        ).execute()
        
        files = results.get('files', [])
        print(f"✅ Conexão com Google Drive OK!")
        print(f"📁 Pasta raiz: {FOLDER_ID}")
        print(f"📄 Arquivos encontrados: {len(files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
