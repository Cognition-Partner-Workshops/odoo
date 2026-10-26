# Recon report: unit `accountLockException`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `6047909ee628` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `3b14eadcf4e7`
- Collections: `accountLockException`
- Seed: `0`
- Generated: 2026-10-26T02:16:34.696457+00:00
- 11 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 2 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 5 | PASS |
| 2 | per_field_aggregates | 5 | PASS |
| 3 | keyed_diffs | 1 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountLockException": 1
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountLockException.userId",
    "accountLockException.createUid",
    "accountLockException.writeUid",
    "accountLockException.reason",
    "accountLockException.lockDateField",
    "accountLockException.lockDate",
    "accountLockException.companyLockDate",
    "accountLockException.active",
    "accountLockException.endDatetime",
    "accountLockException.createDate",
    "accountLockException.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountLockException.reason",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountLockException.lockDateField",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "fields_fully_deferred": 7
}
```

## Tier 3 coverage
```json
{
  "accountLockException": {
    "mode": "full_diff",
    "population": 1,
    "duplicate_source_key_count": 0
  }
}
```
