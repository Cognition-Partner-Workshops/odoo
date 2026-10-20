# Recon report: unit `product-supplierinfo`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productSupplierinfo`
- Seed: `0`
- Generated: 2026-10-20T02:28:51.439540+00:00
- 13 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 2 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 7 | PASS |
| 2 | per_field_aggregates | 13 | PASS |
| 3 | keyed_diffs | 32 | PASS |
| 4 | app_level_parity | 5 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productSupplierinfo": 32
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
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
    "productSupplierinfo.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
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
    }
  ],
  "fields_fully_deferred": 6
}
```

## Tier 3 coverage
```json
{
  "productSupplierinfo": {
    "mode": "full_diff",
    "population": 32,
    "duplicate_source_key_count": 0
  }
}
```
