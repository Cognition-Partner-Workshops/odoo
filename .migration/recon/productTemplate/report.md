# Recon report: unit `productTemplate`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `64b5e9ae6f3e` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `edba3af07504`
- Collections: `productTemplate`
- Seed: `0`
- Generated: 2026-10-26T14:29:45.428156+00:00
- 46 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 25 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 12 | PASS |
| 2 | per_field_aggregates | 17 | PASS |
| 3 | keyed_diffs | 439 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productTemplate": 439
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productTemplate.sequence",
    "productTemplate.categId",
    "productTemplate.companyId",
    "productTemplate.color",
    "productTemplate.baseUnitId",
    "productTemplate.createUid",
    "productTemplate.writeUid",
    "productTemplate.type",
    "productTemplate.serviceTracking",
    "productTemplate.barcode",
    "productTemplate.defaultCode",
    "productTemplate.name",
    "productTemplate.description",
    "productTemplate.descriptionPurchase",
    "productTemplate.descriptionSale",
    "productTemplate.productProperties",
    "productTemplate.listPrice",
    "productTemplate.volume",
    "productTemplate.weight",
    "productTemplate.isStorable",
    "productTemplate.saleOk",
    "productTemplate.purchaseOk",
    "productTemplate.active",
    "productTemplate.canImage1024BeZoomed",
    "productTemplate.hasConfigurableAttributes",
    "productTemplate.isFavorite",
    "productTemplate.createDate",
    "productTemplate.writeDate",
    "productTemplate.propertyAccountIncomeId",
    "productTemplate.propertyAccountExpenseId",
    "productTemplate.lotSequenceId",
    "productTemplate.tracking",
    "productTemplate.responsibleId",
    "productTemplate.propertyStockProduction",
    "productTemplate.propertyStockInventory",
    "productTemplate.descriptionPicking",
    "productTemplate.descriptionPickingout",
    "productTemplate.descriptionPickingin",
    "productTemplate.purchaseMethod",
    "productTemplate.purchaseLineWarnMsg",
    "productTemplate.lotValuated",
    "productTemplate.serviceType",
    "productTemplate.reinvoicePolicy",
    "productTemplate.invoicePolicy",
    "productTemplate.saleDelay",
    "productTemplate.saleLineWarnMsg"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productTemplate.type",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.serviceTracking",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.defaultCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.description",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPurchase",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionSale",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.productProperties",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyAccountIncomeId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyAccountExpenseId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.tracking",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.responsibleId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyStockProduction",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyStockInventory",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPicking",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPickingout",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPickingin",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.purchaseMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.purchaseLineWarnMsg",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.serviceType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.reinvoicePolicy",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.invoicePolicy",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.saleDelay",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.saleLineWarnMsg",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productTemplate.name",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.description",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPurchase",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionSale",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.productProperties",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyAccountIncomeId",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyAccountExpenseId",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.responsibleId",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyStockProduction",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyStockInventory",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPicking",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPickingout",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPickingin",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.saleDelay",
      "key": "productTemplate"
    }
  ],
  "fields_fully_deferred": 31
}
```

## Tier 3 coverage
```json
{
  "productTemplate": {
    "mode": "full_diff",
    "population": 439,
    "duplicate_source_key_count": 0
  }
}
```
