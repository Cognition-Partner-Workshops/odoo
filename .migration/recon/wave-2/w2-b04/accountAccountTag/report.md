# Recon report: unit `accountAccountTag`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `452f777327e6`
- Collections: `accountAccountTag`
- Seed: `1`
- Generated: 2026-10-26T04:51:00.642860+00:00
- 9 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 2 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 7 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 68 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountAccountTag": 15
  },
  "embed_source_counts": {
    "accountAccountTag.accountMoveLineRel": 51,
    "accountAccountTag.accountTaxRepartitionLineRel": 1,
    "accountAccountTag.productTemplateRel": 1
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountAccountTag.color",
    "accountAccountTag.countryId",
    "accountAccountTag.createUid",
    "accountAccountTag.writeUid",
    "accountAccountTag.applicability",
    "accountAccountTag.name",
    "accountAccountTag.active",
    "accountAccountTag.createDate",
    "accountAccountTag.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountAccountTag.applicability",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountAccountTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountAccountTag.name",
      "key": "accountAccountTag"
    }
  ],
  "fields_fully_deferred": 3
}
```

## Tier 3 coverage
```json
{
  "accountAccountTag": {
    "mode": "full_diff",
    "population": 15,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountAccountTag.accountMoveLineRel": 51,
    "accountAccountTag.accountTaxRepartitionLineRel": 1,
    "accountAccountTag.productTemplateRel": 1
  }
}
```
