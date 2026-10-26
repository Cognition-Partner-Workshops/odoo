# Recon report: unit `accountFullReconcile`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `1897642d89d2`
- Collections: `accountFullReconcile`
- Seed: `1`
- Generated: 2026-10-26T04:50:55.785449+00:00
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
