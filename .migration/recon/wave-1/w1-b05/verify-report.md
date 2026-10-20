run_id: ticket-af36adf385c942968dc4b75418b18765
manifest_sha: b965d1e5f34e
verified_head: be4415b9fa8383fc017fe63689fccdfd1936ee58

# Verify report: w1-b05 (wave 1, product-attributes), re-verify after rebase

Verdict: **PASS**

Verifier worked no wave-1 batch ticket. PR #59 branch `devin/1792505471-w1-b05-product-attributes` re-verified at head be4415b9fa8383fc017fe63689fccdfd1936ee58 (rebased onto `mongo-run/unt12` 83cc4af, the PR #63 storage fixes); plugin worktree at the pinned full SHA 9a584b4cdb311ddd64fb07cbd1cf35fc9485062c, unpatched. Nothing was written to `odoo_unt12` or to `odoo_src`. This supersedes the verify of 632a84155a54 (commit 99b265ebd71 on this branch).

## Pinned contracts (bytes at the verified head)
- `.migration/mapping_spec.json`: map-draft-2, sha256 88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc (matches ticket)
- `.migration/recon_tolerances.json`: unt12-3, sha256 7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea (matches ticket)

## Independent reseed (fresh, after the rebase)
- `.migration/fixtures/build_source.sh` rebuilt `odoo_src` (source commit 63446015e3c1, marker 3, fixed instant 2026-10-20 00:00:00).
- Old verifier clone dropped; `createdb -T odoo_src odoo_v_w1b05` again, then `seed_scenario_rows.py` (shared wave-1 seed, adds no product-attribute rows). No `-u product`, no ORM create, no `--replace` reload.
- Row counts on the clone: product_attribute 14, product_attribute_value 101, product_attribute_product_template_rel 9, product_attribute_value_product_template_attribute_line_rel 24 (9 lines).

## Recon re-run (harness verdict, the merge authority)
- Command: pinned `recon run --unit product-attributes --family postgresql --mode live --target-class migration_cluster --collections productAttribute --ops .migration/recon/product-attributes/ops.json`, source = `VERIFY_SRC_DSN` (verifier clone), target = `MONGODB_ATLAS_URI` / `odoo_unt12`.
- Result: `.migration/recon/wave-1/w1-b05/result.json` -> verdict PASS, merge_eligible True, warnings [], error None.
- tier 1 counts_through_mapping: pass, 6 checks  
- tier 2 per_field_aggregates: pass, 6 checks  
- tier 3 keyed_diffs: pass, 124 checks  
- tier 4 app_level_parity: pass, 3 checks
- Tier 3 full diff over 14 root documents, embeds graded: value 101, productTemplateRel 9, duplicate source keys 0.
- Diff against the worker's committed `.migration/recon/product-attributes/result.json` at head: `generated_at` and `redaction_salted` only.

## Probes past the gate (82 probes, 82 pass, `verify-probes.py` -> `verify-probes.json`)
- `odoo_unt12.productAttribute` count equals the source row count (source=14 target_count_documents=14); key set and min/max `_id` equal; collection not empty.
- `odoo_unt12.productAttributeValueProductTemplateAttributeLineRel` has 0 documents (documents=0 collection_present=True): the many2many stays in PostgreSQL.
- Null-vs-missing rate and value equality for all 9 root fields, all 11 `value` element fields and `productTemplateRel.productTemplateId`.
- Embedded arrays: `value` and `productTemplateRel` lengths equal child-row counts per parent (lengths array_lengths=[0, 1, 3, 4, 5, 6, 9, 20, 40] source_fanout_max=40; array_lengths=[0, 1, 2] source_fanout_max=2); childless parents carry no array key; element key sets equal, no duplicate elements, `value.id` unique across the collection.
- No unmapped fields on roots or elements; boundary values (product_attribute.sequence, value.sequence, value.default_extra_price, value.color) equal on both sides; all 3 declared indexes present.
- References: `productTemplateRel.productTemplateId` -> product_template and all create/write uids -> res_users resolve in the source; `productTemplate` is in no wave-1 write target, so no same-wave sibling reference and no sibling namespace probed.
- Tier 4 replay: `attribute_list`, `attribute_values_by_attribute`, `attribute_template_pairs` re-executed source SQL vs target pipeline, sorted at full precision: equal.

## Read-only ORM probes on the storage path (14 probes, 14 pass, `verify-orm-probes.py` -> `verify-orm-probes.json`)
Run as `odoo-bin shell` from the verified head against the verifier clone with `mongodb_migration_db = odoo_v_w1b05` (unprefixed collections), cursor rolled back at the end; every ORM read compared by exact equality with the clone's PostgreSQL rows.
- product.attribute=mongodb product.attribute.value=mongodb product.template.attribute.line=postgresql.
- `product.attribute` search_count / documents / PG rows: pg=14 orm_search_count=14 documents=14; `search([])` order equals `ORDER BY sequence, id`; `product.attribute.value` count pg=101 orm=101.
- `product.template.attribute.line.value_ids` == rel table per line: lines=9 rel_rows=24 orm_pairs=24 mismatching_lines=[].
- `product.attribute.value.pav_attribute_line_ids` == rel table per value: values=101 orm_pairs=24 mismatching_values=[]; both sides give the same 24 (line, value) pairs as the rel table.
- `value.attribute_id`, `attribute.value_ids`, `attribute.product_tmpl_ids` equal PostgreSQL; scalar fields of attributes and values equal (PostgreSQL NULL reads as the ORM's falsy default, as on the PostgreSQL path).
- Relation collection `productAttributeValueProductTemplateAttributeLineRel`: documents=0.
- PR #59 at head no longer carries the `@api.constrains` mirror of the SQL CHECK flagged in the first verify (removed in the rebase; the storage path enforces CHECK constraints since PR #58/#63).

## Findings (none affect the verdict)
1. Both the worker's run and this re-run are redacted with unsalted hashes because no RECON_REDACT_SALT secret is available to this session (harness stderr warning; result.json warnings stay empty, so the verdict is unaffected). The worker's committed result at head has redaction_salted=true, so the two result.json files differ in `generated_at` and `redaction_salted` only.
2. Plugin gap, unpatched: the installed mongo-recon-harness skill text (plugin 0.7.0) names a `--source-concurrency` flag that the pinned CLI at 9a584b4cdb311ddd64fb07cbd1cf35fc9485062c rejects; the flag was omitted.
3. Odoo's config parser warns `unknown option 'mongodb_migration_db'` and stores it unparsed; the storage path still honours it (prefix '' asserted), so the ORM probes read the loaded collections. Cosmetic, for the storage-path owner.
4. `.migration/load/scenario_product_attributes.py` writes through the ORM (rolled back), so it was not replayed under the write-nothing rule; the read-only ORM probes in `verify-orm-probes.py` cover the reads the manager asked for instead.
