import os
from unittest.mock import patch

import pymongo
from pymongo import monitoring

from odoo import Command
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged


class CommandCounter(monitoring.CommandListener):
    """ Counts the commands sent for one collection: one per round trip. """

    def __init__(self, collection):
        self.collection = collection
        self.count = 0

    def started(self, event):
        if next(iter(event.command.values()), None) == self.collection:
            self.count += 1

    def succeeded(self, event):
        pass

    def failed(self, event):
        pass


@tagged('post_install', '-at_install')
class TestOrderpointMongodb(TransactionCase):
    """ The replenishment list reads the forecast of its orderpoints with
    batched lookups: the quantities in progress, the rules and the location
    descendants are read once for all the orderpoints, not once per orderpoint. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        vendor = cls.env['res.partner'].create({'name': 'Wood Corner'})
        products = cls.env['product.product'].create([{
            'name': f'Book Shelf {delay}',
            'is_storable': True,
            'purchase_ok': True,
            'seller_ids': [Command.create({'partner_id': vendor.id, 'delay': delay, 'min_qty': 1, 'price': 750})],
        } for delay in (1, 5, 10)])
        locations = warehouse.lot_stock_id | cls.env['stock.location'].create([
            {'name': name, 'usage': 'internal', 'location_id': warehouse.lot_stock_id.id}
            for name in ('Shelf A', 'Shelf B')
        ])
        cls.orderpoints = cls.env['stock.warehouse.orderpoint'].create([{
            'product_id': product.id,
            'location_id': location.id,
            'product_min_qty': 1,
            'product_max_qty': 5,
        } for product, location in zip(products, locations)])

    def commands(self, orderpoints, model, field='qty_forecast'):
        """ Return the MongoDB round trips to ``model``'s collection of a cold read of ``field``. """
        counter = CommandCounter(storage_mongodb.get_collection(self.env[model]).name)
        uri = os.environ.get('ODOO_MONGODB_URI', storage_mongodb.DEFAULT_URI)
        client = pymongo.MongoClient(uri, tz_aware=False, appname='odoo', connect=False, event_listeners=[counter])
        self.addCleanup(client.close)
        self.env.flush_all()
        self.env.invalidate_all()
        self.env.cr.cache.pop(storage_mongodb._AGGREGATE_CACHE, None)
        with patch.object(storage_mongodb, '_client', lambda uri: client):
            orderpoints.mapped(field)
        return counter.count

    def test_forecast_batches_quantities_in_progress(self):
        """ The purchase lines in progress are looked up once for all the
        orderpoints: their domain reaches the picking types once, not once
        per product context (location and lead horizon). """
        self.assertEqual(len(set(self.orderpoints.mapped('location_id'))), 3)
        self.assertEqual(len(set(self.orderpoints.mapped('lead_horizon_date'))), 3)
        self.assertEqual(self.commands(self.orderpoints, 'stock.picking.type'), 1)

    def test_rules_read_once(self):
        """ The rules of the orderpoints' locations are read once and grouped
        in Python: the round trips to the rules do not grow with the number of
        locations, and each orderpoint gets the rules of its own lookup. """
        one, three = self.orderpoints[1].with_prefetch(), self.orderpoints
        self.assertEqual(len(set(three.mapped('location_id'))), 3)
        self.assertLessEqual(self.commands(three, 'stock.rule', 'rule_ids'), self.commands(one, 'stock.rule', 'rule_ids'))
        for orderpoint in three:
            rules = orderpoint.product_id._get_rules_from_location(orderpoint.location_id, route_ids=orderpoint.route_id)
            self.assertTrue(rules)
            self.assertEqual(orderpoint.rule_ids, rules)

    def test_descendants_read_once(self):
        """ The descendants of the orderpoints' locations are read once for the
        product quantities of all the (location, lead horizon) contexts. """
        one, three = self.orderpoints[1].with_prefetch(), self.orderpoints
        self.assertEqual(len(set(three.mapped('location_id'))), 3)
        self.assertLessEqual(self.commands(three, 'stock.location'), self.commands(one, 'stock.location'))
        in_progress = three._quantity_in_progress()
        for orderpoint in three:
            # the quantities of the product's own read, without the batched descendants
            self.env.cr.cache.pop('stock.location.descendants', None)
            quantities = orderpoint.product_id.with_context(orderpoint._get_product_context()).read(['qty_available', 'virtual_available'])[0]
            self.assertEqual(orderpoint.qty_on_hand, quantities['qty_available'])
            self.assertEqual(orderpoint.qty_forecast, quantities['virtual_available'] + in_progress[orderpoint.id])
