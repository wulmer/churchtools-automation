import os
import shutil
import subprocess
import sys
from pathlib import Path

from churchtools import ChurchToolsApi
from postfix_sync import Mapping, PostMap

if __name__ == "__main__":
    postfix_db = Path("/etc/postfix/virtual")
    if not postfix_db.exists():
        print(
            f"Cannot find file {postfix_db}! Are you running "
            "this script on the right machine?"
        )
        sys.exit(1)

    if not os.environ.get("API_BASE_URL") or not os.environ.get("ADMIN_TOKEN"):
        print("You must define API_BASE_URL and ADMIN_TOKEN!")
        sys.exit(2)

    postmap = PostMap(postfix_db)
    mappings = Mapping.fromfile(postfix_db)

    ct = ChurchToolsApi(os.environ["API_BASE_URL"], os.environ["ADMIN_TOKEN"])
    groups_to_sync = {
        "Technik-Team": "technik-list@johanneskirche-rutesheim.de",
        "Kirchengemeinderat": "kgr-list@johanneskirche-rutesheim.de",
        "KGR-Mitglieder Johanneskirche": "kgr-joki-list@johanneskirche-rutesheim.de",
        "Musik-Team": "musikteam-list@johanneskirche-rutesheim.de",
        "Mesner": "mesner-list@johanneskirche-rutesheim.de",
        "Netzwerktreffen": "netzwerktreffen-list@johanneskirche-rutesheim.de",
        "Welcome-Team": "welcometeam-list@johanneskirche-rutesheim.de",
    }

    has_updates = False
    for group_ctname in groups_to_sync:
        alias = groups_to_sync[group_ctname]
        ctgroup = list(ct.get_groups(query=group_ctname))[0]
        members = ct.get_group_members(group_id=ctgroup["id"])
        recipients = []
        for m in members:
            if "postfix:ignore" in ct.get_tags_for_person(m["personId"]):
                continue
            if not m["groupMemberStatus"] == "active":
                continue
            try:
                default_email = ct.get_default_email_for_person(m["personId"])
            except ValueError:
                default_email = None
            if not default_email:
                print(
                    f"WARNING: User #{m['personId']} has no default email "
                    f"address! Cannot add user to group {group_ctname}!"
                )
                continue
            recipients.append(PostMap.normalize_email(default_email))

        recipients_in_db = [
            PostMap.normalize_email(e) for e in postmap.get_recepients_for_alias(alias)
        ]
        if set(recipients) == set(recipients_in_db):
            # print(f"Nothing to do for group '{group_ctname}'")
            continue
        to_add = set(recipients) - set(recipients_in_db)
        to_remove = set(recipients_in_db) - set(recipients)
        print(
            f"Updating list for group '{group_ctname}': "
            f"adding {to_add} ; removing {to_remove}"
        )
        mappings.update(alias, sorted(set(recipients)))
        has_updates = True

    if has_updates:
        orig_file = postfix_db
        target_file = postfix_db
        backup_file = target_file.with_suffix(".backup")
        shutil.copyfile(str(orig_file), backup_file)
        try:
            mappings.tofile(target_file)
            subprocess.check_call(
                ["/usr/sbin/postmap", str(target_file)],
                shell=False,
            )
            print(
                subprocess.run(
                    [
                        "diff",
                        "--color=never",
                        "--unified=1",
                        str(backup_file),
                        str(orig_file),
                    ],
                    capture_output=True,
                ).stdout.decode()
            )
            backup_file.unlink()
        except Exception:
            backup_file.rename(target_file)
            raise
