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

from abc import ABCMeta, abstractmethod


class Driver(metaclass=ABCMeta):
	"""
	An Abstract class To rule all drivers.
	"""

	@abstractmethod
	def load(self, key, model):
		"""
		Fetch in database the entry referenced by "key" and return it.
		"""
		raise NotImplementedError

	@abstractmethod
	def reload(self, entry):
		"""
		Updates entry data.
		"""
		raise NotImplementedError

	@abstractmethod
	def store(self, entry):
		"""
		Store the entry in the database.
		"""
		raise NotImplementedError

	@abstractmethod
	def remove(self, entry):
		"""
		Remove the entry from database.
		"""
		raise NotImplementedError



