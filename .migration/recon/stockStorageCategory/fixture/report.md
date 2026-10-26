# Recon report: unit `stockStorageCategory`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `2f68f2104eda` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `6dc0598094ca`
- Collections: `stockStorageCategory`
- Seed: `1`
- Generated: 2026-10-26T03:33:13.843678+00:00
- 8 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 2 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 6 | PASS |
| 4 | app_level_parity | 1 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockStorageCategory": 6
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
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
  "fields_fully_deferred": 2
}
```

## Tier 3 coverage
```json
{
  "stockStorageCategory": {
    "mode": "full_diff",
    "population": 6,
    "duplicate_source_key_count": 0
  }
}
```
