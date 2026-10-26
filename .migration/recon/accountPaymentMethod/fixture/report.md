# Recon report: unit `accountPaymentMethod`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `f84dbc723f61` (dirty) | source db `odoo_fixture` | source server `none` | ops sha256 `ceaaba87c790`
- Collections: `accountPaymentMethod`
- Seed: `0`
- Generated: 2026-10-26T16:32:54.216711+00:00
- 7 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 2 | PASS |
| 2 | per_field_aggregates | 5 | PASS |
| 3 | keyed_diffs | 16 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountPaymentMethod": 2
  },
  "embed_source_counts": {
    "accountPaymentMethod.line": 14
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountPaymentMethod.createUid",
    "accountPaymentMethod.writeUid",
    "accountPaymentMethod.code",
    "accountPaymentMethod.paymentType",
    "accountPaymentMethod.name",
    "accountPaymentMethod.createDate",
    "accountPaymentMethod.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountPaymentMethod.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountPaymentMethod.paymentType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountPaymentMethod.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountPaymentMethod.name",
      "key": "accountPaymentMethod"
    }
  ],
  "fields_fully_deferred": 2
}
```

## Tier 3 coverage
```json
{
  "accountPaymentMethod": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountPaymentMethod.line": 14
  }
}
```
