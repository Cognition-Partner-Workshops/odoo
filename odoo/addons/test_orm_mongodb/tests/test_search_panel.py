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
        self.commands = []

    def started(self, event):
        if next(iter(event.command.values()), None) == self.collection:
            self.count += 1
            self.commands.append(f"{event.command_name} {str(event.command.get('pipeline', event.command.get('filter')))[:160]}")

    def succeeded(self, event):
        pass

    def failed(self, event):
        pass


@tagged('at_install', '-post_install')
class TestSearchPanel(TransactionCase):
    """ The search panel's many2many counters come from one grouped read of
    the model's collection, not from one search_count per value. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Tag = cls.env['test_orm_mongodb.tag']
        cls.links = cls.env['test_orm_mongodb.pg_link'].create([{'name': f'link {i}'} for i in range(5)])
        cls.tags = cls.Tag.create([{
            'name': f'tag {i}',
            'sequence': i,
            'link_ids': [Command.set(cls.links[:i + 1].ids)],
        } for i in range(5)])

    def round_trips(self, func):
        """ Return the MongoDB round trips to the tag collection of ``func()``. """
        counter = CommandCounter(storage_mongodb.get_collection(self.Tag).name)
        uri = os.environ.get('ODOO_MONGODB_URI', storage_mongodb.DEFAULT_URI)
        client = pymongo.MongoClient(uri, tz_aware=False, appname='odoo', connect=False, event_listeners=[counter])
        self.addCleanup(client.close)
        self.env.flush_all()
        self.env.invalidate_all()
        self.env.cr.cache.pop(storage_mongodb._AGGREGATE_CACHE, None)
        with patch.object(storage_mongodb, '_client', lambda uri: client):
            result = func()
        self.last_commands = counter.commands
        return counter.count, result

    def counters(self, tags, **kwargs):
        trips, result = self.round_trips(lambda: self.Tag.search_panel_select_multi_range(
            'link_ids', enable_counters=True, search_domain=[('id', 'in', tags.ids)], **kwargs))
        return trips, {value['id']: value['__count'] for value in result['values']}

    def test_counters_in_one_read(self):
        expected = {link.id: self.Tag.search_count([('id', 'in', self.tags.ids), ('link_ids', 'in', link.id)]) for link in self.links}
        self.assertEqual(expected, {self.links[i].id: 5 - i for i in range(5)})
        trips_two, counts = self.counters(self.tags[:2])
        self.assertEqual(counts, {self.links[0].id: 2, self.links[1].id: 1})
        trips_five, counts = self.counters(self.tags)
        self.assertEqual(counts, expected)
        # five values cost the same round trips as two: one grouped read
        self.assertEqual(trips_five, trips_two)

    def test_counters_with_filter_domain(self):
        """ With an extra domain the counts come from a second grouped read, still not one per value. """
        trips_two, counts = self.counters(self.tags[:2], filter_domain=[('sequence', '<', 3)])
        self.assertEqual(counts, {self.links[0].id: 2, self.links[1].id: 1})
        trips_five, counts = self.counters(self.tags, filter_domain=[('sequence', '<', 3)])
        self.assertEqual(counts, {self.links[0].id: 3, self.links[1].id: 2, self.links[2].id: 1, self.links[3].id: 0, self.links[4].id: 0})
        # two grouped reads (search, group, link expansion), not three round trips per value
        self.assertLessEqual(trips_five, 6, self.last_commands)
        self.assertLessEqual(trips_two, trips_five)
