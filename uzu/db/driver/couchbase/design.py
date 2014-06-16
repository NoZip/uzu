
from uzu.db.driver.couchbase.view import View

class Design:
    """
    Couchbase design document
    """

    def __init__(self, bucket, name):
        self._bucket = bucket
        self.name = name

    def view(self, name):
        return View(self, name)