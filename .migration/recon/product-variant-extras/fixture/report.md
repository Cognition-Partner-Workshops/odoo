# Recon report: unit `product-variant-extras`

- **Verdict: UNVERIFIED** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productLabelLayout`, `productAttributeCustomValue`
- Seed: `0`
- Generated: 2026-10-20T02:23:56.537223+00:00
- **WARNING: UNVERIFIED collection productLabelLayout: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection productAttributeCustomValue: 0 source rows, key/shape/field rules unexercised**
- 19 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 6 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 6 | PASS |
| 2 | per_field_aggregates | 12 | PASS |
| 3 | keyed_diffs | 0 | PASS |
| 4 | app_level_parity | 9 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productLabelLayout": 0,
    "productAttributeCustomValue": 0
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productLabelLayout.packagingId",
    "productLabelLayout.pricelistId",
    "productLabelLayout.createUid",
    "productLabelLayout.writeUid",
    "productLabelLayout.barcodeFormat",
    "productLabelLayout.printFormat",
    "productLabelLayout.zplTemplate",
    "productLabelLayout.extraHtml",
    "productLabelLayout.withPrice",
    "productLabelLayout.createDate",
    "productLabelLayout.writeDate",
    "productLabelLayout.moveQuantity",
    "productLabelLayout.printPackaging",
    "productAttributeCustomValue.createUid",
    "productAttributeCustomValue.writeUid",
    "productAttributeCustomValue.customValue",
    "productAttributeCustomValue.createDate",
    "productAttributeCustomValue.writeDate",
    "productAttributeCustomValue.saleOrderLineId"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productLabelLayout.barcodeFormat",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productLabelLayout.printFormat",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productLabelLayout.zplTemplate",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productLabelLayout.extraHtml",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productLabelLayout.moveQuantity",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttributeCustomValue.customValue",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "fields_fully_deferred": 9
}
```

## Tier 3 coverage
```json
{
  "productLabelLayout": {
    "mode": "full_diff",
    "population": 0,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productLabelLayout.productIds": 0,
    "productLabelLayout.productTmplIds": 0,
    "productLabelLayout.productUomIds": 0,
    "productLabelLayout.moveIds": 0
  },
  "productAttributeCustomValue": {
    "mode": "full_diff",
    "population": 0,
    "duplicate_source_key_count": 0
  }
}
```
