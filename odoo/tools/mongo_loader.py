# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""The run's one loader: source rows (or the target-shaped fixture) into MongoDB.

Every batch loads its units through this entry point::

    python -I odoo/tools/mongo_loader.py --mapping .migration/mapping_spec.json \\
        --collections ormSignalingAssets --source-dsn-secret ODOO_PG_RO_DSN \\
        --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt16

It needs only pymongo and psycopg2 or psycopg, so it also runs outside the
Odoo environment (``-I`` keeps ``odoo/tools`` off ``sys.path``).
``--fixture-manifest`` loads the shared synthetic fixture instead of the source.
Each run drops and recreates the selected collections, creates their declared
indexes and checks the loaded counts. The source is read in a read-only
transaction. Secrets are passed by environment variable name only.
"""
import argparse
import datetime
import decimal
import gzip
import importlib
import hashlib
import json
import os
import sys
from pathlib import Path

UNSUPPORTED_EMBED_KEYS = ('overflow', 'copied_fields')
UNSUPPORTED_DECISION_SHAPES = ('polymorphic', 'attribute')


class LoadError(Exception):
    pass


def _secret(name):
    value = os.environ.get(name)
    if not value:
        raise LoadError(f"secret {name} is not set in the environment")
    return value


def source_connect_params(value):
    """PostgreSQL secret: the harness's JSON form, or a libpq DSN string."""
    try:
        parsed = json.loads(value)
    except ValueError:
        return {'dsn': value}, None
    if not isinstance(parsed, dict) or any(not parsed.get(k) for k in ('user', 'password', 'host', 'database')):
        raise LoadError("source secret JSON must have user, password, host, database")
    params = {'user': parsed['user'], 'password': parsed['password'], 'host': parsed['host'],
              'dbname': parsed['database'], 'port': int(parsed.get('port', 5432))}
    if parsed.get('sslmode'):
        params['sslmode'] = parsed['sslmode']
    return params, parsed.get('schema')


def convert(value, bson_type):
    """Convert one source value to the field's declared BSON type."""
    from bson import Binary, Decimal128  # noqa: PLC0415

    if value is None:
        return None
    if bson_type == 'date':
        if isinstance(value, datetime.datetime):
            if value.tzinfo is not None:
                value = value.astimezone(datetime.UTC).replace(tzinfo=None)
        elif isinstance(value, datetime.date):
            value = datetime.datetime(value.year, value.month, value.day)
        return value.replace(microsecond=value.microsecond // 1000 * 1000)
    if bson_type == 'decimal':
        return Decimal128(decimal.Decimal(value))
    if bson_type in ('int', 'long'):
        return int(value)
    if bson_type == 'double':
        return float(value)
    if bson_type == 'bool':
        return bool(value)
    if bson_type == 'binData':
        return Binary(bytes(value))
    if bson_type == 'string':
        return value if isinstance(value, str) else str(value)
    return value


def _check_supported(spec_collection):
    name = spec_collection['collection']
    shape = spec_collection.get('decision', {}).get('shape')
    if shape in UNSUPPORTED_DECISION_SHAPES:
        raise LoadError(f"{name}: shape {shape} is not supported by the loader yet")
    for embed in spec_collection.get('embeds', []):
        bad = [key for key in UNSUPPORTED_EMBED_KEYS if key in embed]
        if bad or embed.get('shape', 'array') not in ('array', 'subdocument'):
            raise LoadError(f"{name}.{embed['array_path']}: {bad or embed.get('shape')} is not supported by the loader yet")


def _pg_driver():
    try:
        import psycopg2 as driver  # noqa: PLC0415
    except ImportError:
        import psycopg as driver  # noqa: PLC0415
    return driver


def _select(cr, table, columns, order):
    sql = importlib.import_module(_pg_driver().__name__ + '.sql')

    query = sql.SQL("SELECT {} FROM {} ORDER BY {}").format(
        sql.SQL(', ').join(map(sql.Identifier, columns)), sql.Identifier(table),
        sql.SQL(', ').join(map(sql.Identifier, order)))
    cr.execute(query)
    return cr.fetchall()


def _key_targets(key):
    target = key['target']
    return [target] if isinstance(target, str) else list(target)


def source_documents(cr, spec_collection):
    """Build the target documents of one collection from the source rows."""
    key = spec_collection['key']
    key_columns, key_targets = key['source'], _key_targets(key)
    key_types = {f['source']: f['bson_type'] for f in spec_collection.get('decision', {}).get('key_fields', [])}
    fields = spec_collection['fields']
    columns = list(dict.fromkeys(key_columns + [f['source'] for f in fields]
                                 + [c for e in spec_collection.get('embeds', []) for c in e['parent_ref']]))
    documents, by_ref = [], {}
    for row in _select(cr, spec_collection['root_table'], columns, key_columns):
        values = dict(zip(columns, row))
        document = {target: convert(values[source], key_types.get(source, 'int'))
                    for source, target in zip(key_columns, key_targets)}
        for field in fields:
            document[field['target']] = convert(values[field['source']], field['bson_type'])
        documents.append(document)
        for embed in spec_collection.get('embeds', []):
            ref = tuple(values[c] for c in embed['parent_ref'])
            by_ref.setdefault(embed['array_path'], {})[ref] = document
    for embed in spec_collection.get('embeds', []):
        element_key = embed['key']
        element_fields = list(zip(element_key['source'], _key_targets(element_key)))
        child_types = {f['source']: f['bson_type'] for f in embed.get('child_fields', [])}
        element_fields = [(s, t, child_types.get(s, 'int')) for s, t in element_fields]
        element_fields += [(f['source'], f['target'], f['bson_type']) for f in embed.get('fields', [])]
        child_columns = list(dict.fromkeys(embed['parent_key'] + [s for s, _t, _b in element_fields]))
        parents = by_ref.get(embed['array_path'], {})
        for document in parents.values():
            if embed.get('shape', 'array') == 'array':
                document[embed['array_path']] = []
        for row in _select(cr, embed['child_table'], child_columns, child_columns):
            values = dict(zip(child_columns, row))
            parent = parents.get(tuple(values[c] for c in embed['parent_key']))
            if parent is None:
                continue
            element = {t: convert(values[s], b) for s, t, b in element_fields}
            if embed.get('shape', 'array') == 'array':
                parent[embed['array_path']].append(element)
            else:
                parent[embed['array_path']] = element
    return documents


def fixture_documents(manifest_path, name):
    from bson import json_util  # noqa: PLC0415

    manifest = json.loads(manifest_path.read_text())
    entry = manifest['files'][name]
    path = (manifest_path.parent / entry['path']).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        raise LoadError(f"fixture checksum mismatch: {name}")
    with gzip.open(path, 'rt') as stream:
        documents = [json_util.loads(line) for line in stream if line.strip()]
    if len(documents) != manifest['row_counts'][name]:
        raise LoadError(f"fixture count mismatch: {name}")
    return documents, manifest


def write_collection(database, spec_collection, documents):
    """Drop, recreate, insert, index and count one collection."""
    name = spec_collection['collection']
    database.drop_collection(name)
    target = database.create_collection(name)
    if documents:
        target.insert_many(documents, ordered=True)
    for index in spec_collection.get('indexes', []):
        options = {k: index[k] for k in ('unique', 'sparse', 'partialFilterExpression', 'name', 'expireAfterSeconds') if k in index}
        target.create_index([tuple(k) for k in index['keys']], **options)
    actual = target.count_documents({})
    if actual != len(documents):
        raise LoadError(f"{name}: loaded {actual} documents, expected {len(documents)}")
    return actual


def load(args):
    from pymongo import MongoClient  # noqa: PLC0415

    allowed = json.loads(Path(args.allowed_targets_file).read_text())
    if args.target_db not in allowed.get('databases', []):
        raise LoadError(f"{args.target_db} is not in {args.allowed_targets_file}")
    spec_bytes = Path(args.mapping).read_bytes()
    spec = json.loads(spec_bytes)
    by_name = {c['collection']: c for c in spec['collections']}
    names = [n.strip() for n in args.collections.split(',') if n.strip()]
    unknown = [n for n in names if n not in by_name]
    if not names or unknown:
        raise LoadError(f"unknown or empty --collections: {unknown}")
    for name in names:
        _check_supported(by_name[name])
    prepared = {}
    if args.fixture_manifest:
        for name in names:
            documents, manifest = fixture_documents(Path(args.fixture_manifest), name)
            if manifest['spec_sha256'] != hashlib.sha256(spec_bytes).hexdigest():
                raise LoadError("fixture is stale against the mapping spec")
            prepared[name] = documents
    else:
        driver = _pg_driver()
        params, schema = source_connect_params(_secret(args.source_dsn_secret))
        if 'dsn' in params and driver.__name__ == 'psycopg':
            params = {'conninfo': params['dsn']}
        with driver.connect(**params) as conn:
            if driver.__name__ == 'psycopg':
                conn.read_only = True
            else:
                conn.set_session(readonly=True)
            with conn.cursor() as cr:
                if schema:
                    cr.execute("SELECT set_config('search_path', %s, true)", [schema])
                for name in names:
                    prepared[name] = source_documents(cr, by_name[name])
            conn.rollback()
        conn.close()
    with MongoClient(_secret(args.target_uri_secret), serverSelectionTimeoutMS=10000) as client:
        database = client[args.target_db]
        report = {name: write_collection(database, by_name[name], documents)
                  for name, documents in prepared.items()}
    print(json.dumps({'mapping_version': spec['version'],
                      'mapping_sha256': hashlib.sha256(spec_bytes).hexdigest(),
                      'source': 'fixture' if args.fixture_manifest else 'source',
                      'target_db': args.target_db, 'counts': report}, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--mapping', default='.migration/mapping_spec.json')
    parser.add_argument('--collections', required=True)
    parser.add_argument('--source-dsn-secret')
    parser.add_argument('--fixture-manifest')
    parser.add_argument('--target-uri-secret', required=True)
    parser.add_argument('--target-db', required=True)
    parser.add_argument('--allowed-targets-file', default='.migration/allowed_targets.json')
    args = parser.parse_args(argv)
    if bool(args.source_dsn_secret) == bool(args.fixture_manifest):
        parser.error("give exactly one of --source-dsn-secret and --fixture-manifest")
    try:
        load(args)
    except LoadError as error:
        print(f"load refused: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
