"""Seed the scenario rows of batch w1-b01 (unit stock-reference) on the worker's own PostgreSQL clone.

Run it through the pre-opt-in source tree (the SOURCE_COMMIT worktree build_source.sh keeps at
../odoo-unt12-src), so every write lands on PostgreSQL and the clone stays a plain source:

    /home/ubuntu/.venvs/odoo/bin/python ../odoo-unt12-src/odoo-bin shell -d <clone> --db_port=5433 \\
        --no-http < .migration/load/seed_scenario_rows.py

1. Deactivates the six cron writers of NOTES.md s2.3 §1 (ids 19-23 and 1) on the clone, as every
   load or recon requires.
2. stock_scrap_reason_tag has 0 fixture rows (units.json recon_unverified): seeds three tags with
   create_date/write_date pinned to FIXED_INSTANT (the build_source.sh instant), so a verifier
   reseeding its own clone gets identical rows and recon grades the collection.
Idempotent: an already seeded clone only gets the cron step again.
"""
FIXED_INSTANT = '2026-10-20 00:00:00'
CRON_IDS = [1, 19, 20, 21, 22, 23]
TAGS = [
    {'name': 'Damaged in transit', 'sequence': 10, 'color': 1},
    {'name': 'Expired', 'sequence': 20, 'color': 5},
    {'name': 'Quality check failed', 'sequence': 5},  # default color
]

crons = env['ir.cron'].browse(CRON_IDS).exists()
assert set(crons.ids) == set(CRON_IDS), f"cron ids on this clone: {crons.ids}"
crons.write({'active': False})
print(f"crons deactivated: {sorted(crons.ids)}")

Tag = env['stock.scrap.reason.tag']
if Tag.search_count([]):
    print(f"stock.scrap.reason.tag already seeded: {Tag.search_count([])} rows")
else:
    tags = Tag.create(TAGS)
    tags.flush_recordset()
    env.cr.execute(
        "UPDATE stock_scrap_reason_tag SET create_date = %s, write_date = %s WHERE id IN %s",
        (FIXED_INSTANT, FIXED_INSTANT, tuple(tags.ids)),
    )
    print(f"stock.scrap.reason.tag seeded: ids {tags.ids}")
env.cr.commit()
env.cr.execute("SELECT id, name->>'en_US', sequence, color, create_date FROM stock_scrap_reason_tag ORDER BY id")
for row in env.cr.fetchall():
    print(row)
