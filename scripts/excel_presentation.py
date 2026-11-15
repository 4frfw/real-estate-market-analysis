from openpyxl.chart import LineChart, Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.styles import Alignment, Font


def enhance(wb, data, summary):
    for name in ('Charts', 'Conclusions', 'Guide'):
        if name in wb:
            del wb[name]
    sheet = wb['Data']
    columns = {cell.value: cell.column for cell in sheet[1]}
    charts = wb.create_sheet('Charts')
    specs = [
        ('Средние цены', 'тыс. руб./м²', ['primary', 'secondary']),
        ('Прирост индексов и инфляция', '% за год', ['primary_index_growth', 'secondary_index_growth', 'inflation']),
        ('Реальный прирост индексов', '% за год', ['primary_real_growth', 'secondary_real_growth']),
        ('Макрофакторы: декабрь', '%', ['inflation', 'key_rate']),
    ]
    for index, (title, unit, fields) in enumerate(specs):
        chart = LineChart()
        chart.title, chart.y_axis.title, chart.x_axis.title = title, unit, 'Год'
        chart.height, chart.width = 8, 25
        chart.legend.position = 'b'
        for field in fields:
            chart.add_data(Reference(sheet, min_col=columns[field], min_row=1, max_row=len(data)+1), titles_from_data=True)
            label = 'Инфляция' if field == 'inflation' else 'Ключевая ставка' if field == 'key_rate' else 'Первичный рынок' if field.startswith('primary') else 'Вторичный рынок'
            chart.series[-1].tx = SeriesLabel(v=label)
        chart.set_categories(Reference(sheet, min_col=columns['year'], min_row=2, max_row=len(data)+1))
        charts.add_chart(chart, f'A{1+index*17}')
    notes = wb.create_sheet('Conclusions')
    rows = [
        ['Показатель', 'Значение', 'Единица / пояснение'],
        ['Период', f'{int(data.year.iloc[0])}–{int(data.year.iloc[-1])}', f'{len(data)} наблюдений'],
        ['Изменение средней цены: первичный рынок', summary['primary_growth'], '% за весь период'],
        ['Изменение средней цены: вторичный рынок', summary['secondary_growth'], '% за весь период'],
        ['Разрыв средних цен в последнем году', summary['premium'], '% к вторичному рынку'],
        ['Реальный прирост индекса: первичный рынок, последний год', summary['real_primary'], '% за год'],
        ['Реальный прирост индекса: вторичный рынок, последний год', summary['real_secondary'], '% за год'],
        ['Ограничения', 'Средняя цена и индекс — разные показатели.', f'Корреляции по {len(data)} годам не доказывают причинность.'],
    ]
    for row in rows:
        notes.append(row)
    for row in range(3, 8):
        notes.cell(row, 2).number_format = '0.00'
    guide = wb.create_sheet('Guide')
    for row in [
        ['Раздел', 'Пояснение'],
        ['Data', 'Цены: тыс. руб./м² на конец года; инфляция и ключевая ставка: декабрь, %.'],
        ['Индексы', '100 означает отсутствие изменения. Прирост индекса = индекс − 100.'],
        ['Реальный прирост', '(индекс / (100 + инфляция) − 1) × 100%.'],
        ['Формат процентов', 'Значение 8.8 означает 8.8%; процентный формат Excel не применять.'],
        ['deflator', 'Коэффициент накопленной инфляции; первый год = 1.'],
        ['Correlations', 'r: Пирсон; loo_min/max: исключение одного года. Корреляция не доказывает причинность.'],
        ['Statistics', 'count: число значений; std: выборочное стандартное отклонение.'],
        ['Scenarios', 'rate: % годовых; loan: руб.; months: месяцы; payment: руб./месяц. Не предложения банков.'],
        ['Formulas', 'Формулы пересчитываются при открытии. Data и Conclusions содержат готовые значения.'],
        ['Источники', 'data/sources.md. Жилищный ряд не включает Крым и Севастополь.'],
        ['Обновление', 'Изменить CSV в data/raw и запустить python scripts/analyze.py.'],
    ]:
        guide.append(row)
    for page in (notes, guide):
        page.freeze_panes = 'A2'
        for cell in page[1]:
            cell.font = Font(bold=True, color='17324D')
        for row in page.iter_rows(min_row=2):
            page.row_dimensions[row[0].row].height = 48
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
        for column in ('A', 'B', 'C'):
            page.column_dimensions[column].width = 65
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
