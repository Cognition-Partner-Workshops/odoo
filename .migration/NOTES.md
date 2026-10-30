# UNT15 migration notes

Run: Odoo (`mongo-run/unt15`, cut from `mongo-run/unt13`) from local read-only PostgreSQL `odoo_src` to Atlas database `odoo_unt15`, bounded to wave-1 close. Plugin pinned in `plugin_sha`.

## Run findings (not plugin gaps)

- Base branch `mongo-run/unt13` carried the finished UNT14 migration code (50 `_storage = 'mongodb'` opt-ins, database literal `odoo_unt13`). Reset in PR #165 (Dhrov's option 1): opt-ins removed, storage-path mechanism kept, `storage_mongodb.DATABASE` read from `allowed_targets.json`.
- Board UNT15O was created as a plain board (identifier UNT15 was taken), so there is no Plan view; `plan.yaml` is committed here and decisions are taken in the manager session chat.
- Source secret: the auto-injected org copy of `ODOO_PG_RO_DSN` is a URL; `build_source.sh` and the probe need the JSON form (personal copy, bound explicitly).
- Target principal in `MONGODB_ATLAS_URI` is over-scoped (readWriteAnyDatabase/dbAdminAnyDatabase); recorded with `--allow-broad-target`, mongo_guard is the write fence (same as UNT14).

## Plugin gaps

(none yet; format: ticket, what the plugin did, what was done instead, ACU cost)

## Bill

| ticket | step | session | ACU | wall |
|---|---|---|---|---|
| manager | p1 | this session | tbd | tbd |
