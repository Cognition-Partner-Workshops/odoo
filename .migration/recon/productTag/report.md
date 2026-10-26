# Recon report: unit `productTag`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `8098a4187145` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `3c2cb729c906`
- Collections: `productTag`
- Seed: `0`
- Generated: 2026-10-26T04:24:59.115723+00:00
- 8 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 2 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 6 | PASS |
| 2 | per_field_aggregates | 4 | PASS |
| 3 | keyed_diffs | 487 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productTag": 10
  },
  "embed_source_counts": {
    "productTag.productProductRel": 1,
    "productTag.productTemplateRel": 476
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productTag.sequence",
    "productTag.createUid",
    "productTag.writeUid",
    "productTag.color",
    "productTag.name",
    "productTag.visibleToCustomers",
    "productTag.createDate",
    "productTag.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productTag.color",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productTag.name",
      "key": "productTag"
    }
  ],
  "fields_fully_deferred": 4
}
```

## Tier 3 coverage
```json
{
  "productTag": {
    "mode": "full_diff",
    "population": 10,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productTag.productProductRel": 1,
    "productTag.productTemplateRel": 476
  }
}
```
