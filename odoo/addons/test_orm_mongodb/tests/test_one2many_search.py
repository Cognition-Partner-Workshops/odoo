import os
from unittest.mock import patch

import pymongo
from pymongo import monitoring

from odoo import Command
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged

from .test_storage_mongodb import setUpModule  # noqa: F401  (local MongoDB only)


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


@tagged('at_install', '-post_install')
class TestOne2manySearch(TransactionCase):
    """ A one2many condition reads the comodel's inverse column in the
    comodel search itself, not in a second round trip over its records. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Category = cls.env['test_orm_mongodb.storage_category']
        cls.Capacity = cls.env['test_orm_mongodb.storage_capacity']
        cls.categories = cls.Category.create([{
            'name': f'category {i}',
            'capacity_ids': [Command.create({'quantity': quantity}) for quantity in range(i + 1)],
        } for i in range(3)])

    def round_trips(self, func):
        counter = CommandCounter(storage_mongodb.get_collection(self.Capacity).name)
        uri = os.environ.get('ODOO_MONGODB_URI', storage_mongodb.DEFAULT_URI)
        client = pymongo.MongoClient(uri, tz_aware=False, appname='odoo', connect=False, event_listeners=[counter])
        self.addCleanup(client.close)
        self.env.flush_all()
        self.env.invalidate_all()
        self.env.cr.cache.pop(storage_mongodb._AGGREGATE_CACHE, None)
        with patch.object(storage_mongodb, '_client', lambda uri: client):
            result = func()
        return counter.count, result

    def test_one2many_condition_is_one_comodel_round_trip(self):
        trips, found = self.round_trips(lambda: self.Category.search([('capacity_ids.quantity', '>=', 1)]))
        self.assertEqual(found, self.categories[1:])
        self.assertEqual(trips, 1)
        trips, found = self.round_trips(lambda: self.Category.search([('capacity_ids', 'any', [('quantity', '=', 2)])]))
        self.assertEqual(found, self.categories[2])
        self.assertEqual(trips, 1)
        trips, found = self.round_trips(lambda: self.Category.search([('capacity_ids', 'not any', [('quantity', '>=', 1)])]))
        self.assertEqual(found, self.categories[0])
        self.assertEqual(trips, 1)
