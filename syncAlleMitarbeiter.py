import functools
import os

import requests

BASE_URL = "https://elkw2806.church.tools/api"


class ChurchToolsApi:
    def __init__(self, base_url, token):
        self._base_url = base_url
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Login {token}"})

    def add_to_group(self, who, to):
        response = self._session.put(self._base_url + f'/groups/{to}/members/{who}')
        response.raise_for_status()

    def remove_from_group(self, who, from_):
        response = self._session.delete(self._base_url + f'/groups/{from_}/members/{who}')
        response.raise_for_status()

    def get_persons(self, statuses=None):
        params = {}
        if statuses is not None:
            params['status_ids[]'] = statuses
        for person in self.paginate(self._base_url + '/persons', params=params):
            yield person

    def get_groups(self, query=None):
        params = {}
        if query is not None:
            params['query'] = query
        for group in self.paginate(self._base_url + '/groups', params=params):
            yield group

    def get_group_members(self, group_id):
        for member in self.paginate(self._base_url + f'/groups/{group_id}/members'):
            yield member

    def get_statuses(self):
        for status in self.paginate(self._base_url + '/statuses'):
            yield status

    def paginate(self, url, params=None):
        if params is None:
            params = {}
        last_page = 999
        current_page = 1
        while current_page <= last_page:
            params.update({'page': current_page})
            response = self._session.get(url, params=params)
            response.raise_for_status()
            paged_data = response.json()
            for data in paged_data['data']:
                yield data
            meta = paged_data['meta']
            if 'pagination' in meta:
                current_page = meta['pagination']['current'] + 1
                last_page = meta['pagination']['lastPage']
            else:
                break



if __name__ == "__main__":
    ct = ChurchToolsApi(BASE_URL, os.environ['ADMIN_TOKEN'])

    all_members_group_id = list(ct.get_groups(query="Auto-Gruppe: Alle Mitarbeiter"))[0]['id']

    member_status_ids = [s['id'] for s in ct.get_statuses() if s['isMember']]

    member_persons = ct.get_persons(statuses=member_status_ids)
    member_person_ids = {p['id'] for p in member_persons}

    existing_group_members = ct.get_group_members(group_id=all_members_group_id)
    existing_group_member_ids = {p['personId'] for p in existing_group_members}

    to_add = member_person_ids - existing_group_member_ids
    to_remove = existing_group_member_ids - member_person_ids

    for p in to_add:
        ct.add_to_group(who=p, to=all_members_group_id)
    for p in to_remove:
        ct.remove_from_group(who=p, from_=all_members_group_id)
