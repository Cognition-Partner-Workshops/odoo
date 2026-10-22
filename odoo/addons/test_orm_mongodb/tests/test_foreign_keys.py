import psycopg2.errors

from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('at_install', '-post_install')
class TestForeignKeysMongodb(TransactionCase):
    """ PostgreSQL foreign keys into MongoDB models point at their shadow rows,
    so PostgreSQL still applies ``ondelete``. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Link = cls.env['test_orm_mongodb.pg_link']
        cls.Tag = cls.env['test_orm_mongodb.tag']

    def test_set_null(self):
        tag = self.Tag.create({'name': 't'})
        link = self.Link.create({'name': 'l', 'tag_id': tag.id})
        tag.unlink()
        self.env.invalidate_all()
        self.assertFalse(link.tag_id)

    @mute_logger('odoo.sql_db')
    def test_restrict(self):
        tag = self.Tag.create({'name': 't'})
        link = self.Link.create({'name': 'l', 'restrict_tag_id': tag.id})
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation), self.env.cr.savepoint():
            tag.unlink()
        self.env.invalidate_all()
        self.assertEqual(link.restrict_tag_id, tag)
        self.assertEqual(self.Tag.search([('id', '=', tag.id)]), tag, "the document survives the failed delete")

    def test_key_into_embedded_child(self):
        attribute = self.env['test_orm_mongodb.attribute'].create({
            'name': 'a', 'value_ids': [(0, 0, {'name': 'v1'}), (0, 0, {'name': 'v2'})],
        })
        first, second = attribute.value_ids
        links = self.Link.create([{'name': 'l1', 'attribute_value_id': first.id},
                                  {'name': 'l2', 'attribute_value_id': second.id}])
        first.unlink()
        self.env.invalidate_all()
        self.assertEqual(links.mapped('attribute_value_id'), second)
        attribute.unlink()      # cascades to its values
        self.env.invalidate_all()
        self.assertFalse(links.mapped('attribute_value_id'))


@tagged('at_install', '-post_install')
class TestReportColumnsMongodb(TransactionCase):

    def test_mirror_columns(self):
        """ A shadow column added for a report is filled from the documents. """
        Lock = self.env['test_orm_mongodb.lock_exception']
        locks = Lock.create([{'company_id': self.env.company.id}, {'company_id': self.env.company.id, 'active': False}])
        other = self.env['res.company'].create({'name': 'Other'})
        self.env.flush_all()
        self.env.cr.execute("UPDATE account_lock_exception SET company_id = %s WHERE id IN %s", [other.id, tuple(locks.ids)])
        storage_mongodb.mirror_columns(Lock, ['company_id'])
        self.env.cr.execute("SELECT company_id FROM account_lock_exception WHERE id IN %s", [tuple(locks.ids)])
        self.assertEqual([row[0] for row in self.env.cr.fetchall()], [self.env.company.id] * 2)
