"""
This file is part of Uzu.

Uzu is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Uzu is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Uzu.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
from uuid import uuid4
from collections.abc import Sequence, Mapping
from datetime import datetime

from tornado.gen import coroutine

from uzu.db.driver import Driver
from uzu.tools.memcached import Memcached
from uzu.tools.structure import structure
from uzu.db.field import *
# from uzu.db.field.relations import *


Meta = structure("Meta", ("key", "cas"))

ISO_DATE = "%Y-%m-%d"
ISO_TIME = "%H:%M:%S.%f%z"
ISO_DATETIME = ISO_DATE + 'T' + ISO_TIME

def encode_field(value, field):
	if isinstance(field, DateTimeField):
		return value.strftime(ISO_DATETIME)
	elif isinstance(field, ListField):
		return [encode_field(item, field.field) for item in value]
	# elif isinstance(field, ModelField):
	# 	return value.key
	else:
		return value

@coroutine
def decode_field(value, field):
	if isinstance(field, DateTimeField):
		return datetime.strptime(value, ISO_DATETIME)
	elif isinstance(field, ListField):
		return [decode_field(item, field.field) for item in value]
	# elif isinstance(field, ModelField):
	# 	entry = yield field.model.load(value)
	# 	return entry
	else:
		return value


class CouchbaseBucket(Driver):

	def __init__(self, host, port):
		self._client = Memcached(host, port)
		self._cache = {}

	@coroutine
	def load(self, key, schema, refresh_cache=False):
		if key not in self._cache:
			response = yield self._client.get(key)
			doc = json.loads(response.value.decode())

			data = {}
			for name, value in doc.items():
				data[name] = yield decode_field(value, schema.fields[name])

			entry = schema(data)
			entry.meta = Meta(key, response.header.cas)

			self._cache[key] = entry

		elif refresh_cache:
			yield self._cache[key].reload()

		return self._cache[key]

	@coroutine
	def reload(self, entry):
		response = yield self._client.get(entry.key)

		data = {}
		for name, value in entry.items():
			data[name] = yield decode_field(value, entry.fields[name])

		entry.clear()
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
			response = yield self._client.replace(meta.key, doc, entry.meta.cas)
			entry.meta.cas = response.header.cas
		else:
			#create the document in database
			key = uuid4().hex
			response = yield self._client.add(key, doc)
			entry.meta = Meta(key, response.header.cas)
			self._cache[key] = entry

	@coroutine
	def remove(self, entry):
		response = yield self._client.delete(entry.key)
		del self._cache[entry.key]
		del entry.meta


class CouchbaseSASLBucket(CouchbaseBucket):

	def __init__(self, host, name, password):
		self._client = Memcached(host, 11211)
		self._client.sasl_plain_auth(name, password)
