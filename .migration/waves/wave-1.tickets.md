# Wave 1 ticket blocks (s4.1.0-preflight)

Emitted by `skills/wave-preflight/preflight.py --wave .migration/waves/wave-1.json --root . --emit-tickets` at plugin `c7f5feff23bd995dd4adfb6364a16583c668e171` (`.migration/plugin_sha`).
Preflight: `wave 1 OK: 3 batches, manifest_sha ea9f6b868dc7`.

The `## Ticket:` blocks below are the tool's output verbatim; each `### Worker notes` section is the run-specific addendum the manager pastes under the matching block.

### Worker notes (apply to every wave-1 batch; paste after the emitted block)

- Storage path (run branch after PR #19, `odoo/orm/storage_mongodb.py`): opt each unit model in with `_storage = 'mongodb'`; collection names and indexes come from `.migration/mapping_spec.json` (map-draft-5) plus the model's unique constraints/indexes; `CHECK` constraints run as Python predicates per `orm_backend_contract.md` §3. `_id` = the PostgreSQL integer id (d-id-key keep-int-id); an id-only shadow table stays in PostgreSQL for the inbound FKs and the D6 SQL readers (contract §4) — not the batch's code to port.
- Target database = `.migration/allowed_targets.json` `databases[0]` (`odoo_migration`). The Odoo config key `mongodb_uri` names the *environment variable* holding the URI (default `MONGODB_ATLAS_URI`); the value never enters the config. Secrets are present only in one-shot exec shells; bind `secret:personal:ODOO_PG_RO_DSN` (JSON) for the read-only source and `MONGODB_ATLAS_URI` for the target. Write only to the batch's write targets.
- `_parent_store` is supported (`parent_path` computed in Python) — `product.category` (w1-b02) and `uom.uom` (w1-b01) rely on it.
- No raw SQL in any wave-1 unit (`units.json` `raw_sql: []`); cross-boundary readers are listed per unit under `cross_boundary.d6_sql_readers` and are served by the shadow table.
- Recon is strict (`recon_tolerances.json` v1: exact, `full_diff_row_threshold` 100000). Load fixture-first (`odoo_fixture`, rebuilt by `.migration/fixtures/build_source.sh` then `build_fixture.sh`; manifest `.migration/fixtures/odoo_fixture.json`), then the demo data, then one `--mode live` run with `--target-class migration_cluster`. A `fixture_zero_rows` table is schema-only for recon until the batch adds scenario rows (tier 4) and says so in the PR.
- `auto_merge` is `false` for this wave: the PR stays open; the manager grades with `preflight.py --grade` at wave close.

## Ticket: migrate batch w1-b01 (wave 1)

Wave: 1
Batch id: w1-b01
Units: ["uom"]
Write targets: ["odoo_migration.uomUom"]
Fixture manifest: .migration/fixtures/odoo_fixture.json
Mapping version: map-draft-5 (sha256 e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a)
Tolerances version: v1 (sha256 59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68)
source_access: live
target_access: migration_cluster
auto_merge eligible: False
manifest_sha: ea9f6b868dc7
Required evidence: harness result.json per unit committed on the PR branch, PR URL echoing manifest_sha in the body, failure class if FAIL, and a batch result JSON with ["batch", "status", "recon_results", "write_targets", "one_line_summary"] plus pr_url, branch, failure_class (recon_results lists the committed result.json paths; verdicts are read from them, never asserted).

## Ticket: migrate batch w1-b02 (wave 1)

Wave: 1
Batch id: w1-b02
Units: ["product-taxonomy"]
Write targets: ["odoo_migration.productCategory", "odoo_migration.productTag", "odoo_migration.productBaseUnit"]
Fixture manifest: .migration/fixtures/odoo_fixture.json
Mapping version: map-draft-5 (sha256 e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a)
Tolerances version: v1 (sha256 59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68)
source_access: live
target_access: migration_cluster
auto_merge eligible: False
manifest_sha: ea9f6b868dc7
Required evidence: harness result.json per unit committed on the PR branch, PR URL echoing manifest_sha in the body, failure class if FAIL, and a batch result JSON with ["batch", "status", "recon_results", "write_targets", "one_line_summary"] plus pr_url, branch, failure_class (recon_results lists the committed result.json paths; verdicts are read from them, never asserted).

### Worker notes: w1-b02 `product-taxonomy` (`product.category`, `product.tag`, `product.base.unit` in `addons/product/models/`)

- Expected rows: `product_category` 8, `product_tag` 0, `product_base_unit` 0. **`fixture_zero_rows`: `product_tag`, `product_base_unit`** — add scenario rows for both before claiming recon on them.
- **PG-owned relation table / unbounded array**: `productCategory.routeIds ← stock_route_categ` is declared by `stock` (model_only) and stays a PostgreSQL relation table this run (NOTES.md D1, units.json `pg_owned_arrays`); any array snapshot is point-in-time only, so state how the batch treats it in the PR (snapshot vs. excluded) — strict recon on it cannot be continuous.
- `_parent_store` + `parent_path` index on `product.category`.
- D2: foreign-module stored fields on `product.category` (account `property_account_*` ×7 company-dependent JSONB, stock `packaging_reserve_method` / `removal_strategy_id`, stock_account `property_cost_method` / `property_valuation`, sale/purchase `property_*`) must land in the document. D6: `stock_avco_report` reads `product_category.property_cost_method` → shadow `product_category(id, property_cost_method)` (S).
- `product.tag._name_uniq` → unique index. `product.category` is `mail.thread`: its 8 `mail_message` rows and 7 `ir_model_data` xmlids stay PostgreSQL (D4).

## Ticket: migrate batch w1-b03 (wave 1)

Wave: 1
Batch id: w1-b03
Units: ["product-attributes"]
Write targets: ["odoo_migration.productAttribute", "odoo_migration.productAttributeValue", "odoo_migration.updateProductAttributeValue"]
Fixture manifest: .migration/fixtures/odoo_fixture.json
Mapping version: map-draft-5 (sha256 e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a)
Tolerances version: v1 (sha256 59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68)
source_access: live
target_access: migration_cluster
auto_merge eligible: False
manifest_sha: ea9f6b868dc7
Required evidence: harness result.json per unit committed on the PR branch, PR URL echoing manifest_sha in the body, failure class if FAIL, and a batch result JSON with ["batch", "status", "recon_results", "write_targets", "one_line_summary"] plus pr_url, branch, failure_class (recon_results lists the committed result.json paths; verdicts are read from them, never asserted).

### Worker notes: w1-b03 `product-attributes` (`product.attribute`, `product.attribute.value`, `update.product.attribute.value` in `addons/product/`)

- Expected rows: `product_attribute` 17, `product_attribute_value` 114, `product_attribute_product_template_rel` 12, `update_product_attribute_value` 0. **`fixture_zero_rows`: `update_product_attribute_value`** (TransientModel → `_transient_vacuum` = `deleteMany`, contract §3) — exercise the wizard to produce scenario rows.
- **Unbounded embed**: `productAttribute.productTmplIds ← product_attribute_product_template_rel` (embedded in the batch's own collection; the referenced `productTemplate` ids migrate in wave 2 — store ints only, no join at load).
- `CHECK _check_multi_checkbox_no_variant` (`product_attribute.py:14`) → Python check; the spec drops index `product_attribute_value(sequence)`.
- D4: 8 `ir_attachment` rows (attribute-value images) and 14 + 101 `ir_model_data` xmlids stay PostgreSQL. `forward_refs_same_or_later_depth`: `product-catalog` (wave 2).

## Ticket: verify wave 1 (independent verifier)

Wave: 1
Batch id: wave-1-verify
Units: ["product-attributes", "product-taxonomy", "uom"]
Write targets: ["odoo_migration.productAttribute", "odoo_migration.productAttributeValue", "odoo_migration.productBaseUnit", "odoo_migration.productCategory", "odoo_migration.productTag", "odoo_migration.uomUom", "odoo_migration.updateProductAttributeValue"] (read-only; verify writes nothing)
Fixture manifest: n/a (re-runs from the spec and each batch's fixture manifest)
Contracts per batch (re-run each batch against exactly the committed mapping / tolerances bytes whose sha256 it pins, from the batch's merged PR): w1-b01: mapping map-draft-5 sha256 e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a, tolerances v1 sha256 59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68; w1-b02: mapping map-draft-5 sha256 e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a, tolerances v1 sha256 59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68; w1-b03: mapping map-draft-5 sha256 e329b5aec09f4594d2ae8a297ff346e71f0cfe1a82043373c1d995bcdc0b160a, tolerances v1 sha256 59f500708400dbd7ffb23dfbd9264b962cf6307e9a48ec678157cd2dbcdb4b68
source_access: live
target_access: migration_cluster
auto_merge eligible: False
manifest_sha: ea9f6b868dc7
Required evidence: verify report committed as recon/wave-1:.migration/recon/wave-1/verify-report.md whose first lines are `run_id:` and `manifest_sha:`, and a verify result JSON with wave_verdict, unit_verdicts keyed by batch id, recon_results (batch id -> the harness result.json paths of your re-runs, committed on recon/wave-1; a PASS is graded from them, never asserted), findings, report_path.
