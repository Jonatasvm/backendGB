# 🚀 Google Drive Integration - OAuth Setup

## ✅ Arquivos Necessários

Para que o Google Drive funcione no servidor, você precisa copiar estes 3 arquivos:

### 1. **token.json**
- Localização local: `C:\Users\Administrador\Documents\GitHub\backendGB\token.json`
- Copiar para servidor: `/home/gerenciaGR/backendGB/token.json`

### 2. **client_secret.json**
- Localização local: `C:\Users\Administrador\Documents\GitHub\backendGB\client_secret.json`
- Copiar para servidor: `/home/gerenciaGR/backendGB/client_secret.json`

### 3. **services/google_drive_service.py**
- Localização local: `C:\Users\Administrador\Documents\GitHub\backendGB\services\google_drive_service.py`
- Copiar para servidor: `/home/gerenciaGR/backendGB/services/google_drive_service.py`

---

## 📋 Como Copiar (SCP)

No PowerShell do seu PC:

```powershell
# Copiar token.json
scp C:\Users\Administrador\Documents\GitHub\backendGB\token.json root@91.98.132.210:/home/gerenciaGR/backendGB/

# Copiar client_secret.json
scp C:\Users\Administrador\Documents\GitHub\backendGB\client_secret.json root@91.98.132.210:/home/gerenciaGR/backendGB/

# Copiar google_drive_service.py
scp C:\Users\Administrador\Documents\GitHub\backendGB\services\google_drive_service.py root@91.98.132.210:/home/gerenciaGR/backendGB/services/
```

---

## 🔄 Após Copiar

No servidor, reinicie o backend:

```bash
ssh root@91.98.132.210
cd /home/gerenciaGR/backendGB
pm2 restart backend-gb
pm2 logs backend-gb
```

---

## ✅ Verificação

Quando você enviar um arquivo no Dashboard, você deve ver nos logs:

```
[INFO] Iniciando upload para formulário ID: XX
[DEBUG] Criando pasta: Lançamento_XX_Obra_XX
[DEBUG] Fazendo upload do arquivo 1: seu_arquivo.pdf
[DEBUG] Arquivo 1 upado com sucesso
```

**NÃO DEVE aparecer erro de API Key!**

---

## 🎯 Configurações Atuais

- **Pasta Google Drive**: `1dq7j5MgtyXToCTnQ3F6WeSRhRLuH1W7K`
- **Método**: OAuth 2.0 (arquivo token.json)
- **Status**: ✅ Pronto para usar
