# Recon report: unit `productBaseUnit`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `70cb5d4650d2` | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `268f8a6a9d1c`
- Collections: `productBaseUnit`
- Seed: `0`
- Generated: 2026-10-26T03:33:18.811249+00:00
- 5 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 1 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 3 | PASS |
| 3 | keyed_diffs | 2 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productBaseUnit": 2
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productBaseUnit.createUid",
    "productBaseUnit.writeUid",
    "productBaseUnit.name",
    "productBaseUnit.createDate",
    "productBaseUnit.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productBaseUnit.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productBaseUnit.name",
      "key": "productBaseUnit"
    }
  ],
  "fields_fully_deferred": 2
}
```

## Tier 3 coverage
```json
{
  "productBaseUnit": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  }
}
```
