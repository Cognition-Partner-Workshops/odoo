store = env.registry.mongo_store
print('STORE prefix', repr(store.collection_prefix))
for name in ('uom.uom','product.category','product.attribute','product.template','product.product','product.pricelist','product.pricelist.item','product.supplierinfo','product.combo','product.label.layout','stock.quant','stock.move','purchase.order'):
    Model = env[name].sudo().with_context(active_test=False)
    try:
        docs = store.db[store.collection_name(Model)].estimated_document_count()
    except Exception as e:  # noqa: BLE001
        docs = f'n/a ({type(e).__name__})'
    try:
        env.cr.execute(f'SELECT count(*) FROM {Model._table}'); row = env.cr.fetchone(); shadow = row[0] if row else 'intercepted'
    except Exception as e:  # noqa: BLE001
        env.cr.rollback(); shadow = f'n/a ({type(e).__name__})'
    print('FRESH', name, 'orm', Model.search_count([]), 'docs', docs, 'pg_shadow', shadow)
print('MODULES', {m.name: m.state for m in env['ir.module.module'].search([('name','in',['stock','purchase_stock','product','uom','sale','account'])])})
