import os

from churchtools import ChurchToolsApi

if __name__ == "__main__":
    ct = ChurchToolsApi(os.environ["BASE_URL"], os.environ["ADMIN_TOKEN"])

    all_members_group_id = list(ct.get_groups(query="Auto-Gruppe: Alle Mitarbeiter"))[
        0
    ]["id"]

    member_status_ids = [s["id"] for s in ct.get_statuses() if s["isMember"]]

    member_persons = ct.get_persons(status_ids=member_status_ids)
    member_person_ids = {p["id"] for p in member_persons}

    existing_group_members = ct.get_group_members(group_id=all_members_group_id)
    existing_group_member_ids = {p["personId"] for p in existing_group_members}

    to_add = member_person_ids - existing_group_member_ids
    to_remove = existing_group_member_ids - member_person_ids

    if not to_add and not to_remove:
        print("Nothing to do today :-)")
    for p in to_add:
        print(f"Adding #{p}")
        ct.add_to_group(who=p, to=all_members_group_id)
    for p in to_remove:
        print(f"Removing #{p}")
        ct.remove_from_group(who=p, from_=all_members_group_id)
