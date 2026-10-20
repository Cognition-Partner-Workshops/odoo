"""Read-only content digest of every unprefixed odoo_migration collection: count + sha256 over canonical extended JSON sorted by _id.
usage: python digest_unprefixed.py <out.json>"""
import os, sys, json, hashlib, pymongo
from bson.json_util import dumps, CANONICAL_JSON_OPTIONS
db = pymongo.MongoClient(os.environ['MONGODB_ATLAS_URI'])['odoo_migration']
out = {}
for name in sorted(n for n in db.list_collection_names() if '__' not in n):
    lines = [dumps(doc, json_options=CANONICAL_JSON_OPTIONS, sort_keys=True) for doc in db[name].find({}, sort=[('_id', 1)])]
    out[name] = {'count': len(lines), 'sha256': hashlib.sha256('\n'.join(lines).encode()).hexdigest()}
json.dump(out, open(sys.argv[1], 'w'), indent=1, sort_keys=True)
print('DIGEST', len(out), 'collections', sum(v['count'] for v in out.values()), 'docs ->', sys.argv[1])
