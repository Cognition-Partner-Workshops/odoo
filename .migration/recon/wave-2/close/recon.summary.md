# Recon summary: `wave-2-close` - **FAIL**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-2` / tolerances `unt12-3` / seed `0`
- Generated: 2026-10-20T22:38:39.241789+00:00

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 260 | FAIL (2) |

Top findings (2 of 2; full list in result.json):
- T1 `accountTax` embed_cardinality: rows(account_tax_purchase_order_line_rel)=32 vs sum(len(purchaseOrderLineRel))=31
- T1 `accountTax` embed_cardinality: rows(account_tax_sale_order_line_rel)=51 vs sum(len(saleOrderLineRel))=50

Full evidence: result.json, report.md (linked from the PR, not pasted).
