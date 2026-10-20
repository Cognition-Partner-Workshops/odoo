"""MongoDB storage for models declaring ``_storage = 'mongodb'``.

Implements ``.migration/orm_backend_contract.md``: one lazy client per
registry, documents keyed by the PostgreSQL integer ``id`` (``_id``), an
id-only PostgreSQL shadow table per model (id authority and FK target), and a
per-cursor undo log that replays MongoDB writes backwards when PostgreSQL
rolls back.  Writes to the two stores are not atomic: a process dying between
the MongoDB write and the PostgreSQL commit leaves a document whose shadow
row was never committed (or the reverse); :meth:`MongoStore.repair` removes
those orphans.
"""
from __future__ import annotations

import datetime as dt
import decimal
import json
import logging
import os
import re
import typing
from functools import partial
from pathlib import Path

if typing.TYPE_CHECKING:
    from odoo.sql_db import Cursor

    from .fields import Field
    from .models import BaseModel

_logger = logging.getLogger(__name__)

MIGRATION_DIR = Path(__file__).resolve().parents[2] / '.migration'
DEFAULT_MONGODB_URI_ENV = 'MONGODB_ATLAS_URI'


def camelize(name: str) -> str:
    """``product_tmpl_id`` -> ``productTmplId`` (the mapping spec convention)."""
    head, *tail = name.split('_')
    return head + ''.join(part[:1].upper() + part[1:] for part in tail)


def to_bson(value):
    """Normalize an SQL parameter (``convert_to_column_insert`` output) into a BSON value."""
    if value is None or isinstance(value, (bool, int, float, str, bytes, dt.datetime)):
        return value
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day)
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): to_bson(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_bson(v) for v in value]
    adapted = getattr(value, 'adapted', None)  # psycopg2 Json / Binary wrappers
    if adapted is not None:
        return to_bson(bytes(adapted) if isinstance(adapted, memoryview) else adapted)
    raise TypeError(f"Cannot store {value!r} in MongoDB")


NUMERIC_COLUMN_TYPES = ('numeric', 'float8')


def is_numeric_column_text(field, value) -> bool:
    """``Float`` (with ``digits``) and ``Monetary`` pass their rounded value to
    the column as a ``float_repr()`` string, which the numeric column casts.
    """
    return isinstance(value, str) and bool(field.column_type) and field.column_type[0] in NUMERIC_COLUMN_TYPES


def column_to_bson(field, value):
    """``to_bson`` plus the numeric column cast: BSON would otherwise store and
    compare the ``float_repr()`` string as a string."""
    value = to_bson(value)
    return float(value) if is_numeric_column_text(field, value) else value


class MongoUndoLog:
    """Undo entries of one PostgreSQL transaction, replayed on rollback."""

    def __init__(self, store: MongoStore, cr: Cursor):
        self.store = store
        self.cr = cr
        self.entries: list[tuple[str, str, list]] = []
        # one log per PostgreSQL transaction: replayed then dropped on
        # rollback, dropped on commit (the hooks run once per transaction)
        cr.prerollback.add(self._on_rollback)
        cr.postcommit.add(partial(store._discard_undo, cr))

    def _on_rollback(self) -> None:
        try:
            self.rollback_to(0)
        finally:
            self.store._discard_undo(self.cr)

    def mark(self) -> int:
        return len(self.entries)

    def append(self, kind: str, collection: str, payload: list) -> None:
        if payload:
            self.entries.append((kind, collection, payload))

    def rollback_to(self, mark: int) -> None:
        while len(self.entries) > mark:
            kind, collection, payload = self.entries.pop()
            coll = self.store.db[collection]
            try:
                # every replay is idempotent: it also works when the logged
                # operation was never applied (e.g. the write failed)
                if kind == 'insert':
                    coll.delete_many({'_id': {'$in': payload}})
                else:  # update / delete: restore the prior documents
                    for doc in payload:
                        coll.replace_one({'_id': doc['_id']}, doc, upsert=True)
            except Exception:
                _logger.exception("MongoDB undo failed for %s on %s; run repair", kind, collection)


class MongoStore:
    """One MongoDB client per registry; all collections live in the single allowed
    database, under a per-Odoo-database prefix unless the database is the migration one."""

    def __init__(self, registry):
        self.registry = registry
        self._client = None
        self._spec = None
        self._unique_messages: dict[tuple[str, str], str] = {}
        self._namespace_checked: set[str] = set()

    # ------------------------------------------------------------------
    # connection
    # ------------------------------------------------------------------
    @property
    def client(self):
        if self._client is None:
            import pymongo  # noqa: PLC0415

            from odoo.tools import config  # noqa: PLC0415
            # name of the environment variable holding the URI (the secret
            # itself never goes through the config)
            env_name = config.get('mongodb_uri') or DEFAULT_MONGODB_URI_ENV
            uri = os.environ.get(env_name)
            if not uri:
                raise RuntimeError(f"MongoDB URI environment variable {env_name!r} is not set")
            self._client = pymongo.MongoClient(uri, appname=f"odoo-{self.registry.db_name}")
        return self._client

    @property
    def database_name(self) -> str:
        with open(MIGRATION_DIR / 'allowed_targets.json', encoding='utf-8') as f:
            return json.load(f)['databases'][0]

    @property
    def db(self):
        return self.client[self.database_name]

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    # ------------------------------------------------------------------
    # mapping spec
    # ------------------------------------------------------------------
    @property
    def spec(self) -> dict:
        if self._spec is None:
            with open(MIGRATION_DIR / 'mapping_spec.json', encoding='utf-8') as f:
                spec = json.load(f)
            self._spec = {
                'version': spec['version'],
                'by_table': {c['root_table']: c for c in spec['collections']},
                'embeds': {
                    embed['child_table']: (c, embed)
                    for c in spec['collections']
                    for embed in c.get('embeds', ())
                    if embed.get('shape') == 'array'
                },
            }
        return self._spec

    def collection_spec(self, model: BaseModel) -> dict | None:
        return self.spec['by_table'].get(model._table)

    def spec_bson_type(self, model: BaseModel, fname: str) -> str | None:
        spec = self.collection_spec(model)
        return next((f['bson_type'] for f in spec['fields'] if f['source'] == fname), None) if spec else None

    def document_value(self, model: BaseModel, fname: str, value):
        """``column_to_bson`` plus the mapping spec's numeric type: ``decimal`` fields store
        Decimal128, with the scale of the column text (``'2.00'``) like the loaded rows."""
        field = model._fields[fname]
        value = to_bson(value)
        if self.spec_bson_type(model, fname) == 'decimal':
            from bson.decimal128 import Decimal128  # noqa: PLC0415
            if is_numeric_column_text(field, value):
                return Decimal128(value)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return Decimal128(str(value))
        return column_to_bson(field, value)

    @property
    def collection_prefix(self) -> str:
        """Per-Odoo-database namespace inside the allowed database.

        Only the migration database, named by the config key
        ``mongodb_migration_db``, reads and writes the spec collections; every
        other database (test and scratch installs) gets ``<db_name>__`` in
        front of each collection name, so a fresh install never touches the
        migrated documents.
        """
        from odoo.tools import config  # noqa: PLC0415
        db_name = self.registry.db_name
        return '' if db_name == config.get('mongodb_migration_db') else f'{db_name}__'

    def collection_name(self, model: BaseModel) -> str:
        spec = self.collection_spec(model)
        name = spec['collection'] if spec else camelize(model._table)
        prefix = self.collection_prefix
        if prefix and name not in self._namespace_checked and self._check_namespace(model, name, prefix + name):
            self._namespace_checked.add(name)
        return prefix + name

    def _check_namespace(self, model: BaseModel, name: str, prefixed: str) -> bool:
        """Fail closed instead of serving a migrated database from an empty namespace.

        A database with committed shadow ids whose documents sit in the
        unprefixed collection is the migration database started without
        ``mongodb_migration_db``: reads would return nothing and ``repair``
        would delete its shadow rows. Returns whether the prefixed namespace
        is established (documents in it), the only outcome worth caching: a
        negative probe may come from a snapshot older than a concurrent load.
        """
        if not self._has_committed_rows(model):
            return False
        if self.db[prefixed].estimated_document_count():
            return True
        if not self.db[name].estimated_document_count():
            return False
        db_name = self.registry.db_name
        raise RuntimeError(
            f"database {db_name!r} has committed ids for {model._name} but its documents are in the "
            f"unprefixed collection {name!r}: set mongodb_migration_db = {db_name} in the config file "
            f"if this is the migration database"
        )

    def _has_committed_rows(self, model: BaseModel) -> bool:
        """Committed shadow rows only, read with the current cursor so a table this
        transaction is altering cannot block: ``age(xmin) > 0`` excludes the rows
        the transaction itself (or one of its savepoints) inserted, i.e. the ids
        ``allocate_ids`` takes before the documents are written."""
        from odoo.tools import SQL  # noqa: PLC0415
        cr = model.env.cr
        cr.execute(SQL("SELECT to_regclass(%s)", model._table))
        if cr.fetchone()[0] is None:
            return False
        cr.execute(SQL("SELECT 1 FROM %s WHERE age(xmin) > 0 LIMIT 1", SQL.identifier(model._table)))
        return cr.fetchone() is not None

    def field_path(self, model: BaseModel, fname: str) -> str:
        if fname == 'id':
            return '_id'
        spec = self.collection_spec(model)
        if spec:
            for f in spec['fields']:
                if f['source'] == fname:
                    return f['target']
        return camelize(fname)

    def m2m_layout(self, model: BaseModel, field: Field) -> tuple | None:
        """Where a Many2many relation lives.

        Returns ``(owner_model_name, array_path, element_key)`` when the
        relation is an id-object array on a MongoDB document (d-m2m-arrays),
        or ``None`` when it stays a PostgreSQL relation table.
        """
        registry = self.registry
        if field.relation in self.spec['embeds']:
            coll, embed = self.spec['embeds'][field.relation]
            owner = next(
                (m for m in registry.mongodb_models if registry[m]._table == coll['root_table']),
                None,
            )
            if owner is None:
                return None
            return owner, embed['array_path'], embed['child_fields'][0]['target']
        candidates = sorted(
            (mname, fn)
            for mname, fn in registry.many2many_relations[field.relation, field.column1, field.column2]
            | registry.many2many_relations[field.relation, field.column2, field.column1]
            if mname in registry.mongodb_models
        )
        if not candidates:
            return None
        owner_name, owner_fname = candidates[0]
        owner_field = registry[owner_name]._fields[owner_fname]
        return owner_name, camelize(owner_fname), camelize(owner_field.column2)

    # ------------------------------------------------------------------
    # reads
    # ------------------------------------------------------------------
    def find(self, model: BaseModel, filter_: dict, projection=None, sort=None, skip=0, limit=None) -> list[dict]:
        coll = self.db[self.collection_name(model)]
        if sort and any(len(term) >= 4 or isinstance(term[0], dict) for term in sort):
            return list(coll.aggregate(self._parent_sort_pipeline(coll.name, filter_, projection, sort, skip, limit)))
        cursor = coll.find(filter_, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def _parent_sort_pipeline(cls, collection: str, filter_: dict, projection, sort: list, skip: int, limit) -> list[dict]:
        """Sort through many2one parents and/or on computed keys: a
        ``(path, direction, parent_sort, nulls_first, parent_collection)`` term joins the
        parent document (``$lookup``; recursively for the parent's own parent terms), a
        missing parent or parent value taking the requested NULLS placement (SQL default:
        last ascending, first descending); a term whose path is an expression (translated
        field: ``{'$ifNull': [...]}``, cross-store rank) is evaluated into a temporary
        field first."""
        stages, keys, temporary = cls._sort_stages(sort)
        pipeline: list[dict] = [{'$match': filter_}, *stages, {'$sort': dict(keys)}]
        if skip:
            pipeline.append({'$skip': skip})
        if limit:
            pipeline.append({'$limit': limit})
        if projection:
            pipeline.append({'$project': {k: 1 for k in projection} if isinstance(projection, (list, tuple))
                             else dict(projection)})
        else:
            pipeline.append({'$unset': temporary})
        return pipeline

    @classmethod
    def _sort_stages(cls, sort: list, tag: str = '') -> tuple[list[dict], list[tuple[str, int]], list[str]]:
        """Stages evaluating the sort keys of ``sort`` on the current document:
        ``(stages, [(key, direction)], temporary fields)``."""
        from bson import MaxKey, MinKey  # noqa: PLC0415
        stages: list[dict] = []
        keys: list[tuple[str, int]] = []
        temporary: list[str] = []
        computed: dict[str, dict] = {}
        for index, term in enumerate(sort):
            if len(term) == 2:
                path, direction = term
                if isinstance(path, dict):
                    path = f'__sort{tag}{index}'
                    computed[path] = term[0]
                    temporary.append(path)
                keys.append((path, direction))
                continue
            path, direction, parent_sort, nulls_first, parent_collection = term
            alias = f'_parent{tag}{index}'
            temporary.append(alias)
            missing = MinKey() if nulls_first == (direction == 1) else MaxKey()
            parent_stages, parent_keys, _ = cls._sort_stages(parent_sort, f'{tag}{index}_')
            stages += [
                {'$lookup': {'from': parent_collection, 'localField': path, 'foreignField': '_id', 'as': alias,
                             'pipeline': [*parent_stages, {'$project': {key: 1 for key, _ in parent_keys}}]}},
                {'$unwind': {'path': f'${alias}', 'preserveNullAndEmptyArrays': True}},
                {'$addFields': {f'{alias}.{key}': {'$ifNull': [f'${alias}.{key}', missing]} for key, _ in parent_keys}},
            ]
            keys += [(f'{alias}.{key}', parent_direction * direction) for key, parent_direction in parent_keys]
        if computed:
            stages.insert(0, {'$addFields': computed})
        return stages, keys, temporary

    def distinct(self, model: BaseModel, path: str, filter_: dict) -> list:
        return [v for v in self.db[self.collection_name(model)].distinct(path, filter_) if v is not None]

    def aggregate(self, model: BaseModel, pipeline: list[dict]) -> list[dict]:
        return list(self.db[self.collection_name(model)].aggregate(pipeline))

    def count(self, model: BaseModel, filter_: dict) -> int:
        return self.db[self.collection_name(model)].count_documents(filter_)

    # ------------------------------------------------------------------
    # writes (logged for rollback)
    # ------------------------------------------------------------------
    def _undo(self, cr: Cursor) -> MongoUndoLog:
        if cr._mongo_undo is None:
            cr._mongo_undo = MongoUndoLog(self, cr)
        return cr._mongo_undo

    def _discard_undo(self, cr: Cursor) -> None:
        cr._mongo_undo = None

    def allocate_ids(self, model: BaseModel, shadow_columns: list[str], shadow_rows: list[list]) -> list[int]:
        """Allocate ids from the model's PostgreSQL shadow table (the single id authority),
        writing the full-shadow column values of each row through (``_shadow_columns``, contract §4)."""
        from odoo.tools import SQL  # noqa: PLC0415
        cr = model.env.cr
        nextval = SQL("nextval(pg_get_serial_sequence(%s, 'id'))", model._table)
        cr.execute(SQL(
            "INSERT INTO %s (%s) VALUES %s RETURNING id",
            SQL.identifier(model._table),
            SQL(', ').join(map(SQL.identifier, ['id', *shadow_columns])),
            SQL(', ').join(SQL('(%s)', SQL(', ').join([nextval, *row])) for row in shadow_rows),
        ))
        return [row[0] for row in cr.fetchall()]

    def _raise_unique(self, model: BaseModel, exc) -> typing.NoReturn:
        """Map a duplicate-key error to the constraint's ValidationError (like psycopg's IntegrityError)."""
        from odoo.exceptions import ValidationError  # noqa: PLC0415
        from odoo.tools import format_list  # noqa: PLC0415
        details = getattr(exc, 'details', None) or {}
        errors = details.get('writeErrors') or [details]
        for error in errors:
            if error.get('code') == 11000:
                match = re.search(r"index: (\S+)", error.get('errmsg', ''))
                message = self._unique_messages.get((self.collection_name(model), match[1] if match else ''))
                if not message:
                    # like models._sql_error_to_exception for a UniqueViolation: the
                    # columns are the index keys (``keyValue``), mapped back to field names
                    paths = {self.field_path(model, f.name): f.name for f in model._fields.values() if f.store and f.column_type}
                    key_value = error.get('keyValue') or {}
                    columns = [paths.get(path, path) for path in key_value]
                    if columns:
                        names = [model._fields[c].string if c in model._fields else c for c in columns]
                        message = model.env._(
                            "The value for %(field_display)s already exists.\n\nDetail: %(detail)s\n",
                            field_display=f"'{', '.join(columns)}' ({format_list(model.env, names)})",
                            detail=f"Key ({', '.join(columns)})=({', '.join(map(str, key_value.values()))}) already exists.",
                        )
                raise ValidationError(message or model.env._("The operation cannot be completed: another record already has the same value for a unique key.")) from exc
        raise exc

    def insert_many(self, model: BaseModel, docs: list[dict]) -> None:
        if not docs:
            return
        import pymongo.errors  # noqa: PLC0415
        name = self.collection_name(model)
        # log before writing: a failed or ambiguous write is still undone
        self._undo(model.env.cr).append('insert', name, [doc['_id'] for doc in docs])
        try:
            self.db[name].insert_many(docs, ordered=True)
        except (pymongo.errors.DuplicateKeyError, pymongo.errors.BulkWriteError) as exc:
            self._raise_unique(model, exc)

    def update_many(self, model: BaseModel, ids: list[int], update: dict) -> None:
        if not ids or not update:
            return
        name = self.collection_name(model)
        coll = self.db[name]
        prior = list(coll.find({'_id': {'$in': ids}}))
        self._undo(model.env.cr).append('update', name, prior)
        coll.update_many({'_id': {'$in': ids}}, update)

    def bulk_update(self, model: BaseModel, updates: list[tuple[int, dict]]) -> None:
        """``updates``: list of ``(id, update_document)``."""
        if not updates:
            return
        import pymongo.errors  # noqa: PLC0415
        from pymongo import UpdateOne  # noqa: PLC0415
        name = self.collection_name(model)
        coll = self.db[name]
        prior = list(coll.find({'_id': {'$in': [id_ for id_, _ in updates]}}))
        self._undo(model.env.cr).append('update', name, prior)
        try:
            coll.bulk_write([UpdateOne({'_id': id_}, update) for id_, update in updates], ordered=True)
        except (pymongo.errors.DuplicateKeyError, pymongo.errors.BulkWriteError) as exc:
            self._raise_unique(model, exc)

    def delete_many(self, model: BaseModel, ids: list[int]) -> None:
        if not ids:
            return
        name = self.collection_name(model)
        coll = self.db[name]
        prior = list(coll.find({'_id': {'$in': ids}}))
        self._undo(model.env.cr).append('delete', name, prior)
        coll.delete_many({'_id': {'$in': ids}})

    # ------------------------------------------------------------------
    # schema
    # ------------------------------------------------------------------
    def ensure_shadow_table(self, model: BaseModel) -> None:
        """Create the shadow table (id authority and FK target) or, on a pre-existing table,
        relax the columns whose values moved to MongoDB: ``allocate_ids`` inserts only ``id``
        and the full-shadow columns (``_shadow_columns``, contract §4), so every other column
        loses its NOT NULL and default. The full-shadow columns are created when missing and
        written through by ``allocate_ids`` and ``_write_multi``; the other columns stay until
        the cutover reduction."""
        from odoo.tools import SQL, sql  # noqa: PLC0415
        cr = model.env.cr
        created = not sql.table_exists(cr, model._table)
        if created:
            sql.create_model_table(cr, model._table, f"{model._description} (MongoDB shadow: ids and {list(model._shadow_columns)})")
        columns = sql.table_columns(cr, model._table)
        shadow = [fname for fname in model._shadow_columns if fname in model._fields]  # loaded modules only
        missing = [fname for fname in shadow if fname not in columns]
        for fname in shadow:
            model._fields[fname].update_db_column(model, columns.get(fname))
        if created:
            return
        if missing:
            self._backfill_shadow_columns(model, missing)
        kept = {'id', *model._shadow_columns}
        cr.execute(SQL(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema AND table_name = %s "
            "AND (is_nullable = 'NO' OR column_default IS NOT NULL) "
            "ORDER BY ordinal_position", model._table,
        ))
        for (column,) in cr.fetchall():
            if column in kept:
                continue
            cr.execute(SQL(
                "ALTER TABLE %s ALTER COLUMN %s DROP NOT NULL, ALTER COLUMN %s DROP DEFAULT",
                SQL.identifier(model._table), SQL.identifier(column), SQL.identifier(column),
            ))
            _logger.info("Table %r: column %r moved to MongoDB, dropped NOT NULL and default", model._table, column)

    def _backfill_shadow_columns(self, model: BaseModel, fnames: list[str]) -> None:
        """Fill full-shadow columns just added to a populated shadow table from the documents,
        so the SQL readers see the current values instead of NULL."""
        from psycopg2.extras import Json  # noqa: PLC0415

        from odoo.tools import SQL  # noqa: PLC0415
        fields = [model._fields[fname] for fname in fnames]
        paths = [model._mongodb_path(field) for field in fields]

        def column_value(field, value):
            # jsonb columns (translated, company-dependent, properties) keep the whole document
            # value; other columns get the cache value, cast to the column type
            if value is None:
                return SQL("NULL::%s", SQL(field.column_type[1]))
            if field.column_type[0] == 'jsonb':
                return SQL("%s::jsonb", Json(value))
            return SQL("%s::%s", model._document_value_to_cache(field, value), SQL(field.column_type[1]))

        rows = [
            (doc['_id'], *(column_value(field, doc.get(path)) for field, path in zip(fields, paths)))
            for doc in self.db[self.collection_name(model)].find({}, dict.fromkeys(paths, 1))
        ]
        if not rows:
            return
        model.env.cr.execute(SQL(
            "UPDATE %s AS t SET %s FROM (VALUES %s) AS v (id, %s) WHERE t.id = v.id",
            SQL.identifier(model._table),
            SQL(', ').join(SQL('%s = v.%s', SQL.identifier(fname), SQL.identifier(fname)) for fname in fnames),
            SQL(', ').join(SQL('(%s)', SQL(', ').join(row)) for row in rows),
            SQL(', ').join(map(SQL.identifier, fnames)),
        ))
        _logger.info("Table %r: backfilled full-shadow columns %s for %d rows", model._table, fnames, len(rows))

    def ensure_collection(self, model: BaseModel) -> None:
        import pymongo  # noqa: PLC0415
        name = self.collection_name(model)
        if name not in self.db.list_collection_names(filter={'name': name}):
            self.db.create_collection(name)
        coll = self.db[name]
        existing = {tuple(map(tuple, ix['key'].items())) for ix in coll.list_indexes()}
        for keys, options in self.indexes_for(model):
            key_tuple = tuple((k, pymongo.ASCENDING if d == 1 else pymongo.DESCENDING) for k, d in keys)
            if key_tuple in existing:
                continue
            existing.add(key_tuple)
            coll.create_index(list(key_tuple), **options)

    def indexes_for(self, model: BaseModel) -> list[tuple[list, dict]]:
        """Indexes from the mapping spec plus the model's unique constraints/indexes."""
        from .table_objects import Constraint, Index  # noqa: PLC0415
        indexes: list[tuple[list, dict]] = []
        spec = self.collection_spec(model)
        if spec:
            for ix in spec.get('indexes', ()):
                indexes.append(([tuple(k) for k in ix['keys']], {'unique': True} if ix.get('unique') else {}))
            for nk in spec['decision'].get('natural_keys', ()):
                if any(col not in model._fields for col in nk['columns']):
                    continue  # column of a module not installed yet: indexed when that module loads the model
                definition = f"({', '.join(nk['columns'])})"
                indexes.append(self._unique_index(model, definition, nk['name'].removeprefix(f"{model._table}_"), None))
        if model._parent_store:  # child_of / parent_of and subtree rewrites: anchored prefix match
            indexes.append(([(self.field_path(model, 'parent_path'), 1)], {}))
        for field in model._fields.values():
            if field.type == 'many2many' and field.store and (layout := self.m2m_layout(model, field)) \
                    and layout[0] == model._name:
                indexes.append(([(f"{layout[1]}.{layout[2]}", 1)], {}))
        for name, obj in model._table_objects.items():
            if isinstance(obj, Index):
                definition = obj._index_definition(self.registry) if callable(obj._index_definition) else obj._index_definition
                if not definition:
                    continue
                if not obj.unique:
                    continue  # non-unique Odoo indexes are covered by the mapping spec indexes
                indexes.append(self._unique_index(model, definition, name, obj.message))
            elif isinstance(obj, Constraint):
                definition = obj._definition.strip()
                if definition.upper().startswith('UNIQUE'):
                    indexes.append(self._unique_index(model, definition[6:], name, obj.message))
                elif definition.upper().startswith('CHECK'):
                    model.pool.mongodb_checks[model._name, name] = parse_check(model, definition[5:], obj.message)
                else:
                    raise NotImplementedError(
                        f"{model._name}: constraint {name!r} ({definition}) has no MongoDB equivalent",
                    )
        return indexes

    def _unique_index(self, model: BaseModel, definition: str, name: str, message) -> tuple[list, dict]:
        """``(col1, col2) WHERE pred`` -> unique index keys, partial on nullable columns."""
        index_name = f"{model._table}_{name}"
        self._unique_messages[self.collection_name(model), index_name] = str(message) if message else ''
        definition = definition.strip()
        match = re.fullmatch(r"\((?P<cols>[^)]*)\)(?:\s+WHERE\s+(?P<pred>.+))?", definition, re.I | re.S)
        if not match:
            raise NotImplementedError(f"{model._name}: cannot translate unique index {definition!r} to MongoDB")
        columns = [c.strip().strip('"') for c in match['cols'].split(',')]
        keys = [(self.field_path(model, col), 1) for col in columns]
        partial_filter = {}
        if match['pred']:
            partial_filter = parse_partial_predicate(model, self, match['pred'])
        for col in columns:
            field = model._fields[col]
            if field not in self.registry.not_null_fields and not field.required:
                partial_filter.setdefault(self.field_path(model, col), {'$type': bson_type(field)})
        options = {'unique': True, 'name': index_name}
        if partial_filter:
            options['partialFilterExpression'] = partial_filter
        return keys, options

    # ------------------------------------------------------------------
    # repair
    # ------------------------------------------------------------------
    def repair(self, model: BaseModel) -> dict:
        """Remove documents without a committed shadow row and shadow rows without a document."""
        from odoo.tools import SQL  # noqa: PLC0415
        cr = model.env.cr
        cr.execute(SQL("SELECT id FROM %s", SQL.identifier(model._table)))
        shadow_ids = {row[0] for row in cr.fetchall()}
        coll = self.db[self.collection_name(model)]
        doc_ids = {doc['_id'] for doc in coll.find({}, {'_id': 1})}
        orphan_docs = sorted(doc_ids - shadow_ids)
        orphan_rows = sorted(shadow_ids - doc_ids)
        if orphan_docs:
            coll.delete_many({'_id': {'$in': orphan_docs}})
        if orphan_rows:
            cr.execute(SQL("DELETE FROM %s WHERE id IN %s", SQL.identifier(model._table), tuple(orphan_rows)))
        return {'documents_removed': len(orphan_docs), 'shadow_rows_removed': len(orphan_rows)}


def bson_type(field: Field) -> str:
    return {
        'integer': 'int', 'many2one': 'int', 'many2one_reference': 'int',
        'float': 'double', 'monetary': 'double',
        'boolean': 'bool', 'date': 'date', 'datetime': 'date', 'binary': 'binData',
    }.get(field.type, 'string')


_CHECK_TOKEN = re.compile(r"\s*(?:(?P<num>-?\d+(?:\.\d+)?)|'(?P<str>(?:[^']|'')*)'|(?P<op><>|!=|>=|<=|=|>|<|\(|\)|,)|(?P<word>[A-Za-z_][A-Za-z0-9_]*))")


def _tokenize_check(expression: str) -> list[tuple[str, typing.Any]]:
    tokens = []
    pos = 0
    expression = expression.strip()
    while pos < len(expression):
        m = _CHECK_TOKEN.match(expression, pos)
        if not m or m.end() == pos:
            raise NotImplementedError(f"Cannot parse CHECK expression at {expression[pos:]!r}")
        pos = m.end()
        if m['num'] is not None:
            tokens.append(('lit', float(m['num']) if '.' in m['num'] else int(m['num'])))
        elif m['str'] is not None:
            tokens.append(('lit', m['str'].replace("''", "'")))
        elif m['op'] is not None:
            tokens.append(('op', m['op']))
        else:
            word = m['word']
            tokens.append(('kw', word.upper()) if word.upper() in ('AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'TRUE', 'FALSE') else ('name', word))
    return tokens


def parse_check(model: BaseModel, expression: str, message: str):
    """Parse a SQL ``CHECK (...)`` body into a Python predicate ``f(record) -> bool``.

    Supports ``=``, ``!=``/``<>``, ``<``, ``<=``, ``>``, ``>=``, ``IN``,
    ``IS [NOT] NULL``, ``AND``/``OR``/``NOT`` and parentheses; anything else
    raises :class:`NotImplementedError` at ``_auto_init`` so a lost invariant
    is loud.
    """
    tokens = _tokenize_check(expression)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else (None, None)

    def take(expected=None):
        nonlocal pos
        tok = peek()
        if expected is not None and tok != expected:
            raise NotImplementedError(f"Unsupported CHECK expression {expression!r} (near {tok})")
        pos += 1
        return tok

    def value_of(tok):
        kind, val = tok
        if kind == 'lit':
            return lambda rec: val
        if kind == 'kw' and val in ('TRUE', 'FALSE', 'NULL'):
            const = {'TRUE': True, 'FALSE': False, 'NULL': None}[val]
            return lambda rec: const
        if kind == 'name':
            field = model._fields[val]
            getter = field.expression_getter(val)

            def get(rec):
                v = getter(rec)
                return None if v is False and field.type not in ('boolean',) else v
            return get
        raise NotImplementedError(f"Unsupported CHECK expression {expression!r} (near {tok})")

    def combine(left, right, any_of):
        if any_of:
            return lambda rec: left(rec) or right(rec)
        return lambda rec: left(rec) and right(rec)

    def parse_or():
        pred = parse_and()
        while peek() == ('kw', 'OR'):
            take()
            pred = combine(pred, parse_and(), True)
        return pred

    def parse_and():
        pred = parse_not()
        while peek() == ('kw', 'AND'):
            take()
            pred = combine(pred, parse_not(), False)
        return pred

    def parse_not():
        if peek() == ('kw', 'NOT'):
            take()
            inner = parse_not()
            return lambda rec: not inner(rec)
        return parse_comparison()

    def parse_comparison():
        if peek() == ('op', '('):
            take()
            inner = parse_or()
            take(('op', ')'))
            return inner
        left = value_of(take())
        kind, op = peek()
        if (kind, op) == ('kw', 'IS'):
            take()
            negate = peek() == ('kw', 'NOT') and take()
            take(('kw', 'NULL'))
            return (lambda rec: (left(rec) is not None) if negate else (left(rec) is None))
        if (kind, op) == ('kw', 'IN'):
            take()
            take(('op', '('))
            items = [value_of(take())]
            while peek() == ('op', ','):
                take()
                items.append(value_of(take()))
            take(('op', ')'))
            return lambda rec: left(rec) in [item(rec) for item in items]
        if kind != 'op' or op not in ('=', '!=', '<>', '<', '<=', '>', '>='):
            raise NotImplementedError(f"Unsupported CHECK expression {expression!r} (near {(kind, op)})")
        take()
        right = value_of(take())
        import operator as _op  # noqa: PLC0415
        fn = {'=': _op.eq, '!=': _op.ne, '<>': _op.ne, '<': _op.lt, '<=': _op.le, '>': _op.gt, '>=': _op.ge}[op]

        def compare(rec):
            a, b = left(rec), right(rec)
            if a is None or b is None:
                return True  # SQL NULL comparisons do not fail a CHECK
            return fn(a, b)
        return compare

    predicate = parse_or()
    if pos != len(tokens):
        raise NotImplementedError(f"Unsupported CHECK expression {expression!r} (trailing {tokens[pos:]})")
    return predicate, message


def parse_partial_predicate(model: BaseModel, store: MongoStore, predicate: str) -> dict:
    """``WHERE`` predicate of a partial unique index -> ``partialFilterExpression``."""
    predicate = predicate.strip()
    if m := re.fullmatch(r"(\w+)\s+IS\s+TRUE", predicate, re.I):
        return {store.field_path(model, m[1]): True}
    if m := re.fullmatch(r"(\w+)\s+IS\s+NOT\s+NULL", predicate, re.I):
        return {store.field_path(model, m[1]): {'$type': bson_type(model._fields[m[1]])}}
    if m := re.fullmatch(r"(\w+)\s*=\s*'([^']*)'", predicate, re.I):
        return {store.field_path(model, m[1]): m[2]}
    raise NotImplementedError(f"{model._name}: cannot translate index predicate {predicate!r} to MongoDB")
