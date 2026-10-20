# Recon report: unit `account-chart`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `accountAccount`, `accountAccountTag`, `accountFiscalPosition`, `accountTax`, `accountTaxGroup`, `accountTaxRepartitionLine`
- Seed: `0`
- Generated: 2026-10-20T15:01:46.023457+00:00
- 90 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 31 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 62 | PASS |
| 2 | per_field_aggregates | 52 | PASS |
| 3 | keyed_diffs | 997 | PASS |
| 4 | app_level_parity | 6 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountAccount": 184,
    "accountAccountTag": 10,
    "accountFiscalPosition": 4,
    "accountTax": 58,
    "accountTaxGroup": 26,
    "accountTaxRepartitionLine": 232
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
    "accountTaxRepartitionLine.writeDate"
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
      "field": "accountFiscalPosition.name",
      "key": "accountFiscalPosition"
    },
    {
      "field": "accountFiscalPosition.note",
      "key": "accountFiscalPosition"
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
    }
  ],
  "fields_fully_deferred": 46
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
    "accountAccount.taxDefaultRel": 1,
    "accountAccountTag.accountMoveLineRel": 1,
    "accountAccountTag.accountTaxRepartitionLineRel": 1,
    "accountAccountTag.productTemplateRel": 1,
    "accountFiscalPosition.account": 1,
    "accountFiscalPosition.resCountryStateRel": 2,
    "accountFiscalPosition.accountTaxRel": 50,
    "accountTax.alternatives": 2,
    "accountTax.filiationRel": 2,
    "accountTax.purchaseOrderLineRel": 31,
    "accountTax.saleOrderLineRel": 50,
    "accountTax.productSupplierTaxesRel": 72,
    "accountTax.productTaxesRel": 72
  },
  "accountAccountTag": {
    "mode": "full_diff",
    "population": 10,
    "duplicate_source_key_count": 0
  },
  "accountFiscalPosition": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
  },
  "accountTax": {
    "mode": "full_diff",
    "population": 58,
    "duplicate_source_key_count": 0
  },
  "accountTaxGroup": {
    "mode": "full_diff",
    "population": 26,
    "duplicate_source_key_count": 0
  },
  "accountTaxRepartitionLine": {
    "mode": "full_diff",
    "population": 232,
    "duplicate_source_key_count": 0
  }
}
```
