# Recon report: unit `productCategory`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `2f68f2104eda` (dirty) | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `e410c5367439`
- Collections: `productCategory`
- Seed: `1`
- Generated: 2026-10-26T03:33:35.568114+00:00
- 22 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 15 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 2 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 24 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productCategory": 20
  },
  "embed_source_counts": {
    "productCategory.stockPickingTypeRel": 4
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
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
    "productCategory.propertyAccountInvoicedNotDeliveredId"
  ],
  "string_aggregates_deferred_to_tier3": [
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
    }
  ],
  "document_aggregates_deferred_to_tier3": [
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
    }
  ],
  "fields_fully_deferred": 16
}
```

## Tier 3 coverage
```json
{
  "productCategory": {
    "mode": "full_diff",
    "population": 20,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productCategory.stockPickingTypeRel": 4
  }
}
```
