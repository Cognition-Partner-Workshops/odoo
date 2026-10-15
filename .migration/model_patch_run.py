#!/usr/bin/env python3
"""Run the pinned plugin's model_patch.py apply path on this run's spec.

The proposer excluded 306 shared/framework tables (`modeling.excluded_tables`) but still
emits `references` rows pointing at them (resUsers, resCompany, ...). model_patch.py's
`_check_references` treats those as dangling and refuses every decision, the same
plugin gap as the "no rationale row" false positives of `--check`. This wrapper does not
change the plugin: it runs `apply_decisions` with references into excluded tables
ignored by that one check, then writes the spec exactly as `model_patch.main` does.
Usage: model_patch_run.py --plugin <dir> --spec S --decisions D --out O --version V
       [--data-profile P] [--access-patterns A]
"""
import argparse
import json
import pathlib
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True, help="pinned plugin checkout (plugin_sha)")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--data-profile")
    ap.add_argument("--access-patterns")
    a = ap.parse_args()
    sys.path.insert(0, str(pathlib.Path(a.plugin) / "skills" / "schema-modeling"))
    import model_patch as mp  # noqa: PLC0415

    spec = json.loads(pathlib.Path(a.spec).read_text())
    excluded = {mp.camel(t) for t in spec["modeling"].get("excluded_tables", [])}
    original_check = mp._check_references

    def check_references_skipping_excluded(out: dict) -> None:
        # check a pruned copy; `out` is what gets written and must keep every reference.
        # references into excluded tables are not dangling: the table was excluded on
        # purpose and the column stays an integer id (NOTES.md D3)
        pruned = json.loads(json.dumps(out))
        for c in pruned["collections"]:
            c["decision"]["references"] = [r for r in c["decision"]["references"]
                                           if r["to"] not in excluded]
            for emb in c["embeds"]:
                emb["child_references"] = [r for r in emb.get("child_references", [])
                                           if r["to"] not in excluded]
        original_check(pruned)

    mp._check_references = check_references_skipping_excluded
    profile = access = None
    if a.data_profile:
        p = pathlib.Path(a.data_profile)
        profile = {**json.loads(p.read_text()), "_bytes": p.read_bytes()}
    if a.access_patterns:
        p = pathlib.Path(a.access_patterns)
        access = {**json.loads(p.read_text()), "_bytes": p.read_bytes()}
    decisions = json.loads(pathlib.Path(a.decisions).read_text())
    try:
        out = mp.apply_decisions(spec, decisions, workspace=pathlib.Path("."),
                                 profile=profile, access=access)
    except mp.DecisionError as e:
        print(f"decision refused: {e}", file=sys.stderr)
        return 1
    out["version"] = a.version
    out["canonicalization"]["version"] = f"{a.version}-canon"
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2) + "\n")
    n_embed = sum(len(c["embeds"]) for c in out["collections"])
    print(f"mapping spec {a.version} written to {a.out}: collections={len(out['collections'])} "
          f"embeds={n_embed} unresolved={len(out['modeling']['unresolved'])} "
          f"decisions={len(decisions)} (references into {len(excluded)} excluded tables kept)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
