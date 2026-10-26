# Recon report: unit `stockScrapReasonTag`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `70cb5d4650d2` | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `124011c81a73`
- Collections: `stockScrapReasonTag`
- Seed: `0`
- Generated: 2026-10-26T03:33:24.547689+00:00
- 7 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 1 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
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
