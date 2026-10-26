# Recon report: unit `productAttributeValueProductTemplateAttributeLineRel`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `24ec4b56d6cb` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `dff99825de17`
- Collections: `productAttributeValueProductTemplateAttributeLineRel`
- Seed: `0`
- Generated: 2026-10-26T04:11:33.308576+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 3 | PASS |
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
