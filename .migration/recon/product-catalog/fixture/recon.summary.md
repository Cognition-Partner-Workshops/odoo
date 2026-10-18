# Recon summary: `product-catalog` - **PASS**

- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-5` / tolerances `v1` / seed `0`
- Generated: 2026-10-18T21:46:03.581694+00:00
- **WARNING: UNVERIFIED collection productUom: 0 source rows, key/shape/field rules unexercised**

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 19 | PASS |
| 2 per_field_aggregates | 51 | PASS |
| 3 keyed_diffs | 594 | PASS |
| 4 app_level_parity | 7 | PASS |

Full evidence: result.json, report.md (linked from the PR, not pasted).
