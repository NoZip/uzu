import sys

sys.path.append("../")

from tornado.ioloop import IOLoop
from tornado.testing import AsyncTestCase, gen_test, main

from uzu.db.schema import Schema, drived
from uzu.db.field import *
import uzu.db.driver.couchbase as couchbase

server = couchbase.Server()
default_bucket = server.bucket()

@drived(default_bucket)
class Test(Schema):
	@classmethod
	def __fields__(cls):
		return dict(
			name = StringField(required=True),
			age = IntegerField(min=0),
			creation = DateTimeField(required=True, auto_now=True)
		)

# music_bucket = CouchbaseSASLBucket("localhost", "music", "nab3shin")

# class SASLTest(Model, driver=music_bucket):
# 	name = StringField(required=True)
# 	age = IntegerField(min=0)


class CouchbaseTestCase(AsyncTestCase):

	def get_new_ioloop(self):
		return IOLoop.instance()

	@gen_test
	def test_client(self):
		test = Test(name="Thomas", age=19)
		yield test.store()
		loaded = yield Test.load(test.key)
		self.assertEqual(dict(test), dict(loaded))
		test["age"] = 23
		yield test.store()
		yield test.remove()

	# @gen_test
	# def test_sasl_client(self):
	# 	test = SASLTest(name="Thomas", age=19)
	# 	yield test.store()
	# 	print(test.meta.key)
	# 	loaded = yield Test.load(test.meta.key)
	# 	self.assertEqual(dict(test), dict(loaded))
	# 	yield test.remove()


if __name__ == "__main__":
	main()