import os
from unittest.mock import patch

from odoo.fields import Command, Domain
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL


@tagged('at_install', '-post_install')
class TestConformance(TransactionCase):
    """ Storage-on gaps found by the s3.5 conformance probes. """

    def test_sweep_seeds_link_arrays(self):
        # account.account companyIds: the relation rows of a storage-off install
        # must reach the owner's link array when the sweep seeds it
        Template = self.env['test_orm_mongodb.template']
        template = Template.create({'name': 't'})
        tag = self.env['test_orm_mongodb.tag'].create({'name': 'a'})
        self.env.cr.execute(SQL("CREATE TABLE IF NOT EXISTS product_tag_product_template_rel "
                                "(product_template_id integer, product_tag_id integer)"))
        self.env.cr.execute(SQL("INSERT INTO product_tag_product_template_rel VALUES (%s, %s)", template.id, tag.id))
        storage_mongodb._seed_links(Template, {template.id})
        storage_mongodb._seed_links(Template, {template.id})
        template.invalidate_recordset()
        self.assertEqual(template.tag_ids, tag)
        [doc] = storage_mongodb.get_collection(Template).find({'_id': template.id})
        self.assertEqual(len(doc['productTagIds']), 1, "seeded once")
        with patch.dict(os.environ, {'ODOO_MONGODB_SWEEP': '1'}):
            template.tag_ids = [Command.unlink(tag.id)]
            storage_mongodb._seed_sweep(Template)
            storage_mongodb._seed_links(Template, {template.id})
        template.invalidate_recordset()
        self.assertFalse(template.tag_ids, "a removed link is not seeded again")
        self.env.cr.execute(SQL("SELECT count(*) FROM product_tag_product_template_rel"))
        self.assertEqual(self.env.cr.fetchone()[0], 0)

    def test_sweep_seeds_junction_from_either_side(self):
        Tag, Incoterm = self.env['test_orm_mongodb.tag'], self.env['test_orm_mongodb.incoterm']
        tag, incoterm = Tag.create({'name': 'a'}), Incoterm.create({'code': 'I'})
        self.env.cr.execute(SQL("INSERT INTO product_tag_product_product_rel VALUES (%s, %s)", tag.id, incoterm.id))
        storage_mongodb._seed_links(Incoterm, {incoterm.id})
        tag.invalidate_recordset()
        self.assertEqual(tag.incoterm_ids, incoterm)

    def test_sweep_keeps_mirror_rows(self):
        # account.account companyIds: the sweep's mirror fill ran before the seed
        # and emptied the PostgreSQL relation rows the seed copies from
        Tag = self.env['test_orm_mongodb.tag']
        tag = Tag.create({'name': 'a'})
        incoterm = self.env['test_orm_mongodb.incoterm'].create({'code': 'I'})
        field = Tag._fields['incoterm_ids']
        self.env.cr.execute(SQL("INSERT INTO product_tag_product_product_rel VALUES (%s, %s)", tag.id, incoterm.id))
        with patch.dict(os.environ, {'ODOO_MONGODB_SWEEP': '1'}):
            storage_mongodb.fill_relation_mirror(field, self.env, storage_mongodb.relation_layout(field, self.env))
            storage_mongodb._seed_links(Tag, {tag.id})
        tag.invalidate_recordset()
        self.assertEqual(tag.incoterm_ids, incoterm)
        self.assertEqual(storage_mongodb.relation_mirror_diff(field, self.env), (set(), set()))

    def test_one2many_many2one_reference_inverse(self):
        # discuss.channel: message_ids' inverse res_id is an integer, not a record
        Tag, Link = self.env['test_orm_mongodb.tag'], self.env['test_orm_mongodb.pg_link']
        tags = Tag.create([{'name': 'a'}, {'name': 'b'}])
        Link.create([
            {'name': 'x', 'res_model': 'test_orm_mongodb.tag', 'res_id': tags[0].id},
            {'name': 'x', 'res_model': 'res.partner', 'res_id': tags[1].id},
        ])
        domain = Domain('id', 'in', tags.ids)
        self.assertEqual(Tag.search(domain & Domain('ref_link_ids', 'any', [('name', '=', 'x')])), tags[0])
        self.assertEqual(Tag.search(domain & Domain('ref_link_ids', 'not any', [('name', '=', 'x')])), tags[1])
        query = Link._search(Domain('name', '=', 'x'))
        self.assertEqual(Tag.search(domain & Domain('ref_link_ids', 'any!', query)), tags[0])

    def test_column_any_subquery(self):
        # mail.message: ('res_id', 'any!', <query of the document model>)
        Tag, Expression = self.env['test_orm_mongodb.tag'], self.env['test_orm_mongodb.report_expression']
        tags = Tag.create([{'name': 'a'}, {'name': 'b'}])
        exprs = Expression.create([{'report_line_id': tags[0].id}, {'report_line_id': tags[1].id}, {}])
        domain = Domain('id', 'in', exprs.ids)
        query = Tag._search(Domain('id', '=', tags[0].id))
        self.assertEqual(Expression.search(domain & Domain('report_line_id', 'any!', query)), exprs[0])
        self.assertEqual(Expression.search(domain & Domain('report_line_id', 'not any!', query)), exprs[1])
        subquery = SQL("SELECT %s", tags[1].id)
        self.assertEqual(Expression.search(domain & Domain('report_line_id', 'any!', subquery)), exprs[1])

    def test_grouped_select_keeps_order(self):
        # mail.message _filter_accessible_from_query groups the rows of a search by id
        Tag = self.env['test_orm_mongodb.tag']
        tags = Tag.create([{'name': 'a', 'sequence': 2}, {'name': 'b', 'sequence': 1}])
        query = Tag._search(Domain('id', 'in', tags.ids), order='sequence')
        query.groupby = query.table.id
        self.env.cr.execute(query.select(query.table.id, SQL("count(*)")))
        self.assertEqual(self.env.cr.fetchall(), [(tags[1].id, 1), (tags[0].id, 1)])
