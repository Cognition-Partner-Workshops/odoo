# Recon report: unit `ormSignalingAssets`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Mapping version: `map-draft-3` (sha256 `f1f72a0107c0`)
- Tolerance version: `2` (sha256 `62d5a8ce4e40`)
- Evidence: git `4b9b33628874` | source db `odoo_src` | source server `hmac-sha256:0f95230fa7038f9e` | ops sha256 `aa4cfeb4017a`
- Collections: `ormSignalingAssets`
- Seed: `1`
- Generated: 2026-11-12T08:34:35.171443+00:00
- 1 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)

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
    "ormSignalingAssets": 1
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "ormSignalingAssets.date"
  ],
  "fields_fully_deferred": 1
}
```

## Tier 3 coverage
```json
{
  "ormSignalingAssets": {
    "mode": "full_diff",
    "population": 1,
    "duplicate_source_key_count": 0
  }
}
```
