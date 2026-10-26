# Recon report: unit `accountAccount`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `7e53e0a39694` | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `0a11e985e456`
- Collections: `accountAccount`
- Seed: `1`
- Generated: 2026-10-26T03:47:08.536061+00:00
- 17 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 6 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 4 | PASS |
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
