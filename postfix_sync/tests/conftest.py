import shutil
from pathlib import Path

import pytest


@pytest.fixture
def postmap():
    postmap_location = "/usr/sbin/postmap"
    if Path(postmap_location).exists():
        return postmap_location
    else:
        pytest.skip(f"No postmap found under {postmap_location}")


@pytest.fixture(scope="function")
def mapping_file(tmp_path):
    source_file = Path(__file__).parent.joinpath("etc/virtual.template")
    mapping_file = tmp_path / "virtual"
    shutil.copyfile(src=str(source_file), dst=str(mapping_file))
    return mapping_file
