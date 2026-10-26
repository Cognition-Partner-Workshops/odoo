# Recon report: unit `accountReconcileModelLineAccountTaxRel`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `743e75613640` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `c16adfcb675a`
- Collections: `accountReconcileModelLineAccountTaxRel`
- Seed: `0`
- Generated: 2026-10-26T06:03:34.919706+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 3 | PASS |
| 2 | per_field_aggregates | 0 | PASS |
| 3 | keyed_diffs | 1 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountReconcileModelLineAccountTaxRel": 1
  },
  "embed_source_counts": {}
}
```

## Tier 3 coverage
```json
{
  "accountReconcileModelLineAccountTaxRel": {
    "mode": "full_diff",
    "population": 1,
    "duplicate_source_key_count": 0
  }
}
```
