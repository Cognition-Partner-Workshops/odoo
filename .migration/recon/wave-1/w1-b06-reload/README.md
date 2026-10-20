# Wave 1 — account-chart (w1-b06) seeded reload

Ticket UNT12-38. Fixes the only wave-1 close FAIL (`recon/wave-1-close`, `.migration/recon/wave-1/close/`):
the live account-chart collections had been loaded from an unseeded `odoo_src`, so the seven zero-fixture arrays
seeded by `.migration/load/seed_scenario_rows.py` (odoo PR #68) were absent and PR #64's recon could not grade them.

## What was done
1. `.migration/fixtures/build_source.sh` rebuilt `odoo_src` (marker 3, 70 modules), then `createdb -T odoo_src odoo_w1b06`.
2. Seeds applied to the clone only via the pre-opt-in tree (`../odoo-unt12-src/odoo-bin shell`): `seed_scenario_rows.py`
   (crons 1, 19-23 deactivated; account-chart block created tags 9-10, tax 58, repartition lines 229-232, 1 fiscal-position
   account row, 7 junction rows) and `seed_uom_packaging.py`. Odoo was never started with `mongodb_migration_db`.
3. `.migration/load/load_unit.py --unit account-chart --replace` from the clone into `odoo_unt12` (secrets by name:
   clone DSN derived in-process from `ODOO_PG_RO_DSN`, target `MONGODB_ATLAS_URI`). No other writer touched the target.
4. Scoped live recon from `mongo-run/unt12` tip `7fee6d9` with plugin `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c`,
   `--collections` the six account-chart collections, `--ops .migration/recon/account-chart/ops.json`.

No migration code, mapping, tolerances or target allowlist were changed. PR #64's `load_unit.py` reloaded the seeded
clone cleanly, so no code correction is needed; its committed `.migration/recon/account-chart/result.json` (graded
against the unseeded source, Tier 3 = 981 checks) is superseded by `result.json` here (Tier 3 = 997) and was left untouched.

## Recon (`result.json`)
verdict **PASS**, `merge_eligible: true`, `target_class: migration_cluster`, mode `live`,
mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`,
tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`, warnings: 0.
Output is redacted; `RECON_REDACT_SALT` was not set (`redaction_salted: false`), same as every earlier run on this board.

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 62 | PASS |
| 2 per_field_aggregates | 52 | PASS |
| 3 keyed_diffs | 997 | PASS |
| 4 app_level_parity | 6 | PASS |

The seven previously UNVERIFIED arrays, now graded (`tiers[2].stats.embeds_graded`, elements compared):

| Array | Elements |
|---|---|
| `accountAccount.taxDefaultRel` | 1 |
| `accountAccountTag.accountMoveLineRel` | 1 |
| `accountAccountTag.accountTaxRepartitionLineRel` | 1 |
| `accountAccountTag.productTemplateRel` | 1 |
| `accountTax.filiationRel` | 2 |
| `accountFiscalPosition.account` | 1 |
| `accountFiscalPosition.resCountryStateRel` | 2 |

## Target before / after the reload (`target_before.json`, `target_after.json`)
All 25 wave-1 collections in `odoo_unt12`; only the six account-chart collections were rewritten (`--replace` rewrites
every document, so `accountAccount` and `accountFiscalPosition` keep their counts but gained the seeded array elements).
Max `writeDate` is the fixture's pinned instant everywhere.

| Collection | Count before | Count after | Max writeDate before | Max writeDate after | |
|---|---|---|---|---|---|
| `accountAccount` | 184 | 184 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | reloaded |
| `accountAccountTag` | 8 | 10 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | reloaded |
| `accountCashRounding` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountFiscalPosition` | 4 | 4 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | reloaded |
| `accountIncoterms` | 11 | 11 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountJournalGroup` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountLockException` | 1 | 1 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountPaymentTerm` | 11 | 11 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountReport` | 5 | 5 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountReportExpression` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountReportExternalValue` | 1 | 1 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `accountTax` | 57 | 58 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | reloaded |
| `accountTaxGroup` | 26 | 26 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | reloaded |
| `accountTaxRepartitionLine` | 228 | 232 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | reloaded |
| `productAttribute` | 14 | 14 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `productBaseUnit` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `productCategory` | 7 | 7 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `productDocument` | 2 | 2 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `productRemoval` | 4 | 4 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `productTag` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `returnReason` | 5 | 5 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `stockPackageType` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `stockScrapReasonTag` | 3 | 3 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `stockStorageCategory` | 6 | 6 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
| `uomUom` | 30 | 30 | 2026-10-20T00:00:00 | 2026-10-20T00:00:00 | untouched |
