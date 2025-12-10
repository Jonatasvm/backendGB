"""
Serviço para integração com Google Drive
Realiza upload de arquivos e cria pastas
"""

import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from io import BytesIO

# Credenciais do Google
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
SCOPES = ['https://www.googleapis.com/auth/drive']

# ID da pasta raiz onde salvar os lançamentos
# https://drive.google.com/drive/folders/1bVQSFBReGXSQsWxSZL_ImUWL62ZRt2nn
ROOT_FOLDER_ID = "1bVQSFBReGXSQsWxSZL_ImUWL62ZRt2nn"

def get_drive_service():
    """Retorna um cliente autenticado do Google Drive"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, 
        scopes=SCOPES
    )
    return build('drive', 'v3', credentials=credentials)


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
        file_obj: Objeto de arquivo (BytesIO ou file-like object)
        filename: Nome do arquivo
        folder_id: ID da pasta destino
    
    Returns:
        Dict com 'id' e 'webViewLink' do arquivo
    """
    service = get_drive_service()
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(
        file_obj.filename if hasattr(file_obj, 'filename') else None,
        resumable=True,
        chunksize=1024 * 1024  # 1MB chunks
    )
    
    # Se não temos filename direto, criamos a media de forma diferente
    if isinstance(file_obj, BytesIO) or not hasattr(file_obj, 'filename'):
        # Para uploads de BytesIO
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(file_obj, mimetype='application/octet-stream', resumable=True)
    
    file_obj_drive = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    return {
        'id': file_obj_drive.get('id'),
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
        folder_id = create_folder(folder_name)
        
        # Upload de cada arquivo
        upload_links = []
        for file in files:
            if file and file.filename:
                result = upload_file_to_drive(file, file.filename, folder_id)
                upload_links.append({
                    'name': result['name'],
                    'link': result['webViewLink'],
                    'drive_id': result['id']
                })
        
        return upload_links
    
    except Exception as e:
        print(f"Erro ao fazer upload para Google Drive: {e}")
        raise


def get_file_link(file_id):
    """
    Retorna o link compartilhável de um arquivo
    
    Args:
        file_id: ID do arquivo no Google Drive
    
    Returns:
        URL de visualização do arquivo
    """
    service = get_drive_service()
    
    file = service.files().get(
        fileId=file_id,
        fields='webViewLink'
    ).execute()
    
    return file.get('webViewLink')


def share_file_with_user(file_id, user_email):
    """
    Compartilha um arquivo com um usuário específico
    
    Args:
        file_id: ID do arquivo no Google Drive
        user_email: Email do usuário para compartilhar
    """
    service = get_drive_service()
    
    permission = {
        'type': 'user',
        'role': 'reader',
        'emailAddress': user_email
    }
    
    service.permissions().create(
        fileId=file_id,
        body=permission,
        fields='id'
    ).execute()
