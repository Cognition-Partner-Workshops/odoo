# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    picking_type_id = fields.Many2one('stock.warehouse', 'Warehouse', readonly=True)
    effective_date = fields.Datetime(string="Effective Date")
    days_to_arrival = fields.Float('Effective Days To Arrival', digits=(16, 2), readonly=True, aggregator='avg')

    def _picking_type_warehouse_sql(self, table):
        # stock_picking_type is MongoDB-stored: the order's warehouse is inlined per operation type instead of joined
        warehouse_by_picking_type = {t.id: t.warehouse_id.id or None for t in self.env['stock.picking.type'].sudo().with_context(active_test=False).search([])}
        if not warehouse_by_picking_type:
            return SQL("NULL::integer")
        return SQL("CASE %s %s ELSE NULL END", table.order_id.picking_type_id, SQL(" ").join(
            SQL("WHEN %s THEN %s", picking_type_id, warehouse_id) for picking_type_id, warehouse_id in warehouse_by_picking_type.items()
        ))

    def _select_list(self, table):
        # stock_location is MongoDB-stored: the non-supplier destinations are resolved through the ORM and inlined
        non_supplier_location_ids = tuple(self.env['stock.location'].sudo().with_context(active_test=False).search([('usage', '!=', 'supplier')]).ids) or (None,)
        table._query.add_join('LEFT JOIN', 'order_effective_date', SQL("""(
            SELECT MIN(picking.date_done) AS date_done,
                   purchase.id AS purchase_id
              FROM purchase_order AS purchase
              JOIN purchase_order_line AS order_line
                ON order_line.order_id = purchase.id
              JOIN stock_move AS move
                ON move.purchase_line_id = order_line.id
              JOIN stock_picking AS picking
                ON picking.id = move.picking_id
             WHERE picking.state = 'done'
               AND picking.location_dest_id IN %s
               AND picking.date_done IS NOT NULL
          GROUP BY purchase.id
        )""", non_supplier_location_ids), SQL("order_effective_date.purchase_id = %s", table.order_id))
        return super()._select_list(table) + [
            SQL("%s AS picking_type_id", self._picking_type_warehouse_sql(table)),
            table.order_id.effective_date,
            SQL(
                """EXTRACT(epoch FROM AGE(COALESCE(order_effective_date.date_done, %s), %s))/(24*60*60)::decimal(16,2) as days_to_arrival""",
                table.date_planned, table.order_id.date_order,
            ),
        ]

    def _groupby_list(self, table):
        return super()._groupby_list(table) + [
            self._picking_type_warehouse_sql(table),
            SQL("order_effective_date.date_done"),
        ]
