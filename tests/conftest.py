import functools
import os

import pytest

from churchtools import ChurchToolsApi


@pytest.fixture
def api():
    return ChurchToolsApi(os.environ["BASE_URL"], os.environ["ADMIN_TOKEN"])


@pytest.fixture
def make_user_api(api: ChurchToolsApi):
    def wrapped_function(user_id: int):
        token = api.get_login_token(user_id)
        user_api = ChurchToolsApi(os.environ["BASE_URL"], token)
        return user_api

    return wrapped_function
