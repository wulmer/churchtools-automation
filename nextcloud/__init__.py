from pathlib import Path

from webdav4.fsspec import WebdavFileSystem


class NextCloud:
    def __init__(self, webdav_url: str, webdav_auth):
        self._fs = WebdavFileSystem(webdav_url, auth=webdav_auth)

    def ls(self, path: str = "/", detail: bool = False):
        return self._fs.ls(path, detail=detail)

    def exists(self, path: str):
        return self._fs.exists(path)

    def mkdir(self, path: str):
        return self._fs.makedirs(path, exist_ok=True)

    def mv(self, src: str, dest: str):
        src_path = Path(src)
        self.mkdir(dest)
        dest_path = Path(dest) / src_path.stem
        return self._fs.mv(src, str(dest_path), recursive=True)

    # def rm(self, path: str, recursive: bool = False):
    # return self._fs.rm(path, recursive=recursive)
