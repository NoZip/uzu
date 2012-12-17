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

from uzu.db.errors import FieldError


class Field(object):
	"""
	The base class for other fields.

	Attributes:
		required: A boolean that indicate if the field is required.
		default: The default value of this field.
		display: properties used to display the field.
	"""

	def __init__(self, required=False, default=None, display={}):
		self._required = required
		self._default = default
		self._display = display

	@property
	def required(self):
		return self._required

	@property
	def default(self):
		return self._default

	@property
	def display(self):
		return self._display

	def _required_test(self, value):
		return not self._required and value is None

	def is_valid(self, value):
		"""
		Test if the field is required and filled.
		Do not test anything if the field is not required
		"""
		return self._required_test(value)


#================#
# Numeric Fields #
#================#

class NumericField(Field):
	"""
	An abstract numeric field.
	In the child classes a class argument `_type`, that indicate the field's
	numeric type, must be present.

	Attributes:
		min: the minimum value of the field.
		max: the maximum value of the field.
	"""

	def __init__(self, min=None, max=None, **kwargs):
		super().__init__(**kwargs)

		self._min = min
		self._max = max

	@property
	def min(self):
		return self._min

	@property
	def max(self):
		return self._max

	def _range_test(self, value):
		min_test = (
			self._min is None
			or (self._min is not None and (self._min < value))
		)

		max_test = (
			self._max is None
			or (self._max is not None and (value < self._max))
		)

		return min_test and max_test

	def is_valid(self, value):
		return (
			self._required_test(value)
			or (
				isinstance(value, self._type)
				and self._range_test(value)
			)
		)

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
		max_length:	maximum length of the field's value.
		pattern: a pattern used to check the field's value
	"""

	def __init__(self, min_length=None,
		               max_length=None,
		               pattern=None,
		               **kwargs):
		super().__init__(**kwargs)

		self._min_length = min_length
		self._max_length = max_length

		if pattern:
			if (isinstance(pattern, str)):
				self._pattern = re.compile(pattern)
			# elif (isinstance(pattern, re.regex)):
			# 	self._pattern = pattern
			else:
				raise FieldError("Invalid type for the 'pattern' argument")
		else:
			self._pattern = None

	def min_length(self):
		return self._min_length

	def max_length(self):
		return self._max_length

	def pattern(self):
		return self._pattern

	def _length_test(self, value):
		min_length_test = (
			self._min_length is None
			or (
				self._min_length is not None
				and (self._min_length < len(value))
			)
		)

		max_length_test = (
			self._max_length is None
			or (
				self._max_length is not None
				and (len(value) < self._max_length)
			)
		)

		return min_length_test and max_length_test

	def _pattern_test(self, value):
		return (
			self._pattern is None
			or (
				self._pattern is not None
				and bool(self._pattern.match(value))
			)
		)

	def is_valid(self, value):
		return (
			self._required_test(value)
			or (
				isinstance(value, str)
				and self._length_test(value)
				and self._pattern_test(value)
			)
		)


#======================#
# Date and Time Fields #
#======================#

class DateTimeField(Field):
	"""
	A date and time field

	Attributes:
		auto_now: fill the field with the current date by default.
		utc: toggle the use of utc time instead of local time.
	"""

	def __init__(self, auto_now=False, utc=False, **kwargs):
		super().__init__(**kwargs)

		if auto_now:
			del self._default

		self._auto_now = auto_now
		self._utc = utc

	@property
	def default(self):
		"""
		Overriding of the Field#default property in order to handle auto_now.
		"""
		if not self._auto_now:
			return self._default
		else:
			if not self._utc:
				return datetime.now()
			else:
				return datetime.now(timezone.utc)

	@property
	def auto_now(self):
		return self._auto_now

	@property
	def utc(self):
		return self._utc

	def _utc_test(self, value):
		return (
			not self._utc
			or (self._utc and value.tzinfo == timezone.utc)
		)

	def is_valid(self, value):
		return (
			self._required_test(value)
			or (isinstance(value, datetime) and self._utc_test(value))
		)


#==================#
# Composite Fields #
#==================#

class ListField(Field):
	"""
	A list field.

	Attributes:
		field: the type of the fields in this list field.
	"""
	def __init__(self, field, **kwargs):
		super().__init__(**kwargs)

		if not isinstance(field, Field):
			raise FieldError("'field' argument must be a Field instance")

		self._field = field

	@property
	def field(self):
		return self._field

	def is_valid(self, value):
		return (
			self._required_test(value)
			or (
				isinstance(value, Sequence)
				and all(self.field.is_valid(v) for v in value)
			)
		)
