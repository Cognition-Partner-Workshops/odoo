# Recon report: unit `productRemoval`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `3b75e4814e52`
- Collections: `productRemoval`
- Seed: `1`
- Generated: 2026-10-26T04:49:45.976699+00:00
- 6 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 2 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 4 | PASS |
| 3 | keyed_diffs | 4 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productRemoval": 4
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productRemoval.createUid",
    "productRemoval.writeUid",
    "productRemoval.name",
    "productRemoval.method",
    "productRemoval.createDate",
    "productRemoval.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productRemoval.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productRemoval.method",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productRemoval.name",
      "key": "productRemoval"
    },
    {
      "field": "productRemoval.method",
      "key": "productRemoval"
    }
  ],
  "fields_fully_deferred": 2
}
```

## Tier 3 coverage
```json
{
  "productRemoval": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
  }
}
```
