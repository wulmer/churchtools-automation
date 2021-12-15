import requests


class ChurchToolsApi:
    def __init__(self, base_url, token):
        self._base_url = base_url
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Login {token}"})

    def add_to_group(self, who, to):
        response = self._session.put(self._base_url + f"/groups/{to}/members/{who}")
        response.raise_for_status()

    def remove_from_group(self, who, from_):
        response = self._session.delete(
            self._base_url + f"/groups/{from_}/members/{who}"
        )
        response.raise_for_status()

    def get_person(self, person_id):
        response = self._session.get(self._base_url + f"/persons/{person_id}")
        response.raise_for_status()
        return response.json()["data"]

    def get_default_email_for_person(self, person_id):
        person = self.get_person(person_id)
        emails = person.get("emails", [])
        for email in emails:
            if email["isDefault"] == True:
                return email["email"]

    def get_tags_for_person(self, person_id):
        response = self._session.get(self._base_url + f"/persons/{person_id}/tags")
        response.raise_for_status()
        tags = {d['name'] for d in response.json()["data"]}
        return tags

    def get_persons(self, statuses=None):
        params = {}
        if statuses is not None:
            params["status_ids[]"] = statuses
        for person in self.paginate(self._base_url + "/persons", params=params):
            yield person

    def get_groups(self, query=None):
        params = {}
        if query is not None:
            params["query"] = query
        for group in self.paginate(self._base_url + "/groups", params=params):
            yield group

    def get_group_members(self, group_id):
        for member in self.paginate(self._base_url + f"/groups/{group_id}/members"):
            yield member

    def get_statuses(self):
        for status in self.paginate(self._base_url + "/statuses"):
            yield status

    def paginate(self, url, params=None):
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
