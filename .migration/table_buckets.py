"""Copy proposal buckets into a cited census register; make no scope decisions."""

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path


def reference(filename: str, *parts: object) -> str:
    pointer = '/'.join(str(part).replace('~', '~0').replace('/', '~1') for part in parts)
    return f'.migration/{filename}#/{pointer}'


def build_buckets(census: dict, spec: dict) -> dict:
    tables = {}

    def add(name: str, bucket: str, proposalRef: str) -> None:
        if name not in census['tables']:
            raise ValueError(f'Proposal table absent from census: {name}')
        if name in tables:
            raise ValueError(f'Table assigned more than once: {name}')
        tables[name] = {
            'bucket': bucket,
            'status': 'proposal',
            'cite': [reference('census.json', 'tables', name), proposalRef],
        }

    for index, collection in enumerate(spec['collections']):
        add(collection['root_table'], 'root_collection',
            reference('mapping_spec.json', 'collections', index, 'root_table'))
        for embedIndex, embed in enumerate(collection.get('embeds', [])):
            add(embed['child_table'], 'embedded',
                reference('mapping_spec.json', 'collections', index, 'embeds', embedIndex, 'child_table'))
    for index, name in enumerate(spec['modeling']['excluded_tables']):
        add(name, 'transient_excluded', reference('mapping_spec.json', 'modeling', 'excluded_tables', index))
    missing = sorted(set(census['tables']) - tables.keys())
    if missing:
        raise ValueError(f'Census tables absent from proposal: {missing}')
    views = {}
    for index, name in enumerate(census['views']):
        if name in tables or name in views:
            raise ValueError(f'Duplicate census relation: {name}')
        views[name] = {
            'bucket': 'view_needs_review',
            'status': 'unmodeled',
            'cite': [reference('census.json', 'views', index)],
        }
    return {
        'kind': 'table-buckets',
        'version': 1,
        'mapping_version': spec['version'],
        'status': 'proposal_only',
        'scope_decision': None,
        'table_count': len(tables),
        'view_count': len(views),
        'counts': dict(sorted(collections.Counter(row['bucket'] for row in [*tables.values(), *views.values()]).items())),
        'tables': dict(sorted(tables.items())),
        'views': dict(sorted(views.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    migration = args.root / '.migration'
    censusPath, specPath = migration / 'census.json', migration / 'mapping_spec.json'
    result = build_buckets(json.loads(censusPath.read_text()), json.loads(specPath.read_text()))
    result['inputs_sha256'] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [censusPath, specPath]
    }
    (migration / 'table_buckets.json').write_text(json.dumps(result, indent=2) + '\n')
    sys.stdout.write(json.dumps({
        'tables': result['table_count'], 'views': result['view_count'], **result['counts'],
    }) + '\n')


if __name__ == '__main__':
    main()
