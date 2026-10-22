# odoo-bin shell stdin script for the s2.3 register, run on a throwaway clone of odoo_src
# (never on odoo_src itself): prints JSON with every registry model's table and storage flags,
# and the SQL that each _auto = False model selects from (_table_sql / _table_query rendered
# with mogrify; init() views are read from pg_views by register_db.py instead).
import json
import os
out = {"models": {}, "table_sql": {}}
for name, model in sorted(env.registry.items()):
    out["models"][name] = {"table": model._table, "abstract": model._abstract,
                           "transient": model._transient, "auto": model._auto}
    if model._abstract or model._auto:
        continue
    rec = env[name].sudo()
    for attr in ("_table_query", "_table_sql"):
        try:
            value = getattr(rec, attr, None)
        except Exception as e:  # noqa: BLE001 — record why a report cannot render
            out["table_sql"][name] = {"attr": attr, "error": repr(e)[:300]}
            break
        if value:
            text = env.cr.mogrify(value).decode() if not isinstance(value, str) else value
            out["table_sql"][name] = {"attr": attr, "sql": text}
            break
env.cr.rollback()
with open(os.environ["REGISTER_PROBE_OUT"], "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
