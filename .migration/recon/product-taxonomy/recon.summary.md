# Recon summary: `product-taxonomy` - **PASS**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-5` / tolerances `v1` / seed `1`
- Generated: 2026-10-15T16:58:08.808930+00:00
- **WARNING: UNVERIFIED collection productBaseUnit: 0 source rows, key/shape/field rules unexercised**
- **WARNING: UNVERIFIED collection productTag: 0 source rows, key/shape/field rules unexercised**

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 10 | PASS |
| 2 per_field_aggregates | 13 | PASS |
| 3 keyed_diffs | 8 | PASS |
| 4 app_level_parity | 4 | PASS |

Full evidence: result.json, report.md (linked from the PR, not pasted).
