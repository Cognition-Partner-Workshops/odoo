# Wave 1 close: full-scope recon (independent, read-only)

- Run branch `mongo-run/unt12` @ `7fee6d9d335fba6b392b2658159eb9f47714c0ec` (all six wave-1 batch PRs merged: #56 #61 #62 #60 #59 #64)
- Plugin `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (pinned, unpatched), harness mode `live`, target `odoo_unt12`, `target_class: migration_cluster`
- Mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`; tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (both verified against the pinned values)
- Source: `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (marker 3), cloned with `createdb -T`; crons 1,19-23 deactivated on the clones only (`odoo_src` still all active)
- 25 collections in one run; Tier 4 ops = the six batches' committed `ops.json` merged (`ops.json`, 28 ops, 22 collections)

## Verdict

**Primary run (`result.json`): FAIL, merge_eligible=False**, Tier 1 `counts_through_mapping` 141 checks, 10 findings, all on account-chart (#64) collections. The harness halts at the first failing tier, so Tiers 2-4 were not graded in this run.

Clone: `seed_scenario_rows.py` (whole committed script, incl. the w1-b06 account-chart block at lines 117-166) + `seed_uom_packaging.py`, exactly as the ticket asked.

**Diagnostic run (`diag-unseeded-account-chart/result.json`): PASS, merge_eligible=True**, 25/25 collections, Tiers 1-4 = T1 141, T2 164, T3 1251, T4 28 checks, 0 findings, 0 warnings. Identical setup except the clone was seeded with the same script minus the w1-b06 account-chart block (how PR #64 actually ran: its own result records `source odoo_src`, i.e. unseeded).

### Reading

No batch broke another batch's data. Every account-chart root and junction count on the target equals the unseeded `odoo_src` exactly (tags 8, taxes 57, repartition lines 228, all seven zero-fixture junction tables 0), and the 19 non-#64 collections pass all four tiers with the full committed seed. The FAIL is an **evidence gap in #64 (account-chart)**: the committed seed block for its seven zero-fixture arrays (added by #68) was never loaded into `odoo_unt12` and #64's live recon ran against the unseeded `odoo_src`, so those arrays are still graded over 0 rows (`embeds_graded` in the diag run: `accountAccount.taxDefaultRel`, `accountAccountTag.{accountMoveLineRel,accountTaxRepartitionLineRel,productTemplateRel}`, `accountTax.filiationRel`, `accountFiscalPosition.{account,resCountryStateRel}` all 0). Per the ticket nothing was fixed or reloaded; manager decision needed on whether #64 must reload from a seeded clone and re-prove, or the seed block is dropped from the close criteria.

### Differing keys (primary run, source clone vs target)

Seeded in the clone, absent on the target: `account_account_tag` ids 9,10; `account_tax` id 58; `account_tax_repartition_line` ids 229-232; junction rows `account_account_tax_default_rel` 1, `account_account_tag_account_move_line_rel` 1, `account_account_tag_account_tax_repartition_line_rel` 1, `account_account_tag_product_template_rel` 1, `account_tax_filiation_rel` 2, `account_fiscal_position_account` 1, `account_fiscal_position_res_country_state_rel` 2. Most likely culprit batch: **#64 account-chart** (not an interference from another batch).

## Per-collection tier table

| collection | batch | target docs | primary T1 (seeded clone) | diag T1-T4 (clone without #64 seed) |
|---|---|---|---|---|
| `stockStorageCategory` | #56 | 6 | PASS (src 6) | PASS (src 6) |
| `stockScrapReasonTag` | #56 | 3 | PASS (src 3) | PASS (src 3) |
| `returnReason` | #56 | 5 | PASS (src 5) | PASS (src 5) |
| `productCategory` | #61 | 7 | PASS (src 7) | PASS (src 7) |
| `productRemoval` | #61 | 4 | PASS (src 4) | PASS (src 4) |
| `productTag` | #61 | 3 | PASS (src 3) | PASS (src 3) |
| `productDocument` | #61 | 2 | PASS (src 2) | PASS (src 2) |
| `productBaseUnit` | #61 | 2 | PASS (src 2) | PASS (src 2) |
| `uomUom` | #62 | 30 | PASS (src 30) | PASS (src 30) |
| `stockPackageType` | #62 | 3 | PASS (src 3) | PASS (src 3) |
| `accountPaymentTerm` | #60 | 11 | PASS (src 11) | PASS (src 11) |
| `accountIncoterms` | #60 | 11 | PASS (src 11) | PASS (src 11) |
| `accountCashRounding` | #60 | 2 | PASS (src 2) | PASS (src 2) |
| `accountJournalGroup` | #60 | 2 | PASS (src 2) | PASS (src 2) |
| `accountLockException` | #60 | 1 | PASS (src 1) | PASS (src 1) |
| `accountReport` | #60 | 5 | PASS (src 5) | PASS (src 5) |
| `accountReportExpression` | #60 | 3 | PASS (src 3) | PASS (src 3) |
| `accountReportExternalValue` | #60 | 1 | PASS (src 1) | PASS (src 1) |
| `productAttribute` | #59 | 14 | PASS (src 14) | PASS (src 14) |
| `accountAccount` | #64 | 184 | FAIL: rows(account_account_tax_default_rel)=1 vs sum(len(taxDefaultRel))=0 | PASS (src 184) |
| `accountAccountTag` | #64 | 8 | FAIL: rows(account_account_tag)=10 vs docs=8; rows(account_account_tag_account_move_line_rel)=1 vs sum(len(accountMoveLineRel))=0; rows(account_account_tag_account_tax_repartition_line_rel)=1 vs sum(len(accountTaxRepartitionLineRel))=0; rows(account_account_tag_product_template_rel)=1 vs sum(len(productTemplateRel))=0 | PASS (src 8) |
| `accountTax` | #64 | 57 | FAIL: rows(account_tax)=58 vs docs=57; rows(account_tax_filiation_rel)=2 vs sum(len(filiationRel))=0 | PASS (src 57) |
| `accountTaxGroup` | #64 | 26 | PASS (src 26) | PASS (src 26) |
| `accountTaxRepartitionLine` | #64 | 228 | FAIL: rows(account_tax_repartition_line)=232 vs docs=228 | PASS (src 228) |
| `accountFiscalPosition` | #64 | 4 | FAIL: rows(account_fiscal_position_account)=1 vs sum(len(account))=0; rows(account_fiscal_position_res_country_state_rel)=2 vs sum(len(resCountryStateRel))=0 | PASS (src 4) |

## Read-only proof (target `odoo_unt12`)

`target_before.json` taken 2026-10-20T19:41:22.975117+00:00 (before the primary run) and `target_after.json` taken 2026-10-20T19:45:32.311392+00:00 (after the diagnostic run): `countDocuments` and max `writeDate`/`createDate` identical for all 25 collections; max `writeDate` is `2026-10-20T00:00:00` everywhere.

| collection | count before | count after | max writeDate before | max writeDate after |
|---|---|---|---|---|
| `stockStorageCategory` | 6 | 6 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `stockScrapReasonTag` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `returnReason` | 5 | 5 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productCategory` | 7 | 7 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productRemoval` | 4 | 4 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productTag` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productDocument` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productBaseUnit` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `uomUom` | 30 | 30 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `stockPackageType` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountPaymentTerm` | 11 | 11 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountIncoterms` | 11 | 11 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountCashRounding` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountJournalGroup` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountLockException` | 1 | 1 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountReport` | 5 | 5 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountReportExpression` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountReportExternalValue` | 1 | 1 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `productAttribute` | 14 | 14 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountAccount` | 184 | 184 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountAccountTag` | 8 | 8 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountTax` | 57 | 57 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountTaxGroup` | 26 | 26 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountTaxRepartitionLine` | 228 | 228 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |
| `accountFiscalPosition` | 4 | 4 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 |

Not run: `load_unit.py`, any Odoo process against the target, any Odoo with `mongodb_migration_db` set. Redaction unsalted (`RECON_REDACT_SALT` unset, same as batches #56/#61/#62/#60/#64).
