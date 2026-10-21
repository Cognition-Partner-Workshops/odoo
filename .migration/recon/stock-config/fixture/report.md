# Recon report: unit `stock-config`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `stockLocation`, `stockPickingType`, `stockPutawayRule`, `stockRoute`, `stockRule`, `stockStorageCategoryCapacity`, `stockWarehouse`, `stockWarehouseOrderpoint`
- Seed: `0`
- Generated: 2026-10-20T23:47:16.150190+00:00
- 164 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 31 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 15 | PASS |
| 2 | per_field_aggregates | 114 | PASS |
| 3 | keyed_diffs | 114 | PASS |
| 4 | app_level_parity | 5 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "stockLocation": 38,
    "stockPickingType": 24,
    "stockPutawayRule": 2,
    "stockRoute": 9,
    "stockRule": 15,
    "stockStorageCategoryCapacity": 2,
    "stockWarehouse": 3,
    "stockWarehouseOrderpoint": 5
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
    "stockPutawayRule.productId",
    "stockPutawayRule.categoryId",
    "stockPutawayRule.sequence",
    "stockPutawayRule.storageCategoryId",
    "stockPutawayRule.createUid",
    "stockPutawayRule.writeUid",
    "stockPutawayRule.sublocation",
    "stockPutawayRule.active",
    "stockPutawayRule.createDate",
    "stockPutawayRule.writeDate",
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
    "stockRule.sequence",
    "stockRule.companyId",
    "stockRule.locationSrcId",
    "stockRule.routeSequence",
    "stockRule.delay",
    "stockRule.partnerAddressId",
    "stockRule.warehouseId",
    "stockRule.createUid",
    "stockRule.writeUid",
    "stockRule.action",
    "stockRule.procureMethod",
    "stockRule.auto",
    "stockRule.pushDomain",
    "stockRule.name",
    "stockRule.active",
    "stockRule.locationDestFromRule",
    "stockRule.propagateCancel",
    "stockRule.propagateCarrier",
    "stockRule.createDate",
    "stockRule.writeDate",
    "stockStorageCategoryCapacity.productId",
    "stockStorageCategoryCapacity.packageTypeId",
    "stockStorageCategoryCapacity.createUid",
    "stockStorageCategoryCapacity.writeUid",
    "stockStorageCategoryCapacity.createDate",
    "stockStorageCategoryCapacity.writeDate",
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
    "stockWarehouse.buyPullId",
    "stockWarehouseOrderpoint.replenishmentUomId",
    "stockWarehouseOrderpoint.routeId",
    "stockWarehouseOrderpoint.createUid",
    "stockWarehouseOrderpoint.writeUid",
    "stockWarehouseOrderpoint.name",
    "stockWarehouseOrderpoint.trigger",
    "stockWarehouseOrderpoint.minMaxBasedOn",
    "stockWarehouseOrderpoint.snoozedUntil",
    "stockWarehouseOrderpoint.deadlineDate",
    "stockWarehouseOrderpoint.qtyToOrderComputed",
    "stockWarehouseOrderpoint.qtyToOrderManual",
    "stockWarehouseOrderpoint.active",
    "stockWarehouseOrderpoint.createDate",
    "stockWarehouseOrderpoint.writeDate",
    "stockWarehouseOrderpoint.supplierId"
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
      "field": "stockPutawayRule.sublocation",
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
      "field": "stockRule.action",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockRule.procureMethod",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockRule.auto",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockRule.pushDomain",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockRule.name",
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
    },
    {
      "field": "stockWarehouseOrderpoint.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockWarehouseOrderpoint.trigger",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "stockWarehouseOrderpoint.minMaxBasedOn",
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
    },
    {
      "field": "stockRule.name",
      "key": "stockRule"
    }
  ],
  "fields_fully_deferred": 72
}
```

## Tier 3 coverage
```json
{
  "stockLocation": {
    "mode": "full_diff",
    "population": 38,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "stockLocation.stockPickingTypeRel": 2,
    "stockPickingType.pickingTypeFavoriteUserRel": 1,
    "stockRoute.categ": 1,
    "stockRoute.move": 1,
    "stockRoute.product": 1,
    "stockRoute.warehouse": 9,
    "stockWarehouse.stockWhResupplyTable": 1
  },
  "stockPickingType": {
    "mode": "full_diff",
    "population": 24,
    "duplicate_source_key_count": 0
  },
  "stockPutawayRule": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "stockRoute": {
    "mode": "full_diff",
    "population": 9,
    "duplicate_source_key_count": 0
  },
  "stockRule": {
    "mode": "full_diff",
    "population": 15,
    "duplicate_source_key_count": 0
  },
  "stockStorageCategoryCapacity": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "stockWarehouse": {
    "mode": "full_diff",
    "population": 3,
    "duplicate_source_key_count": 0
  },
  "stockWarehouseOrderpoint": {
    "mode": "full_diff",
    "population": 5,
    "duplicate_source_key_count": 0
  }
}
```
