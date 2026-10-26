# Recon report: unit `stockPackageType`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `2f68f2104eda` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `54a7a62b9aa5`
- Collections: `stockPackageType`
- Seed: `1`
- Generated: 2026-10-26T03:33:21.820051+00:00
- 15 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 3 | PASS |
| 2 | per_field_aggregates | 12 | PASS |
| 3 | keyed_diffs | 7 | PASS |
| 4 | app_level_parity | 1 | PASS |

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
