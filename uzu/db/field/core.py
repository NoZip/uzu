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

import re

from datetime import datetime, timezone
from collections import Sequence, Mapping


class FieldError(Exception):
    pass


class Field(object):
    """
    The base class for other fields.

    Attributes:
        required: A boolean that indicate if the field is required.
        default: The default value of this field.
    """

    def __init__(self, required=False, default=None):
        self.required = required
        self.default = default

    def _required_test(self, value):
        return not (self.required and value is None)

    def _type_test(self, value):
        return isinstance(value, self._type)

    def is_valid(self, value):
        """
        Test if the field is required and filled.
        Do not test anything if the field is not required
        """
        return self._required_test(value) and self._type_test(value)


#================#
# Numeric Fields #
#================#

class NumericField(Field):
    """
    An abstract numeric field.

    Attributes:
        min: the minimum value of the field.
        max: the maximum value of the field.
    """

    def __init__(self, min=None, max=None, **kwargs):
        super().__init__(**kwargs)

        self.min = min
        self.max = max

    def _range_test(self, value):
        min_test = (
            self.min is None
            or (self.min is not None and (self.min < value))
        )

        max_test = (
            self.max is None
            or (self.max is not None and (value < self.max))
        )

        return min_test and max_test

    def is_valid(self, value):
        return super().is_valid(value) and self._range_test(value)

class IntegerField(NumericField):
    """An integer field."""

    _type = int


class FloatField(NumericField):
    """A float field."""

    _type = float


#===============#
# String Fields #
#===============#

class StringField(Field):
    """
    A string field

    Attributes:
        min_length: minimum length of the field's value.
        max_length: maximum length of the field's value.
        pattern: a pattern used to check the field's value
    """

    _type = str

    def __init__(
        self,
        min_length=None,
        max_length=None,
        pattern=None,
        multiline=False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.min_length = min_length
        self.max_length = max_length

        if pattern:
            if (isinstance(pattern, str)):
                self.pattern = re.compile(pattern)
            # TODO: regex pattern case.
            # elif (isinstance(pattern, re.regex)):
            #   self.pattern = pattern
            else:
                raise FieldError("Invalid type for the 'pattern' argument")
        else:
            self.pattern = None

        self.multiline = multiline

    def _length_test(self, value):
        min_length_test = (
            self.min_length is None
            or (
                self.min_length is not None
                and (self.min_length < len(value))
            )
        )

        max_length_test = (
            self.max_length is None
            or (
                self.max_length is not None
                and (len(value) < self.max_length)
            )
        )

        return min_length_test and max_length_test

    def _pattern_test(self, value):
        return (
            self.pattern is None
            or (
                self._pattern is not None
                and bool(self._pattern.match(value))
            )
        )

    def is_valid(self, value):
        return (
            super().is_valid(value)
            and (self._length_test(value) and self._pattern_test(value))
        )


#======================#
# Date and Time Fields #
#======================#

class DateTimeField(Field):
    """
    A date and time field

    Attributes:
        auto_now: fill the field with the current date by default.
    """

    _type = datetime

    def __init__(self, auto_now=False, **kwargs):
        super().__init__(**kwargs)

        self.auto_now = auto_now

    @property
    def default(self):
        if self.auto_now:
            return datetime.now(timezone.utc)
        else:
            return self._default

    @default.setter
    def default(self, value):
        self._default = value


#==================#
# Composite Fields #
#==================#

class ListField(Field):
    """
    A list field.

    Attributes:
        field: the type of the fields in this list field.
    """

    _type = list

    def __init__(self, field, **kwargs):
        kwargs.setdefault("default", [])

        super().__init__(**kwargs)

        if not isinstance(field, Field):
            raise FieldError("'field' argument must be a Field instance")

        self.field = field

    def is_valid(self, value):
        return (
            super().is_valid()
            and all(self.field.is_valid(v) for v in value)
        )
