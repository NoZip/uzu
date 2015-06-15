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

from uzu.db.field.core import Field

class RelationField(Field):
    """
    Abstract relation field.
    """
    pass

class ForeignKeyField(RelationField):
    """
    A field that reference another entry by key.

    Attributes:
        schema: The schema class linked to the key.
    """

    _type = (DrivedMixin, Proxy)

    def __init__(self, schema, required=False, default=None):
        assert issubclass(schema, self._type)

        super().__init__(required=required, default=default)

        self.schema = schema
