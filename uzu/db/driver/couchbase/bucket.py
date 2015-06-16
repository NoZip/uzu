
import json

from uuid import uuid4
from collections.abc import Sequence, Mapping
from datetime import datetime

from tornado.gen import coroutine

from uzu.db.driver import Driver
from uzu.tools.memcached import Memcached
from uzu.tools.structure import structure
from uzu.db.field import *

from uzu.db.driver.couchbase.design import Design


Meta = structure("Meta", ("key", "cas"))

ISO_DATE = "%Y-%m-%d"
ISO_TIME = "%H:%M:%S.%f%z"
ISO_DATETIME = ISO_DATE + 'T' + ISO_TIME

def encode_field(value, field):
    if isinstance(field, DateTimeField):
        return value.strftime(ISO_DATETIME)

    elif isinstance(field, ListField):
        return [encode_field(item, field.field) for item in value]
        
    elif isinstance(field, ForeignKeyField):
        return value.key

    else:
        return value

def decode_field(value, field):
    if isinstance(field, DateTimeField):
        return datetime.strptime(value, ISO_DATETIME)

    elif isinstance(field, ListField):
        return [decode_field(item, field.field) for item in value]

    elif isinstance(field, ForeignKeyField):
        return Proxy(key=value, schema=field.schema)

    else:
        return value


class Bucket(Driver):
    """
    Couchbase Bucket
    """

    def __init__(self, server, name, port):
        self._server = server
        self.name = name
        self._port = port

        self._memcached_client = Memcached(self._server._host, self._port)

        self._cache = {}

    @coroutine
    def load(self, key, schema, refresh_cache=True):
        if key not in self._cache:
            response = yield self._memcached_client.get(key)
            doc = json.loads(response.value.decode())

            data = {}
            for name, value in doc.items():
                data[name] = decode_field(value, schema.fields[name])

            entry = schema(data)
            entry.meta = Meta(key, response.header.cas)

            self._cache[key] = entry

        elif refresh_cache:
            yield self._cache[key].reload()

        return self._cache[key]

    @coroutine
    def reload(self, entry):
        response = yield self._memcached_client.get(entry.key)
        doc = json.loads(response.value.decode())

        data = {}
        for name, value in doc.items():
            data[name] = decode_field(value, entry.fields[name])

        entry.update(data)
        entry.meta.cas = response.header.cas

    @coroutine
    def store(self, entry):
        meta = getattr(entry, "meta", None)
        doc = {
            name: encode_field(value, entry.fields[name])
            for name, value in entry.items()
        }

        doc = json.dumps(doc)

        if meta:
            # Update the document in database
            response = yield self._memcached_client.replace(meta.key, doc, entry.meta.cas)
            entry.meta.cas = response.header.cas
        else:
            # Create the document in database
            key = uuid4().hex
            response = yield self._memcached_client.add(key, doc)
            entry.meta = Meta(key, response.header.cas)
            self._cache[key] = entry

    @coroutine
    def remove(self, entry):
        response = yield self._memcached_client.delete(entry.key)
        del self._cache[entry.key]
        del entry.meta

    def design(self, name):
        return Design(self, name)