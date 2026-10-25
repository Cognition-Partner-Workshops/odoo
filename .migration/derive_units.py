#!/usr/bin/env python3
"""Derive migration units and waves (plan step s3.5-units) from the signed mapping spec.

Reads only committed files: .migration/{mapping_spec,census,data_profile,source_fingerprint,
recon_tolerances,conformance.md,NOTES.md,plugin_sha} and the addons tree. Writes
.migration/units.json and the "## s3.5 units and waves" section of .migration/NOTES.md.
`--check` re-derives and exits 1 when either committed output differs.

Rules (migration-planning SKILL, s3.3-unit-derivation, at the pinned plugin):
- A reference orders waves when its column is NOT NULL, has filled rows in the live profile
  (unsampled fk_integrity child_rows - null_fk > 0; an unmeasured stat orders, fail closed),
  or code on the write path sets it (cited in WRITE_PATH_SETTERS).
- A reference held by a pure link table (two NOT NULL foreign-key columns) is a junction
  reference: a plain id, it orders nothing.
- A never-filled reference whose target is not already in an earlier wave is a forward
  reference and must be cited in NO_WRITE_PATH_SETTER; an uncited one stops the derivation.
- Collections that reference each other in a cycle form one unit (strongly connected
  component); a unit's depth is its longest ordering path to a unit with no dependencies.
- Wave 1 is the canary alone: the smallest depth-0 unit by rows with at least one row; it
  lands the run's one shared loader. Wave 2 holds the other depth-0 units, wave d+2 depth d.
  Within a wave units go smallest first (rows, then id); batches take up to 5 units in order.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIG = ROOT / '.migration'
SIGNED_MAPPING_SHA256 = 'c0b93dad9526fc8f02df6b8199436d76da9f938a05ccadc98ab3adb7a35202a7'
TARGET_DB = 'odoo_unt13'
FIXTURE_MANIFEST = '.migration/fixtures/odoo_fixture.json'
SHARED_LOADER = '.migration/load/load_unit.py'
BATCH_MAX_UNITS = 5
NOTES_HEADING = '## s3.5 units and waves'

# (table, column) -> where installed code sets it; these never-filled references still order.
WRITE_PATH_SETTERS = {
    ('account_move', 'tax_cash_basis_rec_id'): 'addons/account/models/account_partial_reconcile.py:555',
    ('stock_warehouse_orderpoint', 'supplier_id'): 'addons/purchase_stock/models/product.py:322',
    ('product_value', 'lot_id'): 'addons/stock_account/models/stock_lot.py:100',
    ('product_value', 'move_id'): 'addons/stock_account/models/stock_move.py:230',
    ('purchase_order_line', 'sale_line_id'): 'addons/sale_purchase/models/sale_order_line.py:207',
    ('sale_order_line', 'combo_item_id'): 'addons/sale/models/sale_order.py:1403',
    ('stock_move', 'account_move_id'): 'addons/stock_account/models/stock_move.py:283',
}
# (table, column) -> why no installed code sets it; these become forward references.
NO_WRITE_PATH_SETTER = {
    ('account_move_line', 'stock_move_id'): 'only repair (repair/models/stock_move.py:169) and l10n_in_boe set it; neither is installed (no repair_order / l10n_in_* table in census.json)',
    ('product_value', 'account_move_id'): 'no installed code assigns product.value.account_move_id (stock_account creates product.value at product.py:240, stock_lot.py:99, stock_move.py:229 without it)',
    ('product_category', 'removal_strategy_id'): 'user setting only: set from the form (stock/views/product_views.xml:23), read at stock/models/stock_quant.py:653',
    ('uom_uom', 'package_type_id'): 'user setting only: field at stock/models/product.py:1346, no code assigns it',
}
# PostgreSQL mirrors of MongoDB links (`_shadow_relations`), checked against the addons tree.
MIRRORED_RELATIONS = [
    ('account.account', 'company_ids', 'account_account_res_company_rel', 'addons/account/models/account_account.py'),
    ('account.tax', 'children_tax_ids', 'account_tax_filiation_rel', 'addons/account/models/account_tax.py'),
    ('account.tax', 'replacing_tax_ids', 'account_tax_alternatives', 'addons/account/models/account_tax.py'),
    ('account.move.line', 'tax_ids', 'account_move_line_account_tax_rel', 'addons/account/models/account_move_line.py'),
    ('stock.route', 'product_ids', 'stock_route_product', 'addons/stock/models/stock_location.py'),
    ('stock.route', 'warehouse_ids', 'stock_route_warehouse', 'addons/stock/models/stock_location.py'),
    ('stock.picking.type', 'favorite_user_ids', 'picking_type_favorite_user_rel', 'addons/stock/models/stock_picking_type.py'),
    ('sale.order.line', 'invoice_lines', 'sale_order_line_invoice_rel', 'addons/sale/models/sale_order_line.py'),
]
PLUGIN_FINDINGS = [
    'No unit or wave derivation tool at the pin: skills/migration-planning/SKILL.md:90 states the s3.3 rule '
    'in prose and no script under skills/ computes units or waves, so this run carries the derivation in '
    '.migration/derive_units.py.',
    'skills/wave-preflight/preflight.py:380 refuses every never_filled_refs entry when connectivity.json '
    'source.server is null (a local-socket PostgreSQL source), even though data_profile.json source is the '
    'same {database: odoo_src, server: null}. Repro: preflight.py --wave <wave 2 spec built from units.json> '
    '--root . -> "profile source (database, server) is not the probed source". The profile (as_of '
    '2026-10-22) is also past the 24h limit at preflight.py:101, so waves 2 and 8 need a fresh live profile '
    'and this fix before they preflight.',
    'skills/migration-planning/SKILL.md:90 orders waves on "code on the write path sets it", but no plugin '
    'artifact records ORM field writes (access_patterns.json write patterns are raw SQL only), so the setters '
    'are cited by hand in WRITE_PATH_SETTERS.',
    'skills/migration-planning/SKILL.md:90 has no rule for reference cycles; this derivation merges each cycle '
    'into one unit.',
]
U1 = {'id': 'U1', 'table': 'stock_location',
      'text': 'the scope must load with only the declared shadow columns: the SQL view at '
              'addons/stock/report/report_stock_quantity.py:194 (register sql read 240, report 8) reads '
              'stock_location.parent_path, which is not a shadow column (.migration/conformance.md, U1)'}


def load(name):
    return json.loads((MIG / name).read_text())


def sha256_file(name):
    return hashlib.sha256((MIG / name).read_bytes()).hexdigest()


def md_tables(text, heading):
    """Rows of the first markdown table under `heading` as lists of cells."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == heading)
    rows, seen = [], False
    for line in lines[start + 1:]:
        if line.startswith('#'):
            break
        if line.startswith('|'):
            seen = True
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if not set(''.join(cells)) <= set('-: '):
                rows.append(cells)
        elif seen and line.strip():
            break
    return rows[1:]  # drop the header row


def site_in(site, cell):
    """True when `file:line` falls on a line or line range the conformance cell cites for that file."""
    path, line = site.rsplit(':', 1)
    if path not in cell:
        return False
    tail = cell[cell.index(path) + len(path):]
    for a, b in re.findall(r':(\d+)(?:-(\d+))?', tail.split('; addons/')[0]):
        if int(a) <= int(line) <= int(b or a):
            return True
    return False


def table_names(cell):
    return [t.strip().removesuffix(' (w)').strip() for t in cell.split(',') if t.strip() not in ('', '-')]


def derive():
    if sha256_file('mapping_spec.json') != SIGNED_MAPPING_SHA256:
        sys.exit('mapping_spec.json is not the signed spec (sha256 differs)')
    spec, census, fp = load('mapping_spec.json'), load('census.json'), load('source_fingerprint.json')
    profile, tol = load('data_profile.json'), load('recon_tolerances.json')
    rows = fp['row_counts']
    rc_input = ''.join(f'{t}\t{rows[t]}\n' for t in sorted(rows))
    if hashlib.sha256(rc_input.encode()).hexdigest() != fp['row_counts_sha256']:
        sys.exit('source_fingerprint.json row_counts do not hash to row_counts_sha256')
    tables = census['tables']
    stats = {s['id']: s for s in profile['stats']}
    fk_parent = {(r['child'], tuple(r['child_columns'])): r['parent'] for r in census['relationships']}
    fk_cols = defaultdict(set)
    for r in census['relationships']:
        fk_cols[r['child']].update(r['child_columns'])

    colls = {c['collection']: c for c in spec['collections']}
    coll_tables = {name: [c['root_table']] + [e['child_table'] for e in c['embeds']] for name, c in colls.items()}
    coll_of_table = {t: name for name, ts in coll_tables.items() for t in ts}
    coll_rows = {name: sum(rows[t] for t in ts) for name, ts in coll_tables.items()}

    def nullable(t, col):
        return next(c['nullable'] for c in tables[t]['columns'] if c['name'] == col)

    def is_junction(t):
        cols = tables[t]['columns']
        return len(cols) == 2 and all(not c['nullable'] and c['name'] in fk_cols[t] for c in cols)

    # every reference between two different mapped collections, classified
    order_edges = defaultdict(dict)   # coll -> to -> [basis]
    junction_refs, never_filled = [], []
    for name, c in colls.items():
        held = [(c['root_table'], r) for r in c['decision'].get('references', [])]
        held += [(e['child_table'], r) for e in c['embeds'] for r in e.get('child_references', [])]
        for t, r in held:
            to = r['to']
            if to not in colls or to == name:
                continue
            col = tuple(r['column'])
            parent = fk_parent[(t, col)]
            stat_id = f"fk_integrity:{t}->{parent}({','.join(col)})"
            ref = {'collection': name, 'table': t, 'column': ','.join(col), 'to': to, 'stat': stat_id}
            if is_junction(t):
                junction_refs.append(ref)
                continue
            s = stats.get(stat_id)
            if any(not nullable(t, x) for x in col):
                basis = 'not null'
            elif s is None or s['status'] != 'ok' or s['sampled'] is not False:
                basis = 'fill unmeasured (fail closed)'
            elif s['values']['child_rows'] - s['values']['null_fk'] > 0:
                basis = f"filled {s['values']['child_rows'] - s['values']['null_fk']}"
            elif len(col) == 1 and (t, col[0]) in WRITE_PATH_SETTERS:
                basis = 'set by ' + WRITE_PATH_SETTERS[(t, col[0])]
            else:
                never_filled.append(ref)
                continue
            order_edges[name].setdefault(to, []).append({'table': t, 'column': ref['column'], 'basis': basis})

    # strongly connected components (iterative Tarjan) -> units
    index, low, stack, on, comps, counter = {}, {}, [], set(), [], [0]
    for root in sorted(colls):
        if root in index:
            continue
        work = [(root, iter(sorted(order_edges[root])))]
        index[root] = low[root] = counter[0]; counter[0] += 1; stack.append(root); on.add(root)
        while work:
            v, it = work[-1]
            w = next(it, None)
            if w is not None:
                if w not in index:
                    index[w] = low[w] = counter[0]; counter[0] += 1; stack.append(w); on.add(w)
                    work.append((w, iter(sorted(order_edges[w]))))
                elif w in on:
                    low[v] = min(low[v], index[w])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    x = stack.pop(); on.discard(x); comp.append(x)
                    if x == v:
                        break
                comps.append(sorted(comp))
    unit_of = {}
    for comp in comps:
        uid = max(comp, key=lambda n: (coll_rows[n], n))  # named after its largest collection
        for n in comp:
            unit_of[n] = uid
    units = {uid: sorted(n for n in colls if unit_of[n] == uid) for uid in set(unit_of.values())}
    deps = {u: {} for u in units}
    for n, tos in order_edges.items():
        for to, via in tos.items():
            if unit_of[to] != unit_of[n]:
                deps[unit_of[n]].setdefault(unit_of[to], []).extend(
                    {'collection': n, **v, 'to': to} for v in via)
    depth = {}

    def depth_of(u):
        if u not in depth:
            depth[u] = 1 + max((depth_of(d) for d in deps[u]), default=-1)
        return depth[u]
    for u in sorted(units):
        depth_of(u)
    unit_rows = {u: sum(coll_rows[n] for n in ns) for u, ns in units.items()}

    candidates = [u for u in units if depth[u] == 0 and unit_rows[u] > 0]
    canary = min(candidates, key=lambda u: (unit_rows[u], len(units[u]), u))
    wave_of = {u: 1 if u == canary else depth[u] + 2 for u in units}
    ordered = sorted(units, key=lambda u: (wave_of[u], unit_rows[u], u))
    position = {u: i + 1 for i, u in enumerate(ordered)}

    def earlier(a, b):  # unit a merges in an earlier wave than unit b
        return wave_of[a] < wave_of[b]

    forward = defaultdict(list)
    for ref in never_filled:
        holder, target = unit_of[ref['collection']], unit_of[ref['to']]
        if holder == target or earlier(target, holder):
            continue
        key = (ref['table'], ref['column'])
        if key not in NO_WRITE_PATH_SETTER:
            sys.exit(f"never-filled reference {ref['stat']} needs a cited write-path setter or "
                     f"no-setter reason before it can order or be a forward reference")
        forward[holder].append({**ref, 'to_unit': target, 'kind': 'never_filled',
                                'why': 'profile shows 0 filled rows; ' + NO_WRITE_PATH_SETTER[key]})
    for ref in junction_refs:
        holder, target = unit_of[ref['collection']], unit_of[ref['to']]
        if holder != target and not earlier(target, holder):
            forward[holder].append({**ref, 'to_unit': target, 'kind': 'junction',
                                    'why': 'link-table id: resolves once the target unit merges'})

    acceptance = {u: defaultdict(list) for u in units}
    unit_of_table = {t: unit_of[coll_of_table[t]] for t in coll_of_table}

    def first_moved(ts):
        us = sorted({unit_of_table[t] for t in ts if t in unit_of_table}, key=position.get)
        return us

    notes = (MIG / 'NOTES.md').read_text()
    reg = {}
    for heading, section in (('### Raw SQL writes into in-scope tables (26)', 'write'),
                             ('### Raw SQL reads of in-scope tables (247)', 'read')):
        for cells in md_tables(notes, heading):
            num, disp, kind, site, func, tcell = cells[:6]
            ts = table_names(tcell)
            if re.fullmatch(r'\d+ tables \(\d+ written\)', tcell.strip()):
                # dynamic fan-out lists only a count: a unit-owned (B) row resolves to the function's model
                ts = [func.strip('`').rsplit('.', 1)[0].replace('.', '_')] if disp == 'B' else []
                assert all(t in tables for t in ts), ts
            reg.setdefault((kind, int(num)), []).append(
                {'section': section, 'num': int(num), 'disp': disp, 'kind': kind,
                 'site': site.strip('`'), 'function': func.strip('`'), 'tables': ts})

    conf = (MIG / 'conformance.md').read_text()
    conf_lines = conf.splitlines()
    start = conf_lines.index('### Per-unit acceptance list (71)')
    end = next(i for i in range(start + 1, len(conf_lines)) if conf_lines[i].startswith('## '))
    failures, group = [], None
    for line in conf_lines[start:end]:
        m = re.match(r'#### (\S+) \((\d+)\)', line)
        if m:
            group = m.group(1)
            continue
        m = re.match(r'\| (\d+) \| (.+) \| (.+) \| (.+) \| (C\d) \|$', line)
        if m:
            n, test, sites, regcell, fam = m.groups()
            kind, nums = regcell.split(' ', 1)
            numbers = []
            for part in nums.split(','):
                a, _, b = part.strip().partition('-')
                numbers += list(range(int(a), int(b or a) + 1))
            rows_hit = []
            for num in numbers:
                hits = [r for r in reg.get((kind, num), []) if site_in(r['site'], sites)]
                if len(hits) != 1:
                    sys.exit(f'conformance {group} #{n}: register {kind} {num} matches {len(hits)} rows')
                rows_hit.append(hits[0])
            failures.append({'group': group, 'n': int(n), 'test': test.strip(), 'family': fam,
                             'register': [f"{r['section']} {r['kind']} {r['num']}" for r in rows_hit],
                             'rows': rows_hit})
    if len(failures) != 71:
        sys.exit(f'conformance per-unit list has {len(failures)} rows, expected 71')
    owned_rows = {}
    for f in failures:
        owners = []
        for r in f['rows']:
            us = first_moved(r['tables'])
            key = f"{r['section']} {r['kind']} {r['num']}"
            if key not in owned_rows:
                owned_rows[key] = us
                acceptance[us[0]]['register_rows_owned'].append(
                    {'row': key, 'site': r['site'], 'function': r['function'], 'tables': r['tables']})
                for later in us[1:]:
                    acceptance[later]['register_rows_recheck'].append(
                        {'row': key, 'owner': us[0],
                         'tests': [g['test'] for g in failures if key in g['register']]})
            owners.append(us[0])
        gate = max(owners, key=position.get)
        acceptance[gate]['raw_sql_failures'].append(
            {'test': f['test'], 'family': f['family'], 'conformance_group': f['group'],
             'register': f['register'], 'row_owners': sorted(set(owners), key=position.get)})

    for cells in md_tables(notes, '### SQL views and `_table_sql` reports'):
        num, disp, model, how, tcell = cells[:5]
        if disp != 'B':
            continue
        us = first_moved(table_names(tcell))
        item = {'report': int(num), 'model': model.strip('`'), 'how': how, 'tables': table_names(tcell)}
        acceptance[us[0]]['sql_view_reports'].append({**item, 'role': 'owner'})
        for later in us[1:]:
            acceptance[later]['sql_view_reports'].append({**item, 'role': 'recheck', 'owner': us[0]})

    for model, field, rel, path in MIRRORED_RELATIONS:
        text = (ROOT / path).read_text()
        if not re.search(r"_shadow_relations = \([^)]*'" + field + "'", text):
            sys.exit(f'{path}: {field} is not in _shadow_relations')
        acceptance[unit_of_table[rel]]['mirrored_link_tables'].append(
            {'relation': rel, 'model': model, 'field': field, 'declared_in': path})
    declared = sum(len(re.findall(r"'([a-z_]+)'", m.group(1)))
                   for p in ROOT.glob('addons/*/models/*.py')
                   for m in re.finditer(r'_shadow_relations = \(([^)]*)\)', p.read_text()))
    if declared != len(MIRRORED_RELATIONS):
        sys.exit(f'addons declare {declared} _shadow_relations, MIRRORED_RELATIONS lists {len(MIRRORED_RELATIONS)}')

    review_crons = []
    for cells in md_tables(notes, '### Scheduled jobs (`ir_cron`)'):
        cid, disp, xmlid, model, active, every, direct, possible = cells[:8]
        direct_ts = table_names(direct)
        item = {'cron': int(cid), 'xmlid': xmlid.strip('`'), 'disp': disp, 'active': active == 'True'}
        if xmlid.strip('`') == 'base.autovacuum_job':
            for u in units:
                acceptance[u]['crons_to_pause'].append({**item, 'why': 'vacuums every in-scope model'})
        elif direct_ts:
            us = first_moved(direct_ts)
            for u in us:
                acceptance[u]['crons_to_pause'].append(
                    {**item, 'why': 'writes its tables directly' + (' (unit owns the rewrite)' if disp == 'B' and u == us[0] else ''),
                     'tables': sorted(t for t in direct_ts if unit_of_table.get(t) == u)})
        elif not possible.startswith('0:'):
            review_crons.append({**item, 'possible_reach': possible})
    acceptance[unit_of_table[U1['table']]]['storage_items'].append(U1)

    # browser tours in the scope addons and bridges, by the models their test files name
    buckets = load('table_buckets.json')
    tours = defaultdict(list)
    for addon in sorted(buckets['scope_addons'] + buckets['bridges']):
        for path in sorted((ROOT / 'addons' / addon / 'tests').glob('test_*.py')):
            text = path.read_text()
            if 'start_tour(' not in text:
                continue
            models = sorted(set(re.findall(r"env\[['\"]([a-z0-9_.]+)['\"]\]", text)))
            by_unit = defaultdict(list)
            for model in models:
                t = model.replace('.', '_')
                if t in unit_of_table:
                    by_unit[unit_of_table[t]].append(model)
            for u, ms in by_unit.items():
                tours[u].append({'file': str(path.relative_to(ROOT)), 'models': ms})

    mapping_version, tol_version = spec['version'], str(tol['version'])
    base_batch = {'fixture_manifest': FIXTURE_MANIFEST, 'recon_tolerances_version': tol_version,
                  'mapping_version': mapping_version, 'mapping_sha256': SIGNED_MAPPING_SHA256,
                  'tolerance_sha256': sha256_file('recon_tolerances.json')}
    waves, batch_of = [], {}
    for w in sorted(set(wave_of.values())):
        members = [u for u in ordered if wave_of[u] == w]
        batches = []
        for i in range(0, len(members), BATCH_MAX_UNITS):
            chunk = members[i:i + BATCH_MAX_UNITS]
            bid = f'w{w}-b{len(batches) + 1:02d}'
            nf = sorted({f['stat'] for u in chunk for f in forward[u] if f['kind'] == 'never_filled'})
            b = {'id': bid, 'units': chunk,
                 'write_targets': sorted(f'{TARGET_DB}.{n}' for u in chunk for n in units[u]), **base_batch}
            if nf:
                b['never_filled_refs'] = nf
            batches.append(b)
            for u in chunk:
                batch_of[u] = bid
        waves.append({'wave': w, 'depth': depth[members[0]], 'units': members, 'batches': batches})

    out_units = []
    for u in ordered:
        out_units.append({
            'id': u, 'wave': wave_of[u], 'batch': batch_of[u], 'order': position[u], 'depth': depth[u],
            'rows': unit_rows[u],
            'collections': [{'collection': n, 'root_table': colls[n]['root_table'],
                             'embedded_tables': [e['child_table'] for e in colls[n]['embeds']],
                             'rows': {t: rows[t] for t in coll_tables[n]}} for n in units[u]],
            'write_targets': sorted(f'{TARGET_DB}.{n}' for n in units[u]),
            'depends_on': [{'unit': d, 'via': sorted(v, key=lambda x: (x['collection'], x['table'], x['column']))}
                           for d, v in sorted(deps[u].items(), key=lambda kv: position[kv[0]])],
            'forward_refs': sorted(forward[u], key=lambda f: (f['kind'], f['stat'])),
            'tours': tours[u],
            'acceptance': {k: acceptance[u][k] for k in
                           ('raw_sql_failures', 'register_rows_owned', 'register_rows_recheck',
                            'sql_view_reports', 'mirrored_link_tables', 'crons_to_pause', 'storage_items')
                           if acceptance[u][k]},
        })
    return {
        'kind': 'migration-units', 'plan_step': 's3.5-units', 'generator': '.migration/derive_units.py',
        'plugin_sha': (MIG / 'plugin_sha').read_text().strip(),
        'mapping_version': mapping_version, 'mapping_sha256': SIGNED_MAPPING_SHA256,
        'recon_tolerances_version': tol_version, 'tolerance_sha256': base_batch['tolerance_sha256'],
        'fixture_manifest': FIXTURE_MANIFEST,
        'source_fingerprint': {'path': '.migration/source_fingerprint.json',
                               'row_counts_sha256': fp['row_counts_sha256']},
        'target_database': TARGET_DB,
        'rules': [' '.join(r.split()) for r in __doc__.split('Rules', 1)[1].split('\n- ')[1:]],
        'write_path_setters': [{'table': t, 'column': c, 'set_at': s} for (t, c), s in sorted(WRITE_PATH_SETTERS.items())],
        'shared_loader': {'path': SHARED_LOADER, 'landed_by': canary, 'batch': 'w1-b01',
                          'rule': 'one loader per run; later batches import it, never ship a copy'},
        'canary': {'unit': canary, 'rows': unit_rows[canary], 'why': 'smallest depth-0 unit by rows with at least one row'},
        'totals': {'collections': len(colls), 'units': len(units), 'waves': len(waves),
                   'batches': sum(len(w['batches']) for w in waves), 'rows': sum(unit_rows.values()),
                   'raw_sql_failures': len(failures), 'junction_refs': len(junction_refs),
                   'never_filled_refs': len(never_filled)},
        'waves': waves,
        'units': out_units,
        'crons_review_before_load': review_crons,
        'plugin_findings': PLUGIN_FINDINGS,
    }


def notes_section(d):
    L = [NOTES_HEADING, '',
         f"Generated by `{d['generator']}` from the signed spec {d['mapping_version']} "
         f"(sha256 `{d['mapping_sha256']}`) and the row counts in `.migration/source_fingerprint.json` "
         f"(row_counts_sha256 `{d['source_fingerprint']['row_counts_sha256']}`); machine copy `.migration/units.json`. "
         f"Plugin {d['plugin_sha']}.", '',
         f"{d['totals']['collections']} collections -> {d['totals']['units']} units in {d['totals']['waves']} waves "
         f"({d['totals']['batches']} batches of at most {BATCH_MAX_UNITS} units), {d['totals']['rows']} rows.", '',
         f"**Canary**: `{d['canary']['unit']}` ({d['canary']['rows']} row{'' if d['canary']['rows'] == 1 else 's'}), wave 1 alone; it lands the run's one "
         f"shared loader (`{d['shared_loader']['path']}`), which every later batch imports.", '',
         '### Rules', ''] + [f'- {r}' for r in d['rules']] + [
         '', 'Never-filled references that still order because installed code sets them:', ''] + [
         f"- `{s['table']}.{s['column']}`: `{s['set_at']}`" for s in d['write_path_setters']] + [
         '', '### Waves', '', '| wave | depth | batch | units (smallest first) | rows |', '|---|---|---|---|---|']
    rows = {u['id']: u['rows'] for u in d['units']}
    for w in d['waves']:
        for b in w['batches']:
            L.append(f"| {w['wave']} | {w['depth']} | {b['id']} | " + ', '.join(f'`{u}`' for u in b['units'])
                     + f" | {sum(rows[u] for u in b['units'])} |")
    L += ['', '### Units', '',
          'Order is the global migration order. Tables: root table first, embedded tables after it. '
          'Tours: test files under the scope addons and bridges that call `start_tour` and name one of the unit\'s '
          'models in `env[...]`.', '',
          '| order | unit | wave | batch | rows | collections and embedded tables | depends on | browser tours |',
          '|---|---|---|---|---|---|---|---|']
    for u in d['units']:
        cs = '; '.join(f"`{c['collection']}` ({', '.join(f'{t} {n}' for t, n in c['rows'].items())})" for c in u['collections'])
        dep = ', '.join(f"`{x['unit']}`" for x in u['depends_on']) or '-'
        tr = ', '.join(f"`{t['file']}`" for t in u['tours']) or '-'
        L.append(f"| {u['order']} | `{u['id']}` | {u['wave']} | {u['batch']} | {u['rows']} | {cs} | {dep} | {tr} |")
    L += ['', '### Acceptance per unit', '',
          'Raw-SQL failures (from `.migration/conformance.md`, per-unit list of 71) sit on the unit that completes '
          'every register row the test needs; a register row is owned by the first unit in migration order among '
          'the tables it names, and later units naming it re-check it. Reports and cron rows follow the same owner rule. '
          'Every unit pauses `base.autovacuum_job` during its load window.', '']
    for u in d['units']:
        a = u['acceptance']
        items = []
        if a.get('raw_sql_failures'):
            fams = defaultdict(int)
            for f in a['raw_sql_failures']:
                fams[f['family']] += 1
            items.append(f"raw-SQL failures {len(a['raw_sql_failures'])} ("
                         + ', '.join(f'{k} {v}' for k, v in sorted(fams.items())) + '): '
                         + '; '.join(f"{f['test']}" for f in a['raw_sql_failures']))
        if a.get('register_rows_owned'):
            items.append('owns register rows ' + ', '.join(f"{r['row']} (`{r['site']}`)" for r in a['register_rows_owned']))
        if a.get('register_rows_recheck'):
            items.append('re-checks register rows ' + ', '.join(f"{r['row']} (owner `{r['owner']}`)" for r in a['register_rows_recheck']))
        if a.get('sql_view_reports'):
            items.append('SQL-view reports ' + ', '.join(
                f"{r['report']} `{r['model']}` ({r['role']}" + (f" of `{r['owner']}`" if r['role'] == 'recheck' else '') + ')'
                for r in a['sql_view_reports']))
        if a.get('mirrored_link_tables'):
            items.append('mirrored link tables ' + ', '.join(
                f"`{r['relation']}` (`{r['model']}.{r['field']}`)" for r in a['mirrored_link_tables']))
        other = [c for c in a.get('crons_to_pause', []) if c['xmlid'] != 'base.autovacuum_job']
        if other:
            items.append('pause crons ' + ', '.join(f"`{c['xmlid']}` ({c['disp']}{', inactive' if not c['active'] else ''})" for c in other))
        if a.get('storage_items'):
            items.append('; '.join(f"{s['id']}: {s['text']}" for s in a['storage_items']))
        if u['forward_refs']:
            nf = [f for f in u['forward_refs'] if f['kind'] == 'never_filled']
            jn = [f for f in u['forward_refs'] if f['kind'] == 'junction']
            if nf:
                items.append('forward refs (never filled, listed as never_filled_refs) ' + '; '.join(
                    f"`{f['stat']}` -> `{f['to_unit']}`: {f['why']}" for f in nf))
            if jn:
                items.append('junction refs into later or same-wave units ' + ', '.join(
                    f"`{f['table']}.{f['column']}` -> `{f['to_unit']}`" for f in jn))
        L.append(f"- `{u['id']}`: " + ('; '.join(items) if items else 'autovacuum pause only'))
    L += ['', '### Scheduled jobs with only possible indirect reach (review before any load)', '',
          ', '.join(f"`{c['xmlid']}`" for c in d['crons_review_before_load']), '',
          '### Plugin findings', ''] + [f'- {f}' for f in d['plugin_findings']] + ['']
    return '\n'.join(L) + '\n'


def render():
    d = derive()
    units_text = json.dumps(d, indent=1, sort_keys=False) + '\n'
    notes = (MIG / 'NOTES.md').read_text()
    section = notes_section(d)
    if NOTES_HEADING in notes:
        head, _, rest = notes.partition(NOTES_HEADING)
        nxt = re.search(r'^## ', rest[1:], re.M)
        notes_text = head + section + ('\n' + rest[1 + nxt.start():] if nxt else '')
    else:
        notes_text = notes.rstrip('\n') + '\n\n' + section
    return units_text, notes_text


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='re-derive and fail when the committed outputs differ')
    args = ap.parse_args()
    units_text, notes_text = render()
    if args.check:
        stale = [n for n, t in (('units.json', units_text), ('NOTES.md', notes_text))
                 if not (MIG / n).exists() or (MIG / n).read_text() != t]
        if stale:
            sys.exit('stale: ' + ', '.join(stale))
        print('units.json and NOTES.md match the derivation')
        return
    (MIG / 'units.json').write_text(units_text)
    (MIG / 'NOTES.md').write_text(notes_text)
    print('wrote .migration/units.json and the NOTES.md section')


if __name__ == '__main__':
    main()
