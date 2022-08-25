import datetime
import os
from itertools import zip_longest
from typing import Generator, List

import dateparser

from nextcloud import NextCloud

from .auth import spreadsheet_service

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
NEXTCLOUD_BASE_URL = os.environ["NEXTCLOUD_BASE_URL"]
NEXTCLOUD_TOKEN = os.environ["NEXTCLOUD_TOKEN"]
NEXTCLOUD_USER = os.environ["NEXTCLOUD_USER"]


class GoogleSheet:
    def __init__(self, spreadsheet_id, table_name, last_column="P"):
        self._sheets = spreadsheet_service.spreadsheets()
        self._values = self._sheets.values()
        self._spreadsheet_id = spreadsheet_id
        self._table_name = table_name
        self._sheet_id = None
        spreadsheet = self._sheets.get(spreadsheetId=self._spreadsheet_id).execute()
        for sheet in spreadsheet["sheets"]:
            if sheet["properties"]["title"] == self._table_name:
                self._sheet_id = sheet["properties"]["sheetId"]
                break
        else:
            raise ValueError(
                f"Could not get sheet id of '{table_name}. Is the name correct?"
            )
        self._last_column = last_column

    def get(self):
        return self._sheets.get(spreadsheetId=self._spreadsheet_id).execute()

    def get_rows_values(self, n_rows=30, skip_rows=0):
        row_range = (
            f"{self._table_name}!A{skip_rows+1}:{self._last_column}{skip_rows+n_rows}"
        )
        return self._values.get(
            spreadsheetId=self._spreadsheet_id,
            range=row_range,
            dateTimeRenderOption="FORMATTED_STRING",
            valueRenderOption="FORMATTED_VALUE",
        ).execute()["values"]

    def insert_row(self, row, before_row: int = 1):
        result = self._sheets.batchUpdate(
            spreadsheetId=self._spreadsheet_id,
            body={
                "requests": [
                    {
                        "insertDimension": {
                            "range": {
                                "sheetId": self._sheet_id,
                                "dimension": "ROWS",
                                "startIndex": before_row - 1,
                                "endIndex": before_row,
                            }
                        }
                    }
                ]
            },
        ).execute()
        result = self._values.append(
            spreadsheetId=self._spreadsheet_id,
            range=self._table_name + "!A" + str(before_row),
            valueInputOption="USER_ENTERED",
            body={"values": [row]},
        ).execute()
        return result.get("updates").get("updatedRows") == 1

    def delete_row(self, row_index: int):
        self._sheets.batchUpdate(
            spreadsheetId=self._spreadsheet_id,
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": self._sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_index - 1,
                                "endIndex": row_index,
                            }
                        }
                    }
                ]
            },
        ).execute()


class Gottesdienstplan:
    def __init__(self):
        self._sheet = GoogleSheet(SPREADSHEET_ID, "Gottesdienstplan")
        self._headers = None

    def get_headers(self):
        if self._headers is None:
            self._headers = [
                h.strip() for h in self._sheet.get_rows_values(1, skip_rows=1)[0]
            ]
        return self._headers

    def iter_rows(self, starting_row=3) -> Generator[List[str], None, None]:
        assert starting_row >= 1
        i = starting_row - 1
        while True:
            yield self._sheet.get_rows_values(1, skip_rows=i)[0]
            i = i + 1

    def iter_row_data(self, starting_row=3):
        headers = self.get_headers()
        for values in self.iter_rows(starting_row=starting_row):
            try:
                date = dateparser.parse(
                    values[0], settings={"TIMEZONE": "CET"}, languages=["de"]
                )
                if date is None:
                    raise ValueError(f"Invalid 'Datum': {values[0]}")
                values[0] = date
            except ValueError:
                raise ValueError(f"Invalid 'Datum': {values[0]}")
            yield dict(zip_longest(headers, values, fillvalue=None))

    def iter_future_events(self):
        """Get the next rows/events that lie in the future."""
        in_future = False
        for row_data in self.iter_row_data(starting_row=3):
            if in_future:
                yield row_data
            else:
                try:
                    if row_data["Datum"] > datetime.datetime.today():
                        in_future = True
                        yield row_data
                except KeyError:
                    print(f"Could not parse date for {row_data}")
                    raise

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
            self.check_mesner(event, report=report)
            self.check_liturg_opfer(event, report=report)
            self.check_opferzweck(event, report=report)
            self.check_technik_ton_kirche(event, report=report)
            self.check_technik_video_stream(event, report=report)
            self.check_technik_songbeamer(event, report=report)
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

    def check_mesner(self, event, report=None):
        if not event["Mesnerdienst"]:
            if report is None:
                report = print
            report(
                {
                    "message": (
                        "Kein(e) Mesner(in) eingetragen am "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]}! '
                        "Bitte eine Person eintragen, oder wenn niemand benötigt "
                        "wird, ein Minuszeichen eintragen."
                    ),
                    "recipient": f"mesner@{self._mail_domain}",
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
                        f'{event["Uhrzeit"]} für Liturgendienst und Opfer zählen! '
                        "Bitte eine Person eintragen, oder wenn niemand benötigt "
                        "wird, ein Minuszeichen eintragen."
                    ),
                    "recipient": f"kgr@{self._mail_domain}",
                }
            )

    def check_opferzweck(self, event, report=None):
        if not event["Opferzweck"]:
            if report is None:
                report = print
            report(
                {
                    "message": (
                        "Kein Opferzweck eingetragen für "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]}! '
                        "Bitte einen Opferzweck eintragen, oder wenn kein Opfer "
                        "gesammelt wird oder kein Opferzweck benannt werden "
                        "kann ein Minuszeichen eintragen."
                    ),
                    "recipient": f"kirchenpflege@{self._mail_domain}",
                }
            )

    def check_technik_ton_kirche(self, event, report=None):
        if not event["Ton Kirche"]:
            if report is None:
                report = print
            report(
                {
                    "message": (
                        "Kein Tontechniker eingetragen am "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]}. '
                        "Bitte eine Person eintragen, oder wenn niemand benötigt "
                        "wird, ein Minuszeichen eintragen."
                    ),
                    "recipient": f"technik@{self._mail_domain}",
                }
            )

    def check_technik_video_stream(self, event, report=None):
        if not event["Stream u. Kamera Mischpult"]:
            if report is None:
                report = print
            report(
                {
                    "message": (
                        "Kein Techniker für Stream und Kamera Mischpult eingetragen am "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]}. '
                        "Bitte eine Person eintragen, oder wenn niemand benötigt "
                        "wird, ein Minuszeichen eintragen."
                    ),
                    "recipient": f"technik@{self._mail_domain}",
                }
            )

    def check_technik_songbeamer(self, event, report=None):
        if not event["Songbeamer Texte und Lieder"]:
            if report is None:
                report = print
            report(
                {
                    "message": (
                        "Kein Techniker für Songbeamer eingetragen am "
                        f'{event["Datum"].strftime("%a., %d. %b")}, '
                        f'{event["Uhrzeit"]}. '
                        "Bitte eine Person eintragen, oder wenn niemand benötigt "
                        "wird, ein Minuszeichen eintragen."
                    ),
                    "recipient": f"technik@{self._mail_domain}",
                }
            )

    def check_for_nextcloud_folder_and_ablauf(self, event, report=None):
        if report is None:
            report = print
        nc = NextCloud(
            webdav_url=f"{NEXTCLOUD_BASE_URL}/remote.php/dav/files/wulmer/",
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
                                f"Gottesdienst (\"{event['Art/Anlass/Thema']}\") am "
                                f"{event['Datum'].strftime('%a., %d. %b')} abgelegt. "
                                f"Bitte im Verzeichnis '{base_folder}{event_datum}' "
                                "eine Datei mit 'Ablauf' im Dateinamen ablegen! "
                                f"Eingetragen für Predigt ist: {event['Prediger']}"
                            ),
                            "recipient": f"webmaster@{self._mail_domain}",
                        }
                    )
                break
        else:
            report(
                {
                    "message": (
                        "Es ist noch kein Verzeichnis auf NextCloud für den "
                        f"Gottesdienst (\"{event['Art/Anlass/Thema']}\") am "
                        f"{event['Datum'].strftime('%a., %d. %b')} angelegt. "
                        f"Bitte ein Verzeichnis '{base_folder}{event_datum}' anlegen "
                        "und den Ablauf dort ablegen! Die Datei sollte das Wort "
                        "'Ablauf' im Namen haben."
                    ),
                    "recipient": f"webmaster@{self._mail_domain}",
                }
            )
