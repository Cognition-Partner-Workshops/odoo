run_id: UNT14-39
manifest_sha: 97b919423b64

# w1-b01 independent verification: accountLockException

**Verdict: PASS** (live recon, `target_class: migration_cluster`, `merge_eligible: true`)

Verified head: `6047909ee628d2c84a4ef115b94d4d68734cd91e` (PR #136 head; its parent `e1941f7f6b5` is the batch's recon commit, the head commit only adds `result.batch.json`).
Plugin pin: `608ef5b035ba2d13a1246d4d731aa525ce04ff6f` (harness run from a detached worktree at that commit).

## Source

- `odoo_src` rebuilt with `.migration/fixtures/build_source.sh` (source commit `63446015e3c1`, `DONE rc=0`).
- `.migration/fixtures/source_fingerprint.py` (via `secret:personal:ODOO_PG_RO_DSN`): `a100e84ee2fb6282f30b45c003fd1db47561317c739340a10564d9e869e56a4e`, exact match to `.migration/source_fingerprint.json` and the ticket.
- Recon `source_db: odoo_src`, `source_server: hmac-sha256:545efbd0aca82e45` (salted via `RECON_REDACT_SALT`), matching `.migration/connectivity.json`.

## Recon (`accountLockException/result.json`)

Run: `recon.cli run --mode live --family postgresql --unit accountLockException --collections accountLockException --target-db odoo_unt13 --target-class migration_cluster`, committed `mapping_spec.json` (map-draft-5, sha `c0b93dad…02a7`), `recon_tolerances.json` (v1, sha `8c9b9e4c…5416`), canonicalization = the mapping's `map-draft-5-canon` block (`verify-canon.json`).

| Tier | Check | Result |
|---|---|---|
| 1 | counts through mapping | PASS (source 1, target 1) |
| 2 | per-field aggregates | PASS (7 fields deferred to Tier 3 by the harness) |
| 3 | keyed diffs | PASS (full diff, population 1, 0 duplicate source keys) |
| 4 | app-level parity | PASS (2 verifier ops) |

Tier 4 used verifier-owned `verify-ops.json`, `ops_sha256 3b14eadcf4e7…7166` (batch's ops `0310a36bfd09…63e8`; no reuse). Ops:
- `verify_lock_scope_by_company_field`: the `ResCompany` lock-date lookups (company, lock date field, global vs user-bound exception) with count and min/max lock dates.
- `verify_audit_columns_by_id`: per-row reason and audit uid/date columns, which the batch ops do not project.

## Probes past the gate (`probe_w1_b01.py`, read-only)

- Snapshot before (`probe_before.json`) and after (`probe_after.json`) recon: identical count (1), raw-BSON sha256 `aa510072…c028`, max `writeDate` `2026-10-20T00:00:00`; no writes during verification.
- Every mapped field present, no explicit nulls, no type mismatches against `bson_type`, no unmapped keys, no duplicate `_id`.
- Independent row-by-row value comparison against `account_lock_exception`: 0 mismatches.
- Indexes: all four spec indexes present, none extra.
- References `companyId -> resCompany`, `userId/createUid/writeUid -> resUsers`: neither target is a migrated collection in a merged wave, so they were resolved against `odoo_src` (`res_company`, `res_users`): 0 dangling.
- No embeds in this collection; empty-collection case not applicable (source has 1 row).

## Findings

None.

Coverage note (not a finding): the source fixture has a single `account_lock_exception` row, so Tiers 2-4 exercise one document. That is the full population and recon covered all of it.
