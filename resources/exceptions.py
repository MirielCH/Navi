#exceptions.py
"""Contains custom exceptions"""


class NoArgumentsError(ValueError):
    """Custom exception for when no arguments are passed to a function"""
    pass


class MissingArgumentsError(ValueError):
    """Custom exception for when an expected argument is missing in a function"""
    pass


class NoDataFoundError(Exception):
    """Custom exception for when no data is returned from the database"""
    pass


class RecordExistsError(Exception):
    """Custom exception for when a database record is supposed to be deleted but is not"""
    pass


class FirstTimeUserError(Exception):
    """Custom exception for when no user record is found in the database"""
    pass


class InvalidTimestringError(ValueError):
    """Custom exception for when a timestring is not valid."""
    pass


class NoClanLeaderFoundError(Exception):
    """Custom exception for when a clan has no leader in the database."""
    pass