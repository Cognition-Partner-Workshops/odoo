# Recon summary: `wave-1-close` - **FAIL**

- Mode: `live`
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping `map-draft-2` / tolerances `unt12-3` / seed `0`
- Generated: 2026-10-20T19:42:07.749708+00:00

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 141 | FAIL (10) |

Top findings (5 of 10; full list in result.json):
- T1 `accountAccount` embed_cardinality: rows(account_account_tax_default_rel)=1 vs sum(len(taxDefaultRel))=0
- T1 `accountAccountTag` root_count: rows(account_account_tag)=10 vs docs=8
- T1 `accountAccountTag` embed_cardinality: rows(account_account_tag_account_move_line_rel)=1 vs sum(len(accountMoveLineRel))=0
- T1 `accountAccountTag` embed_cardinality: rows(account_account_tag_account_tax_repartition_line_rel)=1 vs sum(len(accountTaxRepartitionLineRel))=0
- T1 `accountAccountTag` embed_cardinality: rows(account_account_tag_product_template_rel)=1 vs sum(len(productTemplateRel))=0

Full evidence: result.json, report.md (linked from the PR, not pasted).
