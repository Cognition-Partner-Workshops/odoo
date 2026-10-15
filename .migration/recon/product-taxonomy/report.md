# Recon report: unit `product-taxonomy`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productBaseUnit`, `productCategory`, `productTag`
- Seed: `1`
- Generated: 2026-10-15T16:58:08.808930+00:00
- **WARNING: UNVERIFIED collection productBaseUnit: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection productTag: 0 source rows, key/shape/field rules unexercised**
- 35 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 18 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 10 | PASS |
| 2 | per_field_aggregates | 13 | PASS |
| 3 | keyed_diffs | 8 | PASS |
| 4 | app_level_parity | 4 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productBaseUnit": 0,
    "productCategory": 8,
    "productTag": 0
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
  "fields_fully_deferred": 22
}
```

## Tier 3 coverage
```json
{
  "productBaseUnit": {
    "mode": "full_diff",
    "population": 0,
    "duplicate_source_key_count": 0
  },
  "productCategory": {
    "mode": "full_diff",
    "population": 8,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productCategory.routeIds": 0
  },
  "productTag": {
    "mode": "full_diff",
    "population": 0,
    "duplicate_source_key_count": 0
  }
}
```
