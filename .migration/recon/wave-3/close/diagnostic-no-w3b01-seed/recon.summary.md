# Recon summary: `wave-3-close-diag-no-w3b01-seed` - **FAIL**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-2` / tolerances `unt12-3` / seed `0`
- Generated: 2026-10-21T05:33:29.116522+00:00

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 260 | FAIL (1) |

Top findings (1 of 1; full list in result.json):
- T1 `stockPackageType` embed_cardinality: rows(stock_package_type_stock_putaway_rule_rel)=2 vs sum(len(stockPutawayRuleRel))=4

Full evidence: result.json, report.md (linked from the PR, not pasted).
