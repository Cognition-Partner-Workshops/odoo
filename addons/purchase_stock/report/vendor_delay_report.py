# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools
from odoo.fields import Domain
from odoo.tools import SQL


class VendorDelayReport(models.Model):
    _name = 'vendor.delay.report'
    _description = "Vendor Delay Report"
    _auto = False
    _uom_factor_view = True  # rebuilt by uom.uom._rebuild_factor_views()
    _product_values_view = True  # rebuilt by product.product._rebuild_product_views()

    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    category_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    date = fields.Datetime('Effective Date', readonly=True)
    qty_total = fields.Float('Total Quantity', readonly=True)
    qty_on_time = fields.Float('On-Time Quantity', readonly=True)
    on_time_rate = fields.Float('On-Time Delivery Rate', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'vendor_delay_report')
        self.env.cr.execute(SQL("""
CREATE OR replace VIEW vendor_delay_report AS(
SELECT pol.id                   AS id,
       Min(m.date)              AS date,
       pol.id                   AS purchase_line_id,
       pol.product_id           AS product_id,
       Min(pt.categ_id)         AS category_id,
       pol.partner_id           AS partner_id,
       pol.product_uom_qty      AS qty_total,
       Sum(CASE
             WHEN (m.state = 'done' and pol.date_promised::date >= m.date::date) THEN ((ml.quantity * ml_uom.factor) / pt_uom.factor)
             ELSE 0
           END)                 AS qty_on_time,
       CASE
         WHEN pol.product_uom_qty != 0 THEN
           Sum(CASE
                 WHEN (m.state = 'done' and pol.date_promised::date >= m.date::date) THEN ((ml.quantity * ml_uom.factor) / pt_uom.factor)
                 ELSE 0
               END) / pol.product_uom_qty * 100
         ELSE 100
       END                      AS on_time_rate
FROM   stock_move m
       JOIN purchase_order_line pol
         ON pol.id = m.purchase_line_id
       JOIN %(products)s pt(id, product_tmpl_id, categ_id, uom_id, is_storable)
         ON pt.id = m.product_id
       JOIN %(uom_factors)s pt_uom(id, factor)
         ON pt_uom.id = pt.uom_id
       LEFT JOIN stock_move_line ml
         ON ml.move_id = m.id
       LEFT JOIN %(uom_factors)s ml_uom(id, factor)
         ON ml_uom.id = ml.uom_id
GROUP  BY pol.id
)""", uom_factors=self.env['uom.uom']._factor_values_sql(),  # uom_uom is stored in MongoDB: factors as of this (re)build
     products=self.env['product.product']._values_sql()))  # product tables too: columns as of this (re)build

    def _read_group_select(self, table, aggregate_spec):
        if aggregate_spec == 'on_time_rate:sum':
            # Make a weigthed average instead of simple average for these fields
            return SQL(
                'CASE WHEN SUM(%s) !=0 THEN SUM(%s) / SUM(%s) * 100 ELSE 100 END',
                table.qty_total, table.qty_on_time, table.qty_total,
            )
        return super()._read_group_select(table, aggregate_spec)

    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        if 'on_time_rate:sum' in aggregates:
            having = Domain.AND([having, [('qty_total:sum', '>', '0')]])
        return super()._read_group(domain, groupby, aggregates, having, offset, limit, order)
