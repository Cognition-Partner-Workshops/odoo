# Recon report: unit `accountCashRounding`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `79986d18a0e5`
- Collections: `accountCashRounding`
- Seed: `1`
- Generated: 2026-10-26T04:50:00.426772+00:00
- 11 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 5 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 9 | PASS |
| 2 | per_field_aggregates | 7 | PASS |
| 3 | keyed_diffs | 7 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountCashRounding": 2
  },
  "embed_source_counts": {
    "accountCashRounding.resCurrencyRel": 1,
    "accountCashRounding.resPartnerCategoryRel": 2,
    "accountCashRounding.accountPaymentMethodLineRel": 2
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountCashRounding.companyId",
    "accountCashRounding.createUid",
    "accountCashRounding.writeUid",
    "accountCashRounding.roundingMethod",
    "accountCashRounding.strategy",
    "accountCashRounding.name",
    "accountCashRounding.profitAccountId",
    "accountCashRounding.lossAccountId",
    "accountCashRounding.active",
    "accountCashRounding.createDate",
    "accountCashRounding.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountCashRounding.roundingMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountCashRounding.strategy",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountCashRounding.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountCashRounding.profitAccountId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountCashRounding.lossAccountId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountCashRounding.name",
      "key": "accountCashRounding"
    },
    {
      "field": "accountCashRounding.profitAccountId",
      "key": "accountCashRounding"
    },
    {
      "field": "accountCashRounding.lossAccountId",
      "key": "accountCashRounding"
    }
  ],
  "fields_fully_deferred": 6
}
```

## Tier 3 coverage
```json
{
  "accountCashRounding": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountCashRounding.resCurrencyRel": 1,
    "accountCashRounding.resPartnerCategoryRel": 2,
    "accountCashRounding.accountPaymentMethodLineRel": 2
  }
}
```
