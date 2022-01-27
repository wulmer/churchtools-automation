import datetime
import os

import dateparser

from gottesdienstplan import GoogleSheet, Gottesdienstplan

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]


if __name__ == "__main__":
    plan = Gottesdienstplan()
    archive = GoogleSheet(SPREADSHEET_ID, "Archiv")
    rows_to_delete = []
    starting_row = 3
    now = datetime.datetime.today()
    yesterday = now - datetime.timedelta(days=1)
    for index, row in enumerate(plan.iter_rows(starting_row=starting_row)):
        try:
            date = dateparser.parse(row[0])
        except ValueError:
            print(f"Could not parse date value in row {starting_row+index}")
            raise

        if date >= yesterday:
            break

        if archive.insert_row(row, before_row=2):
            rows_to_delete.append(starting_row + index)

    if len(rows_to_delete) > 1:
        raise RuntimeError(
            "Not going to delete more than one row in automatic"
            "mode. Run this script manually to perform this operation!"
        )

    for row_index in rows_to_delete[::-1]:
        print(f"Deleting row {row_index} with values:")
        print(plan._sheet.get_rows_values(n_rows=1, skip_rows=row_index - 1))
        plan._sheet.delete_row(row_index)
