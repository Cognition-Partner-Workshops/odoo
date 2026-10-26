# Recon report: unit `saleOrderLineStockRouteRel`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `9932d353c286`
- Collections: `saleOrderLineStockRouteRel`
- Seed: `0`
- Generated: 2026-10-26T05:30:39.880252+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 0 | PASS |
| 3 | keyed_diffs | 1 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "saleOrderLineStockRouteRel": 1
  },
  "embed_source_counts": {}
}
```

## Tier 3 coverage
```json
{
  "saleOrderLineStockRouteRel": {
    "mode": "full_diff",
    "population": 1,
    "duplicate_source_key_count": 0
  }
}
```
