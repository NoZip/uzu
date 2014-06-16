
import json

from urllib.parse import urlunsplit, urlencode

from tornado.gen import coroutine

class View:
    """
    Couchbase view
    """

    def __init__(self, design, name, **options):
        self._design = design
        self.name = name
        self._options = options

        self._http_client = self._design._bucket._server._http_client
        self._server = (self._design._bucket._server._host, "8092")

    @coroutine
    def execute(self, **options):
        options.update(self._options)

        url = urlunsplit((
            "http",
            ":".join(self._server),
            "{bucket}/_design/{design}/_view/{name}".format(
                bucket = self._design._bucket.name,
                design = self._design.name,
                name = self.name
            ),
            urlencode(options),
            None
        ))

        response = yield self._http_client.fetch(url)

        return json.loads(response.body.decode())["rows"]

