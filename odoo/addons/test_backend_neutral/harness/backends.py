""" Selection of the isolation backend the neutral suite runs on.

This is the one place to change when another backend becomes available.
"""
from .isolation import IsolationBackend
from .postgresql import PostgresqlIsolation

#: the adapter class of the active backend
ACTIVE_BACKEND: type[IsolationBackend] = PostgresqlIsolation


def new_backend() -> IsolationBackend:
    """ Return a backend instance for one test class. """
    return ACTIVE_BACKEND()
