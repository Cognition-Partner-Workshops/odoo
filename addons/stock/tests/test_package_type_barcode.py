import threading

from odoo import sql_db
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPackageTypeBarcode(TransactionCase):
    """ unique(barcode) of stock.package.type on MongoDB storage, where the SQL
    constraint does not apply: the ORM check and its advisory lock. """

    def test_duplicate_barcode_rejected(self):
        PackageType = self.env['stock.package.type']
        PackageType.create({'name': 'Box 42', 'barcode': 'BOX-42'})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            PackageType.create({'name': 'Box 42 again', 'barcode': 'BOX-42'})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            PackageType.create([{'name': 'Box 43', 'barcode': 'BOX-43'}, {'name': 'Box 43 again', 'barcode': 'BOX-43'}])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            PackageType.create({'name': 'Box 44', 'barcode': 'BOX-44'}).write({'barcode': 'BOX-42'})
        PackageType.create([{'name': 'No barcode'}, {'name': 'No barcode either'}])

    def _cursor(self):
        """ A real connection, outside the test cursor's transaction. """
        return sql_db.db_connect(self.registry.db_name).cursor()

    def _claim(self, env, barcode, outcome):
        """ Claim ``barcode`` in ``env``'s own transaction. """
        try:
            env['stock.package.type'].create({'name': 'Rival', 'barcode': barcode})
            outcome['result'] = 'created'
        except ValidationError:
            outcome['result'] = 'rejected'

    def _rival(self, barcode):
        """ Start a rival claim of ``barcode`` in its own transaction and check
        that it waits on the lock of the first claim, flushed but not ended.
        The environment is built and ended here: the test runner holds the
        registry lock, which the thread would need for both. """
        outcome = {}
        env = self.env(cr=self._cursor())
        rival = threading.Thread(target=self._claim, args=(env, barcode, outcome))
        rival.start()
        rival.join(timeout=3)
        self.assertTrue(rival.is_alive(), "the rival claim waits for the first transaction to end")

        def end():
            rival.join(timeout=30)
            env.cr.rollback()
            env.cr.close()
            return outcome.get('result')
        return end

    def test_rival_claim_rejected_after_commit(self):
        with self._cursor() as cr:
            first = self.env(cr=cr)['stock.package.type'].create({'name': 'First', 'barcode': 'BOX-77'})
            first.env.flush_all()
            rival = self._rival('BOX-77')
            cr.commit()
        try:
            self.assertEqual(rival(), 'rejected', "the committed claim is visible to the rival")
        finally:
            with self._cursor() as cr:
                self.env(cr=cr)['stock.package.type'].browse(first.id).unlink()
                cr.commit()

    def test_rival_claim_succeeds_after_rollback(self):
        with self._cursor() as cr:
            first = self.env(cr=cr)['stock.package.type'].create({'name': 'First', 'barcode': 'BOX-78'})
            first.env.flush_all()
            rival = self._rival('BOX-78')
            cr.rollback()
        self.assertEqual(rival(), 'created', "a rolled-back claim is undone before its lock is released")
