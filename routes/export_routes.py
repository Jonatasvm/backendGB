from flask import Blueprint, request, send_file, jsonify
import xlsxwriter
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

    # Criar arquivo Excel em memória com XlsxWriter
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Planilha de Importação")

    # Definir cabeçalhos
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

    # Formatos SEM problemas de caracteres especiais
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    text_format = workbook.add_format({
        'border': 1,
        'align': 'left'
    })
    
    # ✅ NOVO: Formato para data (previne problemas de CSV)
    date_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'num_format': 'yyyy-mm-dd'
    })

    # Adicionar cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Adicionar dados
    row_num = 1
    for registro in registros:
        # ID vem como número do frontend
        id_final = int(registro.get('id', 0)) if registro.get('id') else 0

        # Data vem como string ISO (YYYY-MM-DD) do frontend
        data_pagamento_raw = registro.get('dataPagamento', '')
        data_pagamento_final = None
        if data_pagamento_raw:
            try:
                from datetime import datetime as dt
                data_obj = dt.strptime(data_pagamento_raw, '%Y-%m-%d')
                data_pagamento_final = data_obj + timedelta(days=1)
            except Exception:
                data_pagamento_final = None

        # Valor vem em centavos como número inteiro do frontend
        valor_raw = registro.get('valor', 0)
        try:
            # Se valor_raw for 0 ou None, usa 0.0
            if not valor_raw:
                valor_final = 0.0
            else:
                valor_num = float(valor_raw)
                valor_final = valor_num / 100  # Divide por 100 para converter centavos para reais
        except Exception:
            valor_final = 0.0

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

        # Status lançamento
        status = "Lançado" if registro.get('lancado') == 'Y' else "Pendente"

        # Escrever dados na linha - USANDO write_string PARA EVITAR PROBLEMAS DE CSV
        worksheet.write_string(row_num, 0, str(id_final).strip() if id_final else '')  # ID - como texto puro
        # Data: se houver, escreve como datetime; se não, deixa em branco
        if data_pagamento_final:
            worksheet.write_datetime(row_num, 1, data_pagamento_final, date_format)  # Data com formato seguro
        else:
            worksheet.write_blank(row_num, 1, '', text_format)  # Data vazia com formato
        # Valor formatado como texto para evitar ' e manter 2 casas decimais
        valor_formatado = f"{valor_final:.2f}".replace('.', ',')
        worksheet.write_string(row_num, 2, valor_formatado.strip())  # Valor - texto formatado
        worksheet.write_string(row_num, 3, str(forma_pagamento_normalizada).strip())  # Forma de Pagamento
        worksheet.write_string(row_num, 4, str(quem_paga_normalizado).strip())  # Quem Paga
        worksheet.write_string(row_num, 5, str(obra_normalizada).strip())  # Centro de Custo
        worksheet.write_string(row_num, 6, str(registro.get('titular', '')).strip())  # Titular
        worksheet.write_string(row_num, 7, str(registro.get('cpfCnpjTitularConta', '')).strip())  # CPF/CNPJ
        worksheet.write_string(row_num, 8, str(registro.get('chavePix', '')).strip())  # Chave Pix
        worksheet.write_string(row_num, 9, str(registro.get('obra', '')).strip())  # Obra
        worksheet.write_string(row_num, 10, str(categoria_nome).strip())  # Categoria
        worksheet.write_string(row_num, 11, str(status).strip())  # Status Lançamento
        worksheet.write_string(row_num, 12, str(registro.get('observacao', '')).strip())  # Observação

        row_num += 1

    # Ajustar largura das colunas
    worksheet.set_column(0, 0, 10)   # ID
    worksheet.set_column(1, 1, 15)   # Data Pagamento
    worksheet.set_column(2, 2, 12)   # Valor
    worksheet.set_column(3, 3, 18)   # Forma de Pagamento
    worksheet.set_column(4, 4, 12)   # Quem Paga
    worksheet.set_column(5, 5, 15)   # Centro de Custo
    worksheet.set_column(6, 6, 20)   # Titular
    worksheet.set_column(7, 7, 15)   # CPF/CNPJ
    worksheet.set_column(8, 8, 15)   # Chave Pix
    worksheet.set_column(9, 9, 15)   # Obra
    worksheet.set_column(10, 10, 18) # Categoria
    worksheet.set_column(11, 11, 18) # Status Lançamento
    worksheet.set_column(12, 12, 25) # Observação

    workbook.close()
    output.seek(0)

    # Enviar arquivo como download
    return send_file(
        output,
        as_attachment=True,
        download_name=f"lancamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            'Content-Disposition': f'attachment; filename="lancamentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )