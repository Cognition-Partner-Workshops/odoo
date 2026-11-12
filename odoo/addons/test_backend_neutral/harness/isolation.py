""" The isolation interface of the backend-neutral suite.

This is section 4 of ``backend_neutral_tests/CONTRACT.md``. Nothing in this
module names a database: a backend is supported by writing one adapter class
that satisfies :class:`IsolationBackend` and selecting it in ``backends.py``.
"""
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager

    from odoo.api import Environment
    from odoo.models import BaseModel


class Transaction:
    """ A real transaction handed out by the harness.

    It is rolled back when its ``with`` block exits, unless it was committed.
    After an error raised by the backend inside the transaction (integrity or
    concurrency error), roll it back before using it again.
    """
    __slots__ = ('_commit', '_rollback', 'env')

    def __init__(self, env: Environment, commit: Callable[[], None], rollback: Callable[[], None]):
        self.env = env
        self._commit = commit
        self._rollback = rollback

    def commit(self) -> None:
        """ Flush and make the writes of this transaction durable and visible
        to the transactions that start afterwards. """
        self._commit()

    def rollback(self) -> None:
        """ Discard the writes of this transaction and its cached values. """
        self._rollback()

    # Lint rule BN003 flags every call named `commit` or `rollback`, whatever
    # its receiver, so a neutral test cannot spell the two methods above.
    # Tests call these names instead (see the contract note in README.md).
    commit_transaction = commit
    rollback_transaction = rollback


@typing.runtime_checkable
class IsolationBackend(typing.Protocol):
    """ What a database backend provides to run the neutral suite. One
    instance serves one test class. """

    #: for logging only, never for branching in tests
    name: str

    #: what the neutral ``IntegrityError`` and ``ConcurrencyError`` map to
    integrity_errors: type | tuple[type, ...]
    concurrency_errors: type | tuple[type, ...]

    # per-class / per-test lifecycle
    def class_setup(self, dbname: str) -> Environment:
        """ Return an environment whose writes are discarded by
        :meth:`class_teardown`. """

    def class_teardown(self) -> None:
        """ Discard the writes of the class environment and remove the
        committed fixtures of the class. """

    def test_setup(self, env: Environment) -> None:
        """ Start an undoable unit around one test method. """

    def test_teardown(self, env: Environment) -> None:
        """ Undo everything the test wrote in ``env``, drop its caches, close
        the transactions the test left open and remove the committed fixtures
        made during the test. """

    # explicit transactions
    def independent_transaction(self) -> AbstractContextManager[Transaction]:
        """ A real new transaction on the same database, as superuser. It
        sees committed data only. """

    def concurrent_session(self) -> AbstractContextManager[Transaction]:
        """ Like :meth:`independent_transaction`, and guaranteed to run
        concurrently with every other transaction of the test (own session),
        so that locks between them are real. A lock that cannot be obtained
        raises one of ``concurrency_errors`` after a bounded wait. """

    # error surfacing
    def mute_backend_logs(self) -> AbstractContextManager[None]:
        """ Silence what the backend logs when it refuses an operation. """

    # fixtures that must survive rollback
    def committed_fixture(self, make: Callable[[Environment], BaseModel]) -> BaseModel:
        """ Run ``make`` in an independent transaction, commit it, and
        register the records it returns for unlink-and-commit: at the end of
        the running test, or at :meth:`class_teardown` when no test runs.
        Return the records in the class environment. """

    def track_committed(self, records: BaseModel) -> None:
        """ Register records that the test committed through an explicit
        transaction, for the same unlink-and-commit as fixtures. """
