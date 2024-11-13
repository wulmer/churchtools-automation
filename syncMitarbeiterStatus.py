import argparse
import os

from churchtools import ChurchToolsApi

# the following list defines all roles for groups which should
# be treated as 'Mitarbeiter'
MITARBEITER_GROUP_ROLES = {
    "Kleingruppe": {"Leiter"},
    "Dienst": {"Leiter", "Mitarbeiter"},
    "Gremium/Ausschuss": {"Vorsitz", "Stellv. Vorsitz", "Mitglieder"},
    "Orga-Gruppe": {"Leiter"},
}

PROTECTED_STATUS = "Mitarbeiter (HA)"

DEFAULT_MITARBEITER_STATUS = "Mitarbeiter (EA)"

EX_MITARBEITER_STATUS = "Ehemalige MA"

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not change anything, just print what would be done",
    )
    args = arg_parser.parse_args()
    if args.dry_run:
        print("==== DRY RUN ====")

    api = ChurchToolsApi(os.environ["API_BASE_URL"], os.environ["ADMIN_TOKEN"])
    status_ids = api.get_status_ids()

    members_from_roles = set()
    for group_type in MITARBEITER_GROUP_ROLES:
        group_type_id = api.get_id_of_group_type(group_type)
        role_ids = [
            api.get_id_of_group_role(group_type_id, group_role)
            for group_role in MITARBEITER_GROUP_ROLES[group_type]
        ]
        active_groups = api.get_groups(group_type_ids=[group_type_id])
        for group in active_groups:
            members = api.get_group_members(group["id"], role_ids=role_ids)
            for member in members:
                members_from_roles.add(member["personId"])

    systemuser_status_id = status_ids["Systembenutzer"]

    members_from_status = set()
    member_status_ids = [s["id"] for s in api.get_statuses() if s["isMember"]]
    for person in api.get_persons(status_ids=member_status_ids):
        members_from_status.add(person["id"])

    should_have_member_status = members_from_roles - members_from_status
    should_not_have_member_status = members_from_status - members_from_roles

    if not should_have_member_status and not should_not_have_member_status:
        print("Nothing to do today :-)")
    if should_have_member_status:
        print(f"Upgrading persons to '{DEFAULT_MITARBEITER_STATUS}' status:")
        for p in should_have_member_status:
            print(
                f"- #{p}\t{os.environ['CT_BASE_URL']}?q=churchdb#/PersonView/searchEntry:%23{p}/"
            )
            if not args.dry_run:
                api.set_person_status(p, status_ids[DEFAULT_MITARBEITER_STATUS])
    if should_not_have_member_status:
        print(f"Downgrading persons from members to '{EX_MITARBEITER_STATUS}':")
        for p in should_not_have_member_status:
            person_info = api.get_person(p)
            if person_info["statusId"] == systemuser_status_id:
                # ignore system users
                continue
            if person_info["statusId"] == status_ids[PROTECTED_STATUS]:
                print(f"- Not removing protected person #{p}")
                continue
            print(
                f"- #{p}\t{os.environ['CT_BASE_URL']}?q=churchdb#/PersonView/searchEntry:%23{p}/"
            )
            if not args.dry_run:
                api.set_person_status(p, status_ids[EX_MITARBEITER_STATUS])
