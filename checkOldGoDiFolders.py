import datetime
import os
import re

from nextcloud import NextCloud

NEXTCLOUD_BASE_URL = os.environ["NEXTCLOUD_BASE_URL"]
NEXTCLOUD_TOKEN = os.environ["NEXTCLOUD_TOKEN"]
NEXTCLOUD_USER = os.environ["NEXTCLOUD_USER"]

if __name__ == "__main__":
    nc = NextCloud(
        webdav_url=f"{NEXTCLOUD_BASE_URL}/remote.php/dav/files/wulmer/",
        webdav_auth=(NEXTCLOUD_USER, NEXTCLOUD_TOKEN),
    )
    base_folder = "Gottesdienste/"
    existing_items = nc.ls(base_folder, detail=True)
    now = datetime.datetime.now()
    fourteen_weeks_ago = now - datetime.timedelta(weeks=14)
    for item in existing_items:
        if item["type"] == "directory" and re.match(
            f"^{base_folder}" + r"\d{4}-\d{2}-\d{2}.*$", item["name"]
        ):
            date = datetime.datetime.strptime(
                item["name"][len(base_folder) : len(base_folder) + 10], "%Y-%m-%d"
            )
            if date < fourteen_weeks_ago:
                print(
                    f"Das Gottesdienstverzeichnis '{item['name']}' "
                    "sollte gelöscht werden!"
                )
