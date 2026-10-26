# Recon report: unit `accountReportExpression`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `00116db715cf` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `524730c4c1d8`
- Collections: `accountReportExpression`
- Seed: `0`
- Generated: 2026-10-26T17:40:59.709922+00:00
- 14 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 7 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 5 | PASS |
| 2 | per_field_aggregates | 7 | PASS |
| 3 | keyed_diffs | 4 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountReportExpression": 3
  },
  "embed_source_counts": {
    "accountReportExpression.accountReportExternalValue": 1
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountReportExpression.createUid",
    "accountReportExpression.writeUid",
    "accountReportExpression.label",
    "accountReportExpression.engine",
    "accountReportExpression.dateScope",
    "accountReportExpression.figureType",
    "accountReportExpression.carryoverTarget",
    "accountReportExpression.formula",
    "accountReportExpression.subformula",
    "accountReportExpression.greenOnPositive",
    "accountReportExpression.blankIfZero",
    "accountReportExpression.auditable",
    "accountReportExpression.createDate",
    "accountReportExpression.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountReportExpression.label",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExpression.engine",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExpression.dateScope",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExpression.figureType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExpression.carryoverTarget",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExpression.formula",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExpression.subformula",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "fields_fully_deferred": 8
}
```

## Tier 3 coverage
```json
{
  "accountReportExpression": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountReportExpression.accountReportExternalValue": 1
  }
}
```
