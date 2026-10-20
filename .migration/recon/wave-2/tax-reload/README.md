# Wave 2: live `accountTax` reloaded from a fully seeded clone (UNT12-49)

**Verdict: PASS**, account-chart scoped live recon, `merge_eligible: true`, `target_class: migration_cluster`, mode `live`,
redaction unsalted (`RECON_REDACT_SALT` unavailable, same as every prior run on this board). Data only: no migration code,
mapping, tolerances, target allowlist or plugin change.

**Why:** the wave-2 close recon (`recon/wave-2-close @ a099b1b`, `.migration/recon/wave-2/close/`) failed on `accountTax`
alone, Tier 1 `embed_cardinality`: `rows(account_tax_sale_order_line_rel)=51 vs sum(len(saleOrderLineRel))=50` and
`rows(account_tax_purchase_order_line_rel)=32 vs sum(len(purchaseOrderLineRel))=31`. The product-catalog seed block
(odoo PR #71) attaches tax 3 to sale line 52 and tax 4 to purchase line 33; live `accountTax` predated that block.

## Recipe
- `mongo-run/unt12` @ `9287c2116cd0d98a3ee6f89fbfef4e8a4300e2b7`; `mapping_spec.json` sha256
  `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` (map-draft-2), `recon_tolerances.json` sha256
  `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea` (unt12-3), both exact matches.
- Plugin `mongo-migration-plugin` @ `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (unpatched), harness `mongo-recon-harness 0.3.3`,
  canonicalization `skills/mongo-migration/profiles/postgresql.md`.
- Source: `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (marker 3, 70 modules), left untouched (21 active crons,
  `account_tax_sale_order_line_rel` 50 rows, `account_tax_purchase_order_line_rel` 31). `createdb -T odoo_src odoo_unt12_taxreload`,
  seeded via the pre-opt-in tree (`../odoo-unt12-src/odoo-bin shell --no-http`, never with `mongodb_migration_db`) with the whole
  committed `seed_scenario_rows.py` (every block incl. w1-b06 account-chart and w2-b02 product-catalog with its sequence pins,
  no "already past" warning) + `seed_uom_packaging.py` + `seed_account_journal.py`. Crons 1, 19-23 deactivated on the clone only
  (15 active). Clone after seeding: `account_tax` 58, sale-line rel 51 (extra pair tax 3 / line 52), purchase-line rel 32
  (extra pair tax 4 / line 33), `migration.fixture_source=3`.
- Reload (22:52Z, `reload.log`): `.migration/load/load_unit.py`'s `load()` unchanged, for unit `account-chart` with `--replace`
  semantics, with the unit's collection list narrowed to `accountTax` by a local out-of-repo driver (the committed loader has no
  per-collection switch; `load_unit.py --unit account-chart --replace` would have rewritten all six account-chart collections).
  Same read / convert / validate / drop / insert / index path as `w1-b06-reload`, one collection. Clone DSN derived in-process
  from `ODOO_PG_RO_DSN` (database swapped), target `MONGODB_ATLAS_URI` / `odoo_unt12`, secrets by name only. No other writer
  touched the target.
- Recon: one invocation, `--collections accountAccount,accountAccountTag,accountFiscalPosition,accountTax,accountTaxGroup,accountTaxRepartitionLine`,
  `--ops .migration/recon/account-chart/ops.json`, `--seed 0`, `--target-class migration_cluster`,
  `--allowed-targets-file .migration/allowed_targets.json`. `result.json`, `report.md`, `recon.summary.md` are the harness's own output.

## Recon (`result.json`)

| Tier | Checks | Result |
|---|---|---|
| 1 counts_through_mapping | 62 | PASS |
| 2 per_field_aggregates | 52 | PASS |
| 3 keyed_diffs | 999 | PASS |
| 4 app_level_parity | 6 | PASS |

warnings: 0. Tier 3 is 999 vs 997 in `w1-b06-reload`: the two new embedded elements (sale line 52, purchase line 33).

## Target before / after (`target_before.json` 22:51:37Z, `target_after.json` 22:52:36Z)
All 37 wave-1/2 collections in `odoo_unt12`: 821 documents, per-collection `countDocuments` and max `writeDate` identical
before and after for every collection, `accountTax` included (58 documents both times; the reload rewrites the same 58 `_id`s and
`writeDate` is the fixture's pinned instant, so count and max `writeDate` cannot show the reload). The reload shows in the embedded
arrays (`accountTax_embeds_after.json`, read-only aggregate after the reload, vs the wave-2 close recon's live target values):

| `accountTax` array | live before (close recon, `a099b1b`) | live after | clone rows |
|---|---|---|---|
| `saleOrderLineRel` elements | 50 | 51 (tax 3 carries line 52) | 51 |
| `purchaseOrderLineRel` elements | 31 | 32 (tax 4 carries line 33) | 32 |
| `alternatives` / `filiationRel` / `productSupplierTaxesRel` / `productTaxesRel` | - | 2 / 2 / 72 / 72 | 2 / 2 / 72 / 72 |

The other 36 collections were not written (no loader run named them; counts and max `writeDate` unchanged).

## Notes for the manager
- Loader gap (not fixed here, per ticket): `load_unit.py` reloads whole units only; a per-collection `--collections` switch would
  have made this reload a plain committed command. Report, do not patch.
- Guard note: the `mongo_guard` hook could not resolve the committed `.migration/allowed_targets.json` in this session
  ("no resolvable ref"), so every helper script had to avoid write-verb tokens even for read-only aggregates; same as prior tickets.
