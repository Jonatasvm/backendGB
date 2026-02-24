from flask import Blueprint, request, send_file, jsonify
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO
from datetime import datetime, timedelta
from db import get_connection

export_bp = Blueprint('export', __name__)

def normalize_forma_pagamento(forma_pagamento):
    """
    Normaliza a forma de pagamento para Título Case.
    PIX -> Pix, BOLETO -> Boleto, CHEQUE -> Cheque
    """
    if not forma_pagamento:
        return ''
    
    # Converter para maiúsculas e remover espaços
    forma_upper = str(forma_pagamento).strip().upper()
    
    if forma_upper == 'PIX':
        return 'Pix'
    elif forma_upper == 'BOLETO':
        return 'Boleto'
    elif forma_upper == 'CHEQUE':
        return 'Cheque'
    else:
        # Se não reconhecer, retornar com primeira letra maiúscula
        return str(forma_pagamento).strip().capitalize() if forma_pagamento else ''

def normalize_text_field(text):
    """
    Normaliza um texto para Título Case (primeira letra maiúscula).
    """
    if not text:
        return ''
    
    text = str(text).strip()
    return text[0].upper() + text[1:].lower() if len(text) > 0 else ''

@export_bp.route('/api/export/xls', methods=['POST'])
def export_xls():
    data = request.get_json()
    registros = data.get('registros', [])

    if not registros:
        return jsonify({'error': 'Nenhum registro selecionado'}), 400

    # Criar workbook e worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Planilha de Importação"

    # Definir cabeçalhos (baseado nos campos do seu formulário)
    headers = [
        'ID',
        'Data Pagamento',
        'Valor',
        'Forma de Pagamento',
        'Quem Paga',
        'Centro de Custo',
        'Titular',
        'CPF/CNPJ',
        'Chave Pix',
        'Obra',
        'Categoria',
        'Status Lançamento',
        'Observação'
    ]
    ws.append(headers)

    # Estilizar cabeçalho
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Adicionar dados
    for registro in registros:
        # Valor: de centavos para reais, como número (float), sem formatação de string
        valor_raw = registro.get('valor', 0)
        try:
            valor_float = float(valor_raw) / 100 if valor_raw else 0
        except:
            valor_float = 0.0

        # Status lançamento
        status = "Lançado" if registro.get('lancado') == 'Y' else "Pendente"

        # Data Pagamento: corrigida para tipo data, formato dd/mm/yyyy
        data_pagamento_raw = registro.get('dataPagamento', '')
        data_pagamento_corrigida = ''
        data_obj = None
        if data_pagamento_raw:
            try:
                from datetime import datetime as dt
                data_obj = dt.strptime(str(data_pagamento_raw), '%Y-%m-%d')
                data_corrigida = data_obj + timedelta(days=1)
                data_pagamento_corrigida = data_corrigida
            except:
                data_pagamento_corrigida = data_pagamento_raw

        forma_pagamento = registro.get('formaDePagamento', '')
        forma_pagamento_normalizada = normalize_forma_pagamento(forma_pagamento)
        quem_paga_normalizado = 'Empresa'
        obra_raw = registro.get('obra', '')
        obra_normalizada = normalize_text_field(str(obra_raw)) if obra_raw else ''

        categoria_nome = ''
        categoria_raw = registro.get('categoria')
        if categoria_raw:
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT nome FROM categoria WHERE id = %s", (categoria_raw,))
                resultado = cursor.fetchone()
                cursor.close()
                conn.close()
                categoria_nome = resultado['nome'] if resultado else ''
            except:
                categoria_nome = ''

        # Sanitizar campos para remover aspas simples no início
        id_sanit = str(registro.get('id', '')).lstrip("'")
        data_pagamento_sanit = data_pagamento_corrigida
        if isinstance(data_pagamento_sanit, str):
            data_pagamento_sanit = data_pagamento_sanit.lstrip("'")
        # valor_float é float, não precisa sanitizar, mas se vier string, sanitiza
        valor_sanit = valor_float
        if isinstance(valor_sanit, str):
            valor_sanit = valor_sanit.lstrip("'")

        # Garantir que data_pagamento_sanit seja datetime ou string sem aspas
        if isinstance(data_pagamento_corrigida, str):
            data_pagamento_final = data_pagamento_corrigida.lstrip("'")
        elif data_pagamento_corrigida:
            data_pagamento_final = data_pagamento_corrigida
        else:
            data_pagamento_final = ''

        # Garantir que valor seja float e nunca string com aspas
        if isinstance(valor_float, str):
            try:
                valor_final = float(valor_float.lstrip("'"))
            except:
                valor_final = 0.0
        else:
            valor_final = valor_float

        row = [
            id_sanit,
            data_pagamento_final,  # tipo data ou string sem aspas
            valor_final,           # número float, nunca string!
            forma_pagamento_normalizada,
            quem_paga_normalizado,
            obra_normalizada,
            registro.get('titular', ''),
            registro.get('cpfCnpjTitularConta', ''),
            registro.get('chavePix', ''),
            registro.get('obra', ''),
            categoria_nome,
            status,
            registro.get('observacao', '')
        ]
        ws.append(row)

    # Formatar coluna de valor como número com ponto decimal (compatível com LibreOffice)
    for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
        for cell in row:
            cell.number_format = '0.00'
            cell.alignment = Alignment(horizontal='right')

    # Formatar coluna de data como data completa (dd/mm/yyyy)
    for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
        for cell in row:
            cell.number_format = 'dd/mm/yyyy'

    # Salvar arquivo em memória
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Enviar arquivo como download
    return send_file(
        output,
        as_attachment=True,
        download_name=f"lancamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )