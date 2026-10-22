"""Read-only odoo_src facts for the s2.3 dependency register (run on the frozen source).

Checks the row-count fingerprint against .migration/source_fingerprint.json first and exits 2
on a mismatch. Then dumps installed modules, ir_cron jobs with their server-action code,
server actions whose code touches the cursor, public views/matviews with the base tables they
read, non-internal triggers, public functions and every foreign key, as JSON on stdout.
Run (JSON secret bound to ODOO_PG_RO_DSN, read-only session):
  PYTHONPATH=<plugin>/skills/mongo-recon-harness/harness python .migration/register_db.py > db.json
"""
import hashlib
import json
import os
import pathlib
import sys

import psycopg
from psycopg import sql
from recon.adapters import parse_postgresql_secret

FINGERPRINT = pathlib.Path(__file__).resolve().parent / "source_fingerprint.json"


def main():
    want = json.loads(FINGERPRINT.read_text())["row_counts_sha256"]
    with psycopg.connect(**parse_postgresql_secret(os.environ["ODOO_PG_RO_DSN"])) as conn:
        conn.read_only = True
        q = lambda text, *a: conn.execute(text, a).fetchall()
        tables = sorted(r[0] for r in q(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"))
        lines = "".join(
            "%s\t%d\n" % (t, conn.execute(sql.SQL("SELECT count(*) FROM {}").format(
                sql.Identifier(t))).fetchone()[0]) for t in tables)
        got = hashlib.sha256(lines.encode()).hexdigest()
        if got != want:
            print("fingerprint mismatch: %s != %s" % (got, want), file=sys.stderr)
            sys.exit(2)
        out = {"row_counts_sha256": got, "table_count": len(tables)}
        out["installed_modules"] = sorted(r[0] for r in q(
            "SELECT name FROM ir_module_module WHERE state = 'installed'"))
        out["crons"] = [dict(zip(
            ("id", "name", "active", "interval_number", "interval_type", "model", "state",
             "code", "xmlid"), r)) for r in q(
            "SELECT c.id, c.cron_name, c.active, "
            "c.interval_number, c.interval_type, m.model, a.state, a.code, "
            "(SELECT d.module || '.' || d.name FROM ir_model_data d "
            " WHERE d.model = 'ir.cron' AND d.res_id = c.id ORDER BY 1 LIMIT 1) "
            "FROM ir_cron c JOIN ir_act_server a ON a.id = c.ir_actions_server_id "
            "JOIN ir_model m ON m.id = a.model_id ORDER BY c.id")]
        out["server_actions_cursor"] = [dict(zip(("id", "model", "code"), r)) for r in q(
            "SELECT a.id, m.model, a.code FROM ir_act_server a JOIN ir_model m "
            "ON m.id = a.model_id WHERE a.state = 'code' "
            "AND (a.code ~ '\\mcr\\.' OR a.code ~ 'execute') "
            "AND a.id NOT IN (SELECT ir_actions_server_id FROM ir_cron) ORDER BY a.id")]
        out["views"] = [dict(zip(("name", "kind", "reads"), r)) for r in q(
            "SELECT v.relname, v.relkind, coalesce(array_agg(DISTINCT t.relname) "
            "FILTER (WHERE t.relname IS NOT NULL), '{}') FROM pg_class v "
            "JOIN pg_namespace n ON n.oid = v.relnamespace AND n.nspname = 'public' "
            "LEFT JOIN pg_rewrite w ON w.ev_class = v.oid "
            "LEFT JOIN pg_depend d ON d.objid = w.oid AND d.classid = 'pg_rewrite'::regclass "
            "LEFT JOIN pg_class t ON t.oid = d.refobjid AND t.oid <> v.oid AND t.relkind = 'r' "
            "WHERE v.relkind IN ('v', 'm') GROUP BY v.relname, v.relkind ORDER BY 1")]
        out["triggers"] = [dict(zip(("table", "name", "function"), r)) for r in q(
            "SELECT c.relname, t.tgname, p.proname FROM pg_trigger t "
            "JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_proc p ON p.oid = t.tgfoid "
            "WHERE NOT t.tgisinternal ORDER BY 1, 2")]
        out["functions"] = [dict(zip(("name", "kind", "language"), r)) for r in q(
            "SELECT p.proname, p.prokind, l.lanname FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public' "
            "JOIN pg_language l ON l.oid = p.prolang "
            "WHERE NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = p.oid "
            "AND d.deptype = 'e') ORDER BY 1")]
        out["foreign_keys"] = [dict(zip(("name", "table", "columns", "ref_table", "on_del"), r))
                               for r in q(
            "SELECT k.conname, c.relname, array_agg(a.attname ORDER BY a.attnum), "
            "f.relname, k.confdeltype FROM pg_constraint k "
            "JOIN pg_class c ON c.oid = k.conrelid JOIN pg_class f ON f.oid = k.confrelid "
            "JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = ANY (k.conkey) "
            "WHERE k.contype = 'f' GROUP BY k.conname, c.relname, f.relname, k.confdeltype "
            "ORDER BY 2, 1")]
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=str)


if __name__ == "__main__":
    main()
