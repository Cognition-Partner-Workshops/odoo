# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Characterisation tests for business methods that bypass the ORM.

Each class below targets one ``raw_sql.*`` entry of
``backend_neutral_tests/sample.yaml``.  The methods under test build their
result with hand-written queries; these tests only call them through the
public ORM/API surface and pin what a caller can observe: returned values,
record state after the call, and search results.  Nothing here depends on
how the backend computes that result.
"""
import re
import uuid

from odoo import Command
from odoo.exceptions import AccessError

from ..harness import NeutralCase


class TestRawSqlOrmCore(NeutralCase):
    """ raw_sql.orm_core: ``_read_group``, ``_write_multi``, ``_create``,
    ``exists`` and the Many2many relation table helpers. """

    def setUp(self):
        super().setUp()
        self.Item = self.env['test_backend_neutral.item']
        self.Partner = self.env['res.partner']
        self.Category = self.env['res.partner.category']

    def test_create_write_exists_round_trip(self):
        items = self.Item.create([
            {'name': 'Alpha', 'code': 'RA', 'quantity': 1},
            {'name': 'Beta', 'code': 'RB', 'quantity': 2},
        ])
        items.write({'quantity': 7})
        self.env.flush_all()
        self.env.invalidate_all()

        self.assertEqual(items.exists(), items)
        self.assertEqual(items.read(['name', 'code', 'quantity']), [
            {'id': items[0].id, 'name': 'Alpha', 'code': 'RA', 'quantity': 7},
            {'id': items[1].id, 'name': 'Beta', 'code': 'RB', 'quantity': 7},
        ])

        items[0].unlink()
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(items.exists(), items[1])
        self.assertFalse(items[0].exists())
        self.assertFalse(self.Item.browse([items[0].id]).exists())

    def test_read_group_aggregates(self):
        self.Item.create([
            {'name': 'G1', 'code': 'RG1', 'quantity': 3},
            {'name': 'G2', 'code': 'RG2', 'quantity': 5},
            {'name': 'G3', 'code': 'RG3', 'quantity': 3},
        ])
        self.env.flush_all()
        self.env.invalidate_all()

        groups = self.Item._read_group(
            [('code', 'like', 'RG')],
            groupby=['quantity'],
            aggregates=['__count', 'quantity:sum', 'name:array_agg'],
            order='quantity',
        )
        self.assertEqual(groups, [
            (3, 2, 6, ['G1', 'G3']),
            (5, 1, 5, ['G2']),
        ])
        self.assertEqual(
            self.Item._read_group([('code', 'like', 'RG')], aggregates=['quantity:sum']),
            [(11,)],
        )

    def test_many2many_link_is_idempotent(self):
        catA, catB = self.Category.create([{'name': 'RSQL A'}, {'name': 'RSQL B'}])
        partner = self.Partner.create({'name': 'M2M Partner', 'category_id': [Command.link(catA.id)]})
        self.env.flush_all()

        # linking an already-linked pair is a no-op, in the same or another command
        partner.write({'category_id': [Command.link(catA.id), Command.link(catA.id), Command.link(catB.id)]})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(partner.category_id, catA + catB)
        self.assertEqual(catA.partner_ids, partner)
        self.assertEqual(catB.partner_ids, partner)

        partner.write({'category_id': [Command.set((catA + catB).ids)]})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(partner.category_id, catA + catB)

    def test_many2many_unlink_non_linked_pair_is_noop(self):
        catA, catB = self.Category.create([{'name': 'RSQL C'}, {'name': 'RSQL D'}])
        partner = self.Partner.create({'name': 'M2M Partner 2', 'category_id': [Command.link(catA.id)]})
        other = self.Partner.create({'name': 'M2M Partner 3', 'category_id': [Command.link(catB.id)]})
        self.env.flush_all()

        partner.write({'category_id': [Command.unlink(catB.id)]})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(partner.category_id, catA)
        self.assertEqual(other.category_id, catB)

        partner.write({'category_id': [Command.unlink(catA.id)]})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertFalse(partner.category_id)
        self.assertFalse(catA.partner_ids)
        self.assertEqual(catB.partner_ids, other)

        partner.write({'category_id': [Command.clear()]})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertFalse(partner.category_id)

    def test_parent_store_compute_rebuilds_hierarchy(self):
        root = self.Category.create({'name': 'PS Root'})
        child = self.Category.create({'name': 'PS Child', 'parent_id': root.id})
        grandchild = self.Category.create({'name': 'PS Grandchild', 'parent_id': child.id})
        self.env.flush_all()

        self.Category._parent_store_compute()
        self.env.invalidate_all()

        self.assertEqual(root.parent_path, f'{root.id}/')
        self.assertEqual(child.parent_path, f'{root.id}/{child.id}/')
        self.assertEqual(grandchild.parent_path, f'{root.id}/{child.id}/{grandchild.id}/')
        self.assertEqual(
            self.Category.search([('id', 'child_of', root.id)], order='id'),
            root + child + grandchild,
        )
        self.assertEqual(
            self.Category.search([('id', 'parent_of', grandchild.id)], order='id'),
            root + child + grandchild,
        )
        self.assertEqual(self.Category.search([('id', 'child_of', child.id)], order='id'), child + grandchild)


class TestRawSqlAccount(NeutralCase):
    """ raw_sql.account_move: duplicate detection, sequence domain,
    account search ordering, partner credit/debit and invoiced totals. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        if not cls.company.chart_template:
            cls.env['account.chart.template'].try_loading(
                'generic_coa', company=cls.company, install_demo=False)
        cls.partner = cls.env['res.partner'].create({'name': 'RSQL Account Partner'})
        cls.other_partner = cls.env['res.partner'].create({'name': 'RSQL Other Partner'})

    def _invoice(self, move_type, partner, amount, ref=False, date='2026-01-15', post=False):
        move = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'invoice_date': date,
            'date': date,
            'ref': ref,
            'invoice_line_ids': [Command.create({
                'name': 'line',
                'quantity': 1,
                'price_unit': amount,
                'tax_ids': [Command.clear()],
            })],
        })
        if post:
            move.action_post()
        return move

    def test_duplicate_vendor_bill_reference(self):
        bill1 = self._invoice('in_invoice', self.partner, 100.0, ref='BILL-RSQL-1')
        bill2 = self._invoice('in_invoice', self.partner, 250.0, ref='BILL-RSQL-1')
        other_ref = self._invoice('in_invoice', self.partner, 120.0, ref='BILL-RSQL-2')
        other_partner = self._invoice('in_invoice', self.other_partner, 100.0, ref='BILL-RSQL-1')
        self.env.flush_all()
        self.env.invalidate_all()

        self.assertEqual(bill1.duplicated_ref_ids, bill2)
        self.assertEqual(bill2.duplicated_ref_ids, bill1)
        self.assertFalse(other_ref.duplicated_ref_ids)
        self.assertFalse(other_partner.duplicated_ref_ids)

        bill2.ref = 'BILL-RSQL-3'
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertFalse(bill1.duplicated_ref_ids)
        self.assertFalse(bill2.duplicated_ref_ids)

    def test_duplicate_customer_invoice_by_amount_and_date(self):
        inv1 = self._invoice('out_invoice', self.partner, 300.0)
        inv2 = self._invoice('out_invoice', self.partner, 300.0)
        inv_other_amount = self._invoice('out_invoice', self.partner, 301.0)
        inv_other_date = self._invoice('out_invoice', self.partner, 300.0, date='2026-01-16')
        self.env.flush_all()
        self.env.invalidate_all()

        self.assertEqual(inv1.duplicated_ref_ids, inv2)
        self.assertEqual(inv2.duplicated_ref_ids, inv1)
        self.assertFalse(inv_other_amount.duplicated_ref_ids)
        self.assertFalse(inv_other_date.duplicated_ref_ids)

    def test_sequence_continues_from_last_posted_move(self):
        inv1 = self._invoice('out_invoice', self.partner, 10.0, date='2026-03-01', post=True)
        inv2 = self._invoice('out_invoice', self.partner, 20.0, date='2026-03-02', post=True)
        self.env.flush_all()
        self.env.invalidate_all()

        match = re.fullmatch(r'(.*?)(\d+)', inv1.name)
        self.assertTrue(match, inv1.name)
        prefix, number = match.groups()
        self.assertEqual(inv2.name, f'{prefix}{int(number) + 1:0{len(number)}d}')
        self.assertEqual(inv1.sequence_number + 1, inv2.sequence_number)
        self.assertEqual(inv1.sequence_prefix, inv2.sequence_prefix)
        self.assertEqual(inv1.journal_id, inv2.journal_id)

    def test_account_search_order_by_code_matches_python_sort(self):
        Account = self.env['account.account'].with_company(self.company)
        Account.create([
            {'code': 'RSQL9', 'name': 'RSQL nine', 'account_type': 'asset_current'},
            {'code': 'RSQL10', 'name': 'RSQL ten', 'account_type': 'asset_current'},
            {'code': 'RSQL1', 'name': 'RSQL one', 'account_type': 'asset_current'},
        ])
        self.env.flush_all()
        self.env.invalidate_all()

        accounts = Account.search([('company_ids', 'in', self.company.id), ('code', 'like', 'RSQL')], order='code')
        self.assertEqual(accounts.mapped('code'), ['RSQL1', 'RSQL10', 'RSQL9'])
        accounts = Account.search([('company_ids', 'in', self.company.id), ('code', 'like', 'RSQL')], order='code desc')
        self.assertEqual(accounts.mapped('code'), ['RSQL9', 'RSQL10', 'RSQL1'])
        all_accounts = Account.search([('company_ids', 'in', self.company.id)], order='code')
        self.assertEqual(all_accounts.mapped('code'), sorted(all_accounts.mapped('code')))

    def test_account_search_includes_inactive_parents_on_request(self):
        Account = self.env['account.account'].with_company(self.company)
        parent = Account.create({'code': 'RSQLP', 'name': 'RSQL parent', 'account_type': 'asset_current'})
        child = Account.create({'code': 'RSQLP1', 'name': 'RSQL child', 'account_type': 'asset_current', 'parent_id': parent.id})
        parent.active = False
        self.env.flush_all()
        self.env.invalidate_all()

        domain = [('company_ids', 'in', self.company.id), ('code', 'like', 'RSQLP')]
        self.assertEqual(Account.search(domain, order='code'), child)
        self.assertEqual(
            Account.with_context(include_inactive_account_parents=True).search(domain, order='code'),
            parent + child,
        )
        self.assertEqual(child.parent_ids, parent + child)

    def test_partner_credit_debit_follow_posted_open_items(self):
        partner = self.env['res.partner'].create({'name': 'RSQL Balance Partner'})
        self.env.invalidate_all()
        self.assertEqual(partner.credit, 0.0)
        self.assertEqual(partner.debit, 0.0)

        self._invoice('out_invoice', partner, 100.0)  # draft: not counted
        self.env.invalidate_all()
        self.assertEqual(partner.credit, 0.0)

        inv = self._invoice('out_invoice', partner, 100.0, post=True)
        self._invoice('out_invoice', partner, 25.0, post=True)
        self._invoice('in_invoice', partner, 40.0, ref='RSQL-DEBIT', post=True)
        self.env.invalidate_all()
        self.assertEqual(partner.credit, 125.0)
        self.assertEqual(partner.debit, 40.0)

        inv.button_draft()
        self.env.invalidate_all()
        self.assertEqual(partner.credit, 25.0)
        self.assertEqual(partner.debit, 40.0)

        found = self.env['res.partner'].search([('id', '=', partner.id), ('credit', '>', 20.0)])
        self.assertEqual(found, partner)
        self.assertFalse(self.env['res.partner'].search([('id', '=', partner.id), ('credit', '>', 30.0)]))

    def test_partner_total_invoiced(self):
        partner = self.env['res.partner'].create({'name': 'RSQL Invoiced Partner'})
        self._invoice('out_invoice', partner, 100.0, post=True)
        self._invoice('out_invoice', partner, 50.0, post=True)
        self._invoice('out_refund', partner, 30.0, post=True)
        self._invoice('in_invoice', partner, 999.0, ref='RSQL-NOT-SALES', post=True)
        self._invoice('out_invoice', partner, 1000.0)  # draft: not counted
        self.env.invalidate_all()
        self.assertEqual(partner.total_invoiced, 120.0)


class TestRawSqlMailFollowers(NeutralCase):
    """ raw_sql.mail_followers: recipient and subscription data,
    follower-based searches and message access filtering. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'RSQL Mail User',
            'login': 'rsql_mail_user',
            'email': 'rsql.mail.user@example.com',
            'notification_type': 'inbox',
            'group_ids': [Command.link(cls.env.ref('base.group_user').id)],
        })
        cls.follower_comment = cls.env['res.partner'].create({'name': 'RSQL Comment Follower', 'email': 'rsql.comment@example.com'})
        cls.follower_note = cls.env['res.partner'].create({'name': 'RSQL Note Follower', 'email': 'rsql.note@example.com'})
        cls.record = cls.env['res.partner'].create({'name': 'RSQL Thread Record', 'email': 'rsql.thread@example.com'})
        cls.mt_comment = cls.env.ref('mail.mt_comment')
        cls.mt_note = cls.env.ref('mail.mt_note')

    def test_message_post_recipients_follow_subscriptions(self):
        self.record.message_subscribe(partner_ids=self.follower_comment.ids, subtype_ids=self.mt_comment.ids)
        self.record.message_subscribe(partner_ids=self.follower_note.ids, subtype_ids=self.mt_note.ids)
        self.record.message_subscribe(partner_ids=self.user.partner_id.ids, subtype_ids=(self.mt_comment + self.mt_note).ids)
        self.env.flush_all()

        followers = self.record.message_follower_ids
        self.assertEqual(followers.mapped('partner_id'), self.follower_comment + self.follower_note + self.user.partner_id)
        self.assertEqual(followers.filtered(lambda f: f.partner_id == self.follower_comment).subtype_ids, self.mt_comment)
        self.assertEqual(followers.filtered(lambda f: f.partner_id == self.follower_note).subtype_ids, self.mt_note)

        comment = self.record.message_post(body='comment body', message_type='comment', subtype_xmlid='mail.mt_comment')
        note = self.record.message_post(body='note body', message_type='comment', subtype_xmlid='mail.mt_note')
        self.env.flush_all()
        self.env.invalidate_all()

        self.assertEqual(comment.notified_partner_ids, self.follower_comment + self.user.partner_id)
        # notes are internal: the external follower of the note subtype is not notified
        self.assertEqual(note.notified_partner_ids, self.user.partner_id)
        self.assertEqual(
            comment.notification_ids.filtered(lambda n: n.res_partner_id == self.user.partner_id).notification_type,
            'inbox',
        )
        self.assertEqual(
            comment.notification_ids.filtered(lambda n: n.res_partner_id == self.follower_comment).notification_type,
            'email',
        )

    def test_message_post_to_partner_not_following(self):
        self.record.message_subscribe(partner_ids=self.follower_comment.ids, subtype_ids=self.mt_comment.ids)
        message = self.record.message_post(
            body='direct', message_type='comment', subtype_xmlid='mail.mt_comment',
            partner_ids=self.follower_note.ids,
        )
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(message.notified_partner_ids, self.follower_comment + self.follower_note)
        self.assertEqual(message.partner_ids, self.follower_note)

    def test_search_message_is_follower_and_message_partner_ids(self):
        other = self.env['res.partner'].create({'name': 'RSQL Unfollowed Record'})
        self.record.message_subscribe(partner_ids=self.user.partner_id.ids)
        other.message_subscribe(partner_ids=self.follower_note.ids)
        self.env.flush_all()
        self.env.invalidate_all()

        Partner = self.env['res.partner'].with_user(self.user)
        both = [('id', 'in', (self.record + other).ids)]
        self.assertEqual(Partner.search(both + [('message_is_follower', '=', True)]), self.record)
        self.assertEqual(Partner.search(both + [('message_is_follower', '=', False)]), other)
        self.assertEqual(Partner.search(both + [('message_is_follower', '!=', True)]), other)
        self.assertEqual(Partner.search(both + [('message_partner_ids', 'in', self.follower_note.ids)]), other)
        self.assertEqual(Partner.search(both + [('message_partner_ids', 'not in', self.follower_note.ids)]), self.record)
        self.assertEqual(Partner.search(both + [('message_partner_ids', '=', False)]), Partner.browse())
        self.assertTrue(Partner.browse(self.record.id).message_is_follower)
        self.assertFalse(Partner.browse(other.id).message_is_follower)

        self.record.message_unsubscribe(partner_ids=self.user.partner_id.ids)
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertFalse(Partner.search(both + [('message_is_follower', '=', True)]))

    def test_message_search_filters_inaccessible_messages(self):
        Message = self.env['mail.message']
        on_record = self.record.message_post(body='public on record', message_type='comment', subtype_xmlid='mail.mt_note')
        addressed = Message.create({
            'body': 'addressed to the user',
            'message_type': 'comment',
            'partner_ids': [Command.link(self.user.partner_id.id)],
        })
        private = Message.create({'body': 'nobody can see this', 'message_type': 'comment'})
        self.env.flush_all()
        self.env.invalidate_all()

        domain = [('id', 'in', (on_record + addressed + private).ids)]
        as_user = Message.with_user(self.user)
        self.assertEqual(as_user.search(domain, order='id'), on_record + addressed)
        self.assertEqual(as_user.search_count(domain), 2)
        self.assertEqual(Message.search(domain, order='id'), on_record + addressed + private)
        self.assertEqual(as_user.browse(addressed.id).body, '<p>addressed to the user</p>')
        with self.assertRaises(AccessError):
            as_user.browse(private.id).body  # noqa: B018


class TestRawSqlWebsite(NeutralCase):
    """ raw_sql.website: snippet usage detection and visitor upsert. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1, order='id')

    def test_snippet_usage_follows_html_content(self):
        html_fields = self.website._get_html_fields()
        self.assertIn(('ir.ui.view', 'arch_db'), html_fields)
        is_used = lambda version: self.website._is_snippet_used(  # noqa: E731
            'website', 's_rsql_probe', version, 'css', html_fields)

        def holder_arch(section):
            return f'<t t-name="website.rsql_snippet_holder"><div>{section}</div></t>'

        self.assertFalse(is_used('000'))
        self.assertFalse(is_used('001'))

        view = self.env['ir.ui.view'].create({
            'name': 'RSQL snippet holder',
            'type': 'qweb',
            'key': 'website.rsql_snippet_holder',
            'arch': holder_arch('<section class="s_rsql_probe" data-snippet="s_rsql_probe" data-vcss="001"><p>x</p></section>'),
        })
        self.env.flush_all()
        self.assertTrue(is_used('001'))
        self.assertFalse(is_used('000'))
        self.assertFalse(is_used('002'))
        self.assertFalse(self.website._is_snippet_used('website', 's_rsql_other', '001', 'css', html_fields))

        view.arch = holder_arch('<section class="s_rsql_probe" data-snippet="s_rsql_probe"><p>x</p></section>')
        self.env.flush_all()
        self.assertTrue(is_used('000'))
        self.assertFalse(is_used('001'))

        view.arch = holder_arch('<p>no snippet any more</p>')
        self.env.flush_all()
        self.assertFalse(is_used('000'))
        self.assertFalse(is_used('001'))

    def test_visitor_upsert_is_idempotent_by_access_token(self):
        token = uuid.uuid4().hex
        website_id = self.website.id

        with self.independent_transaction() as transaction:
            Visitor = transaction.env['website.visitor']
            visitor_id, status = Visitor._upsert_visitor(token, website_id)
            self.assertEqual(status, 'inserted')
            visitor = Visitor.browse(visitor_id)
            self.assertEqual(visitor.access_token, token)
            self.assertEqual(visitor.website_id.id, website_id)
            self.assertEqual(visitor.visit_count, 1)
            self.assertEqual(Visitor.search([('access_token', '=', token)]), visitor)
            transaction.commit_transaction()
            self.track_committed(visitor)

        with self.independent_transaction() as transaction:
            Visitor = transaction.env['website.visitor']
            again_id, status = Visitor._upsert_visitor(token, website_id)
            self.assertEqual(status, 'updated')
            self.assertEqual(again_id, visitor_id)
            transaction.env.invalidate_all()
            self.assertEqual(Visitor.search_count([('access_token', '=', token)]), 1)
            self.assertEqual(Visitor.browse(visitor_id).visit_count, 1)

            other_id, status = Visitor._upsert_visitor(uuid.uuid4().hex, website_id)
            self.assertEqual(status, 'inserted')
            self.assertNotEqual(other_id, visitor_id)
            self.assertEqual(Visitor.browse(other_id).visit_count, 1)


class TestRawSqlStockQuant(NeutralCase):
    """ raw_sql.stock_quant: quant merging, zero-quant cleanup and the
    least-packages removal strategy. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.product = cls.env['product.product'].create({'name': 'RSQL Storable', 'is_storable': True})
        cls.Quant = cls.env['stock.quant']

    def _quant_vals(self, quantity, package=None):
        return {
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': quantity,
            'package_id': package.id if package else False,
        }

    def test_duplicate_quants_merge_into_one(self):
        self.Quant.create([self._quant_vals(4.0), self._quant_vals(6.0), self._quant_vals(2.5)])
        self.env.flush_all()
        domain = [('product_id', '=', self.product.id), ('location_id', '=', self.location.id)]
        self.assertEqual(self.Quant.search_count(domain), 3)

        self.Quant._merge_quants()
        self.env.invalidate_all()

        quants = self.Quant.search(domain)
        self.assertEqual(len(quants), 1)
        self.assertEqual(quants.quantity, 12.5)
        self.assertEqual(self.Quant._get_available_quantity(self.product, self.location), 12.5)
        self.assertEqual(self.product.qty_available, 12.5)

    def test_zero_quants_are_removed(self):
        zero = self.Quant.create(self._quant_vals(0.0))
        kept = self.Quant.create(self._quant_vals(3.0))
        self.env.flush_all()

        self.Quant._unlink_zero_quants()
        self.env.invalidate_all()

        self.assertFalse(zero.exists())
        self.assertEqual(kept.exists(), kept)
        self.assertEqual(kept.quantity, 3.0)

        self.Quant._update_available_quantity(self.product, self.location, -3.0)
        self.env.flush_all()
        self.Quant._unlink_zero_quants()
        self.env.invalidate_all()
        self.assertFalse(kept.exists())
        self.assertEqual(self.Quant._get_available_quantity(self.product, self.location), 0.0)

    def test_least_packages_removal_strategy(self):
        self.location.removal_strategy_id = self.env.ref('stock.removal_least_packages')
        Package = self.env['stock.package']
        small, medium, large = Package.create([{'name': 'RSQL-PK-1'}, {'name': 'RSQL-PK-2'}, {'name': 'RSQL-PK-3'}])
        self.Quant._update_available_quantity(self.product, self.location, 2.0, package_id=small)
        self.Quant._update_available_quantity(self.product, self.location, 3.0, package_id=medium)
        self.Quant._update_available_quantity(self.product, self.location, 5.0, package_id=large)
        self.env.flush_all()
        self.env.invalidate_all()

        reserved = self.Quant._get_reserve_quantity(self.product, self.location, 5.0)
        self.assertEqual([(q.package_id, qty) for q, qty in reserved], [(large, 5.0)])

        reserved = self.Quant._get_reserve_quantity(self.product, self.location, 3.0)
        self.assertEqual([(q.package_id, qty) for q, qty in reserved], [(medium, 3.0)])

        reserved = self.Quant._get_reserve_quantity(self.product, self.location, 4.0)
        self.assertEqual(sum(qty for _, qty in reserved), 4.0)
        self.assertEqual(len(reserved), 1)
        self.assertEqual(reserved[0][0].package_id, large)


class TestRawSqlSaleProjectPos(NeutralCase):
    """ raw_sql.sale_project: duplicate orders, invoice search, portal
    user names search and POS order search. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        if not cls.company.chart_template:
            cls.env['account.chart.template'].try_loading(
                'generic_coa', company=cls.company, install_demo=False)
        cls.partner = cls.env['res.partner'].create({'name': 'RSQL Sale Partner'})
        cls.service = cls.env['product.product'].create({
            'name': 'RSQL Service',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 100.0,
        })

    def _order(self, partner=None, ref=False, origin=False):
        return self.env['sale.order'].create({
            'partner_id': (partner or self.partner).id,
            'client_order_ref': ref,
            'origin': origin,
            'order_line': [Command.create({'product_id': self.service.id, 'product_uom_qty': 1})],
        })

    def test_duplicate_orders_by_reference_and_origin(self):
        so1 = self._order(ref='RSQL-REF-1')
        so2 = self._order(ref='RSQL-REF-1')
        from_origin = self._order(ref='RSQL-REF-OTHER', origin=so1.name)
        unrelated = self._order(ref='RSQL-REF-2')
        no_ref = self._order(origin=so1.name)
        other_partner = self._order(partner=self.env['res.partner'].create({'name': 'RSQL Dup Other'}), ref='RSQL-REF-1')
        self.env.flush_all()
        self.env.invalidate_all()

        self.assertEqual(so1.duplicated_order_ids, so2)
        self.assertEqual(so2.duplicated_order_ids, so1)
        # origin matching is one-way: the order whose origin names another one
        self.assertEqual(from_origin.duplicated_order_ids, so1)
        self.assertFalse(unrelated.duplicated_order_ids)
        # only orders with a customer reference get duplicates computed
        self.assertFalse(no_ref.duplicated_order_ids)
        self.assertFalse(other_partner.duplicated_order_ids)

        so1.action_confirm()
        so1.action_cancel()
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertFalse(so2.duplicated_order_ids)
        self.assertFalse(from_origin.duplicated_order_ids)
        # only draft orders are checked for duplicates
        self.assertFalse(so1.duplicated_order_ids)

    def test_search_orders_by_invoice(self):
        invoiced = self._order(ref='RSQL-INV')
        invoiced.action_confirm()
        invoice = invoiced._create_invoices()
        not_invoiced = self._order(ref='RSQL-NOINV')
        self.env.flush_all()
        self.env.invalidate_all()

        Order = self.env['sale.order']
        both = [('id', 'in', (invoiced + not_invoiced).ids)]
        self.assertEqual(invoiced.invoice_ids, invoice)
        self.assertEqual(Order.search(both + [('invoice_ids', 'in', invoice.ids)]), invoiced)
        self.assertEqual(Order.search(both + [('invoice_ids', '=', False)]), not_invoiced)
        self.assertEqual(Order.search(both + [('invoice_ids', '!=', False)]), invoiced)
        self.assertEqual(Order.search(both + [('invoice_ids.partner_id', '=', self.partner.id)]), invoiced)
        self.assertEqual(Order.search(both + [('invoice_ids', 'not in', invoice.ids)]), not_invoiced)

    def test_search_tasks_by_portal_user_names(self):
        user_a, user_b = self.env['res.users'].create([
            {'name': 'RSQL Zelda Assignee', 'login': 'rsql_zelda', 'group_ids': [Command.link(self.env.ref('base.group_user').id)]},
            {'name': 'RSQL Yorick Assignee', 'login': 'rsql_yorick', 'group_ids': [Command.link(self.env.ref('base.group_user').id)]},
        ])
        project = self.env['project.project'].create({'name': 'RSQL Project'})
        Task = self.env['project.task']
        task_a, task_b, task_none = Task.create([
            {'name': 'RSQL Task A', 'project_id': project.id, 'user_ids': [Command.set(user_a.ids)]},
            {'name': 'RSQL Task B', 'project_id': project.id, 'user_ids': [Command.set((user_a + user_b).ids)]},
            {'name': 'RSQL Task None', 'project_id': project.id},
        ])
        self.env.flush_all()
        self.env.invalidate_all()

        scope = [('project_id', '=', project.id)]
        self.assertEqual(Task.search(scope + [('portal_user_names', 'ilike', 'Zelda')], order='id'), task_a + task_b)
        self.assertEqual(Task.search(scope + [('portal_user_names', 'ilike', 'Yorick')]), task_b)
        self.assertEqual(Task.search(scope + [('portal_user_names', 'ilike', 'Nobody')]), Task.browse())
        self.assertEqual(Task.search(scope + [('portal_user_names', 'not ilike', 'Zelda')]), task_none)
        self.assertEqual(task_b.portal_user_names, 'RSQL Yorick Assignee and RSQL Zelda Assignee')

    def test_pos_search_order_ids(self):
        PosConfig = self.env['pos.config']
        bank_journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', self.company.id)], limit=1)
        bank_method = self.env['pos.payment.method'].create({'name': 'RSQL Bank', 'type': 'bank', 'journal_id': bank_journal.id})
        config = PosConfig.create({'name': 'RSQL POS'})
        other_config = PosConfig.create({'name': 'RSQL Other POS', 'payment_method_ids': [Command.set(bank_method.ids)]})
        config.open_ui()
        other_config.open_ui()
        pos_product = self.env['product.product'].create({'name': 'RSQL POS Product', 'available_in_pos': True, 'list_price': 10.0})

        def order_vals(session, state, paid):
            return {
                'company_id': self.company.id,
                'session_id': session.id,
                'partner_id': self.partner.id,
                'lines': [Command.create({
                    'product_id': pos_product.id,
                    'qty': 1,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                })],
                'amount_tax': 0.0,
                'amount_total': 10.0,
                'amount_paid': paid,
                'amount_return': 0.0,
                'state': state,
            }

        Order = self.env['pos.order']
        paid_here, paid_other, cancelled_here, draft_here = Order.create([
            order_vals(config.current_session_id, 'paid', 10.0),
            order_vals(other_config.current_session_id, 'paid', 10.0),
            order_vals(config.current_session_id, 'cancel', 0.0),
            order_vals(config.current_session_id, 'draft', 0.0),
        ])
        self.env.flush_all()
        self.env.invalidate_all()

        def found(domain, **kwargs):
            result = Order.search_order_ids(config.id, domain, 80, 0, **kwargs)
            return [info[0] for info in result['ordersInfo']]

        paid_ids = found([], state_filter='paid')
        self.assertIn(paid_here.id, paid_ids)
        self.assertNotIn(paid_other.id, paid_ids)
        self.assertNotIn(cancelled_here.id, paid_ids)
        self.assertNotIn(draft_here.id, paid_ids)

        self.assertEqual(found([('id', 'in', (paid_here + paid_other).ids)], state_filter='paid'), [paid_here.id])
        self.assertEqual(found([('partner_id.complete_name', 'ilike', 'RSQL Sale Partner'), ('state', '=', 'paid')]), [paid_here.id])
        self.assertEqual(found([('partner_id.complete_name', 'ilike', 'No Such Partner')]), [])
