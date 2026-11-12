# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import os
import tempfile
from unittest.mock import patch

from odoo.orm.registry import Registry
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mongo_storage
from odoo.tools.misc import config

UNIT = 'ormSignalingAssets'


@tagged('-standard', 'mongo_migration')
class TestMongoSignalingAssets(TransactionCase):
    """`assets` signaling behind the per-request source | reads | writes switch.

    Needs MONGO_LOCAL_URI pointing at a local MongoDB holding odoo_unt16.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.environ.get('MONGO_LOCAL_URI'):
            cls.skipTest(cls, "MONGO_LOCAL_URI is not set")

    def setUp(self):
        super().setUp()
        fd, self.switch_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        self.addCleanup(os.unlink, self.switch_path)
        patcher = patch.dict(config.options, {'mongo_storage_switch': self.switch_path})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(mongo_storage._last_source_write.pop, UNIT, None)
        self.set_mode('source')
        self.target = mongo_storage.collection(UNIT)
        self.target.delete_many({})
        self.target.insert_one({'_id': 41, 'date': mongo_storage._utcnow_ms()})
        self.addCleanup(self.target.delete_many, {})

    def set_mode(self, mode, checkpoint=None):
        data = {'database': 'odoo_unt16', 'uri_env': 'MONGO_LOCAL_URI', 'units': {UNIT: mode}}
        if checkpoint:
            data['cdc_checkpoints'] = {UNIT: checkpoint}
        with open(self.switch_path, 'w', encoding='utf-8') as stream:
            json.dump(data, stream)
        mongo_storage._switch['mtime'] = None

    def source_max(self):
        self.env.cr.execute("SELECT max(id) FROM orm_signaling_assets")
        return self.env.cr.fetchone()[0]

    def assets_sequence(self):
        return Registry.get_sequences(self.registry, self.env.cr)[1]['assets']

    def test_source_mode(self):
        before = self.source_max()
        self.assertEqual(self.assets_sequence(), before)
        Registry._signal_changes(self.registry, self.env.cr, ['assets'])
        self.assertGreater(self.source_max(), before)
        self.assertEqual(self.target.count_documents({}), 1)

    def test_reads_mode(self):
        self.set_mode('reads', checkpoint='FFFFFFFF/FFFFFFFF')
        self.assertEqual(self.assets_sequence(), 41)
        before = self.source_max()
        # a request that writes stays on the source until the CDC checkpoint passes it
        Registry._signal_changes(self.registry, self.env.cr, ['assets'])
        self.assertGreater(self.source_max(), before)
        self.assertEqual(self.target.count_documents({}), 1)
        self.assertEqual(self.assets_sequence(), 41)
        self.set_mode('reads', checkpoint='0/0')
        self.assertEqual(self.assets_sequence(), self.source_max())
        self.set_mode('reads')
        self.assertEqual(self.assets_sequence(), self.source_max())

    def test_writes_mode(self):
        self.set_mode('writes')
        before = self.source_max()
        Registry._signal_changes(self.registry, self.env.cr, ['assets'])
        self.assertEqual(self.target.count_documents({}), 1, "applied only after commit")
        self.env.cr.postcommit.run()
        self.assertEqual(self.source_max(), before)
        self.assertEqual(self.target.find_one({}, sort=[('_id', -1)])['_id'], 42)
        self.assertEqual(self.assets_sequence(), 42)

    def test_writes_mode_rollback(self):
        self.set_mode('writes')
        Registry._signal_changes(self.registry, self.env.cr, ['assets'])
        self.env.cr.postcommit.clear()
        self.assertEqual(self.target.count_documents({}), 1)

    def test_writes_mode_autovacuum(self):
        self.set_mode('writes')
        old = mongo_storage._utcnow_ms().replace(year=2000)
        self.target.insert_many([{'_id': i, 'date': old} for i in range(1, 41)])
        self.env['ir.autovacuum']._gc_orm_signaling()
        self.env.cr.postcommit.run()
        self.assertEqual(sorted(d['_id'] for d in self.target.find()), list(range(32, 42)))
