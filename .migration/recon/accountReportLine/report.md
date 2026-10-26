# Recon report: unit `accountReportLine`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `3eb5cde3c663` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `006399b022bc`
- Collections: `accountReportLine`
- Seed: `0`
- Generated: 2026-10-26T05:50:32.304978+00:00
- 15 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 6 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 4 | PASS |
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
