# `-i product,uom --test-enable` on a fresh opted-in database (w3-b03)

`createdb odoo_w3b03_test` + `odoo-bin -d odoo_w3b03_test --no-http -c <conf> -i product,uom --test-enable --stop-after-init`
from the batch branch; `<conf>` sets `mongodb_migration_db = odoo_migration`, so the test database writes only to the
`odoo_w3b03_test__*` namespace (`odoo-tests.unprefixed_after.json`: every wave 1/2 collection still has the count the wave 2 verifier recorded,
this batch's productCombo 4 / productComboItem 10 are as loaded; the other collections present are the parallel
wave 3 batches' loads, not touched here).

Result: `21 failed, 6 error(s) of 1683 tests` over the whole dependency chain (mail, web, base, phone_validation, ...).
Of the 159 `product` + `uom` tests started, **1 failed, 0 errors**:

- `product` `TestProductAttributeValueConfig.test_get_closest_possible_combinations` — the same single failure the wave 2
  verifier recorded on the run-branch tip (`.migration/recon/wave-2/odoo-tests.log`); not a combo path.

Outside the unit's modules, all pre-existing on this VM: `phone_validation` 12 failures of 16 — identical on the pre-opt-in
`odoo-base` worktree (`-i phone_validation --test-enable` on `odoo_w3b03_basepv`: `12 failures, 0 errors of 16 tests`);
`web` 1 failure + 2 errors and `base` 4 errors are the PDF / wkhtmltox / barcode report tests of the base-suite note.

`TestProductCombo` (product) and the three sale combo classes ran green on the fresh `sale` install: see `estate-probe.md`.
Filtered log: `odoo-tests.log` (module loads, test starts, failures, result line).
