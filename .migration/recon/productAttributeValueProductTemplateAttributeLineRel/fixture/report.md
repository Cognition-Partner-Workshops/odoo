# Recon report: unit `productAttributeValueProductTemplateAttributeLineRel`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `24ec4b56d6cb` | source db `odoo_fixture` | source server `none` | ops sha256 `dff99825de17`
- Collections: `productAttributeValueProductTemplateAttributeLineRel`
- Seed: `0`
- Generated: 2026-10-26T04:07:36.847939+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 0 | PASS |
| 3 | keyed_diffs | 1642 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productAttributeValueProductTemplateAttributeLineRel": 1642
  },
  "embed_source_counts": {}
}
```

## Tier 3 coverage
```json
{
  "productAttributeValueProductTemplateAttributeLineRel": {
    "mode": "full_diff",
    "population": 1642,
    "duplicate_source_key_count": 0
  }
}
```
