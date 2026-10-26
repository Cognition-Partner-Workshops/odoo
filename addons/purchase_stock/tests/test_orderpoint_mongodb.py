import os
from unittest.mock import patch

import pymongo
from pymongo import monitoring

from odoo import Command
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged


class CommandCounter(monitoring.CommandListener):
    """ Counts the commands the server is sent: one per round trip. """

    def __init__(self):
        self.count = 0

    def started(self, event):
        self.count += 1

    def succeeded(self, event):
        pass

    def failed(self, event):
        pass


@tagged('post_install', '-at_install')
class TestOrderpointMongodb(TransactionCase):
    """ The replenishment list reads the forecast of its orderpoints with one
    batched lookup of the quantities in progress, not one per lead horizon. """

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
        cls.orderpoints = cls.env['stock.warehouse.orderpoint'].create([{
            'product_id': product.id,
            'location_id': warehouse.lot_stock_id.id,
            'product_min_qty': 1,
            'product_max_qty': 5,
        } for product in products])

    def commands(self, orderpoints):
        """ Return the number of MongoDB round trips a cold read of ``qty_forecast`` takes. """
        counter = CommandCounter()
        uri = os.environ.get('ODOO_MONGODB_URI', storage_mongodb.DEFAULT_URI)
        client = pymongo.MongoClient(uri, tz_aware=False, appname='odoo', connect=False, event_listeners=[counter])
        self.addCleanup(client.close)
        self.env.flush_all()
        self.env.invalidate_all()
        self.env.cr.cache.pop(storage_mongodb._AGGREGATE_CACHE, None)
        with patch.object(storage_mongodb, '_client', lambda uri: client):
            orderpoints.mapped('qty_forecast')
        return counter.count

    def test_forecast_batches_quantities_in_progress(self):
        self.assertEqual(len(set(self.orderpoints.mapped('lead_horizon_date'))), 3)     # three product contexts
        one = self.commands(self.orderpoints[0])
        self.assertEqual(self.commands(self.orderpoints), one)
