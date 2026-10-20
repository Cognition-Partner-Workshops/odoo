"""Read-only probes past the gate on the real odoo_migration collections (counts only, no values)."""
import os, sys, json, pymongo
from bson.decimal128 import Decimal128
from datetime import datetime
db = pymongo.MongoClient(os.environ['MONGODB_ATLAS_URI'])['odoo_migration']
W3 = ['productPricelist','productPricelistItem','productSupplierinfo','productCombo','productComboItem','productAttributeCustomValue','productLabelLayout']
REFS = {  # (collection, field) -> referenced collection
 ('productPricelistItem','pricelistId'):'productPricelist', ('productPricelistItem','basePricelistId'):'productPricelist',
 ('productPricelistItem','categId'):'productCategory', ('productPricelistItem','productTmplId'):'productTemplate',
 ('productPricelistItem','productId'):'productProduct', ('productPricelistItem','uomId'):'uomUom',
 ('productSupplierinfo','productTmplId'):'productTemplate', ('productSupplierinfo','productId'):'productProduct', ('productSupplierinfo','uomId'):'uomUom',
 ('productComboItem','comboId'):'productCombo', ('productComboItem','productId'):'productProduct',
 ('productAttributeCustomValue','customProductTemplateAttributeValueId'):'productTemplateAttributeValue',
 ('productLabelLayout','pricelistId'):'productPricelist', ('productLabelLayout','productIds'):'productProduct', ('productLabelLayout','productTmplIds'):'productTemplate',
 ('productLabelLayout','productUomIds'):'productUom',
 ('productLabelLayout','moveIds'):None, ('productLabelLayout','packagingId'):None,
 ('productTemplate','comboIds'):'productCombo',
}
DEC = {'productPricelistItem':['minQuantity','fixedPrice','priceDiscount','priceRound','priceSurcharge','priceMinMargin','priceMaxMargin'],
       'productSupplierinfo':['minQty','price','discount'], 'productComboItem':['extraPrice']}
ids = {}
def idset(c):
    if c not in ids: ids[c] = set(d['_id'] for d in db[c].find({}, {'_id':1}))
    return ids[c]
out = {'collections':{}, 'refs':{}, 'decimals':{}, 'indexes':{}, 'field_shapes':{}}
for c in W3 + ['productTemplate']:
    docs = list(db[c].find({}))
    out['collections'][c] = {'count': len(docs), 'distinct_ids': len({d['_id'] for d in docs}),
        'id_types': sorted({type(d['_id']).__name__ for d in docs}), 'mongo_count': db[c].count_documents({})}
    shapes = {}
    for d in docs:
        for k,v in d.items():
            shapes.setdefault(k, set()).add(type(v).__name__)
    out['field_shapes'][c] = {k: sorted(v) for k,v in sorted(shapes.items())}
    out['indexes'][c] = sorted(i['name'] for i in db[c].list_indexes())
    for (cc, f), ref in REFS.items():
        if cc != c: continue
        vals = []; nulls = 0; present = 0; dict_keys = set()
        for d in docs:
            if f not in d: continue
            present += 1
            v = d[f]
            if v is None: nulls += 1; continue
            for x in (v if isinstance(v, list) else [v]):
                if isinstance(x, dict):
                    dict_keys.add(tuple(sorted(x.keys()))); x = next((val for key, val in x.items() if key.endswith('Id')), None)
                vals.append(x)
        rec = {'dict_keys': sorted(map(list, dict_keys)), 'docs_with_field': present, 'nulls': nulls, 'values': len(vals), 'non_int_values': sum(1 for v in vals if not isinstance(v, int))}
        if ref: rec['dangling'] = sorted(set(str(v) for v in vals if not isinstance(v, int) or v not in idset(ref)))[:20]; rec['ref'] = ref
        out['refs'][f'{c}.{f}'] = rec
    for f in DEC.get(c, []):
        vals = [d.get(f) for d in docs if f in d]
        out['decimals'][f'{c}.{f}'] = {'present': len(vals), 'types': sorted({type(v).__name__ for v in vals}),
            'non_decimal_non_null': sum(1 for v in vals if v is not None and not isinstance(v, Decimal128))}
# date fields must be datetime or null
bad_dates = {}
for c in W3:
    for d in db[c].find({}):
        for k in ('createDate','writeDate','dateStart','dateEnd'):
            if k in d and d[k] is not None and not isinstance(d[k], datetime): bad_dates[f'{c}.{k}'] = bad_dates.get(f'{c}.{k}', 0) + 1
out['bad_dates'] = bad_dates
# expected counts: the verifier's own live recon results (Tier 1 source_counts) for the seven wave-3 collections
expected = {}
for sub in ('w3-b01/product-pricing', 'w3-b02/product-supplierinfo', 'w3-b03/product-combo', 'w3-b04/product-variant-extras'):
    expected.update(json.load(open(f'.migration/recon/wave-3/{sub}/result.json'))['tiers'][0]['stats']['source_counts'])
problems = []
for c in W3:
    v = out['collections'][c]
    if c not in expected or v['count'] != expected[c]: problems.append(f'{c}: count {v["count"]} != source {expected.get(c)}')
    if v['distinct_ids'] != v['count'] or v['id_types'] != ['int']: problems.append(f'{c}: _id not distinct ints')
for k, v in out['refs'].items():
    if v['non_int_values']: problems.append(f'{k}: {v["non_int_values"]} non-int reference values')
    if v.get('dangling'): problems.append(f'{k}: dangling {v["dangling"]}')
for k, v in out['decimals'].items():
    if v['non_decimal_non_null']: problems.append(f'{k}: {v["non_decimal_non_null"]} non-Decimal128 values')
for k, n in bad_dates.items(): problems.append(f'{k}: {n} non-datetime values')
out['expected_source_counts'] = expected
out['problems'] = problems
json.dump(out, open(sys.argv[1], 'w'), indent=1, sort_keys=True, default=str)
for c,v in out['collections'].items(): print('COLL', c, v['count'], v['distinct_ids'], v['id_types'], 'idx', out['indexes'][c])
for k,v in out['refs'].items(): print('REF', k, 'present', v['docs_with_field'], 'nulls', v['nulls'], 'vals', v['values'], 'nonint', v['non_int_values'], 'dangling', v.get('dangling'))
for k,v in out['decimals'].items(): print('DEC', k, v)
print('BAD_DATES', bad_dates)
print('PROBLEMS', len(problems), problems)
print('LABEL shapes', out['field_shapes']['productLabelLayout'])
print('TMPL comboIds shapes', out['field_shapes']['productTemplate'].get('comboIds'))
sys.exit(1 if problems else 0)
