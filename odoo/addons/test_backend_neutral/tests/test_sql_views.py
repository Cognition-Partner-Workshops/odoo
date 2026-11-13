"""Parity tests for sampled SQL-view reporting models.

Every report below is a computed, read-only model. These tests build a small
fixture through the ORM, compute the expected report content in Python from
that fixture, and compare it with what the report model returns through
``search``/``read``/``_read_group``. Another backend must produce the same rows
and totals, however it computes them.
"""
from datetime import date, timedelta

from odoo import Command, fields
from odoo.addons.test_backend_neutral.harness import NeutralCase


def _next_weekday(start, weekday):
    days_ahead = (weekday - start.weekday()) % 7
    return start + timedelta(days=days_ahead)


class TestAccountInvoiceReport(NeutralCase):
    """``account.invoice.report``: one row per product line, signed amounts in
    company currency, weighted average price as grouped aggregate."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        if not cls.company.chart_template:
            cls.env['account.chart.template'].try_loading(
                'generic_coa', company=cls.company, install_demo=False)
        cls.company_currency = cls.company.currency_id
        cls.other_currency = cls.env['res.currency'].search(
            [('id', '!=', cls.company_currency.id), ('active', 'in', [True, False])], limit=1)
        cls.other_currency.active = True
        cls.other_currency.rate_ids.filtered(lambda r: r.company_id == cls.company).unlink()
        cls.env['res.currency.rate'].create({
            'currency_id': cls.other_currency.id,
            'company_id': cls.company.id,
            'name': '2000-01-01',
            'rate': 2.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Neutral Report Partner'})
        cls.product_a = cls.env['product.product'].create({'name': 'Neutral Report A', 'list_price': 100.0})
        cls.product_b = cls.env['product.product'].create({'name': 'Neutral Report B', 'list_price': 50.0})
        cls.invoice_date = date(2024, 3, 15)

        cls.invoice = cls._create_move('out_invoice', cls.company_currency, [
            (cls.product_a, 2.0, 100.0),
            (cls.product_b, 1.0, 50.0),
        ])
        cls.foreign_invoice = cls._create_move('out_invoice', cls.other_currency, [
            (cls.product_a, 1.0, 200.0),
        ])
        cls.bill = cls._create_move('in_invoice', cls.company_currency, [
            (cls.product_b, 3.0, 30.0),
        ])
        cls.moves = cls.invoice + cls.foreign_invoice + cls.bill
        cls.moves.action_post()

    @classmethod
    def _create_move(cls, move_type, currency, lines):
        return cls.env['account.move'].create({
            'move_type': move_type,
            'partner_id': cls.partner.id,
            'currency_id': currency.id,
            'invoice_date': cls.invoice_date,
            'invoice_line_ids': [
                Command.create({
                    'product_id': product.id,
                    'quantity': quantity,
                    'price_unit': price_unit,
                    'tax_ids': [Command.clear()],
                })
                for product, quantity, price_unit in lines
            ],
        })

    def _report_rows(self, moves):
        return self.env['account.invoice.report'].search(
            [('move_id', 'in', moves.ids)], order='move_id, product_id, quantity')

    @staticmethod
    def _sign(move):
        return -1 if move.move_type in ('in_invoice', 'out_refund') else 1

    def test_one_row_per_product_line(self):
        for move in self.moves:
            lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
            rows = self._report_rows(move)
            self.assertEqual(len(rows), len(lines))
            self.assertEqual(set(rows.mapped('product_id').ids), set(lines.product_id.ids))
            sign = self._sign(move)
            for row in rows:
                line = lines.filtered(lambda l: l.product_id == row.product_id)
                self.assertEqual(row.move_type, move.move_type)
                self.assertEqual(row.state, 'posted')
                self.assertEqual(row.partner_id, self.partner)
                self.assertEqual(row.product_id, line.product_id)
                self.assertEqual(row.invoice_date, self.invoice_date)
                self.assertEqual(row.currency_id, move.currency_id)
                self.assertEqual(row.company_currency_id, self.company_currency)
                self.assertAlmostEqual(row.quantity, sign * line.quantity)
                self.assertAlmostEqual(row.price_subtotal_currency, sign * line.price_subtotal)
                self.assertAlmostEqual(row.price_subtotal, -line.balance)
                self.assertAlmostEqual(row.price_total, -line.balance)

    def test_section_and_note_lines_are_not_rows(self):
        self.invoice.button_draft()
        self.invoice.write({'invoice_line_ids': [
            Command.create({'display_type': 'line_section', 'name': 'Section'}),
            Command.create({'display_type': 'line_note', 'name': 'Note'}),
        ]})
        self.invoice.action_post()
        self.env.flush_all()
        self.assertEqual(len(self._report_rows(self.invoice)), 2)

    def test_foreign_currency_amounts_are_converted(self):
        row = self._report_rows(self.foreign_invoice)
        line = self.foreign_invoice.invoice_line_ids
        self.assertEqual(len(row), 1)
        self.assertEqual(row.currency_id, self.other_currency)
        self.assertAlmostEqual(row.price_subtotal_currency, 200.0)
        self.assertAlmostEqual(line.price_subtotal, 200.0)
        self.assertAlmostEqual(row.price_subtotal, -line.balance)
        self.assertAlmostEqual(row.price_subtotal, 100.0)

    def test_grouped_totals_by_move_type(self):
        expected = {}
        for move in self.moves:
            sign = self._sign(move)
            bucket = expected.setdefault(move.move_type, {'qty': 0.0, 'subtotal': 0.0, 'count': 0})
            for line in move.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                bucket['qty'] += sign * line.quantity
                bucket['subtotal'] += -line.balance
                bucket['count'] += 1

        groups = self.env['account.invoice.report']._read_group(
            [('move_id', 'in', self.moves.ids)],
            groupby=['move_type'],
            aggregates=['quantity:sum', 'price_subtotal:sum', 'price_average:avg_currency', '__count'],
        )
        self.assertEqual({g[0] for g in groups}, set(expected))
        for move_type, qty, subtotal, average, count in groups:
            exp = expected[move_type]
            self.assertAlmostEqual(qty, exp['qty'])
            self.assertAlmostEqual(subtotal, exp['subtotal'])
            self.assertAlmostEqual(average, exp['subtotal'] / exp['qty'])
            self.assertEqual(count, exp['count'])

    def test_grouped_total_by_invoice_month(self):
        groups = self.env['account.invoice.report']._read_group(
            [('move_id', 'in', self.moves.ids)],
            groupby=['invoice_date:month'],
            aggregates=['price_subtotal:sum'],
        )
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0][0], date(2024, 3, 1))
        expected = sum(-line.balance for line in self.moves.invoice_line_ids
                       if line.display_type == 'product')
        self.assertAlmostEqual(groups[0][1], expected)

    def test_unposted_and_cancelled_moves_keep_their_state(self):
        draft = self._create_move('out_invoice', self.company_currency, [(self.product_a, 1.0, 10.0)])
        self.env.flush_all()
        self.assertEqual(self._report_rows(draft).mapped('state'), ['draft'])
        self.invoice.button_draft()
        self.invoice.button_cancel()
        self.env.flush_all()
        self.assertEqual(self.invoice.state, 'cancel')
        self.assertEqual(set(self._report_rows(self.invoice).mapped('state')), {'cancel'})
        self.assertEqual(
            self.env['account.invoice.report'].search_count(
                [('move_id', 'in', self.moves.ids), ('state', '=', 'posted')]),
            len(self._report_rows(self.foreign_invoice + self.bill)))


class TestSaleReport(NeutralCase):
    """``sale.report``: one row per order line, amounts in company currency."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company_currency = cls.company.currency_id
        cls.other_currency = cls.env['res.currency'].search(
            [('id', '!=', cls.company_currency.id), ('active', 'in', [True, False])], limit=1)
        cls.other_currency.active = True
        cls.other_currency.rate_ids.filtered(lambda r: r.company_id == cls.company).unlink()
        cls.env['res.currency.rate'].create({
            'currency_id': cls.other_currency.id,
            'company_id': cls.company.id,
            'name': '2000-01-01',
            'rate': 4.0,
        })
        cls.foreign_pricelist = cls.env['product.pricelist'].create({
            'name': 'Neutral Foreign Pricelist',
            'currency_id': cls.other_currency.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Neutral Sale Partner'})
        cls.product_a = cls.env['product.product'].create({
            'name': 'Neutral Sale A', 'list_price': 100.0, 'type': 'consu'})
        cls.product_b = cls.env['product.product'].create({
            'name': 'Neutral Sale B', 'list_price': 40.0, 'type': 'consu'})
        cls.date_order = fields.Datetime.to_datetime('2024-05-10 10:00:00')

        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'date_order': cls.date_order,
            'order_line': [
                Command.create({'product_id': cls.product_a.id, 'product_uom_qty': 3.0,
                                'price_unit': 100.0, 'tax_ids': [Command.clear()]}),
                Command.create({'product_id': cls.product_b.id, 'product_uom_qty': 2.0,
                                'price_unit': 40.0, 'tax_ids': [Command.clear()]}),
                Command.create({'display_type': 'line_section', 'name': 'Section'}),
                Command.create({'display_type': 'line_note', 'name': 'Note'}),
            ],
        })
        cls.foreign_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'date_order': cls.date_order,
            'pricelist_id': cls.foreign_pricelist.id,
            'order_line': [
                Command.create({'product_id': cls.product_a.id, 'product_uom_qty': 1.0,
                                'price_unit': 400.0, 'tax_ids': [Command.clear()]}),
            ],
        })
        cls.orders = cls.order + cls.foreign_order
        cls.orders.action_confirm()

    def _report_rows(self, orders):
        return self.env['sale.report'].search(
            [('order_reference', 'in', [f'sale.order,{order.id}' for order in orders])],
            order='order_reference, product_id, product_uom_qty')

    def test_one_row_per_product_line(self):
        for order in self.orders:
            lines = order.order_line.filtered(lambda l: not l.display_type)
            rows = self._report_rows(order)
            self.assertEqual(len(rows), len(lines))
            self.assertEqual(set(rows.mapped('product_id').ids), set(lines.product_id.ids))
            for row in rows:
                line = lines.filtered(lambda l: l.product_id == row.product_id)
                self.assertEqual(row.name, order.name)
                self.assertEqual(row.state, 'sale')
                self.assertEqual(row.partner_id, self.partner)
                self.assertEqual(row.company_id, self.company)
                self.assertEqual(row.currency_id, self.company_currency)
                self.assertEqual(row.date, order.date_order)
                self.assertEqual(row.nbr, 1)
                self.assertAlmostEqual(row.product_uom_qty, line.product_uom_qty)
                self.assertAlmostEqual(row.qty_to_deliver, line.product_uom_qty)
                self.assertAlmostEqual(row.qty_invoiced, 0.0)
                self.assertAlmostEqual(row.qty_to_invoice, line.qty_to_invoice)
                self.assertAlmostEqual(
                    row.price_subtotal, line.price_subtotal / order.currency_rate, places=2)
                self.assertAlmostEqual(
                    row.price_total, line.price_total / order.currency_rate, places=2)

    def test_foreign_currency_order_is_reported_in_company_currency(self):
        row = self._report_rows(self.foreign_order)
        line = self.foreign_order.order_line
        self.assertEqual(self.foreign_order.currency_id, self.other_currency)
        self.assertAlmostEqual(self.foreign_order.currency_rate, 4.0)
        self.assertAlmostEqual(line.price_subtotal, 400.0)
        self.assertEqual(row.currency_id, self.company_currency)
        self.assertAlmostEqual(row.price_subtotal, 100.0, places=2)
        self.assertAlmostEqual(row.untaxed_amount_to_invoice, 100.0, places=2)

    def test_grouped_totals_by_order(self):
        expected = {
            order.name: {
                'qty': sum(order.order_line.mapped('product_uom_qty')),
                'subtotal': order.amount_untaxed / order.currency_rate,
                'nbr': len(order.order_line.filtered(lambda l: not l.display_type)),
            }
            for order in self.orders
        }
        groups = self.env['sale.report']._read_group(
            [('order_reference', 'in', [f'sale.order,{o.id}' for o in self.orders])],
            groupby=['name'],
            aggregates=['product_uom_qty:sum', 'price_subtotal:sum', 'nbr:sum', '__count'],
        )
        self.assertEqual({g[0] for g in groups}, set(expected))
        for name, qty, subtotal, nbr, count in groups:
            self.assertAlmostEqual(qty, expected[name]['qty'])
            self.assertAlmostEqual(subtotal, expected[name]['subtotal'], places=2)
            self.assertEqual(nbr, expected[name]['nbr'])
            self.assertEqual(count, expected[name]['nbr'])

    def test_grouped_totals_by_product(self):
        lines = self.orders.order_line.filtered(lambda l: not l.display_type)
        expected = {}
        for line in lines:
            expected[line.product_id] = expected.get(line.product_id, 0.0) + line.product_uom_qty
        groups = self.env['sale.report']._read_group(
            [('order_reference', 'in', [f'sale.order,{o.id}' for o in self.orders])],
            groupby=['product_id'],
            aggregates=['product_uom_qty:sum'],
        )
        self.assertEqual(dict(groups), expected)

    def test_cancelled_order_rows_follow_state(self):
        self.order._action_cancel()
        self.env.flush_all()
        self.assertEqual(set(self._report_rows(self.order).mapped('state')), {'cancel'})
        self.assertEqual(
            self.env['sale.report'].search_count(
                [('order_reference', '=', f'sale.order,{self.order.id}'), ('state', '=', 'sale')]),
            0)


class TestStockQuantityReport(NeutralCase):
    """``report.stock.quantity``: on-hand quantity today, forecast per day
    following confirmed moves, split per warehouse and company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Neutral Stock Co 2'})
        cls.env.user.write({'company_ids': [Command.link(cls.other_company.id)]})
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Neutral WH', 'code': 'NWH', 'company_id': cls.company.id})
        cls.other_warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.other_company.id)], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Neutral Stock Product', 'is_storable': True})
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.today = fields.Date.today()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.in_two_days = cls.today + timedelta(days=2)

        Quant = cls.env['stock.quant']
        Quant._update_available_quantity(cls.product, cls.warehouse.lot_stock_id, 10.0)
        Quant.with_company(cls.other_company)._update_available_quantity(
            cls.product, cls.other_warehouse.lot_stock_id, 4.0)

        cls.outgoing = cls.env['stock.move'].create({
            'product_id': cls.product.id,
            'product_uom_qty': 3.0,
            'location_id': cls.warehouse.lot_stock_id.id,
            'location_dest_id': cls.customer_location.id,
            'date': fields.Datetime.to_datetime(cls.tomorrow) + timedelta(hours=12),
        })
        cls.outgoing._action_confirm()
        cls.env.flush_all()

    def _rows(self, extra_domain, warehouse=None):
        domain = [('product_id', '=', self.product.id)] + extra_domain
        if warehouse is not None:
            domain.append(('warehouse_id', '=', warehouse.id))
        return self.env['report.stock.quantity'].search(domain)

    def test_one_row_per_move_and_quant(self):
        out_rows = self._rows([('state', '=', 'out')], self.warehouse)
        self.assertEqual(len(out_rows), 1)
        self.assertEqual(out_rows.date, self.tomorrow)
        self.assertAlmostEqual(out_rows.product_qty, -3.0)
        self.assertEqual(out_rows.company_id, self.company)
        self.assertFalse(self._rows([('state', '=', 'in')], self.warehouse))
        self.assertFalse(self._rows([('state', 'in', ('in', 'out'))], self.other_warehouse))

    def test_forecast_follows_confirmed_moves_day_by_day(self):
        groups = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', self.product.id), ('state', '=', 'forecast'),
             ('warehouse_id', '=', self.warehouse.id),
             ('date', '>=', self.today), ('date', '<=', self.in_two_days)],
            groupby=['date:day'],
            aggregates=['product_qty:sum'],
        )
        self.assertEqual(
            {day: qty for day, qty in groups},
            {self.today: 10.0, self.tomorrow: 7.0, self.in_two_days: 7.0})

    def test_multi_company_rows_are_kept_apart(self):
        groups = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', self.product.id), ('state', '=', 'forecast'),
             ('date', '=', self.tomorrow)],
            groupby=['company_id', 'warehouse_id'],
            aggregates=['product_qty:sum'],
        )
        self.assertEqual(
            {(company, warehouse): qty for company, warehouse, qty in groups},
            {(self.company, self.warehouse): 7.0, (self.other_company, self.other_warehouse): 4.0})

    def test_grouped_total_across_warehouses(self):
        groups = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', self.product.id), ('state', '=', 'forecast'),
             ('date', 'in', [self.today, self.tomorrow])],
            groupby=['date:day'],
            aggregates=['product_qty:sum'],
        )
        self.assertEqual({day: qty for day, qty in groups},
                         {self.today: 14.0, self.tomorrow: 11.0})

    def test_done_move_leaves_forecast(self):
        self.outgoing.quantity = 3.0
        self.outgoing.picked = True
        self.outgoing._action_done()
        self.env.flush_all()
        self.assertFalse(self._rows([('state', '=', 'out')], self.warehouse))
        groups = self.env['report.stock.quantity']._read_group(
            [('product_id', '=', self.product.id), ('state', '=', 'forecast'),
             ('warehouse_id', '=', self.warehouse.id), ('date', '=', self.today)],
            aggregates=['product_qty:sum'],
        )
        self.assertAlmostEqual(groups[0][0], 7.0)


class TestHrLeaveReport(NeutralCase):
    """``hr.leave.report``: allocations count positive, requests negative,
    per employee and per company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Neutral Leave Co 2'})
        cls.env.user.write({'company_ids': [Command.link(cls.other_company.id)]})
        cls.leave_type = cls.env['hr.work.entry.type'].create({
            'name': 'Neutral Paid Time Off',
            'code': 'NPTO',
            'requires_allocation': True,
            'leave_validation_type': 'no_validation',
            'allocation_validation_type': 'no_validation',
            'request_unit': 'day',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Neutral Employee', 'company_id': cls.company.id})
        cls.colleague = cls.env['hr.employee'].create({
            'name': 'Neutral Colleague', 'company_id': cls.company.id})
        cls.other_employee = cls.env['hr.employee'].with_company(cls.other_company).create({
            'name': 'Neutral Other Employee', 'company_id': cls.other_company.id})

        cls.allocations = cls.env['hr.leave.allocation'].create([
            cls._allocation_vals(cls.employee, 10.0),
            cls._allocation_vals(cls.colleague, 5.0),
            cls._allocation_vals(cls.other_employee, 8.0),
        ])
        cls.allocations.filtered(lambda a: a.state != 'validate').action_approve()

        monday = _next_weekday(date(2025, 3, 3), 0)
        cls.leave = cls.env['hr.leave'].create({
            'name': 'Neutral leave',
            'employee_id': cls.employee.id,
            'work_entry_type_id': cls.leave_type.id,
            'request_date_from': monday,
            'request_date_to': monday + timedelta(days=1),
        })
        cls.other_leave = cls.env['hr.leave'].with_company(cls.other_company).create({
            'name': 'Neutral other leave',
            'employee_id': cls.other_employee.id,
            'work_entry_type_id': cls.leave_type.id,
            'request_date_from': monday + timedelta(days=7),
            'request_date_to': monday + timedelta(days=7),
        })
        cls.leaves = cls.leave + cls.other_leave
        cls.env.flush_all()

    @classmethod
    def _allocation_vals(cls, employee, days):
        return {
            'name': f'Allocation {employee.name}',
            'employee_id': employee.id,
            'work_entry_type_id': cls.leave_type.id,
            'number_of_days': days,
            'date_from': date(2025, 1, 1),
        }

    def _rows(self, employees):
        return self.env['hr.leave.report'].search(
            [('employee_id', 'in', employees.ids), ('work_entry_type_id', '=', self.leave_type.id)],
            order='employee_id, leave_type, number_of_days')

    def test_one_row_per_allocation_and_request(self):
        employees = self.employee + self.colleague + self.other_employee
        rows = self._rows(employees)
        self.assertEqual(len(rows), len(self.allocations) + len(self.leaves))
        for allocation in self.allocations:
            row = rows.filtered(lambda r: r.leave_type == 'allocation' and r.employee_id == allocation.employee_id)
            self.assertEqual(len(row), 1)
            self.assertEqual(row.name, allocation.name)
            self.assertAlmostEqual(row.number_of_days, allocation.number_of_days)
            self.assertEqual(row.state, 'validate')
            self.assertEqual(row.company_id, allocation.employee_id.company_id)
            self.assertEqual(row.date_from.date(), date(2025, 1, 1))
        for leave in self.leaves:
            row = rows.filtered(lambda r: r.leave_type == 'request' and r.employee_id == leave.employee_id)
            self.assertEqual(len(row), 1)
            self.assertEqual(row.name, leave.name)
            self.assertAlmostEqual(row.number_of_days, -leave.number_of_days)
            self.assertEqual(row.state, leave.state)
            self.assertEqual(row.date_from, leave.date_from)
            self.assertEqual(row.date_to, leave.date_to)
            self.assertEqual(row.company_id, leave.employee_id.company_id)
        self.assertAlmostEqual(self.leave.number_of_days, 2.0)
        self.assertAlmostEqual(self.other_leave.number_of_days, 1.0)

    def test_grouped_balance_per_employee(self):
        employees = self.employee + self.colleague + self.other_employee
        expected = {}
        for allocation in self.allocations:
            expected[allocation.employee_id] = expected.get(allocation.employee_id, 0.0) + allocation.number_of_days
        for leave in self.leaves:
            expected[leave.employee_id] = expected.get(leave.employee_id, 0.0) - leave.number_of_days
        groups = self.env['hr.leave.report']._read_group(
            [('employee_id', 'in', employees.ids), ('work_entry_type_id', '=', self.leave_type.id)],
            groupby=['employee_id'],
            aggregates=['number_of_days:sum'],
        )
        self.assertEqual({emp: round(days, 6) for emp, days in groups},
                         {emp: round(days, 6) for emp, days in expected.items()})

    def test_grouped_balance_per_company(self):
        employees = self.employee + self.colleague + self.other_employee
        groups = self.env['hr.leave.report']._read_group(
            [('employee_id', 'in', employees.ids), ('work_entry_type_id', '=', self.leave_type.id)],
            groupby=['company_id', 'leave_type'],
            aggregates=['number_of_days:sum', '__count'],
        )
        self.assertEqual(
            {(company, kind): (round(days, 6), count) for company, kind, days, count in groups},
            {
                (self.company, 'allocation'): (15.0, 2),
                (self.company, 'request'): (-2.0, 1),
                (self.other_company, 'allocation'): (8.0, 1),
                (self.other_company, 'request'): (-1.0, 1),
            })

    def test_refused_request_keeps_row_with_refused_state(self):
        self.leave.action_refuse()
        self.env.flush_all()
        row = self._rows(self.employee).filtered(lambda r: r.leave_type == 'request')
        self.assertEqual(row.state, 'refuse')
        groups = self.env['hr.leave.report']._read_group(
            [('employee_id', '=', self.employee.id), ('state', '=', 'validate')],
            aggregates=['number_of_days:sum'],
        )
        self.assertAlmostEqual(groups[0][0], 10.0)


class TestProjectTaskReport(NeutralCase):
    """``report.project.task.user``: one row per task with rating and state
    aggregates, per project and per company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Neutral Project Co 2'})
        cls.env.user.write({'company_ids': [Command.link(cls.other_company.id)]})
        cls.partner = cls.env['res.partner'].create({'name': 'Neutral Project Partner'})
        cls.stage_new, cls.stage_done = cls.env['project.task.type'].create([
            {'name': 'Neutral New', 'sequence': 1},
            {'name': 'Neutral Done', 'sequence': 2, 'fold': True},
        ])
        cls.project = cls.env['project.project'].create({
            'name': 'Neutral Project',
            'company_id': cls.company.id,
            'partner_id': cls.partner.id,
            'type_ids': [Command.set((cls.stage_new + cls.stage_done).ids)],
        })
        cls.other_project = cls.env['project.project'].with_company(cls.other_company).create({
            'name': 'Neutral Other Project',
            'company_id': cls.other_company.id,
            'type_ids': [Command.set((cls.stage_new + cls.stage_done).ids)],
        })
        cls.task_a, cls.task_b, cls.task_c = cls.env['project.task'].create([
            {'name': 'Neutral Task A', 'project_id': cls.project.id, 'stage_id': cls.stage_new.id,
             'partner_id': cls.partner.id, 'priority': '1'},
            {'name': 'Neutral Task B', 'project_id': cls.project.id, 'stage_id': cls.stage_done.id,
             'partner_id': cls.partner.id, 'state': '1_done'},
            {'name': 'Neutral Task C', 'project_id': cls.project.id, 'stage_id': cls.stage_new.id,
             'partner_id': cls.partner.id, 'state': '1_canceled'},
        ])
        cls.other_task = cls.env['project.task'].with_company(cls.other_company).create({
            'name': 'Neutral Other Task', 'project_id': cls.other_project.id,
            'stage_id': cls.stage_new.id,
        })
        cls.tasks = cls.task_a + cls.task_b + cls.task_c + cls.other_task
        rating_vals = {
            'res_model_id': cls.env['ir.model']._get('project.task').id,
            'rated_partner_id': cls.partner.id,
            'partner_id': cls.partner.id,
            'consumed': True,
        }
        cls.env['rating.rating'].create([
            {**rating_vals, 'rating': 5, 'res_id': cls.task_a.id},
            {**rating_vals, 'rating': 4, 'res_id': cls.task_a.id},
            {**rating_vals, 'rating': 3, 'res_id': cls.task_b.id},
        ])
        cls.env['project.task'].invalidate_model(['rating_avg', 'rating_last_value'])
        cls.env.flush_all()

    def _rows(self, tasks):
        return self.env['report.project.task.user'].search([('task_id', 'in', tasks.ids)])

    def test_one_row_per_task(self):
        rows = self._rows(self.tasks)
        self.assertEqual(len(rows), len(self.tasks))
        self.assertEqual(set(rows.mapped('task_id').ids), set(self.tasks.ids))
        for row in rows:
            task = row.task_id
            self.assertEqual(row.name, task.name)
            self.assertEqual(row.project_id, task.project_id)
            self.assertEqual(row.stage_id, task.stage_id)
            self.assertEqual(row.state, task.state)
            self.assertEqual(row.is_closed, task.is_closed)
            self.assertEqual(row.priority, task.priority)
            self.assertEqual(row.partner_id, task.partner_id)
            self.assertEqual(row.company_id, task.project_id.company_id)
            self.assertEqual(row.nbr, 1)
            self.assertAlmostEqual(row.rating_avg, task.rating_avg)
            self.assertAlmostEqual(row.rating_last_value, task.rating_last_value)

    def test_rating_rows_match_python_average(self):
        rows = self._rows(self.task_a + self.task_b + self.task_c)
        by_task = {row.task_id: row for row in rows}
        self.assertAlmostEqual(by_task[self.task_a].rating_avg, 4.5)
        self.assertAlmostEqual(by_task[self.task_a].rating_last_value, 4.0)
        self.assertAlmostEqual(by_task[self.task_b].rating_avg, 3.0)
        self.assertAlmostEqual(by_task[self.task_c].rating_avg, 0.0)
        self.assertAlmostEqual(by_task[self.task_c].rating_last_value, 0.0)

    def test_multi_company_rows(self):
        groups = self.env['report.project.task.user']._read_group(
            [('task_id', 'in', self.tasks.ids)],
            groupby=['company_id'],
            aggregates=['nbr:sum'],
        )
        self.assertEqual(dict(groups), {self.company: 3, self.other_company: 1})

    def test_grouped_totals_by_project_and_state(self):
        expected = {}
        for task in self.tasks:
            expected[(task.project_id, task.state)] = expected.get((task.project_id, task.state), 0) + 1
        groups = self.env['report.project.task.user']._read_group(
            [('task_id', 'in', self.tasks.ids)],
            groupby=['project_id', 'state'],
            aggregates=['nbr:sum', '__count'],
        )
        self.assertEqual({(p, s): n for p, s, n, _count in groups}, expected)
        self.assertEqual({(p, s): c for p, s, _n, c in groups}, expected)

    def test_grouped_rating_average_by_project(self):
        groups = self.env['report.project.task.user']._read_group(
            [('task_id', 'in', (self.task_a + self.task_b).ids)],
            groupby=['project_id'],
            aggregates=['rating_avg:avg', 'rating_last_value:avg'],
        )
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0][0], self.project)
        self.assertAlmostEqual(groups[0][1], (4.5 + 3.0) / 2)
        self.assertAlmostEqual(groups[0][2], (4.0 + 3.0) / 2)

    def test_closed_tasks_grouped(self):
        groups = self.env['report.project.task.user']._read_group(
            [('task_id', 'in', self.tasks.ids)],
            groupby=['is_closed'],
            aggregates=['__count'],
        )
        expected = {}
        for task in self.tasks:
            expected[task.is_closed] = expected.get(task.is_closed, 0) + 1
        self.assertEqual(dict(groups), expected)


class TestProjectBurndownReport(NeutralCase):
    """``project.task.burndown.chart.report``: +1 for the stage a task enters
    and -1 for the stage it leaves, dated by the stage change; grouping must
    include a date part and the stage."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.todo, cls.doing, cls.done = cls.env['project.task.type'].create([
            {'name': 'Neutral BD Todo', 'sequence': 1},
            {'name': 'Neutral BD Doing', 'sequence': 2},
            {'name': 'Neutral BD Done', 'sequence': 3, 'fold': True},
        ])
        cls.stages = cls.todo + cls.doing + cls.done
        cls.project = cls.env['project.project'].create({
            'name': 'Neutral Burndown Project',
            'company_id': cls.env.company.id,
            'type_ids': [Command.set(cls.stages.ids)],
        })
        cls.tasks = cls.env['project.task'].create([
            {'name': f'Neutral BD {i}', 'project_id': cls.project.id,
             'stage_id': cls.todo.id, 'allocated_hours': 2.0}
            for i in range(4)
        ])
        cls.history = {task: [cls.todo] for task in cls.tasks}
        cls._move(cls.tasks[1] + cls.tasks[2] + cls.tasks[3], cls.doing)
        cls._move(cls.tasks[3], cls.done, state='1_done')
        cls.env.flush_all()

    @classmethod
    def _move(cls, tasks, stage, state=None):
        vals = {'stage_id': stage.id}
        if state:
            vals['state'] = state
        tasks.write(vals)
        cls.env.flush_all()
        for task in tasks:
            cls.history[task].append(stage)

    def _expected_net_by_stage(self, tasks):
        expected = {}
        for task in tasks:
            visited = self.history[task]
            for previous, entered in zip([None] + visited[:-1], visited):
                expected[entered] = expected.get(entered, 0) + 1
                if previous is not None:
                    expected[previous] = expected.get(previous, 0) - 1
        return expected

    def _grouped(self, domain, groupby):
        return self.env['project.task.burndown.chart.report']._read_group(
            domain, groupby=groupby, aggregates=['__count'])

    def test_grouped_count_by_month_and_stage(self):
        groups = self._grouped([('project_id', '=', self.project.id)], ['date:month', 'stage_id'])
        self.assertEqual({g[0].date().replace(day=1) for g in groups}, {fields.Date.today().replace(day=1)})
        self.assertEqual({stage: count for _month, stage, count in groups},
                         self._expected_net_by_stage(self.tasks))
        self.assertEqual(sum(count for *_rest, count in groups), len(self.tasks))

    def test_task_domain_filters_source_tasks(self):
        groups = self._grouped(
            [('project_id', '=', self.project.id), ('stage_id', 'in', self.stages.ids),
             ('state', '!=', '1_done')],
            ['date:day', 'stage_id'])
        open_tasks = self.tasks.filtered(lambda t: t.state != '1_done')
        self.assertEqual({g[0].date() for g in groups}, {fields.Date.today()})
        self.assertEqual({stage: count for _day, stage, count in groups},
                         self._expected_net_by_stage(open_tasks))

    def test_allocated_hours_follow_the_task(self):
        groups = self.env['project.task.burndown.chart.report']._read_group(
            [('project_id', '=', self.project.id)],
            groupby=['date:month', 'stage_id'],
            aggregates=['allocated_hours:sum'])
        expected = {stage: count * 2.0 for stage, count in self._expected_net_by_stage(self.tasks).items()}
        self.assertEqual({stage: hours for _month, stage, hours in groups}, expected)

    def test_grouping_requires_date_and_stage(self):
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            self._grouped([('project_id', '=', self.project.id)], ['stage_id'])
        with self.assertRaises(UserError):
            self._grouped([('project_id', '=', self.project.id)], ['date:month'])


class TestProjectTaskStageReport(NeutralCase):
    """``project.task.stage.report``: one row per stage a task has been in,
    with the time spent there taken from the task's ``duration_tracking``."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Neutral Stage Co 2'})
        cls.env.user.write({'company_ids': [Command.link(cls.other_company.id)]})
        cls.todo, cls.doing, cls.done = cls.env['project.task.type'].create([
            {'name': 'Neutral ST Todo', 'sequence': 1},
            {'name': 'Neutral ST Doing', 'sequence': 2},
            {'name': 'Neutral ST Done', 'sequence': 3, 'fold': True},
        ])
        stages = cls.todo + cls.doing + cls.done
        cls.project = cls.env['project.project'].create({
            'name': 'Neutral Stage Project', 'company_id': cls.company.id,
            'type_ids': [Command.set(stages.ids)],
        })
        cls.other_project = cls.env['project.project'].with_company(cls.other_company).create({
            'name': 'Neutral Stage Project 2', 'company_id': cls.other_company.id,
            'type_ids': [Command.set(stages.ids)],
        })
        cls.task_a, cls.task_b = cls.env['project.task'].create([
            {'name': 'Neutral ST A', 'project_id': cls.project.id, 'stage_id': cls.todo.id, 'priority': '1'},
            {'name': 'Neutral ST B', 'project_id': cls.project.id, 'stage_id': cls.todo.id},
        ])
        cls.other_task = cls.env['project.task'].with_company(cls.other_company).create({
            'name': 'Neutral ST C', 'project_id': cls.other_project.id, 'stage_id': cls.todo.id})
        cls.env.flush_all()
        (cls.task_a + cls.task_b).write({'stage_id': cls.doing.id})
        cls.env.flush_all()
        cls.task_a.write({'stage_id': cls.done.id, 'state': '1_done'})
        cls.tasks = cls.task_a + cls.task_b + cls.other_task
        cls.visited = {
            cls.task_a: cls.todo + cls.doing + cls.done,
            cls.task_b: cls.todo + cls.doing,
            cls.other_task: cls.todo,
        }
        cls.env.flush_all()

    def _rows(self, tasks):
        return self.env['project.task.stage.report'].search([('task_id', 'in', tasks.ids)])

    def test_one_row_per_task_and_visited_stage(self):
        rows = self._rows(self.tasks)
        self.assertEqual(
            {(row.task_id, row.stage_id) for row in rows},
            {(task, stage) for task, stages in self.visited.items() for stage in stages})
        for row in rows:
            task = row.task_id
            self.assertEqual(row.name, task.name)
            self.assertEqual(row.project_id, task.project_id)
            self.assertEqual(row.company_id, task.project_id.company_id)
            self.assertEqual(row.priority, task.priority)
            self.assertEqual(row.is_closed, task.state in ('1_done', '1_canceled'))
            self.assertEqual(row.sequence, row.stage_id.sequence)
            self.assertEqual(row.date_last_stage_update, task.date_last_stage_update)

    def test_time_spent_matches_duration_tracking(self):
        for row in self._rows(self.tasks):
            task = row.task_id
            tracked_minutes = task.duration_tracking.get(str(row.stage_id.id), 0)
            if row.stage_id == task.stage_id:
                self.assertGreaterEqual(row.time_spent, tracked_minutes / 60)
                self.assertLess(row.time_spent, tracked_minutes / 60 + 1.0)
            else:
                self.assertAlmostEqual(row.time_spent, tracked_minutes / 60)

    def test_grouped_counts_by_stage_and_company(self):
        groups = self.env['project.task.stage.report']._read_group(
            [('task_id', 'in', self.tasks.ids)],
            groupby=['company_id', 'stage_id'],
            aggregates=['__count'])
        expected = {}
        for task, stages in self.visited.items():
            for stage in stages:
                key = (task.project_id.company_id, stage)
                expected[key] = expected.get(key, 0) + 1
        self.assertEqual({(c, s): n for c, s, n in groups}, expected)

    def test_grouped_average_time_spent_by_stage(self):
        groups = self.env['project.task.stage.report']._read_group(
            [('task_id', 'in', self.tasks.ids), ('stage_id', '!=', self.todo.id)],
            groupby=['stage_id'],
            aggregates=['time_spent:avg'])
        rows = self._rows(self.tasks).filtered(lambda r: r.stage_id != self.todo)
        for stage, average in groups:
            stage_rows = rows.filtered(lambda r: r.stage_id == stage)
            self.assertAlmostEqual(average, sum(stage_rows.mapped('time_spent')) / len(stage_rows), places=4)


class TestHrLeaveEmployeeTypeReport(NeutralCase):
    """``hr.leave.employee.type.report``: FIFO remaining balance per allocation
    ('left'), validated requests ('taken') and pending ones ('planned')."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.auto_type, cls.manual_type = cls.env['hr.work.entry.type'].create([{
            'name': 'Neutral Auto Leave', 'code': 'NAL', 'requires_allocation': True,
            'leave_validation_type': 'no_validation', 'allocation_validation_type': 'no_validation',
            'request_unit': 'day',
        }, {
            'name': 'Neutral Manual Leave', 'code': 'NML', 'requires_allocation': True,
            'leave_validation_type': 'hr', 'allocation_validation_type': 'hr',
            'request_unit': 'day',
        }])
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Neutral Balance Employee', 'company_id': cls.company.id})
        cls.first_allocation, cls.second_allocation, cls.manual_allocation = cls.env['hr.leave.allocation'].create([
            cls._allocation_vals(cls.auto_type, 10.0, date(2025, 1, 1)),
            cls._allocation_vals(cls.auto_type, 5.0, date(2025, 2, 1)),
            cls._allocation_vals(cls.manual_type, 4.0, date(2025, 1, 1)),
        ])
        cls.allocations = cls.first_allocation + cls.second_allocation + cls.manual_allocation
        cls.allocations.filtered(lambda a: a.state != 'validate').action_approve()
        monday = _next_weekday(date(2025, 3, 3), 0)
        cls.taken_leave = cls.env['hr.leave'].create({
            'name': 'Neutral taken', 'employee_id': cls.employee.id,
            'work_entry_type_id': cls.auto_type.id,
            'request_date_from': monday, 'request_date_to': monday + timedelta(days=1),
        })
        cls.planned_leave = cls.env['hr.leave'].create({
            'name': 'Neutral planned', 'employee_id': cls.employee.id,
            'work_entry_type_id': cls.manual_type.id,
            'request_date_from': monday + timedelta(days=7), 'request_date_to': monday + timedelta(days=7),
        })
        if cls.planned_leave.state != 'confirm':
            cls.planned_leave.action_back_to_approval()
        cls.env.flush_all()

    @classmethod
    def _allocation_vals(cls, leave_type, days, date_from):
        return {
            'name': f'Allocation {leave_type.name} {days}',
            'employee_id': cls.employee.id,
            'work_entry_type_id': leave_type.id,
            'number_of_days': days,
            'date_from': date_from,
        }

    def _rows(self, domain=()):
        return self.env['hr.leave.employee.type.report'].search(
            [('employee_id', '=', self.employee.id)] + list(domain))

    def test_fixture_states(self):
        self.assertEqual(set(self.allocations.mapped('state')), {'validate'})
        self.assertEqual(self.taken_leave.state, 'validate')
        self.assertEqual(self.planned_leave.state, 'confirm')
        self.assertAlmostEqual(self.taken_leave.number_of_days, 2.0)
        self.assertAlmostEqual(self.planned_leave.number_of_days, 1.0)

    def test_one_left_row_per_allocation_with_fifo_balance(self):
        rows = self._rows([('holiday_status', '=', 'left')])
        self.assertEqual(len(rows), len(self.allocations))
        expected = {
            self.first_allocation: 10.0 - self.taken_leave.number_of_days,
            self.second_allocation: 5.0,
            self.manual_allocation: 4.0,
        }
        by_key = {(row.work_entry_type_id, row.date_from.date()): row for row in rows}
        for allocation, days_left in expected.items():
            row = by_key[(allocation.work_entry_type_id, allocation.date_from)]
            self.assertAlmostEqual(row.number_of_days, days_left)
            self.assertEqual(row.state, 'validate')
            self.assertEqual(row.company_id, self.company)
            self.assertTrue(row.active_employee)

    def test_one_row_per_request(self):
        taken = self._rows([('holiday_status', '=', 'taken')])
        planned = self._rows([('holiday_status', '=', 'planned')])
        self.assertEqual(len(taken), 1)
        self.assertEqual(len(planned), 1)
        self.assertAlmostEqual(taken.number_of_days, self.taken_leave.number_of_days)
        self.assertEqual(taken.state, 'validate')
        self.assertEqual(taken.work_entry_type_id, self.auto_type)
        self.assertEqual(taken.date_from, self.taken_leave.date_from)
        self.assertAlmostEqual(planned.number_of_days, self.planned_leave.number_of_days)
        self.assertEqual(planned.state, 'confirm')
        self.assertEqual(planned.work_entry_type_id, self.manual_type)

    def test_grouped_totals_by_status_and_type(self):
        groups = self.env['hr.leave.employee.type.report']._read_group(
            [('employee_id', '=', self.employee.id)],
            groupby=['work_entry_type_id', 'holiday_status'],
            aggregates=['number_of_days:sum', '__count'])
        self.assertEqual(
            {(t, s): (round(d, 6), n) for t, s, d, n in groups},
            {
                (self.auto_type, 'left'): (13.0, 2),
                (self.auto_type, 'taken'): (2.0, 1),
                (self.manual_type, 'left'): (4.0, 1),
                (self.manual_type, 'planned'): (1.0, 1),
            })

    def test_approving_planned_leave_moves_it_to_taken_and_reduces_left(self):
        self.planned_leave.action_approve()
        self.env.flush_all()
        self.assertEqual(self.planned_leave.state, 'validate')
        groups = self.env['hr.leave.employee.type.report']._read_group(
            [('employee_id', '=', self.employee.id), ('work_entry_type_id', '=', self.manual_type.id)],
            groupby=['holiday_status'],
            aggregates=['number_of_days:sum'])
        self.assertEqual({s: round(d, 6) for s, d in groups}, {'left': 3.0, 'taken': 1.0})
