# Recon report: unit `product-taxonomy`

- **Verdict: FAIL** (values redacted)
- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productBaseUnit`, `productCategory`, `productTag`
- Seed: `0`
- Generated: 2026-10-15T23:00:05.646919+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 10 | FAIL (2 findings) |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productBaseUnit": 0,
    "productCategory": 8,
    "productTag": 0
  }
}
```

## Tier 1 findings (2)
- `productBaseUnit` root_count: rows(product_base_unit)=0 vs docs=2
- `productTag` root_count: rows(product_tag)=0 vs docs=3
