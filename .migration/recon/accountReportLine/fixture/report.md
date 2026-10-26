# Recon report: unit `accountReportLine`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `006399b022bc`
- Collections: `accountReportLine`
- Seed: `0`
- Generated: 2026-10-26T05:30:08.941231+00:00
- 15 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 6 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 8 | PASS |
| 3 | keyed_diffs | 2 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountReportLine": 2
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountReportLine.parentId",
    "accountReportLine.sequence",
    "accountReportLine.actionId",
    "accountReportLine.createUid",
    "accountReportLine.writeUid",
    "accountReportLine.groupby",
    "accountReportLine.userGroupby",
    "accountReportLine.code",
    "accountReportLine.foldability",
    "accountReportLine.horizontalSplitSide",
    "accountReportLine.name",
    "accountReportLine.printOnNewPage",
    "accountReportLine.hideIfZero",
    "accountReportLine.createDate",
    "accountReportLine.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountReportLine.groupby",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportLine.userGroupby",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportLine.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportLine.foldability",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportLine.horizontalSplitSide",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportLine.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountReportLine.name",
      "key": "accountReportLine"
    }
  ],
  "fields_fully_deferred": 9
}
```

## Tier 3 coverage
```json
{
  "accountReportLine": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  }
}
```
