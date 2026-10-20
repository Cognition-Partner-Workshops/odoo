# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
import json

from odoo.fields import Domain

from . import controllers
from . import models
from . import report
from . import wizard


# TODO: Apply proper fix & remove in master
def pre_init_hook(env):
    env['ir.model.data'].search([
        ('model', 'like', 'stock'),
        ('module', '=', 'stock')
    ]).unlink()


def post_init_hook(env):
    _assign_default_mail_template_picking_id(env)
    _create_inventory_adjustment(env)


def uninstall_hook(env):
    picking_type_ids = env["stock.picking.type"].with_context({"active_test": False}).search([])
    picking_type_ids.sequence_id.unlink()
    _save_current_inventory(env)


def _assign_default_mail_template_picking_id(env):
    company_ids_without_default_mail_template_id = env['res.company'].search([
        ('stock_mail_confirmation_template_id', '=', False)
    ])
    default_mail_template_id = env.ref('stock.mail_template_data_delivery_confirmation', raise_if_not_found=False)
    if default_mail_template_id:
        company_ids_without_default_mail_template_id.write({
            'stock_mail_confirmation_template_id': default_mail_template_id.id,
        })


def _read_stored_qty_available(env):
    """ Stored ``qty_available`` of product.product (the column stock turns into a
        computed field), as ``{product_id: {company_id: quantity}}``, read from the
        model's storage: its collection when the model is on MongoDB, else its table.
    """
    Product = env['product.product']
    if Product._storage == 'mongodb':
        store = env.registry.mongo_store
        path = store.field_path(Product, 'qty_available')
        return {doc['_id']: doc[path] for doc in store.find(Product, {path: {'$ne': None}}, {path: 1})}
    env.cr.execute("""SELECT id, qty_available FROM product_product WHERE qty_available IS NOT NULL;""")
    return dict(env.cr.fetchall())


def _write_stored_qty_available(env, qty_available_by_product):
    """ Inverse of ``_read_stored_qty_available``: write the stored ``qty_available``
        of the given products into the model's storage. """
    Product = env['product.product']
    if Product._storage == 'mongodb':
        store = env.registry.mongo_store
        path = store.field_path(Product, 'qty_available')
        store.bulk_update(Product, [
            (product_id, {'$set': {path: quantity_per_company}})
            for product_id, quantity_per_company in qty_available_by_product.items()
        ])
        return
    query = """
        UPDATE product_product AS p
        SET qty_available = v.qty::jsonb
        FROM (VALUES %s) AS v(id, qty)
        WHERE p.id = v.id
    """
    values = [
        (product_id, json.dumps(quantity_per_company))
        for product_id, quantity_per_company in qty_available_by_product.items()
    ]
    env.cr.execute_values(query, values)


def _create_inventory_adjustment(env):
    qty_available_by_company = defaultdict(lambda: defaultdict(float))
    for product_id, qty_available in _read_stored_qty_available(env).items():
        for company_id, quantity in qty_available.items():
            qty_available_by_company[int(company_id)][product_id] = quantity

    for company_id, qty_available in qty_available_by_company.items():
        inventory_quant_vals = []
        location = env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1).lot_stock_id
        # Maybe we should automatically create a warehouse for them?
        if not location:
            continue
        for product, quantity in qty_available.items():
            inventory_quant_vals.append({
                'product_id': product,
                'inventory_quantity': quantity,
                'location_id': location.id,
            })
        env['stock.quant'].create(inventory_quant_vals)._apply_inventory()


def _save_current_inventory(env):
    """ Injects the current computed value qty_on_hand in the stored qty_on_hand field
        (with stock module installed qty_on_hand is computed and its stored without)
    """
    qty_available_by_product = defaultdict(lambda: defaultdict(float))
    to_adjust = Domain.AND([
        Domain('type', '=', 'consu'),
        Domain('is_storable', '=', True)
    ])
    for company in env["res.company"].sudo().search([]):
        for product in env['product.product'].with_company(company).sudo().search([to_adjust]):
            if product.qty_available:
                qty_available_by_product[product.id][str(company.id)] = product.qty_available
    _write_stored_qty_available(env, qty_available_by_product)
