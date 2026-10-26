# Recon report: unit `stockReference`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `24ec4b56d6cb` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `c326ab61859a`
- Collections: `stockReference`
- Seed: `0`
- Generated: 2026-10-26T04:11:27.632463+00:00
- 5 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 1 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 7 | PASS |
| 2 | per_field_aggregates | 3 | PASS |
| 3 | keyed_diffs | 524 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockReference": 121
  },
  "embed_source_counts": {
    "stockReference.moveRel": 281,
    "stockReference.purchaseRel": 8,
    "stockReference.saleRel": 114
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "stockReference.createUid",
    "stockReference.writeUid",
    "stockReference.name",
    "stockReference.createDate",
    "stockReference.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "stockReference.name",
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
  "stockReference": {
    "mode": "full_diff",
    "population": 121,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "stockReference.moveRel": 281,
    "stockReference.purchaseRel": 8,
    "stockReference.saleRel": 114
  }
}
```
