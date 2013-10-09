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

from abc import ABCMeta
from collections.abc import MutableMapping
from types import new_class

from tornado.gen import coroutine

from uzu.db.driver import Driver


class SchemaError(Exception):
    pass


class MetaSchema(ABCMeta):

    def __init__(cls, name, bases, namespace):
        fields = {}

        for base in bases:
            if hasattr(base, "__fields__"):
                fields.update(base.__fields__())

        fields.update(cls.__fields__())

        cls.fields = fields


class Schema(MutableMapping, metaclass=MetaSchema):
    """
    The base class to all schemas. its role is to hold data.
    """

    def __init__(self, *args, **kwargs):
        if args and len(args) == 1:
            self._data = dict(args[0])
        else:
            self._data = kwargs

        for name in self.required_fields():
            field = self.fields[name]

            if name not in self._data:
                if not field.default:
                    raise SchemaError("required field must be filled")

                self._data[name] = field.default

    # Classmethods

    @classmethod
    def __fields__(cls):
        return dict()

    @classmethod
    def required_fields(cls):
        return filter(lambda name: cls.fields[name].required, cls.fields)

    # Mixins

    def __len__(self):
        return len(self._data)

    def __contains__(self, name):
        return name in self._data

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise KeyError("No '{}' field".format(name))

    def __setitem__(self, name, value):
        if name in self.fields:
            if value is not None:
                self._data[name] = value
            else:
                raise SchemaError("A field can not be set to None")
        else:
            raise KeyError("No '{}' field".format(name))

    def __delitem__(self, name):
        if self.fields[name].required:
            msg = "'{}' required field can not be deleted".format(name)
            raise SchemaError(msg)

        del self._data[name]


    # Validation
    
    def is_valid(self):
        return all(self.fields[name].is_valid(self[name]) for name in self)


class DrivedMixin:

    @property
    def key(self):
        return self.meta.key

    @classmethod
    @coroutine
    def load(cls, key):
        entry = yield cls.driver.load(key, cls)
        return entry

    @coroutine
    def reload(self):
        yield self.driver.reload(self)

    @coroutine
    def store(self):
        if not self.is_valid():
            raise SchemaError("Schema not valid")

        yield self.driver.store(self)

    @coroutine
    def remove(self):
        yield self.driver.remove(self)


def drived(driver):
    def decorator(cls):
        assert isinstance(driver, Driver)
        assert issubclass(cls, Schema)
        assert not issubclass(cls, DrivedMixin)

        drived_class = new_class(cls.__name__, (cls, DrivedMixin))
        drived_class.driver = driver

        return drived_class
    return decorator
