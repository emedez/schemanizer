"""Exceptions"""

class Error(StandardError):
    """Base class for exceptions in this module."""
    pass


class PrivilegeError(Error):
    pass


class SchemaDoesNotMatchError(Error):

    def __init__(self, message, expected, actual, delta):
        super(SchemaDoesNotMatchError, self).__init__(
            message, expected, actual, delta)
        self.message = message
        self.expected = expected
        self.actual = actual
        self.delta = delta