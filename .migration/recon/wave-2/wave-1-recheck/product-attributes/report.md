# Recon report: unit `product-attributes`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productAttribute`, `productAttributeValue`, `updateProductAttributeValue`
- Seed: `0`
- Generated: 2026-10-19T21:32:05.822944+00:00
- **WARNING: UNVERIFIED collection updateProductAttributeValue: 0 source rows, key/shape/field rules unexercised**
- 25 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 6 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 8 | PASS |
| 2 | per_field_aggregates | 16 | PASS |
| 3 | keyed_diffs | 124 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productAttribute": 14,
    "productAttributeValue": 101,
    "updateProductAttributeValue": 0
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productAttribute.sequence",
    "productAttribute.createUid",
    "productAttribute.writeUid",
    "productAttribute.createVariant",
    "productAttribute.displayType",
    "productAttribute.name",
    "productAttribute.active",
    "productAttribute.createDate",
    "productAttribute.writeDate",
    "productAttributeValue.sequence",
    "productAttributeValue.color",
    "productAttributeValue.createUid",
    "productAttributeValue.writeUid",
    "productAttributeValue.htmlColor",
    "productAttributeValue.name",
    "productAttributeValue.isCustom",
    "productAttributeValue.active",
    "productAttributeValue.createDate",
    "productAttributeValue.writeDate",
    "productAttributeValue.defaultExtraPrice",
    "updateProductAttributeValue.createUid",
    "updateProductAttributeValue.writeUid",
    "updateProductAttributeValue.mode",
    "updateProductAttributeValue.createDate",
    "updateProductAttributeValue.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productAttribute.createVariant",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttribute.displayType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttribute.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttributeValue.htmlColor",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttributeValue.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "updateProductAttributeValue.mode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productAttribute.name",
      "key": "productAttribute"
    },
    {
      "field": "productAttributeValue.name",
      "key": "productAttributeValue"
    }
  ],
  "fields_fully_deferred": 11
}
```

## Tier 3 coverage
```json
{
  "productAttribute": {
    "mode": "full_diff",
    "population": 14,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productAttribute.productTmplIds": 9
  },
  "productAttributeValue": {
    "mode": "full_diff",
    "population": 101,
    "duplicate_source_key_count": 0
  },
  "updateProductAttributeValue": {
    "mode": "full_diff",
    "population": 0,
    "duplicate_source_key_count": 0
  }
}
```
