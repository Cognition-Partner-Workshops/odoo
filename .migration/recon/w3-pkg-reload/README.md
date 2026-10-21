# w3-pkg-reload: reload `stockPutawayRule` / `stockPackageType` after the w3-b01 seed collision

Wave-1 seed `.migration/load/seed_uom_packaging.py` creates putaway rule 1 (warehouse0 stock location, linked to Pallet and
the seeded tote), embedded in `stockPackageType.stockPutawayRuleRel`. The first w3-b01 seed block pinned
`stock_putaway_rule_id_seq` to 0 on a clone that had not applied that seed, so its two rules took ids 1 and 2 and the live
`stockPutawayRule` collection disagreed with the live `stockPackageType` arrays.

Fix (manager decision on the batch ticket): the w3-b01 seed block no longer pins the putaway-rule / capacity sequences
(forward-only from what the earlier seeds leave: the rules become 2 and 3), the seeded clone `odoo_w3b01` was rebuilt from
`odoo_src` applying every committed seed in run-branch order (`seed_uom_packaging.py`, `seed_scenario_rows.py`,
`seed_account_journal.py`, all through the pre-opt-in tree), and `.migration/load/load_unit.py --replace` reloaded
`--unit stock-config` and `--unit uom-packaging` from it. No allowlist, mapping, tolerance or loader change.

- `before/` — read-only dump of the live `stockPackageType` and `stockPutawayRule` documents before the reload.
- `after/` — the same two collections after the reload.
- `uom-packaging/` — live recon of the uom-packaging unit (`uomUom`, `stockPackageType`) after the reload.
- The stock-config live recon, scenario log, tests and batch result are refreshed on PR #73
  (`.migration/recon/stock-config/`, `.migration/recon/w3-b01.json`).
