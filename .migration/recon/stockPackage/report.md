# Recon report: unit `stockPackage`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `e8cd18976582` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `e5aa312f89a7`
- Collections: `stockPackage`
- Seed: `0`
- Generated: 2026-10-26T16:36:21.738569+00:00
- 14 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 9 | PASS |
| 2 | per_field_aggregates | 9 | PASS |
| 3 | keyed_diffs | 3 | PASS |
| 4 | app_level_parity | 1 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockPackage": 3
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "stockPackage.packageTypeId",
    "stockPackage.locationId",
    "stockPackage.companyId",
    "stockPackage.parentPackageId",
    "stockPackage.packageDestId",
    "stockPackage.createUid",
    "stockPackage.writeUid",
    "stockPackage.name",
    "stockPackage.completeName",
    "stockPackage.parentPath",
    "stockPackage.packDate",
    "stockPackage.createDate",
    "stockPackage.writeDate",
    "stockPackage.shippingWeight"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "stockPackage.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPackage.completeName",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPackage.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "fields_fully_deferred": 5
}
```

## Tier 3 coverage
```json
{
  "stockPackage": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  }
}
```
