from flask import Blueprint, request, send_file, jsonify
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO
from datetime import datetime, timedelta

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
    try:
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
            # Formatar valor (centavos para reais) - SEM símbolo de moeda
            valor_raw = registro.get('valor', 0)
            try:
                valor_formatado = float(valor_raw) / 100 if valor_raw else 0
            except:
                valor_formatado = 0

            # Status lançamento
            status = "Lançado" if registro.get('lancado') == 'Y' else "Pendente"

            # ✅ CORREÇÃO DE DATA: Adicionar 1 dia para compensar diferença
            data_pagamento_raw = registro.get('dataPagamento', '')
            data_pagamento_corrigida = ''
            if data_pagamento_raw:
                try:
                    from datetime import datetime as dt
                    data_obj = dt.strptime(str(data_pagamento_raw), '%Y-%m-%d')
                    data_corrigida = data_obj + timedelta(days=1)
                    data_pagamento_corrigida = data_corrigida.strftime('%Y-%m-%d')
                except:
                    data_pagamento_corrigida = data_pagamento_raw

            # ✅ NORMALIZAÇÃO: Forma de Pagamento (Boleto, Pix, Cheque - com primeira letra maiúscula)
            forma_pagamento = registro.get('formaDePagamento', '')
            forma_pagamento_normalizada = normalize_forma_pagamento(forma_pagamento)
            
            # ✅ NORMALIZAÇÃO: Quem Paga - "Empresa" (com E maiúsculo)
            quem_paga_normalizado = 'Empresa'
            
            # ✅ NORMALIZAÇÃO: Centro de Custo (Obra) - primeira letra maiúscula
            obra_raw = registro.get('obra', '')
            obra_normalizada = normalize_text_field(str(obra_raw)) if obra_raw else ''

            row = [
                registro.get('id', ''),
                data_pagamento_corrigida,
                valor_formatado,
                forma_pagamento_normalizada,
                quem_paga_normalizado,
                obra_normalizada,
                registro.get('titular', ''),
                registro.get('cpfCnpjTitularConta', ''),
                registro.get('chavePix', ''),
                registro.get('obra', ''),
                status,
                registro.get('observacao', '')
            ]
            ws.append(row)

        # Formatar coluna de valor - sem símbolo de moeda, apenas número puro
        for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
            for cell in row:
                cell.number_format = '0.00'  # Apenas número, nenhum símbolo de moeda

        # Ajustar largura das colunas
        column_widths = [8, 15, 15, 20, 15, 18, 30, 20, 20, 25, 15, 40]
        for i, width in enumerate(column_widths, 1):
            col_letter = chr(64 + i) if i <= 26 else 'A' + chr(64 + i - 26)
            ws.column_dimensions[col_letter].width = width

        # Adicionar bordas em todas as células com dados
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.border = thin_border

        # Salvar em memóriaa
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Gerar nome do arquivo com data
        filename = f"Planilha de Importação_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Erro ao gerar XLS: {e}")
        return jsonify({'error': f'Erro ao gerar arquivo: {str(e)}'}), 500