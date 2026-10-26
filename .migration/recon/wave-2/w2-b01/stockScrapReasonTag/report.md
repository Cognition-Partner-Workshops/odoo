# Recon report: unit `stockScrapReasonTag`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `af21e9ea1eec`
- Collections: `stockScrapReasonTag`
- Seed: `1`
- Generated: 2026-10-26T04:49:41.817337+00:00
- 7 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 1 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 2 | PASS |
| 2 | per_field_aggregates | 5 | PASS |
| 3 | keyed_diffs | 3 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockScrapReasonTag": 3
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "stockScrapReasonTag.sequence",
    "stockScrapReasonTag.color",
    "stockScrapReasonTag.createUid",
    "stockScrapReasonTag.writeUid",
    "stockScrapReasonTag.name",
    "stockScrapReasonTag.createDate",
    "stockScrapReasonTag.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "stockScrapReasonTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "stockScrapReasonTag.name",
      "key": "stockScrapReasonTag"
    }
  ],
  "fields_fully_deferred": 2
}
```

## Tier 3 coverage
```json
{
  "stockScrapReasonTag": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  }
}
```
