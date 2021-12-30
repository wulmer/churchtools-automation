import os
import re
from itertools import chain
from typing import List

import pytest
import requests
from pytest_bdd import given, parsers, then, when

from churchtools import ChurchToolsApi

GROUP_ID_ALLE_MITARBEITER = 172


# Fixtures for scenarios tests
@pytest.fixture
def group_context():
    return []


@pytest.fixture
def api():
    return ChurchToolsApi(os.environ["API_BASE_URL"], os.environ["ADMIN_TOKEN"])


@pytest.fixture
def make_user_api(api: ChurchToolsApi):
    def wrapped_function(user_id: int):
        token = api.get_login_token(user_id)
        user_api = ChurchToolsApi(os.environ["API_BASE_URL"], token)
        return user_api

    return wrapped_function


# Fixtures for BDD


@given(
    parsers.parse("all active '{group_type}' groups"), target_fixture="search_result"
)
def all_groups_of_a_type(api: ChurchToolsApi, group_type: str):
    group_type_id = api.get_id_of_group_type(group_type)
    groups = api.get_groups(group_type_ids=[group_type_id])
    return groups


@given("a user who is not member of any group", target_fixture="user")
def no_group_user(api: ChurchToolsApi, request):
    all_users = api.get_persons()
    user_id = request.config.cache.get("ct/user/not-member-of-any-group", None)
    if user_id is not None:
        potential_users = chain([api.get_person(user_id)], all_users)
    else:
        potential_users = all_users
    for user in potential_users:
        if len(api.get_memberships(user["id"])) == 0:
            request.config.cache.set("ct/user/not-member-of-any-group", user["id"])
            return user
    raise RuntimeError("No user found who is in no group!")


@given(
    parsers.parse("all users who are '{group_role}' of a '{group_type}' group"),
    target_fixture="search_result",
)
def all_users_who_are_role_of_a_group(
    api: ChurchToolsApi, group_role, group_type
) -> List[dict]:
    group_type_id = api.get_id_of_group_type(group_type)
    role_id = api.get_id_of_group_role(group_type_id, group_role)
    groups = api.get_groups(group_type_ids=[group_type_id])
    collected_persons = set()
    for group in groups:
        members = api.get_group_members(group["id"], role_ids=[role_id])
        for member in members:
            collected_persons.add(member["personId"])
    return collected_persons


@given(
    parsers.parse("a user who is '{group_role}' of one '{group_type}' group"),
    target_fixture="user",
)
def a_user_who_is_only_member_of_one_group_type(
    api: ChurchToolsApi,
    group_role,
    group_type,
    request,
    group_context,
):
    all_users = api.get_persons()
    user_id = request.config.cache.get(
        f"ct/user/member-{group_role}-of-group-{group_type}", None
    )
    if user_id is not None:
        potential_users = chain([api.get_person(user_id)], all_users)
    else:
        potential_users = all_users
    required_group_type_id = api.get_id_of_group_type(group_type)
    required_group_role_id = api.get_id_of_group_role(
        required_group_type_id, group_role
    )
    for user in potential_users:
        for membership in api.get_memberships(user["id"]):
            assert membership["group"]["domainType"] == "group"
            group_id = int(membership["group"]["domainIdentifier"])
            if group_id == GROUP_ID_ALLE_MITARBEITER:
                continue  # don't count alle mitarbeiter merkmal
            role_id = int(membership["groupTypeRoleId"])
            if role_id != required_group_role_id:
                continue
            group = api.get_group(id=membership["group"]["domainIdentifier"])
            group_type_id = int(group["information"]["groupTypeId"])
            if group_type_id == required_group_type_id:
                request.config.cache.set(
                    f"ct/user/member-{group_role}-of-group-{group_type}",
                    user["id"],
                )
                group_context.append(group_id)
                return user
            break
    raise RuntimeError(
        f"Could not find a user who has role {group_role} "
        f"in a group of type '{group_type}'"
    )


@when("the user searches for other persons", target_fixture="search_result")
def the_user_searches_for_other_persons(make_user_api, user) -> List[dict]:
    user_api: ChurchToolsApi = make_user_api(user["id"])
    search_result = user_api.get_persons()
    # convert to list to prevent errors if two @then steps read the generator
    try:
        return list(search_result)
    except Exception:
        return []


@when(
    "the user searches for other persons of that group", target_fixture="search_result"
)
def the_user_searches_for_other_persons_of_that_group(
    make_user_api, user, group_context
) -> List[dict]:
    user_api: ChurchToolsApi = make_user_api(user["id"])
    search_result = user_api.get_group_members(group_context[0])
    # convert to list to prevent errors if two @then steps read the generator
    try:
        return list(search_result)
    except Exception:
        return []


@when("the user searches for groups", target_fixture="search_result")
def the_user_searches_for_groups(make_user_api, user) -> List[dict]:
    user_api: ChurchToolsApi = make_user_api(user["id"])
    search_result = user_api.get_groups()
    # convert to list to prevent errors if two @then steps read the generator
    return list(search_result)


@then(parsers.parse("there is at least one '{role}' in that group"))
def there_is_at_least_one_role_in_that_group(
    role, search_result: List[dict], api: ChurchToolsApi
):
    if "'" in role:
        role_str = "'" + role + "'"
        roles = re.findall(r"'(.*?)'", role_str)
    else:
        roles = [role]
    invalid_groups = []
    for group in search_result:
        has_required_role = False
        for r in roles:
            if has_required_role:
                break
            role_id = api.get_id_of_group_role(group["information"]["groupTypeId"], r)
            persons_with_role = api.get_group_members(group["id"], role_ids=[role_id])
            for _ in persons_with_role:
                has_required_role = True
                break
        if not has_required_role:
            invalid_groups.append(group["name"])
    if invalid_groups:
        raise AssertionError(
            f"There is no person with role '{role}' in each "
            f"of the following groups: {', '.join(invalid_groups)}"
        )


@then("the user should not see other persons")
@then("there should be only public search results")
def there_should_be_only_public_search_results(search_result, user):
    try:
        for result in search_result:
            if "personId" in result:
                if result["personId"] == user["id"]:
                    continue  # users may see themselves
            if "securityLevelForGroup" in result:
                if result["settings"]["isPublic"]:
                    continue  # public groups in search results are OK
            raise AssertionError("There should be no private search results!")
    except requests.HTTPError as e:
        assert e.response.status_code in (401, 403)


@then("the user should only see members of that group")
def the_user_should_only_see_members_of_that_group(
    api: ChurchToolsApi, user, search_result, make_user_api
):
    user_api = make_user_api(user["id"])
    memberships = user_api.get_memberships(user["id"])
    assert (
        len(memberships) > 0
    ), f"User #{user['id']} cannot see their own membership in any group!"
    membership = memberships[0]
    group_of_user = membership["group"]["domainIdentifier"]
    for person in search_result:
        if person["id"] == user["id"]:
            continue  # we don't mind seeing ourself ;-)
        memberships_of_other_member = user_api.get_memberships(person["id"])
        for membership in memberships_of_other_member:
            group_of_other_member = membership["group"]["domainIdentifier"]
            assert group_of_other_member == group_of_user, (
                f"User #{user['id']} of group {group_of_user} can see person "
                f"#{person['id']} of their group who is also in "
                f"group {group_of_other_member}"
            )


@then("the user should see all members of that group")
def the_user_should_see_all_members_of_that_group(
    api: ChurchToolsApi, user, search_result, group_context
):
    global_search_result = api.get_group_members(group_context[0])
    global_result_ids = {r["personId"] for r in global_search_result}

    try:
        users_search_result = search_result
        users_result_ids = {r["personId"] for r in users_search_result}
    except Exception as e:
        raise Exception(
            f"User #{user['id']} should see all members of group {group_context[0]}"
        ) from e

    assert users_result_ids == global_result_ids


@then(parsers.parse("the user should only see up to level {level:d} details"))
def the_user_should_only_see_up_to_level_details(
    api: ChurchToolsApi, user, search_result, make_user_api, level
):
    user_api: ChurchToolsApi = make_user_api(user["id"])
    for result in search_result:
        other_person_id = result["personId"]
        if user["id"] == other_person_id:
            continue  # no need to check seeing one's own details
        permissions = user_api.get_person_permissions(other_person_id)
        active_level = permissions["churchdb"]["+see persons"]
        assert active_level == level, (
            f"User #{user['id']} can only see level {active_level} "
            f"of person #{result['personId']} instead of level {level}"
        )


@then("the user should have the permission to edit other persons' details")
def the_user_should_have_the_permission_to_edit_other_persons_details(
    api: ChurchToolsApi, user, search_result, make_user_api
):
    user_api: ChurchToolsApi = make_user_api(user["id"])
    for result in search_result:
        other_person_id = result["personId"]
        if user["id"] == other_person_id:
            continue  # no need to check seeing one's own details
        permissions = user_api.get_person_permissions(other_person_id)
        assert permissions["churchdb"]["+edit persons"]


@then("the user should see all non-hidden groups")
def the_user_should_see_all_non_hidden_groups(api: ChurchToolsApi, search_result):
    group_ids = {g["id"] for g in search_result}
    all_group_ids = {g["id"] for g in api.get_groups()}

    assert group_ids == all_group_ids


@then(parsers.parse("these users have status in {status_list}"))
def these_users_have_status_in_status_list(
    api: ChurchToolsApi, status_list, search_result
):
    statuses = api.get_statuses()
    evald_status_list = set(eval(status_list))
    status_ids = [s["id"] for s in statuses if s["name"] in evald_status_list]
    all_person_ids_with_these_statuses = {
        p["id"] for p in api.get_persons(status_ids=status_ids)
    }
    found_user_ids = search_result
    all_persons_with_wrong_status = found_user_ids - all_person_ids_with_these_statuses
    assert not all_persons_with_wrong_status, (
        "Following persons have not the required status "
        f"{status_list}: {all_persons_with_wrong_status}"
    )
