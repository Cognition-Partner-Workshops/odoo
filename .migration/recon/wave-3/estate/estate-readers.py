# Seven D6 readers of the full estate, counted through the ORM (search_count([])), same as the baseline.
for model in ('sale.report', 'purchase.report', 'account.invoice.report', 'purchase.bill.line.match',
              'report.stock.quantity', 'stock.avco.report', 'vendor.delay.report'):
    try:
        print('READER', model, env[model].search_count([]))
    except Exception as e:  # noqa: BLE001
        print('READER', model, 'ERROR', type(e).__name__, str(e)[:200])
store = env.registry.mongo_store
print('STORE prefix', repr(store.collection_prefix))
for name in ('product.combo', 'product.combo.item', 'product.template', 'product.product'):
    Model = env[name]
    print('COUNT', name, 'orm', Model.sudo().with_context(active_test=False).search_count([]),
          'docs', store.db[store.collection_name(Model)].estimated_document_count())
    env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (Model._table,))
    print('SHADOW', Model._table, [r[0] for r in env.cr.fetchall()])
combos = env['product.combo'].sudo().search([], order='sequence, id')
print('COMBOS', [(c.id, c.name, c.company_id.id or None, c.currency_id.name, c.combo_item_count, round(c.base_price, 2)) for c in combos])
