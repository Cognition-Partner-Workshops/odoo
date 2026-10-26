# Recon report: unit `productRemoval`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `70cb5d4650d2` | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `68bd5e0f79a9`
- Collections: `productRemoval`
- Seed: `0`
- Generated: 2026-10-26T03:33:27.320706+00:00
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
