# Recon report: unit `uom-packaging`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `stockPackageType`, `uomUom`
- Seed: `0`
- Generated: 2026-10-20T18:07:10.933975+00:00
- 27 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 6 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 11 | PASS |
| 2 | per_field_aggregates | 20 | PASS |
| 3 | keyed_diffs | 37 | PASS |
| 4 | app_level_parity | 4 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockPackageType": 3,
    "uomUom": 30
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
    "stockPackageType.maxWeight",
    "uomUom.sequence",
    "uomUom.relativeUomId",
    "uomUom.createUid",
    "uomUom.writeUid",
    "uomUom.parentPath",
    "uomUom.name",
    "uomUom.factor",
    "uomUom.active",
    "uomUom.createDate",
    "uomUom.writeDate",
    "uomUom.packageTypeId",
    "uomUom.uneceCode"
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
    },
    {
      "field": "uomUom.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "uomUom.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "uomUom.uneceCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "uomUom.name",
      "key": "uomUom"
    }
  ],
  "fields_fully_deferred": 8
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
  },
  "uomUom": {
    "mode": "full_diff",
    "population": 30,
    "duplicate_source_key_count": 0
  }
}
```
