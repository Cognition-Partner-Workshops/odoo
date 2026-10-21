"""Read-only snapshot of the odoo_unt12 target (--db odoo_unt12): per-collection countDocuments, max writeDate,
and a sha256 over the raw BSON of every document ordered by _id. Usage: python target_snapshot.py <out.json>
Reads MONGODB_ATLAS_URI from the environment; never prints it. Only find/count calls are issued."""
import datetime, hashlib, json, os, sys
import bson
import pymongo

COLLECTIONS = (
    "stockStorageCategory,stockScrapReasonTag,returnReason,productCategory,productRemoval,productTag,productDocument,"
    "productBaseUnit,uomUom,stockPackageType,accountPaymentTerm,accountIncoterms,accountCashRounding,accountJournalGroup,"
    "accountLockException,accountReport,accountReportExpression,accountReportExternalValue,productAttribute,accountAccount,"
    "accountAccountTag,accountTax,accountTaxGroup,accountTaxRepartitionLine,accountFiscalPosition,"
    "accountJournal,accountPaymentMethod,accountReconcileModel,accountReconcileModelLineAccountTaxRel,productTemplate,"
    "productProduct,productTemplateAttributeValue,productAttributeValueProductTemplateAttributeLineRel,productCombo,"
    "productSupplierinfo,productPricelist,productPricelistItem,"
    "stockWarehouse,stockLocation,stockPickingType,stockRoute,stockRule,stockPutawayRule,stockStorageCategoryCapacity,"
    "stockWarehouseOrderpoint"
).split(",")

client = pymongo.MongoClient(os.environ["MONGODB_ATLAS_URI"], serverSelectionTimeoutMS=20000)
db = client.get_database("odoo_unt12")
existing = set(db.list_collection_names())
out = {"taken_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "db": "odoo_unt12", "collections": {}}
total = 0
for name in COLLECTIONS:
    if name not in existing:
        out["collections"][name] = {"count": None, "note": "collection absent"}
        continue
    coll = db.get_collection(name)
    docs = list(coll.find({}, sort=[("_id", 1)]))
    total += len(docs)
    stamps = [d["writeDate"] for d in docs if d.get("writeDate") is not None]
    latest = max(stamps) if stamps else None
    out["collections"][name] = {
        "count": coll.count_documents({}),
        "max_writeDate": latest.isoformat() if hasattr(latest, "isoformat") else latest,
        "bson_sha256": hashlib.sha256(b"".join(bson.encode(d) for d in docs)).hexdigest(),
    }
out["total_docs"] = total
out["collections_present"] = sum(1 for v in out["collections"].values() if v["count"] is not None)
with open(sys.argv[1], "w") as fh:
    json.dump(out, fh, indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != "collections"}))
print("\n".join(f"{n:55s} {v.get('count')!s:>5} {v.get('max_writeDate')}" for n, v in out["collections"].items()))
