from unittest.mock import patch

import psycopg2.errors

from odoo import Command
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL, sql


@tagged('at_install', '-post_install')
class TestMany2manyMongodb(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Tag = cls.env['test_orm_mongodb.tag']
        cls.Link = cls.env['test_orm_mongodb.pg_link']
        cls.Incoterm = cls.env['test_orm_mongodb.incoterm']
        cls.links = cls.Link.create([{'name': f'link {i}'} for i in range(3)])
        cls.incoterms = cls.Incoterm.create([{'code': code, 'name': code} for code in ('EXW', 'FOB')])

    def doc(self, record):
        return storage_mongodb.get_collection(record).find_one({'_id': record.id})

    def array(self, record, path, key):
        return sorted(item[key] for item in (self.doc(record) or {}).get(path, []))

    def junction(self):
        layout = storage_mongodb.relation_layout(self.Incoterm._fields['optional_link_ids'], self.env)
        collection = storage_mongodb._relation_collection(self.env, layout)
        return collection, sorted((doc['srcId'], doc['destId']) for doc in collection.find())

    def test_junction_array_commands(self):
        a, b, c = self.links
        tag = self.Tag.create({'name': 'red', 'link_ids': [Command.link(a.id), Command.link(b.id)]})
        self.assertEqual(self.array(tag, 'productTemplateRel', 'productTemplateId'), sorted([a.id, b.id]))
        self.assertFalse(sql.table_exists(self.env.cr, 'product_tag_product_template_rel'))

        tag.write({'link_ids': [Command.unlink(a.id), Command.link(c.id)]})
        self.assertEqual(self.array(tag, 'productTemplateRel', 'productTemplateId'), sorted([b.id, c.id]))
        tag.invalidate_recordset()
        self.assertEqual(tag.link_ids, b + c)
        tag.link_ids = [Command.set([a.id])]
        self.assertEqual(self.array(tag, 'productTemplateRel', 'productTemplateId'), [a.id])
        tag.link_ids = [Command.clear()]
        self.assertEqual(self.doc(tag).get('productTemplateRel'), [])

    def test_junction_array_reverse_side(self):
        a, b, _c = self.links
        red, blue = self.Tag.create([{'name': 'red', 'sequence': 2}, {'name': 'blue', 'sequence': 1}])
        a.tag_ids = [Command.set([red.id, blue.id])]
        b.tag_ids = [Command.link(red.id)]
        self.assertEqual(self.array(red, 'productTemplateRel', 'productTemplateId'), sorted([a.id, b.id]))
        self.env.invalidate_all()
        self.assertEqual(a.tag_ids.ids, [blue.id, red.id], "ordered by the comodel's _order")
        self.assertEqual(red.link_ids, a + b)
        a.tag_ids = [Command.unlink(red.id)]
        self.assertEqual(self.array(red, 'productTemplateRel', 'productTemplateId'), [b.id])

    def test_junction_array_search(self):
        a, b, c = self.links
        red, blue, bare = self.Tag.create([
            {'name': 'red', 'link_ids': [Command.set([a.id, b.id])]},
            {'name': 'blue', 'link_ids': [Command.set([b.id])]},
            {'name': 'bare'},
        ])
        tags = red + blue + bare
        self.assertEqual(self.Tag.search([('id', 'in', tags.ids), ('link_ids', 'in', a.ids)]), red)
        self.assertEqual(self.Tag.search([('id', 'in', tags.ids), ('link_ids', 'not in', a.ids)]), blue + bare)
        self.assertEqual(self.Tag.search([('id', 'in', tags.ids), ('link_ids', '=', False)]), bare)
        self.assertEqual(self.Tag.search([('id', 'in', tags.ids), ('link_ids.name', '=', 'link 1')]), red + blue)
        links = self.links
        self.assertEqual(self.Link.search([('id', 'in', links.ids), ('tag_ids', 'in', blue.ids)]), b)
        self.assertEqual(self.Link.search([('id', 'in', links.ids), ('tag_ids', '=', False)]), c)
        self.assertEqual(self.Link.search([('id', 'in', links.ids), ('tag_ids.name', '=', 'red')]), a + b)

    def test_junction_array_between_mongodb_models(self):
        exw, fob = self.incoterms
        tag = self.Tag.create({'name': 'red', 'incoterm_ids': [Command.set([fob.id, exw.id])]})
        self.assertEqual(self.array(tag, 'productProductRel', 'productProductId'), sorted([exw.id, fob.id]))
        tag.invalidate_recordset()
        self.assertEqual(tag.incoterm_ids, exw + fob)
        self.assertEqual(self.Tag.search([('id', '=', tag.id), ('incoterm_ids.code', '=', 'FOB')]), tag)

    def test_postgresql_relation_table_search(self):
        partner = self.env['res.partner'].create({'name': 'Linked partner'})
        linked = self.Tag.create({'name': 'linked', 'partner_ids': [Command.link(partner.id)]})
        unlinked = self.Tag.create({'name': 'unlinked'})
        self.assertTrue(sql.table_exists(self.env.cr, 'test_orm_mongodb_tag_partner_rel'))
        Tag = self.Tag.with_context(active_test=False)
        tags = [('id', 'in', (linked | unlinked).ids)]
        # pricelist lookups search ('country_group_ids', '=', False), a 'not any!'
        self.assertEqual(Tag.search(tags + [('partner_ids', '=', False)]), unlinked)
        self.assertEqual(Tag.search(tags + [('partner_ids', '!=', False)]), linked)
        self.assertEqual(Tag.search(tags + [('partner_ids', 'in', partner.ids)]), linked)
        self.assertEqual(Tag.search(tags + [('partner_ids', 'not in', partner.ids)]), unlinked)
        self.assertEqual(Tag.search(tags + [('partner_ids.name', '=', 'Linked partner')]), linked)

    def test_postgresql_cascade_follows_mongodb_references(self):
        Incoterm = self.env['test_orm_mongodb.incoterm']
        gone, kept = Incoterm.create([{'name': 'Gone', 'code': 'GON'}, {'name': 'Kept', 'code': 'KPT'}])
        link = self.env['test_orm_mongodb.pg_link'].create({'name': 'Cascaded', 'incoterm_id': gone.id})
        kept.optional_link_ids = link
        warehouse = self.env['test_orm_mongodb.warehouse'].create({'name': 'WH', 'buy_pull_id': link.id})
        gone.unlink()
        self.assertFalse(link.exists())
        self.env.invalidate_all()
        self.assertFalse(warehouse.buy_pull_id)
        self.assertFalse(kept.optional_link_ids)

    def test_unlink_follows_ondelete(self):
        a, b, _c = self.links
        exw, fob = self.incoterms
        tag = self.Tag.create({'name': 'red', 'link_ids': [Command.set([a.id, b.id])],
                               'incoterm_ids': [Command.set([exw.id])]})
        a.unlink()
        self.assertEqual(self.array(tag, 'productTemplateRel', 'productTemplateId'), [b.id])
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
            exw.unlink()
        fob.unlink()
        self.assertEqual(self.array(tag, 'productProductRel', 'productProductId'), [exw.id])

    def test_root_junction_collection(self):
        a, b, c = self.links
        exw, fob = self.incoterms
        collection, before = self.junction()
        exw.optional_link_ids = [Command.set([a.id, b.id])]
        c.optional_incoterm_ids = [Command.link(exw.id), Command.link(fob.id)]
        expected = sorted(before + [(exw.id, a.id), (exw.id, b.id), (exw.id, c.id), (fob.id, c.id)])
        self.assertEqual(self.junction()[1], expected)
        self.assertFalse(sql.table_exists(self.env.cr, 'product_optional_rel'))
        unique = [index['key'] for index in collection.list_indexes() if index.get('unique')]
        self.assertIn({'destId': 1, 'srcId': 1}, [dict(key) for key in unique])

        self.env.invalidate_all()
        self.assertEqual(exw.optional_link_ids, a + b + c)
        self.assertEqual(c.optional_incoterm_ids, exw + fob)
        self.assertEqual(self.Incoterm.search([('id', 'in', self.incoterms.ids), ('optional_link_ids', 'in', a.ids)]), exw)
        self.assertEqual(self.Link.search([('id', 'in', self.links.ids), ('optional_incoterm_ids', 'in', fob.ids)]), c)
        self.assertEqual(self.Link.search([('id', 'in', self.links.ids), ('optional_incoterm_ids', '=', False)]),
                         self.Link)

        exw.optional_link_ids = [Command.unlink(a.id)]
        c.unlink()
        fob.unlink()
        self.assertEqual(self.junction()[1], sorted(before + [(exw.id, b.id)]))

    def test_root_junction_mongodb_writes_from_both_sides(self):
        incoterm = self.Incoterm.create({'code': 'TST', 'name': 'Test'})
        link = self.Link.create({'name': 'Test'})
        pair = (incoterm.id, link.id)

        incoterm.optional_link_ids = [Command.link(link.id)]
        self.assertIn(pair, self.junction()[1])
        self.assertFalse(sql.table_exists(self.env.cr, 'product_optional_rel'))
        self.env.invalidate_all()
        self.assertEqual(incoterm.optional_link_ids, link)
        self.assertEqual(link.optional_incoterm_ids, incoterm)

        incoterm.optional_link_ids = [Command.unlink(link.id)]
        self.assertNotIn(pair, self.junction()[1])
        self.env.invalidate_all()
        self.assertFalse(incoterm.optional_link_ids)
        self.assertFalse(link.optional_incoterm_ids)

        link.optional_incoterm_ids = [Command.link(incoterm.id)]
        self.assertIn(pair, self.junction()[1])
        self.assertFalse(sql.table_exists(self.env.cr, 'product_optional_rel'))
        self.env.invalidate_all()
        self.assertEqual(incoterm.optional_link_ids, link)
        self.assertEqual(link.optional_incoterm_ids, incoterm)

        link.optional_incoterm_ids = [Command.unlink(incoterm.id)]
        self.assertNotIn(pair, self.junction()[1])
        self.env.invalidate_all()
        self.assertFalse(incoterm.optional_link_ids)
        self.assertFalse(link.optional_incoterm_ids)

    def test_link_to_missing_record_fails(self):
        exw, _fob = self.incoterms
        tag = self.Tag.create({'name': 'red'})
        missing = self.links[-1].id + 1000
        for record, fname in ((tag, 'link_ids'), (exw, 'optional_link_ids')):
            with self.subTest(fname=fname), self.assertRaises(psycopg2.errors.ForeignKeyViolation):
                record[fname] = [Command.link(missing)]
        self.assertFalse(self.doc(tag).get('productTemplateRel'))
        self.assertNotIn(missing, [dest for _src, dest in self.junction()[1]])

    def test_savepoint_rollback_undoes_links(self):
        a, b, _c = self.links
        exw, _fob = self.incoterms
        tag = self.Tag.create({'name': 'red', 'link_ids': [Command.set([a.id])]})
        exw.optional_link_ids = [Command.set([a.id])]
        _collection, before = self.junction()
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            tag.link_ids = [Command.set([b.id])]
            exw.optional_link_ids = [Command.set([b.id])]
            1 / 0
        self.assertEqual(self.array(tag, 'productTemplateRel', 'productTemplateId'), [a.id])
        self.assertEqual(self.junction()[1], before)

    def mirror(self, table, column, ids):
        self.env.cr.execute(SQL("SELECT * FROM %s WHERE %s IN %s", SQL.identifier(table), SQL.identifier(column), tuple(ids)))
        return sorted(self.env.cr.fetchall())

    def test_relation_mirror(self):
        field = self.Tag._fields['incoterm_ids']
        exw, fob = self.incoterms
        red = self.Tag.create({'name': 'red', 'incoterm_ids': [Command.set([exw.id, fob.id])]})
        self.assertEqual(self.array(red, 'productProductRel', 'productProductId'), sorted([exw.id, fob.id]))
        rows = lambda: self.mirror('product_tag_product_product_rel', 'product_tag_id', red.ids)  # noqa: E731
        self.assertEqual(rows(), sorted([(red.id, exw.id), (red.id, fob.id)]))

        red.incoterm_ids = [Command.unlink(fob.id)]
        self.assertEqual(rows(), [(red.id, exw.id)])
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            red.incoterm_ids = [Command.set([fob.id])]
            self.assertEqual(rows(), [(red.id, fob.id)])
            1 / 0
        self.assertEqual(rows(), [(red.id, exw.id)])
        self.assertEqual(self.array(red, 'productProductRel', 'productProductId'), [exw.id])
        self.assertEqual(storage_mongodb.relation_mirror_diff(field, self.env), (set(), set()))
        red.unlink()
        self.assertEqual(rows(), [])

    def test_relation_mirror_check_detects_drift(self):
        field = self.Tag._fields['incoterm_ids']
        exw, fob = self.incoterms
        red = self.Tag.create({'name': 'red', 'incoterm_ids': [Command.set([exw.id])]})
        self.assertEqual(storage_mongodb.relation_mirror_diff(field, self.env), (set(), set()))
        self.env.cr.execute(SQL(
            "UPDATE product_tag_product_product_rel SET product_product_id = %s WHERE product_tag_id = %s", fob.id, red.id))
        self.assertEqual(storage_mongodb.relation_mirror_diff(field, self.env),
                         ({(red.id, exw.id)}, {(red.id, fob.id)}))

    def test_root_junction_mirror(self):
        a, b, c = self.links
        exw, fob = self.incoterms
        field = self.Incoterm._fields['optional_link_ids']
        exw.optional_link_ids = [Command.set([a.id, b.id])]  # before the mirror exists
        self.patch(type(self.Incoterm), '_shadow_relations', ('optional_link_ids',))
        caches = self.env.registry.__dict__
        caches.pop('_mongodb_mirrored_relations', None)
        self.addCleanup(caches.pop, '_mongodb_mirrored_relations', None)
        with patch.object(self.env.registry, 'post_init', lambda *args: None):
            field.update_db(self.Incoterm, {})
        self.assertEqual(storage_mongodb.relation_mirror_diff(field, self.env), (set(), set()), "filled from MongoDB")
        rows = lambda: self.mirror('product_optional_rel', 'src_id', self.incoterms.ids)  # noqa: E731
        self.assertEqual(rows(), sorted([(exw.id, a.id), (exw.id, b.id)]))

        c.optional_incoterm_ids = [Command.link(fob.id)]
        exw.optional_link_ids = [Command.unlink(a.id)]
        self.assertEqual(rows(), sorted([(exw.id, b.id), (fob.id, c.id)]))
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            exw.optional_link_ids = [Command.clear()]
            1 / 0
        self.assertEqual(rows(), sorted([(exw.id, b.id), (fob.id, c.id)]))
        self.assertEqual(storage_mongodb.relation_mirror_diff(field, self.env), (set(), set()))
