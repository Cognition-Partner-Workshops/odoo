# Recon report: unit `stockPackageType`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `985ead020ca2`
- Collections: `stockPackageType`
- Seed: `1`
- Generated: 2026-10-26T04:50:07.022329+00:00
- 15 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 6 | PASS |
| 2 | per_field_aggregates | 12 | PASS |
| 3 | keyed_diffs | 7 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockPackageType": 3
  },
  "embed_source_counts": {
    "stockPackageType.stockPutawayRuleRel": 2,
    "stockPackageType.stockRouteRel": 2
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "stockPackageType.sequence",
    "stockPackageType.sequenceId",
    "stockPackageType.companyId",
    "stockPackageType.createUid",
    "stockPackageType.writeUid",
    "stockPackageType.name",
    "stockPackageType.barcode",
    "stockPackageType.packageUse",
    "stockPackageType.createDate",
    "stockPackageType.writeDate",
    "stockPackageType.height",
    "stockPackageType.width",
    "stockPackageType.packagingLength",
    "stockPackageType.baseWeight",
    "stockPackageType.maxWeight"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "stockPackageType.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPackageType.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPackageType.packageUse",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "fields_fully_deferred": 3
}
```

## Tier 3 coverage
```json
{
  "stockPackageType": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "stockPackageType.stockPutawayRuleRel": 2,
    "stockPackageType.stockRouteRel": 2
  }
}
```
