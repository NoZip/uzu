
import json

from urllib.parse import urlunsplit

from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient

from uzu.db.driver.couchbase.bucket import Bucket


class Server:
    """
    Couchbase Server
    """

    def __init__(self, host="localhost"):
        self._host = host

        self._http_client = AsyncHTTPClient()

    def bucket(self, name="default", port=11211):
        return Bucket(self, name, port)
