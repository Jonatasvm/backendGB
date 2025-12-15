"""
Serviço para integração com Google Drive
Realiza upload de arquivos e cria pastas
Usa OAuth 2.0 (autenticação do usuário) ao invés de Service Account
"""

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Caminhos dos arquivos de credenciais
BASE_DIR = os.path.dirname(__file__)
CREDENTIALS_FILE = os.path.join(BASE_DIR, '..', 'credencials.json')  # OAuth client secrets
TOKEN_FILE = os.path.join(BASE_DIR, '..', 'token.json')              # Token do usuário autenticado

SCOPES = ['https://www.googleapis.com/auth/drive']

# ID da pasta raiz onde salvar os lançamentos
# https://drive.google.com/drive/folders/123C6ItHLqoRnb_hNNHRwE7FczSh9yhun
ROOT_FOLDER_ID = "123C6ItHLqoRnb_hNNHRwE7FczSh9yhun"


def get_credentials():
    """
    Obtém credenciais OAuth do usuário.
    Se não existir token ou estiver expirado, abre o navegador para login.
    """
    creds = None

    # Verifica se já existe um token salvo
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Se não há credenciais válidas, faz o fluxo de autenticação
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Salva o token para próximas execuções
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


def get_drive_service():
    """Retorna um cliente autenticado do Google Drive usando OAuth"""
    credentials = get_credentials()
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
