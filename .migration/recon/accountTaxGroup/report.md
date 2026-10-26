# Recon report: unit `accountTaxGroup`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `e987b78c3002` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `d12ee51d4821`
- Collections: `accountTaxGroup`
- Seed: `1`
- Generated: 2026-10-26T03:40:05.675145+00:00
- 9 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 3 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 27 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountTaxGroup": 27
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountTaxGroup.sequence",
    "accountTaxGroup.countryId",
    "accountTaxGroup.createUid",
    "accountTaxGroup.writeUid",
    "accountTaxGroup.posReceiptLabel",
    "accountTaxGroup.name",
    "accountTaxGroup.precedingSubtotal",
    "accountTaxGroup.createDate",
    "accountTaxGroup.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountTaxGroup.posReceiptLabel",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTaxGroup.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTaxGroup.precedingSubtotal",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountTaxGroup.name",
      "key": "accountTaxGroup"
    },
    {
      "field": "accountTaxGroup.precedingSubtotal",
      "key": "accountTaxGroup"
    }
  ],
  "fields_fully_deferred": 4
}
```

## Tier 3 coverage
```json
{
  "accountTaxGroup": {
    "mode": "full_diff",
    "population": 27,
    "duplicate_source_key_count": 0
  }
}
```
