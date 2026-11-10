"""Build a slice's MongoDB documents from source rows, following one mapping_spec.json entry.

Pure Python (no Odoo import) so the CDC stand-in (sync_slice.py) and the Odoo switch share it.
"""
import json
from datetime import date, datetime, timezone
from pathlib import Path

repoRoot = Path(__file__).resolve().parents[4]
mappingPath = repoRoot / ".migration" / "mapping_spec.json"


def loadEntry(collectionName, specPath=mappingPath):
    spec = json.loads(Path(specPath).read_text())
    for entry in spec["collections"]:
        if entry["collection"] == collectionName:
            return entry
    raise KeyError(f"collection {collectionName} is not in {specPath}")


def toBson(value, bsonType):
    if value is None:
        return None
    if bsonType == "bool":
        return bool(value)
    if bsonType == "int":
        return int(value)
    if bsonType == "date":
        if isinstance(value, datetime):
            stamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            return stamp.replace(microsecond=stamp.microsecond // 1000 * 1000)
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if bsonType == "object" and isinstance(value, str):
        return json.loads(value)
    return value


def buildDocument(entry, row, childRows):
    """row: {column: value} of the root table; childRows: {array_path: [child row dicts]}."""
    keyColumn = entry["key"]["source"][0]
    doc = {"_id": row[keyColumn]}
    for field in entry["fields"]:
        doc[field["target"]] = toBson(row.get(field["source"]), field["bson_type"])
    for embed in entry.get("embeds", []):
        doc[embed["array_path"]] = [
            {f["target"]: toBson(child.get(f["source"]), f["bson_type"]) for f in embed["child_fields"]}
            for child in childRows.get(embed["array_path"], [])
        ]
    return doc
