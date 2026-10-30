# UNT15 migration notes

Run: Odoo (`mongo-run/unt15`, cut from `mongo-run/unt13`) from local read-only PostgreSQL `odoo_src` to Atlas database `odoo_unt15`, bounded to wave-1 close. Plugin pinned in `plugin_sha`.

## Run findings (not plugin gaps)

- Runtime `SPEC_SHA256` still pins the UNT14 spec; rebound at `s3.2-storage-path` after schema sign-off (`g-model-accepted`). No installed application model opts into MongoDB before then; the draft is not a signed runtime spec. The MongoDB-stored models in `test_orm_mongodb` would hit the stale pin, so that suite remains red until `s3.2` re-signs the spec; it was not run for this modeling ticket.
- `build_fixture.py` filters `bucket == 'in_scope'`; UNT15 `table_buckets.json` carries raw proposer buckets, fixture ticket maps `root_collection` + `embedded` to its scope.
- Base branch `mongo-run/unt13` carried the finished UNT14 migration code (50 `_storage = 'mongodb'` opt-ins, database literal `odoo_unt13`). Reset in PR #165 (Dhrov's option 1): opt-ins removed, storage-path mechanism kept, `storage_mongodb.DATABASE` read from `allowed_targets.json`.
- Board UNT15O was created as a plain board (identifier UNT15 was taken), so there is no Plan view; `plan.yaml` is committed here and decisions are taken in the manager session chat.
- Source secret: the auto-injected org copy of `ODOO_PG_RO_DSN` is a URL; `build_source.sh` and the probe need the JSON form (personal copy, bound explicitly).
- Frozen source: `odoo_ro` is SELECT-only (no superuser, no non-SELECT grants) and `.migration/source_fingerprint.json` pins the per-table row counts and marker; `fixtures/source_fingerprint.py` re-checks it and every recon/preflight compares against the same hash, so any change by another local role is detected before merge evidence is accepted. Local PostgreSQL has no other application roles writing to odoo_src.
- Target principal in `MONGODB_ATLAS_URI` is over-scoped (readWriteAnyDatabase/dbAdminAnyDatabase); recorded with `--allow-broad-target`, mongo_guard is the write fence (same as UNT14).

## Plugin gaps

- UNT15O-2 — The recon snapshot lacked the PostgreSQL driver (`ModuleNotFoundError: psycopg2`) despite the worker setup contract. Installed `psycopg2-binary==2.9.10` into `/home/ubuntu/.venvs/recon`; no plugin changes. ACU cost: not separately metered; included in the worker total.
- UNT15O-2 — `skills/wave-preflight/apps.py` accepts directory roots only, so the requested `odoo-bin` file root is rejected. Used one Odoo app rooted at `.`; attribution covers the server, addons and entry point without overlapping roots. The ORM's `odoo%` sessions and the committed recipe's default `psql%` deploy sessions are declared. ACU cost: not separately metered; included in the worker total.
- UNT15O-2 — The live census retains five SQL views, but the pinned proposer generates neither mappings nor questions for them (`report_stock_quantity`, `res_device`, `res_session`, `stock_avco_report`, `vendor_delay_report`). Preserved each as an explicit unmodeled `view_review` entry with a census citation in `modeling_run.json`; no view exclusion or migration decision was made. All 521 base tables are independently covered exactly once by proposal buckets. ACU cost: not separately metered; included in the worker total.
- UNT15O-2 — Workload export exits 2 because this frozen source has no `pg_stat_statements` result. The pipeline continues with 6,163 unconfirmed static access candidates and unmeasured frequencies; no source extension or grants were changed. ACU cost: not separately metered; included in the worker total.

## Bill

| ticket | step | session | ACU | wall |
|---|---|---|---|---|
| manager | p1 | this session | tbd | tbd |
