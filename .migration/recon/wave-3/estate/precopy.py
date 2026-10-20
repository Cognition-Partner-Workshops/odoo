"""Pre-copy every unprefixed odoo_migration collection into <clone>__<name> (the clone's own prefixed namespace).
usage: python precopy.py <clone db name>"""
import os, sys, pymongo
clone = sys.argv[1]; assert clone and '__' not in clone
db = pymongo.MongoClient(os.environ['MONGODB_ATLAS_URI'])['odoo_migration']
for name in sorted(n for n in db.list_collection_names() if '__' not in n):
    target = f'{clone}__{name}'
    db.drop_collection(target)
    docs = list(db[name].find({}))
    if docs:
        db[target].insert_many(docs)
    print('PRECOPY', name, db[name].count_documents({}), '->', target, db[target].count_documents({}))
