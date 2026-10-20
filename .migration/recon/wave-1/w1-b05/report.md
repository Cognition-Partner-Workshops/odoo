# Recon report: unit `product-attributes`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `productAttribute`
- Seed: `0`
- Generated: 2026-10-20T18:36:54.185639+00:00
- 9 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 6 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 124 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productAttribute": 14
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
    "productAttribute.writeDate"
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
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productAttribute.name",
      "key": "productAttribute"
    }
  ],
  "fields_fully_deferred": 3
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
    "productAttribute.productTemplateRel": 9,
    "productAttribute.value": 101
  }
}
```
