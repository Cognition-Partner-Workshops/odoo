# Recon summary: `product-attributes` - **PASS**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-5` / tolerances `v1` / seed `1`
- Generated: 2026-10-15T20:02:11.876635+00:00
- **WARNING: UNVERIFIED collection updateProductAttributeValue: 0 source rows, key/shape/field rules unexercised**

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 8 | PASS |
| 2 per_field_aggregates | 16 | PASS |
| 3 keyed_diffs | 124 | PASS |
| 4 app_level_parity | 2 | PASS |

Full evidence: result.json, report.md (linked from the PR, not pasted).
