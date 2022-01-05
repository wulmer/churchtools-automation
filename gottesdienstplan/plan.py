import datetime
import os
from itertools import zip_longest

import dateparser
from nextcloud import NextCloud

from .auth import spreadsheet_service

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
NEXTCLOUD_USER = os.environ["NEXTCLOUD_USER"]
NEXTCLOUD_TOKEN = os.environ["NEXTCLOUD_TOKEN"]


class GoogleSheet:
    def __init__(self, sheet_id, table_name, last_column="P"):
        self._sheets = spreadsheet_service.spreadsheets()
        self._values = self._sheets.values()
        self._sheetid = sheet_id
        self._table_name = table_name
        self._last_column = last_column

    def get(self):
        return self._sheets.get(spreadsheetId=self._sheetid).execute()

    def get_rows_values(self, n_rows=30, skip_rows=0):
        row_range = (
            f"{self._table_name}!A{skip_rows+1}:{self._last_column}{skip_rows+n_rows}"
        )
        return self._values.get(
            spreadsheetId=self._sheetid,
            range=row_range,
            dateTimeRenderOption="FORMATTED_STRING",
            valueRenderOption="FORMATTED_VALUE",
        ).execute()["values"]


class Gottesdienstplan:
    def __init__(self):
        self._sheet = GoogleSheet(SPREADSHEET_ID, "Gottesdienstplan")
        self._headers = None

    def get_headers(self):
        if self._headers is None:
            self._headers = self._sheet.get_rows_values(1, skip_rows=1)[0]
        return self._headers

    def iter_rows(self, starting_row=3):
        i = starting_row - 1
        while True:
            yield self._sheet.get_rows_values(1, skip_rows=i)[0]
            i = i + 1

    def iter_row_data(self, starting_row=3):
        headers = self.get_headers()
        for values in self.iter_rows(starting_row=starting_row):
            try:
                date = dateparser.parse(values[0])
                values[0] = date
            except ValueError:
                pass
            yield dict(zip_longest(headers, values, fillvalue=None))

    def iter_future_events(self):
        """Get the next rows/events that lie in the future."""
        in_future = False
        for row_data in self.iter_row_data(starting_row=3):
            if in_future:
                yield row_data
            else:
                if row_data["Datum"] > datetime.datetime.now():
                    in_future = True
                    yield row_data

    def iter_next_future_events(self, *, num: int = None, span: str = None):
        if num is not None:
            remaining = num
            for row_data in self.iter_future_events():
                yield row_data
                remaining -= 1
                if remaining == 0:
                    break
        elif span is not None:
            now = datetime.datetime.now()
            if span.endswith("d"):
                range_end = now + datetime.timedelta(days=int(span[:-1]))
            elif span.endswith("w"):
                range_end = now + datetime.timedelta(weeks=int(span[:-1]))
            for row_data in self.iter_future_events():
                if row_data["Datum"] > range_end:
                    break
                yield row_data

        else:
            raise TypeError("Missing argument: either `num` or `span` must be given!")


class GoDiPlanChecker:
    def __init__(self, mail_domain: str = None):
        self._plan = Gottesdienstplan()
        self._mail_domain = mail_domain

    def check(self, span="1w", report=None):
        for event in self._plan.iter_next_future_events(span=span):
            self.check_basics(event, reporter=report)
            self.check_liturg_opfer(event, report=report)
            self.check_technik_ton_kirche(event, report=report)
            self.check_for_nextcloud_folder_and_ablauf(event, report=report)

    def check_basics(self, event, reporter=None):
        if (
            not event["Uhrzeit"]
            or not event["Art/Anlass/Thema"]
            or not event["Prediger"]
        ):
            if reporter is None:
                reporter = print
            reporter(
                {
                    "message": (
                        f"Basisdaten (Uhrzeit, Anlass, Prediger) fehlen am "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]}'
                    ),
                    "recipient": f"webmaster@{self._mail_domain}",
                }
            )

    def check_liturg_opfer(self, event, report=None):
        if not event["Liturg+Opfer"]:
            if report is None:
                report = print
            report(
                {
                    "message": (
                        "Kein KGR eingetragen am "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]} für Liturgendienst und Opfer zählen!'
                    ),
                    "recipient": f"kgr@{self._mail_domain}",
                }
            )

    def check_technik_ton_kirche(self, event, report=None):
        if not event["Ton Kirche"]:
            if report is None:
                report = print
            report(
                {
                    "message": (
                        "Kein Tontechniker am "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]}'
                    ),
                    "recipient": f"technik@{self._mail_domain}",
                }
            )

    def check_for_nextcloud_folder_and_ablauf(self, event, report=None):
        if report is None:
            report = print
        nc = NextCloud(
            webdav_url="https://nc-7380861684881042724.nextcloud-ionos.com/remote.php/dav/files/wulmer/",
            webdav_auth=(NEXTCLOUD_USER, NEXTCLOUD_TOKEN),
        )
        base_folder = "Gottesdienste/"
        event_datum = event["Datum"].strftime("%Y-%m-%d")
        existing_folders = nc.ls(base_folder, detail=True)
        for folder in existing_folders:
            if folder["type"] == "directory" and folder["name"].startswith(
                f"{base_folder}{event_datum}"
            ):
                for file in nc.ls(folder["name"], detail=True):
                    if "ablauf" in file["name"].lower():
                        break
                else:
                    report(
                        {
                            "message": (
                                "Es ist noch kein Ablauf auf NextCloud für den "
                                "Gottesdienst am "
                                f"{event['Datum'].strftime('%a., %d. %b')} abgelegt. "
                                f"Bitte im Verzeichnis '{base_folder}{event_datum}' "
                                "eine Datei mit 'Ablauf' im Dateinamen ablegen! "
                                "Eingetragen für Predigt ist: {event['Prediger']}"
                            ),
                            "recipient": f"webmaster@{self._mail_domain}",
                        }
                    )

        else:
            report(
                {
                    "message": (
                        "Es ist noch kein Verzeichnis auf NextCloud für den "
                        "Gottesdienst am "
                        f"{event['Datum'].strftime('%a., %d. %b')} angelegt. "
                        f"Bitte ein Verzeichnis '{base_folder}{event_datum}' anlegen "
                        "und den Ablauf dort ablegen!"
                    ),
                    "recipient": f"webmaster@{self._mail_domain}",
                }
            )
