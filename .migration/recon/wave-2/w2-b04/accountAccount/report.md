# Recon report: unit `accountAccount`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `d1c02f78cef7`
- Collections: `accountAccount`
- Seed: `1`
- Generated: 2026-10-26T04:51:07.792458+00:00
- 17 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 6 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 15 | PASS |
| 2 | per_field_aggregates | 8 | PASS |
| 3 | keyed_diffs | 461 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountAccount": 213
  },
  "embed_source_counts": {
    "accountAccount.resCompanyRel": 213,
    "accountAccount.accountTag": 34,
    "accountAccount.taxDefaultRel": 1
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountAccount.currencyId",
    "accountAccount.parentId",
    "accountAccount.accountStockVariationId",
    "accountAccount.accountStockExpenseId",
    "accountAccount.createUid",
    "accountAccount.writeUid",
    "accountAccount.accountType",
    "accountAccount.parentPath",
    "accountAccount.name",
    "accountAccount.description",
    "accountAccount.codeStore",
    "accountAccount.note",
    "accountAccount.active",
    "accountAccount.reconcile",
    "accountAccount.nonTrade",
    "accountAccount.createDate",
    "accountAccount.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountAccount.accountType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountAccount.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountAccount.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountAccount.description",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountAccount.codeStore",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountAccount.note",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountAccount.name",
      "key": "accountAccount"
    },
    {
      "field": "accountAccount.description",
      "key": "accountAccount"
    },
    {
      "field": "accountAccount.codeStore",
      "key": "accountAccount"
    }
  ],
  "fields_fully_deferred": 9
}
```

## Tier 3 coverage
```json
{
  "accountAccount": {
    "mode": "full_diff",
    "population": 213,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountAccount.resCompanyRel": 213,
    "accountAccount.accountTag": 34,
    "accountAccount.taxDefaultRel": 1
  }
}
```
