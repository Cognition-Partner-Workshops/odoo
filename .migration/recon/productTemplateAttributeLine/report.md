# Recon report: unit `productTemplateAttributeLine`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `8368a2ac229b` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `22ef4e3e20cf`
- Collections: `productTemplateAttributeLine`
- Seed: `0`
- Generated: 2026-10-26T16:35:37.501244+00:00
- 7 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 8 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 2052 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productTemplateAttributeLine": 410
  },
  "embed_source_counts": {
    "productTemplateAttributeLine.productTemplateAttributeValue": 1642
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productTemplateAttributeLine.sequence",
    "productTemplateAttributeLine.valueCount",
    "productTemplateAttributeLine.createUid",
    "productTemplateAttributeLine.writeUid",
    "productTemplateAttributeLine.active",
    "productTemplateAttributeLine.createDate",
    "productTemplateAttributeLine.writeDate"
  ],
  "fields_fully_deferred": 3
}
```

## Tier 3 coverage
```json
{
  "productTemplateAttributeLine": {
    "mode": "full_diff",
    "population": 410,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productTemplateAttributeLine.productTemplateAttributeValue": 1642
  }
}
```
