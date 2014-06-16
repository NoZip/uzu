import sys

sys.path.append("../")

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application
from tornado.gen import coroutine

from uzu.db.schema import Schema, drived
from uzu.db.field import *
import uzu.db.driver.couchbase as couchbase

server = couchbase.Server()
default_bucket = server.bucket()

@drived(default_bucket)
class User(Schema):
    @classmethod
    def __fields__(cls):
        return dict(
            name = StringField(required=True),
        )

class UserHandler(RequestHandler):
    @coroutine
    def get(self, key):
        user = yield User.load(key)
        self.write(user["name"])

class UserListHandler(RequestHandler):
    @coroutine
    def get(self):
        view = default_bucket.design("dev_user").view("list")
        userList = yield view.execute()
        # self.write(repr(userList))
        self.render("list.html", userList = userList)

class UserCreationHandler(RequestHandler):
    def get(self):
        self.render("form.html", uri = self.request.uri)

    @coroutine
    def post(self):
        name = self.get_argument("name")
        user = User(name = name)
        yield user.store()
        self.write(name + " stored")

application = Application([
    (r"/user/([0-9a-f]+)", UserHandler),
    (r"/user/list", UserListHandler),
    (r"/user/create", UserCreationHandler)
])

if __name__ == "__main__":
    application.listen(8888)
    IOLoop.instance().start()
