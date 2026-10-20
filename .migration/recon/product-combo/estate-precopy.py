"""Pre-copy the opted-in models' unprefixed collections into a clone's prefixed namespace.

usage: python precopy.py <clone db name>   (MONGODB_ATLAS_URI in the environment)
Copies documents only; the storage path builds the indexes on -u. Idempotent: the prefixed
collection is removed and refilled on every run. Writes go to odoo_migration.<clone>__* only.
"""
import os, sys, json
import pymongo

MODELS = ['uomUom', 'updateProductAttributeValue', 'productAttribute', 'productBaseUnit', 'productAttributeValue',
          'productTemplate', 'productComboItem', 'productTag', 'productUom', 'productProduct',
          'productTemplateAttributeLine', 'productCategory', 'productTemplateAttributeValue', 'productDocument',
          'productCombo']
clone = sys.argv[1]
assert clone and clone != 'odoo_migration'
db = pymongo.MongoClient(os.environ['MONGODB_ATLAS_URI'])['odoo_migration']
out = {}
for name in MODELS:
    target = f'{clone}__{name}'
    db.drop_collection(target)
    docs = list(db[name].find({}))
    if docs:
        db[target].insert_many(docs, ordered=True)
    out[name] = {'source': db[name].count_documents({}), 'copied': db[target].count_documents({})}
    assert out[name]['source'] == out[name]['copied'], name
print(json.dumps({'clone': clone, 'collections': out}, indent=1))
