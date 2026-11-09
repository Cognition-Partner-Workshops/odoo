# Synthetic target fixture

From the repository root, using `/home/ubuntu/.venvs/recon/bin/python`:

```sh
python .migration/fixtures/build_fixture.py
MONGO_LOCAL_URI=mongodb://localhost:27017 python .migration/fixtures/load_fixture.py
```

After the mapping spec version changes at sign-off, rebuild and commit the data and
manifest together. The loader rejects stale specs and checks compressed-file hashes
and counts before dropping the selected collections in local `odoo_unt16` only.
No source connection or source records are used. Gzip keeps the all-collection
relaxed Extended JSON dataset small; gzip headers and document content are seeded
and reproducible (the manifest's `produced_at` is the actual build time).

For a slice, pass `--collections accountAccount,resCountry,resCity` and/or
`--collections-file slice.json` (a JSON list) to the builder. Use
`--out-dir <directory>/data --manifest <directory>/fixture_manifest.json` to keep
slice output separate, then load with `--manifest` pointing at that manifest.
The loader also accepts `--collections`. Filtered builds retain the global
synthetic IDs; referenced collections outside the slice must already be loaded.

`--parents 20` is the minimum base size, not a fixed size: sizing expands parents
and children to satisfy nearest-rank p50/p99 fanouts and embedded-row placement.
The designated maximum-fanout parent needs at least 101 parents so its one extreme
value does not alter p99. Unmeasured fanouts are listed in the manifest, not invented
as measured targets. `--seed` defaults to 16.

Profile-empty root tables produce zero documents (`empty_in_profile`); the loader
still creates their collections and indexes. Every measured relation is capped at
its profile maximum. The manifest records actual post-repair, post-embed-projection
fanouts, including `fanout_mismatches`: nullable owner bindings can leave source
rows unrepresentable in the draft embed shape, and unique-key repairs can change
quantiles. These are explicit fixture limitations, not parity claims. Unique-key
repairs retain valid synthetic FK IDs and respect the measured maximum fanouts.
The outlier tie and deterministic tie-break are recorded in `outlier_tie`.

These are target-shaped fixture-first development inputs, not source parity
evidence. The pinned harness's fixture mode reads a *source copy via DSN*, not a
target JSON file; it cannot reconcile this JSON alone. Workers must supply their
ticket's source fixture/adapter before claiming any recon result. Local fixture
checks are never merge evidence.
