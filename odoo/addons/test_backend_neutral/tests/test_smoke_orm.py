from odoo.addons.test_backend_neutral.harness import NeutralCase


class TestSmokeOrm(NeutralCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Item = cls.env['test_backend_neutral.item']
        cls.items = cls.Item.create([
            {'name': 'Alpha', 'code': 'A', 'quantity': 3},
            {'name': 'Beta', 'code': 'B', 'quantity': 1},
            {'name': 'Gamma', 'code': 'C', 'quantity': 2},
        ])

    def test_create_read(self):
        item = self.Item.create({'name': 'Delta', 'code': 'D', 'quantity': 4})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertTrue(item.exists())
        self.assertEqual(item.name, 'Delta')
        self.assertEqual(item.read(['name', 'code', 'quantity']), [
            {'id': item.id, 'name': 'Delta', 'code': 'D', 'quantity': 4},
        ])

    def test_write(self):
        alpha, beta, gamma = self.items
        (alpha + beta).write({'quantity': 7})
        gamma.parent_id = alpha
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(self.items.mapped('quantity'), [7, 7, 2])
        self.assertEqual(gamma.parent_id, alpha)
        self.assertEqual(alpha.child_ids, gamma)

    def test_unlink(self):
        alpha, beta, gamma = self.items
        beta.unlink()
        self.env.invalidate_all()
        self.assertFalse(beta.exists())
        self.assertEqual(self.items.exists(), alpha + gamma)
        self.assertEqual(self.Item.search([('code', 'in', ['A', 'B', 'C'])]), alpha + gamma)

    def test_search(self):
        alpha, beta, gamma = self.items
        # the default order is the id, which is the creation order
        self.assertEqual(self.Item.search([('id', 'in', self.items.ids)]), self.items)
        self.assertEqual(self.Item.search([('quantity', '>=', 2)], order='quantity'), gamma + alpha)
        self.assertEqual(self.Item.search([('name', 'like', 'a')], order='name desc', limit=2), gamma + beta)
        self.assertEqual(self.Item.search_count([('code', '!=', 'B')]), 2)
        self.assertFalse(self.Item.search([('code', '=', 'Z')]))

    def test_tests_are_isolated_first(self):
        self._check_test_isolation()

    def test_tests_are_isolated_second(self):
        self._check_test_isolation()

    def _check_test_isolation(self):
        """ What a test writes is undone before the next one: both tests
        modify the class data the same way, whichever runs first. """
        alpha, beta, _gamma = self.items
        self.assertEqual(alpha.quantity, 3)
        self.assertTrue(beta.exists())
        self.assertFalse(self.Item.search([('code', '=', 'ISOLATED')]))
        alpha.quantity = 30
        beta.unlink()
        self.Item.create({'name': 'Isolated', 'code': 'ISOLATED'})
        self.env.flush_all()

    def test_backend_internals_are_not_available(self):
        for name in ('cr', 'registry', 'cursor', 'assertQueries', 'assertQueryCount', 'registry_test_mode'):
            with self.subTest(name=name), self.assertRaises(NotImplementedError):
                getattr(self, name)
