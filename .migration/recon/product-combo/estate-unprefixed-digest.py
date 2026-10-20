"""Read-only content digest of the 15 unprefixed collections: sha256 over the canonical extended JSON of every
document sorted by _id, plus the count. usage: python unprefixed_digest.py <out.json>"""
import os, sys, json, hashlib, pymongo
from bson.json_util import dumps, CANONICAL_JSON_OPTIONS
MODELS = ['uomUom', 'updateProductAttributeValue', 'productAttribute', 'productBaseUnit', 'productAttributeValue',
          'productTemplate', 'productComboItem', 'productTag', 'productUom', 'productProduct',
          'productTemplateAttributeLine', 'productCategory', 'productTemplateAttributeValue', 'productDocument',
          'productCombo']
db = pymongo.MongoClient(os.environ['MONGODB_ATLAS_URI'])['odoo_migration']
out = {}
for name in MODELS:
    lines = [dumps(doc, json_options=CANONICAL_JSON_OPTIONS, sort_keys=True) for doc in db[name].find({}, sort=[('_id', 1)])]
    out[name] = {'count': len(lines), 'sha256': hashlib.sha256('\n'.join(lines).encode()).hexdigest()}
with open(sys.argv[1], 'w') as f:
    json.dump(out, f, indent=1)
print(json.dumps(out))
