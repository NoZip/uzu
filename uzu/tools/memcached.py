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

See http://code.google.com/p/memcached/wiki/BinaryProtocolRevamped
"""

import socket

from tornado.iostream import IOStream, SSLIOStream
from tornado.gen import coroutine, Task

from uzu.tools.structure import structure, packable_structure


class MemcachedError(Exception):
	pass

class RequestError(MemcachedError):
	pass

class ServerError(MemcachedError):
	pass


RequestHeader = packable_structure(
	"RequestHeader",
	(
		"magic",
		"opcode", 
		"key_len",
		"extra_len",
		"data_type",
		"vbucket_id",
		"body_len",
		"opaque",
		"cas"
	),
	"!BBHBBHI4s8s"
)

ResponseHeader = packable_structure(
	"ResponseHeader",
	(
		"magic",
		"opcode", 
		"key_len",
		"extra_len",
		"data_type",
		"status",
		"body_len",
		"opaque",
		"cas"
	),
	"!BBHBBHI4s8s"
)

Request = structure("Request", ("header", "extra", "key", "value"))
Response = structure("Response", ("request", "header", "extra", "key", "value"))

GetExtra = packable_structure("GetExtra", ("flags"), "!I")
SetExtra = packable_structure("SetExtra", ("flags", "expiration"), "!II")
TouchExtra = packable_structure("GetExtra", ("expiration"), "!I")

status_reason = {
	0x0000 : "no error",
	0x0001 : "key not found",
	0x0002 : "key exist",
	0x0003 : "value too large",
	0x0004 : "invalid arguments",
	0x0005 : "item not stored",
	0x0006 : "incr/decr on non-numeric value",
	0x0007 : "the vbucket belong to another server",
	0x0008 : "authentification error",
	0x0009 : "authentification continue",
	0x0020 : "authentification required / not successful",
	0x0021 : "further authentification step required",
	0x0081 : "unknown command",
	0x0082 : "out of memory",
	0x0083 : "not supported",
	0x0084 : "internal error",
	0x0085 : "busy",
	0x0086 : "temporary failure"
}

class Memcached:

	def __init__(self, host, port):
		self._server = (host, port)
		stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
		self._stream = IOStream(stream)
		self.connect()

	def __del__(self):
		self.close()

	def connect(self):
		self._stream.connect(self._server)

	def close(self):
		self._stream.close()

	@coroutine
	def send_package(
		self,
		opcode,
		extra=b"",
		key=b"",
		value=b"",
		data_type=0x00,
		vbucket_id=0x0000,
		opaque=bytes(4),
		cas=bytes(8)
	):
		"""
		Sends a package to the Memcached server.

		Parameters:
			opcode: the command code.
			extra: the extra data.
			key: TODO
			value: TODO
			data_type: Reserved for future use, so live it blank.
			vbucket_id: The virtual bucket for this command.
			opaque: a value that will be returned in the response.
			cas: data version check

		Returns:
			The request object that have been sent.
		"""

		if isinstance(key, str):
			key = key.encode()

		if isinstance(value, str):
			value = value.encode()

		header = RequestHeader(
			magic = 0x80,
			opcode = opcode,
			key_len = len(key),
			extra_len = len(extra),
			data_type = data_type,
			vbucket_id = vbucket_id,
			body_len = len(extra + key + value),
			opaque = opaque,
			cas = cas
		)

		request = Request(header, extra, key, value)

		write = self._stream.write

		yield Task(write, header.pack())
		yield Task(write, extra + key + value)

		return request

	@coroutine
	def receive_package(self, request):
		read_bytes = self._stream.read_bytes

		packed_header = yield Task(read_bytes, ResponseHeader._packer.size)
		header = ResponseHeader.unpack(packed_header)

		body = yield Task(read_bytes, header.body_len)

		extra = body[:header.extra_len]
		key = body[header.extra_len:header.extra_len + header.key_len]
		value = body[header.extra_len + header.key_len:]

		response = Response(request, header, extra, key, value)

		return response

	@coroutine
	def query(self, opcode, extra=b"", key=b"", value=b"", **kwargs):
		request = yield self.send_package(opcode, extra, key, value, **kwargs)
		response = yield self.receive_package(request)

		status = response.header.status

		if status != 0x0000:
			if status > 0x0080:
				raise ServerError(status_reason[status])
			else:
				raise RequestError(status_reason[status])

		return response

	#====================#
	# Memcached commands #
	#====================#

	@coroutine
	def get(self, key):
		"""
		Get data from Memcached server.

		Parameters:
			key: the to get.

		Returns:
			The server response.
		"""
		assert key

		opcode = 0x00 #if not quiet else 0x09
		response =  yield self.query(opcode, key=key)

		response.extra = GetExtra.unpack(response.extra)

		return response

	@coroutine
	def get_key(self, key):
		raise NotImplementedError

	@coroutine
	def set(
		self,
		key,
		value=b"",
		cas=bytes(8),
		flags=0x0000,
		expiration=0
	):
		"""
		Change the key data on Memcached server.
		If the key does not exist, key and data will be created.
		If the key exist, it's data will be modified.

		Parameters:
			key: TODO
			value: TODO
			cas: TODO
			flags: TODO
			expiration: TODO

		Returns:
			The server response.
		"""
		assert(key)

		opcode = 0x01 #if not quiet else 0x11
		extra = SetExtra(flags, expiration).pack()
		response = yield self.query(
			opcode,
			extra=extra,
			key=key,
			value=value,
			cas=cas
		)

		assert(response.header.cas)

		return response

	@coroutine
	def add(
		self,
		key,
		value=b"",
		cas=bytes(8),
		flags=0x0000,
		expiration=0
	):
		"""
		Add a new key to the Memcached Server.
		Attempting to use this command on a key already in database will raise
		an exception.

		Parameters:
			key: TODO
			value: TODO
			cas: TODO
			flags: TODO
			expiration: TODO

		Returns:
			The server response.
		"""
		assert(key)

		opcode = 0x02 #if not quiet else 0x13
		extra = SetExtra(flags, expiration).pack()

		response = yield self.query(
			opcode,
			extra=extra,
			key=key,
			value=value,
			cas=cas
		)

		assert(response.header.cas)

		return response

	@coroutine
	def replace(
		self,
		key,
		value=b"",
		cas=bytes(8),
		flags=0x0000,
		expiration=0
	):
		"""
		Replace data associated to a key on Memcached server.
		If the key does not exist, an exception will be raised.

		Parameters:
			key: TODO
			value: TODO
			cas: TODO
			flags: TODO
			expiration: TODO

		Returns:
			The server response.
		"""
		assert(key)

		opcode = 0x03 #if not quiet else 0x13
		extra = SetExtra(flags, expiration).pack()
		
		response = yield self.query(
			opcode,
			extra=extra,
			key=key,
			value=value,
			cas=cas
		)

		assert(response.header.cas)

		return response

	@coroutine
	def delete(self, key):
		assert(key)

		opcode = 0x04 #if not quiet else 0x14
		response =  yield self.query(opcode, key=key)

		return response

	@coroutine
	def increment(self, key, delta, initial, expiration=0):
		raise NotImplementedError

	@coroutine
	def decrement(self, key, delta, initial, expiration=0):
		raise NotImplementedError
	
	@coroutine
	def touch(self, key, expiration=0):
		raise NotImplementedError

	@coroutine
	def get_and_touch(self, key, expiration=0):
		raise NotImplementedError

	@coroutine
	def append(self, key, value):
		raise NotImplementedError

	@coroutine
	def prepend(self, key, value):
		raise NotImplementedError

	@coroutine
	def quit(self):
		raise NotImplementedError

	@coroutine
	def flush(self, expiration=0):
		raise NotImplementedError

	@coroutine
	def noop(self):
		raise NotImplementedError

	@coroutine
	def version(self):
		raise NotImplementedError

	@coroutine
	def stat(self, key=b""):
		raise NotImplementedError

	@coroutine
	def verbosity(self, level):
		raise NotImplementedError

	#================#
	# SASL Extension #
	#================#

	@coroutine
	def sasl_list_mecanisms(self):
		response = yield self.query(0x20)

		return response

	@coroutine
	def sasl_plain_auth(self, login, password):
		value = "python-memcached\x00" + login + "\x00" + password
		response = yield self.query(0x21, key="PLAIN", value=value)

		return response