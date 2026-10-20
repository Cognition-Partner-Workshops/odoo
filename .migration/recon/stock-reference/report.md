# Recon report: unit `stock-reference`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `returnReason`, `stockScrapReasonTag`, `stockStorageCategory`
- Seed: `0`
- Generated: 2026-10-20T13:26:23.464976+00:00
- 21 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 4 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 5 | PASS |
| 2 | per_field_aggregates | 15 | PASS |
| 3 | keyed_diffs | 14 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "returnReason": 5,
    "stockScrapReasonTag": 3,
    "stockStorageCategory": 6
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "returnReason.sequence",
    "returnReason.createUid",
    "returnReason.writeUid",
    "returnReason.name",
    "returnReason.createDate",
    "returnReason.writeDate",
    "stockScrapReasonTag.sequence",
    "stockScrapReasonTag.color",
    "stockScrapReasonTag.createUid",
    "stockScrapReasonTag.writeUid",
    "stockScrapReasonTag.name",
    "stockScrapReasonTag.createDate",
    "stockScrapReasonTag.writeDate",
    "stockStorageCategory.companyId",
    "stockStorageCategory.createUid",
    "stockStorageCategory.writeUid",
    "stockStorageCategory.name",
    "stockStorageCategory.allowNewProduct",
    "stockStorageCategory.maxWeight",
    "stockStorageCategory.createDate",
    "stockStorageCategory.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "returnReason.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockScrapReasonTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockStorageCategory.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockStorageCategory.allowNewProduct",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "returnReason.name",
      "key": "returnReason"
    },
    {
      "field": "stockScrapReasonTag.name",
      "key": "stockScrapReasonTag"
    }
  ],
  "fields_fully_deferred": 6
}
```

## Tier 3 coverage
```json
{
  "returnReason": {
    "mode": "full_diff",
    "population": 5,
    "duplicate_source_key_count": 0
  },
  "stockScrapReasonTag": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "stockStorageCategory": {
    "mode": "full_diff",
    "population": 6,
    "duplicate_source_key_count": 0
  }
}
```
