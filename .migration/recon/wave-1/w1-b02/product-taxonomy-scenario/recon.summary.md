# Recon summary: `product-taxonomy` - **FAIL**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-5` / tolerances `v1` / seed `0`
- Generated: 2026-10-15T23:00:48.928114+00:00

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 10 | PASS |
| 2 per_field_aggregates | 13 | PASS |
| 3 keyed_diffs | 13 | FAIL (10) |
| 4 app_level_parity | 4 | PASS |

Top findings (5 of 10; full list in result.json):
- T3 `productBaseUnit` field_diff: field create_date->createDate key=tuple:28cb03b06c28
- T3 `productBaseUnit` field_diff: field write_date->writeDate key=tuple:28cb03b06c28
- T3 `productBaseUnit` field_diff: field create_date->createDate key=tuple:0555debc8a65
- T3 `productBaseUnit` field_diff: field write_date->writeDate key=tuple:0555debc8a65
- T3 `productTag` field_diff: field create_date->createDate key=tuple:28cb03b06c28

Full evidence: result.json, report.md (linked from the PR, not pasted).
