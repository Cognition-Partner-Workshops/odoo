# Recon report: unit `product-pricing`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productPricelist`, `productPricelistItem`
- Seed: `0`
- Generated: 2026-10-20T15:28:02.119629+00:00
- 32 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 4 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 18 | PASS |
| 2 | per_field_aggregates | 26 | PASS |
| 3 | keyed_diffs | 12 | PASS |
| 4 | app_level_parity | 7 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productPricelist": 4,
    "productPricelistItem": 7
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
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
    "productPricelistItem.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
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
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productPricelist.name",
      "key": "productPricelist"
    }
  ],
  "fields_fully_deferred": 7
}
```

## Tier 3 coverage
```json
{
  "productPricelist": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "productPricelist.resCountryGroupPricelistRel": 1
  },
  "productPricelistItem": {
    "mode": "full_diff",
    "population": 7,
    "duplicate_source_key_count": 0
  }
}
```
