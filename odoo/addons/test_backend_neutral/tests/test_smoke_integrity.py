from odoo.addons.test_backend_neutral.harness import NeutralCase


class TestSmokeIntegrity(NeutralCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Item = cls.env['test_backend_neutral.item']
        cls.item = cls.Item.create({'name': 'Alpha', 'code': 'A', 'quantity': 3})

    def test_unique(self):
        with self.assertIntegrityError():
            self.Item.create({'name': 'Duplicate', 'code': 'A'})
        # the test goes on after the failure, which left nothing behind
        self.env.invalidate_all()
        self.assertEqual(self.Item.search([('code', '=', 'A')]), self.item)
        self.assertTrue(self.Item.create({'name': 'Other', 'code': 'B'}).exists())

    def test_check(self):
        with self.assertIntegrityError():
            self.item.quantity = -1
        self.env.invalidate_all()
        self.assertEqual(self.item.quantity, 3)

    def test_not_null(self):
        with self.assertIntegrityError():
            self.Item.create({'code': 'B'})
        self.env.invalidate_all()
        self.assertFalse(self.Item.search([('code', '=', 'B')]))

    def test_restrict(self):
        child = self.Item.create({'name': 'Child', 'parent_id': self.item.id})
        with self.assertIntegrityError():
            self.item.unlink()
        self.env.invalidate_all()
        self.assertTrue(self.item.exists())
        self.assertEqual(child.parent_id, self.item)

    def test_no_error_is_a_failure(self):
        with self.assertRaises(AssertionError), self.assertIntegrityError():
            self.Item.create({'name': 'Valid', 'code': 'B'})
