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

from struct import Struct

class StructureBase:

	__slots__ = ()

	def __init__(self, *args, **kwargs):
		if args:
			assert(len(args) == len(self.__slots__))
			for n, field in enumerate(self.__slots__):
				setattr(self, field, args[n])

		else:
			for field in self.__slots__:
				setattr(self, field, kwargs.get(field, None))

	def __iter__(self):
		for field in self.__slots__:
			yield getattr(self, field)

	def to_dict(self):
		return {field: getattr(self, field) for field in self.__slots__}

	__dict__ = property(to_dict)

	def __repr__(self):
		return repr(self.to_dict())


class PackableStructureBase(StructureBase):

	__slots__ = ()

	def pack(self):
		return self._packer.pack(*self)

	@classmethod
	def unpack(cls, data):
		return cls(*cls._packer.unpack(data))


def structure(name, fields):
	attrs = {
		"__slots__" : tuple(fields)
	}

	return type(name, (StructureBase,), attrs)

def packable_structure(name, fields, format):
	attrs = {
		"__slots__" : tuple(fields),
		"_packer" : Struct(format)
	}

	return type(name, (PackableStructureBase,), attrs)


if __name__ == "__main__":
	import sys
	Point = structure("Point", ("x", "y"))
	p = Point(1, 2)
	print(p)
	print(sys.getsizeof(p))


