"""
backup_database.py
==================
Faz dump do MySQL, compacta em .gz e envia para a pasta de backup no Google Drive.
Após o upload, apaga backups com mais de 10 dias na mesma pasta do Drive.

Uso manual:
    python backup_database.py

Agendado (via backup_scheduler.py ou Windows Task Scheduler):
    python backup_database.py
"""

import os
import sys
import gzip
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta

# Adiciona o diretório do projeto ao path para poder importar config e services
sys.path.insert(0, os.path.dirname(__file__))

from config import DB_CONFIG
from services.google_drive_service import get_drive_service

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────
BACKUP_FOLDER_ID = "1Xf-QyBJI1hkrvjGlHtuuXinTudOR-e7i"   # Pasta criada pelo usuário
RETENTION_DAYS   = 10                                       # Dias para manter backups
MYSQLDUMP_PATH   = "mysqldump"                              # Ajuste se não estiver no PATH


def run_dump(dump_path: str) -> None:
    """Executa mysqldump e salva o .sql no caminho indicado."""
    cmd = [
        MYSQLDUMP_PATH,
        "--host",     DB_CONFIG["host"],
        "--user",     DB_CONFIG["user"],
        f"--password={DB_CONFIG['password']}",
        "--single-transaction",
        "--routines",
        "--triggers",
        DB_CONFIG["database"],
    ]
    with open(dump_path, "wb") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise RuntimeError(
            f"mysqldump falhou (código {result.returncode}):\n"
            + result.stderr.decode("utf-8", errors="replace")
        )


def compress_file(src_path: str, gz_path: str) -> None:
    """Compacta src_path → gz_path com gzip."""
    with open(src_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


def upload_to_drive(service, gz_path: str, filename: str) -> str:
    """Faz upload do arquivo compactado para a pasta de backup no Drive."""
    from googleapiclient.http import MediaFileUpload

    file_metadata = {
        "name": filename,
        "parents": [BACKUP_FOLDER_ID],
    }
    media = MediaFileUpload(gz_path, mimetype="application/gzip", resumable=True)
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, size",
    ).execute()
    return uploaded.get("id")


def delete_old_backups(service) -> int:
    """
    Lista arquivos na pasta de backup e exclui os que têm mais de RETENTION_DAYS dias.
    Retorna o número de arquivos excluídos.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    deleted = 0

    page_token = None
    while True:
        resp = service.files().list(
            q=f"'{BACKUP_FOLDER_ID}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, createdTime)",
            pageToken=page_token,
        ).execute()

        for f in resp.get("files", []):
            created = datetime.fromisoformat(f["createdTime"].replace("Z", "+00:00"))
            if created < cutoff:
                service.files().delete(fileId=f["id"]).execute()
                print(f"  🗑  Backup antigo removido: {f['name']} (criado em {created.strftime('%d/%m/%Y')})")
                deleted += 1

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return deleted


def main() -> None:
    now       = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename  = f"backup_{DB_CONFIG['database']}_{timestamp}.sql.gz"

    print(f"\n{'='*60}")
    print(f"  BACKUP - {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}")

    # Diretório temporário para o dump
    with tempfile.TemporaryDirectory() as tmpdir:
        sql_path = os.path.join(tmpdir, "dump.sql")
        gz_path  = os.path.join(tmpdir, filename)

        # 1. Dump
        print(f"\n[1/3] Executando mysqldump...")
        run_dump(sql_path)
        sql_size = os.path.getsize(sql_path)
        print(f"      Dump gerado: {sql_size / 1024:.1f} KB")

        # 2. Compactar
        print(f"[2/3] Compactando...")
        compress_file(sql_path, gz_path)
        gz_size = os.path.getsize(gz_path)
        print(f"      Arquivo final: {filename} ({gz_size / 1024:.1f} KB)")

        # 3. Upload
        print(f"[3/3] Enviando para o Google Drive...")
        service   = get_drive_service()
        file_id   = upload_to_drive(service, gz_path, filename)
        print(f"      ✅ Upload concluído! ID: {file_id}")

    # 4. Limpar backups antigos
    print(f"\n[+]  Removendo backups com mais de {RETENTION_DAYS} dias...")
    deleted = delete_old_backups(service)
    if deleted == 0:
        print("      Nenhum backup antigo encontrado.")

    print(f"\n{'='*60}")
    print(f"  BACKUP FINALIZADO COM SUCESSO")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO no backup: {e}", file=sys.stderr)
        sys.exit(1)
