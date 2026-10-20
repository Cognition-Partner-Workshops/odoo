run_id: ticket-af36adf385c942968dc4b75418b18765
manifest_sha: b965d1e5f34e

# Verify report: w1-b05 (wave 1, product-attributes)

Verdict: **PASS**

Verifier worked no wave-1 batch ticket. PR #59 branch `devin/1792505471-w1-b05-product-attributes` checked out as pushed at 632a84155a54; plugin worktree at the pinned full SHA 9a584b4cdb311ddd64fb07cbd1cf35fc9485062c, unpatched. Nothing was written to `odoo_unt12` or to `odoo_src`.

## Pinned contracts (bytes on the PR branch)
- `.migration/mapping_spec.json`: map-draft-2, sha256 88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc (matches ticket)
- `.migration/recon_tolerances.json`: unt12-3, sha256 7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea (matches ticket)

## Independent reseed
- `.migration/fixtures/build_source.sh` rebuilt `odoo_src` (source commit 63446015e3c1, marker 3, fixed instant 2026-10-20 00:00:00).
- `createdb -T odoo_src odoo_v_w1b05`, then `seed_scenario_rows.py` (shared wave-1 seed; it adds no product-attribute rows). No `-u product`, no ORM create, no `--replace` reload.
- Row counts on the clone: product_attribute 14, product_attribute_value 101, product_attribute_product_template_rel 9.

## Recon re-run (harness verdict, the merge authority)
- Command: pinned `recon run --unit product-attributes --family postgresql --mode live --target-class migration_cluster --collections productAttribute --ops .migration/recon/product-attributes/ops.json`, source = `VERIFY_SRC_DSN` (verifier clone), target = `MONGODB_ATLAS_URI` / `odoo_unt12`.
- Result: `.migration/recon/wave-1/w1-b05/result.json` -> verdict PASS, merge_eligible True, warnings [], error None.
- tier 1 counts_through_mapping: pass, 6 checks  
- tier 2 per_field_aggregates: pass, 6 checks  
- tier 3 keyed_diffs: pass, 124 checks  
- tier 4 app_level_parity: pass, 3 checks
- Tier 3 full diff over 14 root documents, embeds graded: value 101, productTemplateRel 9, duplicate source keys 0.
- Diff against the worker's committed `.migration/recon/product-attributes/result.json`: only `generated_at` differs.

## Probes past the gate (80 probes, 80 pass, `verify-probes.py` -> `verify-probes.json`)
- Counts, key set, min/max `_id` present; collection not empty; only `productAttribute` touched by this batch.
- Null-vs-missing rate and value equality for all 9 root fields and all 11 `value` element fields, plus `productTemplateRel.productTemplateId`.
- Embedded arrays: `value` and `productTemplateRel` lengths equal child-row counts per parent (lengths array_lengths=[0, 1, 3, 4, 5, 6, 9, 20, 40] source_fanout_max=40; array_lengths=[0, 1, 2] source_fanout_max=2); childless parents carry no array key (childless=[4, 5, 14] with_key=[]; childless=[4, 2, 5, 8, 7, 6, 13, 1, 14] with_key=[]); element key sets equal, no duplicate elements, `value.id` unique across the collection.
- No unmapped fields on roots or elements (observed element keys: extra=[] observed_keys=['active', 'color', 'createDate', 'createUid', 'defaultExtraPrice', 'htmlColor', 'id', 'isCustom', 'name', 'sequence', 'writeDate', 'writeUid']).
- Boundary values: min/max of product_attribute.sequence, value.sequence, value.default_extra_price, value.color equal on both sides.
- Indexes: all 3 declared indexes present (sequence; value.id unique; productTemplateRel.productTemplateId).
- References: `productTemplateRel.productTemplateId` -> product_template and all create/write uids -> res_users resolve in the source; `productTemplate` is in no wave-1 write target, so no same-wave sibling reference and no sibling namespace probed.
- Tier 4 replay: `attribute_list`, `attribute_values_by_attribute`, `attribute_template_pairs` re-executed source SQL vs target pipeline, sorted at full precision: equal.

## Findings (none affect the verdict)
1. Storage-path gap (UNT12-33, not patched): my fresh `createdb -T odoo_src` clone still carries PostgreSQL NOT NULL on product_attribute(create_variant, display_type, name) and product_attribute_value(attribute_id, name), so the first ORM create would hit the NotNullViolation the worker reported; this verify ran no ORM create, `-u product` or `--replace` reload, so the gap was reachable but not exercised here.
2. PR #59 is cut from acab458 and adds an `@api.constrains` mirror (`_check_multi_checkbox_no_variant_documents`) of the model's SQL CHECK; the run branch has since merged PR #58, which enforces CHECK constraints on the storage path (f73b4c71ec0), so the mirror is redundant after rebase. `git merge-tree` shows no conflicts; a manager call, not a verdict changer.
3. Both the worker's run and this re-run are redacted with unsalted hashes because no RECON_REDACT_SALT secret exists (harness stderr warning; result.json warnings stay empty, so the verdict is unaffected).
4. Plugin gap, unpatched: the installed mongo-recon-harness skill text (plugin 0.7.0) names a `--source-concurrency` flag that the pinned CLI at 9a584b4cdb311ddd64fb07cbd1cf35fc9485062c rejects; the flag was omitted.
5. No scenario rows exist for this unit: `.migration/load/seed_scenario_rows.py` seeds only the w1-b01 stock scenario, and `scenario_product_attributes.py` writes through the ORM, so it was not replayed under the write-nothing rule; the 14/101/9 fixture rows were verified instead.
