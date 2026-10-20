run_id: ticket-2b3f882c17a846d69b8095d102368ba1
manifest_sha: ae71ec6a28e6

# Verify report: wave 2, batch w2-b02 (unit product-catalog) - **PASS**

Independent verifier; this session migrated none of wave 2 and wrote nothing to `odoo_unt12`.

## What was re-run
- Batch PR: https://github.com/Cognition-Partner-Workshops/odoo/pull/71, verified at the exact pushed head `c8f81e30931c150f8da4fd9da0b68349435c4787` (the batch-result commit on top of code head `be4d6578dee`), base `mongo-run/unt12@8ac087cabc1` (confirmed an ancestor of the head; it carries the shared fixes #70 and #72). Verifier branch `recon/verify-w2-b02` is cut from that head; no implementation file was changed.
- Mapping `map-draft-2` sha256 `88650faf41b79db3c9bc266313ea224c37047053636507942f23ebe0b20b0ebc` and tolerances `unt12-3` sha256 `7b426db2145915686a86975ccdb3192d2f622282975207e8f8bb59363de498ea`: committed bytes on the PR head, re-hashed by the verifier, equal to the ticket pins and to the values the rerun `result.json` records.
- Plugin/harness pinned at `9a584b4cdb311ddd64fb07cbd1cf35fc9485062c` (detached worktree, unpatched); canonicalization from `skills/mongo-migration/profiles/postgresql.md`.
- Source: `odoo_src` did not exist on this VM; rebuilt from scratch with `.migration/fixtures/build_source.sh` as committed on the head (marker `migration.fixture_source=3`, 70 modules, 65 s; product_template 37 / product_product 47 / uom_uom 30). Then `createdb -T odoo_src odoo_v43` and `seed_scenario_rows.py` (which carries the w2-b02 seed block) applied to `odoo_v43` through the pre-opt-in source tree (`odoo-unt12-src/odoo-bin shell`, PostgreSQL storage only); crons 1 and 19-23 deactivated on the clone only (`odoo_src` still has all 6 active). The seed block's sequence pins reproduced the live ids on the fresh clone: pricelists `[7, 8]`, items `[3, 4]`, product.uom 2, customer.product.reference 2, sale 26 / line 52, purchase 18 / line 33, stock.move 136 - no "already past" warning was printed.
- Target: `odoo_unt12` on `MONGODB_ATLAS_URI` (class `migration_cluster`), read-only. Collections graded (`--collections`): `productTemplate`, `productProduct`, `productTemplateAttributeValue`, `productAttributeValueProductTemplateAttributeLineRel`, `productCombo`, `productSupplierinfo`, `productPricelist`, `productPricelistItem`.
- Tier 4 ops: the verifier's own file `.migration/recon/wave-2/w2-b02/verify-ops.json` (10 ops, sha256 `7aeb5a72848d25e52d7e34b580a7f95707b90a3e2c25c5f3f84fa6244a98f7be`), not the batch's `.migration/recon/product-catalog/ops.json` (8 ops, sha256 `132579d3f1b3065ed76e622cb60c83e6294e9ffbc361deaced88e64fa8c335b2`).

## Recon rerun (harness verdict)
- Result: `.migration/recon/wave-2/w2-b02/product-catalog/result.json` - verdict **PASS**, mode `live`, target_class `migration_cluster`, merge_eligible `True`, generated `2026-10-20T22:21:36.509126+00:00`, warnings `[]`, 33 s.

| Tier | Name | Checks | Findings | Result |
|---|---|---|---|---|
| 1 | counts_through_mapping | 83 | 0 | PASS |
| 2 | per_field_aggregates | 78 | 0 | PASS |
| 3 | keyed_diffs | 220 | 0 | PASS |
| 4 | app_level_parity | 10 | 0 | PASS |

- Source counts seen by the harness: productTemplate 37, productProduct 47, productTemplateAttributeValue 24, productAttributeValueProductTemplateAttributeLineRel 24, productCombo 3, productSupplierinfo 28, productPricelist 2, productPricelistItem 2 - identical to the worker's run (`.migration/recon/product-catalog/result.json`, 83/78/220/8). Tier 1-3 `stats` blocks of the two result files are byte-identical apart from `generated_at`; Tier 4 differs only in the number of ops (10 verifier ops vs 8 worker ops).
- One live run was enough: no mismatch, so no source re-read for drift was needed; the probe script re-read the source counts at its end and they were unchanged.

### Verifier ops (Tier 4), all 10 PASS
template_embed_counts (per template: categ/uom/type/list_price/active + sizes of attributeLine, productOptionalRel, uomUomRel), variant_embed_counts (per variant: template/default_code/active/lst_price + sizes of productVariantCombination, productUom, customerProductReference, uomUomRel), variant_combination_pairs (unwound junction), ptav_relation_counts (per PTAV: price_extra/ptav_active + sizes of the excluded-value, sale-line, purchase-line and stock-move arrays), attribute_line_value_counts ($group per attribute line with min/max value id), combo_item_lines (unwound items with extra_price), combo_templates (unwound junction), vendor_lines_per_partner ($group: lines, min/max price, sum min_qty, max delay), pricelists_with_rule_counts ($lookup into productPricelistItem), pricelist_rules_detail (14 columns per rule).

## Probes past the gate
Script `.migration/recon/wave-2/w2-b02/probe_w2_b02.py` (read-only on both sides: PG `default_transaction_read_only`, Atlas `secondaryPreferred`, no mutating call), evidence `.migration/recon/wave-2/w2-b02/probe-results.json`. 263 probes: 260 PASS, 0 FAIL, 3 SKIP.

| Probe family | Probes | Result | What it checked |
|---|---|---|---|
| count | 8 | PASS | document count == source row count per collection; none empty (37/47/24/24/3/28/2/2) |
| null_missing | 139 | PASS | per mapped field: no explicit BSON null on the target (null_missing_equiv), and target missing-field count == source NULL count |
| duplicates | 11 | PASS | no duplicate `_id`; no duplicate natural keys (productProduct barcode, productTmplId+combinationIndices; productTemplateAttributeValue attributeLineId+productAttributeValueId; the rel pair) |
| boundaries | 7 | PASS | min/max `_id` and min/max of sequence / productTmplId / minQuantity equal source |
| boundary_doc | 8 | PASS | first and last template, variant, vendor line and pricelist rule compared field by field against the source row |
| jsonb_fields | 4 | PASS | every JSONB (translated, company-dependent, properties) field on every row of productTemplate (18 fields), productProduct (standardPrice 28 non-null rows, qtyAvailable, lotPropertiesDefinition), productCombo.name, productPricelist.name: object-equal after key/number canonicalization |
| embed_lengths | 13 | PASS | per parent: embedded array length == source child-row count, no child without a parent document; distributions: productTemplate.productOptionalRel 3 {0:35,1:1,2:1}, attributeLine 9 {0:30,1:5,2:2}, uomUomRel 2 {0:36,2:1}; productProduct.customerProductReference 1, uomUomRel 1, productUom 1 (each {0:46,1:1}), productVariantCombination 20 {0:32,1:10,2:5}; productTemplateAttributeValue excluded 1, purchaseOrderLineRel 2 {0:22,1:2}, saleOrderLineRel 1, templateAttributeValueStockMoveRel 1; productCombo.item 8 {2:1,3:2}, productTemplateRel 3 {1:3} |
| embed_elements | 13 | PASS | the same 13 arrays element by element: multiset of (parent id + every child field) on the target == source child rows, 0 only-source / 0 only-target |
| reference | 29 PASS, 3 SKIP | PASS | outbound references resolve; FK targets taken from the census `ref_table`, resolved to a root collection `_id` or an embedded array's `id`; merged wave-1 collections (productCategory 5 values, uomUom, productAttribute._id 5, productAttribute.value.id 16, productBaseUnit 0) and same-batch targets (productTemplate._id, productTemplate.attributeLine.id 9, productProduct._id, productTemplateAttributeValue._id, productPricelist._id) only; 0 dangling everywhere. SKIP: purchaseOrderLine, saleOrderLine, stockMove (later waves, PostgreSQL-resident). Sibling batch w2-b01 (accountJournal, accountPaymentMethod, accountReconcileModel, accountReconcileModelLineAccountTaxRel) is referenced by nothing and its namespaces were never inspected - no `cross_batch_reference` |
| indexes | 8 | PASS | every index declared by the mapping exists on the live collection (16/13/8/2/3/6/4/10) |
| ops_replay | 10 | PASS | the 10 verifier ops replayed independently (source SQL on the clone vs target pipeline), compared as unordered row sets keyed by column name: 37=37, 47=47, 20=20, 24=24, 9=9, 8=8, 3=3, 6=6, 2=2, 2=2 rows |
| seeded_nonempty | 9 | PASS | the two zero-fixture roots and seven zero-fixture arrays the seed block fills are non-empty on the target (2, 2, 2, 1, 1, 1, 2, 1, 1 elements), so none is UNVERIFIED |
| source_stability | 1 | PASS | source counts re-read after all probes, unchanged |

## Findings
No findings. Nothing in the batch blocks merge; no tolerance, target or model change is requested.

Observations (not findings, for the manager):
- Plugin gap at pin `9a584b4`: the harness `result.json` has no `ops_sha256` key, so preflight's `verifier_reused_ops` check cannot be fed from it; the ops sha256 values above are recorded here instead (verifier `7aeb5a72...`, worker `132579d3...`, different files).
- Proposer precision gap (mapping, not batch): `decision.references[].to` names the owning collection for FKs into embedded tables (`product_attribute_value_id -> productAttribute`, `attribute_line_id -> productTemplate`), so a probe that reads `to` literally compares against the wrong `_id` set (16 dangling values on a first pass). The probe resolves targets via the census `ref_table` instead; the data is consistent (`productAttribute.value.id` holds all 101 values, `productTemplate.attributeLine.id` all 9 lines).
- `RECON_REDACT_SALT` is not set in this environment either; the committed artifacts are redacted with unsalted hashes, as in every run of this engagement.
- Not re-run by the verifier: the batch's ORM scenario (`scenario_product_catalog.py`, worker 59/59) and the three rebuilt PostgreSQL views - both need an opted-in Odoo instance against a prefixed copy of the collections, which this no-write verify did not start. The recon gate, the element-level embed checks and the reference checks above are the evidence this verdict rests on.

## Verdict
**PASS** - graded from the committed rerun `result.json` (head `c8f81e30931`), not asserted.
