# Recon summary: `wave-3-close` - **FAIL**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-2` / tolerances `unt12-3` / seed `0`
- Generated: 2026-10-21T05:29:45.504982+00:00

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 371 | PASS |
| 2 per_field_aggregates | 394 | PASS |
| 3 keyed_diffs | 1647 | FAIL (3) |
| 4 app_level_parity | 46 | FAIL (1) |

Top findings (4 of 4; full list in result.json):
- T3 `productPricelist` field_diff: field active->active key=tuple:24a6ade6d35f
- T3 `productPricelist` field_diff: field write_date->writeDate key=tuple:24a6ade6d35f
- T3 `productProduct` field_diff: field write_date->writeDate key=tuple:666aa17826ad
- T4 `productPricelist` parity_mismatch: op pricelist_list: 1 source rows unmatched, 1 target rows unmatched

Full evidence: result.json, report.md (linked from the PR, not pasted).
