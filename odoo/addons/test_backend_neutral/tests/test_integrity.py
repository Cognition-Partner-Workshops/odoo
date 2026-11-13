""" Neutral tests of the `integrity.*` targets of backend_neutral_tests/sample.yaml:
the rules the database enforces today (unique, check, not-null, foreign key
ondelete), asserted through the ORM only.

Each target has at least one positive test (the rule lets valid data through)
and one negative test (the rule refuses invalid data, and nothing is left
behind). What is asserted after a refused write is re-read after
``invalidate_all()`` so the cache cannot hide the state of the storage.
"""
from datetime import date, timedelta

from odoo.addons.test_backend_neutral.harness import NeutralCase, errors


class TestIntegrityResUsers(NeutralCase):
    """ integrity.res_users: UNIQUE(login), CHECK on partner type/name,
    Many2one partner_id ondelete='restrict'.

    A duplicate login is refused by the unique index, or earlier by the
    Python constraint ``_check_login`` when ``website`` is installed with
    the combined suite; both refusals are asserted. """

    DUPLICATE_LOGIN_REFUSED = (errors.IntegrityError, errors.ValidationError)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Users = cls.env['res.users']
        cls.Partner = cls.env['res.partner']
        cls.user = cls.Users.create({'name': 'Neutral User', 'login': 'neutral_user'})

    def test_login_unique_distinct_logins_accepted(self):
        other = self.Users.create({'name': 'Other User', 'login': 'neutral_other'})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(self.Users.search([('login', 'in', ['neutral_user', 'neutral_other'])]), self.user + other)

    def test_login_unique_duplicate_create_refused(self):
        with self.assertRaises(self.DUPLICATE_LOGIN_REFUSED):
            self.Users.create({'name': 'Duplicate User', 'login': 'neutral_user'})
        self.env.invalidate_all()
        self.assertEqual(self.Users.search([('login', '=', 'neutral_user')]), self.user)

    def test_login_unique_duplicate_write_refused(self):
        other = self.Users.create({'name': 'Other User', 'login': 'neutral_other'})
        with self.assertRaises(self.DUPLICATE_LOGIN_REFUSED):
            other.login = 'neutral_user'
        self.env.invalidate_all()
        self.assertEqual(other.login, 'neutral_other')
        self.assertEqual(self.Users.search_count([('login', '=', 'neutral_user')]), 1)

    def test_partner_name_check_non_contact_without_name_accepted(self):
        company = self.Partner.create({'name': 'Neutral Company', 'is_company': True})
        address = self.Partner.create({'type': 'delivery', 'parent_id': company.id, 'street': 'Somewhere'})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertTrue(address.exists())
        self.assertFalse(address.name)
        self.assertEqual(address.type, 'delivery')

    def test_partner_name_check_contact_without_name_refused(self):
        with self.assertIntegrityError():
            self.Partner.create({'type': 'contact', 'email': 'nameless@example.com'})
        self.env.invalidate_all()
        self.assertFalse(self.Partner.search([('email', '=', 'nameless@example.com')]))

    def test_partner_name_check_contact_name_cleared_refused(self):
        contact = self.Partner.create({'name': 'Named Contact', 'type': 'contact'})
        with self.assertIntegrityError():
            contact.name = False
        self.env.invalidate_all()
        self.assertEqual(contact.name, 'Named Contact')

    def test_partner_restrict_partner_without_user_unlinked(self):
        partner = self.Partner.create({'name': 'Free Partner'})
        partner.unlink()
        self.env.invalidate_all()
        self.assertFalse(partner.exists())

    def test_partner_restrict_partner_of_archived_user_kept(self):
        # the ORM itself refuses to unlink the partner of an *active* user; once
        # the user is archived only the storage rule stands in the way
        partner = self.user.partner_id
        self.user.action_archive()
        self.env.flush_all()
        with self.assertIntegrityError():
            partner.unlink()
        self.env.invalidate_all()
        self.assertTrue(partner.exists())
        self.assertEqual(self.user.partner_id, partner)
        self.assertEqual(
            self.Users.with_context(active_test=False).search([('partner_id', '=', partner.id)]),
            self.user,
        )


class TestIntegrityAccountMove(NeutralCase):
    """ integrity.account_move: partial UniqueIndex (name, journal_id) on
    posted entries, CHECK document_tax_mode set on invoices, CHECK
    credit*debit=0, CHECK account required on accountable lines / forbidden
    balance on non-accountable lines, Many2one move_id ondelete='cascade'. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Move = cls.env['account.move']
        cls.Line = cls.env['account.move.line']
        cls.customer = cls.env['res.partner'].create({'name': 'Neutral Invoiced Customer'})
        cls.journal = cls.env['account.journal'].create({
            'name': 'Neutral Miscellaneous',
            'code': 'NEUTR',
            'type': 'general',
        })
        cls.account_a, cls.account_b = cls.env['account.account'].create([
            {'name': 'Neutral A', 'code': 'NEUT.A', 'account_type': 'asset_current'},
            {'name': 'Neutral B', 'code': 'NEUT.B', 'account_type': 'liability_current'},
        ])

    @classmethod
    def _move_values(cls, amount=100.0, **values):
        return {
            'journal_id': cls.journal.id,
            'date': date(2024, 3, 15),
            'line_ids': [
                (0, 0, {'account_id': cls.account_a.id, 'debit': amount, 'credit': 0.0}),
                (0, 0, {'account_id': cls.account_b.id, 'debit': 0.0, 'credit': amount}),
            ],
            **values,
        }

    def test_unique_name_drafts_share_a_name(self):
        first, second = self.Move.create([self._move_values(), self._move_values()])
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(first.name, second.name)
        self.assertEqual(first.journal_id, second.journal_id)
        self.assertEqual(
            self.Move.search([('name', '=', first.name), ('journal_id', '=', self.journal.id)]),
            first + second,
        )

    def test_unique_name_draft_may_share_posted_name(self):
        first, second = self.Move.create([self._move_values(), self._move_values()])
        first.action_post()
        self.env.flush_all()
        second.name = first.name
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual((first.state, second.state), ('posted', 'draft'))
        self.assertEqual(second.name, first.name)
        self.assertEqual(
            self.Move.search([('name', '=', first.name), ('journal_id', '=', self.journal.id)]),
            first + second,
        )

    def test_unique_name_posted_moves_get_distinct_names(self):
        first, second = self.Move.create([self._move_values(), self._move_values()])
        (first + second).action_post()
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual((first + second).mapped('state'), ['posted', 'posted'])
        self.assertNotEqual(first.name, '/')
        self.assertNotEqual(first.name, second.name)

    def test_unique_name_posted_duplicate_refused(self):
        first, second = self.Move.create([self._move_values(), self._move_values()])
        (first + second).action_post()
        self.env.flush_all()
        taken = first.name
        with self.assertIntegrityError():
            second.name = taken
        self.env.invalidate_all()
        self.assertNotEqual(second.name, taken)
        self.assertEqual(self.Move.search([('name', '=', taken), ('journal_id', '=', self.journal.id)]), first)

    def test_credit_debit_check_one_sided_lines_accepted(self):
        move = self.Move.create(self._move_values(amount=40.0))
        self.env.flush_all()
        self.env.invalidate_all()
        debit_line, credit_line = move.line_ids.sorted('id')
        self.assertEqual((debit_line.debit, debit_line.credit), (40.0, 0.0))
        self.assertEqual((credit_line.debit, credit_line.credit), (0.0, 40.0))

    def test_credit_debit_check_both_sides_collapse_to_one(self):
        # debit and credit are two views of the balance: the ORM never hands
        # the storage a line with both sides set, so the rule always holds
        move = self.Move.create(self._move_values(amount=40.0))
        self.env.flush_all()
        move.line_ids.write({'debit': 10.0, 'credit': 10.0})
        self.env.flush_all()
        self.env.invalidate_all()
        for line in move.line_ids:
            self.assertEqual(line.debit * line.credit, 0.0)
            self.assertEqual(line.balance, line.debit - line.credit)

    def test_accountable_required_fields_note_without_account_accepted(self):
        move = self.Move.create(self._move_values())
        note = self.Line.create({'move_id': move.id, 'display_type': 'line_note', 'name': 'A note'})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertTrue(note.exists())
        self.assertFalse(note.account_id)
        self.assertIn(note, move.line_ids)

    def test_accountable_required_fields_product_line_without_account_refused(self):
        move = self.Move.create(self._move_values())
        self.env.flush_all()
        with self.assertIntegrityError():
            self.Line.create({
                'move_id': move.id,
                'display_type': 'product',
                'name': 'No account',
                'debit': 10.0,
                'credit': 0.0,
            })
        self.env.invalidate_all()
        self.assertEqual(len(move.line_ids), 2)
        self.assertFalse(self.Line.search([('move_id', '=', move.id), ('name', '=', 'No account')]))

    def test_non_accountable_fields_note_with_balance_refused(self):
        move = self.Move.create(self._move_values())
        self.env.flush_all()
        with self.assertIntegrityError():
            self.Line.create({
                'move_id': move.id,
                'display_type': 'line_note',
                'name': 'Priced note',
                'debit': 5.0,
            })
        self.env.invalidate_all()
        self.assertEqual(len(move.line_ids), 2)
        self.assertFalse(self.Line.search([('move_id', '=', move.id), ('display_type', '=', 'line_note')]))

    def test_document_tax_mode_check_invoice_gets_a_mode(self):
        invoice = self.Move.create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_date': date(2024, 3, 15),
        })
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertTrue(invoice.exists())
        self.assertTrue(invoice.document_tax_mode)

    def test_document_tax_mode_check_invoice_without_mode_refused(self):
        invoice = self.Move.create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_date': date(2024, 3, 15),
        })
        self.env.flush_all()
        mode = invoice.document_tax_mode
        with self.assertIntegrityError():
            invoice.document_tax_mode = False
        self.env.invalidate_all()
        self.assertEqual(invoice.document_tax_mode, mode)

    def test_cascade_lines_follow_their_move(self):
        move, other = self.Move.create([self._move_values(), self._move_values(amount=7.0)])
        self.env.flush_all()
        line_ids = move.line_ids.ids
        other_line_ids = other.line_ids.ids
        self.assertEqual(len(line_ids), 2)

        move.unlink()
        self.env.invalidate_all()
        self.assertFalse(move.exists())
        self.assertFalse(self.Line.browse(line_ids).exists())
        self.assertFalse(self.Line.search([('move_id', '=', move.id)]))
        # the lines of the other move are untouched
        self.assertEqual(other.line_ids.ids, other_line_ids)


class TestIntegrityHrLeave(NeutralCase):
    """ integrity.hr_leave: CHECK date_from <= date_to, CHECK request_date_from
    <= request_date_to, CHECK number_of_days >= 0, Many2one employee_id
    ondelete='restrict'. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Leave = cls.env['hr.leave']
        cls.employee = cls.env['hr.employee'].create({'name': 'Neutral Employee'})
        cls.leave_type = cls.env['hr.work.entry.type'].create({
            'name': 'Neutral Time Off',
            'code': 'NEUTRAL_TO',
            'requires_allocation': False,
            'leave_validation_type': 'no_validation',
            'request_unit': 'day',
        })
        # a Wednesday and the Thursday after it
        cls.day_from = date(2024, 3, 13)
        cls.day_to = date(2024, 3, 14)

    def _leave_values(self, **values):
        return {
            'name': 'Neutral Leave',
            'employee_id': self.employee.id,
            'work_entry_type_id': self.leave_type.id,
            'request_date_from': self.day_from,
            'request_date_to': self.day_to,
            **values,
        }

    def test_date_check_ordered_dates_accepted(self):
        leave = self.Leave.create(self._leave_values())
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertTrue(leave.exists())
        self.assertEqual((leave.request_date_from, leave.request_date_to), (self.day_from, self.day_to))
        self.assertLessEqual(leave.date_from, leave.date_to)
        self.assertGreaterEqual(leave.number_of_days, 0)

    def test_date_check_reversed_dates_on_create_refused(self):
        with self.assertIntegrityError():
            self.Leave.create(self._leave_values(
                request_date_from=self.day_to,
                request_date_to=self.day_from,
            ))
        self.env.invalidate_all()
        self.assertFalse(self.Leave.search([('employee_id', '=', self.employee.id)]))

    def test_date_check_reversed_dates_on_write_refused(self):
        leave = self.Leave.create(self._leave_values())
        self.env.flush_all()
        with self.assertIntegrityError():
            leave.write({
                'request_date_from': self.day_to,
                'request_date_to': self.day_from,
            })
        self.env.invalidate_all()
        self.assertEqual((leave.request_date_from, leave.request_date_to), (self.day_from, self.day_to))

    def test_duration_check_negative_duration_refused(self):
        leave = self.Leave.create(self._leave_values())
        self.env.flush_all()
        duration = leave.number_of_days
        with self.assertIntegrityError():
            leave.number_of_days = -1.0
        self.env.invalidate_all()
        self.assertEqual(leave.number_of_days, duration)

    def test_employee_restrict_employee_without_leave_unlinked(self):
        employee = self.env['hr.employee'].create({'name': 'Leaving Employee'})
        employee.unlink()
        self.env.invalidate_all()
        self.assertFalse(employee.exists())

    def test_employee_restrict_employee_with_leave_kept(self):
        leave = self.Leave.create(self._leave_values())
        self.env.flush_all()
        with self.assertIntegrityError():
            self.employee.unlink()
        self.env.invalidate_all()
        self.assertTrue(self.employee.exists())
        self.assertEqual(leave.employee_id, self.employee)


class TestIntegrityMailFollowers(NeutralCase):
    """ integrity.mail_followers: unique (res_model, res_id, partner_id),
    partner_id required and ondelete='cascade'; discuss.channel.member:
    partial unique (channel_id, partner_id), XOR CHECK partner/guest. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Followers = cls.env['mail.followers']
        cls.Member = cls.env['discuss.channel.member']
        cls.partner, cls.other_partner = cls.env['res.partner'].create([
            {'name': 'Neutral Follower'},
            {'name': 'Other Follower'},
        ])
        cls.record = cls.env['res.partner'].create({'name': 'Followed Record'})
        cls.channel = cls.env['discuss.channel'].create({'name': 'Neutral Channel', 'channel_type': 'channel'})
        cls.guest = cls.env['mail.guest'].create({'name': 'Neutral Guest'})

    def _followers(self, record):
        return self.Followers.search([('res_model', '=', record._name), ('res_id', '=', record.id)])

    def test_follower_unique_subscribe_twice_keeps_one(self):
        self.record.message_subscribe(partner_ids=self.partner.ids)
        self.record.message_subscribe(partner_ids=self.partner.ids)
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(self._followers(self.record).partner_id, self.partner)
        self.assertEqual(len(self._followers(self.record)), 1)

    def test_follower_unique_distinct_partners_accepted(self):
        followers = self.Followers.create([
            {'res_model': self.record._name, 'res_id': self.record.id, 'partner_id': self.partner.id},
            {'res_model': self.record._name, 'res_id': self.record.id, 'partner_id': self.other_partner.id},
        ])
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(self._followers(self.record), followers)

    def test_follower_unique_duplicate_create_refused(self):
        follower = self.Followers.create({
            'res_model': self.record._name, 'res_id': self.record.id, 'partner_id': self.partner.id,
        })
        self.env.flush_all()
        with self.assertIntegrityError():
            self.Followers.create({
                'res_model': self.record._name, 'res_id': self.record.id, 'partner_id': self.partner.id,
            })
        self.env.invalidate_all()
        self.assertEqual(self._followers(self.record), follower)

    def test_follower_partner_required(self):
        with self.assertIntegrityError():
            self.Followers.create({'res_model': self.record._name, 'res_id': self.record.id})
        self.env.invalidate_all()
        self.assertFalse(self._followers(self.record))

    def test_follower_cascade_unlinked_with_partner(self):
        partner = self.env['res.partner'].create({'name': 'Short-lived Follower'})
        self.record.message_subscribe(partner_ids=(partner + self.partner).ids)
        self.env.flush_all()
        follower = self._followers(self.record).filtered(lambda f: f.partner_id == partner)
        self.assertTrue(follower)

        partner.unlink()
        self.env.invalidate_all()
        self.assertFalse(partner.exists())
        self.assertFalse(follower.exists())
        self.assertEqual(self._followers(self.record).partner_id, self.partner)

    def test_member_unique_distinct_partners_accepted(self):
        members = self.Member.create([
            {'channel_id': self.channel.id, 'partner_id': self.partner.id},
            {'channel_id': self.channel.id, 'partner_id': self.other_partner.id},
        ])
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(members.channel_id, self.channel)
        self.assertEqual(members.partner_id, self.partner + self.other_partner)
        self.assertFalse(members.guest_id)

    def test_member_unique_same_partner_twice_refused(self):
        member = self.Member.create({'channel_id': self.channel.id, 'partner_id': self.partner.id})
        self.env.flush_all()
        with self.assertIntegrityError():
            self.Member.create({'channel_id': self.channel.id, 'partner_id': self.partner.id})
        self.env.invalidate_all()
        self.assertEqual(
            self.Member.search([('channel_id', '=', self.channel.id), ('partner_id', '=', self.partner.id)]),
            member,
        )

    def test_member_unique_same_guest_twice_refused(self):
        member = self.Member.create({'channel_id': self.channel.id, 'guest_id': self.guest.id})
        self.env.flush_all()
        with self.assertIntegrityError():
            self.Member.create({'channel_id': self.channel.id, 'guest_id': self.guest.id})
        self.env.invalidate_all()
        self.assertEqual(
            self.Member.search([('channel_id', '=', self.channel.id), ('guest_id', '=', self.guest.id)]),
            member,
        )

    def _members(self):
        return self.Member.search([('channel_id', '=', self.channel.id)])

    def test_member_xor_check_neither_partner_nor_guest_refused(self):
        members = self._members()
        with self.assertIntegrityError():
            self.Member.create({'channel_id': self.channel.id})
        self.env.invalidate_all()
        self.assertEqual(self._members(), members)

    def test_member_xor_check_both_partner_and_guest_refused(self):
        members = self._members()
        with self.assertIntegrityError():
            self.Member.create({
                'channel_id': self.channel.id,
                'partner_id': self.partner.id,
                'guest_id': self.guest.id,
            })
        self.env.invalidate_all()
        self.assertEqual(self._members(), members)
        self.assertNotIn(self.partner, members.partner_id)
        self.assertNotIn(self.guest, members.guest_id)

    def test_member_cascade_unlinked_with_partner(self):
        partner = self.env['res.partner'].create({'name': 'Short-lived Member'})
        member = self.Member.create({'channel_id': self.channel.id, 'partner_id': partner.id})
        self.env.flush_all()

        partner.unlink()
        self.env.invalidate_all()
        self.assertFalse(member.exists())
        self.assertFalse(self.Member.search([('channel_id', '=', self.channel.id), ('partner_id', '=', partner.id)]))
        self.assertTrue(self.channel.exists())


class TestIntegrityStockLocation(NeutralCase):
    """ integrity.stock_location: unique (barcode, company_id) with empty
    barcodes allowed, CHECK cyclic_inventory_frequency >= 0, stock.quant
    product_id / location_id ondelete='restrict', orderpoint unique
    (product_id, location_id, company_id). """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Location = cls.env['stock.location']
        cls.Quant = cls.env['stock.quant']
        cls.Orderpoint = cls.env['stock.warehouse.orderpoint']
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.location = cls.Location.create({
            'name': 'Neutral Shelf',
            'usage': 'internal',
            'location_id': cls.stock_location.id,
            'barcode': 'NEUTRAL-SHELF',
            'company_id': cls.company.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Neutral Storable',
            'type': 'consu',
            'is_storable': True,
        })

    def _shelf_values(self, **values):
        return {
            'name': 'Another Shelf',
            'usage': 'internal',
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
            **values,
        }

    def test_barcode_unique_empty_barcodes_accepted(self):
        first, second = self.Location.create([
            self._shelf_values(barcode=False),
            self._shelf_values(barcode=False),
        ])
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual((first + second).exists(), first + second)
        self.assertFalse(first.barcode)
        self.assertFalse(second.barcode)

    def test_barcode_unique_distinct_barcodes_accepted(self):
        other = self.Location.create(self._shelf_values(barcode='NEUTRAL-OTHER'))
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(
            self.Location.search([('barcode', 'in', ['NEUTRAL-SHELF', 'NEUTRAL-OTHER'])]),
            self.location + other,
        )

    def test_barcode_unique_same_barcode_in_company_refused(self):
        with self.assertIntegrityError():
            self.Location.create(self._shelf_values(barcode='NEUTRAL-SHELF'))
        self.env.invalidate_all()
        self.assertEqual(self.Location.search([('barcode', '=', 'NEUTRAL-SHELF')]), self.location)

    def test_inventory_frequency_check_non_negative_accepted(self):
        self.location.cyclic_inventory_frequency = 0
        self.env.flush_all()
        self.location.cyclic_inventory_frequency = 30
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(self.location.cyclic_inventory_frequency, 30)

    def test_inventory_frequency_check_negative_refused(self):
        with self.assertIntegrityError():
            self.location.cyclic_inventory_frequency = -1
        self.env.invalidate_all()
        self.assertEqual(self.location.cyclic_inventory_frequency, 0)
        with self.assertIntegrityError():
            self.Location.create(self._shelf_values(cyclic_inventory_frequency=-7))
        self.env.invalidate_all()
        self.assertFalse(self.Location.search([('name', '=', 'Another Shelf')]))

    def test_quant_restrict_product_without_quant_unlinked(self):
        product = self.env['product.product'].create({'name': 'Unused Storable', 'type': 'consu', 'is_storable': True})
        product.unlink()
        self.env.invalidate_all()
        self.assertFalse(product.exists())

    def test_quant_restrict_product_with_quant_kept(self):
        quant = self.Quant.create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 5.0,
        })
        self.env.flush_all()
        with self.assertIntegrityError():
            self.product.unlink()
        self.env.invalidate_all()
        self.assertTrue(self.product.exists())
        self.assertEqual(quant.product_id, self.product)
        self.assertEqual(quant.quantity, 5.0)

    def test_quant_restrict_location_with_quant_kept(self):
        quant = self.Quant.create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 5.0,
        })
        self.env.flush_all()
        with self.assertIntegrityError():
            self.location.unlink()
        self.env.invalidate_all()
        self.assertTrue(self.location.exists())
        self.assertEqual(quant.location_id, self.location)

    def test_orderpoint_unique_distinct_locations_accepted(self):
        first, second = self.Orderpoint.create([
            {'product_id': self.product.id, 'location_id': self.stock_location.id, 'warehouse_id': self.warehouse.id},
            {'product_id': self.product.id, 'location_id': self.location.id, 'warehouse_id': self.warehouse.id},
        ])
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(self.Orderpoint.search([('product_id', '=', self.product.id)]), first + second)

    def test_orderpoint_unique_same_product_location_refused(self):
        orderpoint = self.Orderpoint.create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'warehouse_id': self.warehouse.id,
        })
        self.env.flush_all()
        with self.assertIntegrityError():
            self.Orderpoint.create({
                'product_id': self.product.id,
                'location_id': self.location.id,
                'warehouse_id': self.warehouse.id,
            })
        self.env.invalidate_all()
        self.assertEqual(self.Orderpoint.search([('product_id', '=', self.product.id)]), orderpoint)


class TestIntegritySaleOrderLine(NeutralCase):
    """ integrity.sale_order_line: CHECK constraints keyed on display_type,
    date_order required (not-null, and CHECK once confirmed), Many2one
    order_id ondelete='cascade', Many2one campaign_id ondelete='set null'. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Order = cls.env['sale.order']
        cls.Line = cls.env['sale.order.line']
        cls.customer = cls.env['res.partner'].create({'name': 'Neutral Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Neutral Service',
            'type': 'service',
            'list_price': 10.0,
        })
        cls.campaign = cls.env['utm.campaign'].create({'name': 'Neutral Campaign'})

    def _order(self, **values):
        return self.Order.create({'partner_id': self.customer.id, **values})

    def test_section_line_check_section_without_product_accepted(self):
        order = self._order()
        section = self.Line.create({'order_id': order.id, 'display_type': 'line_section', 'name': 'Section'})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertTrue(section.exists())
        self.assertFalse(section.product_id)
        self.assertEqual(section.product_uom_qty, 0.0)
        self.assertEqual(section.price_unit, 0.0)

    def test_section_line_check_section_with_product_refused(self):
        order = self._order()
        with self.assertIntegrityError():
            self.Line.create({
                'order_id': order.id,
                'display_type': 'line_section',
                'name': 'Section',
                'product_id': self.product.id,
            })
        self.env.invalidate_all()
        self.assertFalse(order.order_line)

    def test_section_line_check_note_with_price_refused(self):
        order = self._order()
        with self.assertIntegrityError():
            self.Line.create({
                'order_id': order.id,
                'display_type': 'line_note',
                'name': 'Priced note',
                'price_unit': 5.0,
            })
        self.env.invalidate_all()
        self.assertFalse(order.order_line)

    def test_accountable_line_check_product_line_accepted(self):
        order = self._order()
        line = self.Line.create({'order_id': order.id, 'product_id': self.product.id, 'product_uom_qty': 2.0})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(line.product_uom_id, self.product.uom_id)
        self.assertEqual(order.order_line, line)

    def test_accountable_line_check_product_line_without_unit_refused(self):
        order = self._order()
        # is_downpayment must be stored as an actual False: the rule is
        # "display_type set OR is_downpayment OR unit set", and an unset
        # (unknown) is_downpayment lets a unit-less line through
        line = self.Line.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 2.0,
            'is_downpayment': False,
        })
        self.env.flush_all()
        with self.assertIntegrityError():
            line.product_uom_id = False
        self.env.invalidate_all()
        self.assertEqual(line.product_uom_id, self.product.uom_id)

    def test_date_order_required_confirmed_order_has_date(self):
        order = self._order()
        self.Line.create({'order_id': order.id, 'product_id': self.product.id, 'product_uom_qty': 1.0})
        order.action_confirm()
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.date_order)

    def test_date_order_required_confirmed_order_without_date_refused(self):
        order = self._order()
        self.Line.create({'order_id': order.id, 'product_id': self.product.id, 'product_uom_qty': 1.0})
        order.action_confirm()
        self.env.flush_all()
        date_order = order.date_order
        with self.assertIntegrityError():
            order.date_order = False
        self.env.invalidate_all()
        self.assertEqual(order.date_order, date_order)

    def test_cascade_lines_follow_their_order(self):
        order, other = self._order(), self._order()
        lines = self.Line.create([
            {'order_id': order.id, 'product_id': self.product.id, 'product_uom_qty': 1.0},
            {'order_id': order.id, 'display_type': 'line_note', 'name': 'Note'},
        ])
        other_line = self.Line.create({'order_id': other.id, 'product_id': self.product.id})
        self.env.flush_all()
        line_ids = lines.ids

        order.unlink()
        self.env.invalidate_all()
        self.assertFalse(order.exists())
        self.assertFalse(self.Line.browse(line_ids).exists())
        self.assertFalse(self.Line.search([('order_id', '=', order.id)]))
        self.assertEqual(other.order_line, other_line)

    def test_set_null_campaign_kept_while_it_exists(self):
        order = self._order(campaign_id=self.campaign.id)
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(order.campaign_id, self.campaign)
        self.assertEqual(self.Order.search([('campaign_id', '=', self.campaign.id)]), order)

    def test_set_null_order_survives_campaign_unlink(self):
        campaign = self.env['utm.campaign'].create({'name': 'Short-lived Campaign'})
        order = self._order(campaign_id=campaign.id)
        other = self._order(campaign_id=self.campaign.id)
        self.env.flush_all()

        campaign.unlink()
        self.env.invalidate_all()
        self.assertFalse(campaign.exists())
        self.assertTrue(order.exists())
        self.assertFalse(order.campaign_id)
        self.assertEqual(order.partner_id, self.customer)
        self.assertEqual(other.campaign_id, self.campaign)
