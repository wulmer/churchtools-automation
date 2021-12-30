from postfix_sync import PostMap

import pytest


@pytest.fixture
def mypostmap(postmap, mapping_file):
    return PostMap(mapping_file)


def test_normalize_email():
    assert "foo@server.com" == PostMap.normalize_email("FoO@SeRVER.cOm")


def test_get_aliases(mypostmap: PostMap):
    assert {
        "single_bar@domain2.de",
        "single_baz@domain2.de",
        "group@domain2.de",
        "no_empty_line_before@domain2.de",
        "group-with-comments@domain2.de",
    } == mypostmap.get_aliases()
