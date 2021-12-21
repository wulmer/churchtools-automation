from functools import cache
from typing import Dict, Iterator, List, Set

import requests

SYSTEMUSER_STATUSCODE = 7


class ChurchToolsApi:
    def __init__(self, base_url, token):
        self._base_url = base_url
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Login {token}"})
        self.non_protected_group_ids = set()

    @cache
    def get_id_of_group_type(self, group_type: str) -> int:
        response = self._session.get(self._base_url + "/person/masterdata")
        response.raise_for_status()
        group_types = response.json()["data"]["groupTypes"]
        filtered_group_types = list(
            filter(lambda g: g["name"] == group_type, group_types)
        )
        if len(filtered_group_types) == 0:
            raise ValueError(f"No group type found for '{group_type}'!")
        return int(filtered_group_types[0]["id"])

    @cache
    def get_id_of_group_role(self, group_type_id: int, group_role: str):
        response = self._session.get(self._base_url + "/masterdata/person/roles")
        response.raise_for_status()
        roles = response.json()["data"]
        filtered_roles = list(
            filter(
                lambda r: r["groupTypeId"] == group_type_id and r["name"] == group_role,
                roles,
            )
        )
        if len(filtered_roles) == 0:
            raise ValueError(f"No group role found for group ID '{group_type_id}'!")
        return int(filtered_roles[0]["id"])

    def create_group(self, group_name: str, group_type: str) -> Dict:
        group_type_id = self.get_id_of_group_type(group_type=group_type)
        data = {
            "name": group_name,
            "groupTypeId": group_type_id,
            "groupStatusId": 1,
            "superiorGroupId": 0,
            "campusId": 0,
            "force": False,
        }
        response = self._session.post(self._base_url + "/groups", json=data)
        response.raise_for_status()
        return response.json()["data"]

    def delete_group(self, group_id: int):
        assert group_id in self.non_protected_group_ids
        response = self._session.delete(self._base_url + f"/groups/{group_id}")
        response.raise_for_status()
        self.non_protected_group_ids.remove(group_id)

    def add_to_group(self, who: int, to: int):
        response = self._session.put(self._base_url + f"/groups/{to}/members/{who}")
        response.raise_for_status()

    def remove_from_group(self, who: int, from_: int):
        response = self._session.delete(
            self._base_url + f"/groups/{from_}/members/{who}"
        )
        response.raise_for_status()

    def get_login_token(self, person_id: int) -> str:
        response = self._session.get(
            self._base_url + f"/persons/{person_id}/logintoken"
        )
        response.raise_for_status()
        return response.json()["data"]

    def get_person(self, person_id: int):
        response = self._session.get(self._base_url + f"/persons/{person_id}")
        response.raise_for_status()
        return response.json()["data"]

    def get_memberships(self, person_id: int) -> List[Dict]:
        response = self._session.get(self._base_url + f"/persons/{person_id}/groups")
        response.raise_for_status()
        return response.json()["data"]

    def get_system_person_by_name(self, name: str) -> Dict:
        for user in self.get_persons(statuses=[SYSTEMUSER_STATUSCODE]):
            if user["firstName"] == name or user["lastName"] == name:
                return user
        raise KeyError(f"System user with name '{name}' not found.")

    def get_default_email_for_person(self, person_id: int) -> str:
        person = self.get_person(person_id)
        emails = person.get("emails", [])
        for email in emails:
            if email["isDefault"]:
                return email["email"]
        raise ValueError(f"Person #{person_id} has no default email address!")

    def get_tags_for_person(self, person_id: int) -> Set[str]:
        response = self._session.get(self._base_url + f"/persons/{person_id}/tags")
        response.raise_for_status()
        tags = {d["name"] for d in response.json()["data"]}
        return tags

    def get_persons(self, statuses: List[str] = None) -> Iterator[Dict]:
        params = {}
        if statuses is not None:
            params["status_ids[]"] = statuses
        for person in self.paginate(self._base_url + "/persons", params=params):
            yield person

    def get_group(self, name: str = None, id: int = None) -> Dict:
        multiple_results = False
        if id is not None:
            response = self._session.get(self._base_url + f"/groups/{id}")
        elif name is not None:
            response = self._session.get(
                self._base_url + "/groups", params={"query": name}
            )
            multiple_results = True
        else:
            raise ValueError("Either 'name' or 'id' must be given!")
        if response.status_code == 404:
            raise ValueError(f"Group '{name}' not found or not accessible!")
        response.raise_for_status()
        try:
            if multiple_results:
                return response.json()["data"][0]
            else:
                return response.json()["data"]
        except Exception as e:
            raise ValueError(response) from e

    def get_groups(
        self, query: str = None, group_type_ids: List[int] = None
    ) -> Iterator[Dict]:
        params = {}
        if query is not None:
            params["query"] = query
        if group_type_ids is not None:
            params["group_type_ids[]"] = group_type_ids
        for group in self.paginate(self._base_url + "/groups", params=params):
            yield group

    def get_group_members(
        self, group_id: int, role_ids: List[int] = None
    ) -> Iterator[Dict]:
        params = {}
        if role_ids is not None:
            params["role_ids[]"] = role_ids
        for member in self.paginate(
            self._base_url + f"/groups/{group_id}/members", params=params
        ):
            yield member

    def get_statuses(self) -> Iterator[Dict]:
        for status in self.paginate(self._base_url + "/statuses"):
            yield status

    def paginate(self, url: str, params: Dict[str, str] = None):
        if params is None:
            params = {}
        last_page = 999
        current_page = 1
        while current_page <= last_page:
            params.update({"page": current_page})
            response = self._session.get(url, params=params)
            response.raise_for_status()
            paged_data = response.json()
            for data in paged_data["data"]:
                yield data
            meta = paged_data["meta"]
            if "pagination" in meta:
                current_page = meta["pagination"]["current"] + 1
                last_page = meta["pagination"]["lastPage"]
            else:
                break
