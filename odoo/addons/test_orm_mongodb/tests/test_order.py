from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged


@tagged('at_install', '-post_install')
class TestOrderOutsideDocument(TransactionCase):
    """ Orders on fields the MongoDB document doesn't hold. """

    def test_order_inherited_field(self):
        Variant = self.env['test_orm_mongodb.variant']
        b = Variant.create({'name': 'Bravo', 'default_code': 'b'})
        a = Variant.create({'name': 'Alpha', 'default_code': 'a'})
        c = Variant.create({'name': 'Charlie'})
        domain = [('id', 'in', (a | b | c).ids)]
        # product lookups search product.product ordered by the template's translated name
        self.assertEqual(Variant.search(domain, order='name').ids, [a.id, b.id, c.id])
        self.assertEqual(Variant.search(domain, order='name desc').ids, [c.id, b.id, a.id])
        self.assertEqual(Variant.search(domain, order='name', limit=1), a)
        self.assertEqual(Variant.search(domain + [('name', '=', 'Bravo')]), b)

    def test_order_boolean_unset_is_false(self):
        # like PostgreSQL's COALESCE(field, FALSE): an unset boolean sorts as False, not as NULL
        Incoterm = self.env['test_orm_mongodb.incoterm'].with_context(active_test=False)
        unset, active, inactive = Incoterm.create([
            {'code': 'U', 'name': 'Unset'},
            {'code': 'A', 'name': 'Active', 'active': True},
            {'code': 'I', 'name': 'Inactive', 'active': False},
        ])
        storage_mongodb.update(Incoterm, unset.ids, [{'active': None}])
        self.assertNotIn('active', storage_mongodb.get_collection(Incoterm).find_one({'_id': unset.id}))
        domain = [('id', 'in', (unset + active + inactive).ids)]
        self.assertEqual(Incoterm.search(domain, order='active desc, id').ids, (active + unset + inactive).ids)
        self.assertEqual(Incoterm.search(domain, order='active, id').ids, (unset + inactive + active).ids)

    def test_order_compute_sql_field(self):
        Tag = self.env['test_orm_mongodb.tag']
        tags = Tag.create([{'name': str(i)} for i in range(4)])
        expected = sorted(tags.ids, key=lambda id_: (id_ % 2, id_))
        self.assertEqual(Tag.search([('id', 'in', tags.ids)], order='is_even desc, id').ids, expected)
        # an outside term keeps its place after an in-document term
        tags.write({'sequence': 1})
        tags[0].sequence = 2
        expected = sorted(tags.ids, key=lambda id_: (id_ == tags[0].id, id_ % 2, id_))
        self.assertEqual(Tag.search([('id', 'in', tags.ids)], order='sequence, is_even desc, id').ids, expected)
        # ties of an outside term are broken by the next terms
        # (stock.picking.type orders by 'is_favorite desc, sequence, id')
        tags.write({'sequence': 1})
        tags[:2].write({'sequence': 2})
        expected = sorted(tags.ids, key=lambda id_: (id_ % 2, id_ in tags[:2].ids, id_))
        self.assertEqual(Tag.search([('id', 'in', tags.ids)], order='is_even desc, sequence, id').ids, expected)

    def test_order_many2one_cycle(self):
        # product.category orders by its own parent_id: the inner parent_id adds no term
        Category = self.env['test_orm_mongodb.category']
        self.patch(self.registry[Category._name], '_order', 'parent_id desc, name, id')
        a, b = Category.create([{'name': 'cycle a'}, {'name': 'cycle b'}])
        c1, c2, c3 = Category.create([
            {'name': 'cycle x', 'parent_id': b.id},
            {'name': 'cycle y', 'parent_id': a.id},
            {'name': 'cycle w', 'parent_id': a.id},
        ])
        records = a | b | c1 | c2 | c3
        self.assertEqual(Category.search([('id', 'in', records.ids)]), a + b + c1 + c3 + c2)
