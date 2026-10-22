from odoo.fields import Domain
from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL


@tagged('at_install', '-post_install')
class TestSqlConditions(TransactionCase):
    """ Domain conditions whose value is a raw SQL subquery of ids. """

    def test_id_sql_subquery(self):
        Tag = self.env['test_orm_mongodb.tag']
        tags = Tag.create([{'name': 'a'}, {'name': 'b'}])
        domain = Domain('id', 'in', tags.ids)
        # product name search and stock location filters pass ('id', 'in', SQL(...))
        subquery = SQL("SELECT id FROM product_tag WHERE id = %s", tags[0].id)
        self.assertEqual(Tag.search(domain & Domain('id', 'in', subquery)), tags[0])
        self.assertEqual(Tag.search(domain & Domain('id', 'any!', subquery)), tags[0])
        self.assertEqual(Tag.search(domain & Domain('id', 'not any!', subquery)), tags[1])

    def test_many2one_sql_subquery(self):
        Category = self.env['test_orm_mongodb.category']
        parent, other = Category.create([{'name': 'parent'}, {'name': 'other'}])
        children = Category.create([{'name': 'c1', 'parent_id': parent.id}, {'name': 'c2', 'parent_id': other.id}])
        domain = Domain('id', 'in', children.ids)
        subquery = SQL("SELECT %s", parent.id)
        self.assertEqual(Category.search(domain & Domain('parent_id', 'any!', subquery)), children[0])
        self.assertEqual(Category.search(domain & Domain('parent_id', 'not any!', subquery)), children[1])

    def test_sql_subquery_with_null(self):
        # PostgreSQL: x IN (.., NULL) ignores the NULL, x NOT IN (.., NULL) is never true
        Category = self.env['test_orm_mongodb.category']
        parent = Category.create({'name': 'parent'})
        child, orphan = Category.create([{'name': 'c', 'parent_id': parent.id}, {'name': 'o'}])
        records = parent | child | orphan
        domain = Domain('id', 'in', records.ids)
        subquery = SQL("SELECT unnest(ARRAY[%s, NULL]::int[])", parent.id)
        self.assertEqual(Category.search(domain & Domain('id', 'any!', subquery)), parent)
        self.assertFalse(Category.search(domain & Domain('id', 'not any!', subquery)))
        self.assertEqual(Category.search(domain & Domain('parent_id', 'any!', subquery)), child)
        self.assertEqual(Category.search(domain & Domain('parent_id', 'not any!', subquery)), parent | orphan)
