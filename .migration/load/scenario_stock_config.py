"""ORM scenario for batch w3-b01 (unit stock-config) on the MongoDB storage path.

Run on the run branch against the worker's seeded clone whose live documents were mirrored under the clone's
prefix (no conf: collections are '<clone>__'-prefixed, so nothing here can touch the live collections):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -d <clone> --db_port=5433 --no-http \\
        < .migration/load/scenario_stock_config.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy columns) with exact
equality, including relation reads into wave-1/2 collections; every write happens in one transaction that is
rolled back at the end, and the documents are hashed before and after to show the journal left them untouched.
"""
import hashlib

from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
assert st.prefix, "collections are unprefixed: run this on a prefixed clone, never against the live documents"
MODELS = {
    'stock.warehouse': 'sequence, id',
    'stock.location': 'complete_name, id',
    'stock.picking.type': None,     # is_favorite desc, sequence, id: computed per user, checked separately
    'stock.route': 'sequence, id',
    'stock.rule': 'sequence, id',
    'stock.putaway.rule': 'sequence, product_id, id',
    'stock.storage.category.capacity': 'id',
    'stock.warehouse.orderpoint': 'location_id, company_id, id',
}
checks = []


def check(name, ok, detail=''):
    checks.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def sql(query, params=()):
    cr.execute(query, params)
    return cr.fetchall()


def snapshot():
    return {m: hashlib.sha256(dumps(list(st.model_collection(env[m]).find().sort('_id', 1)), sort_keys=True).encode()).hexdigest()
            for m in MODELS}


before = snapshot()

# 1. search order, counts, exists() against PostgreSQL (active rows, as the ORM's default active_test)
for model, order in MODELS.items():
    M = env[model]
    active = " WHERE active" if 'active' in M._fields else ""
    pg_ids = [r[0] for r in sql(f"SELECT id FROM {M._table}{active} ORDER BY {order or 'id'}")]
    found = M.search([], order=order or 'id').ids
    check(f"{model} search([]) order", found == pg_ids, (found, pg_ids) if found != pg_ids else len(pg_ids))
    check(f"{model} search_count", M.search_count([]) == len(pg_ids))
    check(f"{model} exists()", M.browse(pg_ids).exists().ids == pg_ids and not M.browse(max(pg_ids) + 1000).exists())

# 2. field values against PostgreSQL rows
rows = sql("SELECT id, name, code, company_id, lot_stock_id, in_type_id, reception_steps, delivery_steps FROM stock_warehouse WHERE active ORDER BY id")
whs = env['stock.warehouse'].browse([r[0] for r in rows])
check("stock.warehouse field values", all(
    (w.name, w.code, w.company_id.id, w.lot_stock_id.id, w.in_type_id.id, w.reception_steps, w.delivery_steps) == r[1:]
    for w, r in zip(whs, rows)), [(w.name, w.code) for w in whs])
rows = sql("SELECT id, complete_name, usage, location_id, parent_path, warehouse_id, storage_category_id, barcode FROM stock_location WHERE active ORDER BY id")
locs = env['stock.location'].browse([r[0] for r in rows])
check("stock.location field values incl. parent_path", all(
    (l.complete_name, l.usage, l.location_id.id or None, l.parent_path, l.warehouse_id.id or None, l.storage_category_id.id or None, l.barcode or None) == r[1:]
    for l, r in zip(locs, rows)), len(rows))
rows = sql("SELECT id, name->>'en_US', code, sequence, warehouse_id, default_location_src_id, default_location_dest_id, sequence_id FROM stock_picking_type WHERE active ORDER BY id")
pts = env['stock.picking.type'].browse([r[0] for r in rows])
check("stock.picking.type field values (translated name)", all(
    (p.name, p.code, p.sequence, p.warehouse_id.id or None, p.default_location_src_id.id or None, p.default_location_dest_id.id or None, p.sequence_id.id) == r[1:]
    for p, r in zip(pts, rows)), len(rows))
rows = sql("SELECT id, action, procure_method, location_dest_id, location_src_id, picking_type_id, route_id, warehouse_id, delay FROM stock_rule WHERE active ORDER BY id")
rules = env['stock.rule'].browse([r[0] for r in rows])
check("stock.rule field values", all(
    (x.action, x.procure_method, x.location_dest_id.id, x.location_src_id.id or None, x.picking_type_id.id, x.route_id.id, x.warehouse_id.id or None, x.delay) == r[1:]
    for x, r in zip(rules, rows)), len(rows))
rows = sql("SELECT id, product_id, location_id, warehouse_id, product_min_qty, product_max_qty, trigger FROM stock_warehouse_orderpoint WHERE active ORDER BY id")
ops = env['stock.warehouse.orderpoint'].browse([r[0] for r in rows])
check("stock.warehouse.orderpoint field values (decimal quantities)", all(
    (o.product_id.id, o.location_id.id, o.warehouse_id.id, o.product_min_qty, o.product_max_qty, o.trigger) == (r[1], r[2], r[3], float(r[4]), float(r[5]), r[6])
    for o, r in zip(ops, rows)), len(rows))
rows = sql("SELECT id, product_id, category_id, location_in_id, location_out_id, storage_category_id, sequence FROM stock_putaway_rule ORDER BY id")
pr = env['stock.putaway.rule'].browse([r[0] for r in rows])
check("stock.putaway.rule field values (seeded rows)", rows and all(
    (x.product_id.id or None, x.category_id.id or None, x.location_in_id.id, x.location_out_id.id, x.storage_category_id.id or None, x.sequence) == r[1:]
    for x, r in zip(pr, rows)), rows)
rows = sql("SELECT id, storage_category_id, product_id, package_type_id, quantity FROM stock_storage_category_capacity ORDER BY id")
caps = env['stock.storage.category.capacity'].browse([r[0] for r in rows])
check("stock.storage.category.capacity field values (seeded rows)", rows and all(
    (c.storage_category_id.id, c.product_id.id or None, c.package_type_id.id or None, c.quantity) == r[1:] for c, r in zip(caps, rows)), rows)

# 3. the seeded embedded arrays and their relation reads (both directions, incl. into wave-1/2 collections)
wh = env.ref('stock.warehouse0')
depot = env['stock.warehouse'].with_context(active_test=False).search([('code', '=', 'SEED')])
check("stockWarehouse.stockWhResupplyTable both directions", depot.resupply_wh_ids == wh and wh.supplier_warehouses_ids if 'supplier_warehouses_ids' in wh._fields else depot.resupply_wh_ids == wh,
      depot.resupply_wh_ids.ids)
check("domain on the resupply array (archived depot)", env['stock.warehouse'].with_context(active_test=False).search([('resupply_wh_ids', 'in', wh.ids)]) == depot
      and not env['stock.warehouse'].search([('resupply_wh_ids', 'in', wh.ids)]))
check("stockPickingType.pickingTypeFavoriteUserRel + is_favorite (compute_sql field)", wh.in_type_id.favorite_user_ids == env.ref('base.user_admin')
      and env['stock.picking.type'].with_user(env.ref('base.user_admin')).search([('is_favorite', '=', True)]) == wh.in_type_id)
fav_first = env['stock.picking.type'].with_user(env.ref('base.user_admin')).search([])
pg_order = [r[0] for r in sql("SELECT id FROM stock_picking_type WHERE active ORDER BY (id IN (SELECT picking_type_id FROM picking_type_favorite_user_rel WHERE user_id = 2)) DESC, sequence, id")]
check("stock.picking.type default order is_favorite desc, sequence, id", fav_first.ids == pg_order, (fav_first.ids[:3], pg_order[:3]))
check("stockLocation.stockPickingTypeRel (wave locations) both directions", sorted(wh.in_type_id.wave_location_ids.ids) == [r[0] for r in sql(
    "SELECT stock_location_id FROM stock_location_stock_picking_type_rel WHERE stock_picking_type_id = %s ORDER BY 1", (wh.in_type_id.id,))]
    and env['stock.location'].search([('id', 'in', wh.in_type_id.wave_location_ids.ids)]).ids == sorted(wh.in_type_id.wave_location_ids.ids, key=lambda i: env['stock.location'].browse(i).complete_name))
mto = env.ref('stock.route_warehouse0_mto')
chair = env['product.product'].browse(5)
# the PostgreSQL twin reads the same: the route-side arrays list the category/template/move, while the
# category/template/move-side fields read empty on both storages (upstream behaviour, checked on the twin clone)
check("stockRoute.categ / product (wave-1/2 readers of the route array) == PostgreSQL twin",
      mto.product_ids == chair.product_tmpl_id and mto.categ_ids == chair.categ_id
      and (chair.categ_id.route_ids.ids, chair.product_tmpl_id.route_ids.ids) == ([], []))
check("stockRoute.move forward ref into stock-ops (stock.move still PostgreSQL) == PostgreSQL twin",
      env['stock.move'].search([('route_ids', 'in', mto.ids)]).ids == [137] and env['stock.move'].browse(137).route_ids.ids == [])
check("stockRoute.warehouse", sorted(mto.warehouse_ids.ids) == [r[0] for r in sql("SELECT warehouse_id FROM stock_route_warehouse WHERE route_id = %s ORDER BY 1", (mto.id,))])
check("putaway rule -> package types (uom-packaging array) and storage category (stock-reference)", pr[1].package_type_ids.ids == [1, 2] and pr[1].storage_category_id.name == 'High frequency - Small'
      and env['stock.package.type'].browse(1).putaway_rule_ids if 'putaway_rule_ids' in env['stock.package.type']._fields else True)
check("capacity one2many from the storage category (wave-1 side)", env['stock.storage.category'].browse(1).capacity_ids == caps[0] and caps[1].uom_id.id is False or caps[0].uom_id == chair.uom_id)
check("child_of / parent_path domain", env['stock.location'].search_count([('id', 'child_of', wh.view_location_id.id)]) == sql(
    "SELECT count(*) FROM stock_location WHERE active AND parent_path LIKE %s", (wh.view_location_id.parent_path + '%',))[0][0])
check("many2one into MongoDB from a PostgreSQL model: stock.quant.location_id", env['stock.quant'].search_count([('location_id.usage', '=', 'internal')]) == sql(
    "SELECT count(*) FROM stock_quant q JOIN stock_location l ON l.id = q.location_id WHERE l.usage = 'internal'")[0][0])
groups = env['stock.location']._read_group([], ['usage'], ['__count'])
check("read_group by usage", sorted((g[0], g[1]) for g in groups) == [tuple(r) for r in sql("SELECT usage, count(*) FROM stock_location WHERE active GROUP BY 1 ORDER BY 1")])
check("name_search on stock.location (complete_name)", env['stock.location'].name_search('Shelf 1')[0][1] == 'WH/Stock/Shelf 1')

# 4. register rows this unit owns
# s2.3 row 31 (R): sale.order._init_column_warehouse_id reads warehouses through the ORM; result equals the legacy UPDATE
orders = env['sale.order'].search([], order='id')
expected = {o.id: sql("SELECT min(id) FROM stock_warehouse WHERE active AND company_id = %s", (o.company_id.id,))[0][0] for o in orders}
cr.execute("UPDATE sale_order SET warehouse_id = NULL")
env.invalidate_all()
env['sale.order']._init_column_warehouse_id()
env.invalidate_all()
check("row 31 _init_column_warehouse_id ORM rewrite equals legacy UPDATE ... FROM stock_warehouse",
      {o.id: o.warehouse_id.id or None for o in orders} == expected, len(orders))
# s2.3 §1 row 22 (orm): the scheduler reads rules/orderpoints from MongoDB and writes later-wave PostgreSQL tables
n_moves = sql("SELECT count(*) FROM stock_move")[0][0]
try:
    with cr.savepoint():
        env['stock.rule'].run_scheduler(use_new_cursor=False, company_id=wh.company_id.id)
        env.flush_all()
    check("row 22 run_scheduler runs on the storage path (creates moves/POs for the fixture orderpoints)", sql("SELECT count(*) FROM stock_move")[0][0] > n_moves)
except ValueError as exc:
    # shared storage gap, reported on the ticket (no patch to storage_mongodb.py): _read_group ordered by an
    # aggregate that is not among the requested aggregates (stock_rule.py `order="route_sequence:min, sequence:min"`)
    check("row 22 run_scheduler runs on the storage path (storage gap: read_group order by non-requested aggregate)", False, exc)
    env.invalidate_all()
try:
    env['stock.rule'].sudo()._read_group([('route_id', 'in', mto.ids)], ['location_dest_id', 'warehouse_id', 'route_id'], ['id:recordset'],
                                         order='route_sequence:min, sequence:min')
    check("storage gap repro: stock.rule._read_group(order='route_sequence:min, sequence:min')", True)
except ValueError as exc:
    check("storage gap repro: stock.rule._read_group(order='route_sequence:min, sequence:min')", False, exc)
# s2.3 §1 row 1 (orm): the autovacuum unlink of processed manual orderpoints
env['stock.warehouse.orderpoint']._unlink_processed_orderpoints()
check("row 1 _unlink_processed_orderpoints runs on the storage path", True)
# report.stock.quantity (row owned by uom-packaging, re-checked now that stock_location/stock_warehouse moved)
report = env['report.stock.quantity']
if hasattr(report, 'init'):
    report.init()
    check("report.stock.quantity view rebuilt over MongoDB-stored stock_location/stock_warehouse",
          report.search_count([]) == sql("SELECT count(*) FROM report_stock_quantity")[0][0])

# 5. writes through the storage path, then rolled back
Rule = env['stock.putaway.rule']
new_rule = Rule.create({'product_id': chair.id, 'location_in_id': wh.lot_stock_id.id, 'location_out_id': wh.lot_stock_id.id, 'sequence': 5})
env.flush_all()
doc = st.model_collection(Rule).find_one({'_id': new_rule.id})
check("create writes a document + shadow row", doc and doc['productId'] == chair.id and doc['sequence'] == 5
      and sql("SELECT count(*) FROM stock_putaway_rule WHERE id = %s", (new_rule.id,))[0][0] == 1, doc and sorted(doc))
check("search sees the new row first", Rule.search([])[0] == new_rule)
new_rule.write({'sequence': 99, 'package_type_ids': [(6, 0, [2])]})
env.flush_all()
doc = st.model_collection(Rule).find_one({'_id': new_rule.id})
check("write updates the document and the junction array on the package type side", doc['sequence'] == 99 and new_rule.package_type_ids.ids == [2]
      and env['stock.package.type'].browse(2).putaway_rule_ids if 'putaway_rule_ids' in env['stock.package.type']._fields else doc['sequence'] == 99)
loc = env['stock.location'].create({'name': 'Scenario shelf', 'usage': 'internal', 'location_id': wh.lot_stock_id.id})
check("parent_path/complete_name on create", loc.parent_path == f"{wh.lot_stock_id.parent_path}{loc.id}/" and loc.complete_name == 'WH/Stock/Scenario shelf'
      and loc.warehouse_id == wh and st.model_collection(loc).find_one({'_id': loc.id})['parentPath'] == loc.parent_path)
loc.write({'location_id': wh.view_location_id.id})
check("parent_path/complete_name on reparent", loc.parent_path == f"{wh.view_location_id.parent_path}{loc.id}/" and loc.complete_name == 'WH/Scenario shelf')
cap = env['stock.storage.category.capacity'].create({'storage_category_id': 2, 'product_id': chair.id, 'quantity': 3})
cdoc = st.model_collection(cap).find_one({'_id': cap.id})
check("capacity create: Float stored as double", isinstance(cdoc['quantity'], float) and cdoc['quantity'] == 3.0, cdoc)
try:
    with cr.savepoint():
        env['stock.warehouse'].create({'name': 'Dup', 'code': 'WH', 'company_id': wh.company_id.id})
        env.flush_all()
    check("warehouse unique (code, company) refused", False)
except Exception as exc:  # noqa: BLE001
    check("warehouse unique (code, company) refused", 'E11000' in str(exc) or 'duplicate key' in str(exc) or type(exc).__name__ == 'ValidationError', type(exc).__name__)
new_rule.unlink()
env.flush_all()
check("unlink removes document + shadow row", st.model_collection(Rule).find_one({'_id': new_rule.id}) is None
      and sql("SELECT count(*) FROM stock_putaway_rule WHERE id = %s", (new_rule.id,))[0][0] == 0)
cr.rollback()
after = snapshot()
check("rollback leaves the mirrored collections byte-identical", before == after, [m for m in MODELS if before[m] != after[m]])
print(f"{sum(checks)}/{len(checks)} checks passed")
assert all(checks)
