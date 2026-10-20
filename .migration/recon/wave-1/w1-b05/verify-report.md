run_id: ticket-af36adf385c942968dc4b75418b18765
manifest_sha: b965d1e5f34e
verified_head: 9ce27f95020cfcee76c28eb51309701f51990e77

# Verify report: w1-b05 (wave 1, product-attributes), third verify after the PR #68 rebase

Verdict: **PASS**

Verifier worked no wave-1 batch ticket. PR #59 branch `devin/1792505471-w1-b05-product-attributes` verified at head 9ce27f95020cfcee76c28eb51309701f51990e77 (rebased onto `mongo-run/unt12` a25acb9, the unified loader PR #68); plugin worktree at the pinned full SHA 9a584b4cdb311ddd64fb07cbd1cf35fc9485062c, unpatched. Nothing was written to the batch collections or to `odoo_src`; the only target write was the verifier's own reseed into `odoo_unt12.odoo_v_w1b05c__productAttribute` (the clone's test-isolation prefix), removed afterwards. Supersedes the verifies of 632a84155a54 and be4415b9 on this branch.

## Pinned contracts (bytes at the verified head)
- `.migration/mapping_spec.json`: map-draft-2, sha256 88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc (matches ticket)
- `.migration/recon_tolerances.json`: unt12-3, sha256 7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea (matches ticket)

## Independent reseed
- `.migration/fixtures/build_source.sh` rebuilt `odoo_src` (source commit 63446015e3c1, marker 3, fixed instant 2026-10-20 00:00:00).
- New clone `createdb -T odoo_src odoo_v_w1b05c`, then `seed_scenario_rows.py` through the pre-opt-in source tree (adds no product-attribute rows). Odoo was never run on a clone named in `mongodb_migration_db`; no `-u`, no `-i`, no ORM create, no `--replace`.
- Own reseed into the prefix: `verify-load-prefixed.py --unit product-attributes` loaded 14 documents (101 `value`, 9 `productTemplateRel` elements) and the spec indexes into `odoo_unt12.odoo_v_w1b05c__productAttribute` from the clone.
- Row counts on the clone: product_attribute 14, product_attribute_value 101, product_attribute_product_template_rel 9, product_attribute_value_product_template_attribute_line_rel 24 (9 lines).

## Recon re-run (harness verdict, the merge authority)
- Command: pinned `recon run --unit product-attributes --family postgresql --mode live --target-class migration_cluster --collections productAttribute --ops .migration/recon/product-attributes/ops.json`, source = `VERIFY_SRC_DSN` (verifier clone odoo_v_w1b05c), target = `MONGODB_ATLAS_URI` / `odoo_unt12` (live collection).
- Result: `.migration/recon/wave-1/w1-b05/result.json` -> verdict PASS, merge_eligible True, warnings [], error None.
- tier 1 counts_through_mapping: pass, 6 checks  
- tier 2 per_field_aggregates: pass, 6 checks  
- tier 3 keyed_diffs: pass, 124 checks  
- tier 4 app_level_parity: pass, 3 checks
- Tier 3 full diff over 14 root documents, embeds graded: value 101, productTemplateRel 9, duplicate source keys 0.
- Diff against the worker's committed `.migration/recon/product-attributes/result.json` at head: `generated_at` and `redaction_salted` only.

## Probes past the gate on the live collection (82 probes, 82 pass, `verify-probes.py` -> `verify-probes.json`, read-only)
- `odoo_unt12.productAttribute` count equals the source row count (source=14 target_count_documents=14); key set and min/max `_id` equal; collection not empty.
- `odoo_unt12.productAttributeValueProductTemplateAttributeLineRel` has 0 documents (documents=0 collection_present=True): the many2many stays in PostgreSQL.
- Null-vs-missing rate and value equality for all 9 root fields, all 11 `value` element fields and `productTemplateRel.productTemplateId`.
- Embedded arrays: `value` and `productTemplateRel` lengths equal child-row counts per parent (lengths array_lengths=[0, 1, 3, 4, 5, 6, 9, 20, 40] source_fanout_max=40; array_lengths=[0, 1, 2] source_fanout_max=2); childless parents carry no array key; element key sets equal, no duplicate elements, `value.id` unique across the collection.
- No unmapped fields on roots or elements; boundary values (product_attribute.sequence, value.sequence, value.default_extra_price, value.color) equal on both sides; all 3 declared indexes present.
- References: `productTemplateRel.productTemplateId` -> product_template and all create/write uids -> res_users resolve in the source; `productTemplate` is in no wave-1 write target, so no same-wave sibling reference and no sibling namespace probed.
- Tier 4 replay: `attribute_list`, `attribute_values_by_attribute`, `attribute_template_pairs` re-executed source SQL vs target pipeline, sorted at full precision: equal.

## ORM compare on the prefixed path (17 probes, 17 pass, `verify-orm-probes.py` -> `verify-orm-probes.json`)
Run as `odoo-bin shell` from the verified head against `odoo_v_w1b05c` with a conf that does not set `mongodb_migration_db`, so the ORM read `odoo_v_w1b05c__productAttribute` (asserted); cursor rolled back at the end.
- product.attribute=mongodb product.attribute.value=mongodb product.template.attribute.line=postgresql.
- `product.attribute` search_count / documents / PG rows: pg=14 orm_search_count=14 documents=14; `search([])` order equals `ORDER BY sequence, id`; `product.attribute.value` count pg=101 orm=101.
- `product.template.attribute.line.value_ids` == rel table per line: lines=9 rel_rows=24 orm_pairs=24 mismatching_lines=[].
- `product.attribute.value.pav_attribute_line_ids` == rel table per value: values=101 orm_pairs=24 mismatching_values=[]; both sides give the same 24 (line, value) pairs as the rel table.
- `value.attribute_id`, `attribute.value_ids`, `attribute.product_tmpl_ids` equal PostgreSQL; scalar fields of attributes and values equal (PostgreSQL NULL reads as the ORM's falsy default, as on the PostgreSQL path).
- Verifier's prefixed reseed vs the live collection: documents equal one by one (live=14 verifier_prefixed=14 first_diff_id=None); index key sets equal.
- Relation collection `productAttributeValueProductTemplateAttributeLineRel`: documents=0.

## Findings (none affect the verdict)
1. Storage-path gap (UNT12-33, not patched): the fresh `createdb -T odoo_src` clone has PostgreSQL NOT NULL on product_attribute('create_variant', 'display_type', 'name') and product_attribute_value('attribute_id', 'name'); `relax_shadow_tables` runs only in `auto_init` (install/update), so a clone that never ran `-u product` would still hit NotNullViolation on its first ORM create. This verify ran no ORM create, `-u`, `-i` or `--replace` reload (reads only), so the gap was reachable but not exercised.
2. No committed tooling reseeds a unit into a clone's `<clone>__` prefix: `.migration/load/load_unit.py` only targets the unit's unprefixed write-target collections. The verifier's `verify-load-prefixed.py` reuses the loader's own functions (documents, validate, index_specs, write_collection) unchanged against `<clone>__productAttribute` instead; the prefixed documents and indexes equal the live collection exactly, and the temporary collection was removed afterwards (temporary collection removed: odoo_v_w1b05c__productAttribute present now: False). Run/plugin gap for the manager: the verifier procedure asks for a prefixed reseed the loader cannot do.
3. Disclosure: the previous re-verify (be4415b9) ran `odoo-bin shell` with `mongodb_migration_db = <clone>` to read the unprefixed live collections (reads only, cursor rolled back, no `-u`/`-i`, no ORM create; the storage path writes indexes only in `auto_init`), the pattern the manager has since forbidden. This verify reads only the clone's prefixed collections.
4. Both the worker's run and this re-run are redacted with unsalted hashes because no RECON_REDACT_SALT secret is available to this session (harness stderr warning; result.json warnings stay empty, so the verdict is unaffected). The worker's committed result at head has redaction_salted=true, so the two result.json files differ in `generated_at` and `redaction_salted` only.
5. Plugin gap, unpatched: the installed mongo-recon-harness skill text (plugin 0.7.0) names a `--source-concurrency` flag that the pinned CLI at 9a584b4cdb311ddd64fb07cbd1cf35fc9485062c rejects; the flag was omitted.
6. `.migration/load/scenario_product_attributes.py` writes through the ORM (rolled back), so it was not replayed under the write-nothing rule; the read-only ORM probes in `verify-orm-probes.py` cover the reads the manager asked for instead.
