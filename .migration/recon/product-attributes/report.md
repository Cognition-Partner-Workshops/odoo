# Recon report: unit `product-attributes`

- **Verdict: ERROR** (values redacted)
- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productAttribute`, `productAttributeValue`, `updateProductAttributeValue`
- Seed: `1`
- Generated: 2026-10-15T17:03:41.685524+00:00

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 8 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productAttribute": 14,
    "productAttributeValue": 101,
    "updateProductAttributeValue": 0
  }
}
```
