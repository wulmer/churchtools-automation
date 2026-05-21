from pathlib import Path

import httpx
import tenacity
from webdav4.fsspec import WebdavFileSystem


class NextCloud:
    def __init__(self, webdav_url: str, webdav_auth):
        self._fs = WebdavFileSystem(webdav_url, auth=webdav_auth)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential_jitter(initial=1, max=60, jitter=2),
        retry=tenacity.retry_if_exception_type(httpx.ReadTimeout),
        reraise=True,
    )
    def ls(self, path: str = "/", detail: bool = False):
        return self._fs.ls(path, detail=detail)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential_jitter(initial=1, max=60, jitter=2),
        retry=tenacity.retry_if_exception_type(httpx.ReadTimeout),
        reraise=True,
    )
    def exists(self, path: str):
        return self._fs.exists(path)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential_jitter(initial=1, max=60, jitter=2),
        retry=tenacity.retry_if_exception_type(httpx.ReadTimeout),
        reraise=True,
    )
    def mkdir(self, path: str):
        return self._fs.makedirs(path, exist_ok=True)

    def mv(self, src: str, dest: str):
        src_path = Path(src)
        self.mkdir(dest)
        dest_path = Path(dest) / src_path.stem
        return self._fs.mv(src, str(dest_path), recursive=True)

    def rm(self, path: str, recursive: bool = False):
        print(f"Deleting {path} with recursive={recursive}")
        return self._fs.rm(path, recursive=recursive)
