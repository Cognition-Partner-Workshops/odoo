# Recon report: unit `product-taxonomy`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `productBaseUnit`, `productCategory`, `productDocument`, `productRemoval`, `productTag`
- Seed: `0`
- Generated: 2026-10-20T14:37:51.702660+00:00
- 48 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 21 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 18 | PASS |
| 2 | per_field_aggregates | 22 | PASS |
| 3 | keyed_diffs | 27 | PASS |
| 4 | app_level_parity | 7 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productBaseUnit": 2,
    "productCategory": 7,
    "productDocument": 2,
    "productRemoval": 4,
    "productTag": 3
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productBaseUnit.createUid",
    "productBaseUnit.writeUid",
    "productBaseUnit.name",
    "productBaseUnit.createDate",
    "productBaseUnit.writeDate",
    "productCategory.parentId",
    "productCategory.companyId",
    "productCategory.createUid",
    "productCategory.writeUid",
    "productCategory.parentPath",
    "productCategory.name",
    "productCategory.productPropertiesDefinition",
    "productCategory.createDate",
    "productCategory.writeDate",
    "productCategory.propertyAccountIncomeCategId",
    "productCategory.propertyAccountExpenseCategId",
    "productCategory.propertyValuation",
    "productCategory.propertyStockValuationAccountId",
    "productCategory.propertyStockJournal",
    "productCategory.propertyCostMethod",
    "productCategory.propertyPriceDifferenceAccountId",
    "productCategory.removalStrategyId",
    "productCategory.packagingReserveMethod",
    "productCategory.propertyAccountBillsToReceiveId",
    "productCategory.propertyAccountBilledNotReceivedId",
    "productCategory.propertyAccountInvoicesToIssueId",
    "productCategory.propertyAccountInvoicedNotDeliveredId",
    "productDocument.sequence",
    "productDocument.createUid",
    "productDocument.writeUid",
    "productDocument.active",
    "productDocument.createDate",
    "productDocument.writeDate",
    "productDocument.attachedOnSale",
    "productRemoval.createUid",
    "productRemoval.writeUid",
    "productRemoval.name",
    "productRemoval.method",
    "productRemoval.createDate",
    "productRemoval.writeDate",
    "productTag.sequence",
    "productTag.createUid",
    "productTag.writeUid",
    "productTag.color",
    "productTag.name",
    "productTag.visibleToCustomers",
    "productTag.createDate",
    "productTag.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productBaseUnit.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.productPropertiesDefinition",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountIncomeCategId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountExpenseCategId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyValuation",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyStockValuationAccountId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyStockJournal",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyCostMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyPriceDifferenceAccountId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.packagingReserveMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountBillsToReceiveId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountBilledNotReceivedId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountInvoicesToIssueId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountInvoicedNotDeliveredId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productDocument.attachedOnSale",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productRemoval.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productRemoval.method",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTag.color",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productBaseUnit.name",
      "key": "productBaseUnit"
    },
    {
      "field": "productCategory.name",
      "key": "productCategory"
    },
    {
      "field": "productCategory.productPropertiesDefinition",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountIncomeCategId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountExpenseCategId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyValuation",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyStockValuationAccountId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyStockJournal",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyCostMethod",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyPriceDifferenceAccountId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountBillsToReceiveId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountBilledNotReceivedId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountInvoicesToIssueId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountInvoicedNotDeliveredId",
      "key": "productCategory"
    },
    {
      "field": "productRemoval.name",
      "key": "productRemoval"
    },
    {
      "field": "productRemoval.method",
      "key": "productRemoval"
    },
    {
      "field": "productTag.name",
      "key": "productTag"
    }
  ],
  "fields_fully_deferred": 27
}
```

## Tier 3 coverage
```json
{
  "productBaseUnit": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "productCategory": {
    "mode": "full_diff",
    "population": 7,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productCategory.stockPickingTypeRel": 3,
    "productTag.productProductRel": 3,
    "productTag.productTemplateRel": 3
  },
  "productDocument": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "productRemoval": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
  },
  "productTag": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  }
}
```
