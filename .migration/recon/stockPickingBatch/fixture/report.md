# Recon report: unit `stockPickingBatch`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `f84dbc723f61` (dirty) | source db `odoo_fixture` | source server `none` | ops sha256 `1727c1d313a6`
- Collections: `stockPickingBatch`
- Seed: `0`
- Generated: 2026-10-26T16:34:35.212525+00:00
- 13 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 5 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 7 | PASS |
| 3 | keyed_diffs | 2 | PASS |
| 4 | app_level_parity | 1 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockPickingBatch": 2
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "stockPickingBatch.userId",
    "stockPickingBatch.pickingTypeId",
    "stockPickingBatch.createUid",
    "stockPickingBatch.writeUid",
    "stockPickingBatch.name",
    "stockPickingBatch.description",
    "stockPickingBatch.state",
    "stockPickingBatch.priority",
    "stockPickingBatch.properties",
    "stockPickingBatch.isWave",
    "stockPickingBatch.scheduledDate",
    "stockPickingBatch.createDate",
    "stockPickingBatch.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "stockPickingBatch.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingBatch.description",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingBatch.state",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingBatch.priority",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingBatch.properties",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "stockPickingBatch.properties",
      "key": "stockPickingBatch"
    }
  ],
  "fields_fully_deferred": 7
}
```

## Tier 3 coverage
```json
{
  "stockPickingBatch": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  }
}
```
