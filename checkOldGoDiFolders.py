import datetime
import os
import re

from nextcloud import NextCloud

NEXTCLOUD_BASE_URL = os.environ["NEXTCLOUD_BASE_URL"]
NEXTCLOUD_TOKEN = os.environ["NEXTCLOUD_TOKEN"]
NEXTCLOUD_USER = os.environ["NEXTCLOUD_USER"]


def find_outdated_folders(nc, base_folder, weeks):
    """Find outdated folders.

    Finds folders which have a folder name that contains a date that is older
    than x weeks and which have been last modified at least x weeks ago."""
    existing_items = nc.ls(base_folder, detail=True)
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    x_weeks_ago = now - datetime.timedelta(weeks=weeks)
    outdated_folders = []
    for item in existing_items:
        if item["type"] == "directory" and re.match(
            f"^{base_folder}" + r"\d{4}-\d{2}-\d{2}.*$", item["name"]
        ):
            foldername_date = datetime.datetime.strptime(
                item["name"][len(base_folder) : len(base_folder) + 10], "%Y-%m-%d"
            ).replace(tzinfo=datetime.timezone.utc)
            folder_date = item["modified"]
            if foldername_date < x_weeks_ago and folder_date < x_weeks_ago:
                outdated_folders.append(item["name"])
    return outdated_folders


if __name__ == "__main__":
    nc = NextCloud(
        webdav_url=f"{NEXTCLOUD_BASE_URL}/remote.php/dav/files/wulmer/",
        webdav_auth=(NEXTCLOUD_USER, NEXTCLOUD_TOKEN),
    )
    base_folder = "Gottesdienste/"
    archive_folder = f"{base_folder}Archiv"
    weeks = 1
    outdated_folders = find_outdated_folders(nc, base_folder, weeks=weeks)
    for outdated_folder in outdated_folders:
        print(
            f"Das Gottesdienstverzeichnis '{outdated_folder}' "
            f"ist älter als {weeks} Woche(n) und wird jetzt ins Archiv verschoben."
        )
        nc.mv(
            outdated_folder,
            archive_folder,
        )

    base_folder = "Gottesdienste/Archiv"
    weeks = 14
    outdated_folders = find_outdated_folders(nc, base_folder, weeks=weeks)
    for outdated_folder in outdated_folders:
        print(
            f"Das Gottesdienstverzeichnis '{outdated_folder}' "
            f"ist älter als {weeks} Woche(n) und wird jetzt "
            "(noch nicht wirklich) gelöscht."
        )
        # nc.rm(
        #     outdated_folder,
        # )
