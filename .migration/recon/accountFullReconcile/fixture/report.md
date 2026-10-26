# Recon report: unit `accountFullReconcile`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `7e53e0a39694` | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `288bc9e21d6a`
- Collections: `accountFullReconcile`
- Seed: `1`
- Generated: 2026-10-26T03:46:59.686113+00:00
- 4 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 2 | PASS |
| 3 | keyed_diffs | 42 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountFullReconcile": 42
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountFullReconcile.createUid",
    "accountFullReconcile.writeUid",
    "accountFullReconcile.createDate",
    "accountFullReconcile.writeDate"
  ],
  "fields_fully_deferred": 2
}
```

## Tier 3 coverage
```json
{
  "accountFullReconcile": {
    "mode": "full_diff",
    "population": 42,
    "duplicate_source_key_count": 0
  }
}
```
