""" Concurrency and locking tests of the backend-neutral suite.

Every test drives two or more real transactions through the harness
(``concurrent_session()``) and asserts on outcomes only: which records could
be locked, which values are stored once every transaction has ended, which
exception class the loser of a conflict gets. How a backend spells its row
locks is never observed.

Sampled targets (``backend_neutral_tests/sample.yaml``, category
``concurrency``): ``concurrency.lock_for_update``, ``concurrency.ir_sequence``,
``concurrency.ir_cron``, ``concurrency.discuss_channel``, plus the stock quant
reservation and the "concurrent write to the same record" hypotheses of the
ticket.
"""
from contextlib import contextmanager
from datetime import timedelta

from odoo import fields

from odoo.addons.test_backend_neutral.harness import NeutralCase, errors
from odoo.addons.test_backend_neutral.harness.errors import LockError, UserError

ITEM = 'test_backend_neutral.item'


def _classes(spec):
    return spec if isinstance(spec, tuple) else (spec,)


def make_items(count, **values):
    """ Return a factory of ``count`` items, for ``committed_fixture()``. """
    return lambda env: env[ITEM].create([
        {'name': f'Item {index}', 'quantity': 10, **values} for index in range(count)
    ])


class ConcurrencyCase(NeutralCase):
    """ Helpers shared by the concurrency tests. """

    def read_committed(self, records, field_name):
        """ Return the stored value of ``field_name``, as seen by a transaction
        that starts now. """
        with self.independent_transaction() as transaction:
            return records.with_env(transaction.env).mapped(field_name)

    @contextmanager
    def assertRefused(self):
        """ Assert that the block fails because another transaction wrote
        the same thing first: either it must be retried, or the write
        violates a constraint once the other transaction is visible. """
        expected = (*_classes(errors.ConcurrencyError), *_classes(errors.IntegrityError))
        with self.backend.mute_backend_logs(), self.assertRaises(expected):
            yield


class TestRowLocks(ConcurrencyCase):
    """ concurrency.lock_for_update: ``lock_for_update`` / ``try_lock_for_update``. """

    def test_try_lock_returns_the_unlocked_subset(self):
        items = self.committed_fixture(make_items(3))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            mine = items.with_env(first.env)
            theirs = items.with_env(second.env)

            mine[0].lock_for_update()
            self.assertEqual(theirs.try_lock_for_update(), theirs[1:])
            # once locked by the second session, the records stay its own
            self.assertEqual(theirs.try_lock_for_update(), theirs[1:])
            self.assertEqual(theirs.try_lock_for_update(limit=1), theirs[1])

            # nothing is left for a third session
            with self.concurrent_session() as third:
                others = items.with_env(third.env)
                self.assertFalse(others.try_lock_for_update())
                self.assertFalse(others.try_lock_for_update(limit=2))
                with self.assertRaises(LockError):
                    others.lock_for_update()
                # a failed lock changes nothing
                self.assertEqual(others.mapped('quantity'), [10, 10, 10])
                self.assertEqual(others.exists(), others)

    def test_lock_keeps_the_order_of_the_records_with_limit(self):
        items = self.committed_fixture(make_items(4))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            items.with_env(first.env)[1].lock_for_update()
            reordered = items.with_env(second.env)
            reordered = reordered[3] | reordered[1] | reordered[0] | reordered[2]
            # the first two lockable records, in the order given
            self.assertEqual(reordered.try_lock_for_update(limit=2), reordered[0] | reordered[2])

    def test_lock_is_released_by_commit(self):
        item = self.committed_fixture(make_items(1))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            mine = item.with_env(first.env)
            mine.lock_for_update()
            mine.quantity = 11
            first.commit_transaction()

            theirs = item.with_env(second.env)
            theirs.lock_for_update()
            self.assertEqual(theirs.quantity, 11)
            self.assertEqual(theirs.try_lock_for_update(), theirs)

    def test_locked_record_stays_readable(self):
        item = self.committed_fixture(make_items(1, code='READABLE'))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            mine = item.with_env(first.env)
            mine.lock_for_update()
            mine.quantity = 99
            mine.env.flush_all()

            Item = second.env[ITEM]
            # readers see the committed values and are not blocked
            self.assertEqual(Item.search([('code', '=', 'READABLE')]).ids, item.ids)
            self.assertEqual(item.with_env(second.env).quantity, 10)
            self.assertEqual(Item.search_count([('code', '=', 'READABLE'), ('quantity', '=', 10)]), 1)

    def test_lock_allowing_references_lets_others_reference_the_record(self):
        parent = self.committed_fixture(make_items(1))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            parent.with_env(first.env).lock_for_update(allow_referencing=True)
            child = second.env[ITEM].create({'name': 'Child', 'parent_id': parent.id})
            second.commit_transaction()
            self.track_committed(child)
        with self.independent_transaction() as transaction:
            self.assertEqual(parent.with_env(transaction.env).child_ids.ids, child.ids)

    def test_lock_on_new_records_does_nothing(self):
        with self.concurrent_session() as session:
            new = session.env[ITEM].new({'name': 'Not stored'})
            new.lock_for_update()
            self.assertEqual(new.try_lock_for_update(), new)
            self.assertEqual(new.try_lock_for_update(limit=1), new)


class TestConcurrentWrites(ConcurrencyCase):
    """ Two transactions write the same record: the loser waits or gets a
    retryable error, and no update is lost once both have ended. """

    def test_writes_to_different_fields_both_persist(self):
        item = self.committed_fixture(make_items(1, code='BOTH'))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            item.with_env(first.env).name = 'Renamed by the first'
            first.env.flush_all()

            theirs = item.with_env(second.env)
            with self.assertConcurrencyError():
                theirs.quantity = 20
                theirs.env.flush_all()
            second.rollback_transaction()
            first.commit_transaction()

            theirs.quantity = 20
            second.commit_transaction()

        with self.independent_transaction() as transaction:
            stored = item.with_env(transaction.env)
            self.assertEqual(stored.name, 'Renamed by the first')
            self.assertEqual(stored.quantity, 20)
            self.assertEqual(stored.code, 'BOTH')

    def test_locked_read_modify_write_loses_no_increment(self):
        item = self.committed_fixture(make_items(1))

        def increment(transaction):
            record = item.with_env(transaction.env)
            record.lock_for_update()
            record.invalidate_recordset(['quantity'])
            record.quantity = record.quantity + 1

        with self.concurrent_session() as first, self.concurrent_session() as second:
            increment(first)
            # the second session cannot read-modify-write while the first holds the record
            with self.assertRaises(LockError):
                increment(second)
            second.rollback_transaction()
            first.commit_transaction()
            # retried after the commit, it builds on the committed value
            increment(second)
            second.commit_transaction()

        self.assertEqual(self.read_committed(item, 'quantity'), [12])

    def test_write_waits_for_a_lock_holder(self):
        item = self.committed_fixture(make_items(1))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            item.with_env(first.env).lock_for_update()
            theirs = item.with_env(second.env)
            with self.assertConcurrencyError():
                theirs.quantity = 1
                theirs.env.flush_all()
            second.rollback_transaction()
            first.rollback_transaction()
            theirs.quantity = 1
            second.commit_transaction()
        self.assertEqual(self.read_committed(item, 'quantity'), [1])

    def test_write_on_a_record_being_unlinked(self):
        item = self.committed_fixture(make_items(1))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            item.with_env(first.env).unlink()
            theirs = item.with_env(second.env)
            with self.assertConcurrencyError():
                theirs.quantity = 1
                theirs.env.flush_all()
            second.rollback_transaction()
            first.commit_transaction()
            self.assertFalse(theirs.exists())
            self.assertFalse(second.env[ITEM].search([('id', 'in', item.ids)]))

    def test_unlink_waits_for_a_writer(self):
        item = self.committed_fixture(make_items(1))
        with self.concurrent_session() as first, self.concurrent_session() as second:
            item.with_env(first.env).quantity = 5
            first.env.flush_all()
            with self.assertConcurrencyError():
                item.with_env(second.env).unlink()
            second.rollback_transaction()
            first.commit_transaction()
            item.with_env(second.env).unlink()
            second.commit_transaction()
        with self.independent_transaction() as transaction:
            self.assertFalse(item.with_env(transaction.env).exists())

    def test_concurrent_creates_of_a_unique_value_keep_one(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            winner = first.env[ITEM].create({'name': 'Winner', 'code': 'UNIQUE-RACE'})
            first.env.flush_all()
            # the second create cannot succeed before the first transaction ends
            with self.assertRefused():
                second.env[ITEM].create({'name': 'Loser', 'code': 'UNIQUE-RACE'})
                second.env.flush_all()
            second.rollback_transaction()
            first.commit_transaction()
            self.track_committed(winner)
            # and once it has ended, the value is taken
            with self.assertIntegrityError():
                second.env[ITEM].create({'name': 'Loser', 'code': 'UNIQUE-RACE'})
                second.env.flush_all()
            second.rollback_transaction()

        with self.independent_transaction() as transaction:
            found = transaction.env[ITEM].search([('code', '=', 'UNIQUE-RACE')])
            self.assertEqual(found.ids, winner.ids)
            self.assertEqual(found.name, 'Winner')


class TestSequenceNumbering(ConcurrencyCase):
    """ concurrency.ir_sequence: numbers drawn by concurrent transactions
    are distinct; a no-gap sequence hands out contiguous numbers. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nogap = cls.committed_fixture(lambda env: env['ir.sequence'].create({
            'name': 'Neutral no gap',
            'code': 'test_backend_neutral.nogap',
            'implementation': 'no_gap',
            'padding': 0,
            'number_next': 1,
        }))
        cls.standard = cls.committed_fixture(lambda env: env['ir.sequence'].create({
            'name': 'Neutral standard',
            'code': 'test_backend_neutral.standard',
            'implementation': 'standard',
            'padding': 0,
            'number_next': 1,
        }))
        cls.ranged = cls.committed_fixture(lambda env: env['ir.sequence'].create({
            'name': 'Neutral no gap by year',
            'code': 'test_backend_neutral.ranged',
            'implementation': 'no_gap',
            'use_date_range': True,
            'padding': 0,
            'prefix': '%(range_year)s/',
        }))
        today = fields.Date.today()
        cls.committed_fixture(lambda env: env['ir.sequence.date_range'].create({
            'sequence_id': cls.ranged.id,
            'date_from': today.replace(month=1, day=1),
            'date_to': today.replace(month=12, day=31),
            'number_next': 1,
        }))

    @staticmethod
    def draw(sequence, transaction):
        return int(sequence.with_env(transaction.env).next_by_id().rsplit('/', 1)[-1])

    def test_nogap_contender_gets_a_retryable_error(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            number = self.draw(self.nogap, first)
            with self.assertConcurrencyError():
                self.draw(self.nogap, second)
            second.rollback_transaction()
            first.commit_transaction()
            self.assertEqual(self.draw(self.nogap, second), number + 1)
            second.commit_transaction()
        with self.concurrent_session() as third:
            self.assertEqual(self.draw(self.nogap, third), number + 2)

    def test_nogap_rolled_back_number_is_drawn_again(self):
        with self.concurrent_session() as first:
            number = self.draw(self.nogap, first)
            first.rollback_transaction()
        with self.concurrent_session() as second:
            self.assertEqual(self.draw(self.nogap, second), number)
            second.commit_transaction()
        with self.concurrent_session() as third:
            self.assertEqual(self.draw(self.nogap, third), number + 1)

    def test_nogap_numbers_are_contiguous_across_sessions(self):
        drawn = []
        with self.concurrent_session() as first, self.concurrent_session() as second, \
                self.concurrent_session() as third:
            sessions = [first, second, third, first, second]
            for session in sessions:
                drawn.append(self.draw(self.nogap, session))
                session.commit_transaction()
        self.assertEqual(drawn, list(range(drawn[0], drawn[0] + len(sessions))))

    def test_nogap_contention_resolved_by_retry(self):
        """ Three sessions want a number at the same time: each one retries
        on a retryable error, and the three numbers are distinct and contiguous. """
        with self.concurrent_session() as first, self.concurrent_session() as second, \
                self.concurrent_session() as third:
            holder = self.draw(self.nogap, first)
            drawn = {}
            for session in (second, third):
                with self.assertConcurrencyError():
                    self.draw(self.nogap, session)
                session.rollback_transaction()
            first.commit_transaction()
            drawn['second'] = self.draw(self.nogap, second)
            with self.assertConcurrencyError():
                self.draw(self.nogap, third)
            third.rollback_transaction()
            second.commit_transaction()
            drawn['third'] = self.draw(self.nogap, third)
            third.commit_transaction()
        self.assertEqual([holder, drawn['second'], drawn['third']], [holder, holder + 1, holder + 2])

    def test_nogap_date_range_contention(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            number = self.draw(self.ranged, first)
            with self.assertConcurrencyError():
                self.draw(self.ranged, second)
            second.rollback_transaction()
            first.commit_transaction()
            self.assertEqual(self.draw(self.ranged, second), number + 1)
            second.commit_transaction()
        with self.independent_transaction() as transaction:
            prefix = str(fields.Date.today().year) + '/'
            self.assertTrue(self.ranged.with_env(transaction.env).next_by_id().startswith(prefix))

    def test_standard_concurrent_draws_are_distinct(self):
        with self.concurrent_session() as first, self.concurrent_session() as second, \
                self.concurrent_session() as third:
            # a standard sequence lets concurrent transactions draw: no error, no wait
            drawn = [self.draw(self.standard, first), self.draw(self.standard, second),
                     self.draw(self.standard, third), self.draw(self.standard, first)]
            second.rollback_transaction()
            first.commit_transaction()
            third.commit_transaction()
            # a number consumed by a rolled back transaction is never handed out again
            drawn.append(self.draw(self.standard, second))
            second.commit_transaction()
        self.assertEqual(len(set(drawn)), len(drawn))

    def test_standard_numbers_are_increasing_per_session(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            mine = [self.draw(self.standard, first) for _ in range(3)]
            theirs = [self.draw(self.standard, second) for _ in range(3)]
            first.commit_transaction()
            second.commit_transaction()
        self.assertEqual(mine, sorted(mine))
        self.assertEqual(theirs, sorted(theirs))
        self.assertFalse(set(mine) & set(theirs))


class TestCronJobClaiming(ConcurrencyCase):
    """ concurrency.ir_cron: a job is claimed by exactly one session; the
    others are refused and the job is never run twice for one claim. """

    MARKER = 'Made by the neutral cron'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cron = cls.committed_fixture(lambda env: env['ir.cron'].create({
            'name': 'Neutral cron',
            'model_id': env['ir.model']._get_id(ITEM),
            'state': 'code',
            'code': f"model.create({{'name': {cls.MARKER!r}}})",
            'interval_number': 1,
            'interval_type': 'days',
            'active': True,
        }))

    def runs(self):
        """ Return the records the job created so far, tracked for removal. """
        with self.independent_transaction() as transaction:
            made = transaction.env[ITEM].search([('name', '=', self.MARKER)])
        self.track_committed(made)
        return made

    def test_job_is_claimed_by_one_session(self):
        self.assertFalse(self.runs())
        with self.concurrent_session() as first, self.concurrent_session() as second:
            self.assertTrue(self.cron.with_env(first.env).method_direct_trigger())
            self.assertEqual(len(self.runs()), 1)

            # the job is held by the first session: the second one is refused
            with self.assertRaises(UserError):
                self.cron.with_env(second.env).method_direct_trigger()
            self.assertEqual(len(self.runs()), 1)
            # and cannot modify or remove the running job
            with self.assertRaises(UserError):
                self.cron.with_env(second.env).write({'interval_number': 2})
            with self.assertRaises(UserError):
                self.cron.with_env(second.env).unlink()
            # toggling is best effort: it does not fail and changes nothing
            self.assertTrue(self.cron.with_env(second.env).toggle(ITEM, [('name', '=', self.MARKER)]))
            self.assertEqual(self.read_committed(self.cron, 'interval_number'), [1])
            self.assertEqual(self.read_committed(self.cron, 'active'), [True])

            first.commit_transaction()
            # released, but the second session started before the job was
            # run: it has to retry in a new transaction
            with self.assertConcurrencyError():
                self.cron.with_env(second.env).method_direct_trigger()
            second.rollback_transaction()
            self.assertEqual(len(self.runs()), 1)
            self.assertTrue(self.cron.with_env(second.env).method_direct_trigger())
            second.commit_transaction()
        self.assertEqual(len(self.runs()), 2)

    def test_job_held_by_a_writer_is_not_claimed(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            self.cron.with_env(first.env).write({'interval_number': 3})
            with self.assertRaises(UserError):
                self.cron.with_env(second.env).method_direct_trigger()
            self.assertFalse(self.runs())
            first.rollback_transaction()
            self.assertTrue(self.cron.with_env(second.env).method_direct_trigger())
            second.commit_transaction()
        self.assertEqual(len(self.runs()), 1)
        self.assertEqual(self.read_committed(self.cron, 'interval_number'), [1])

    def test_job_runs_once_per_claim(self):
        with self.concurrent_session() as first:
            self.assertTrue(self.cron.with_env(first.env).method_direct_trigger())
            first.commit_transaction()
        with self.concurrent_session() as second:
            self.assertTrue(self.cron.with_env(second.env).method_direct_trigger())
            second.commit_transaction()
        made = self.runs()
        self.assertEqual(len(made), 2)
        self.assertEqual(len(set(made.ids)), 2)


class TestStockQuantReservation(ConcurrencyCase):
    """ Concurrent reservations and receipts on one quant add up: nothing is
    lost, nothing is counted twice. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.committed_fixture(lambda env: env['product.product'].create({
            'name': 'Neutral storable',
            'type': 'consu',
            'is_storable': True,
        }))
        cls.location = cls.env.ref('stock.stock_location_stock')

    def setUp(self):
        super().setUp()

        def make_quant(env):
            Quant = env['stock.quant']
            Quant._update_available_quantity(self.product.with_env(env), self.location.with_env(env), 10)
            return Quant.search(self._quant_domain())

        self.quant = self.committed_fixture(make_quant)
        self.assertEqual(len(self.quant), 1)

    @classmethod
    def _quant_domain(cls):
        return [('product_id', '=', cls.product.id), ('location_id', '=', cls.location.id)]

    def quants(self, env):
        return env['stock.quant'].search(self._quant_domain())

    def _update(self, transaction, **kwargs):
        env = transaction.env
        env['stock.quant']._update_available_quantity(
            self.product.with_env(env), self.location.with_env(env), **kwargs)

    def _check_totals(self, quantity, reserved):
        with self.independent_transaction() as transaction:
            quants = self.quants(transaction.env)
            self.track_committed(quants - self.quant)
            self.assertEqual(sum(quants.mapped('quantity')), quantity)
            self.assertEqual(sum(quants.mapped('reserved_quantity')), reserved)
            Quant = transaction.env['stock.quant']
            available = Quant._get_available_quantity(
                self.product.with_env(transaction.env), self.location.with_env(transaction.env))
            self.assertEqual(available, quantity - reserved)

    def test_concurrent_reservations_add_up(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            self._update(first, reserved_quantity=3)
            # the second session must not wait for the first, nor lose its reservation
            self._update(second, reserved_quantity=2)
            second.commit_transaction()
            first.commit_transaction()
        self._check_totals(quantity=10, reserved=5)

    def test_concurrent_receipts_add_up(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            self._update(first, quantity=4)
            self._update(second, quantity=6)
            first.commit_transaction()
            second.commit_transaction()
        self._check_totals(quantity=20, reserved=0)

    def test_rolled_back_reservation_leaves_no_trace(self):
        with self.concurrent_session() as first, self.concurrent_session() as second:
            self._update(first, reserved_quantity=3)
            self._update(second, reserved_quantity=2)
            first.rollback_transaction()
            second.commit_transaction()
        self._check_totals(quantity=10, reserved=2)


class TestDiscussChannelLastInterest(ConcurrencyCase):
    """ concurrency.discuss_channel: syncing the last interest of a channel
    held by another transaction is skipped silently, and converges later. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel = cls.committed_fixture(lambda env: env['discuss.channel'].create({
            'name': 'Neutral channel',
            'channel_type': 'channel',
        }))

    def queue_updates(self, *dates):
        return self.committed_fixture(lambda env: env['discuss.channel.last.interest.update'].create([
            {'channel_id': self.channel.id, 'last_interest_dt': date} for date in dates
        ]))

    def pending(self, env):
        return env['discuss.channel.last.interest.update'].search([('channel_id', '=', self.channel.id)])

    def test_sync_skips_a_held_channel_and_converges(self):
        before = self.read_committed(self.channel, 'last_interest_dt')[0]
        older, newest = before + timedelta(hours=1), before + timedelta(hours=2)
        updates = self.queue_updates(newest, older)

        with self.concurrent_session() as first, self.concurrent_session() as second:
            self.channel.with_env(first.env).description = 'Held by the first session'
            first.env.flush_all()

            Channel = second.env['discuss.channel']
            self.assertFalse(Channel._sync_last_interest_dt(self.channel.ids))
            second.commit_transaction()
            # nothing was lost and nothing corrupted
            self.assertEqual(self.read_committed(self.channel, 'last_interest_dt'), [before])
            self.assertEqual(self.pending(second.env), updates.with_env(second.env))

            first.commit_transaction()
            # the second session read the channel before the first committed
            # its write: the sync is refused and must be retried
            with self.assertConcurrencyError():
                Channel._sync_last_interest_dt(self.channel.ids)
            second.rollback_transaction()
            self.assertEqual(Channel._sync_last_interest_dt(self.channel.ids), self.channel.with_env(second.env))
            second.commit_transaction()

        with self.independent_transaction() as transaction:
            stored = self.channel.with_env(transaction.env)
            self.assertEqual(stored.last_interest_dt, newest)
            self.assertEqual(stored.description, 'Held by the first session')
            self.assertFalse(self.pending(transaction.env))

    def test_concurrent_syncs_apply_each_update_once(self):
        before = self.read_committed(self.channel, 'last_interest_dt')[0]
        newest = before + timedelta(hours=3)
        self.queue_updates(newest)

        with self.concurrent_session() as first, self.concurrent_session() as second:
            mine = first.env['discuss.channel']._sync_last_interest_dt(self.channel.ids)
            self.assertEqual(mine.ids, self.channel.ids)
            # the channel is held by the first syncer: the second one skips it
            self.assertFalse(second.env['discuss.channel']._sync_last_interest_dt(self.channel.ids))
            second.commit_transaction()
            first.commit_transaction()
            # nothing is left to sync, the channel can be locked again
            self.assertEqual(self.read_committed(self.channel, 'last_interest_dt'), [newest])
            self.assertFalse(self.pending(second.env))
            self.assertEqual(
                second.env['discuss.channel']._sync_last_interest_dt(self.channel.ids),
                self.channel.with_env(second.env),
            )
            second.rollback_transaction()

        self.assertEqual(self.read_committed(self.channel, 'last_interest_dt'), [newest])
