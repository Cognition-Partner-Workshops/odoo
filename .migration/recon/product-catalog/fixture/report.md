# Recon report: unit `product-catalog`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `productAttributeValueProductTemplateAttributeLineRel`, `productCombo`, `productPricelist`, `productPricelistItem`, `productProduct`, `productSupplierinfo`, `productTemplate`, `productTemplateAttributeValue`
- Seed: `0`
- Generated: 2026-10-20T22:04:44.511114+00:00
- 126 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 38 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 21 | PASS |
| 2 | per_field_aggregates | 78 | PASS |
| 3 | keyed_diffs | 220 | PASS |
| 4 | app_level_parity | 8 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productAttributeValueProductTemplateAttributeLineRel": 24,
    "productCombo": 3,
    "productPricelist": 2,
    "productPricelistItem": 2,
    "productProduct": 47,
    "productSupplierinfo": 28,
    "productTemplate": 37,
    "productTemplateAttributeValue": 24
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productCombo.sequence",
    "productCombo.companyId",
    "productCombo.createUid",
    "productCombo.writeUid",
    "productCombo.name",
    "productCombo.createDate",
    "productCombo.writeDate",
    "productPricelist.sequence",
    "productPricelist.companyId",
    "productPricelist.createUid",
    "productPricelist.writeUid",
    "productPricelist.name",
    "productPricelist.active",
    "productPricelist.createDate",
    "productPricelist.writeDate",
    "productPricelistItem.pricelistId",
    "productPricelistItem.companyId",
    "productPricelistItem.currencyId",
    "productPricelistItem.categId",
    "productPricelistItem.productTmplId",
    "productPricelistItem.productId",
    "productPricelistItem.uomId",
    "productPricelistItem.basePricelistId",
    "productPricelistItem.createUid",
    "productPricelistItem.writeUid",
    "productPricelistItem.appliedOn",
    "productPricelistItem.base",
    "productPricelistItem.computePrice",
    "productPricelistItem.minQuantity",
    "productPricelistItem.fixedPrice",
    "productPricelistItem.priceDiscount",
    "productPricelistItem.priceRound",
    "productPricelistItem.priceSurcharge",
    "productPricelistItem.priceMinMargin",
    "productPricelistItem.priceMaxMargin",
    "productPricelistItem.dateStart",
    "productPricelistItem.dateEnd",
    "productPricelistItem.createDate",
    "productPricelistItem.writeDate",
    "productProduct.baseUnitId",
    "productProduct.createUid",
    "productProduct.writeUid",
    "productProduct.defaultCode",
    "productProduct.barcode",
    "productProduct.combinationIndices",
    "productProduct.standardPrice",
    "productProduct.qtyAvailable",
    "productProduct.lstPrice",
    "productProduct.volume",
    "productProduct.weight",
    "productProduct.active",
    "productProduct.canImageVariant1024BeZoomed",
    "productProduct.isFavorite",
    "productProduct.writeDate",
    "productProduct.createDate",
    "productProduct.lotPropertiesDefinition",
    "productSupplierinfo.sequence",
    "productSupplierinfo.companyId",
    "productSupplierinfo.productId",
    "productSupplierinfo.createUid",
    "productSupplierinfo.writeUid",
    "productSupplierinfo.productName",
    "productSupplierinfo.productCode",
    "productSupplierinfo.dateStart",
    "productSupplierinfo.dateEnd",
    "productSupplierinfo.price",
    "productSupplierinfo.discount",
    "productSupplierinfo.createDate",
    "productSupplierinfo.writeDate",
    "productTemplate.sequence",
    "productTemplate.categId",
    "productTemplate.companyId",
    "productTemplate.color",
    "productTemplate.baseUnitId",
    "productTemplate.createUid",
    "productTemplate.writeUid",
    "productTemplate.type",
    "productTemplate.serviceTracking",
    "productTemplate.barcode",
    "productTemplate.defaultCode",
    "productTemplate.name",
    "productTemplate.description",
    "productTemplate.descriptionPurchase",
    "productTemplate.descriptionSale",
    "productTemplate.productProperties",
    "productTemplate.listPrice",
    "productTemplate.volume",
    "productTemplate.weight",
    "productTemplate.isStorable",
    "productTemplate.saleOk",
    "productTemplate.purchaseOk",
    "productTemplate.active",
    "productTemplate.canImage1024BeZoomed",
    "productTemplate.hasConfigurableAttributes",
    "productTemplate.isFavorite",
    "productTemplate.createDate",
    "productTemplate.writeDate",
    "productTemplate.propertyAccountIncomeId",
    "productTemplate.propertyAccountExpenseId",
    "productTemplate.lotSequenceId",
    "productTemplate.tracking",
    "productTemplate.responsibleId",
    "productTemplate.propertyStockProduction",
    "productTemplate.propertyStockInventory",
    "productTemplate.descriptionPicking",
    "productTemplate.descriptionPickingout",
    "productTemplate.descriptionPickingin",
    "productTemplate.purchaseMethod",
    "productTemplate.purchaseLineWarnMsg",
    "productTemplate.lotValuated",
    "productTemplate.serviceType",
    "productTemplate.reinvoicePolicy",
    "productTemplate.invoicePolicy",
    "productTemplate.saleDelay",
    "productTemplate.saleLineWarnMsg",
    "productTemplateAttributeValue.sequence",
    "productTemplateAttributeValue.productTmplId",
    "productTemplateAttributeValue.attributeId",
    "productTemplateAttributeValue.color",
    "productTemplateAttributeValue.createUid",
    "productTemplateAttributeValue.writeUid",
    "productTemplateAttributeValue.priceExtra",
    "productTemplateAttributeValue.ptavActive",
    "productTemplateAttributeValue.showPriceExtra",
    "productTemplateAttributeValue.createDate",
    "productTemplateAttributeValue.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productCombo.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productPricelist.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productPricelistItem.appliedOn",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productPricelistItem.base",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productPricelistItem.computePrice",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.defaultCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.combinationIndices",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.standardPrice",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.qtyAvailable",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productProduct.lotPropertiesDefinition",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productSupplierinfo.productName",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productSupplierinfo.productCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.type",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.serviceTracking",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.defaultCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.description",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPurchase",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionSale",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.productProperties",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyAccountIncomeId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyAccountExpenseId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.tracking",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.responsibleId",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyStockProduction",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.propertyStockInventory",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPicking",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPickingout",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.descriptionPickingin",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.purchaseMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.purchaseLineWarnMsg",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.serviceType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.reinvoicePolicy",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.invoicePolicy",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.saleDelay",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "productTemplate.saleLineWarnMsg",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productCombo.name",
      "key": "productCombo"
    },
    {
      "field": "productPricelist.name",
      "key": "productPricelist"
    },
    {
      "field": "productProduct.standardPrice",
      "key": "productProduct"
    },
    {
      "field": "productProduct.qtyAvailable",
      "key": "productProduct"
    },
    {
      "field": "productProduct.lotPropertiesDefinition",
      "key": "productProduct"
    },
    {
      "field": "productTemplate.name",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.description",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPurchase",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionSale",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.productProperties",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyAccountIncomeId",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyAccountExpenseId",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.responsibleId",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyStockProduction",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.propertyStockInventory",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPicking",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPickingout",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.descriptionPickingin",
      "key": "productTemplate"
    },
    {
      "field": "productTemplate.saleDelay",
      "key": "productTemplate"
    }
  ],
  "fields_fully_deferred": 61
}
```

## Tier 3 coverage
```json
{
  "productAttributeValueProductTemplateAttributeLineRel": {
    "mode": "full_diff",
    "population": 24,
    "duplicate_source_key_count": 0
  },
  "productCombo": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productCombo.item": 8,
    "productCombo.productTemplateRel": 3,
    "productProduct.customerProductReference": 1,
    "productProduct.uomUomRel": 1,
    "productProduct.productUom": 1,
    "productProduct.productVariantCombination": 20,
    "productTemplate.productOptionalRel": 3,
    "productTemplate.attributeLine": 9,
    "productTemplate.uomUomRel": 2,
    "productTemplateAttributeValue.productTemplateAttributeExcludedValueIdsRel": 1,
    "productTemplateAttributeValue.purchaseOrderLineRel": 2,
    "productTemplateAttributeValue.saleOrderLineRel": 1,
    "productTemplateAttributeValue.templateAttributeValueStockMoveRel": 1
  },
  "productPricelist": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "productPricelistItem": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "productProduct": {
    "mode": "full_diff",
    "population": 47,
    "duplicate_source_key_count": 0
  },
  "productSupplierinfo": {
    "mode": "full_diff",
    "population": 28,
    "duplicate_source_key_count": 0
  },
  "productTemplate": {
    "mode": "full_diff",
    "population": 37,
    "duplicate_source_key_count": 0
  },
  "productTemplateAttributeValue": {
    "mode": "full_diff",
    "population": 24,
    "duplicate_source_key_count": 0
  }
}
```
