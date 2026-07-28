from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


def export_to_excel(applications):

    file_name = "заявки.xlsx"

    wb = Workbook()
    sheet = wb.active

    sheet.title = "Заявки"

    headers = [
        "ID",
        "Дата",
        "Имя",
        "Телефон",
        "Услуга",
        "Задача",
        "Статус"
    ]

    sheet.append(headers)

    # Заголовки
    for cell in sheet[1]:

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # Данные
    for application in applications:

        sheet.append(application)

    # Ширина колонок
    widths = {
        1: 8,
        2: 20,
        3: 20,
        4: 18,
        5: 25,
        6: 50,
        7: 15
    }

    for column, width in widths.items():

        sheet.column_dimensions[
            get_column_letter(column)
        ].width = width

    # Перенос текста
    for row in sheet.iter_rows():

        for cell in row:

            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )

    wb.save(file_name)

    return file_name