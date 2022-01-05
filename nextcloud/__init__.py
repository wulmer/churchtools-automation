from webdav4.fsspec import WebdavFileSystem


class NextCloud:
    def __init__(self, webdav_url: str, webdav_auth):
        self._fs = WebdavFileSystem(webdav_url, auth=webdav_auth)

    def ls(self, path: str = "/", detail: bool = False):
        return self._fs.ls(path, detail=detail)

    def exists(self, path: str):
        return self._fs.exists(path)
