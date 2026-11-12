from odoo.addons.test_backend_neutral.harness import NeutralCase, NeutralConcurrencyCase
from odoo.addons.test_backend_neutral.harness.errors import LockError

MODEL = 'test_backend_neutral.item'


def make_item(**values):
    """ Return a factory of one item, for ``committed_fixture()``. """
    return lambda env: env[MODEL].create({'name': 'Shared', **values})


class TestSmokeIndependentTransaction(NeutralCase):

    def test_sees_committed_data_only(self):
        uncommitted = self.env[MODEL].create({'name': 'Uncommitted', 'code': 'U'})
        self.env.flush_all()
        committed = self.committed_fixture(make_item(code='C'))

        with self.independent_transaction() as transaction:
            Item = transaction.env[MODEL]
            self.assertFalse(uncommitted.with_env(transaction.env).exists())
            self.assertFalse(Item.search([('code', '=', 'U')]))
            self.assertEqual(Item.search([('code', '=', 'C')]).ids, committed.ids)

    def test_rolled_back_unless_committed(self):
        item = self.committed_fixture(make_item(quantity=1))

        with self.independent_transaction() as transaction:
            item.with_env(transaction.env).quantity = 2
            transaction.env.flush_all()
        with self.independent_transaction() as transaction:
            self.assertEqual(item.with_env(transaction.env).quantity, 1)

        with self.independent_transaction() as transaction:
            item.with_env(transaction.env).quantity = 3
            transaction.commit_transaction()
            item.with_env(transaction.env).quantity = 4
            transaction.rollback_transaction()
            self.assertEqual(item.with_env(transaction.env).quantity, 3)
        with self.independent_transaction() as transaction:
            self.assertEqual(item.with_env(transaction.env).quantity, 3)

    def test_lock_of_the_test_blocks_other_session(self):
        # a record that every transaction sees
        partner = self.env.ref('base.partner_root')
        partner.lock_for_update()

        with self.concurrent_session() as other:
            with self.assertRaises(LockError):
                partner.with_env(other.env).lock_for_update()
            self.assertFalse(partner.with_env(other.env).try_lock_for_update())

    def test_blocked_test_fails_instead_of_hanging(self):
        partner = self.env.ref('base.partner_root')
        name = partner.name
        with self.concurrent_session() as other:
            partner.with_env(other.env).name = 'Held by the other session'
            other.env.flush_all()
            with self.assertConcurrencyError():
                partner.name = 'Blocked'
                self.env.flush_all()
        # the test goes on after the failure
        self.env.invalidate_all()
        self.assertEqual(partner.name, name)
        partner.name = 'Not blocked anymore'
        self.env.flush_all()

    def test_runs_as_the_user_of_the_test(self):
        user = self.env.ref('base.user_admin')
        self.env = self.env(user=user, context={'smoke': True})
        with self.independent_transaction() as transaction:
            self.assertEqual(transaction.env.user, user.with_env(transaction.env))
            self.assertEqual(transaction.env.context.get('smoke'), True)
            self.assertFalse(transaction.env.su)

    def test_committed_fixture_is_removed_first(self):
        self._check_fixture_removal()

    def test_committed_fixture_is_removed_second(self):
        self._check_fixture_removal()

    def _check_fixture_removal(self):
        """ The committed fixture of a test is unlinked at the end of the
        test: both tests make the same one, whichever runs first. """
        with self.independent_transaction() as transaction:
            self.assertFalse(transaction.env[MODEL].search([('code', '=', 'FIXTURE')]))
        self.committed_fixture(make_item(code='FIXTURE'))


class TestSmokeConcurrency(NeutralConcurrencyCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shared = cls.committed_fixture(make_item(code='SHARED', quantity=1))

    def test_lock_contention(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            mine = self.shared.with_env(first.env)
            theirs = self.shared.with_env(second.env)

            mine.lock_for_update()
            with self.assertRaises(LockError):
                theirs.lock_for_update()
            self.assertFalse(theirs.try_lock_for_update())

            # the lock is released with the transaction that holds it
            first.rollback_transaction()
            theirs.lock_for_update()
            with self.assertRaises(LockError):
                mine.lock_for_update()

    def test_write_contention(self):
        item = self.committed_fixture(make_item(quantity=1))

        with self.concurrent_session() as first, self.concurrent_session() as second:
            item.with_env(first.env).quantity = 2
            first.env.flush_all()

            # the second session waits for the first one, which does not end
            with self.assertConcurrencyError():
                item.with_env(second.env).quantity = 3
                second.env.flush_all()
            second.rollback_transaction()
            first.commit_transaction()

            # the second session can retry now, and sees the committed value
            theirs = item.with_env(second.env)
            self.assertEqual(theirs.quantity, 2)
            theirs.quantity = 5
            second.commit_transaction()

        with self.independent_transaction() as transaction:
            self.assertEqual(item.with_env(transaction.env).quantity, 5)

    def test_own_transaction_is_real(self):
        # it sees the committed fixture of the class
        self.assertEqual(self.shared.with_env(self.env).code, 'SHARED')

        created = self.env[MODEL].create({'name': 'Own', 'code': 'OWN'})
        self.env.flush_all()
        with self.concurrent_session() as other:
            self.assertFalse(other.env[MODEL].search([('code', '=', 'OWN')]))

        self.transaction.commit_transaction()
        self.track_committed(created)
        with self.concurrent_session() as other:
            self.assertEqual(other.env[MODEL].search([('code', '=', 'OWN')]).ids, created.ids)

    def test_own_transaction_sees_commits_once_restarted(self):
        item = self.committed_fixture(make_item(quantity=1))
        self.assertEqual(item.with_env(self.env).quantity, 1)

        with self.concurrent_session() as other:
            item.with_env(other.env).quantity = 2
            self.track_committed(other.env[MODEL].create({'name': 'Added', 'code': 'ADDED'}))
            other.commit_transaction()

        self.transaction.rollback_transaction()
        self.assertEqual(item.with_env(self.env).quantity, 2)
        self.assertTrue(self.env[MODEL].search([('code', '=', 'ADDED')]))
