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

		
from uzu.db.fields import Field

from uzu.db.errors import ModelError, ModelFieldError


class MetaModel(type):
	"""The metaclass for models"""

	def __new__(mcls, name, bases, attrs):
		new_attrs = {}

		fields = {}

		# Adds the base models' fields to the new model
		if name != "Model":
			for base in bases:
				if (issubclass(base, Model)):
					fields.update(base._fields)

		# Populate the new_attr variable
		for name, value in attrs.items():
			# Populate the fields variable
			if (isinstance(value, Field)):
				fields[name] = attrs[name]

				fields[name]._display.setdefault("name", name)
				fields[name]._display.setdefault("name_plural", name + 's')

			else:
				new_attrs[name] = attrs[name]

		new_attrs["_fields"] = fields

		return type.__new__(mcls, name, bases, new_attrs)


class Model(object, metaclass=MetaModel):
	"""Base class for models"""

	def __init__(self, **kwargs):
		"""
		Create the model an fill its fields with keyword arguments. All the
		argument passed to this constructor must have their name precised.
		Ommitted fields are set to the default value of their field.

		Usage example:
			u = User(name="Thomas", age=22)

		Arguments:
			kwargs: The keywords additionnal argument contains the values to
			        fill the model's fields with.

		Raises:
			ValueError: if a required field with no default value is not in the
			            keywords additionnals arguments.
		"""

		# Populate the instance with kwargs data
		for name, field in self._fields.items():
			if field.required and field.default is None:
					if name in kwargs:
						setattr(self, name, kwargs[name])
					else:
						raise ModelFieldError(
							name,
							"A {name} field is required"
						)
			
			else:
				setattr(self, name, kwargs.get(name, field.default))


	def __repr__(self):
		model_name = self.__class__.__name__

		fields = ("{}: {}".format(name, value) for name, value in self.items())

		return "<{} ".format(model_name)  + ", ".join(fields) + ">"

	def __delattr__(self, name):
		"""Forbid the deletion of fields values."""
		if name in self._fields:
			raise ModelFieldError(
				name,
				"'{name}' attribute is a field value and can not be deleted."
			)
		else:
			super().__delattr__(name)

	#=================#
	# Sized interface #
	#=================#

	def __len__(self):
		"""Return the number of fields of this model."""
		return len(self._fields)

	#=====================#
	# Container interface #
	#=====================#

	def __contains__(self, name):
		"""Verify if this model has a field named name."""
		return name in self._fields

	#====================#
	# Iterable interface #
	#====================#

	def __iter__(self):
		"""Return an iterator over the model fields' names."""
		return self.keys()

	#===================#
	# Mapping interface #
	#===================#

	def __getitem__(self, name):
		"""
		Allow to get fields values using the Mapping interface.

		Raises:
			KeyError: if there is no field named `name`.
		"""
		if name in self._fields:
			return getattr(self, name)
		else:
			raise ModelFieldError(name, "No '{name}' field")

	def __setitem__(self, name, value):
		"""
		Allow to set fields values using the Mapping interface.

		Raises:
			KeyError: if there is no field named `name`.
			ValueError: if the field to fill is required an the value is None.
		"""
		if name in self._fields:
			if not (self._fields[name].required and value is None):
				setattr(self, name, value)
			else:
				raise ValueError("A required field can not be filled with None")
		else:
			raise ModelFieldError(name, "No '{name}' field")

	def __delitem__(self, name):
		"""Forbid the deletion of fields values using the Mapping interface."""
		raise ModelFieldError(
			name,
			"'{name}' is a field value and can not be deleted."
		)

	def items(self):
		"""Returns an iterator on a fields name and value pair."""
		for name in self._fields.keys():
			yield (name, getattr(self, name))

	def keys(self):
		"""Return an iterator on fields names."""
		for name in self._fields.keys():
			yield name

	def values(self):
		"""Return an iterator on fields values."""
		for name in self._fields.keys():
			yield getattr(self, name)

	#=========#
	# Methods #
	#=========#

	def is_valid(self):
		"""Validate a model if all its fields values are valid."""
		return all(
			field.is_valid(getattr(self, name))
			for name, field in self._fields.items()
		)
