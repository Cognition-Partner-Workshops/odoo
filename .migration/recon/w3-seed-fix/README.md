# w3-seed-fix: the w3-b01 stock-config seed no longer changes wave-2 product data (UNT12-53)

**Verdict: PASS**, `merge_eligible: true`, `target_class: migration_cluster`, mode `live`, the same 45 wave-1/2/3 collections and
46-op `ops.json` as the wave-3 close (UNT12-52, branch `recon/wave-3-close` @ `0a3408ec626`): T1 counts_through_mapping 371,
T2 per_field_aggregates 394, T3 keyed_diffs 1647, T4 app_level_parity 46, 0 findings (`result.json`, `report.md`, `recon.summary.md`).
Mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc`, tolerances `unt12-3` sha256
`7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`, plugin `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c`
(worktree of exactly that SHA, unpatched; redaction unsalted as in every prior run). Harness run 05:46:50Z-05:49:38Z.
Nothing was loaded, reloaded or changed on the target; `load_unit.py` was not run.

## The fix (strategy: restore what the settings run changed, re-pin what it touched)

`stock.warehouse.create` for the archived "Seeded Depot" runs `_check_multiwarehouse_group`, which switches the multi-location
group on through `res.config.settings.execute()`; product's `set_values` archives every active pricelist while
`group_product_pricelist` is off. The block already undid the group change; it now also

- records the active pricelists before the create and re-activates whichever the settings run archived (pricelist 7
  "Seeded wholesale"), asserting the active set is unchanged;
- adds `product_product` and `product_pricelist` to the final `create_date`/`write_date` re-pin loop (product 5 "Office Chair"
  and pricelist 7 were bumped by that transaction).

Preventing the side effect instead was rejected: the live `stockPickingType` documents were loaded from a clone on which that
same settings run had *activated* the internal picking types 7 and 15 (inactive on `odoo_src`), so skipping it would change
`stockPickingType` against live. Restoring keeps all 8 stock-config collections and `stockPackageType` byte-identical.
Modules and demo data are untouched; the block stays idempotent (guarded by the SEED warehouse) and forward-only (no
"already past" sequence-pin warning in `seed_clone_new.log`).

## Evidence

1. **Before/after clone diff** (`clone_diff/`): `odoo_w3sf_old` seeded with the committed block (`seed_clone_old.log`) and
   `odoo_w3sf_new` with the new one (`seed_clone_new.log`), both `createdb -T odoo_src` after a fresh
   `.migration/fixtures/build_source.sh`, seeded in run-branch order (`seed_uom_packaging.py`, `seed_scenario_rows.py`,
   `seed_account_journal.py`) through the pre-opt-in tree's `odoo-bin shell --no-http`, all exit 0.
   `table_diff.sh` (sorted column-insert dumps) finds 140 differing INSERT lines; `field_diff.txt` lists them per row and
   column. The only in-scope rows that differ are **`product_pricelist` 7** (`active` false -> true, `write_date` re-pinned)
   and **`product_product` 5** (`write_date` re-pinned). Everything else is wall-clock noise between two seed runs two
   seconds apart (05:45:53 vs 05:45:55), none of it a migrated collection: framework rows written by the same settings
   transaction in both clones (`ir_config_parameter` 28-55, `res_groups` 1/41/42, `res_config_settings` 1, `res_company` 1,
   `res_partner` 1, `ir_default` 37-38, `bus_bus`, `orm_signaling_*`, `mail_message`, the 6 `ir_cron` rows the seed
   deactivates) and the w2-b02 sale/purchase sample whose `date_order`/`date_planned`/`stock_move.date`/`account_move_line`
   dates are `now()` by design (`sale_order` 26, `purchase_order` 18, `stock_move` 136-137, `account_move_line` 164-167).
   No table has rows only on one side.
2. **Live recon** from `odoo_w3sf_new` (this directory): PASS as above.
3. **Scenarios** on the prefixed clone `odoo_w3sf_new` (collections `odoo_w3sf_new__*`, live documents copied with their
   indexes, dropped again afterwards): `scenario_product_catalog.log` **59/59**, `scenario_stock_config.log` **61/61**.
4. **Target unchanged**: `target_before.json` (05:45:17Z, before any run) and `target_after.json` (05:53:22Z, after the recon,
   both scenarios and the scratch-collection cleanup) agree on every one of the 45 collections: `countDocuments`, max
   `writeDate` and the sha256 over every document's raw BSON; 920 documents. `target_snapshot.py` is the read-only script.
