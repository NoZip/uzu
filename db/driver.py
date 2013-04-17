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


class DBDriver(metaclass=ABCMeta):
    """
    The base class for all drivers.
    """

    special_fields = {} # database build-in fields

    def __init__(self, model):
        self._model = model

    @abstractmethod
    def load(self, id):
        """
        Loads the entry in database identified with `id`.
        """
        raise NotImplementedError

    @abstractmethod
    def store(self, entry):
        """
        Store an entry in the database.
        """
        raise NotImplementedError
