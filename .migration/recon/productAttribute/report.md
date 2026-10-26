# Recon report: unit `productAttribute`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `8098a4187145` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `d97ad10689b8`
- Collections: `productAttribute`
- Seed: `0`
- Generated: 2026-10-26T04:25:05.667837+00:00
- 9 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 7 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 853 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productAttribute": 40
  },
  "embed_source_counts": {
    "productAttribute.productTemplateRel": 410,
    "productAttribute.value": 403
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productAttribute.sequence",
    "productAttribute.createUid",
    "productAttribute.writeUid",
    "productAttribute.createVariant",
    "productAttribute.displayType",
    "productAttribute.name",
    "productAttribute.active",
    "productAttribute.createDate",
    "productAttribute.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productAttribute.createVariant",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttribute.displayType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttribute.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productAttribute.name",
      "key": "productAttribute"
    }
  ],
  "fields_fully_deferred": 3
}
```

## Tier 3 coverage
```json
{
  "productAttribute": {
    "mode": "full_diff",
    "population": 40,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productAttribute.productTemplateRel": 410,
    "productAttribute.value": 403
  }
}
```
