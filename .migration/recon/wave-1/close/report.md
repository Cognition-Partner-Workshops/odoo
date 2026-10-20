# Recon report: unit `wave-1-close`

- **Verdict: FAIL** (values redacted)
- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `accountAccount`, `accountAccountTag`, `accountCashRounding`, `accountFiscalPosition`, `accountIncoterms`, `accountJournalGroup`, `accountLockException`, `accountPaymentTerm`, `accountReport`, `accountReportExpression`, `accountReportExternalValue`, `accountTax`, `accountTaxGroup`, `accountTaxRepartitionLine`, `productAttribute`, `productBaseUnit`, `productCategory`, `productDocument`, `productRemoval`, `productTag`, `returnReason`, `stockPackageType`, `stockScrapReasonTag`, `stockStorageCategory`, `uomUom`
- Seed: `0`
- Generated: 2026-10-20T19:42:07.749708+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 141 | FAIL (10 findings) |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountAccount": 184,
    "accountAccountTag": 10,
    "accountCashRounding": 2,
    "accountFiscalPosition": 4,
    "accountIncoterms": 11,
    "accountJournalGroup": 2,
    "accountLockException": 1,
    "accountPaymentTerm": 11,
    "accountReport": 5,
    "accountReportExpression": 3,
    "accountReportExternalValue": 1,
    "accountTax": 58,
    "accountTaxGroup": 26,
    "accountTaxRepartitionLine": 232,
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

## Tier 1 findings (10)
- `accountAccount` embed_cardinality: rows(account_account_tax_default_rel)=1 vs sum(len(taxDefaultRel))=0
- `accountAccountTag` root_count: rows(account_account_tag)=10 vs docs=8
- `accountAccountTag` embed_cardinality: rows(account_account_tag_account_move_line_rel)=1 vs sum(len(accountMoveLineRel))=0
- `accountAccountTag` embed_cardinality: rows(account_account_tag_account_tax_repartition_line_rel)=1 vs sum(len(accountTaxRepartitionLineRel))=0
- `accountAccountTag` embed_cardinality: rows(account_account_tag_product_template_rel)=1 vs sum(len(productTemplateRel))=0
- `accountFiscalPosition` embed_cardinality: rows(account_fiscal_position_account)=1 vs sum(len(account))=0
- `accountFiscalPosition` embed_cardinality: rows(account_fiscal_position_res_country_state_rel)=2 vs sum(len(resCountryStateRel))=0
- `accountTax` root_count: rows(account_tax)=58 vs docs=57
- `accountTax` embed_cardinality: rows(account_tax_filiation_rel)=2 vs sum(len(filiationRel))=0
- `accountTaxRepartitionLine` root_count: rows(account_tax_repartition_line)=232 vs docs=228
