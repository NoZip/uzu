
class Error(Exception):
	"""Base exception for db module errors"""
	pass

class FieldError(Error):
	"""Exception to handle fields errors"""
	pass

class ModelError(Error):
	"""Exception to handle models errors"""
	pass

class ModelFieldError(FieldError):
	"""Exception to handle models fields errors"""
	def __init__(self, name, message):
		self.name = name
		self.message = message

	def __str__(self):
		return self.message.format(name=self.name)