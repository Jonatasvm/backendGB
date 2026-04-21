"""
backup_scheduler.py
===================
Mantém o processo rodando e dispara o backup todo dia às 23:00.

Uso:
    python backup_scheduler.py

Para rodar em segundo plano no Windows (recomendado com PM2):
    pm2 start backup_scheduler.py --interpreter python --name backup-db

Ou via Windows Task Scheduler apontando direto para backup_database.py (sem este arquivo).
"""

import time
import subprocess
import sys
import os
from datetime import datetime

BACKUP_HOUR   = 23   # 23:00
BACKUP_MINUTE = 0
SCRIPT        = os.path.join(os.path.dirname(__file__), "backup_database.py")


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {msg}", flush=True)


def run_backup() -> None:
    log("🔄 Iniciando backup automático...")
    result = subprocess.run(
        [sys.executable, SCRIPT],
        capture_output=False,   # deixa stdout/stderr fluir para o terminal/PM2
    )
    if result.returncode == 0:
        log("✅ Backup concluído com sucesso.")
    else:
        log(f"❌ Backup terminou com erro (código {result.returncode}).")


def main() -> None:
    log(f"📅 Agendador iniciado — backup todo dia às {BACKUP_HOUR:02d}:{BACKUP_MINUTE:02d}")
    last_run_date = None   # evita rodar duas vezes no mesmo dia

    while True:
        now = datetime.now()
        if (
            now.hour == BACKUP_HOUR
            and now.minute == BACKUP_MINUTE
            and now.date() != last_run_date
        ):
            run_backup()
            last_run_date = now.date()

        time.sleep(30)   # verifica a cada 30 segundos


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("⏹  Agendador encerrado pelo usuário.")
