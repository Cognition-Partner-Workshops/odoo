# Recon report: unit `accountIncoterms`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `485e5b5e1a8c` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `4cdaea958067`
- Collections: `accountIncoterms`
- Seed: `1`
- Generated: 2026-10-26T04:11:39.980973+00:00
- 7 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 2 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 2 | PASS |
| 2 | per_field_aggregates | 4 | PASS |
| 3 | keyed_diffs | 11 | PASS |
| 4 | app_level_parity | 1 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountIncoterms": 11
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountIncoterms.createUid",
    "accountIncoterms.writeUid",
    "accountIncoterms.code",
    "accountIncoterms.name",
    "accountIncoterms.active",
    "accountIncoterms.createDate",
    "accountIncoterms.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountIncoterms.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountIncoterms.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountIncoterms.name",
      "key": "accountIncoterms"
    }
  ],
  "fields_fully_deferred": 3
}
```

## Tier 3 coverage
```json
{
  "accountIncoterms": {
    "mode": "full_diff",
    "population": 11,
    "duplicate_source_key_count": 0
  }
}
```
