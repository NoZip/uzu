import sys

sys.path.append("../")

from tornado.ioloop import IOLoop
from tornado.testing import AsyncTestCase, gen_test, main

from uzu.tools.memcached import Memcached


client = Memcached("localhost", 11211)


class MemcachedTestCase(AsyncTestCase):

	def get_new_ioloop(self):
		return IOLoop.instance()

	@gen_test
	def test_get(self):
		# client = Memcached("localhost", 11211)
		response = yield client.get("test")
		self.assertEqual(response.header.status, 0x0000)

	@gen_test
	def test_set(self):
		# client = Memcached("localhost", 11211)
		string = "{\"value\": 19}"
		response = yield client.set("__test__", string)
		self.assertEqual(response.header.status, 0x0000)
		response = yield client.get("__test__")
		self.assertEqual(response.header.status, 0x0000)
		self.assertEqual(response.value.decode(), string)
		reponse = yield client.delete("__test__")
		self.assertEqual(response.header.status, 0x0000)

	@gen_test
	def test_sasl(self):
		# client = Memcached("localhost", 11211)
		response = yield client.sasl_list_mecanisms()
		self.assertEqual(response.header.status, 0x0000)
		mecanisms = response.value.decode().split()
		self.assertIn("PLAIN", mecanisms)
		response = yield client.sasl_plain_auth(login="music", password="nab3shin")
		string = "{\"value\": 19}"
		response = yield client.set("__test__", string)
		self.assertEqual(response.header.status, 0x0000)
		response = yield client.get("__test__")
		self.assertEqual(response.header.status, 0x0000)
		self.assertEqual(response.value.decode(), string)
		reponse = yield client.delete("__test__")
		self.assertEqual(response.header.status, 0x0000)

if __name__ == "__main__":
	main()