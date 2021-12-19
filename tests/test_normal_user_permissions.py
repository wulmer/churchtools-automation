from functools import partial

import pytest_bdd
import requests
from pytest_bdd import given, parsers, then, when

from churchtools import ChurchToolsApi


GROUP_ID_ALLE_MITARBEITER = 172


scenario = partial(pytest_bdd.scenario, "normal_user.feature")


@scenario("Normal user in no group cannot see other persons")
def test_normal_user_cannot_see_others():
    pass


@given("a user who is not member of any group", target_fixture="user")
def no_group_user(api: ChurchToolsApi):
    for user in api.get_persons():
        if len(api.get_memberships(user["id"])) == 0:
            return user
    raise RuntimeError("No user found who is in no group!")


@when("the user searches for other persons", target_fixture="search_result")
def the_user_searches_for_other_persons(make_user_api, user):
    user_api: ChurchToolsApi = make_user_api(user["id"])
    search_result = user_api.get_persons()
    return search_result


@then("the user should not see other persons")
def the_user_should_not_see_other_persons(search_result):
    try:
        for person in search_result:
            raise AssertionError("There should be no search result!")
    except requests.HTTPError as e:
        assert e.response.status_code == 401


@scenario("Normal user in a 'Kleingruppe' group can only see other group members")
def test_normal_user_in_a_kleingruppe_can_only_see_other_group_members():
    pass


@scenario("Normal user in a 'Dienst' group can only see other group members")
def test_normal_user_in_a_dienst_can_only_see_other_group_members():
    pass


@scenario("Normal user in a 'Gremium/Ausschuss' group can only see other group members")
def test_normal_user_in_a_gremium_can_only_see_other_group_members():
    pass


@given(
    parsers.parse("a user who is only member of one '{group_type}' group"),
    target_fixture="user",
)
def a_user_who_is_only_member_of_one_group_type(api: ChurchToolsApi, group_type):
    required_group_type_id = api.get_id_of_group_type(group_type)
    for user in api.get_persons():
        counter_for_groups_of_correct_type = 0
        for membership in api.get_memberships(user["id"]):
            assert membership["group"]["domainType"] == "group"
            group_id = int(membership["group"]["domainIdentifier"])
            if group_id == GROUP_ID_ALLE_MITARBEITER:
                continue  # don't count alle mitarbeiter merkmal
            group = api.get_group(id=membership["group"]["domainIdentifier"])
            group_type_id = group["information"]["groupTypeId"]
            if group_type_id == required_group_type_id:
                return user
            break
    raise RuntimeError(
        f"Could not find a user who is only in a group of type '{group_type}'"
    )


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
                f"#{person['id']} of their group who is also in group {group_of_other_member}"
            )
