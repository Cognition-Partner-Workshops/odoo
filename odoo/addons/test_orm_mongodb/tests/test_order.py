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
