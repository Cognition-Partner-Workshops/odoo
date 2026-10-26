# Recon report: unit `accountTax`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `574e7d597871`
- Collections: `accountTax`
- Seed: `0`
- Generated: 2026-10-26T05:31:13.286224+00:00
- 28 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 13 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 8 | PASS |
| 2 | per_field_aggregates | 16 | PASS |
| 3 | keyed_diffs | 2574 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountTax": 65
  },
  "embed_source_counts": {
    "accountTax.alternatives": 2,
    "accountTax.filiationRel": 5,
    "accountTax.purchaseOrderLineRel": 35,
    "accountTax.repartitionLine": 260,
    "accountTax.saleOrderLineRel": 455,
    "accountTax.productSupplierTaxesRel": 876,
    "accountTax.productTaxesRel": 876
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
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
    "accountTax.l10nUsJurisdictionType"
  ],
  "string_aggregates_deferred_to_tier3": [
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
    }
  ],
  "document_aggregates_deferred_to_tier3": [
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
    }
  ],
  "fields_fully_deferred": 17
}
```

## Tier 3 coverage
```json
{
  "accountTax": {
    "mode": "full_diff",
    "population": 65,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountTax.alternatives": 2,
    "accountTax.filiationRel": 5,
    "accountTax.purchaseOrderLineRel": 35,
    "accountTax.repartitionLine": 260,
    "accountTax.saleOrderLineRel": 455,
    "accountTax.productSupplierTaxesRel": 876,
    "accountTax.productTaxesRel": 876
  }
}
```
