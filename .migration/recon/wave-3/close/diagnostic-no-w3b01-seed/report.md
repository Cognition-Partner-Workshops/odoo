# Recon report: unit `wave-3-close-diag-no-w3b01-seed`

- **Verdict: FAIL** (values redacted)
- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `accountAccount`, `accountAccountTag`, `accountCashRounding`, `accountFiscalPosition`, `accountIncoterms`, `accountJournal`, `accountJournalGroup`, `accountLockException`, `accountPaymentMethod`, `accountPaymentTerm`, `accountReconcileModel`, `accountReconcileModelLineAccountTaxRel`, `accountReport`, `accountReportExpression`, `accountReportExternalValue`, `accountTax`, `accountTaxGroup`, `accountTaxRepartitionLine`, `productAttribute`, `productAttributeValueProductTemplateAttributeLineRel`, `productBaseUnit`, `productCategory`, `productCombo`, `productDocument`, `productPricelist`, `productPricelistItem`, `productProduct`, `productRemoval`, `productSupplierinfo`, `productTag`, `productTemplate`, `productTemplateAttributeValue`, `returnReason`, `stockPackageType`, `stockScrapReasonTag`, `stockStorageCategory`, `uomUom`
- Seed: `0`
- Generated: 2026-10-21T05:33:29.116522+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 260 | FAIL (1 findings) |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountAccount": 184,
    "accountAccountTag": 10,
    "accountCashRounding": 2,
    "accountFiscalPosition": 4,
    "accountIncoterms": 11,
    "accountJournal": 14,
    "accountJournalGroup": 2,
    "accountLockException": 1,
    "accountPaymentMethod": 2,
    "accountPaymentTerm": 11,
    "accountReconcileModel": 8,
    "accountReconcileModelLineAccountTaxRel": 1,
    "accountReport": 5,
    "accountReportExpression": 3,
    "accountReportExternalValue": 1,
    "accountTax": 58,
    "accountTaxGroup": 26,
    "accountTaxRepartitionLine": 232,
    "productAttribute": 14,
    "productAttributeValueProductTemplateAttributeLineRel": 24,
    "productBaseUnit": 2,
    "productCategory": 7,
    "productCombo": 3,
    "productDocument": 2,
    "productPricelist": 2,
    "productPricelistItem": 2,
    "productProduct": 47,
    "productRemoval": 4,
    "productSupplierinfo": 28,
    "productTag": 3,
    "productTemplate": 37,
    "productTemplateAttributeValue": 24,
    "returnReason": 5,
    "stockPackageType": 3,
    "stockScrapReasonTag": 3,
    "stockStorageCategory": 6,
    "uomUom": 30
  }
}
```

## Tier 1 findings (1)
- `stockPackageType` embed_cardinality: rows(stock_package_type_stock_putaway_rule_rel)=2 vs sum(len(stockPutawayRuleRel))=4
