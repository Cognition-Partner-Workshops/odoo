""" PostgreSQL adapter of the isolation interface.

The class and test lifecycle is the one of ``TransactionCase`` (class cursor,
flushing savepoint per test, rollback, cache layers), ported from
``odoo/tests/common.py``. Explicit transactions are real cursors on their own
connection, never ``TestCursor``.
"""
from __future__ import annotations

import logging
import traceback
import typing
from collections import deque
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from unittest.mock import patch

import psycopg2
from passlib.context import CryptContext

import odoo.exceptions
from odoo import api
from odoo.modules.registry import Registry
from odoo.orm.environments import CacheLayer
from odoo.sql_db import PG_CONCURRENCY_EXCEPTIONS_TO_RETRY
from odoo.tests.common import _registry_test_lock
from odoo.tests.test_cursor import TestCursor
from odoo.tools import mute_logger

from .isolation import Transaction

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from odoo.api import Environment
    from odoo.models import BaseModel
    from odoo.sql_db import Cursor

_logger = logging.getLogger(__name__)


def _reset_registry(registry, *, registry_sequence, caches):
    registry.registry_sequence = registry_sequence
    registry.registry_caches__ = caches


def _reset_callbacks(callbacks, funcs, data):
    callbacks._funcs = funcs
    callbacks.data = data


def _forbidden(*args, **kwargs):
    traceback.print_stack()
    message = (
        "Cannot commit or rollback the transaction of a neutral test; "
        "use independent_transaction() or concurrent_session() instead"
    )
    raise AssertionError(message)


def _crypt_context(self):  # noqa: ARG001
    # speedup CryptContext, see TransactionCase.setUpClass
    cryptCtx = CryptContext(['pbkdf2_sha512', 'plaintext'], pbkdf2_sha512__rounds=1)
    originalVerifyAndUpdate = cryptCtx.verify_and_update

    def verify_and_update(*args, **kwargs):
        valid, _replacementHash = originalVerifyAndUpdate(*args, **kwargs)
        return valid, None

    cryptCtx.verify_and_update = verify_and_update
    return cryptCtx


class PostgresqlIsolation:
    name = 'postgresql'

    integrity_errors = psycopg2.IntegrityError
    concurrency_errors = (*PG_CONCURRENCY_EXCEPTIONS_TO_RETRY, odoo.exceptions.ConcurrencyError)

    #: how long a transaction of the harness waits for a lock before it
    #: fails with LockNotAvailable, in milliseconds
    lock_timeout = 2000

    def __init__(self):
        self._registry: Registry | None = None
        self._env: Environment | None = None
        self._savepoint = None
        self._classStack: ExitStack | None = None
        self._testStack: ExitStack | None = None
        # (model name, ids) to unlink and commit, per scope
        self._classFixtures: list[tuple[str, list[int]]] = []
        self._testFixtures: list[tuple[str, list[int]]] | None = None
        # cursors of the explicit transactions that are still open
        self._openCursors: list[Cursor] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def class_setup(self, dbname: str) -> Environment:
        assert self._classStack is None, "class_setup() called twice"
        self._registry = registry = Registry(dbname)

        def signal_changes(cr, names):  # noqa: ARG001
            if 'registry' in names:
                if not registry.ready:
                    return
                registry.registry_sequence += 1
                for key, (seq, _data) in registry.registry_caches__.items():
                    registry.registry_caches__[key] = (seq + 1, {})
            else:
                for name in names:
                    registry.registry_caches__[name] = (registry.registry_caches__[name][0] + 1, {})

        def get_sequences(cr):  # noqa: ARG001
            return registry.registry_sequence, {name: val[0] for name, val in registry.registry_caches__.items()}

        with ExitStack() as stack:
            stack.callback(
                _reset_registry, registry,
                registry_sequence=registry.registry_sequence,
                caches=registry.registry_caches__.copy(),
            )
            stack.enter_context(patch.object(registry, '_signal_changes', signal_changes))
            stack.enter_context(patch.object(registry, 'get_sequences', get_sequences))
            stack.callback(self._gc_filestore)
            # after the class cursor is closed, so that it holds no lock on them
            stack.callback(self._remove_committed, self._classFixtures)

            cr = registry.cursor()
            assert not isinstance(cr, TestCursor), "the class cursor must be a real cursor"
            stack.callback(cr.close)
            self._set_lock_timeout(cr, local=True)

            for method in ('commit', 'rollback', 'close'):
                stack.enter_context(patch.object(cr, method, _forbidden))

            env = api.Environment(cr, api.SUPERUSER_ID, {})
            env.transaction._wrote__ = True  # isolate tests: avoid propagating cache on rollback

            stack.enter_context(patch(
                'odoo.addons.base.models.res_users.ResUsersPatchedInTest._crypt_context',
                _crypt_context,
            ))
            self._classStack = stack.pop_all()

        self._env = env
        return env

    def class_teardown(self) -> None:
        stack, self._classStack = self._classStack, None
        if stack is None:
            return
        try:
            self._close_open_cursors()
        finally:
            stack.close()
            self._savepoint = None
            self._env = None

    def test_setup(self, env: Environment) -> None:
        assert self._testStack is None, "test_setup() called twice"
        registry = self._registry
        cr = env.cr

        with ExitStack() as stack:
            stack.callback(
                # for flushing cursor
                _reset_registry, registry,
                registry_sequence=registry.registry_sequence,
                caches=registry.registry_caches__.copy(),
            )
            self._testFixtures = testFixtures = []
            stack.callback(setattr, self, '_testFixtures', None)
            # after the rollback of the test, so that it holds no lock on them
            stack.callback(self._remove_committed, testFixtures)
            stack.callback(self._close_open_cursors)
            stack.callback(self._check_registry_lock)

            if self._savepoint is None:
                # flush everything of the class setup before the savepoint,
                # which is shared by the tests and released at class teardown
                self._savepoint = savepoint = cr.savepoint(flush=True)
                self._classStack.callback(savepoint.close, rollback=False)

            # This prevents precommit functions and data from piling up
            # until the cursor is flushed in 'assertRaises' clauses
            for callbacks in (cr.precommit, cr.postcommit, cr.prerollback, cr.postrollback):
                stack.callback(_reset_callbacks, callbacks, deque(callbacks._funcs), deepcopy(callbacks.data))

            stack.callback(self._savepoint.rollback)

            # To keep tests isolated, add a CacheLayer (see TransactionCase.setUp)
            transaction = env.transaction
            for name, layer in transaction.ormcaches__.items():
                transaction.ormcaches__[name] = CacheLayer(layer)

            self._testStack = stack.pop_all()

    def test_teardown(self, env: Environment) -> None:  # noqa: ARG002
        stack, self._testStack = self._testStack, None
        if stack is not None:
            stack.close()

    @staticmethod
    def _check_registry_lock():
        if _registry_test_lock.count != 1:
            _logger.warning(
                "The registry test lock count is %s instead of 1 at the end of a neutral test",
                _registry_test_lock.count,
            )

    def _gc_filestore(self):
        # attachments can be created or unlinked during the tests, and the
        # crons do not run: collect the filestore outside of the class cursor
        with self._registry.cursor() as cr:
            api.Environment(cr, api.SUPERUSER_ID, {})['ir.attachment']._gc_file_store_unsafe(grace_period=0)

    # ------------------------------------------------------------------
    # Explicit transactions
    # ------------------------------------------------------------------

    def _set_lock_timeout(self, cr: Cursor, *, local: bool = False):
        # `local` lasts until the end of the transaction, which is the whole
        # life of the class cursor; a session setting must be committed, or
        # the first rollback of the transaction would undo it
        if local:
            cr.execute("SET LOCAL lock_timeout = %s", [self.lock_timeout])
        else:
            cr.execute("SET lock_timeout = %s", [self.lock_timeout])
            cr.commit()

    @contextmanager
    def _session(self) -> Generator[Transaction]:
        cr = self._registry.cursor()
        try:
            # inside `registry_test_mode` this would be a TestCursor that
            # wraps the connection of the class cursor: no real transaction
            assert not isinstance(cr, TestCursor), "an explicit transaction needs a real cursor"
            self._openCursors.append(cr)
            self._set_lock_timeout(cr)
            env = api.Environment(cr, api.SUPERUSER_ID, {})
            yield Transaction(env, commit=cr.commit, rollback=cr.rollback)
        finally:
            self._close_cursor(cr)

    def _close_cursor(self, cr):
        if cr in self._openCursors:
            self._openCursors.remove(cr)
        if not cr.closed:
            # closing rolls back what was not committed; the connection is
            # reset when it goes back to the pool, which drops the timeout
            cr.close()

    def _close_open_cursors(self):
        for cr in reversed(self._openCursors[:]):
            _logger.warning("An explicit transaction was still open at the end of a neutral test, closing it")
            self._close_cursor(cr)

    def independent_transaction(self):
        return self._session()

    def concurrent_session(self):
        # a PostgreSQL connection is already a session of its own
        return self._session()

    # ------------------------------------------------------------------
    # Error surfacing
    # ------------------------------------------------------------------

    def mute_backend_logs(self):
        return mute_logger('odoo.sql_db')

    # ------------------------------------------------------------------
    # Committed fixtures
    # ------------------------------------------------------------------

    def committed_fixture(self, make: Callable[[Environment], BaseModel]) -> BaseModel:
        with self._session() as transaction:
            records = make(transaction.env)
            transaction.commit()
            self.track_committed(records)
            return self._env[records._name].browse(records.ids)

    def track_committed(self, records: BaseModel) -> None:
        fixtures = self._classFixtures if self._testFixtures is None else self._testFixtures
        fixtures.append((records._name, list(records.ids)))

    def _remove_committed(self, fixtures: list[tuple[str, list[int]]]):
        """ Unlink the given fixtures, last made first, in committed transactions. """
        errors = []
        while fixtures:
            modelName, ids = fixtures.pop()
            try:
                with self._session() as transaction:
                    transaction.env[modelName].browse(ids).exists().unlink()
                    transaction.commit()
            except Exception as error:  # noqa: BLE001
                _logger.error("Could not remove the committed fixture %s%s", modelName, ids)
                errors.append(error)
        if errors:
            raise errors[0]
