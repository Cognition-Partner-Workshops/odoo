# Recon report: unit `accountPaymentTerm`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `953d4130cb4d`
- Collections: `accountPaymentTerm`
- Seed: `1`
- Generated: 2026-10-26T04:50:43.348770+00:00
- 13 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 4 | PASS |
| 2 | per_field_aggregates | 7 | PASS |
| 3 | keyed_diffs | 28 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountPaymentTerm": 13
  },
  "embed_source_counts": {
    "accountPaymentTerm.line": 15
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountPaymentTerm.companyId",
    "accountPaymentTerm.discountDays",
    "accountPaymentTerm.createUid",
    "accountPaymentTerm.writeUid",
    "accountPaymentTerm.earlyPayDiscountComputation",
    "accountPaymentTerm.name",
    "accountPaymentTerm.note",
    "accountPaymentTerm.active",
    "accountPaymentTerm.displayOnInvoice",
    "accountPaymentTerm.earlyDiscount",
    "accountPaymentTerm.createDate",
    "accountPaymentTerm.writeDate",
    "accountPaymentTerm.discountPercentage"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountPaymentTerm.earlyPayDiscountComputation",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountPaymentTerm.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountPaymentTerm.note",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountPaymentTerm.name",
      "key": "accountPaymentTerm"
    },
    {
      "field": "accountPaymentTerm.note",
      "key": "accountPaymentTerm"
    }
  ],
  "fields_fully_deferred": 7
}
```

## Tier 3 coverage
```json
{
  "accountPaymentTerm": {
    "mode": "full_diff",
    "population": 13,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountPaymentTerm.line": 15
  }
}
```
