# Recon summary: `product-taxonomy` - **FAIL**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-5` / tolerances `v1` / seed `0`
- Generated: 2026-10-15T23:00:05.646919+00:00

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 10 | FAIL (2) |

Top findings (2 of 2; full list in result.json):
- T1 `productBaseUnit` root_count: rows(product_base_unit)=0 vs docs=2
- T1 `productTag` root_count: rows(product_tag)=0 vs docs=3

Full evidence: result.json, report.md (linked from the PR, not pasted).
