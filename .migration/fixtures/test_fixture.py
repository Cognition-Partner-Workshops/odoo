import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fixture as builder
import load_fixture as loader


class FixtureTests(unittest.TestCase):
    def testBounds(self):
        stat = {"values": {"p50": 2, "p99": 7, "max": 20}}
        low, high = builder.bounds(stat, 101)
        for counts in (low, high):
            self.assertEqual(builder.quantile(counts, .5), 2)
            self.assertEqual(builder.quantile(counts, .99), 7)
            self.assertLessEqual(max(counts), 20)
        low, _ = builder.bounds(stat, 101, True)
        self.assertEqual(low.count(20), 1)
        self.assertEqual(builder.bounds(stat, 0), ([], []))

    def testLocalUri(self):
        for uri in ("mongodb://localhost:27017", "mongodb://127.0.0.1/odoo_unt16"):
            with patch.dict(os.environ, {"MONGO_LOCAL_URI": uri}):
                self.assertEqual(loader.localUri(), uri)
        for uri in ("mongodb+srv://example.com", "mongodb://example.com", "mongodb://localhost/other",
                    "mongodb://localhost,example.com"):
            with patch.dict(os.environ, {"MONGO_LOCAL_URI": uri}):
                with self.assertRaises(ValueError):
                    loader.localUri()

    def testUniqueRepair(self):
        collection = {"collection": "example", "root_table": "example", "fields": [
            {"source": "name", "target": "name", "bson_type": "string"}],
            "decision": {}, "indexes": [{"keys": [["name", 1]], "unique": True}]}
        documents = [{"_id": 1, "name": "same"}, {"_id": 2, "name": "same"}]
        repairs = builder.repairUnique(documents, collection, {}, {}, [])
        self.assertEqual(len(repairs), 1)
        self.assertNotEqual(documents[0]["name"], documents[1]["name"])
        self.assertEqual(builder.repairUnique([], collection, {}, {}, []), [])

    def testUniqueFkRepairRespectsCap(self):
        collection = {"collection": "example", "root_table": "example", "fields": [
            {"source": "parent_id", "target": "parentId", "bson_type": "int"}],
            "decision": {"references": [{"column": ["parent_id"], "to": "parent"}]},
            "indexes": [{"keys": [["parentId", 1]], "unique": True}]}
        stat = {"subject": {"child": "example", "child_columns": ["parent_id"]}, "values": {"max": 1}}
        documents = [{"_id": 1, "parentId": None}, {"_id": 2, "parentId": None}]
        builder.repairUnique(documents, collection, {"parent": "parent"}, {"parent": 2}, [stat])
        self.assertEqual(documents[1]["parentId"], 1)


if __name__ == "__main__":
    unittest.main()
