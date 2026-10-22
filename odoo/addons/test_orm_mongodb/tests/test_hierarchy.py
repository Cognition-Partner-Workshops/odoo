from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('at_install', '-post_install')
class TestParentStoreMongodb(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Category = cls.env['test_orm_mongodb.category']

    def test_parent_path(self):
        a, d = self.Category.create([{'name': 'a'}, {'name': 'd'}])
        b = self.Category.create({'name': 'b', 'parent_id': a.id})
        c = self.Category.create({'name': 'c', 'parent_id': b.id})
        self.assertEqual(c.parent_path, f'{a.id}/{b.id}/{c.id}/')
        self.assertEqual(self.Category.search([('id', 'child_of', a.id)]), a + b + c)
        self.assertEqual(self.Category.search([('id', 'parent_of', c.id)]), a + b + c)

        b.parent_id = d
        self.env.invalidate_all()
        self.assertEqual((b.parent_path, c.parent_path), (f'{d.id}/{b.id}/', f'{d.id}/{b.id}/{c.id}/'))
        self.assertEqual(self.Category.search([('id', 'child_of', d.id)]), b + c + d)
        self.assertEqual(self.Category.search([('id', 'child_of', a.id)]), a)

        b.parent_id = False
        self.env.invalidate_all()
        self.assertEqual(c.parent_path, f'{b.id}/{c.id}/')
        with self.assertRaises(UserError):
            b.parent_id = c

    def test_company_dependent(self):
        from odoo.orm import storage_mongodb  # noqa: PLC0415
        other = self.env['res.company'].create({'name': 'Other'})
        first, second = self.Category.create([{'name': 'x', 'property_cost_method': 'average'}, {'name': 'y'}])
        first.with_company(other).property_cost_method = 'standard'
        self.env.invalidate_all()
        self.assertEqual((first.property_cost_method, first.with_company(other).property_cost_method), ('average', 'standard'))
        self.assertFalse(second.with_company(other).property_cost_method)

        domain = [('id', 'in', (first + second).ids)]
        self.assertEqual(self.Category.search(domain + [('property_cost_method', '=', 'average')]), first)
        self.assertEqual(self.Category.search(domain + [('property_cost_method', '=', False)]), second)
        Other = self.Category.with_company(other)
        self.assertEqual(Other.search(domain, order='property_cost_method').ids, [first.id, second.id])
        self.assertEqual(dict(Other._read_group(domain, ['property_cost_method'], ['__count'])), {'standard': 1, False: 1})

        # the other company's default is the fallback, and a value equal to it is not stored
        self.env['ir.default'].set(self.Category._name, 'property_cost_method', 'average', company_id=other.id)
        self.env.invalidate_all()
        self.assertEqual(second.with_company(other).property_cost_method, 'average')
        self.assertEqual(Other.search(domain + [('property_cost_method', '=', 'average')]), second)
        first.with_company(other).property_cost_method = 'average'
        self.env.flush_all()
        doc = storage_mongodb.get_collection(self.Category).find_one({'_id': first.id})
        self.assertEqual(doc['propertyCostMethod'], {str(self.env.company.id): 'average'})

    def test_company_dependent_many2one_ondelete(self):
        cleared, kept = self.env['res.partner'].create([{'name': 'cleared'}, {'name': 'kept'}])
        category = self.Category.create({'name': 'z', 'property_stock_journal': cleared.id,
                                         'property_account_income_categ_id': kept.id})
        cleared.unlink()
        self.env.invalidate_all()
        self.assertFalse(category.property_stock_journal)
        with self.assertRaises(UserError):
            kept.unlink()
