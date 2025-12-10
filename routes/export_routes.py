from flask import Blueprint, request, send_file, jsonify
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO
from datetime import datetime

export_bp = Blueprint('export', __name__)

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
        ws.title = "Pagamentos"

        # Definir cabeçalhos (baseado nos campos do seu formulário)
        headers = [
            'ID',
            'Data Pagamento',
            'Valor',
            'Forma de Pagamento',
            'Titular',
            'CPF/CNPJ',
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
            # Formatar valor (centavos para reais)
            valor_raw = registro.get('valor', 0)
            try:
                valor_formatado = float(valor_raw) / 100 if valor_raw else 0
            except:
                valor_formatado = 0

            # Status lançamento
            status = "Lançado" if registro.get('statusLancamento') else "Pendente"

            row = [
                registro.get('id', ''),
                registro.get('dataPagamento', ''),
                valor_formatado,
                registro.get('formaDePagamento', ''),
                registro.get('titular', ''),
                registro.get('cpfCnpjTitularConta', ''),
                registro.get('obra', ''),
                status,
                registro.get('observacao', '')
            ]
            ws.append(row)

        # Formatar coluna de valor como moeda
        for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
            for cell in row:
                cell.number_format = 'R$ #,##0.00'

        # Ajustar largura das colunas
        column_widths = [8, 15, 15, 20, 30, 20, 25, 15, 40]
        for i, width in enumerate(column_widths, 1):
            col_letter = chr(64 + i) if i <= 26 else 'A' + chr(64 + i - 26)
            ws.column_dimensions[col_letter].width = width

        # Adicionar bordas em todas as células com dados
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.border = thin_border

        # Salvar em memória
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Gerar nome do arquivo com data
        filename = f"pagamentos_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Erro ao gerar XLS: {e}")
        return jsonify({'error': f'Erro ao gerar arquivo: {str(e)}'}), 500