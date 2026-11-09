import hashlib
import json
import unittest
from unittest.mock import MagicMock, patch

import source_fingerprint as fingerprint


class ContentTests(unittest.TestCase):
    def testRows(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchall.side_effect = [
            [('example',), ('bus_bus',)],
            [('example', 'id', 'integer')],
            [('id',)],
        ]
        cur.copy_expert.side_effect = lambda query, output: output.write(b'1\n2\n')
        with patch.object(fingerprint.sql.Composed, 'as_string', return_value='COPY query'):
            summary = fingerprint.contentSummary(conn, {'bus_bus'}, True)
        tableHashes = {'example': hashlib.sha256(b'1\n2\n').hexdigest()}
        canonical = json.dumps(tableHashes, sort_keys=True, separators=(',', ':'))
        self.assertEqual(summary['fingerprint'], 'sha256:' + hashlib.sha256(canonical.encode()).hexdigest())
        self.assertEqual(summary['table_hashes'], tableHashes)
        self.assertEqual(summary['tables'], 1)
        self.assertEqual(summary['excluded_tables'], ['bus_bus'])
        conn.set_session.assert_called_once_with(readonly=True, isolation_level='REPEATABLE READ')

    def testEmpty(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchall.side_effect = [[], []]
        summary = fingerprint.contentSummary(conn, {'bus_bus'})
        self.assertEqual(summary['fingerprint'], 'sha256:' + hashlib.sha256(b'{}').hexdigest())
        self.assertEqual(summary['tables'], 0)
        cur.copy_expert.assert_not_called()

    def testCopyError(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchall.side_effect = [[('example',)], [('example', 'value', 'json')], []]
        cur.copy_expert.side_effect = RuntimeError('copy failed')
        with patch.object(fingerprint.sql.Composed, 'as_string', return_value='COPY query'):
            with self.assertRaisesRegex(RuntimeError, 'copy failed'):
                fingerprint.contentSummary(conn, set())


if __name__ == '__main__':
    unittest.main()
