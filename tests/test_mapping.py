import shutil
import subprocess
from pathlib import Path

import pytest

from postfix_sync import Mapping
from postfix_sync.postmap import PostMap


@pytest.fixture(scope="function")
def mapping_file(tmp_path):
    source_file = Path(__file__).parent.joinpath("etc/virtual.template")
    mapping_file = tmp_path / "virtual"
    shutil.copyfile(src=str(source_file), dst=str(mapping_file))
    return mapping_file


def test_parsing_from_file(mapping_file):
    mf = Mapping.fromfile(mapping_file)
    assert len(mf) == 5


def test_parsing_comment_only():
    mf = Mapping.fromtext("# some@alias for@testing\n")
    assert len(mf) == 0

    mf = Mapping.fromtext("  \t   # some@alias for@testing")
    assert len(mf) == 0


def test_parsing_from_text():
    mf = Mapping.fromtext("some@alias for@testing\n")
    assert len(mf) == 1
    assert mf[0]["key"] == "some@alias"
    assert mf[0]["value"] == ["for@testing"]
    assert mf[0]["start_line"] == 1
    assert mf[0]["end_line"] == 1


def test_parsing_with_line_continuation():
    mf = Mapping.fromtext("alias@domain.com\n\treal@address.com")
    assert len(mf) == 1
    assert mf[0]["key"] == "alias@domain.com"
    assert mf[0]["value"] == ["real@address.com"]
    assert mf[0]["start_line"] == 1
    assert mf[0]["end_line"] == 2

    mf = Mapping.fromtext("alias@domain.com\n   real@address.com")
    assert len(mf) == 1
    assert mf[0]["key"] == "alias@domain.com"
    assert mf[0]["value"] == ["real@address.com"]
    assert mf[0]["start_line"] == 1
    assert mf[0]["end_line"] == 2


def test_parsing_multiple_entries_per_key():
    mf = Mapping.fromtext(
        "alias@domain.com first@mail.com, second@mail.com,\n\tthird@mail.com\n  fourth@mail.com"
    )
    assert len(mf) == 1
    assert mf[0]["key"] == "alias@domain.com"
    assert mf[0]["value"] == [
        "first@mail.com",
        "second@mail.com",
        "third@mail.com",
        "fourth@mail.com",
    ]
    assert mf[0]["start_line"] == 1
    assert mf[0]["end_line"] == 3


def test_parsing_finds_alias_at_correct_position(mapping_file):
    mf = Mapping.fromfile(mapping_file)
    entry = mf.get("group@domain2.de")
    assert entry["start_line"] == 8
    assert entry["end_line"] == 11


def test_line_replacement():
    assert "x\n2\n3\n4\n5" == Mapping._replace_lines("1\n2\n3\n4\n5", 1, 1, "x")
    assert "x" == Mapping._replace_lines("1\n2\n3\n4\n5", 1, 5, "x")
    assert "x\ny\n" == Mapping._replace_lines("1\n2\n3\n4\n5", 1, 5, "x\ny\n")
    assert "1\n2\n" == Mapping._replace_lines("1\n2\n3\n4\n5", 3, 5, "")


def test_verify_update_step(mapping_file):
    subprocess.check_call(["/usr/sbin/postmap", str(mapping_file)], shell=False)
    table_before = subprocess.check_output(
        ["/usr/sbin/postmap", "-s", str(mapping_file)], shell=False
    ).decode()
    mf = Mapping.fromfile(mapping_file)
    entry = mf.get("group@domain2.de")
    mf.update("group@domain2.de", ["foo"])
    mf.update("group@domain2.de", ["foo", "bar"])
    mf.update("group@domain2.de", [""])
    mf.update("group@domain2.de", entry["value"])
    mf.tofile(mapping_file)
    subprocess.check_call(["/usr/sbin/postmap", str(mapping_file)], shell=False)
    table_after = subprocess.check_output(
        ["/usr/sbin/postmap", "-s", str(mapping_file)], shell=False
    ).decode()
    assert table_before == table_after


def test_update_with_single_address(mapping_file):
    mf = Mapping.fromfile(mapping_file)
    mf.update("group@domain2.de", ["first@address"])
    entry = mf.get("group@domain2.de")
    assert entry["value"] == ["first@address"]
    assert entry["start_line"] == 8
    assert entry["end_line"] == 9


def test_update_with_two_addresses(mapping_file):
    mf = Mapping.fromfile(mapping_file)
    mf.update("group@domain2.de", ["first@address", "second@address"])
    entry = mf.get("group@domain2.de")
    assert entry["value"] == ["first@address", "second@address"]
    assert entry["start_line"] == 8
    assert entry["end_line"] == 10


def test_update_without_address(mapping_file):
    mf = Mapping.fromfile(mapping_file)
    mf.update("group@domain2.de", [""])
    entry = mf.get("group@domain2.de")
    assert entry["value"] == []
    assert entry["start_line"] == 8
    assert entry["end_line"] == 8


def test_revert_of_invalid_changes(mapping_file):
    orig_content = mapping_file.read_bytes()
    mf = Mapping.fromfile(mapping_file)
    entry = mf.get("group@domain2.de")
    mf.update("group@domain2.de", ["x\ngroup@domain2.de y\n"])
    with pytest.raises(RuntimeError):
        mf.tofile(mapping_file)
    assert orig_content == mapping_file.read_bytes()
