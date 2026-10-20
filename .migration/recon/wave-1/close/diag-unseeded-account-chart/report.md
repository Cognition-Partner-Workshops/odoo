# Recon report: unit `wave-1-close-diag`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `accountAccount`, `accountAccountTag`, `accountCashRounding`, `accountFiscalPosition`, `accountIncoterms`, `accountJournalGroup`, `accountLockException`, `accountPaymentTerm`, `accountReport`, `accountReportExpression`, `accountReportExternalValue`, `accountTax`, `accountTaxGroup`, `accountTaxRepartitionLine`, `productAttribute`, `productBaseUnit`, `productCategory`, `productDocument`, `productRemoval`, `productTag`, `returnReason`, `stockPackageType`, `stockScrapReasonTag`, `stockStorageCategory`, `uomUom`
- Seed: `0`
- Generated: 2026-10-20T19:45:31.760762+00:00
- 306 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 101 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 141 | PASS |
| 2 | per_field_aggregates | 164 | PASS |
| 3 | keyed_diffs | 1251 | PASS |
| 4 | app_level_parity | 28 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountAccount": 184,
    "accountAccountTag": 8,
    "accountCashRounding": 2,
    "accountFiscalPosition": 4,
    "accountIncoterms": 11,
    "accountJournalGroup": 2,
    "accountLockException": 1,
    "accountPaymentTerm": 11,
    "accountReport": 5,
    "accountReportExpression": 3,
    "accountReportExternalValue": 1,
    "accountTax": 57,
    "accountTaxGroup": 26,
    "accountTaxRepartitionLine": 228,
    "productAttribute": 14,
    "productBaseUnit": 2,
    "productCategory": 7,
    "productDocument": 2,
    "productRemoval": 4,
    "productTag": 3,
    "returnReason": 5,
    "stockPackageType": 3,
    "stockScrapReasonTag": 3,
    "stockStorageCategory": 6,
    "uomUom": 30
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
    "accountAccount.writeDate",
    "accountAccountTag.color",
    "accountAccountTag.countryId",
    "accountAccountTag.createUid",
    "accountAccountTag.writeUid",
    "accountAccountTag.applicability",
    "accountAccountTag.name",
    "accountAccountTag.active",
    "accountAccountTag.createDate",
    "accountAccountTag.writeDate",
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
    "accountFiscalPosition.sequence",
    "accountFiscalPosition.countryId",
    "accountFiscalPosition.countryGroupId",
    "accountFiscalPosition.createUid",
    "accountFiscalPosition.writeUid",
    "accountFiscalPosition.zipFrom",
    "accountFiscalPosition.zipTo",
    "accountFiscalPosition.foreignVat",
    "accountFiscalPosition.name",
    "accountFiscalPosition.note",
    "accountFiscalPosition.active",
    "accountFiscalPosition.autoApply",
    "accountFiscalPosition.vatRequired",
    "accountFiscalPosition.isDomestic",
    "accountFiscalPosition.createDate",
    "accountFiscalPosition.writeDate",
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
    "accountReportExternalValue.value",
    "accountTax.cashBasisTransitionAccountId",
    "accountTax.createUid",
    "accountTax.writeUid",
    "accountTax.typeTaxUse",
    "accountTax.taxScope",
    "accountTax.amountType",
    "accountTax.priceIncludeOverride",
    "accountTax.taxExigibility",
    "accountTax.name",
    "accountTax.description",
    "accountTax.invoiceLabel",
    "accountTax.invoiceLegalNotes",
    "accountTax.isDomestic",
    "accountTax.active",
    "accountTax.includeBaseAmount",
    "accountTax.isBaseAffected",
    "accountTax.analytic",
    "accountTax.createDate",
    "accountTax.writeDate",
    "accountTax.ublCiiTaxCategoryCode",
    "accountTax.ublCiiTaxExemptionReason",
    "accountTax.ublCiiTaxExemptionReasonCode",
    "accountTax.l10nUsStateId",
    "accountTax.l10nUsCountyId",
    "accountTax.l10nUsCityId",
    "accountTax.l10nUsExemptParentTaxId",
    "accountTax.l10nUsNontaxableParentTaxId",
    "accountTax.l10nUsJurisdictionType",
    "accountTaxGroup.sequence",
    "accountTaxGroup.countryId",
    "accountTaxGroup.createUid",
    "accountTaxGroup.writeUid",
    "accountTaxGroup.posReceiptLabel",
    "accountTaxGroup.name",
    "accountTaxGroup.precedingSubtotal",
    "accountTaxGroup.createDate",
    "accountTaxGroup.writeDate",
    "accountTaxRepartitionLine.accountId",
    "accountTaxRepartitionLine.taxId",
    "accountTaxRepartitionLine.companyId",
    "accountTaxRepartitionLine.sequence",
    "accountTaxRepartitionLine.createUid",
    "accountTaxRepartitionLine.writeUid",
    "accountTaxRepartitionLine.repartitionType",
    "accountTaxRepartitionLine.documentType",
    "accountTaxRepartitionLine.useInTaxClosing",
    "accountTaxRepartitionLine.createDate",
    "accountTaxRepartitionLine.writeDate",
    "productAttribute.sequence",
    "productAttribute.createUid",
    "productAttribute.writeUid",
    "productAttribute.createVariant",
    "productAttribute.displayType",
    "productAttribute.name",
    "productAttribute.active",
    "productAttribute.createDate",
    "productAttribute.writeDate",
    "productBaseUnit.createUid",
    "productBaseUnit.writeUid",
    "productBaseUnit.name",
    "productBaseUnit.createDate",
    "productBaseUnit.writeDate",
    "productCategory.parentId",
    "productCategory.companyId",
    "productCategory.createUid",
    "productCategory.writeUid",
    "productCategory.parentPath",
    "productCategory.name",
    "productCategory.productPropertiesDefinition",
    "productCategory.createDate",
    "productCategory.writeDate",
    "productCategory.propertyAccountIncomeCategId",
    "productCategory.propertyAccountExpenseCategId",
    "productCategory.propertyValuation",
    "productCategory.propertyStockValuationAccountId",
    "productCategory.propertyStockJournal",
    "productCategory.propertyCostMethod",
    "productCategory.propertyPriceDifferenceAccountId",
    "productCategory.removalStrategyId",
    "productCategory.packagingReserveMethod",
    "productCategory.propertyAccountBillsToReceiveId",
    "productCategory.propertyAccountBilledNotReceivedId",
    "productCategory.propertyAccountInvoicesToIssueId",
    "productCategory.propertyAccountInvoicedNotDeliveredId",
    "productDocument.sequence",
    "productDocument.createUid",
    "productDocument.writeUid",
    "productDocument.active",
    "productDocument.createDate",
    "productDocument.writeDate",
    "productDocument.attachedOnSale",
    "productRemoval.createUid",
    "productRemoval.writeUid",
    "productRemoval.name",
    "productRemoval.method",
    "productRemoval.createDate",
    "productRemoval.writeDate",
    "productTag.sequence",
    "productTag.createUid",
    "productTag.writeUid",
    "productTag.color",
    "productTag.name",
    "productTag.visibleToCustomers",
    "productTag.createDate",
    "productTag.writeDate",
    "returnReason.sequence",
    "returnReason.createUid",
    "returnReason.writeUid",
    "returnReason.name",
    "returnReason.createDate",
    "returnReason.writeDate",
    "stockPackageType.sequence",
    "stockPackageType.sequenceId",
    "stockPackageType.companyId",
    "stockPackageType.createUid",
    "stockPackageType.writeUid",
    "stockPackageType.name",
    "stockPackageType.barcode",
    "stockPackageType.packageUse",
    "stockPackageType.createDate",
    "stockPackageType.writeDate",
    "stockPackageType.height",
    "stockPackageType.width",
    "stockPackageType.packagingLength",
    "stockPackageType.baseWeight",
    "stockPackageType.maxWeight",
    "stockScrapReasonTag.sequence",
    "stockScrapReasonTag.color",
    "stockScrapReasonTag.createUid",
    "stockScrapReasonTag.writeUid",
    "stockScrapReasonTag.name",
    "stockScrapReasonTag.createDate",
    "stockScrapReasonTag.writeDate",
    "stockStorageCategory.companyId",
    "stockStorageCategory.createUid",
    "stockStorageCategory.writeUid",
    "stockStorageCategory.name",
    "stockStorageCategory.allowNewProduct",
    "stockStorageCategory.maxWeight",
    "stockStorageCategory.createDate",
    "stockStorageCategory.writeDate",
    "uomUom.sequence",
    "uomUom.relativeUomId",
    "uomUom.createUid",
    "uomUom.writeUid",
    "uomUom.parentPath",
    "uomUom.name",
    "uomUom.factor",
    "uomUom.active",
    "uomUom.createDate",
    "uomUom.writeDate",
    "uomUom.packageTypeId",
    "uomUom.uneceCode"
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
    },
    {
      "field": "accountAccountTag.applicability",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountAccountTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
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
      "field": "accountFiscalPosition.zipFrom",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.zipTo",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.foreignVat",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.note",
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
    },
    {
      "field": "accountTax.typeTaxUse",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.taxScope",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.amountType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.priceIncludeOverride",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.taxExigibility",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.description",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.invoiceLabel",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.invoiceLegalNotes",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.ublCiiTaxCategoryCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.ublCiiTaxExemptionReason",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.ublCiiTaxExemptionReasonCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTax.l10nUsJurisdictionType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTaxGroup.posReceiptLabel",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTaxGroup.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTaxGroup.precedingSubtotal",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTaxRepartitionLine.repartitionType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountTaxRepartitionLine.documentType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttribute.createVariant",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttribute.displayType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productAttribute.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productBaseUnit.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.productPropertiesDefinition",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountIncomeCategId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountExpenseCategId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyValuation",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyStockValuationAccountId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyStockJournal",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyCostMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyPriceDifferenceAccountId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.packagingReserveMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountBillsToReceiveId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountBilledNotReceivedId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountInvoicesToIssueId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productCategory.propertyAccountInvoicedNotDeliveredId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productDocument.attachedOnSale",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productRemoval.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productRemoval.method",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTag.color",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "returnReason.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPackageType.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPackageType.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPackageType.packageUse",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockScrapReasonTag.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockStorageCategory.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockStorageCategory.allowNewProduct",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "uomUom.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "uomUom.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "uomUom.uneceCode",
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
    },
    {
      "field": "accountAccountTag.name",
      "key": "accountAccountTag"
    },
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
      "field": "accountFiscalPosition.name",
      "key": "accountFiscalPosition"
    },
    {
      "field": "accountFiscalPosition.note",
      "key": "accountFiscalPosition"
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
    },
    {
      "field": "accountTax.name",
      "key": "accountTax"
    },
    {
      "field": "accountTax.description",
      "key": "accountTax"
    },
    {
      "field": "accountTax.invoiceLabel",
      "key": "accountTax"
    },
    {
      "field": "accountTax.invoiceLegalNotes",
      "key": "accountTax"
    },
    {
      "field": "accountTaxGroup.name",
      "key": "accountTaxGroup"
    },
    {
      "field": "accountTaxGroup.precedingSubtotal",
      "key": "accountTaxGroup"
    },
    {
      "field": "productAttribute.name",
      "key": "productAttribute"
    },
    {
      "field": "productBaseUnit.name",
      "key": "productBaseUnit"
    },
    {
      "field": "productCategory.name",
      "key": "productCategory"
    },
    {
      "field": "productCategory.productPropertiesDefinition",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountIncomeCategId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountExpenseCategId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyValuation",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyStockValuationAccountId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyStockJournal",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyCostMethod",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyPriceDifferenceAccountId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountBillsToReceiveId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountBilledNotReceivedId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountInvoicesToIssueId",
      "key": "productCategory"
    },
    {
      "field": "productCategory.propertyAccountInvoicedNotDeliveredId",
      "key": "productCategory"
    },
    {
      "field": "productRemoval.name",
      "key": "productRemoval"
    },
    {
      "field": "productRemoval.method",
      "key": "productRemoval"
    },
    {
      "field": "productTag.name",
      "key": "productTag"
    },
    {
      "field": "returnReason.name",
      "key": "returnReason"
    },
    {
      "field": "stockScrapReasonTag.name",
      "key": "stockScrapReasonTag"
    },
    {
      "field": "uomUom.name",
      "key": "uomUom"
    }
  ],
  "fields_fully_deferred": 159
}
```

## Tier 3 coverage
```json
{
  "accountAccount": {
    "mode": "full_diff",
    "population": 184,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountAccount.resCompanyRel": 184,
    "accountAccount.accountTag": 13,
    "accountAccount.taxDefaultRel": 0,
    "accountAccountTag.accountMoveLineRel": 0,
    "accountAccountTag.accountTaxRepartitionLineRel": 0,
    "accountAccountTag.productTemplateRel": 0,
    "accountCashRounding.resCurrencyRel": 1,
    "accountCashRounding.resPartnerCategoryRel": 3,
    "accountCashRounding.accountPaymentMethodLineRel": 3,
    "accountFiscalPosition.account": 0,
    "accountFiscalPosition.resCountryStateRel": 0,
    "accountFiscalPosition.accountTaxRel": 50,
    "accountPaymentTerm.line": 13,
    "accountReport.column": 8,
    "accountReport.line": 2,
    "accountReport.sectionRel": 2,
    "accountTax.alternatives": 2,
    "accountTax.filiationRel": 0,
    "accountTax.purchaseOrderLineRel": 31,
    "accountTax.saleOrderLineRel": 50,
    "accountTax.productSupplierTaxesRel": 72,
    "accountTax.productTaxesRel": 72,
    "productAttribute.productTemplateRel": 9,
    "productAttribute.value": 101,
    "productCategory.stockPickingTypeRel": 3,
    "productTag.productProductRel": 3,
    "productTag.productTemplateRel": 3,
    "stockPackageType.stockPutawayRuleRel": 2,
    "stockPackageType.stockRouteRel": 2
  },
  "accountAccountTag": {
    "mode": "full_diff",
    "population": 8,
    "duplicate_source_key_count": 0
  },
  "accountCashRounding": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "accountFiscalPosition": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
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
  },
  "accountTax": {
    "mode": "full_diff",
    "population": 57,
    "duplicate_source_key_count": 0
  },
  "accountTaxGroup": {
    "mode": "full_diff",
    "population": 26,
    "duplicate_source_key_count": 0
  },
  "accountTaxRepartitionLine": {
    "mode": "full_diff",
    "population": 228,
    "duplicate_source_key_count": 0
  },
  "productAttribute": {
    "mode": "full_diff",
    "population": 14,
    "duplicate_source_key_count": 0
  },
  "productBaseUnit": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "productCategory": {
    "mode": "full_diff",
    "population": 7,
    "duplicate_source_key_count": 0
  },
  "productDocument": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "productRemoval": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
  },
  "productTag": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "returnReason": {
    "mode": "full_diff",
    "population": 5,
    "duplicate_source_key_count": 0
  },
  "stockPackageType": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "stockScrapReasonTag": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "stockStorageCategory": {
    "mode": "full_diff",
    "population": 6,
    "duplicate_source_key_count": 0
  },
  "uomUom": {
    "mode": "full_diff",
    "population": 30,
    "duplicate_source_key_count": 0
  }
}
```
