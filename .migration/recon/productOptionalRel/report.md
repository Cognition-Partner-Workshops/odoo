# Recon report: unit `productOptionalRel`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `6a05b487b518` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `4d11004a06fc`
- Collections: `productOptionalRel`
- Seed: `0`
- Generated: 2026-10-26T08:12:47.766868+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 3 | PASS |
| 2 | per_field_aggregates | 0 | PASS |
| 3 | keyed_diffs | 3 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productOptionalRel": 3
  },
  "embed_source_counts": {}
}
```

## Tier 3 coverage
```json
{
  "productOptionalRel": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  }
}
```
