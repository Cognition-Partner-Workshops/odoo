"""Seed the scenario rows of batch w1-b03 (unit uom-packaging) on the worker's own PostgreSQL clone.

Run it through the pre-opt-in source tree (the SOURCE_COMMIT worktree build_source.sh keeps at
../odoo-unt12-src), so every write lands on PostgreSQL and the clone stays a plain source:

    /home/ubuntu/.venvs/odoo/bin/python ../odoo-unt12-src/odoo-bin shell -d <clone> --db_port=5433 \\
        --no-http < .migration/load/seed_uom_packaging.py

1. Deactivates the six cron writers of NOTES.md s2.3 §1 (ids 19-23 and 1) on the clone, as every
   load or recon requires.
2. Both junction arrays of stockPackageType have 0 fixture rows (units.json recon_unverified):
   seeds one package type linked to warehouse0's reception and delivery routes (stockRouteRel) and
   one putaway rule on warehouse0's stock location that applies to it and to the fixture's Pallet
   (stockPutawayRuleRel), create_date/write_date pinned to FIXED_INSTANT (the build_source.sh
   instant), so a verifier reseeding its own clone gets identical rows and recon grades both embeds.
Idempotent: an already seeded clone only gets the cron step again.
"""
FIXED_INSTANT = '2026-10-20 00:00:00'
CRON_IDS = [1, 19, 20, 21, 22, 23]
TOTE = {
    'name': 'Seeded tote', 'barcode': 'TOTE-SEED', 'package_use': 'reusable', 'sequence': 5,
    'height': 30.0, 'width': 40.0, 'packaging_length': 60.0, 'base_weight': 1.5, 'max_weight': 25.0,
}

crons = env['ir.cron'].browse(CRON_IDS).exists()
assert set(crons.ids) == set(CRON_IDS), f"cron ids on this clone: {crons.ids}"
crons.write({'active': False})
print(f"crons deactivated: {sorted(crons.ids)}")

PackageType = env['stock.package.type']
warehouse = env.ref('stock.warehouse0')
pallet = env.ref('stock.package_type_01')
if PackageType.search_count([('barcode', '=', TOTE['barcode'])]):
    print(f"stock.package.type already seeded: {PackageType.search_read([('barcode', '=', TOTE['barcode'])], ['id', 'route_ids'])}")
else:
    routes = warehouse.reception_route_id | warehouse.delivery_route_id
    tote = PackageType.create(dict(TOTE, route_ids=[(6, 0, routes.ids)]))
    rule = env['stock.putaway.rule'].create({
        'company_id': warehouse.company_id.id,
        'location_in_id': warehouse.lot_stock_id.id,
        'location_out_id': warehouse.lot_stock_id.id,
        'package_type_ids': [(6, 0, (pallet | tote).ids)],
    })
    env.flush_all()
    env.cr.execute(
        "UPDATE stock_package_type SET create_date = %s, write_date = %s WHERE id = %s",
        (FIXED_INSTANT, FIXED_INSTANT, tote.id),
    )
    print(f"stock.package.type seeded: id {tote.id}, routes {routes.ids}; stock.putaway.rule {rule.id} -> package types {(pallet | tote).ids}")
env.cr.commit()
env.cr.execute("SELECT stock_package_type_id, stock_route_id FROM stock_package_type_stock_route_rel ORDER BY 1, 2")
print("stock_package_type_stock_route_rel:", env.cr.fetchall())
env.cr.execute("SELECT stock_package_type_id, stock_putaway_rule_id FROM stock_package_type_stock_putaway_rule_rel ORDER BY 1, 2")
print("stock_package_type_stock_putaway_rule_rel:", env.cr.fetchall())
