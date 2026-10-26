# Recon report: unit `productProduct`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `f84dbc723f61` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `11dbbd23435d`
- Collections: `productProduct`, `productSupplierinfo`
- Seed: `0`
- Generated: 2026-10-26T16:33:35.122507+00:00
- 30 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 8 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 7 | PASS |
| 2 | per_field_aggregates | 21 | PASS |
| 3 | keyed_diffs | 5173 | PASS |
| 4 | app_level_parity | 5 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productProduct": 1394,
    "productSupplierinfo": 637
  },
  "embed_source_counts": {
    "productProduct.customerProductReference": 1,
    "productProduct.uomUomRel": 1,
    "productProduct.productUom": 1,
    "productProduct.productVariantCombination": 3109,
    "productProduct.stockWarehouseOrderpoint": 30
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productProduct.baseUnitId",
    "productProduct.createUid",
    "productProduct.writeUid",
    "productProduct.defaultCode",
    "productProduct.barcode",
    "productProduct.combinationIndices",
    "productProduct.standardPrice",
    "productProduct.qtyAvailable",
    "productProduct.lstPrice",
    "productProduct.volume",
    "productProduct.weight",
    "productProduct.active",
    "productProduct.canImageVariant1024BeZoomed",
    "productProduct.isFavorite",
    "productProduct.writeDate",
    "productProduct.createDate",
    "productProduct.lotPropertiesDefinition",
    "productSupplierinfo.sequence",
    "productSupplierinfo.companyId",
    "productSupplierinfo.productId",
    "productSupplierinfo.createUid",
    "productSupplierinfo.writeUid",
    "productSupplierinfo.productName",
    "productSupplierinfo.productCode",
    "productSupplierinfo.dateStart",
    "productSupplierinfo.dateEnd",
    "productSupplierinfo.price",
    "productSupplierinfo.discount",
    "productSupplierinfo.createDate",
    "productSupplierinfo.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productProduct.defaultCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.combinationIndices",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.standardPrice",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.qtyAvailable",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.lotPropertiesDefinition",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productSupplierinfo.productName",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productSupplierinfo.productCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productProduct.standardPrice",
      "key": "productProduct"
    },
    {
      "field": "productProduct.qtyAvailable",
      "key": "productProduct"
    },
    {
      "field": "productProduct.lotPropertiesDefinition",
      "key": "productProduct"
    }
  ],
  "fields_fully_deferred": 17
}
```

## Tier 3 coverage
```json
{
  "productProduct": {
    "mode": "full_diff",
    "population": 1394,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productProduct.customerProductReference": 1,
    "productProduct.uomUomRel": 1,
    "productProduct.productUom": 1,
    "productProduct.productVariantCombination": 3109,
    "productProduct.stockWarehouseOrderpoint": 30
  },
  "productSupplierinfo": {
    "mode": "full_diff",
    "population": 637,
    "duplicate_source_key_count": 0
  }
}
```
