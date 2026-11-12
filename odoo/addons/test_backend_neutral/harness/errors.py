""" Neutral names of the exceptions a neutral test may expect.

This is section 3 of ``backend_neutral_tests/CONTRACT.md``. Tests import
exceptions from here only. ``IntegrityError`` and ``ConcurrencyError`` are
what ``assertRaises`` accepts (a class or a tuple of classes); use
``NeutralCase.assertIntegrityError()`` and ``assertConcurrencyError()``
rather than ``assertRaises`` with them.
"""
from odoo.exceptions import (
    AccessError,
    LockError,
    MissingError,
    UserError,
    ValidationError,
)

from .backends import ACTIVE_BACKEND

#: the backend refused a write because of a declared constraint: unique,
#: check, not-null, foreign key restrict. One alias for all four kinds; it
#: does not accept ValidationError.
IntegrityError = ACTIVE_BACKEND.integrity_errors

#: another transaction holds a lock, or the transaction must be retried.
#: LockError (raised by `lock_for_update`) is not part of it.
ConcurrencyError = ACTIVE_BACKEND.concurrency_errors

__all__ = [
    'AccessError',
    'ConcurrencyError',
    'IntegrityError',
    'LockError',
    'MissingError',
    'UserError',
    'ValidationError',
]
