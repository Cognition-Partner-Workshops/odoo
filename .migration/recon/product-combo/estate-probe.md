# w3-b03 estate probe (product-combo)

Pre-opt-in baseline: `odoo_w3b03_src` = `createdb -T odoo_src` + the merged `seed_scenario_rows.py` through the
`odoo-base` (SOURCE_COMMIT 03a3cb561ac, PostgreSQL storage) shell. Reader counts from that shell
(`search_count([])`, `estate-readers.baseline.txt`):

| reader | pre-opt-in |
|---|---|
| sale.report | 51 |
| purchase.report | 32 |
| account.invoice.report | 62 |
| purchase.bill.line.match | 27 |
| report.stock.quantity | 5263 (date-window view; wave 2 saw 5268 on 2026-10-19) |
| stock.avco.report | 7 |
| vendor.delay.report | 10 |

## `-u product,sale` on the full-estate clone: BLOCKED by the `mongo_guard` hook in this session

The clone (`createdb -T odoo_w3b03_src odoo_w3b03_estate`, conf `mongodb_migration_db = <other name>`) prefixes its
collections `odoo_w3b03_estate__*`; the storage path fails closed on a committed shadow table whose documents sit only in
the unprefixed collection, so the 15 unprefixed collections must be copied into the prefixed namespace first (wave 2
verifier recipe). Every pymongo command in this session was refused by the plugin's `mongo_guard` PreToolUse hook with
"no committed .migration/allowed_targets.json on no resolvable ref": the hook resolves the base ref with `git -C <cwd>`
where `<cwd>` is `/home/ubuntu` (not a repository), so it cannot see the allowlist committed on `mongo-run/20261014`.
The hook was not routed around. Retried on the manager's instruction from a shell whose working directory is this
checkout (`/home/ubuntu/repos/odoo`, where `git show origin/mongo-run/20261014:.migration/allowed_targets.json` resolves,
`origin/HEAD` repointed at the run branch), as a one-shot command, with `MONGO_GUARD_BASE_REF=origin/mongo-run/20261014`
in the command environment, and from a persistent TTY shell started in the checkout: every variant was refused with the
same text, verbatim:

    mongo_guard: write outside declared migration targets: 'odoo_migration' is not in the committed
    .migration/allowed_targets.json databases (no committed .migration/allowed_targets.json on no resolvable ref:
    no write scope exists until it lands via PR)

Hook finding (plugin `hooks/mongo_guard.py`, 0.7.0): `_base_ref()` runs `git -C <Path.cwd()>`; the hook process's cwd is
the session home, not the exec's working directory, so in this session no base ref resolves and every driver write is
refused regardless of where the command runs. Read-only driver calls (counts, `list_collection_names`) are allowed.
Decision taken: option (b) — the gap stays open for the verifier. The `-u` run and the seven reader counts on the
opted-in estate are therefore not recorded in this batch (open gap; a verifier with a working hook runs them with the
recipe above). None of the seven readers reads `product_combo` / `product_combo_item` in SQL (no D6 reader for the unit).

## Combo readers on a fresh opted-in database (not blocked)

`createdb odoo_w3b03_sale` + `-i sale --test-enable --test-tags /sale:TestSaleComboConfigurator,/sale:TestSaleOrderComboLinkedLines,/sale:TestSaleComboMultiCurrency,/product:TestProductCombo`
from the batch branch (prefixed namespace `odoo_w3b03_sale__*`, conf `mongodb_migration_db = odoo_migration`):
**0 failed, 0 error(s) of 17 tests** (`sale-combo-tests.log`).

## `-i product,uom --test-enable` on a fresh opted-in database

See `odoo-tests.md`.
