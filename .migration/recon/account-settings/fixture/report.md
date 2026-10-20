# Recon report: unit `account-settings`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `accountCashRounding`, `accountIncoterms`, `accountJournalGroup`, `accountLockException`, `accountPaymentTerm`, `accountReport`, `accountReportExpression`, `accountReportExternalValue`
- Seed: `0`
- Generated: 2026-10-20T14:28:29.316345+00:00
- 111 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 36 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 15 | PASS |
| 2 | per_field_aggregates | 49 | PASS |
| 3 | keyed_diffs | 68 | PASS |
| 4 | app_level_parity | 5 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountCashRounding": 2,
    "accountIncoterms": 11,
    "accountJournalGroup": 2,
    "accountLockException": 1,
    "accountPaymentTerm": 11,
    "accountReport": 5,
    "accountReportExpression": 3,
    "accountReportExternalValue": 1
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
    "accountCashRounding.writeDate",
    "accountIncoterms.createUid",
    "accountIncoterms.writeUid",
    "accountIncoterms.code",
    "accountIncoterms.name",
    "accountIncoterms.active",
    "accountIncoterms.createDate",
    "accountIncoterms.writeDate",
    "accountJournalGroup.sequence",
    "accountJournalGroup.createUid",
    "accountJournalGroup.writeUid",
    "accountJournalGroup.name",
    "accountJournalGroup.createDate",
    "accountJournalGroup.writeDate",
    "accountLockException.userId",
    "accountLockException.createUid",
    "accountLockException.writeUid",
    "accountLockException.reason",
    "accountLockException.lockDateField",
    "accountLockException.lockDate",
    "accountLockException.companyLockDate",
    "accountLockException.active",
    "accountLockException.endDatetime",
    "accountLockException.createDate",
    "accountLockException.writeDate",
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
    "accountPaymentTerm.discountPercentage",
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
    "accountReport.writeDate",
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
    "accountReportExpression.writeDate",
    "accountReportExternalValue.carryoverOriginReportLineId",
    "accountReportExternalValue.createUid",
    "accountReportExternalValue.writeUid",
    "accountReportExternalValue.name",
    "accountReportExternalValue.textValue",
    "accountReportExternalValue.carryoverOriginExpressionLabel",
    "accountReportExternalValue.date",
    "accountReportExternalValue.createDate",
    "accountReportExternalValue.writeDate",
    "accountReportExternalValue.value"
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
    },
    {
      "field": "accountIncoterms.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountIncoterms.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournalGroup.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountLockException.reason",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountLockException.lockDateField",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
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
    },
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
    },
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
    },
    {
      "field": "accountReportExternalValue.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExternalValue.textValue",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReportExternalValue.carryoverOriginExpressionLabel",
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
    },
    {
      "field": "accountIncoterms.name",
      "key": "accountIncoterms"
    },
    {
      "field": "accountJournalGroup.name",
      "key": "accountJournalGroup"
    },
    {
      "field": "accountPaymentTerm.name",
      "key": "accountPaymentTerm"
    },
    {
      "field": "accountPaymentTerm.note",
      "key": "accountPaymentTerm"
    },
    {
      "field": "accountReport.name",
      "key": "accountReport"
    },
    {
      "field": "accountReport.activeSelection",
      "key": "accountReport"
    }
  ],
  "fields_fully_deferred": 69
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
    "accountCashRounding.resPartnerCategoryRel": 3,
    "accountCashRounding.accountPaymentMethodLineRel": 3,
    "accountPaymentTerm.line": 13,
    "accountReport.column": 8,
    "accountReport.line": 2,
    "accountReport.sectionRel": 2
  },
  "accountIncoterms": {
    "mode": "full_diff",
    "population": 11,
    "duplicate_source_key_count": 0
  },
  "accountJournalGroup": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "accountLockException": {
    "mode": "full_diff",
    "population": 1,
    "duplicate_source_key_count": 0
  },
  "accountPaymentTerm": {
    "mode": "full_diff",
    "population": 11,
    "duplicate_source_key_count": 0
  },
  "accountReport": {
    "mode": "full_diff",
    "population": 5,
    "duplicate_source_key_count": 0
  },
  "accountReportExpression": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "accountReportExternalValue": {
    "mode": "full_diff",
    "population": 1,
    "duplicate_source_key_count": 0
  }
}
```
