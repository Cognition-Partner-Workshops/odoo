"""Seed deterministic Odoo business workflows for the UNT13 fixture source.

Modeled on the synthetic business-data approach in SummitDemoDB's MIT-licensed
generate_data.py: https://github.com/Riktastic/SummitDemoDB/blob/main/generate_data.py
"""

import datetime
import os
import random

from odoo.addons.base.models.avatar_mixin import get_random_ui_color_from_seed
from odoo.tools import BinaryBytes, html_escape


SEED = int(os.environ.get("POPULATE_SEED", "13013"))
FIXED_INSTANT = datetime.datetime(2026, 10, 20, 0, 0)
LOCK_DATE = datetime.date(2026, 10, 19)
LOCK_EXCEPTION_DATE = datetime.date(2026, 9, 30)
rng = random.Random(SEED)


def business_datetime():
    month = rng.randint(1, 9)
    day = rng.randint(1, 25)
    hour = rng.randint(8, 16)
    return datetime.datetime(2026, month, day, hour)


def business_date():
    return business_datetime().date()


def pin_dates(records, field_name):
    for record in records.sorted("id"):
        record[field_name] = business_datetime()


def validate_picking(picking):
    if picking.state == "draft":
        picking.action_confirm()
    picking.action_assign()
    for move in picking.move_ids.filtered(lambda item: item.state not in ("done", "cancel")):
        quantity = move.product_uom_qty
        if move.location_id.usage == "internal" and move.location_dest_id.usage != "internal":
            quantity = min(quantity, move.quantity)
        if quantity > 0:
            move.quantity = quantity
            move.picked = True
    action = picking.button_validate()
    if isinstance(action, dict):
        wizard_model = action.get("res_model")
        if wizard_model == "stock.backorder.confirmation":
            wizard = env[wizard_model].with_context(
                button_validate_picking_ids=picking.ids
            ).create({"pick_ids": [(6, 0, picking.ids)]})
            wizard.process_cancel_backorder()
        elif wizard_model == "stock.immediate.transfer":
            wizard = env[wizard_model].create({"pick_ids": [(6, 0, picking.ids)]})
            wizard.process()
    return picking


def post_invoices(moves, rounding=None):
    moves = moves.sorted("id")
    for index, move in enumerate(moves):
        stamp = business_date()
        move.write({"date": stamp, "invoice_date": stamp})
        if rounding and index == 0 and move.move_type == "out_invoice":
            move.invoice_cash_rounding_id = rounding
            move._recompute_cash_rounding_lines()
        move.action_post()
    return moves


def register_payment(move, amount=None):
    context = {
        "active_model": "account.move",
        "active_ids": move.ids,
    }
    values = {"payment_date": business_date(), "group_payment": False}
    if amount is not None:
        values.update({"amount": amount, "payment_difference_handling": "open"})
    wizard = env["account.payment.register"].with_context(**context).create(values)
    return wizard.action_create_payments()


def ensure_pricelist(company, template):
    Pricelist = env["product.pricelist"]
    pricelist = Pricelist.search(
        [("name", "=", "UNT13 Fixture Wholesale"), ("company_id", "=", company.id)],
        limit=1,
    )
    if not pricelist:
        pricelist = Pricelist.create(
            {
                "name": "UNT13 Fixture Wholesale",
                "currency_id": company.currency_id.id,
                "company_id": company.id,
            }
        )
        env["product.pricelist.item"].create(
            {
                "pricelist_id": pricelist.id,
                "applied_on": "1_product",
                "product_tmpl_id": template.id,
                "compute_price": "fixed",
                "fixed_price": 23.47,
                "min_quantity": 1,
            }
        )
    return pricelist


company = env.company
warehouse = env.ref("stock.warehouse0")

# Normalize every populated sale.order before confirmation can replace dates with now().
sale_orders = env["sale.order"].search([], order="id")
pin_dates(sale_orders, "date_order")
draft_orders = sale_orders.filtered(lambda order: order.state in ("draft", "sent"))
for order in draft_orders.sorted("id"):
    chosen_date = order.date_order
    order.action_confirm()
    order.date_order = chosen_date
print(f"sale orders dated={len(sale_orders)} confirmed={len(draft_orders)}")

# Seed baseline product and accounting configuration through the ORM.
template = env["product.template"].create(
    {
        "name": "UNT13 Fixture Goods",
        "is_storable": True,
        "sale_ok": True,
        "purchase_ok": True,
    }
)
product = template.product_variant_id
base_units = env["product.base.unit"].search([], order="id")
if not base_units:
    base_units = env["product.base.unit"].create(
        [{"name": "Litre"}, {"name": "Kilogram"}]
    )
base_unit = base_units[0]
if "base_unit_id" in template._fields:
    template.base_unit_id = base_unit
    template.base_unit_count = 1

if not env["product.tag"].search_count([]):
    templates = env["product.template"].search([], order="id", limit=2)
    variants = env["product.product"].search([], order="id", limit=3)
    tag_values = [
        {
            "name": "Fragile",
            "sequence": 10,
            "color": 1,
            "visible_to_customers": True,
            "product_template_ids": [(6, 0, templates.ids)],
            "product_product_ids": [(6, 0, variants.ids)],
        },
        {
            "name": "Seasonal",
            "sequence": 20,
            "color": 4,
            "visible_to_customers": False,
            "product_template_ids": [(6, 0, templates[:1].ids)],
        },
        {"name": "Clearance", "sequence": 5},
    ]
    env["product.tag"].create(tag_values)

pricelist = ensure_pricelist(company, template)
customer = env["res.partner"].create(
    {"name": "UNT13 Fixture Customer", "is_company": True, "customer_rank": 1}
)
vendor = env["res.partner"].create(
    {"name": "UNT13 Fixture Supplier", "is_company": True, "supplier_rank": 1}
)

package_type = env["stock.package.type"].search(
    [("barcode", "=", "TOTE-UNT13-FIXTURE")], limit=1
)
if not package_type:
    routes = warehouse.reception_route_id | warehouse.delivery_route_id
    package_type = env["stock.package.type"].create(
        {
            "name": "UNT13 seeded tote",
            "barcode": "TOTE-UNT13-FIXTURE",
            "package_use": "reusable",
            "sequence": 5,
            "height": 30.0,
            "width": 40.0,
            "packaging_length": 60.0,
            "base_weight": 1.5,
            "max_weight": 25.0,
            "route_ids": [(6, 0, routes.ids)],
        }
    )
pallet = env.ref("stock.package_type_01", raise_if_not_found=False)
package_types = package_type | pallet

storage_categories = env["stock.storage.category"].search([], order="id")
if not storage_categories:
    storage_categories = env["stock.storage.category"].create(
        [
            {
                "name": "UNT13 Fixture Capacity",
                "company_id": company.id,
                "max_weight": 250,
                "allow_new_product": "mixed",
            },
            {
                "name": "UNT13 Fixture Overflow",
                "company_id": company.id,
                "max_weight": 500,
                "allow_new_product": "empty",
            },
        ]
    )
elif len(storage_categories) < 2:
    storage_categories |= env["stock.storage.category"].create(
        {
            "name": "UNT13 Fixture Overflow",
            "company_id": company.id,
            "max_weight": 500,
            "allow_new_product": "empty",
        }
    )
storage_category = storage_categories[0]
if not env["stock.storage.category.capacity"].search_count([]):
    capacity_values = [
        {
            "storage_category_id": storage_category.id,
            "product_id": product.id,
            "quantity": 40,
        }
    ]
    if len(storage_categories) > 1:
        capacity_values.append(
            {
                "storage_category_id": storage_categories[1].id,
                "package_type_id": package_type.id,
                "quantity": 4,
            }
        )
    env["stock.storage.category.capacity"].create(capacity_values)

shelf = env["stock.location"].search(
    [("name", "=", "UNT13 Fixture Shelf")], order="id", limit=1
)
if not shelf:
    shelf = env["stock.location"].create(
        {
            "name": "UNT13 Fixture Shelf",
            "location_id": warehouse.lot_stock_id.id,
            "usage": "internal",
            "company_id": company.id,
            "storage_category_id": storage_category.id,
        }
    )
if not env["stock.putaway.rule"].search_count(
    [("product_id", "=", product.id), ("location_out_id", "=", shelf.id)]
):
    env["stock.putaway.rule"].create(
        {
            "company_id": company.id,
            "product_id": product.id,
            "location_in_id": warehouse.lot_stock_id.id,
            "location_out_id": shelf.id,
            "package_type_ids": [(6, 0, package_types.ids)],
        }
    )

tags = env["stock.scrap.reason.tag"].search([], order="id")
if not tags:
    tags = env["stock.scrap.reason.tag"].create(
        [
            {"name": "Damaged in transit", "sequence": 10, "color": 1},
            {"name": "Expired", "sequence": 20, "color": 5},
            {"name": "Quality check failed", "sequence": 5},
        ]
    )

for picking_type in env["stock.picking.type"].search([], order="id")[:2]:
    if not picking_type.wave_category_ids:
        picking_type.wave_category_ids = [
            (6, 0, env["product.category"].search([], order="id", limit=2).ids)
        ]

journals = env["account.journal"].search(
    [("company_id", "=", company.id)], order="id", limit=2
)
journal_groups = env["account.journal.group"].search([], order="id")
if not journal_groups:
    journal_groups = env["account.journal.group"].create(
        [
            {"name": "Statutory ledger", "sequence": 1},
            {"name": "IFRS ledger", "sequence": 2},
        ]
    )
for journal, journal_group in zip(journals, journal_groups):
    if not journal.journal_group_id:
        journal.journal_group_id = journal_group

tax = env["account.tax"].search([("company_id", "=", company.id)], order="id", limit=1)
if not tax:
    tax = env["account.tax"].create(
        {
            "name": "UNT13 fixture sales tax",
            "amount": 5,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "company_id": company.id,
        }
    )
reconcile_model = env["account.reconcile.model"].search(
    [("company_id", "=", company.id)], order="id", limit=1
)
if not reconcile_model:
    reconcile_model = env["account.reconcile.model"].create(
        {
            "name": "UNT13 Fixture Tax Reconciliation",
            "company_id": company.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "account_id": env["account.account"].search(
                            [("company_ids", "in", company.id), ("account_type", "=", "expense")],
                            order="id",
                            limit=1,
                        ).id,
                        "amount_type": "percentage",
                        "amount_string": "100",
                    },
                )
            ],
        }
    )
line = reconcile_model.line_ids[:1]
if not line:
    line = env["account.reconcile.model.line"].create(
        {
            "model_id": reconcile_model.id,
            "account_id": env["account.account"].search(
                [("company_ids", "in", company.id), ("account_type", "=", "expense")],
                order="id",
                limit=1,
            ).id,
            "amount_type": "percentage",
            "amount_string": "100",
        }
    )
line.tax_ids = [(6, 0, tax.ids)]
accounts = env["account.account"].search(
    [("company_ids", "in", company.id)], order="id"
)
if accounts and not accounts[:1].tax_ids:
    accounts[0].tax_ids = [(4, tax.id)]
sale_taxes = env["account.tax"].search(
    [
        ("company_id", "=", company.id),
        ("type_tax_use", "=", "sale"),
    ],
    order="id",
)
if sale_taxes and not env["account.tax"].search(
    [("name", "=", "UNT13 Scenario Group Tax"), ("amount_type", "=", "group")],
    limit=1,
):
    env["account.tax"].create(
        {
            "name": "UNT13 Scenario Group Tax",
            "amount_type": "group",
            "type_tax_use": "sale",
            "company_id": company.id,
            "children_tax_ids": [(6, 0, sale_taxes.ids)],
        }
    )
tax_tag = env["account.account.tag"].search(
    [("name", "=", "UNT13 Scenario Tax Grid")], limit=1
)
if not tax_tag:
    tax_tag = env["account.account.tag"].create(
        {
            "name": "UNT13 Scenario Tax Grid",
            "applicability": "taxes",
            "country_id": company.country_id.id,
        }
    )
product_account_tag = env["account.account.tag"].search(
    [("name", "=", "UNT13 Scenario Product Tag")], limit=1
)
if not product_account_tag:
    product_account_tag = env["account.account.tag"].create(
        {"name": "UNT13 Scenario Product Tag", "applicability": "products"}
    )
if "account_tag_ids" in template._fields and not template.account_tag_ids:
    template.account_tag_ids = [(4, product_account_tag.id)]
repartition = sale_taxes[:1].invoice_repartition_line_ids.filtered(
    lambda item: item.repartition_type == "tax"
)[:1]
if repartition and tax_tag not in repartition.tag_ids:
    repartition.tag_ids = [(4, tax_tag.id)]
fiscal_position = env["account.fiscal.position"].search(
    [("company_id", "=", company.id)], order="id", limit=1
)
if not fiscal_position:
    fiscal_position = env["account.fiscal.position"].create(
        {"name": "UNT13 Fixture Fiscal Position", "company_id": company.id}
    )
mapping_model = env["account.fiscal.position.account"]
if len(accounts) >= 2 and not mapping_model.search(
    [("position_id", "=", fiscal_position.id)], limit=1
):
    mapping_model.create(
        {
            "position_id": fiscal_position.id,
            "account_src_id": accounts[0].id,
            "account_dest_id": accounts[1].id,
        }
    )
states = env["res.country.state"].search(
    [("country_id", "=", company.country_id.id)], order="id", limit=2
)
if states and not fiscal_position.state_ids:
    fiscal_position.state_ids = [(6, 0, states.ids)]
bank_journal = env["account.journal"].search(
    [("company_id", "=", company.id), ("type", "=", "bank")], order="id", limit=1
)
if not bank_journal:
    bank_journal = journals[:1]
if bank_journal and not reconcile_model.match_journal_ids:
    reconcile_model.match_journal_ids = [(6, 0, bank_journal.ids)]
if customer and not reconcile_model.match_partner_ids:
    reconcile_model.match_partner_ids = [(6, 0, customer.ids)]

report = env["account.report"].search(
    [("name", "=", "UNT13 Fixture Sectioned Report")], order="id", limit=1
)
if not report:
    sections = env["account.report"].create(
        [
            {"name": "UNT13 Fixture Report Section A"},
            {"name": "UNT13 Fixture Report Section B"},
        ]
    )
    report = env["account.report"].create(
        {
            "name": "UNT13 Fixture Sectioned Report",
            "section_report_ids": [(6, 0, sections.ids)],
        }
    )
report_lines = env["account.report.line"]
parent_line = report_lines.search(
    [("report_id", "=", report.id), ("code", "=", "UNT13_FIXTURE_SALES")],
    limit=1,
)
if not parent_line:
    parent_line = report_lines.create(
        {
            "name": "UNT13 Fixture Sales",
            "report_id": report.id,
            "code": "UNT13_FIXTURE_SALES",
            "sequence": 9000,
            "expression_ids": [
                (
                    0,
                    0,
                    {
                        "label": "balance",
                        "engine": "domain",
                        "formula": "[('account_id.account_type', '=', 'income')]",
                        "subformula": "-sum",
                    },
                )
            ],
        }
    )
child_line = report_lines.search(
    [("report_id", "=", report.id), ("code", "=", "UNT13_FIXTURE_ADJ")], limit=1
)
if not child_line:
    child_line = report_lines.create(
        {
            "name": "UNT13 Fixture Sales Adjustment",
            "report_id": report.id,
            "parent_id": parent_line.id,
            "code": "UNT13_FIXTURE_ADJ",
            "sequence": 9010,
            "expression_ids": [
                (0, 0, {"label": "balance", "engine": "external", "formula": "sum"})
            ],
        }
    )
if not parent_line.expression_ids.filtered(lambda item: item.label == "adjustment"):
    env["account.report.expression"].create(
        {
            "report_line_id": parent_line.id,
            "label": "adjustment",
            "engine": "aggregation",
            "formula": "UNT13_FIXTURE_ADJ.balance",
        }
    )
expression = child_line.expression_ids.filtered(
    lambda item: item.label == "balance"
)[:1]
if expression and not env["account.report.external.value"].search(
    [("target_report_expression_id", "=", expression.id)], limit=1
):
    env["account.report.external.value"].create(
        {
            "name": "UNT13 fixture opening balance",
            "target_report_expression_id": expression.id,
            "company_id": company.id,
            "date": "2026-01-01",
            "value": 123.45,
        }
    )

cash_roundings = env["account.cash.rounding"].with_context(
    active_test=False
).search([], order="id")
rounding = cash_roundings.filtered(
    lambda item: item.active
    and item.rounding == 0.05
    and item.strategy == "add_invoice_line"
)[:1]
if not rounding:
    income = env["account.account"].search(
        [
            ("company_ids", "in", company.id),
            ("account_type", "in", ("income", "income_other")),
        ],
        order="id",
        limit=1,
    )
    expense = env["account.account"].search(
        [("company_ids", "in", company.id), ("account_type", "=", "expense")],
        order="id",
        limit=1,
    )
    assert income and expense, "cash rounding requires income and expense accounts"
    currencies = env["res.currency"].search([], order="id")
    categories = env["res.partner.category"].search([], order="id", limit=3)
    payment_methods = env["account.payment.method.line"].search(
        [], order="id", limit=3
    )
    rounding = env["account.cash.rounding"].create(
        {
            "name": "Round to 0.05",
            "rounding": 0.05,
            "strategy": "add_invoice_line",
            "rounding_method": "HALF-UP",
            "company_id": company.id,
            "profit_account_id": income.id,
            "loss_account_id": expense.id,
            "currency_ids": [(6, 0, currencies.ids)],
            "partner_category_ids": [(6, 0, categories[:2].ids)],
            "payment_method_line_ids": [(6, 0, payment_methods[:2].ids)],
        }
    )
    if not cash_roundings:
        env["account.cash.rounding"].create(
            {
                "name": "Round to 1.00",
                "rounding": 1.0,
                "strategy": "biggest_tax",
                "rounding_method": "UP",
                "sequence": 20,
                "company_id": company.id,
                "partner_category_ids": [(6, 0, categories[2:].ids)],
                "payment_method_line_ids": [(6, 0, payment_methods[2:].ids)],
            }
        )

# Receive stock from ORM-created purchase orders before confirming the fixture sales.
purchase_orders = env["purchase.order"]
for index in range(2):
    stamp = business_datetime()
    po = env["purchase.order"].create(
        {
            "partner_id": vendor.id,
            "company_id": company.id,
            "date_order": stamp,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_qty": 20,
                        "price_unit": 17.25,
                        "date_planned": stamp,
                    },
                )
            ],
        }
    )
    po.button_confirm()
    po.date_order = stamp
    purchase_orders |= po
for picking in purchase_orders.picking_ids.sorted("id"):
    validate_picking(picking)
print(f"purchase orders confirmed={len(purchase_orders)} receipts={len(purchase_orders.picking_ids)}")

# Create dated sale orders with the populated/custom pricelist, then deliver.
fixture_sales = env["sale.order"]
for index in range(4):
    stamp = business_datetime()
    order = env["sale.order"].create(
        {
            "partner_id": customer.id,
            "company_id": company.id,
            "pricelist_id": pricelist.id,
            "date_order": stamp,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_qty": 2,
                    },
                )
            ],
        }
    )
    order.action_confirm()
    order.date_order = stamp
    fixture_sales |= order
deliveries = fixture_sales.picking_ids.filtered(
    lambda picking: picking.picking_type_id.code == "outgoing"
).sorted("id")
for picking in deliveries:
    if not picking.move_ids.filtered(lambda move: move.product_id == product):
        continue
    picking.action_assign()
    for move in picking.move_ids.filtered(lambda item: item.product_id == product):
        move.quantity = min(move.product_uom_qty, move.quantity or move.product_uom_qty)
        move.picked = True
    if picking == deliveries[0]:
        move_lines = picking.move_line_ids.filtered(lambda line: line.product_id == product and line.quantity > 0)
        if move_lines:
            move_lines[0].action_put_in_pack(
                package_type_id=package_type.id,
                package_name="UNT13-FIXTURE-PACK",
            )
    validate_picking(picking)
print(f"fixture sale orders={len(fixture_sales)} deliveries={len(deliveries)}")

# Return one completed delivery through the Odoo 20 picking return API.
completed_delivery = deliveries.filtered(lambda picking: picking.state == "done")[:1]
if completed_delivery:
    returned = completed_delivery._create_return()
    for move in returned.move_ids:
        move.product_uom_qty = min(1, move.product_uom_qty or 1)
    validate_picking(returned)
    print(f"return picking={returned.name}")

# Odoo 20 scraps through a stock.move flagged by action_scrap (no stock.scrap model).
scrap_move = env["stock.move"].create(
    {
        "product_id": product.id,
        "product_uom_qty": 1,
        "quantity": 1,
        "uom_id": product.uom_id.id,
        "location_id": warehouse.lot_stock_id.id,
        "location_dest_id": company.scrap_location_id.id,
        "company_id": company.id,
        "scrap_reason_tag_ids": [(6, 0, tags[:1].ids)],
    }
)
scrap_move.action_scrap()
assert scrap_move.is_scrap and scrap_move.state == "done", scrap_move.state

# Invoice the confirmed sales and supplier orders through their ORM invoice actions.
sales_to_invoice = fixture_sales.filtered(lambda order: order.state == "sale")
customer_invoices = sales_to_invoice._create_invoices(grouped=True)
scenario_move_line = customer_invoices.line_ids.filtered(
    lambda item: item.display_type == "product"
)[:1]
if not scenario_move_line:
    scenario_move_line = env["account.move.line"].search(
        [("move_id.state", "=", "draft"), ("display_type", "=", "product")],
        order="id",
        limit=1,
    )
if scenario_move_line and "tax_tag_ids" in scenario_move_line._fields:
    scenario_move_line.tax_tag_ids = [(4, tax_tag.id)]
customer_invoices = post_invoices(customer_invoices, rounding=rounding)
purchase_orders.action_create_invoice()
vendor_bills = purchase_orders.invoice_ids
vendor_bills = post_invoices(vendor_bills)
print(f"customer invoices={len(customer_invoices)} vendor bills={len(vendor_bills)}")

# A full payment, a partial payment, a supplier payment, and a reversed customer invoice
# exercise account.payment, partial reconciliation, and full reconciliation through wizards.
receivable_invoices = customer_invoices.filtered(lambda move: move.move_type == "out_invoice").sorted("id")
if len(receivable_invoices) >= 1:
    register_payment(receivable_invoices[0])
if len(receivable_invoices) >= 2:
    residual = receivable_invoices[1].amount_residual
    if residual > 0:
        register_payment(receivable_invoices[1], round(residual / 2, 2))
if vendor_bills:
    register_payment(vendor_bills[0])

if len(receivable_invoices) >= 3:
    original = receivable_invoices[2]
    reversal = env["account.move.reversal"].with_context(
        active_model="account.move", active_ids=original.ids
    ).create(
        {
            "reason": "UNT13 fixture credit note",
            "date": business_date(),
            "journal_id": original.journal_id.id,
        }
    )
    reversal.reverse_moves()
    credit_note = reversal.new_move_ids
    credit_note = post_invoices(credit_note)
    receivable = (original.line_ids | credit_note.line_ids).filtered(
        lambda line: line.account_id.account_type == "asset_receivable"
        and not line.reconciled
    )
    if receivable:
        receivable.reconcile()

# Month-by-month: invoice the populated confirmed orders, then collect in full, in part, or not yet.
populated_sales = sale_orders.filtered(
    lambda order: order.state == "sale" and order.invoice_status == "to invoice"
).sorted("date_order")
populated_invoices = populated_sales._create_invoices(grouped=True).sorted("id")
populated_invoices = post_invoices(populated_invoices.filtered(lambda move: move.amount_total > 0))
collected = {"full": 0, "partial": 0, "open": 0}
for invoice in populated_invoices:
    outcome = rng.choices(["full", "partial", "open"], weights=[5, 3, 2])[0]
    if outcome == "full":
        register_payment(invoice)
    elif outcome == "partial":
        register_payment(invoice, round(invoice.amount_residual * rng.choice([0.25, 0.5, 0.75]), 2))
    collected[outcome] += 1
print(f"populated sale invoices={len(populated_invoices)} collected={collected}")

# Catalog and logistics baseline that UNT12 batches had to seed mid-run (seed_scenario_rows.py).
dozen = env.ref("uom.product_uom_dozen")
pack6 = env.ref("uom.product_uom_pack_6")
template.uom_ids = [(6, 0, (dozen | pack6).ids)]
product.extra_uom_ids = [(6, 0, dozen.ids)]
env["product.uom"].create({"product_id": product.id, "uom_id": dozen.id, "barcode": "UNT13-DOZEN-0001"})
env["customer.product.reference"].create(
    {"product_id": product.id, "partner_id": customer.id, "customer_product_reference": "CUST-UNT13-0001"}
)
env["product.tag"].search([], order="id", limit=1).product_product_ids = [(4, product.id)]

engraving = env["product.attribute"].create(
    {
        "name": "UNT13 Engraving",
        "create_variant": "no_variant",
        "value_ids": [(0, 0, {"name": "None"}), (0, 0, {"name": "Custom text", "is_custom": True})],
    }
)
mto = env.ref("stock.route_warehouse0_mto")
mto.write({"active": True, "product_selectable": True, "product_categ_selectable": True, "sale_selectable": True})
desk = env["product.template"].create(
    {
        "name": "UNT13 Made-to-order Desk",
        "categ_id": env["product.category"].create({"name": "UNT13 Made to order"}).id,
        "is_storable": True,
        "list_price": 640.0,
        "standard_price": 410.0,
        "route_ids": [(6, 0, mto.ids)],
        "seller_ids": [(0, 0, {"partner_id": vendor.id, "price": 410.0, "delay": 5})],
        "attribute_line_ids": [(0, 0, {"attribute_id": engraving.id, "value_ids": [(6, 0, engraving.value_ids.ids)]})],
    }
)
desk.categ_id.route_ids = [(4, mto.id)]
desk_variant = desk.product_variant_id
plain, custom = desk.attribute_line_ids.product_template_value_ids.sorted("id")
stamp = business_datetime()
mto_order = env["sale.order"].create(
    {
        "partner_id": customer.id,
        "date_order": stamp,
        "order_line": [
            (
                0,
                0,
                {
                    "product_id": desk_variant.id,
                    "product_uom_qty": 1,
                    "route_ids": [(6, 0, mto.ids)],
                    "product_no_variant_attribute_value_ids": [(6, 0, custom.ids)],
                    "product_custom_attribute_value_ids": [
                        (0, 0, {"custom_product_template_attribute_value_id": custom.id, "custom_value": "ACME HQ"})
                    ],
                },
            )
        ],
    }
)
mto_order.action_confirm()
mto_order.date_order = stamp
mto_purchase = env["purchase.order"].create(
    {
        "partner_id": vendor.id,
        "date_order": stamp,
        "order_line": [
            (0, 0, {"product_id": desk_variant.id, "product_qty": 2, "product_no_variant_attribute_value_ids": [(6, 0, plain.ids)]})
        ],
    }
)
env["stock.move"].create(
    {
        "product_id": desk_variant.id,
        "product_uom_qty": 1,
        "location_id": warehouse.lot_stock_id.id,
        "location_dest_id": env.ref("stock.stock_location_customers").id,
        "route_ids": [(6, 0, mto.ids)],
        "never_product_template_attribute_value_ids": [(6, 0, plain.ids)],
    }
)
print(f"mto order={mto_order.name} rfqs={mto_order._get_purchase_orders().mapped('name')} purchase={mto_purchase.name}")

other_warehouse = env["stock.warehouse"].search([("id", "!=", warehouse.id)], order="id", limit=1)
if other_warehouse:
    other_warehouse.resupply_wh_ids = [(6, 0, warehouse.ids)]
warehouse.in_type_id.write(
    {
        "favorite_user_ids": [(4, env.ref("base.user_admin").id)],
        "wave_location_ids": [(6, 0, (warehouse.lot_stock_id | shelf).ids)],
    }
)

analytic_account = env["account.analytic.account"].search([], order="id", limit=1)
if analytic_account:
    env["account.analytic.distribution.model"].create(
        {"partner_id": customer.id, "analytic_distribution": {str(analytic_account.id): 100}}
    )
env["resource.calendar.leaves"].create(
    {
        "name": "UNT13 company holiday",
        "calendar_id": company.resource_calendar_id.id,
        "date_from": datetime.datetime(2026, 8, 14, 0),
        "date_to": datetime.datetime(2026, 8, 14, 23),
    }
)
env["resource.resource"].create({"name": "Forklift 1", "resource_type": "material", "calendar_id": company.resource_calendar_id.id})
env["utm.campaign"].create({"name": "UNT13 Autumn promotion", "tag_ids": [(0, 0, {"name": "Seasonal promo"})]})

# Lock dates are applied only after all postings have been completed.
company.write({"sale_lock_date": LOCK_DATE})
env["account.lock_exception"].create(
    {
        "company_id": company.id,
        "user_id": env.uid,
        "reason": "UNT13 fixture late posting exception",
        "lock_date_field": "sale_lock_date",
        "lock_date": LOCK_EXCEPTION_DATE,
        "end_datetime": FIXED_INSTANT + datetime.timedelta(days=7),
    }
)
assert company.with_user(env.user)._get_user_lock_date("sale_lock_date") == LOCK_EXCEPTION_DATE
env.flush_all()
print(
    "seeded mandatory rows:",
    {
        model: env[model].search_count([])
        for model in (
            "account.cash.rounding",
            "account.full.reconcile",
            "account.journal.group",
            "account.lock_exception",
            "account.partial.reconcile",
            "account.payment",
            "account.report.expression",
            "account.report.external.value",
            "product.base.unit",
            "product.pricelist",
            "product.pricelist.item",
            "product.tag",
            "stock.package.history",
            "stock.putaway.rule",
            "stock.scrap.reason.tag",
            "stock.storage.category.capacity",
            "account.reconcile.model.line",
        )
    },
)
# Odoo colours generated user avatars from the partner's PostgreSQL create_date (wall clock);
# redraw them exactly as Odoo does, seeded with the FIXED_INSTANT the build pins create_date to.
generated_avatars = env["ir.attachment"].search(
    [("res_model", "=", "res.partner"), ("res_field", "=", "image_1920"), ("mimetype", "=", "image/svg+xml")],
    order="res_id",
)
for partner in env["res.partner"].with_context(active_test=False).browse(generated_avatars.mapped("res_id")):
    initial = html_escape(partner.name[0].upper())
    bgcolor = get_random_ui_color_from_seed(f"{partner.name}{FIXED_INSTANT.timestamp()}")
    partner.image_1920 = BinaryBytes(
        (
            '<?xml version="1.0" encoding="UTF-8" ?>'
            '<svg height="180" width="180" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
            f'<rect fill="{bgcolor}" height="180" width="180"/>'
            f'<text fill="#ffffff" font-size="96" text-anchor="middle" x="90" y="125" font-family="sans-serif">{initial}</text>'
            "</svg>"
        ).encode(),
        filename=f"avatar_{initial}.svg",
    )
print(f"generated avatars redrawn={len(generated_avatars)}")
env.cr.commit()
