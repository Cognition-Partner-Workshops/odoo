# ORM backend contract — MongoDB storage path for the product + uom slice

Decision implemented: **d-orm-target** = the MongoDB storage lives *inside* the Odoo ORM
(`odoo/orm/`), selected per model; **d-id-key = keep-int-id** = the PostgreSQL integer `id`
is the Mongo `_id` and an id-only shadow of each migrated table stays in PostgreSQL during
coexistence. This file is the contract the ticket "Build the MongoDB storage path in the
ORM" implements. Line numbers are Odoo 20.0 at `mongo-run/20261014` tip `a32c278`.

Scope: the 33 `migrate` tables of `.migration/table_buckets.json` (owners `product` 32,
`uom` 1) = 20 models + 13 relation tables (12 Many2many `_rel` tables and `product_variant_combination`); see `.migration/mapping_spec.json`
(`collections[*].root_table`, `key: {source: [id], target: _id}`). Everything else, including
the model-only `sale`/`purchase`/`stock`/`account` tables, stays PostgreSQL and its code is
not rewritten in this run. No plugin change; no write to Atlas in this ticket.

## 1. Opt-in: `_storage`

| item | contract |
|---|---|
| attribute | `BaseModel._storage: str = 'postgresql'` next to `_auto` (`odoo/orm/models.py:6579`). Slice models declare `_storage = 'mongodb'`. The declaration is made by one new addon, `product_mongodb` (depends on `product`, `uom`), that `_inherit`s each of the 20 models and sets `_storage`; `addons/product` and `addons/uom` are not edited for the opt-in. |
| inheritance | `odoo/orm/model_classes.py` resolves `_storage` like `_table` (`:250-253`, `:286`, `:297`): the value comes from the model class chain; a class that redefines `_storage` for an existing model with a different value raises the same "cannot redefine" error. `_log_access` keeps `= _auto` (`:287`): `create_uid`/`write_uid`/`create_date`/`write_date` are document fields. |
| registry | `Registry._setup_models__` (`odoo/orm/registry.py:456`) records `Registry.mongodb_models: frozenset[str]` after setup. `init_models` (`:812`) skips the `not_null_fields` and column scan for them (`:884` condition `Model._auto and not Model._abstract` gains `and Model._storage == 'postgresql'`); `check_indexes` (`:904`) skips them; `is_an_ordinary_table` (`:1069`) returns `False` for them so `ir.model` tooling treats them like `_auto = False` models for SQL purposes. |
| relation tables | A Many2many field whose `relation` table is in the slice (13 tables, owner `product`) is stored as an array of integer ids on the model that declares the field (`field.model_name`), on whichever side the open-item pick says (`.migration/open_model_items.md`, items A-M2M-*). A Many2many whose relation table is out of slice (e.g. `product_taxes_rel`, owner `account`) stays a PostgreSQL relation table of integer ids (NOTES.md D1). |
| transient | `product.label.layout` and `update.product.attribute.value` are `TransientModel`s in the slice; `_transient_vacuum` (`odoo/orm/models_transient.py`) issues `deleteMany({createDate: {$lt: cutoff}})` for mongodb models. |
| connection | One `MongoClient` per registry (`odoo/orm/storage_mongodb.py`, new), URI read from the config key `mongodb_uri` whose value is the environment variable named by the secret `MONGODB_ATLAS_URI`; database name = the single `databases[]` entry of `.migration/allowed_targets.json`. The client is created lazily on first use and never at import time. |

## 2. Entry points that branch

The branch point is always `model._storage == 'mongodb'`; the PostgreSQL branch is the
existing code, unchanged. "store" below means the `MongoStore` object of §1.

| entry point | PostgreSQL today | MongoDB branch |
|---|---|---|
| `_search` (`models.py:4852`) | `Domain.optimize_full` then `Query(self)` + `query.add_where(domain._to_sql(query.table))`; security domain ANDed; `order`→`_order_to_sql`; limit/offset | identical up to `optimize_full` (§3 makes cross-store conditions single-store first). Then `MongoQuery(self)` (`odoo/orm/query.py`, new subclass of `Query` with `filter: dict`, `sort: list`, `limit`, `offset` and no SQL) with `query.add_filter(domain._to_filter(self))`; security domain → `add_filter`; `order`→`_order_to_sort`. The `('id','any!', Query)` shortcut at `:4914-4928` works unchanged (ids only). |
| `_as_query` (`:4944`), `Query.set_result_ids`/`get_result_ids` (`query.py:257`, `:249`) | ids known | identical; `get_result_ids` on a `MongoQuery` runs `find(filter, {_id:1})` once and caches. |
| `search_fetch` (`:1452`), `_fetch_query` (`:3229`) | `execute_query(query.select(*sql_terms))`, `field._insert_cache` | `store.find(filter, projection=[target of each column field], sort, skip, limit)`; rows re-ordered into `(id, col…)` tuples; `_insert_cache` unchanged; `other_fields` (x2many, `Binary(attachment=True)`, `properties`) still go through `field.read`. A field with `compute_sql` but no column (`:3243` assertion) is treated as a non-column field for mongodb models (see §5, compute_sql). |
| `_fetch_field` (`:3077`), `read` (`:2798`), `_read_format` (`:3014`) | cache | unchanged |
| `_create` (`:4347`) | `INSERT … RETURNING "id"` per batch; inverses; `_parent_store_create`; `other_fields` create | id allocation from the shadow table (§4) inside the cursor's transaction, then `store.insert_many([{_id, …}])` through the write buffer (§6); the rest unchanged. `_parent_store_create` (`:4460`) / `_parent_store_update` (`:4519`) / `_parent_store_compute` (`:2423`) compute `parent_path` in Python from the parent document for mongodb models (`product.category`, `uom.uom` carry `parent_path`). |
| `write` (`:3805`), `_write` (`:3993`) → `_write_multi` (`:3997`) | one `UPDATE … FROM (VALUES …)` per field-set; JSONB `CASE` for `translate`, `jsonb_object_agg` for `company_dependent` | one `bulkWrite` of `UpdateOne({_id}, {$set, $unset})` per batch. `translate is True` → `$set` of the dotted path `<field>.<lang>` for each language in the value (a true merge, no read-modify-write). `company_dependent` → `$set`/`$unset` of `<field>.<company_id>`; the fallback comparison done in SQL at `:4056-4066` is done in Python with `ir.default._get_field_column_fallbacks`. |
| `_flush` (`:5859`) → `_write_multi` | | unchanged entry; see §6 for when the buffered writes reach Mongo. |
| `unlink` (`:3658`) | `flush_all`; cleanup of `ir.model.data`/`ir.attachment`/`ir.default` (PostgreSQL models); company-dependent Many2one `UPDATE … jsonb` on referencing tables (`:3731-3788`); `DELETE`; `invalidate_all` | `DELETE FROM <shadow> WHERE id IN %s` first, in the PostgreSQL transaction (FK `RESTRICT`/`SET NULL`/`CASCADE` actions of the 53 inbound FKs fire here, as today), then `store.delete_many({_id: {$in}})` through the buffer. Framework cleanup unchanged (D4). The company-dependent `UPDATE` at `:3758-3786` runs per referencing model in that model's own store (SQL for PostgreSQL models, `$unset <field>.<company>` for mongodb ones). |
| `_read_group` (`:1996`) via `read_group` (`:1932`) | `_search` + `_read_group_select` (`:2087`) / `_groupby` (`:2124`) / `_orderby` (`:2202`) / having → `query.select` | `_search` filter → `$match`; groupby → `$group` on the field, with `day/week/month/quarter/year` as `$dateTrunc` and the integer date parts as `$year`/`$month`/…; aggregates `count`, `count_distinct`, `sum`, `avg`, `min`, `max`, `array_agg`/`recordset`, `bool_and`, `bool_or`; having → `$match` after `$group`; order/limit/offset → `$sort`/`$skip`/`$limit`. Other PostgreSQL aggregate names raise `NotImplementedError` naming the spec. Group values are post-processed by `_read_group_postprocess_*` unchanged. |
| `_auto_init` (`:2506`) | `sql.create_model_table`, `field.update_db`, `_add_sql_constraints` (`:2599`) | `store.ensure_collection(model)` + the collection's `indexes` from `mapping_spec.json` (natural keys unique); create the shadow table (§4) if missing; no `update_db`, no SQL constraints — Python `_check_*` constraints keep running, SQL `models.Constraint`/`models.UniqueIndex` declarations become indexes: plain `UNIQUE(cols)` → unique index; a partial unique index keeps its predicate as `partialFilterExpression` — on the slice `product.product._combination_unique` (`addons/product/models/product_product.py:152-154`, `(product_tmpl_id, combination_indices) WHERE active IS TRUE`) becomes `{productTmplId: 1, combinationIndices: 1}` unique with `partialFilterExpression: {active: true}`, and `uom_uom__relative_uom_id_index` (filtered, census) keeps its predicate; the spec's non-unique `combinationIndices` index is superseded by it (index decision, open item A for `product_product(combination_indices)`). Any other `CHECK`/expression constraint raises at `_auto_init` instead of being logged, so a lost invariant is loud. `init()` (`:2587`) is still called. |
| `_init_column` (`:2491`), `_check_removed_columns` (`:2462`) | SQL | no-op |
| `exists` (`:5037`) | `SELECT id` | `find({_id: {$in}}, {_id: 1})` |
| `_has_cycle` (`:5116`) | recursive SQL | Python walk over the parent field |
| `_field_to_sql` (`:2380`), `_order_to_sql` (`:4735`), `_table_sql` (`:531`), `Query.select`/`subselect` on a `MongoQuery` | SQL | raise `NotImplementedError("<model> is stored in MongoDB; no SQL")`. This is how every unsupported raw-SQL path of §5 surfaces at the first call instead of silently reading an empty shadow. |
| `filtered_domain` (`:5723`), `_validate_fields` (`:1299`), `_check_company` (`:3351`), `_load_records` (`:4619`), `copy_data`, `name_search` | Python / ORM | unchanged |

### `odoo/orm/fields_relational.py`

| field path | PostgreSQL today | MongoDB branch |
|---|---|---|
| `Many2one.update_db` / `update_db_foreign_key` (`:293`, `:303`) | adds the FK column and constraint | model in mongodb: skipped (the field is a document int). Model in PostgreSQL, comodel in mongodb: unchanged — the FK is created against the shadow table, which has the same name and PK (§4). |
| `Many2one.write` / `_update_inverses` (`:397`, `:446`) | cache | unchanged |
| `Many2one.to_sql` (`:463`), `condition_to_sql` (`:483`) | column, `IN (subselect)` or `JOIN` for `any` | `condition_to_filter`: §3 |
| `_RelationalMulti.create`/`write`/`write_batch` (`:793`, `:802`, `:807`) | commands | unchanged (commands are store-agnostic) |
| `_RelationalMulti.condition_to_sql` (`:845`) | `id IN (SELECT inverse …)` / `EXISTS` on the relation | §3 |
| `One2many.update_db` (`:960`), `read` (`:998`), `write_batch` (`:1029`) | inverse column on the comodel; `comodel.search(inverse in ids)`; comodel create/write/unlink | unchanged — a One2many is a search in the *comodel's* store; it works across stores because `records.ids` are integers on both sides. |
| `Many2many.update_db` / `update_db_foreign_keys` (`:1370`, `:1414`) | relation table + FKs | slice relation: skipped (array field on the declaring side). PostgreSQL relation: unchanged (FKs point at the shadow or at a PostgreSQL table). |
| `Many2many.read` (`:1428`) | `comodel._search` + `add_join` on the relation + `id1 IN ids` | slice relation: project the id array from the declaring side's documents, then `comodel.browse(ids)` ordered with one `comodel._search([('id','in', ids)], order=comodel._order)`. PostgreSQL relation with one mongodb side: `SELECT col1, col2 FROM relation WHERE col1 IN %s` then the same ordered browse. |
| `Many2many.write_batch` (`:1457`) | `INSERT`/`DELETE` on the relation | slice relation: `$addToSet`/`$pull`/`$set` on the array (link/unlink/set/clear). PostgreSQL relation: unchanged SQL with integer ids. |
| `TableSQLId` (`:1794`) | SQL id joins | not used for mongodb models |

## 3. Domains on cross-store relational fields: two steps

`Domain._to_sql(table)` (`odoo/orm/domains.py:499`) ends in `field.condition_to_sql`
(`:1171-1182`). The MongoDB branch adds `Domain._to_filter(model)` with the same shape
(`DomainBool`/`DomainNot`/`DomainAnd`/`DomainOr`/`DomainCondition` → `$and`/`$or`/`$nor`,
condition → `field.condition_to_filter(model, field_expr, operator, value)`) and a default
`Field.condition_to_filter` next to `Field.condition_to_sql` (`odoo/orm/fields.py:1419`) for
the scalar operators (`=`/`in`→`$in`, `like` family → anchored `$regex`, `<`… → `$lt`…,
`=?`, `False`/`None` → `{$in: [null, false, '']}` per column type, as the SQL branch does).

Optimization is unchanged: `optimize_full` (`:461`) runs `_optimize_any_domain_at_level`
(`:1432`), which already looks up `comodel = model.env[field.comodel_name]` and optimizes the
sub-domain against the comodel. The storage path adds one rule there, and in
`_optimize_relational_name_search` (`:1517`):

**Rule.** For a relational condition (`any`, `any!`, `not any`, `not any!`, or `in`/`not in`
whose value is a `Query`/`SQL`) where `model._storage != comodel._storage`, or where both are
`'mongodb'` (MongoDB has no cross-collection sub-query without `$lookup`):

1. *Step 1 — resolve in the comodel's store.* `ids = comodel._search(sub_domain,
   active_test=…, bypass_access=bypass_access).get_result_ids()` with exactly the access
   semantics of the SQL branch: `bypass_access` is true only for `any!`/`not any!` or a field
   with `bypass_search_access` (`fields_relational.py:492`, `:859`); a plain `any` runs the
   comodel's `_access_domain` (record rules) like the SQL sub-select does today. No `sudo()`:
   the only `sudo()` kept is the one the SQL branch already uses for the `search_domain`
   restriction (`domains.py:1470`). Context handling as at `domains.py:1446-1449`. The result is bounded: more than `mongodb.cross_store_max_ids` ids
   (`ir.config_parameter`, default `50000`) raises `UserError` naming the field, so an
   unbounded two-step never silently builds a multi-megabyte `$in`.
2. *Step 2 — rewrite into a single-store condition* and let the normal `_to_sql` /
   `_to_filter` of the model's own store run:
   - `Many2one`: `(field, 'in', ids)` / `(field, 'not in', ids)` with the `can_be_null`
     handling of `fields_relational.py:491` kept (`not any` includes `NULL` rows: `$or:
     [{f: null}, {f: {$nin: ids}}]`, like the SQL `OR … IS NULL`).
   - `One2many`: step 1 projects the inverse column (`inverse_name`) instead of `id`;
     step 2 is `('id', 'in', parent_ids)`.
   - `Many2many`, relation in the slice: step 2 is `{<arrayField>: {$in: ids}}` (or
     `$nin`) on the declaring side; when the condition sits on the non-declaring side, the
     declaring side's documents are queried for `{array: {$in: ids}}` and their `_id`s become
     step 2.
   - `Many2many`, relation in PostgreSQL (sale/purchase/stock/account-owned, e.g.
     `product_template_attribute_value_sale_order_line_rel`): step 1 as above; step 1b
     `SELECT col1 FROM relation WHERE col2 IN %s` in PostgreSQL; step 2 `('id', 'in', …)` in
     the model's store. When the model is PostgreSQL and only the comodel is mongodb, step 1b
     and step 2 collapse into the existing `id IN (SELECT … WHERE col2 IN %s)` subselect with
     a literal id list.
   - The `search_domain` restriction at `:1469-1474` (`restricted_domain_sql` using
     `sub_query.subselect`) applies only when both sides share a store; cross-store takes the
     `Domain.TRUE` branch at `:1475`.

Same-store PostgreSQL conditions keep the single SQL sub-select. Record rules (`ir.rule`,
`_access_domain` `:3603`) and `_check_company_domain` (`:3339`) go through the same rule.

## 4. Document key and the id shadow (d-id-key = keep-int-id)

- `_id` = the PostgreSQL integer `id`, copied verbatim at load (every slice collection in
  `mapping_spec.json` has `key.source = [id]`, `key.target = _id`, `bson_type: int`).
- **Shadow table** = the original table, same name, reduced to `id integer PRIMARY KEY
  DEFAULT nextval('<table>_id_seq')` (one per migrated model table; the 13 slice relation
  tables get no shadow — their inbound FKs are from slice models only). Keeping the name and
  the PK means: the 53 inbound FK columns from 36 out-of-scope tables (NOTES.md §A) keep
  their constraints and actions untouched; the ~530 `ir_model_data`/`ir_attachment`/
  `mail_message`/`ir_default` rows keyed `(model, res_id)` (NOTES.md §F) stay valid; the 3 SQL
  views (NOTES.md §E) keep resolving the join key. The column reduction is performed by the
  cutover unit after its recon PASS, never by `_auto_init`.
- **Id allocation**: `_create` runs `INSERT INTO <table> DEFAULT VALUES RETURNING id` (batch
  of `len(data_list)`) in the ORM cursor, then inserts the documents with those `_id`s. The
  sequence `<table>_id_seq` stays the single id authority, so ids are unique across both
  stores and PostgreSQL FKs to the new record are valid in the same transaction.
- **Deletion**: `unlink` deletes the shadow rows first (§2), so `ON DELETE RESTRICT` from
  e.g. `stock_move.product_id` still rejects the delete before any Mongo write.
- **Full shadow (D6 only)**: for the model-only SQL readers that select slice *columns*,
  the shadow table additionally keeps those columns, written through synchronously by the
  storage path (`_create` inserts them, `_write_multi` issues one extra `UPDATE` for the
  shadowed columns that changed, in the same PostgreSQL transaction). The shadowed column
  set is fixed by the readers in §5: `product_product(id, product_tmpl_id, weight, volume,
  standard_price)`, `product_template(id, uom_id, categ_id, is_storable, purchase_method)`,
  `product_category(id, property_cost_method)`, `uom_uom(id, factor)`. Any other column read
  through SQL raises per §2 (`_table_sql`).

### NOTES.md disposition codes → contract mechanism

| code | count (NOTES.md) | mechanism |
|---|---|---|
| D1 `keep-fk-via-id-shadow` | 53 FK columns / 36 tables + 7 One2many inverses | §4 shadow keeps name + PK; join semantics via §3 two-step; `One2many.read` unchanged (§2) |
| D2 `field-travels-with-document` | 47 stored fields (17 company-dependent) + 37 JSONB columns | `_storage` is per model, not per module: every field in `model._fields` with a `column_type` is a document field whatever module registered it. `translate` JSONB → `{<lang>: …}` object, company-dependent JSONB → `{<company_id>: …}` object with `ir.default` fallbacks resolved in Python (§2 `_write_multi`); `properties`/`properties_definition` JSONB → object (`fields_properties.py` stays column-based). No `ir_property`/`ir_translation` tables exist in Odoo 20, so nothing is joined. |
| D3 `reference-out` | 58 Many2one columns | stored as integer document fields; display/prefetch is `comodel.browse(ids)` in the comodel's store (the ORM never joins for a Many2one read); conditions → §3. `_inherits` delegation (`product.document.ir_attachment_id` → `ir_attachment`): `_create :4347` creates the PostgreSQL parent through its own model first, the document stores the int (D3+D4). |
| D4 `framework-stays-pg` | ~530 rows | unchanged PostgreSQL models keyed `(model, res_id)`; `unlink :3658` cleanup paths run as today; `Binary(attachment=True)` (`fields_binary.py:27-63`, `image.mixin`) has no column and stays in `ir_attachment`; `mail.thread.message_ids` is a cross-store One2many (§3). |
| D5 `orm-write-routed` | 5 writers + 4 indirect crons | they call `write()`/`create()`; the branch is below them at `_write_multi`/`_create`. Non-atomicity: §6. |
| D6 `sql-reader-rewrite` | 3 views + 3 `_table_query` + 2 raw SQL | §5 — rewrite when the code is in scope (`addons/product`), full shadow when the reader is in a model-only addon |
| D7 `none-empty-or-uninstalled` | — | no mechanism; the dependency register must be re-run before any further addon is installed (NOTES.md §A note) |

## 5. Unsupported paths and how each NOTES.md item is handled

Unsupported on a mongodb model, by construction (raise at first call, §2): `_table_query`
/ `_auto = False` models over slice tables, SQL views created in `init()` over slice
tables, raw `cr.execute`/`env.execute_query` naming a slice table, `_field_to_sql` /
`compute_sql`, `Query.select`/`subselect`. Rule: **R (rewrite)** when the code is in the
code-migration scope (`addons/product`, `addons/uom`); **S (full shadow, §4)** when the reader
lives in a model-only addon whose code this run does not change; **B (blocked)** when neither
applies.

| NOTES.md item | kind | handling |
|---|---|---|
| `addons/stock/report/report_stock_quantity.py:62-75` PG view (`pp.product_tmpl_id`, `pt.is_storable`, `pt.uom_id`, `uom_move.factor`/`uom_product.factor`) | `_auto = False` view | **S** — needs `product_product(product_tmpl_id)`, `product_template(is_storable, uom_id)`, `uom_uom(factor)` |
| `addons/stock_account/report/stock_avco_audit_report.py:48-72` PG view (`pt.categ_id`, `pt.uom_id`, `pc.property_cost_method`, `um/up.factor`) | view | **S** — adds `product_template(categ_id)`, `product_category(property_cost_method)` |
| `addons/purchase_stock/report/vendor_delay_report.py:29-58` PG view (`pt.uom_id`, `pt.categ_id`, `pt_uom.factor`) | view | **S** — covered by the set above |
| `addons/sale/report/sale_report.py:137-199` (`table.product_id.uom_id.factor`, `.categ_id`, `.product_tmpl_id`, `.weight`, `.volume`) | `_table_query` | **S** — adds `product_product(weight, volume)` |
| `addons/purchase/report/purchase_report.py:61-115` (`.product_tmpl_id.categ_id`, `.uom_id`, `.purchase_method`, `.weight`, `.volume`) | `_table_query` | **S** — adds `product_template(purchase_method)` |
| `addons/account/report/account_invoice_report.py:95-142` (`.uom_id.factor`, `.categ_id`, `.standard_price`) | `_table_query` | **S** — adds `product_product(standard_price)` (company-dependent JSONB; the shadow column keeps the JSONB shape the report reads with `->>`) |
| `addons/account/models/product.py:243-258` `_check_uom_not_in_invoice` (joins `product_product.product_tmpl_id`, `product_template.uom_id`) | raw SQL constraint on every `uom_id` change | **S** — covered; the `flush_model(['uom_id'])` at `:245` must flush the shadow write too (it does: the shadow `UPDATE` is part of `_write_multi`) |
| `addons/stock/__init__.py:46,83-92` `_create_inventory_adjustment` (`SELECT id, qty_available FROM product_product`; `UPDATE product_product SET qty_available`) | raw SQL *write*, install/uninstall hook of `stock` | **B** — installing or uninstalling `stock` while the slice is on MongoDB is blocked (a write to a non-shadowed column would be lost). `stock` is already installed; the block is an operational constraint recorded for cutover, not a run-time path. |
| `addons/purchase/models/purchase_bill_line_match.py:12,119-150` | `_auto = False`, selects only `product_id` ints from PostgreSQL tables | nothing to do (NOTES.md D1) |
| `addons/product/models/product_template.py:403,413` and `product_combo.py:55` `_compute_sql_currency_id` / `_compute_sql_cost_currency_id` | `compute_sql` on in-scope models | **R** — the storage path ignores `compute_sql` for mongodb models (`_fetch_query` treats the field as non-column, the Python compute `_compute_currency_id` runs); a domain on `currency_id`/`cost_currency_id` is rewritten to `('company_id', 'in', companies_with_that_currency)` plus `('company_id', '=', False)` when the value is the main company's currency, resolved per §3 |
| `addons/product/models/product_template.py:960-975` `_search_display_name` (`UNION ALL` of two `_search().select()`) | raw SQL in scope | **R** — return `Domain.OR([domain, [('product_variant_ids', operator, value)]])`; the `UNION` only exists for the PostgreSQL planner |
| `addons/product/models/product_product.py:1128-1145` (`_search(...).subselect(SQL('product_tmpl_id'))`, `UNION ALL` of `query.select()`) | raw SQL in scope | **R** — materialize each branch with `get_result_ids()` and return `[('id', 'in', union_of_ids)]`; the `product.supplierinfo` branch becomes `('product_tmpl_id', 'in', supplierinfo_search.get_result_ids(project='product_tmpl_id'))` |

## 6. Cross-store transactions are non-atomic

PostgreSQL stays the transaction coordinator; MongoDB has no shared transaction with it.

- **Write buffer and visibility.** Mongo writes produced by `_create`/`_write_multi`/`unlink`
  are applied **immediately** when the ORM flushes (`flush_model :5825`, `_flush :5859`,
  `cr.flush()` in `Transaction.committing` `environments.py:935-950`), not deferred to
  commit. Reason: slice code searches right after writing in the same request
  (`product.template._create_variant_ids`, pricelist rule lookups); a deferred write would
  break read-your-writes. Each write is idempotent per `_id` (`$set`/`$setOnInsert`,
  `deleteMany` by `_id`).
- **Rollback compensation.** The `Transaction` keeps an undo log for the cursor: before each
  Mongo update/delete the previous document image is captured
  (`findOneAndUpdate(returnDocument='before')` / `find` before `deleteMany`), inserts are
  logged by `_id`. `cr.prerollback` (`odoo/sql_db.py:260`) replays the log in reverse
  (restore images, delete inserted `_id`s); `cr.postcommit` (`:259`, run at `:565`) discards
  it. The log lives in the Odoo process; if the process dies between a Mongo write and the
  PostgreSQL `COMMIT`, PostgreSQL rolls back and Mongo keeps the write.
- **Repair.** A cron `product_mongodb.repair` (PostgreSQL side, `ir.cron`) deletes documents
  whose `_id` has no shadow row and reports shadow rows without a document; every Mongo write
  carries `writeDate` (already a stored field) so the recon harness can bound the window.
  Savepoints (`cr.savepoint :308`): entering a savepoint records a mark; a savepoint
  *rollback* replays the undo log back to its mark; a successful *release* keeps the entries
  (they merge into the enclosing transaction's log, since PostgreSQL has not committed them).
  The log is discarded only in `cr.postcommit`, after the PostgreSQL `COMMIT` succeeded.
- **The 5 ORM writers (NOTES.md §D)** and what non-atomicity means for each:

| writer | stores touched in one request | failure window and consequence |
|---|---|---|
| `stock_account/models/product.py:194-247` `_change_standard_price` (also from cron `_cron_post_stock_valuation`) | Mongo: `product.product.standard_price` (company-dependent); PostgreSQL: `account.move` + `stock.valuation.layer` | PostgreSQL rollback after the Mongo write → undo log restores the old price; process death in the window → price changed without the revaluation entry until repair. Recon scenario: price change + posted move, both stores asserted. |
| `stock_account/models/product.py:727-747` `lot_valuated` toggle | Mongo: `product.template.lot_valuated`; PostgreSQL: valuation layers per lot | same pattern; the toggle is idempotent, so a repair re-run of the request is safe. |
| `stock/models/product.py:1054-1061` `_set_store_by` (`is_storable`, `tracking`) | Mongo write; PostgreSQL only read (`stock.quant`/`stock.move.line` existence checks) | one store written → atomic in practice. `is_storable` is a full-shadow column (§4), written in the same PostgreSQL transaction as the checks. |
| `account/models/product.py:307-311` `write` clearing `taxes_id`/`supplier_taxes_id` on combos | PostgreSQL only: `product_taxes_rel`/`product_supplier_taxes_rel` are account-owned relation tables (D1) | atomic in PostgreSQL; no Mongo write. |
| `purchase/models/res_partner.py:66` `supplierinfo.currency_id` on partner currency change | PostgreSQL: `res_partner.property_purchase_currency_id`; Mongo: `product.supplierinfo.currency_id` | partner saved, supplierinfo not (or the reverse after a rollback without undo) → undo log covers the rollback case; repair cron covers process death. Recon scenario: partner currency change, supplierinfo currency asserted. |

Unit/recon rule that follows: every scenario that exercises a D5 writer asserts both stores
after `COMMIT` (harness tier 4), and the recon window excludes the repair cron's lag.

## 7. What the storage-path ticket builds (checklist)

1. `odoo/orm/storage_mongodb.py` (`MongoStore`: client, `find`, `aggregate`, `insert_many`,
   `bulk_write`, `delete_many`, `ensure_collection`, undo log, shadow id allocation).
2. `_storage` attribute and registry bookkeeping (§1); `product_mongodb` addon setting
   `_storage = 'mongodb'` on the 20 models and registering the repair cron.
3. `MongoQuery`, `Domain._to_filter`, `Field.condition_to_filter`, relational
   `condition_to_filter` + the two-step rule in `domains.py` (§3).
4. The branches of §2 in `models.py`, `models_transient.py`, `fields_relational.py`,
   `fields.py` (`convert_to_document` = `convert_to_column` without SQL wrapping; BSON types
   per `mapping_spec.json` `bson_type`: `NUMERIC`→`decimal`, `TIMESTAMP`→`date` (UTC,
   millisecond truncation is the profile's known incompatibility), `JSONB`→`object`,
   `BOOLEAN`→`bool`).
5. The three **R** rewrites of §5 in `addons/product`, and the shadow column set of §4.
6. Tests: the existing `odoo/addons/base/tests` ORM tests run against the slice with
   `_storage = 'mongodb'` on a local Mongo (`docker-compose.local.yml` of the plugin), plus
   one test per row of §3 and §6.

Out of scope here: data load and recon (unit-migration tickets), cutover column reduction,
any change under `addons/sale`, `addons/purchase`, `addons/stock`, `addons/account`.
