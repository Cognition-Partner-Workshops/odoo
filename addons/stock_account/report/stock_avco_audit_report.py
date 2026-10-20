from odoo import api, fields, models, tools
from odoo.fields import Domain
from odoo.tools import SQL, float_is_zero


class StockAverageCostReport(models.AbstractModel):
    _auto = False
    _uom_factor_view = True  # rebuilt by uom.uom._rebuild_factor_views()
    _name = 'stock.avco.report'
    _description = 'Stock AVCO Justifier'
    _order = 'date desc, id desc'

    date = fields.Date(string='Date', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')

    product_id = fields.Many2one('product.product', string='Product', required=True)

    reference = fields.Char(string='Reference', required=True)
    description = fields.Text(string='Description', required=True)

    res_model_name = fields.Selection([
        ('stock.move', 'Stock Move'),
        ('product.value', 'Product Value'),
    ], string='Resource Model Name', required=True)

    quantity = fields.Float(string='Added Quantity', required=True)
    value = fields.Float(string='Value', required=True)

    added_value = fields.Float(string='Added Value', compute='_compute_cumulative_fields')
    total_quantity = fields.Float(string='Total Quantity', compute='_compute_cumulative_fields')
    total_value = fields.Float(string='Total Value', compute='_compute_cumulative_fields')
    avco_value = fields.Float(string='AVCO Value', compute='_compute_cumulative_fields')

    justification = fields.Text(string='Justification', compute='_compute_justification')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_avco_report')
        query = SQL("""
CREATE OR REPLACE VIEW stock_avco_report AS (
SELECT
    sm.id AS id,
    sm.product_id,
    sm.date,
    picking.user_id,
    sm.company_id,
    sm.reference,
    CASE WHEN sm.is_in THEN sm.value ELSE -sm.value END AS value,
    CASE WHEN sm.is_in THEN sm.quantity * (um.factor / up.factor) ELSE -sm.quantity * (um.factor / up.factor) END AS quantity,
    'stock.move' AS res_model_name,
    'Operation' AS description
FROM
    stock_move sm
LEFT JOIN
    stock_picking picking ON sm.picking_id = picking.id
LEFT JOIN
    product_product pp ON sm.product_id = pp.id
LEFT JOIN
    product_template pt ON pp.product_tmpl_id = pt.id
LEFT JOIN
    %(uom_factors)s um(id, factor) ON um.id = sm.uom_id
LEFT JOIN
    %(uom_factors)s up(id, factor) ON up.id = pt.uom_id
WHERE
    sm.state = 'done'
    AND (sm.is_in = TRUE OR sm.is_out = TRUE)
UNION ALL
SELECT
    -pv.id,
    pv.product_id,
    pv.date,
    pv.user_id,
    pv.company_id,
    'Adjustment' AS reference, -- Set a fixed string for the reference
    pv.value,
    0 AS quantity, -- Set quantity to 0 as requested,
    'product.value' AS res_model_name,
    pv.description
FROM
    product_value pv
WHERE
    pv.move_id IS NULL
);
""", uom_factors=self.env['uom.uom']._factor_values_sql())  # uom_uom is stored in MongoDB: factors as of this (re)build
        self.env.cr.execute(query)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, *, active_test=True, bypass_access=False):
        # Ignore moves for standard cost method. Only display the list of cost updates.
        # The view did it in SQL (COALESCE(pc.property_cost_method ->> company, ir_default)) while
        # product_category was a PostgreSQL table; it is stored in MongoDB now, so the filter is
        # applied here through product.category's company-dependent field, per company.
        return super()._search(Domain(domain) & self._cost_method_domain(), offset, limit, order,
                               active_test=active_test, bypass_access=bypass_access)

    @api.model
    def _cost_method_domain(self):
        Category = self.env['product.category'].sudo()
        moves = Domain.FALSE
        for company in self.env['res.company'].sudo().search([]):
            categories = Category.with_company(company).search([('property_cost_method', 'in', ('fifo', 'average'))])
            moves |= Domain('company_id', '=', company.id) & Domain('product_id.product_tmpl_id.categ_id', 'in', categories.ids)
        return Domain('res_model_name', '=', 'product.value') | moves

    def _compute_cumulative_fields(self):
        total_records_grouped = self.env['stock.avco.report'].search(
            [('product_id', 'in', self.product_id.mapped('id')), ('company_id', 'in', self.company_id.mapped('id'))]
        ).grouped(lambda m: (m.product_id, m.company_id))
        for records in self.grouped(lambda m: (m.product_id, m.company_id)).values():
            current_page_records = records.sorted('date, id')
            total_records = total_records_grouped.get((records.product_id, records.company_id)).sorted('date, id')
            added_value = 0.0
            total_value = 0.0
            total_quantity = 0.0
            avco = 0.0
            for record in total_records:
                qty = record.quantity
                if record.res_model_name == 'stock.move':
                    previous_qty = total_quantity
                    total_quantity += qty
                    if qty > 0:
                        added_value = record.value
                        # Regular case, value from accumulation
                        if previous_qty > 0:
                            total_value += added_value
                            avco = total_value / total_quantity if not float_is_zero(total_quantity, precision_digits=self.env['decimal.precision'].precision_get('Product Unit')) else avco
                        # From negative quantity case, value from last_in
                        elif previous_qty <= 0:
                            avco = added_value / qty if qty else avco
                            total_value = avco * total_quantity
                    else:
                        added_value = avco * qty
                        total_value += added_value

                elif record.res_model_name == 'product.value':
                    avco = record.value
                    added_value = (avco * total_quantity) - total_value
                    total_value = avco * total_quantity

                if record in current_page_records:
                    record.added_value = added_value
                    record.total_value = total_value
                    record.total_quantity = total_quantity
                    record.avco_value = avco

    def _compute_justification(self):
        self.justification = False
        for record in self:
            if record.res_model_name == 'stock.move':
                record.justification = self.env['stock.move'].browse(record.id).value_justification
