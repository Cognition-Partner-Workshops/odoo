# Recon report: unit `accountReport`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `485e5b5e1a8c` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `2dd43185d9e2`
- Collections: `accountReport`
- Seed: `1`
- Generated: 2026-10-26T04:11:48.774594+00:00
- 39 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 13 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 6 | PASS |
| 2 | per_field_aggregates | 7 | PASS |
| 3 | keyed_diffs | 17 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountReport": 7
  },
  "embed_source_counts": {
    "accountReport.column": 8,
    "accountReport.sectionRel": 2
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountReport.sequence",
    "accountReport.rootReportId",
    "accountReport.countryId",
    "accountReport.loadMoreLimit",
    "accountReport.createUid",
    "accountReport.writeUid",
    "accountReport.groupby",
    "accountReport.userGroupby",
    "accountReport.chartTemplate",
    "accountReport.availabilityCondition",
    "accountReport.integerRounding",
    "accountReport.defaultOpeningDateFilter",
    "accountReport.currencyTranslation",
    "accountReport.filterMultiCompany",
    "accountReport.filterHide0Lines",
    "accountReport.filterHierarchy",
    "accountReport.filterAccountType",
    "accountReport.name",
    "accountReport.activeSelection",
    "accountReport.activeFallback",
    "accountReport.useSections",
    "accountReport.onlyTaxExigible",
    "accountReport.searchBar",
    "accountReport.allowForeignVat",
    "accountReport.useFiscalPeriods",
    "accountReport.enableSnapshots",
    "accountReport.filterDateRange",
    "accountReport.filterShowDraft",
    "accountReport.filterUnreconciled",
    "accountReport.filterUnfoldAll",
    "accountReport.filterPeriodComparison",
    "accountReport.filterGrowthComparison",
    "accountReport.filterLineComparison",
    "accountReport.filterJournals",
    "accountReport.filterPartner",
    "accountReport.filterAmlIrFilters",
    "accountReport.filterBudgets",
    "accountReport.createDate",
    "accountReport.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountReport.groupby",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.userGroupby",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.chartTemplate",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.availabilityCondition",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.integerRounding",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.defaultOpeningDateFilter",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.currencyTranslation",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.filterMultiCompany",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.filterHide0Lines",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.filterHierarchy",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.filterAccountType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReport.activeSelection",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountReport.name",
      "key": "accountReport"
    },
    {
      "field": "accountReport.activeSelection",
      "key": "accountReport"
    }
  ],
  "fields_fully_deferred": 32
}
```

## Tier 3 coverage
```json
{
  "accountReport": {
    "mode": "full_diff",
    "population": 7,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountReport.column": 8,
    "accountReport.sectionRel": 2
  }
}
```
