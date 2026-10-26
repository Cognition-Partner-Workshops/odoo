# Recon report: unit `stockLocation`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `e80675c263bf` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `b95c45dc5e4f`
- Collections: `stockLocation`, `stockPickingType`, `stockRoute`, `stockWarehouse`
- Seed: `0`
- Generated: 2026-10-26T12:14:05.177789+00:00
- 113 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 22 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 88 | PASS |
| 2 | per_field_aggregates | 65 | PASS |
| 3 | keyed_diffs | 164 | PASS |
| 4 | app_level_parity | 4 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockLocation": 62,
    "stockPickingType": 40,
    "stockRoute": 13,
    "stockWarehouse": 5
  },
  "embed_source_counts": {
    "stockLocation.stockPickingTypeRel": 2,
    "stockPickingType.pickingTypeFavoriteUserRel": 1,
    "stockRoute.categ": 1,
    "stockRoute.move": 2,
    "stockRoute.product": 1,
    "stockRoute.warehouse": 15,
    "stockRoute.stockRule": 21,
    "stockWarehouse.stockWhResupplyTable": 1
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "stockLocation.locationId",
    "stockLocation.companyId",
    "stockLocation.removalStrategyId",
    "stockLocation.cyclicInventoryFrequency",
    "stockLocation.warehouseId",
    "stockLocation.storageCategoryId",
    "stockLocation.createUid",
    "stockLocation.writeUid",
    "stockLocation.name",
    "stockLocation.completeName",
    "stockLocation.usage",
    "stockLocation.parentPath",
    "stockLocation.barcode",
    "stockLocation.lastInventoryDate",
    "stockLocation.nextInventoryDate",
    "stockLocation.active",
    "stockLocation.replenishLocation",
    "stockLocation.createDate",
    "stockLocation.writeDate",
    "stockLocation.valuationAccountId",
    "stockPickingType.color",
    "stockPickingType.sequence",
    "stockPickingType.sequenceId",
    "stockPickingType.allocatedLocationId",
    "stockPickingType.returnPickingTypeId",
    "stockPickingType.warehouseId",
    "stockPickingType.reservationDaysBefore",
    "stockPickingType.reservationDaysBeforePriority",
    "stockPickingType.batchMaxLines",
    "stockPickingType.batchMaxPickings",
    "stockPickingType.createUid",
    "stockPickingType.writeUid",
    "stockPickingType.code",
    "stockPickingType.reservationMethod",
    "stockPickingType.productLabelFormat",
    "stockPickingType.lotLabelFormat",
    "stockPickingType.packageLabelToPrint",
    "stockPickingType.barcode",
    "stockPickingType.createBackorder",
    "stockPickingType.moveType",
    "stockPickingType.waveDateGranularity",
    "stockPickingType.name",
    "stockPickingType.pickingPropertiesDefinition",
    "stockPickingType.batchPropertiesDefinition",
    "stockPickingType.showEntirePacks",
    "stockPickingType.setPackageType",
    "stockPickingType.active",
    "stockPickingType.useCreateLots",
    "stockPickingType.useExistingLots",
    "stockPickingType.printLabel",
    "stockPickingType.autoShowAllocationReport",
    "stockPickingType.autoPrintDeliverySlip",
    "stockPickingType.autoPrintReturnSlip",
    "stockPickingType.autoPrintProductLabels",
    "stockPickingType.autoPrintLotLabels",
    "stockPickingType.autoPrintReceptionReport",
    "stockPickingType.autoPrintReceptionReportLabels",
    "stockPickingType.autoPrintPackages",
    "stockPickingType.autoPrintPackageLabel",
    "stockPickingType.autoBatch",
    "stockPickingType.batchGroupByPartner",
    "stockPickingType.batchGroupByDestination",
    "stockPickingType.batchGroupBySrcLoc",
    "stockPickingType.batchGroupByDestLoc",
    "stockPickingType.waveGroupByProduct",
    "stockPickingType.waveGroupByCategory",
    "stockPickingType.waveGroupByLocation",
    "stockPickingType.waveGroupByDate",
    "stockPickingType.batchAutoConfirm",
    "stockPickingType.createDate",
    "stockPickingType.writeDate",
    "stockRoute.sequence",
    "stockRoute.suppliedWhId",
    "stockRoute.supplierWhId",
    "stockRoute.companyId",
    "stockRoute.createUid",
    "stockRoute.writeUid",
    "stockRoute.name",
    "stockRoute.active",
    "stockRoute.productSelectable",
    "stockRoute.productCategSelectable",
    "stockRoute.warehouseSelectable",
    "stockRoute.packageTypeSelectable",
    "stockRoute.createDate",
    "stockRoute.writeDate",
    "stockRoute.saleSelectable",
    "stockWarehouse.partnerId",
    "stockWarehouse.whInputStockLocId",
    "stockWarehouse.whQcStockLocId",
    "stockWarehouse.whOutputStockLocId",
    "stockWarehouse.whPackStockLocId",
    "stockWarehouse.mtoPullId",
    "stockWarehouse.pickTypeId",
    "stockWarehouse.packTypeId",
    "stockWarehouse.outTypeId",
    "stockWarehouse.inTypeId",
    "stockWarehouse.intTypeId",
    "stockWarehouse.qcTypeId",
    "stockWarehouse.storeTypeId",
    "stockWarehouse.xdockTypeId",
    "stockWarehouse.receptionRouteId",
    "stockWarehouse.deliveryRouteId",
    "stockWarehouse.sequence",
    "stockWarehouse.createUid",
    "stockWarehouse.writeUid",
    "stockWarehouse.name",
    "stockWarehouse.code",
    "stockWarehouse.receptionSteps",
    "stockWarehouse.deliverySteps",
    "stockWarehouse.active",
    "stockWarehouse.createDate",
    "stockWarehouse.writeDate",
    "stockWarehouse.buyPullId"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "stockLocation.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockLocation.completeName",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockLocation.usage",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockLocation.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockLocation.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.reservationMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.productLabelFormat",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.lotLabelFormat",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.packageLabelToPrint",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.barcode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.createBackorder",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.moveType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.waveDateGranularity",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.pickingPropertiesDefinition",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockPickingType.batchPropertiesDefinition",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockRoute.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockWarehouse.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockWarehouse.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockWarehouse.receptionSteps",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockWarehouse.deliverySteps",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "stockPickingType.name",
      "key": "stockPickingType"
    },
    {
      "field": "stockPickingType.pickingPropertiesDefinition",
      "key": "stockPickingType"
    },
    {
      "field": "stockPickingType.batchPropertiesDefinition",
      "key": "stockPickingType"
    },
    {
      "field": "stockRoute.name",
      "key": "stockRoute"
    }
  ],
  "fields_fully_deferred": 54
}
```

## Tier 3 coverage
```json
{
  "stockLocation": {
    "mode": "full_diff",
    "population": 62,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "stockLocation.stockPickingTypeRel": 2,
    "stockPickingType.pickingTypeFavoriteUserRel": 1,
    "stockRoute.categ": 1,
    "stockRoute.move": 2,
    "stockRoute.product": 1,
    "stockRoute.warehouse": 15,
    "stockRoute.stockRule": 21,
    "stockWarehouse.stockWhResupplyTable": 1
  },
  "stockPickingType": {
    "mode": "full_diff",
    "population": 40,
    "duplicate_source_key_count": 0
  },
  "stockRoute": {
    "mode": "full_diff",
    "population": 13,
    "duplicate_source_key_count": 0
  },
  "stockWarehouse": {
    "mode": "full_diff",
    "population": 5,
    "duplicate_source_key_count": 0
  }
}
```
