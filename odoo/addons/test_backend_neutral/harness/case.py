""" Base classes of the backend-neutral suite.

A neutral test observes the ORM only: records, field values and the classes
of the exceptions raised. Everything that depends on the database behind the
ORM is asked to the isolation backend (see ``isolation.py``).
"""
from __future__ import annotations

import functools
import typing
from contextlib import contextmanager

from odoo.tests.common import TransactionCase, get_db_name, tagged

from . import errors
from .backends import new_backend

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from odoo.api import Environment
    from odoo.models import BaseModel

    from .isolation import IsolationBackend, Transaction

#: the tag that selects the neutral suite: `--test-tags backend_neutral`
NEUTRAL_TAG = 'backend_neutral'


class _ClassOrInstanceMethod:
    """ Method bound to the test case when called on one, and to its class
    otherwise (in ``setUpClass``). """

    def __init__(self, function):
        self.function = function
        self.__doc__ = function.__doc__

    def __get__(self, instance, owner=None):
        return functools.partial(self.function, owner if instance is None else instance)


class _NotNeutral:
    """ Attribute of ``TransactionCase`` that a neutral test may not use. """

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            # class-level access: `inspect.getmembers(cls)`, used by Odoo's
            # loader for `allow_inherited_tests_method`, must not raise
            return self
        raise NotImplementedError(f"{self.name}: not available in a neutral test")


@tagged(NEUTRAL_TAG, 'post_install', '-at_install')
class NeutralCase(TransactionCase):
    """ Test case whose methods each run in a unit of work that is undone at
    the end of the method, like ``TransactionCase``, without exposing how the
    backend does it. """

    backend: IsolationBackend
    env: Environment

    # not part of the neutral surface: fail even when the lint is skipped
    cr = _NotNeutral()
    registry = _NotNeutral()
    cursor = _NotNeutral()
    assertQueries = _NotNeutral()
    assertQueryCount = _NotNeutral()
    registry_test_mode = _NotNeutral()

    @classmethod
    def setUpClass(cls):
        # skip TransactionCase.setUpClass(): the backend provides what it does
        super(TransactionCase, cls).setUpClass()
        cls.backend = new_backend()
        cls.addClassCleanup(cls.backend.class_teardown)
        cls.env = cls.backend.class_setup(get_db_name())
        if cls.freeze_time:
            cls.startClassPatcher(cls.freeze_time)

    def setUp(self):
        # skip TransactionCase.setUp(): the backend provides what it does
        super(TransactionCase, self).setUp()
        classEnv = type(self).env
        self.addCleanup(self.backend.test_teardown, classEnv)
        self.backend.test_setup(classEnv)

    # ------------------------------------------------------------------
    # Explicit transactions
    # ------------------------------------------------------------------

    @contextmanager
    def _as_test_user(self, transactions) -> Generator[Transaction]:
        with transactions as transaction:
            transaction.env = transaction.env(user=self.env.uid, context=dict(self.env.context))
            yield transaction

    def independent_transaction(self):
        """ Context manager of a real new transaction on the database, with
        the user and context of ``self.env``. It sees committed data only,
        and it is rolled back on exit unless committed. """
        return self._as_test_user(self.backend.independent_transaction())

    def concurrent_session(self):
        """ Context manager of a real new transaction that runs concurrently
        with the other transactions of the test: the locks between them are
        real, and a lock that cannot be obtained raises ``ConcurrencyError``
        after a bounded wait instead of blocking the test. """
        return self._as_test_user(self.backend.concurrent_session())

    @_ClassOrInstanceMethod
    def committed_fixture(self, make: Callable[[Environment], BaseModel]) -> BaseModel:
        """ Return the records made by ``make(env)`` in an independent
        transaction that is committed; ``env`` is a superuser environment.
        The records are unlinked, in a committed transaction as well, at the
        end of the test, or at the end of the class when this is called on
        the class in ``setUpClass``.

        The records are returned in ``self.env``, but whether the transaction
        of the test itself sees them is not specified: read and write them
        through explicit transactions, with ``records.with_env(transaction.env)``.
        """
        return self.backend.committed_fixture(make).with_env(self.env)

    @_ClassOrInstanceMethod
    def track_committed(self, records: BaseModel) -> None:
        """ Register records that were created and committed through an
        explicit transaction, to have them unlinked like committed fixtures. """
        self.backend.track_committed(records)

    # ------------------------------------------------------------------
    # Model registry
    # ------------------------------------------------------------------

    def patch_registry(self, attribute: str, value) -> None:
        """ Patch an attribute of the ORM's model registry (``ready``,
        ``uninstalling_modules``, ...) for the duration of the test. The
        registry is an ORM object, not a backend one, but tests may not reach
        it themselves (rule F3): they ask the harness. """
        self.patch(self.env.registry, attribute, value)

    # ------------------------------------------------------------------
    # Error surfacing
    # ------------------------------------------------------------------

    @contextmanager
    def _assertBackendError(self, expected):
        with self.backend.mute_backend_logs(), self.assertRaises(expected) as capture:
            yield capture

    def assertIntegrityError(self):
        """ Context manager asserting that the backend refuses a write
        because of a declared constraint, before the block exits. """
        return self._assertBackendError(errors.IntegrityError)

    def assertConcurrencyError(self):
        """ Context manager asserting that the block fails because another
        transaction holds a lock, or because it must be retried. """
        return self._assertBackendError(errors.ConcurrencyError)


class NeutralConcurrencyCase(NeutralCase):
    """ Neutral case whose own transaction is an independent transaction too.

    ``self.env`` belongs to a real transaction opened for each test method,
    so that it can be committed or rolled back with ``self.transaction``, and
    then sees what the other transactions committed. Nothing it commits is
    undone by the harness: make the records the transactions share with
    :meth:`committed_fixture`, also in ``setUpClass``, and register the
    records created and committed by the test with :meth:`track_committed`.
    """

    transaction: Transaction

    def setUp(self):
        super().setUp()
        self.transaction = self.enterContext(self.backend.independent_transaction())
        self.env = self.transaction.env
