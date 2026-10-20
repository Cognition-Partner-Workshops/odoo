# Recon report: unit `product-catalog`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productDocument`, `productProduct`, `productTemplate`, `productTemplateAttributeLine`, `productTemplateAttributeValue`, `productUom`
- Seed: `0`
- Generated: 2026-10-20T00:32:53.172251+00:00
- 94 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 33 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 61 | PASS |
| 2 | per_field_aggregates | 51 | PASS |
| 3 | keyed_diffs | 348 | PASS |
| 4 | app_level_parity | 7 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productDocument": 2,
    "productProduct": 48,
    "productTemplate": 38,
    "productTemplateAttributeLine": 9,
    "productTemplateAttributeValue": 24,
    "productUom": 6
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productDocument.sequence",
    "productDocument.createUid",
    "productDocument.writeUid",
    "productDocument.active",
    "productDocument.createDate",
    "productDocument.writeDate",
    "productDocument.attachedOnSale",
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
    "productTemplateAttributeLine.sequence",
    "productTemplateAttributeLine.valueCount",
    "productTemplateAttributeLine.createUid",
    "productTemplateAttributeLine.writeUid",
    "productTemplateAttributeLine.active",
    "productTemplateAttributeLine.createDate",
    "productTemplateAttributeLine.writeDate",
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
    "productTemplateAttributeValue.writeDate",
    "productUom.companyId",
    "productUom.createUid",
    "productUom.writeUid",
    "productUom.barcode",
    "productUom.createDate",
    "productUom.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productDocument.attachedOnSale",
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
    },
    {
      "field": "productUom.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
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
  "fields_fully_deferred": 54
}
```

## Tier 3 coverage
```json
{
  "productDocument": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "productProduct": {
    "mode": "full_diff",
    "population": 48,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productProduct.productVariantCombination": 20,
    "productProduct.extraUomIds": 5,
    "productProduct.additionalProductTagIds": 6,
    "productTemplate.accountTagIds": 0,
    "productTemplate.comboIds": 3,
    "productTemplate.optionalProductIds": 3,
    "productTemplate.supplierTaxesId": 74,
    "productTemplate.productTagIds": 6,
    "productTemplate.taxesId": 74,
    "productTemplate.uomIds": 5,
    "productTemplate.routeIds": 0,
    "productTemplateAttributeLine.valueIds": 24,
    "productTemplateAttributeValue.excludedValueIds": 1
  },
  "productTemplate": {
    "mode": "full_diff",
    "population": 38,
    "duplicate_source_key_count": 0
  },
  "productTemplateAttributeLine": {
    "mode": "full_diff",
    "population": 9,
    "duplicate_source_key_count": 0
  },
  "productTemplateAttributeValue": {
    "mode": "full_diff",
    "population": 24,
    "duplicate_source_key_count": 0
  },
  "productUom": {
    "mode": "full_diff",
    "population": 6,
    "duplicate_source_key_count": 0
  }
}
```
