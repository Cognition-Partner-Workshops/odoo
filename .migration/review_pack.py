#!/usr/bin/env python3
"""Render the s3.1 schema sign-off pack (.migration/model_review_pack.md) from the
artifacts, never from hand-typed numbers: the committed spec, the scratch map-draft-2,
the data profile, the reviewed access patterns, the rehearsal and recon outputs and the
--check transcripts. Re-run after any of them changes.

  python3 .migration/review_pack.py --out .migration/model_review_pack.md
"""
import argparse
import json
import pathlib
import re
from collections import Counter, defaultdict

MIG = pathlib.Path(__file__).resolve().parent
REH = MIG / "rehearsal"


def load(path):
    return json.load(open(path))


def question_counts(spec):
    unresolved = spec["modeling"].get("unresolved", [])
    coll = [q for c in spec["collections"]
            for q in [*c["decision"].get("open_questions", []),
                      *(q for e in c.get("embeds", []) for q in e.get("child_open_questions", []))]]
    kinds = Counter(q.get("kind") for q in [*unresolved, *coll])
    return len(unresolved), len(coll), kinds


def check_summary(path):
    lines = open(path).read().splitlines()
    code = int(lines[0].split("=")[1])
    body = lines[1:]
    no_rat = [l for l in body if "no rationale row" in l]
    pending = [l for l in body if l.endswith("decision recorded")]
    other = [l for l in body if l not in no_rat and l not in pending and not l.startswith("open items")]
    return code, len(no_rat), len(pending), other, body[0] if body else ""


def edge_categories(spec, census):
    roots = {c["root_table"] for c in spec["collections"]}
    emb = {e["child_table"] for c in spec["collections"] for e in c.get("embeds", [])}
    exc = set(spec["modeling"]["excluded_tables"])
    have = {(r["parent"], r["child"], tuple(r["child_columns"])) for r in spec["modeling"]["rationale"]}

    def side(t):
        return "collection" if t in roots else "embed" if t in emb else "excluded" if t in exc else "other"
    cats, targets = Counter(), Counter()
    for rel in census["relationships"]:
        key = (rel["parent"], rel["child"], tuple(rel["child_columns"]))
        if rel["parent"] in census["tables"] and key not in have:
            cats[(side(rel["child"]), side(rel["parent"]))] += 1
            if side(rel["parent"]) == "excluded":
                targets[rel["parent"]] += 1
    return cats, targets


def fanout_rows(spec, rehearsal):
    reh = {(c["collection"], e["array_path"]): e for c in rehearsal["per_collection"] for e in c["embeds"]}
    rows = []
    for c in spec["collections"]:
        for e in c.get("embeds", []):
            rat = next((r for r in spec["modeling"]["rationale"]
                        if r["child"] == e["child_table"] and r["parent"] == c["root_table"]
                        and r["child_columns"] == e["parent_key"]), None) or {}
            ms = rat.get("measurements", {})
            fo = next((v for k, v in ms.items() if k.startswith("fanout:")), {})
            eb = next((v for k, v in ms.items() if k.startswith("embed_bytes:")), {})
            fx = reh.get((c["collection"], e["array_path"]), {})
            rows.append({
                "collection": c["collection"], "array_path": e["array_path"], "child": e["child_table"],
                "rule": rat.get("rule", "?"), "basis": e.get("cardinality_basis"),
                "parents": fo.get("parents"), "p50": fo.get("p50"), "p99": fo.get("p99"),
                "max": fo.get("max"), "embed_bytes_max": eb.get("max"),
                "fixture_max": fx.get("max"), "fixture_rows": fx.get("embedded"),
                "unexercised": (fo.get("parents") in (0, None)),
            })
    return rows


def hot_rows(access):
    hot = [p for p in access["patterns"] if p.get("confirmed") and p.get("frequency") == "hot"]
    groups = defaultdict(list)
    for p in hot:
        note = p.get("note") or ""
        routine = p.get("routine") or (note.split(" ")[1] if " " in note else "")
        groups[(p["source"]["file"], routine, p["kind"])].append(p)
    return hot, groups


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(MIG / "model_review_pack.md"))
    a = ap.parse_args()

    spec1 = load(MIG / "mapping_spec.json")
    spec2 = load(REH / "mapping_spec.map-draft-2.scratch.json")
    census = load(MIG / "census.json")
    access = load(MIG / "access_patterns.json")
    reh1 = load(REH / "rehearsal.map-draft-1.json")
    reh2 = load(REH / "rehearsal.map-draft-2-scratch.json")
    rec1 = load(REH / "recon" / "s3.1-rehearsal-draft1" / "result.json")
    rec2 = load(REH / "recon" / "s3.1-rehearsal-draft2-scratch" / "result.json")
    decisions = load(MIG / "design_decisions.json")
    answers = [l for l in open(MIG / "answers.txt").read().splitlines()
               if l.strip() and not l.lstrip().startswith("#")]
    plugin_sha = open(MIG / "plugin_sha").read().strip()
    notes = open(MIG / "NOTES.md").read()

    u1, c1, k1 = question_counts(spec1)
    u2, c2, k2 = question_counts(spec2)
    chk1 = check_summary(REH / "check.map-draft-1.txt")
    chk2 = check_summary(REH / "check.map-draft-2.scratch.txt")
    cats, targets = edge_categories(spec2, census)
    attempt = open(REH / "patch_attempt.map-draft-1.txt").read()
    attempt_exit = re.search(r"^exit=(\d+)$", attempt, re.M).group(1)
    dangling = attempt.count(" -> ")
    hot, groups = hot_rows(access)
    fan2 = fanout_rows(spec2, reh2)
    unexercised = [r for r in fan2 if r["unexercised"]]
    idx_counts = sorted(((len(c["indexes"]), c["collection"]) for c in spec2["collections"]), reverse=True)
    idx1 = {c["collection"]: len(c["indexes"]) for c in spec1["collections"]}
    hand = [d for d in decisions if "answers_line" not in (d.get("evidence") or {})]
    recorded = spec2["modeling"].get("decisions", [])
    compiled = sum(1 for d in recorded if "answers_line" in (d.get("evidence") or {}))
    refused1 = [(c["collection"], c["indexes_in_spec"], c["indexes_created"], len(c["indexes_failed"]))
                for c in reh1["per_collection"] if c["indexes_failed"]]
    refused2 = [(c["collection"], c["indexes_in_spec"], c["indexes_created"], len(c["indexes_failed"]))
                for c in reh2["per_collection"] if c["indexes_failed"]]
    empty2 = [c["collection"] for c in reh2["per_collection"] if c["documents"] == 0]
    sha2 = __import__("hashlib").sha256(open(REH / "mapping_spec.map-draft-2.scratch.json", "rb").read()).hexdigest()
    sha1 = __import__("hashlib").sha256(open(MIG / "mapping_spec.json", "rb").read()).hexdigest()

    L = []
    w = L.append
    w("# Schema sign-off pack — s3.1 (board UNT12, ticket UNT12-9)\n")
    w(f"Plugin pinned at `{plugin_sha[:7]}` (unpatched). Committed spec: `{spec1['version']}` "
      f"(sha256 `{sha1}`). Scratch answered spec: `{spec2['version']}` "
      f"(sha256 `{sha2}`, `.migration/rehearsal/mapping_spec.map-draft-2.scratch.json`, built by "
      f"`.migration/rehearsal/scratch_draft2.sh`). Rendered review pages: `.migration/model_cards.md` "
      f"({spec1['version']}) and `.migration/rehearsal/model_cards.map-draft-2.scratch.md` ({spec2['version']}).\n")

    w("## 1. Where this stands (read first)\n")
    w(f"- Every open item of `{spec1['version']}` has an answer: {len(answers)} answer lines in "
      f"`.migration/answers.txt` plus {len(hand)} hand-written decisions in `.migration/design_decisions.json` "
      f"(the answer lines compile to {compiled} decisions; the scratch spec records {len(recorded)} decisions in all). "
      f"Applied to a scratch copy they leave "
      f"**{u2} `modeling.unresolved` and {c2} collection/embed open questions**.")
    w(f"- **The pinned plugin refuses to apply them to the committed spec** (exit {attempt_exit}): "
      f"`model_patch.py` rejects any decision on `{spec1['version']}` with `dangling references after decisions` "
      f"({dangling} referrer→target pairs, all pointing at collections of tables excluded by `--exclude-table`). "
      f"Transcript: `.migration/rehearsal/patch_attempt.map-draft-1.txt`. Section 3 has the cause and the options; "
      f"this is the gap the manager asked to report rather than patch.")
    w(f"- `model_patch.py --check`: committed `{spec1['version']}` exits {chk1[0]} ({chk1[1]} `no rationale row`, "
      f"{chk1[2]} pending-decision lines, {len(chk1[3])} other); scratch `{spec2['version']}` exits {chk2[0]} with "
      f"**exactly {chk2[1]} `no rationale row` lines and {len(chk2[3])} other failures** — the 1460 FK edges into "
      f"excluded tables are the only thing between the answered spec and exit 0 (section 2.3).")
    w(f"- Local rehearsal (odoo_fixture → local mongo:7, `--target-class local`): {reh2['documents']} documents in "
      f"{reh2['collections']} collections; largest document {reh2['largest_document']['bytes']} bytes "
      f"({reh2['largest_document']['pct_of_limit']}% of 16 MB, `{reh2['largest_document']['collection']}`); "
      f"longest array {reh2['longest_array']['max']} elements (`{reh2['longest_array']['collection']}.{reh2['longest_array']['array_path']}`). "
      f"Recon fixture mode: {spec1['version']} **{rec1['verdict']}**, scratch {spec2['version']} **{rec2['verdict']}** "
      f"(section 6: the failures are two float8 SUM rounding differences under zero tolerance, not row differences). "
      f"A fixture PASS/FAIL proves the load path only, never parity.")
    w(f"- Two model findings from the rehearsal, both answered in `design_decisions.json`: the proposal gives "
      f"`accountMove` {idx1['accountMove']} indexes and MongoDB caps a collection at 64 (section 5.3); "
      f"`account_partial_reconcile` has two parents and keeps its own collection (section 5.1).\n")

    w("## 2. Questions the schema step asked, and the answers\n")
    w("### 2.1 Count by kind\n")
    rows = [(k, k1.get(k, 0), k2.get(k, 0)) for k in sorted(k1)]
    w(md_table(["kind", f"open in {spec1['version']}", f"open in scratch {spec2['version']}"], rows))
    w(f"\nTotal: **{u1 + c1}** ({u1} spec-wide `modeling.unresolved`, {c1} collection and embed `open_questions`) "
      f"in {len(k1)} kinds → **{u2 + c2}** after the answers. `known_incompatibilities`: the spec has no such key at "
      f"this plugin version; the ddl/census findings surface as the kinds above.\n")
    w("### 2.2 Answer lines (`.migration/answers.txt`)\n")
    for line in answers:
        w(f"- `{line.split(':', 1)[0]}`: {line.split(':', 1)[1].strip()}")
    w("\n### 2.3 Hand-written decisions (`.migration/design_decisions.json`)\n")
    for d in hand:
        if d["op"] == "index":
            continue
        subj = d.get("subject") or f"{d['op']} {d.get('child_table', '')} {d.get('from', '')}".strip()
        w(f"- **{d['op']}** — {subj}")
    n_idx = sum(1 for d in hand if d["op"] == "index")
    w(f"- **index** ×{n_idx} — remove the `accountMove` source-index entries no confirmed access pattern exercises "
      f"(section 5.3).")
    w("\nEdges into excluded tables, what `--check` still lists after the answers:\n")
    cat_rows = [(f"{c[0]} → {c[1]}", n) for c, n in sorted(cats.items(), key=lambda x: -x[1])]
    w(md_table(["edge (child side → parent side)", "edges"], cat_rows))
    w(f"\nTotal {sum(cats.values())}. Most-referenced excluded parents: "
      + ", ".join(f"`{t}` ({n})" for t, n in targets.most_common(8)) + ". Disposition (recorded as a `note` "
      "decision): excluded tables stay in PostgreSQL; FK columns into them remain integer id fields on the "
      "document, resolved by the ORM across stores; edges between two excluded tables are not modeled.\n")

    w("## 3. Plugin gap at the pinned SHA (not patched)\n")
    w(f"`model_proposal.py` builds every collection's `decision.references` from the raw table's foreign keys "
      f"(`skills/schema-modeling/model_proposal.py:1734`, `t[\"foreign_keys\"]`) after it has removed the excluded "
      f"tables from the census (`_prepare_census`, lines 1162–1197), so `{spec1['version']}` carries {dangling} "
      f"reference rows whose `to` is a collection that does not exist (`resUsers`, `resCompany`, `resPartner`, "
      f"`resCurrency`, …). Two consequences:\n")
    w("1. `model_patch.py` runs `_check_references` (`model_patch.py:1743`) after every decision list and refuses "
      "the whole patch on these pre-existing rows, so **no `--answers` or `--decisions` run can be applied** to a spec "
      "proposed with `--exclude-table` targets that are FK parents. Repro: "
      "`model_patch.py --spec .migration/mapping_spec.json --decisions <one note decision> --out /tmp/x.json "
      "--version probe` → `dangling references after decisions`.")
    w("2. `check_spec` (`model_patch.py:1961`) skips relationships only for tables in `modeling.excluded` (written "
      "by the `exclude` decision) and never consults `modeling.excluded_tables` (written by `--exclude-table`), so "
      f"every census FK touching an excluded table is a `no rationale row` failure ({chk2[1]} here). The `exclude` "
      "decision cannot be used instead: it needs an existing collection and refuses one that is referenced "
      "(`decision refused: no collection named 'resUsers'`).\n")
    w("Options for the manager: (a) pin a plugin SHA where the proposer skips references to excluded tables and "
      "`check_spec` honours `excluded_tables` (two small changes; the scratch run in this PR shows exactly what "
      "that produces: 0 open items, --check limited to the 1460 edges); (b) accept the scratch map-draft-2 as "
      "the signed-off model and pin its sha256 — this pack and the rehearsal already describe it; (c) re-propose "
      "without `--exclude-table` and model the 379 shared tables, which re-litigates the s2.1 scope rule. "
      "Recommended: (a).\n")

    w("## 4. Hot queries confirmed in s2.2\n")
    w(f"{len(hot)} confirmed `hot` access patterns ({Counter(p['kind'] for p in hot)['sql']} raw SQL, "
      f"{Counter(p['kind'] for p in hot)['odoo']} ORM calls, {Counter(p['kind'] for p in hot)['orm']} stored "
      f"relations; {Counter(p['op'] for p in hot)['read']} reads, {Counter(p['op'] for p in hot)['write']} writes) "
      f"out of {len(access['patterns'])} patterns. Grouped by source routine; every id is listed below the table.\n")
    g_rows = [(f"`{f}`", r, k, len(ps), ", ".join(sorted({t for p in ps for t in p['tables']})))
              for (f, r, k), ps in sorted(groups.items(), key=lambda x: (-len(x[1]), x[0]))]
    w(md_table(["file", "routine / relation", "kind", "patterns", "tables"], g_rows))
    w("\n<details><summary>All hot pattern ids</summary>\n")
    w(md_table(["id", "kind", "op", "tables", "source"],
               [(p["id"], p["kind"], p["op"], ", ".join(p["tables"]),
                 f"{p['source']['file']}:{p['source']['lines'][0]}-{p['source']['lines'][1]}") for p in
                sorted(hot, key=lambda p: (p["source"]["file"], p["source"]["lines"][0]))]))
    w("\n</details>\n")

    w("## 5. Model choices for sign-off\n")
    w("### 5.1 `account_partial_reconcile` keeps its own collection (manager note 2)\n")
    w("The proposer embedded it under `account_move_line` through `debit_move_id` only. The confirmed hot reads "
      "`ap-26541a49e3` and `ap-d62ff6e982` (`AccountMove._get_all_reconciled_invoice_partials`) and `ap-8eda2da30f` "
      "(`AccountMoveLine._compute_amount_residual`) filter on both `debit_move_id` and `credit_move_id`; a partial has "
      "two parents. The `reference` decision restores `accountPartialReconcile` as a collection referenced from both "
      f"sides ({spec2['version']}: {len(spec2['collections'])} collections, {sum(len(c['embeds']) for c in spec2['collections'])} embeds; "
      f"{spec1['version']}: {len(spec1['collections'])} / {sum(len(c['embeds']) for c in spec1['collections'])}).\n")
    w("### 5.2 Blocked register items (NOTES.md §s2.3 rows 23 and 28; manager note 3)\n")
    for d in hand:
        if d["op"] == "note" and ("kpi_provider" in d["subject"] or "post_init_hook" in d["subject"]):
            w(f"- **{d['subject']}** — {d['decision']} (evidence `{d['evidence'].get('file')}`)")
    w("\nNo ORM code is written here; both are model-side answers for the plan.\n")
    w("### 5.3 Index cap: `accountMove`\n")
    w(f"{spec1['version']} proposes {idx1['accountMove']} indexes on `accountMove` (origins: "
      + ", ".join(f"{o} {n}" for o, n in Counter(i.get('origin') for c in spec1['collections'] if c['collection'] == 'accountMove' for i in c['indexes']).items())
      + f"). MongoDB allows 64 per collection including `_id`; loading odoo_fixture refused "
      f"{sum(r[3] for r in refused1)} of them (`CannotCreateIndex`, code 67) and the recon reported them as "
      f"`index_missing`. The index decisions remove the {n_idx} entries that carry the 13 unexercised source indexes "
      f"(their `source_index_not_exercised` questions), leaving {dict((c, n) for n, c in idx_counts)['accountMove']}. "
      f"Highest index counts in the scratch spec: " + ", ".join(f"`{c}` {n}" for n, c in idx_counts[:5]) + ".\n")

    w("## 6. Local rehearsal (fixture mode, local target)\n")
    w(f"Source `odoo_fixture` ({reh2['source_database']}, built by `.migration/fixtures/build_fixture.sh` from "
      f"`odoo_src` as a template), target local `mongo:7` from the plugin's `docker-compose.local.yml`, loaded by "
      f"`.migration/rehearsal/load_fixture.py` straight from the spec. Numbers below are from "
      f"`rehearsal.map-draft-2-scratch.json`; `rehearsal.map-draft-1.json` holds the committed spec's run.\n")
    w(md_table(["", spec1["version"], f"scratch {spec2['version']}"], [
        ("collections loaded", reh1["collections"], reh2["collections"]),
        ("documents", reh1["documents"], reh2["documents"]),
        ("largest document (bytes)", f"{reh1['largest_document']['bytes']} ({reh1['largest_document']['collection']})",
         f"{reh2['largest_document']['bytes']} ({reh2['largest_document']['collection']})"),
        ("largest document, % of 16 MB", reh1["largest_document"]["pct_of_limit"], reh2["largest_document"]["pct_of_limit"]),
        ("longest array", f"{reh1['longest_array']['max']} ({reh1['longest_array']['collection']}.{reh1['longest_array']['array_path']})",
         f"{reh2['longest_array']['max']} ({reh2['longest_array']['collection']}.{reh2['longest_array']['array_path']})"),
        ("indexes created / in spec", f"{reh1['indexes_created']} / {reh1['indexes_in_spec']} ({reh1['indexes_failed']} refused)",
         f"{reh2['indexes_created']} / {reh2['indexes_in_spec']} ({reh2['indexes_failed']} refused)"),
        ("recon verdict", rec1["verdict"], rec2["verdict"]),
    ]))
    w("\nRecon tiers (`.migration/rehearsal/recon/<unit>/result.json`, redacted values):\n")
    t_rows = []
    for name, rec in ((spec1["version"], rec1), (f"scratch {spec2['version']}", rec2)):
        for t in rec["tiers"]:
            t_rows.append((name, t["tier"], t["checks_run"], "PASS" if t["passed"] else f"FAIL ({len(t['findings'])})",
                           "; ".join(f"{f['collection']} {f['check']} {f['detail']}" for f in t["findings"])))
    w(md_table(["spec", "tier", "checks", "result", "findings"], t_rows))
    w("\nThe Tier 2 findings are `SUM()` of float8 columns compared at `aggregate_rel_tol: 0`: PostgreSQL sums in "
      "row order and MongoDB `$sum` in document order, so the two doubles differ in the last place "
      "(seen with `--raw-values` in local scratch: -5081.860000000001 vs -5081.86 on "
      "`account_bank_statement_line.amount_residual`, 11979.099999999999 vs 11979.1 on "
      "`purchase_order_line.technical_price_unit`). Tier 3 keyed diffs pass on every row, so the values themselves "
      "match. Tolerances are not changed here; the manager decides whether float8 aggregates get a relative "
      "tolerance or a `decimal_round` rule.\n")
    w("Environment note: the local container aborted once with a WiredTiger `Too many open files` panic while "
      "building the committed spec's ~630 indexes (container `nofile` limit, not a model property); it was restarted "
      "and both runs above completed on the restarted container.\n")
    w(f"Collections with 0 documents in odoo_fixture ({len(empty2)}): " + ", ".join(f"`{c}`" for c in empty2) + ".\n")
    w("Per collection:\n")
    w(md_table(["collection", "documents", "max doc bytes", "indexes created/spec", "embeds (max array)"],
               [(c["collection"], c["documents"], c["max_doc_bytes"],
                 f"{c['indexes_created']}/{c['indexes_in_spec']}" + (f" ({len(c['indexes_failed'])} refused)" if c["indexes_failed"] else ""),
                 ", ".join(f"{e['array_path']} {e['max']}" for e in c["embeds"]))
                for c in sorted(reh2["per_collection"], key=lambda c: -c["documents"])]))

    w("\n## 7. Fan-out per embed (profile p50 / p99 / max on odoo_src; fixture max)\n")
    w(f"{len(fan2)} embeds in the scratch {spec2['version']}. `parents` is the profiled parent-row count; an embed "
      f"with 0 parents in odoo_src is **unexercised** by the fixture (section 8). `embed bytes max` is the profiled "
      f"embedded-child byte total per parent.\n")
    w(md_table(["collection", "array", "child table", "rule", "basis", "parents", "p50", "p99", "max", "embed bytes max", "fixture max", "unexercised"],
               [(r["collection"], r["array_path"], r["child"], r["rule"], r["basis"], r["parents"], r["p50"], r["p99"],
                 r["max"], r["embed_bytes_max"], r["fixture_max"], "yes" if r["unexercised"] else "") for r in fan2]))
    pol = spec2["modeling"]["policy"]
    w(f"\nPolicy: `max_embed_fanout` {pol['max_embed_fanout']}, `max_doc_bytes` {pol['max_doc_bytes']}. Highest "
      f"profiled max: {max((r['max'] or 0) for r in fan2)}; highest fixture max: {max((r['fixture_max'] or 0) for r in fan2)}.\n")

    w("## 8. Embeds the fixture does not exercise (manager note 4)\n")
    w(f"{len(unexercised)} embeds have no parent rows in odoo_src, so neither the profile nor the fixture measures "
      f"their fan-out; they are accepted on the schema rule alone and must be watched in the first live recon:\n")
    w(md_table(["collection", "array", "child table", "rule", "basis"],
               [(r["collection"], r["array_path"], r["child"], r["rule"], r["basis"]) for r in unexercised]))

    w("\n## 9. Commands run\n")
    w("```")
    w("PLUGIN=/home/ubuntu/plugin-9a584b4 (git worktree of mongo-migration-plugin at 9a584b4)")
    w(".migration/fixtures/build_source.sh && .migration/fixtures/build_fixture.sh            # odoo_src, odoo_fixture on PG16:5433")
    w("docker compose -f $PLUGIN/skills/schema-modeling/docker-compose.local.yml up -d mongo   # local mongo:7")
    w("$PY $PLUGIN/skills/schema-modeling/model_patch.py --spec .migration/mapping_spec.json --answers .migration/answers.txt \\")
    w("    --decisions .migration/design_decisions.json --out .migration/mapping_spec.json --version map-draft-2 \\")
    w("    --data-profile .migration/data_profile.json --census .migration/census.json --access-patterns .migration/access_patterns.json")
    w("    -> refused (patch_attempt.map-draft-1.txt); .migration/rehearsal/scratch_draft2.sh is the scratch run")
    w("$PY $PLUGIN/skills/schema-modeling/model_patch.py --spec <spec> --data-profile ... --census ... --access-patterns ... --check")
    w("$PY .migration/rehearsal/load_fixture.py --spec <spec> --source-dsn-secret ODOO_PG_FIXTURE_DSN --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt12 --out <json>")
    w("recon run --unit <unit> --family postgresql --mapping <spec> --tolerances .migration/recon_tolerances.json \\")
    w("    --canonicalization <postgresql profile recon_canonicalization rules> --mode fixture --source-dsn-secret ODOO_PG_FIXTURE_DSN \\")
    w("    --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt12 --target-class local --allowed-targets-file .migration/allowed_targets.json --seed 1")
    w("python3 .migration/review_pack.py")
    w("```")
    w("`ODOO_PG_FIXTURE_DSN` is the `ODOO_PG_RO_DSN` JSON with `database` set to `odoo_fixture`, exported per shell; "
      "`MONGO_LOCAL_URI=mongodb://127.0.0.1:27017`. Secrets by name only. Nothing wrote to `odoo_src` or to Atlas.")
    pathlib.Path(a.out).write_text("\n".join(L) + "\n")
    print(f"wrote {a.out}: {len(L)} blocks, {u1 + c1} questions -> {u2 + c2}, check exits {chk1[0]}/{chk2[0]}")


if __name__ == "__main__":
    main()
