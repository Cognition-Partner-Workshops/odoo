# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""MongoDB storage path for models that opt in with ``_storage = 'mongodb'``.

A model stored in MongoDB keeps an *id shadow* table on PostgreSQL: the same
table name reduced to ``id SERIAL PRIMARY KEY`` (existing data columns are made
nullable, never dropped).  The shadow allocates ids from ``<table>_id_seq``,
keeps every foreign key from tables that stay on PostgreSQL resolving, and
answers :meth:`BaseModel.exists`.  Field values live in a document of the
collection the mapping spec (``.migration/mapping_spec.json``) assigns to the
model's table: a root collection keyed by ``_id``, or an array embedded in a
parent collection.  Many2many relation tables follow the same spec: a
PostgreSQL table (default), an array of the owning document, or a collection.

Domains are rendered to MongoDB filters; conditions that cross a store boundary
(a many2one into PostgreSQL, a one2many from a PostgreSQL model, ...) are
resolved in two steps: the comodel's own store answers with ids, the other
side filters on them.  Writes done through this module are journaled on the
cursor so that a PostgreSQL rollback (full, or to a savepoint) undoes them.

Test isolation: collections are prefixed with ``<dbname>__`` unless the Odoo
config option ``mongodb_migration_db`` names the current PostgreSQL database.
The MongoDB database is ``mongodb_database`` (default: the first entry of
``.migration/allowed_targets.json``) on the cluster whose URI is held by the
environment variable named by ``mongodb_uri`` (default ``MONGODB_ATLAS_URI``).
"""
from __future__ import annotations

import datetime
import decimal
import json
import logging
import os
import re
import typing
from collections import defaultdict

from bson.decimal128 import Decimal128
from pymongo import ASCENDING, MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, OperationFailure
from psycopg2.extensions import QuotedString
from psycopg2.extras import Json as PsycopgJson

from odoo.tools import config
from odoo.tools.misc import OrderedSet
from odoo.tools.sql import SQL
from odoo.tools.translate import StoredTranslations

from .domains import (
    Domain, DomainAnd, DomainBool, DomainCondition, DomainCustom, DomainNary, DomainNot,
    NEGATIVE_CONDITION_OPERATORS,
)
from .query import Query, TableSQL
from .utils import READ_GROUP_TIME_GRANULARITY, parse_field_expr

if typing.TYPE_CHECKING:
    from collections.abc import Iterable
    from .fields import Field
    from .models import BaseModel
    from .table_objects import TableObject
    from .registry import Registry

_logger = logging.getLogger(__name__)

STORAGE_MONGODB = 'mongodb'
FETCH_BATCH = 1000


def camel(name: str) -> str:
    """ ``product_tmpl_id`` -> ``productTmplId`` (the proposer's target naming). """
    first, *rest = name.split('_')
    return first + ''.join(part[:1].upper() + part[1:] for part in rest)


def is_mongodb(model) -> bool:
    return getattr(model, '_storage', None) == STORAGE_MONGODB


# ---------------------------------------------------------------------------
# Mapping spec
# ---------------------------------------------------------------------------

def _field_bson_type(field: Field) -> str:
    if field.translate or field.company_dependent or field.type in ('json', 'properties', 'properties_definition'):
        return 'object'
    return {
        'integer': 'int', 'many2one': 'int', 'many2one_reference': 'int',
        'float': 'double', 'monetary': 'double',
        'boolean': 'bool',
        'date': 'date', 'datetime': 'date',
        'binary': 'binary',
    }.get(field.type, 'string')


class CollectionSpec:
    """ Where a table lives: a root collection (``array_path`` is None) or an
    array embedded in the document of ``parent_table``. """

    def __init__(self, table: str, collection: str, fields: dict[str, tuple[str, str]],
                 key_target, indexes: list | None = None,
                 array_path: str | None = None, parent_table: str | None = None,
                 parent_column: str | None = None, key_source: list[str] | None = None):
        self.table = table
        self.collection = collection
        self.fields = fields              # source column -> (target, bson_type)
        self.key_target = key_target      # '_id', 'id' or a list of targets
        self.key_source = key_source or ['id']
        self.indexes = indexes or []
        self.array_path = array_path
        self.parent_table = parent_table
        self.parent_column = parent_column

    @property
    def embedded(self) -> bool:
        return self.array_path is not None

    def target(self, column: str) -> str:
        if column == 'id':
            return '_id'
        entry = self.fields.get(column)
        return entry[0] if entry else camel(column)

    def bson_type(self, column: str, field: Field | None = None) -> str:
        entry = self.fields.get(column)
        if entry:
            return entry[1]
        return _field_bson_type(field) if field is not None else 'string'


def _parse_fields(entries) -> dict[str, tuple[str, str]]:
    return {f['source']: (f['target'], f.get('bson_type') or 'string') for f in entries}


class MappingSpec:
    """ The committed mapping spec, indexed by source table. """

    def __init__(self, data: dict | None):
        self.version = (data or {}).get('version')
        self.by_table: dict[str, CollectionSpec] = {}
        for coll in (data or {}).get('collections', ()):
            self.add_collection(coll)

    def add_collection(self, coll: dict) -> None:
        key = coll.get('key') or {'source': ['id'], 'target': '_id'}
        self.by_table[coll['root_table']] = CollectionSpec(
            coll['root_table'], coll['collection'], _parse_fields(coll.get('fields', ())),
            key['target'], coll.get('indexes'), key_source=key['source'],
        )
        for emb in coll.get('embeds', ()):
            self.by_table[emb['child_table']] = CollectionSpec(
                emb['child_table'], coll['collection'], _parse_fields(emb.get('fields', ())),
                emb['key']['target'], array_path=emb['array_path'], parent_table=coll['root_table'],
                parent_column=emb['parent_key'][0], key_source=emb['key']['source'],
            )

    def for_table(self, table: str) -> CollectionSpec | None:
        return self.by_table.get(table)


def _own_spec(own: dict | list) -> MappingSpec:
    """ A model's ``_mongodb_spec``: one collection entry, or a list of them
    (the model's collection plus the relation tables it owns). """
    return MappingSpec({'collections': own if isinstance(own, list) else [own]})


# ---------------------------------------------------------------------------
# Value conversion between the ORM's column format and BSON
# ---------------------------------------------------------------------------

def _unwrap_json(value):
    adapted = getattr(value, 'adapted', None)       # PsycopgJson
    return adapted if adapted is not None else value


def to_bson(value, bson_type: str):
    """ Convert a value in the ORM's column (SQL parameter) format to BSON. """
    if value is None or value is False and bson_type != 'bool':
        return None
    value = _unwrap_json(value)
    if bson_type == 'decimal':
        if isinstance(value, Decimal128):
            return value
        return Decimal128(value if isinstance(value, decimal.Decimal) else decimal.Decimal(str(value)))
    if bson_type == 'double':
        return float(value)
    if bson_type == 'int':
        return int(value)
    if bson_type == 'bool':
        return bool(value)
    if bson_type == 'date':
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if isinstance(value, str):
            return datetime.datetime.fromisoformat(value)
        return value
    if bson_type == 'binary':
        return bytes(value) if isinstance(value, memoryview) else value
    if bson_type == 'object':
        if isinstance(value, StoredTranslations):
            return dict(value)
        return value
    if isinstance(value, decimal.Decimal):
        return Decimal128(value)
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return datetime.datetime(value.year, value.month, value.day)
    return value


def from_bson(value, field: Field):
    """ Convert a BSON value to what :meth:`Field._insert_cache` expects from a
    PostgreSQL row. """
    if value is None:
        return None
    if isinstance(value, Decimal128):
        value = value.to_decimal()
    if field.type in ('float', 'monetary'):
        return float(value)
    if field.type == 'integer' or field.type == 'many2one':
        return int(value)
    if field.type == 'date' and isinstance(value, datetime.datetime):
        return value.date()
    if field.type == 'datetime' and isinstance(value, datetime.datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    return value


# ---------------------------------------------------------------------------
# Undo journal: MongoDB writes follow the PostgreSQL transaction
# ---------------------------------------------------------------------------

class MongoJournal:
    """ Inverse operations of the MongoDB writes made through a cursor, undone
    on rollback (full or to a savepoint, see :class:`odoo.sql_db.Savepoint`).

    MongoDB writes are visible to other cursors as soon as they are made (they
    are not part of the PostgreSQL transaction): the undo of an update only
    restores a value this cursor still holds, so a value committed in between
    by another cursor is kept. Inserts and deletes have no such race on a
    record's own id (ids come from the shadow table's sequence). """

    def __init__(self, cr):
        self.cr = cr
        self.ops: list = []

    def record(self, undo) -> None:
        if not self.ops:
            self.cr.prerollback.add(self.rollback)
            self.cr.postcommit.add(self.clear)
        self.ops.append(undo)

    def mark(self) -> int:
        return len(self.ops)

    def rollback_to(self, mark: int) -> None:
        pending, self.ops[mark:] = self.ops[mark:], []
        for undo in reversed(pending):
            undo()

    def rollback(self) -> None:
        self.rollback_to(0)

    def clear(self) -> None:
        self.ops.clear()


# ---------------------------------------------------------------------------
# Store: one per registry
# ---------------------------------------------------------------------------

def _repo_root() -> str:
    return os.path.dirname(os.path.abspath(config.root_path))


class MongoStore:
    """ Connection, naming and document primitives for one registry. """

    def __init__(self, registry: Registry):
        self.registry = registry
        uri_env = config.get('mongodb_uri') or 'MONGODB_ATLAS_URI'
        uri = os.environ.get(uri_env)
        if not uri:
            raise RuntimeError(f"MongoDB storage: environment variable {uri_env!r} (config 'mongodb_uri') is not set")
        self.client = MongoClient(uri, appname=f"odoo:{registry.db_name}")
        self.db = self.client[config.get('mongodb_database') or self._default_database()]
        migration_db = config.get('mongodb_migration_db')
        self.prefix = '' if migration_db and migration_db == registry.db_name else f"{registry.db_name}__"
        self.spec = self._load_spec()
        self._storages: dict[str, CollectionSpec] = {}

    @staticmethod
    def _default_database() -> str:
        path = os.path.join(_repo_root(), '.migration', 'allowed_targets.json')
        try:
            with open(path, encoding='utf-8') as fh:
                return json.load(fh)['databases'][0]
        except (OSError, KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(f"MongoDB storage: set config 'mongodb_database' ({path} unusable: {exc})") from exc

    @staticmethod
    def _load_spec() -> MappingSpec:
        path = config.get('mongodb_mapping_spec') or os.path.join(_repo_root(), '.migration', 'mapping_spec.json')
        if not os.path.exists(path):
            _logger.warning("MongoDB storage: no mapping spec at %s, using camelCase defaults", path)
            return MappingSpec(None)
        with open(path, encoding='utf-8') as fh:
            return MappingSpec(json.load(fh))

    # -- naming --------------------------------------------------------------

    def storage(self, model: BaseModel) -> CollectionSpec:
        """ The spec entry of a model's table (its own ``_mongodb_spec``, the
        mapping spec, or camelCase defaults). """
        spec = self._storages.get(model._name)
        if spec is None:
            own = getattr(model, '_mongodb_spec', None)
            if own:
                spec = _own_spec(own).for_table(model._table)
            else:
                spec = self.spec.for_table(model._table)
            if spec is None:
                spec = CollectionSpec(model._table, camel(model._table), {}, '_id')
            self._storages[model._name] = spec
        return spec

    def table_storage(self, table: str, owner: BaseModel | None = None) -> CollectionSpec | None:
        """ The spec entry of a relation table, or None when it stays on PostgreSQL. """
        if owner is not None and (own := getattr(owner, '_mongodb_spec', None)):
            spec = _own_spec(own).for_table(table)
            if spec:
                return spec
        return self.spec.for_table(table)

    def collection(self, name: str):
        return self.db[self.prefix + name]

    def model_collection(self, model: BaseModel):
        return self.collection(self.storage(model).collection)

    def path(self, model: BaseModel, field_name: str) -> str:
        return self.storage(model).target(field_name)

    def bson_type(self, model: BaseModel, field: Field) -> str:
        return self.storage(model).bson_type(field.name, field)

    # -- journal -------------------------------------------------------------

    @staticmethod
    def journal(cr) -> MongoJournal:
        journal = getattr(cr, '_mongo_journal', None)
        if journal is None:
            journal = cr._mongo_journal = MongoJournal(cr)
            cr.savepoint_listeners.append(journal)
        return journal

    # -- schema --------------------------------------------------------------

    def ensure_indexes(self, model: BaseModel) -> None:
        spec = self.storage(model)
        if spec.embedded:
            return
        coll = self.model_collection(model)
        for index in spec.indexes:
            keys = index.get('keys')
            if not isinstance(keys, list) or not keys:
                continue
            key_spec = [(k[0], k[1]) if isinstance(k, list) else (k, ASCENDING) for k in keys]
            if key_spec == [('_id', ASCENDING)]:
                continue
            try:
                coll.create_index(key_spec, unique=bool(index.get('unique')))
            except OperationFailure as exc:
                _logger.warning("MongoDB storage: index %s on %s not created: %s", key_spec, coll.name, exc)

    # -- journaled primitives ---------------------------------------------------

    def insert_docs(self, cr, coll, docs: list[dict], table: str = '') -> None:
        if not docs:
            return
        try:
            coll.insert_many(docs, ordered=True)
        except BulkWriteError as exc:
            if inserted := [doc['_id'] for doc in docs[:exc.details.get('nInserted', 0)]]:
                coll.delete_many({'_id': {'$in': inserted}})
            _raise_bulk_error(cr, coll, exc, table)
        ids = [doc['_id'] for doc in docs]
        self.journal(cr).record(lambda: coll.delete_many({'_id': {'$in': ids}}))

    def delete_docs(self, cr, coll, ids: list) -> list[dict]:
        if not ids:
            return []
        old = list(coll.find({'_id': {'$in': ids}}))
        coll.delete_many({'_id': {'$in': ids}})
        if old:
            self.journal(cr).record(lambda: coll.insert_many(old))
        return old

    def update_docs(self, cr, coll, updates: dict[int, dict[str, object]], table: str = '') -> None:
        """ ``$set`` per-document values (``{_id: {path: value}}``); the touched
        top-level paths are snapshotted for undo. """
        if not updates:
            return
        ids = list(updates)
        tops = sorted({p.split('.', 1)[0] for values in updates.values() for p in values})
        old = list(coll.find({'_id': {'$in': ids}}, {top: 1 for top in tops}))

        def undo():
            for doc in old:
                written = updates[doc['_id']]
                for top in tops:
                    # per field, and only where the document still holds the value written here
                    condition = {path: value for path, value in written.items() if path.split('.', 1)[0] == top}
                    if not condition:
                        continue
                    op = {'$set': {top: doc[top]}} if top in doc else {'$unset': {top: ''}}
                    coll.update_one({'_id': doc['_id'], **condition}, op)
        try:
            coll.bulk_write([UpdateOne({'_id': id_}, {'$set': values}) for id_, values in updates.items()], ordered=False)
        except BulkWriteError as exc:
            undo()
            _raise_bulk_error(cr, coll, exc, table)
        self.journal(cr).record(undo)

    # -- embedded elements ----------------------------------------------------------

    def push_elements(self, cr, coll, array_path: str, by_parent: dict[int, list[dict]], key: str = 'id') -> None:
        for parent_id, elements in by_parent.items():
            coll.update_one({'_id': parent_id}, {'$push': {array_path: {'$each': elements}}})
        element_ids = [e[key] for elements in by_parent.values() for e in elements]
        self.journal(cr).record(lambda: coll.update_many(
            {'_id': {'$in': list(by_parent)}}, {'$pull': {array_path: {key: {'$in': element_ids}}}}))

    def pull_elements(self, cr, coll, array_path: str, element_ids: list, key: str = 'id') -> dict[int, list[dict]]:
        """ Remove the elements and return them grouped by parent id. """
        if not element_ids:
            return {}
        removed: dict[int, list[dict]] = defaultdict(list)
        pipeline = [
            {'$match': {f'{array_path}.{key}': {'$in': element_ids}}},
            {'$project': {array_path: {'$filter': {
                'input': f'${array_path}', 'as': 'e', 'cond': {'$in': [f'$$e.{key}', element_ids]}}}}},
        ]
        for doc in coll.aggregate(pipeline):
            removed[doc['_id']].extend(doc.get(array_path) or [])
        coll.update_many({f'{array_path}.{key}': {'$in': element_ids}},
                         {'$pull': {array_path: {key: {'$in': element_ids}}}})
        if removed:
            def undo():
                for parent_id, elements in removed.items():
                    coll.update_one({'_id': parent_id}, {'$push': {array_path: {'$each': elements}}})
            self.journal(cr).record(undo)
        return removed

    def set_elements(self, cr, coll, array_path: str, element_ids: list, values: dict, key: str = 'id') -> None:
        """ ``$set`` ``values`` (element-relative paths) on the given elements. """
        if not element_ids or not values:
            return
        old = {}
        for doc in coll.aggregate([
            {'$match': {f'{array_path}.{key}': {'$in': element_ids}}},
            {'$project': {array_path: {'$filter': {
                'input': f'${array_path}', 'as': 'e', 'cond': {'$in': [f'$$e.{key}', element_ids]}}}}},
        ]):
            for element in doc.get(array_path) or []:
                old[element[key]] = {k: element.get(k) for k in values}
        coll.update_many(
            {f'{array_path}.{key}': {'$in': element_ids}},
            {'$set': {f'{array_path}.$[e].{path}': value for path, value in values.items()}},
            array_filters=[{f'e.{key}': {'$in': element_ids}}],
        )

        def undo():
            for element_id, previous in old.items():
                for path, value in previous.items():
                    # per field, and only where the element still holds the value written here
                    coll.update_many(
                        {f'{array_path}.{key}': element_id},
                        {'$set': {f'{array_path}.$[e].{path}': value}},
                        array_filters=[{f'e.{key}': element_id, f'e.{path}': values[path]}],
                    )
        self.journal(cr).record(undo)

    # -- id shadow ------------------------------------------------------------------

    @staticmethod
    def allocate_ids(model: BaseModel, count: int) -> list[int]:
        """ Draw ``count`` ids from the shadow table's sequence and insert the
        shadow rows. """
        cr = model.env.cr
        cr.execute(SQL(
            "INSERT INTO %s (id) SELECT nextval(pg_get_serial_sequence(%s, 'id')) FROM generate_series(1, %s) RETURNING id",
            SQL.identifier(model._table), model._table, count,
        ))
        return [row[0] for row in cr.fetchall()]


# ---------------------------------------------------------------------------
# Query object
# ---------------------------------------------------------------------------

FALSE_FILTER = {'_id': {'$in': []}}


class MongoTableSQL(TableSQL):
    """ The table of a MongoDB query: it has no SQL expression for its fields. """

    def __getitem__(self, field_name: str):
        raise NotImplementedError(
            f"{self._model._name}.{field_name} is stored in MongoDB and has no SQL expression; "
            "cross-store conditions are resolved through the comodel's own search (ids)")

    __getattr__ = __getitem__


class MongoQuery(Query):
    """ A query on a MongoDB-stored model: a filter, an order string, limit and
    offset.  It can be injected where Odoo expects a :class:`Query` holding ids
    (``subselect()`` yields the literal ids), but it has no SQL form. """

    def __init__(self, model: BaseModel, filter: dict | None = None):
        super().__init__(model)
        self.filter: dict = filter if filter is not None else {}
        self.sort_order: str | None = None
        self.sort_model: BaseModel | None = None
        self._ordered_ids = False

    def __copy__(self):
        query = super().__copy__()
        query.filter = dict(self.filter)
        return query

    @property
    def table(self) -> TableSQL:
        return MongoTableSQL(self._model._table, self._model, self)

    def set_result_ids(self, ids, ordered: bool = True) -> None:
        ids = tuple(ids)
        self.filter = {'_id': {'$in': list(ids)}} if ids else FALSE_FILTER
        self._ordered_ids = ordered
        self._ids = ids

    def is_empty(self) -> bool:
        return self._ids == () or self.filter == FALSE_FILTER

    def get_result_ids(self) -> tuple[int, ...]:
        if self._ids is None:
            if self.filter == FALSE_FILTER:
                self._ids = ()
            else:
                self._ids = tuple(doc['_id'] for doc in self.run({'_id': 1}))
        return self._ids

    def run(self, projection: dict | None = None, ids: Iterable[int] | None = None) -> list[dict]:
        return run_pipeline(self._model, self, projection, ids)

    def __len__(self) -> int:
        if self._ids is not None:
            return len(self._ids)
        if self.is_empty():
            return 0
        pipeline = [*base_stages(self._model), *match_stages(self.filter)]
        if self.offset:
            pipeline.append({'$skip': int(self.offset)})
        if self.limit is not None:
            pipeline.append({'$limit': int(self.limit)})
        pipeline.append({'$count': 'n'})
        rows = list(model_collection(self._model).aggregate(pipeline))
        return rows[0]['n'] if rows else 0

    def subselect(self, *args) -> SQL:
        if args:
            raise NotImplementedError(f"{self._model._name} is stored in MongoDB: a sub-query can only provide ids")
        ids = self.get_result_ids()
        if not ids:
            return SQL("(SELECT 1 WHERE FALSE)")
        return SQL("%s", ids)

    def select(self, *args) -> SQL:
        raise NotImplementedError(f"{self._model._name} is stored in MongoDB and cannot be selected with SQL")

    def add_where(self, where_clause, where_params=()) -> None:
        raise NotImplementedError(f"{self._model._name} is stored in MongoDB: add a Domain to the filter instead of SQL")

    def add_join(self, kind, alias, table, condition) -> None:
        raise NotImplementedError(f"{self._model._name} is stored in MongoDB and cannot be joined in SQL")

    def __str__(self) -> str:
        return f"<MongoQuery {self._model._name}: {self.filter!r} order={self.sort_order!r}>"


def store(model: BaseModel) -> MongoStore:
    return model.env.registry.mongo_store


def model_collection(model: BaseModel):
    return store(model).model_collection(model)


def base_stages(model: BaseModel) -> list[dict]:
    """ Pipeline prefix turning the model's collection into one document per
    record: nothing for a root collection, an unwind for an embedded array. """
    spec = store(model).storage(model)
    if not spec.embedded:
        return []
    path = spec.array_path
    key = spec.key_target if isinstance(spec.key_target, str) else 'id'
    return [
        {'$unwind': f'${path}'},
        {'$replaceRoot': {'newRoot': {'$mergeObjects': [
            f'${path}', {'_id': f'${path}.{key}', spec.target(spec.parent_column): '$_id'}]}}},
    ]


def match_stages(filter: dict) -> list[dict]:
    return [{'$match': filter}] if filter else []


def run_pipeline(model: BaseModel, query: MongoQuery, projection: dict | None = None,
                 ids: Iterable[int] | None = None) -> list[dict]:
    pipeline = base_stages(model)
    filter = query.filter
    if ids is not None:
        filter = {'$and': [filter, {'_id': {'$in': list(ids)}}]} if filter else {'_id': {'$in': list(ids)}}
    pipeline += match_stages(filter)
    if query._ids is not None and query._ordered_ids and query._ids:
        pipeline += [{'$addFields': {'__o': {'$indexOfArray': [list(query._ids), '$_id']}}}, {'$sort': {'__o': 1}}]
    elif query.sort_order:
        pipeline += sort_stages(query.sort_model or model, query.sort_order, query.filter)
    if query.offset:
        pipeline.append({'$skip': int(query.offset)})
    if query.limit is not None:
        pipeline.append({'$limit': int(query.limit)})
    if projection:
        pipeline.append({'$project': projection})
    return list(model_collection(model).aggregate(pipeline))


# ---------------------------------------------------------------------------
# Domains -> filters
# ---------------------------------------------------------------------------

def _like_regex(value, operator: str) -> str:
    """ SQL LIKE pattern (with Odoo's implicit wildcards) -> anchored regex. """
    pattern = re.escape(str(value)).replace('%', '.*').replace('_', '.')
    if '=' not in operator:
        pattern = f'.*{pattern}.*'
    return f'^{pattern}$'


class FilterCompiler:
    def __init__(self, model: BaseModel):
        self.model = model
        self.store = store(model)
        self.spec = self.store.storage(model)

    def compile(self, domain: Domain) -> dict:
        if isinstance(domain, DomainBool):
            return {} if domain.value else dict(FALSE_FILTER)
        if isinstance(domain, DomainNot):
            return {'$nor': [self.compile(domain.child)]}
        if isinstance(domain, DomainNary):
            parts = [self.compile(child) for child in domain.children]
            return {'$and' if isinstance(domain, DomainAnd) else '$or': parts}
        if isinstance(domain, DomainCondition):
            return self.condition(domain)
        if isinstance(domain, DomainCustom):
            raise NotImplementedError(f"Domain.custom (SQL) is not supported on MongoDB-stored model {self.model._name}")
        raise NotImplementedError(f"Unsupported domain {domain!r} on MongoDB-stored model {self.model._name}")

    # -- paths ------------------------------------------------------------------

    def path(self, field: Field) -> str:
        return self.spec.target(field.name)

    def _per_lang(self, field: Field, build) -> dict:
        """ Translated fields: compare the first stored language among the
        fallback chain (COALESCE(name->>lang, name->>'en_US')). """
        base = self.path(field)
        lang = field.translation_lang(self.model.env)
        langs = StoredTranslations.fallback_langs(lang)
        branches = []
        for index, code in enumerate(langs):
            branch = build(f'{base}.{code}')
            for previous in langs[:index]:
                branch = {'$and': [{f'{base}.{previous}': {'$exists': False}}, branch]}
            branches.append(branch)
        return branches[0] if len(branches) == 1 else {'$or': branches}

    def _company_dependent(self, field: Field, condition: DomainCondition, build) -> dict:
        base = self.path(field)
        path = f'{base}.{self.model.env.company.id}'
        keeps_fallback = self.model.env['ir.default']._evaluate_condition_with_fallback(
            self.model._name, condition.field_expr, condition.operator, condition.value)
        if keeps_fallback is None:
            raise NotImplementedError(f"Cannot evaluate {condition!r} against the company-dependent fallback of {field}")
        matched = build(path)
        if keeps_fallback:
            return {'$or': [matched, {path: {'$exists': False}}]}
        return {'$and': [matched, {path: {'$exists': True}}]}

    # -- conditions ----------------------------------------------------------------

    def condition(self, condition: DomainCondition) -> dict:
        model = self.model
        field = condition._field(model)
        model.check_field_access(field, 'read')
        fname, property_name = parse_field_expr(condition.field_expr)
        operator, value = condition.operator, condition.value
        if property_name:
            raise NotImplementedError(f"Property paths ({condition.field_expr!r}) are not supported on MongoDB-stored model {model._name}")
        if field.type == 'properties':
            raise NotImplementedError(f"Properties field {field} is not supported on MongoDB-stored model {model._name}")
        if operator in ('any', 'not any', 'any!', 'not any!'):
            if field.name == 'id':
                return self.id_any(operator, value)
            return self.relational(field, operator, value)

        bson_type = self.spec.bson_type(field.name, field)
        def to_column(v):
            if field.name == 'id':
                return int(v)
            return to_bson(field.convert_to_column(v, model, validate=False), bson_type)
        if field.company_dependent:
            # values of the stored object are in the ORM's column format
            return self._company_dependent(field, condition, lambda path: self.scalar(field, path, operator, value, to_column))
        if field.translate:
            return self._per_lang(field, lambda path: self.scalar(field, path, operator, value, lambda v: v if isinstance(v, str) else str(v)))
        return self.scalar(field, self.path(field), operator, value, to_column)

    def scalar(self, field: Field, path: str, operator: str, value, to_column) -> dict:
        model = self.model
        can_be_null = field not in model.env.registry.not_null_fields

        if operator in ('in', 'not in'):
            params = [to_column(v) for v in value if v is not False and v is not None]
            null_in_condition = len(params) < len(value)
            if (null_value := field.falsy_value) is not None:
                null_value = to_column(null_value)
                if null_value in params:
                    null_in_condition = True
                elif null_in_condition:
                    params.append(null_value)
            if (operator == 'in') == null_in_condition:
                # field in {val, False} => IN vals OR IS NULL ; not in {val} => NOT IN vals OR IS NULL
                if operator == 'not in':
                    return {path: {'$nin': params}} if params else {}
                if not can_be_null:
                    return {path: {'$in': params}} if params else dict(FALSE_FILTER)
                return {path: {'$in': [*params, None]}}
            if operator == 'not in' and null_in_condition:
                # not in {val, False} => IS NOT NULL AND NOT IN vals
                return {path: {'$nin': [*params, None]}} if params or can_be_null else {}
            return {path: {'$in': params}} if operator == 'in' else {path: {'$nin': params}}

        if operator.endswith('like'):
            regex = {'$regex': _like_regex(value, operator)}
            if operator.endswith('ilike'):
                regex['$options'] = 'i'
            if field.is_text or field.type == 'selection':
                match = {path: regex}
            else:
                match = {'$expr': {'$regexMatch': {'input': {'$toString': f'${path}'}, 'regex': regex['$regex'],
                                                   **({'options': 'i'} if 'ilike' in operator else {})}}}
            if operator in NEGATIVE_CONDITION_OPERATORS:
                match = {'$nor': [match]}
                if not can_be_null:
                    match = {'$and': [match, {path: {'$ne': None}}]}
            return match

        if operator in ('>', '<', '>=', '<='):
            mongo_operator = {'>': '$gt', '<': '$lt', '>=': '$gte', '<=': '$lte'}[operator]
            accept_null = False
            if (null_value := field.falsy_value) is not None:
                value = field.convert_to_cache(value, model) or null_value
                accept_null = can_be_null and (
                    null_value < value if operator == '<' else
                    null_value > value if operator == '>' else
                    null_value <= value if operator == '<=' else
                    null_value >= value)
            match = {path: {mongo_operator: to_column(value)}}
            return {'$or': [match, {path: None}]} if accept_null else match

        raise NotImplementedError(f"Operator {operator!r} is not supported on MongoDB-stored model {self.model._name} ({field})")

    def id_any(self, operator: str, value) -> dict:
        """ ``('id', 'any', Domain | Query)``: a sub-condition on the model itself. """
        if isinstance(value, Domain):
            match = self.compile(value)
        elif isinstance(value, Query):
            match = {'_id': {'$in': list(value.get_result_ids())}}
        else:
            raise TypeError(f"'any' on id accepts a Domain or Query, got {value!r}")
        return match if operator in ('any', 'any!') else {'$nor': [match]}

    # -- relational conditions ----------------------------------------------------------

    def relational(self, field: Field, operator: str, value) -> dict:
        model = self.model
        positive = operator in ('any', 'any!')
        bypass_access = operator in ('any!', 'not any!') or field.bypass_search_access
        comodel = model.env[field.comodel_name]

        if field.type == 'many2one':
            if isinstance(value, Domain):
                value = comodel.with_context(active_test=False)._search(value, bypass_access=bypass_access)
            if isinstance(value, Query):
                ids = list(value.get_result_ids())
            else:
                raise TypeError(f"'any' on {field} accepts a Domain or Query, got {value!r}")
            path = self.path(field)
            if field.company_dependent:
                path = f'{path}.{model.env.company.id}'
            return {path: {'$in': ids}} if positive else {path: {'$nin': ids}}

        assert field.type in ('one2many', 'many2many'), f"Unexpected relational field {field}"
        comodel = comodel.with_context(**field.context)
        field_domain = field.get_comodel_domain(model)
        if isinstance(value, Domain):
            domain = value & field_domain
            if field.type == 'one2many':
                inverse = comodel._fields[field.inverse_name]
                if inverse.column_type and inverse not in comodel.env.registry.not_null_fields:
                    domain &= Domain(inverse.name, '!=', False)
            coquery = comodel._search(domain, bypass_access=bypass_access)
        elif isinstance(value, Query):
            coquery = comodel._search(field_domain & Domain('id', 'any!', value), active_test=False, bypass_access=True)
        else:
            raise TypeError(f"'any' on {field} accepts a Domain or Query, got {value!r}")

        if coquery.is_empty():
            return dict(FALSE_FILTER) if positive else {}
        if field.type == 'one2many':
            match = {'_id': {'$in': one2many_parent_ids(field, coquery)}}
        else:
            match = many2many_filter(field, model, list(coquery.get_result_ids()))
        return match if positive else {'$nor': [match]}


def one2many_parent_ids(field: Field, coquery: Query) -> list:
    """ The values of the inverse field over the records of ``coquery``. """
    comodel = coquery._model.sudo()
    inverse = comodel._fields[field.inverse_name]
    if isinstance(coquery, MongoQuery):
        if inverse.store and inverse.column_type:
            path = store(comodel).path(comodel, inverse.name)
            return [doc[path] for doc in coquery.run({path: 1}) if doc.get(path) is not None]
    elif inverse.store and inverse.column_type:
        rows = comodel.env.execute_query(coquery.select(SQL("DISTINCT %s", coquery.table[inverse.name])))
        return [row[0] for row in rows if row[0] is not None]
    records = comodel.browse(coquery.get_result_ids()).with_context(prefetch_fields=False)
    values = inverse.__get__(records)
    return list(values.ids) if inverse.relational else [v for v in (inverse.__get__(rec) for rec in records) if v]


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

def _parse_order(model: BaseModel, order: str, reverse: bool = False):
    from .models import regex_order  # noqa: PLC0415
    model._check_qorder(order)
    for part in order.split(','):
        match = regex_order.match(part)
        assert match is not None
        direction = (match['direction'] or 'ASC').upper()
        nulls = (match['nulls'] or '').upper()
        if reverse:
            direction = 'ASC' if direction == 'DESC' else 'DESC'
            if nulls:
                nulls = 'NULLS LAST' if nulls == 'NULLS FIRST' else 'NULLS FIRST'
        if not nulls:
            nulls = 'NULLS LAST' if direction == 'ASC' else 'NULLS FIRST'
        yield match['field'], match['property'], direction, nulls


def ranked_ids(comodel: BaseModel, ids: list, order: str, reverse: bool) -> list:
    """ ``ids`` sorted by the comodel's ``order`` (its own store decides). """
    if not ids:
        return []
    ordered = list(comodel.sudo().with_context(active_test=False)._search(
        [('id', 'in', ids)], order=order).get_result_ids())
    return ordered[::-1] if reverse else ordered


def _index_or_null(array: list, expr) -> dict:
    return {'$let': {'vars': {'i': {'$indexOfArray': [array, expr]}},
                     'in': {'$cond': [{'$eq': ['$$i', -1]}, None, '$$i']}}}


def sort_key_expr(model: BaseModel, fname: str, property_name: str | None, direction: str, filter: dict):
    """ The aggregation expression a record is ordered by for one order term. """
    field = model._fields.get(fname)
    if not field:
        raise ValueError(f"Invalid field {fname!r} on model {model._name!r}")
    spec = store(model).storage(model)
    path = spec.target(fname)
    env = model.env

    if field.inherited or (field.type == 'many2one' and property_name != 'id'):
        if field.inherited:
            parent_fname, coorder = field.related.split('.', 1)
            parent_field = model._fields[parent_fname]
        else:
            parent_field, coorder = field, env[field.comodel_name]._order
            if property_name:
                raise ValueError(f"Cannot order by comodel fields in {fname}.{property_name!r}")
        seen = env.context.get('__m2o_order_seen', ())
        if parent_field in seen:
            return None
        comodel = env[parent_field.comodel_name].with_context(__m2o_order_seen=frozenset((parent_field, *seen)))
        parent_path = spec.target(parent_field.name)
        if coorder == 'id':
            return f'${parent_path}'
        pipeline = [*base_stages(model), *match_stages(filter), {'$group': {'_id': f'${parent_path}'}}]
        values = [doc['_id'] for doc in model_collection(model).aggregate(pipeline) if doc['_id'] is not None]
        ordered = ranked_ids(comodel, values, coorder, reverse=direction == 'DESC')
        return _index_or_null(ordered, f'${parent_path}'), 'ASC'

    if field.type == 'selection':
        return _index_or_null(list(field.get_values(env)), f'${path}')
    if field.type == 'boolean' and field not in env.registry.not_null_fields:
        return {'$ifNull': [f'${path}', False]}
    if field.translate:
        langs = StoredTranslations.fallback_langs(field.translation_lang(env))
        return {'$ifNull': [f'${path}.{code}' for code in langs] + [None]} if len(langs) > 1 else f'${path}.{langs[0]}'
    if field.company_dependent:
        fallback = field.convert_to_column(field.convert_to_write(field.get_company_dependent_fallback(model), model), model)
        return {'$ifNull': [f'${path}.{env.company.id}', to_bson(fallback, spec.bson_type(fname, field))]}
    return f'${path}'


def sort_stages(model: BaseModel, order: str, filter: dict, reverse: bool = False) -> list[dict]:
    fields, sort = {}, {}
    for index, (fname, property_name, direction, nulls) in enumerate(_parse_order(model, order, reverse)):
        expr = sort_key_expr(model, fname, property_name, direction, filter)
        if expr is None:
            continue
        if isinstance(expr, tuple):     # ranks already encode the direction
            expr, direction = expr
        fields[f'__n{index}'] = {'$eq': [expr, None]}
        fields[f'__k{index}'] = expr
        sort[f'__n{index}'] = 1 if nulls == 'NULLS LAST' else -1
        sort[f'__k{index}'] = 1 if direction == 'ASC' else -1
    if not sort:
        return []
    return [{'$addFields': fields}, {'$sort': sort}]


def order_rank_sql(model: BaseModel, field: Field, sql_field: SQL, direction: SQL, nulls: SQL) -> SQL:
    """ ORDER BY term of a PostgreSQL model on a many2one into a MongoDB-stored
    comodel: the comodel ranks its ids, PostgreSQL orders by the rank. """
    comodel = model.env[field.comodel_name]
    ordered = list(comodel.sudo().with_context(active_test=False)._search([], order=comodel._order).get_result_ids())
    return SQL("array_position(%s::int[], %s) %s %s", ordered, sql_field, direction, nulls)


# ---------------------------------------------------------------------------
# Search and fetch
# ---------------------------------------------------------------------------

def search(model: BaseModel, domain: Domain, sec_domain: Domain, sec_model: BaseModel,
           offset: int, limit: int | None, order: str | None) -> MongoQuery:
    filter = FilterCompiler(model).compile(domain) if not domain.is_true() else {}
    if not sec_domain.is_true():
        sec_filter = FilterCompiler(sec_model).compile(sec_domain)
        filter = {'$and': [filter, sec_filter]} if filter else sec_filter
    query = MongoQuery(model, filter)
    if order:
        query.sort_order = order
        query.sort_model = model
    if limit is not None and limit is not False:
        query.limit = limit
    if offset:
        query.offset = offset
    return query


def doc_value(model: BaseModel, field: Field, doc: dict, spec: CollectionSpec):
    """ The cache-insertable value of ``field`` from a document. """
    raw = doc.get(spec.target(field.name))
    env = model.env
    if field.translate:
        if raw is None or env.context.get('prefetch_langs'):
            return raw
        for code in StoredTranslations.fallback_langs(field.translation_lang(env)):
            if code in raw:
                return raw[code]
        return None
    if field.company_dependent:
        if isinstance(raw, dict) and str(env.company.id) in raw:
            raw = raw[str(env.company.id)]
        else:
            raw = field.convert_to_column(field.convert_to_write(field.get_company_dependent_fallback(model), model), model)
        return field.convert_to_cache(from_bson(raw, field), model) if raw is not None else None
    return from_bson(raw, field)


def fetch_query(model: BaseModel, query: MongoQuery, fields: Iterable[Field]) -> BaseModel:
    column_fields: OrderedSet[Field] = OrderedSet()
    other_fields: OrderedSet[Field] = OrderedSet()
    for field in fields:
        if field.name == 'id':
            continue
        assert field.store or field.compute_sql
        if field.compute_sql:
            raise NotImplementedError(f"compute_sql field {field} is not supported on MongoDB-stored model {model._name}")
        (column_fields if field.column_type else other_fields).add(field)

    spec = store(model).storage(model)
    if column_fields:
        projection = {spec.target(field.name): 1 for field in column_fields}
        projection['_id'] = 1
        docs = query.run(projection)
        if not docs:
            return model.browse()
        fetched = model.browse(doc['_id'] for doc in docs)
        for field in column_fields:
            field._insert_cache(fetched, [doc_value(model, field, doc, spec) for doc in docs])
    else:
        fetched = model.browse(query)

    if fetched:
        for field in other_fields:
            field.read(fetched)
    return fetched


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

def _pg_error(cr, condition: str, message: str, **diagnostics: str | None) -> typing.NoReturn:
    """ Raise ``condition`` (check_violation, unique_violation, ...) from
    PostgreSQL itself, so the error has the class and diagnostics of the one a
    PostgreSQL table raises and aborts the transaction the same way. """
    options = [('MESSAGE', message), *diagnostics.items()]
    using = ', '.join(
        f"{option} = {QuotedString(str(value)).getquoted().decode()}"
        for option, value in options if value is not None)
    cr.execute(SQL("DO %s", f"BEGIN RAISE {condition} USING {using}; END"))
    raise AssertionError("unreachable")  # pragma: no cover


def _not_null_violation(model: BaseModel, fname: str) -> typing.NoReturn:
    _pg_error(model.env.cr, 'not_null_violation',
              f'null value in column "{fname}" of relation "{model._table}" violates not-null constraint',
              TABLE=model._table, COLUMN=fname)


def _foreign_key_violation(model: BaseModel, message: str) -> typing.NoReturn:
    _pg_error(model.env.cr, 'foreign_key_violation', message, TABLE=model._table)


def _raise_bulk_error(cr, coll, exc: BulkWriteError, table: str) -> typing.NoReturn:
    """ A duplicate key in a bulk write becomes the unique_violation PostgreSQL
    raises; anything else is re-raised as is. """
    error = (exc.details.get('writeErrors') or [{}])[0]
    if error.get('code') != 11000:
        raise exc
    match = re.search(r'index: (\S+)', error.get('errmsg', ''))
    index = match.group(1) if match else coll.name
    key = error.get('keyValue') or {}
    _pg_error(cr, 'unique_violation', f'duplicate key value violates unique constraint "{index}"',
              TABLE=table or coll.name, CONSTRAINT=index,
              DETAIL=f"Key ({', '.join(key)})=({', '.join(str(v) for v in key.values())}) already exists.")


_CHECK_RE = re.compile(r'^\s*CHECK\s*(\(.*\))\s*$', re.IGNORECASE | re.DOTALL)
_IDENT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')


def _check_constraints(model: BaseModel) -> list[tuple[TableObject, str, list[str]]]:
    """ (constraint, expression, referenced columns) of the model's SQL CHECK constraints. """
    result = []
    for cons in model._table_objects.values():
        if match := _CHECK_RE.match(cons.get_definition(model.env.registry)):
            expr = match.group(1)
            columns = sorted({
                name for name in _IDENT_RE.findall(expr)
                if name in model._fields and model._fields[name].column_type
            })
            result.append((cons, expr, columns))
    return result


def _bson_to_column(value):
    if isinstance(value, Decimal128):
        return value.to_decimal()
    if isinstance(value, (dict, list)):
        return PsycopgJson(value)
    return value


def _enforce_checks(model: BaseModel, rows: dict[int, dict[str, object]], fnames: typing.Collection[str] | None = None) -> None:
    """ Let PostgreSQL evaluate the CHECK constraints of ``model`` on ``rows``
    (``{id: {column: value}}`` in column format; the columns a constraint reads
    and the written ``fnames`` miss are fetched from the documents), and raise
    like a PostgreSQL table does when one fails. """
    checks = _check_constraints(model)
    if fnames is not None:
        checks = [c for c in checks if any(col in fnames for col in c[2])]
    if not checks or not rows:
        return
    cr = model.env.cr
    columns = sorted({col for c in checks for col in c[2]})
    if missing := [col for col in columns if any(col not in row for row in rows.values())]:
        spec = store(model).storage(model)
        projection = {spec.target(col): 1 for col in missing}
        for doc in run_pipeline(model, MongoQuery(model), projection, list(rows)):
            row = rows[doc['_id']]
            for col in missing:
                row.setdefault(col, _bson_to_column(doc.get(spec.target(col))))
    values = SQL(", ").join(
        SQL("(%s)", SQL(", ").join([
            SQL("%s", id_),
            *(SQL("%s::%s", row.get(col), SQL(model._fields[col].column_type[1])) for col in columns),
        ]))
        for id_, row in rows.items()
    )
    for cons, expr, _ in checks:
        cr.execute(SQL(
            "SELECT t.__id FROM (VALUES %s) AS t(__id, %s) WHERE NOT %s LIMIT 1",
            values, SQL(", ").join(SQL.identifier(col) for col in columns), SQL(expr),
        ))
        if cr.rowcount:
            name = cons.full_name(model)
            _pg_error(cr, 'check_violation',
                      f'new row for relation "{model._table}" violates check constraint "{name}"',
                      TABLE=model._table, CONSTRAINT=name)


def _required_column_fields(model: BaseModel) -> list[Field]:
    return [f for f in model._fields.values() if f.store and f.column_type and f.required and f.name != 'id']


def create(model: BaseModel, data_list: list[dict]) -> tuple[list[int], OrderedSet]:
    """ Insert the shadow rows and the documents; return the ids and the fields
    with their own create() protocol. """
    st = store(model)
    spec = st.storage(model)
    other_fields: OrderedSet[Field] = OrderedSet()
    required = _required_column_fields(model)
    ids = st.allocate_ids(model, len(data_list))
    docs = []
    rows: dict[int, dict[str, object]] = {}
    for id_, data in zip(ids, data_list):
        stored = data['stored']
        doc = {}
        row = rows[id_] = {}
        for fname, value in stored.items():
            field = model._fields[fname]
            if field.column_type:
                column = row[fname] = field.convert_to_column_insert(value, model, stored)
                doc[spec.target(fname)] = to_bson(column, spec.bson_type(fname, field))
            else:
                other_fields.add(field)
            if field.type == 'properties':
                other_fields.add(field)
        for field in required:
            if doc.get(spec.target(field.name)) is None:
                _not_null_violation(model, field.name)
        docs.append(doc)
    _enforce_checks(model, {id_: {col: row.get(col) for col in model._fields if model._fields[col].column_type} for id_, row in rows.items()})

    cr = model.env.cr
    coll = model_collection(model)
    if spec.embedded:
        parent_target = spec.target(spec.parent_column)
        by_parent: dict[int, list[dict]] = defaultdict(list)
        for id_, doc in zip(ids, docs):
            parent_id = doc.pop(parent_target, None)
            if parent_id is None:
                _not_null_violation(model, spec.parent_column)
            element = {spec.key_target: id_, **doc}
            by_parent[parent_id].append(element)
        if missing := set(by_parent) - {d['_id'] for d in coll.find({'_id': {'$in': list(by_parent)}}, {'_id': 1})}:
            _foreign_key_violation(
                model, f'insert on table "{model._table}" violates foreign key constraint: {spec.parent_column} {sorted(missing)} not found')
        st.push_elements(cr, coll, spec.array_path, by_parent, spec.key_target)
    else:
        for id_, doc in zip(ids, docs):
            doc['_id'] = id_
        st.insert_docs(cr, coll, docs, model._table)
    return ids, other_fields


def _merge_json(field: Field, old, update):
    """ Apply the ORM's UPDATE semantics for translated (``(is_partial, dict)``)
    and company-dependent (``{company_id: value}``) JSON columns in Python. """
    update = _unwrap_json(update)
    if update is None:
        return None
    if field.translate is True and isinstance(update, tuple):
        is_partial, translations = update
        translations = dict(translations)
        if not is_partial:
            return translations
        base = dict(old) if isinstance(old, dict) else {'en_US': next(iter(translations.values()))}
        return base | translations
    if field.company_dependent and isinstance(update, dict):
        return (dict(old) if isinstance(old, dict) else {}) | update
    return dict(update) if isinstance(update, StoredTranslations) else update


def write_multi(model: BaseModel, vals_list: list[dict]) -> None:
    """ Update the documents of ``model`` (records) with column-format values. """
    st = store(model)
    spec = st.storage(model)
    cr = model.env.cr
    coll = model_collection(model)
    ids = list(model._ids)
    json_fields = {model._fields[f] for vals in vals_list for f in vals
                   if model._fields[f].translate or model._fields[f].company_dependent}
    old_json = {}
    if json_fields:
        projection = {spec.target(f.name): 1 for f in json_fields}
        if spec.embedded:
            old_json = {doc['_id']: doc for doc in run_pipeline(model, MongoQuery(model), projection, ids)}
        else:
            old_json = {doc['_id']: doc for doc in coll.find({'_id': {'$in': ids}}, projection)}
    required = {f.name for f in _required_column_fields(model)}
    _enforce_checks(model, {id_: dict(vals) for id_, vals in zip(ids, vals_list)}, {f for vals in vals_list for f in vals})

    updates: dict[int, dict[str, object]] = {}
    moves: dict[int, int] = {}      # embedded records whose parent changes
    for id_, vals in zip(ids, vals_list):
        values = {}
        for fname, value in vals.items():
            field = model._fields[fname]
            assert field.store and field.column_type
            path = spec.target(fname)
            if field in json_fields:
                value = _merge_json(field, old_json.get(id_, {}).get(path), value)
            else:
                value = to_bson(value, spec.bson_type(fname, field))
            if value is None and fname in required:
                _not_null_violation(model, fname)
            if spec.embedded and fname == spec.parent_column:
                moves[id_] = value
                continue
            values[path] = value
        if values:
            updates[id_] = values

    if not spec.embedded:
        st.update_docs(cr, coll, updates, model._table)
        return
    if moves:
        if missing := set(moves.values()) - {d['_id'] for d in coll.find({'_id': {'$in': list(moves.values())}}, {'_id': 1})}:
            _foreign_key_violation(
                model, f'update on table "{model._table}" violates foreign key constraint: {spec.parent_column} {sorted(missing)} not found')
        removed = st.pull_elements(cr, coll, spec.array_path, list(moves), spec.key_target)
        by_parent: dict[int, list[dict]] = defaultdict(list)
        for elements in removed.values():
            for element in elements:
                element.update(updates.pop(element[spec.key_target], {}))
                by_parent[moves[element[spec.key_target]]].append(element)
        st.push_elements(cr, coll, spec.array_path, by_parent, spec.key_target)
    groups: dict[tuple, list[int]] = defaultdict(list)
    for id_, values in updates.items():
        groups[tuple(sorted(values.items(), key=lambda kv: kv[0]))].append(id_)
    for items, group_ids in groups.items():
        st.set_elements(cr, coll, spec.array_path, group_ids, dict(items), spec.key_target)


def unlink_rows(model: BaseModel, ids: list[int]) -> None:
    """ Remove the shadow rows and the documents of ``ids``. """
    st = store(model)
    spec = st.storage(model)
    cr = model.env.cr
    coll = model_collection(model)
    on_delete(model, ids, check_only=True)
    # records embedded in the deleted documents go with them, through their own unlink()
    if not spec.embedded:
        child_specs = embedded_children(model)
        if child_specs:
            docs = list(coll.find({'_id': {'$in': ids}}, {cs.array_path: 1 for _, cs in child_specs}))
            for child, cs in child_specs:
                child_ids = [e[cs.key_target] for doc in docs for e in doc.get(cs.array_path) or [] if cs.key_target in e]
                if child_ids:
                    child.browse(child_ids).unlink()
    # many2many links stored in MongoDB have no foreign key to cascade them
    for field in many2many_fields_of(model):
        Model = model.env[field.model_name].sudo()
        pairs = set()
        if field.model_name == model._name:
            pairs.update(_rel_pairs(field, Model, ids=ids))
        if field.comodel_name == model._name:       # both for a self-referential relation
            pairs.update(_rel_pairs(field, Model, coids=ids))
        if pairs:
            many2many_write_pairs(field, Model, [], sorted(pairs))
            Model.invalidate_model([field.name])
    cr.execute(SQL("DELETE FROM %s WHERE id IN %s", SQL.identifier(model._table), tuple(ids)))
    if spec.embedded:
        st.pull_elements(cr, coll, spec.array_path, ids, spec.key_target)
    else:
        st.delete_docs(cr, coll, ids)
    on_delete(model, ids)


def embedded_children(model: BaseModel) -> list[tuple[BaseModel, CollectionSpec]]:
    """ The models embedded as arrays in ``model``'s documents, with their spec entry. """
    st = store(model)
    table = model._table
    env = model.env
    result = []
    for Model in env.registry.models.values():
        if is_mongodb(Model) and not Model._abstract and Model._name != model._name:
            child = env[Model._name].sudo().with_context(active_test=False, prefetch_fields=False)
            cs = st.storage(child)
            if cs.embedded and cs.parent_table == table:
                result.append((child, cs))
    return result


def many2many_fields_of(model: BaseModel) -> list[Field]:
    """ Stored many2many fields on either side of ``model`` whose relation table
    is in MongoDB, one per relation table. """
    env = model.env
    result: dict[str, Field] = {}
    for Model in env.registry.models.values():
        for field in Model._fields.values():
            if (
                field.type == 'many2many' and field.store and field.relation not in result
                and model._name in (field.model_name, field.comodel_name)
                and many2many_rel_storage(field, env[field.model_name]) is not None
            ):
                result[field.relation] = field
    return list(result.values())


def referencing_fields(registry: Registry, model_name: str) -> list[Field]:
    """ Stored many2one fields of MongoDB-stored models that point to ``model_name``. """
    cache = registry.__dict__.setdefault('_mongodb_referencing_fields', {})
    if model_name not in cache:
        cache[model_name] = [
            field
            for Model in registry.models.values()
            if is_mongodb(Model) and not Model._abstract
            for field in Model._fields.values()
            if field.type == 'many2one' and field.store and field.column_type
            and field.comodel_name == model_name and not field.company_dependent
        ]
    return cache[model_name]


def on_delete(model: BaseModel, ids: list[int], check_only: bool = False) -> None:
    """ Emulate the foreign-key ``ondelete`` rules of MongoDB-stored models
    referencing the deleted records (PostgreSQL has no constraint for them). """
    env = model.env
    for field in referencing_fields(env.registry, model._name):
        comodel = env[field.model_name].sudo().with_context(active_test=False, prefetch_fields=False)
        if check_only:
            if field.ondelete == 'restrict' and not env.context.get('force_delete'):
                query = comodel._search([(field.name, 'in', ids)], bypass_access=True)
                query.limit = 1
                if query.get_result_ids():
                    _foreign_key_violation(
                        model, f'update or delete on table "{model._table}" violates foreign key constraint '
                        f'"{comodel._table}_{field.name}_fkey" on table "{comodel._table}"')
            continue
        query = comodel._search([(field.name, 'in', ids)], bypass_access=True)
        child_ids = list(query.get_result_ids())
        if not child_ids:
            continue
        if field.ondelete == 'cascade':
            comodel.browse(child_ids).invalidate_recordset()
            unlink_rows(comodel, child_ids)
        else:  # set null
            comodel.browse(child_ids)._write_multi([{field.name: None}] * len(child_ids))
            comodel.browse(child_ids).invalidate_recordset([field.name])


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def auto_init(model: BaseModel) -> None:
    """ Create or adapt the id shadow table, create the spec indexes, and keep
    the PostgreSQL relation tables of many2many fields the spec leaves there. """
    from odoo.tools import sql  # noqa: PLC0415
    cr = model.env.cr
    if not sql.table_exists(cr, model._table):
        sql.create_model_table(cr, model._table, model._description)
    else:
        for name, column in sql.table_columns(cr, model._table).items():
            if name != 'id' and column['is_nullable'] == 'NO':
                sql.drop_not_null(cr, model._table, name)
    st = store(model)
    st.ensure_indexes(model)
    columns = sql.table_columns(cr, model._table)
    for field in model._fields.values():
        if field.type == 'many2many' and field.store and not many2many_rel_storage(field, model):
            field.update_db(model, columns)


# ---------------------------------------------------------------------------
# Many2many relation tables
# ---------------------------------------------------------------------------

def many2many_rel_storage(field: Field, model: BaseModel) -> CollectionSpec | None:
    """ Where the relation table lives in MongoDB, or None (PostgreSQL). A
    relation between two PostgreSQL models stays in PostgreSQL even when the
    mapping spec maps its table: nothing is written for models not opted in. """
    comodel = model.env[field.comodel_name]
    if not (is_mongodb(model) or is_mongodb(comodel)):
        return None
    st = store(model)
    return st.table_storage(field.relation, model) or st.table_storage(field.relation, comodel)


def many2many_cross_store(field: Field, model: BaseModel) -> bool:
    return is_mongodb(model) or is_mongodb(model.env[field.comodel_name])


def _rel_pairs(field: Field, model: BaseModel, ids: list[int] | None = None, coids: list[int] | None = None) -> list[tuple[int, int]]:
    """ (id, coid) pairs of the relation restricted to ``ids`` and/or ``coids``. """
    rel = many2many_rel_storage(field, model)
    env = model.env
    if rel is None:
        conditions = [SQL("TRUE")]
        if ids is not None:
            conditions.append(SQL("%s IN %s", SQL.identifier(field.column1), tuple(ids) or (None,)))
        if coids is not None:
            conditions.append(SQL("%s IN %s", SQL.identifier(field.column2), tuple(coids) or (None,)))
        return env.execute_query(SQL(
            "SELECT %s, %s FROM %s WHERE %s", SQL.identifier(field.column1), SQL.identifier(field.column2),
            SQL.identifier(field.relation), SQL(" AND ").join(conditions)))
    st = store(model)
    coll = st.collection(rel.collection)
    if rel.embedded:
        own_side = rel.parent_table == model._table
        owner_col, other_col = (field.column1, field.column2) if own_side else (field.column2, field.column1)
        element_key = rel.target(other_col)
        owner_ids, other_ids = (ids, coids) if own_side else (coids, ids)
        filter = {}
        if owner_ids is not None:
            filter['_id'] = {'$in': list(owner_ids)}
        if other_ids is not None:
            filter[f'{rel.array_path}.{element_key}'] = {'$in': list(other_ids)}
        pairs = []
        for doc in coll.find(filter, {rel.array_path: 1}):
            for element in doc.get(rel.array_path) or []:
                other = element.get(element_key)
                if other_ids is None or other in other_ids:
                    pairs.append((doc['_id'], other) if own_side else (other, doc['_id']))
        return pairs
    t1, t2 = rel.target(field.column1), rel.target(field.column2)
    filter = {}
    if ids is not None:
        filter[t1] = {'$in': list(ids)}
    if coids is not None:
        filter[t2] = {'$in': list(coids)}
    return [(doc[t1], doc[t2]) for doc in coll.find(filter, {t1: 1, t2: 1})]


def many2many_filter(field: Field, model: BaseModel, coids: list[int]) -> dict:
    """ Filter on a MongoDB-stored ``model`` selecting the records linked to ``coids``. """
    rel = many2many_rel_storage(field, model)
    if rel is not None and rel.embedded and rel.parent_table == model._table:
        return {f'{rel.array_path}.{rel.target(field.column2)}': {'$in': coids}}
    return {'_id': {'$in': [id_ for id_, _ in _rel_pairs(field, model, coids=coids)]}}


def many2many_read(field: Field, records: BaseModel) -> None:
    """ :meth:`Many2many.read` when a side or the relation table is in MongoDB. """
    comodel = records.env[field.comodel_name].with_context(active_test=False, **field.context)
    pairs = _rel_pairs(field, records, ids=list(records.ids))
    coids = list(OrderedSet(coid for _, coid in pairs))
    allowed = comodel.sudo()._search(
        field.get_comodel_domain(records) & Domain('id', 'in', coids), order=comodel._order, bypass_access=True,
    ).get_result_ids() if coids else ()
    rank = {coid: index for index, coid in enumerate(allowed)}
    group = defaultdict(list)
    for id_, coid in pairs:
        if coid in rank:
            group[id_].append(coid)
    values = [tuple(sorted(group[id_], key=rank.__getitem__)) for id_ in records._ids]
    field._insert_cache(records, values)


def many2many_write_pairs(field: Field, model: BaseModel, add_pairs: list, remove_pairs: list) -> None:
    """ Apply relation changes to a MongoDB-stored relation table. """
    rel = many2many_rel_storage(field, model)
    assert rel is not None
    st = store(model)
    cr = model.env.cr
    coll = st.collection(rel.collection)
    if rel.embedded:
        own_side = rel.parent_table == model._table
        element_key = rel.target(field.column2 if own_side else field.column1)
        by_owner_add, by_owner_remove = defaultdict(list), defaultdict(list)
        for x, y in add_pairs:
            owner, other = (x, y) if own_side else (y, x)
            by_owner_add[owner].append(other)
        for x, y in remove_pairs:
            owner, other = (x, y) if own_side else (y, x)
            by_owner_remove[owner].append(other)
        for owner, others in by_owner_remove.items():
            coll.update_one({'_id': owner}, {'$pull': {rel.array_path: {element_key: {'$in': others}}}})
        for owner, others in by_owner_add.items():
            existing = coll.find_one({'_id': owner}, {rel.array_path: 1}) or {}
            present = {e.get(element_key) for e in existing.get(rel.array_path) or []}
            new = [{element_key: other} for other in others if other not in present]
            by_owner_add[owner] = [e[element_key] for e in new]
            if new:
                coll.update_one({'_id': owner}, {'$push': {rel.array_path: {'$each': new}}})

        def undo():
            for owner, others in by_owner_add.items():
                coll.update_one({'_id': owner}, {'$pull': {rel.array_path: {element_key: {'$in': others}}}})
            for owner, others in by_owner_remove.items():
                coll.update_one({'_id': owner}, {'$push': {rel.array_path: {'$each': [{element_key: o} for o in others]}}})
        if add_pairs or remove_pairs:
            st.journal(cr).record(undo)
        return
    t1, t2 = rel.target(field.column1), rel.target(field.column2)
    if remove_pairs:
        removed = list(coll.find({'$or': [{t1: x, t2: y} for x, y in remove_pairs]}))
        if removed:
            coll.delete_many({'_id': {'$in': [d['_id'] for d in removed]}})
            st.journal(cr).record(lambda: coll.insert_many(removed))
    if add_pairs:
        present = {(d[t1], d[t2]) for d in coll.find({'$or': [{t1: x, t2: y} for x, y in add_pairs]}, {t1: 1, t2: 1})}
        docs = [{t1: x, t2: y} for x, y in add_pairs if (x, y) not in present]
        if docs:
            try:
                coll.insert_many(docs, ordered=True)
            except BulkWriteError as exc:
                if inserted := [d['_id'] for d in docs[:exc.details.get('nInserted', 0)]]:
                    coll.delete_many({'_id': {'$in': inserted}})
                _raise_bulk_error(cr, coll, exc, field.relation)
            inserted = [d['_id'] for d in docs]
            st.journal(cr).record(lambda: coll.delete_many({'_id': {'$in': inserted}}))


def many2many_condition_sql(field: Field, table: TableSQL, exists: bool, coquery: Query) -> SQL:
    """ ``_condition_to_sql_relational`` of a PostgreSQL model whose relation
    table (or comodel) lives in MongoDB: resolve the ids, compare in SQL. """
    model = table._model
    ids = tuple(OrderedSet(id_ for id_, _ in _rel_pairs(field, model, coids=list(coquery.get_result_ids()))))
    if not ids:
        return SQL("FALSE") if exists else SQL("TRUE")
    return SQL("%s %s %s", table.id, SQL("IN") if exists else SQL("NOT IN"), ids)


def one2many_condition_sql(field: Field, table: TableSQL, exists: bool, coquery: MongoQuery) -> SQL:
    ids = tuple(OrderedSet(one2many_parent_ids(field, coquery)))
    if not ids:
        return SQL("FALSE") if exists else SQL("TRUE")
    return SQL("%s %s %s", table.id, SQL("IN") if exists else SQL("NOT IN"), ids)


# ---------------------------------------------------------------------------
# read_group
# ---------------------------------------------------------------------------

_NUMBER_GRANULARITY_EXPR = {
    'year_number': '$year', 'month_number': '$month', 'iso_week_number': '$isoWeek',
    'day_of_year': '$dayOfYear', 'day_of_month': '$dayOfMonth',
    'hour_number': '$hour', 'minute_number': '$minute', 'second_number': '$second',
}


def _group_key_expr(model: BaseModel, spec: CollectionSpec, groupby_spec: str, filter: dict, unwinds: list):
    from .models import parse_read_group_spec  # noqa: PLC0415
    fname, seq, granularity = parse_read_group_spec(groupby_spec)
    field = model._fields.get(fname)
    if field is None:
        raise ValueError(f"Invalid field {fname!r} on model {model._name!r}")
    if seq or field.type == 'properties':
        raise NotImplementedError(f"Group by {groupby_spec!r} is not supported on MongoDB-stored model {model._name}")
    path = spec.target(fname)
    if field.type == 'many2many':
        rel = many2many_rel_storage(field, model)
        if rel is None or not rel.embedded or rel.parent_table != model._table:
            raise NotImplementedError(f"Group by many2many {field} needs its relation table embedded in {model._name}'s documents")
        unwinds.append({'$unwind': {'path': f'${rel.array_path}', 'preserveNullAndEmptyArrays': True}})
        return f'${rel.array_path}.{rel.target(field.column2)}'
    if field.type in ('date', 'datetime'):
        if not granularity:
            raise ValueError(f"Granularity not set on a date(time) field: {groupby_spec!r}")
        date = f'${path}'
        tz = model.env.context.get('tz') if field.type == 'datetime' else None
        tz_arg = {'timezone': tz} if tz else {}
        if granularity in _NUMBER_GRANULARITY_EXPR:
            return {_NUMBER_GRANULARITY_EXPR[granularity]: {'date': date, **tz_arg}}
        if granularity == 'quarter_number':
            return {'$ceil': {'$divide': [{'$month': {'date': date, **tz_arg}}, 3]}}
        if granularity == 'day_of_week':
            return {'$subtract': [{'$dayOfWeek': {'date': date, **tz_arg}}, 1]}
        if granularity in READ_GROUP_TIME_GRANULARITY:
            return {'$dateTrunc': {'date': date, 'unit': granularity, 'startOfWeek': 'monday', **tz_arg}}
        raise ValueError(f"Unsupported granularity {granularity!r} in {groupby_spec!r}")
    if granularity:
        raise ValueError(f"Granularity set on a no-datetime field: {groupby_spec!r}")
    if field.type in ('many2one', 'selection') or field.inherited or field.translate:
        return f'${path}'                   # raw value; groups are ranked in Python below
    return sort_key_expr(model, fname, None, 'ASC', filter)


def _aggregate_expr(model: BaseModel, spec: CollectionSpec, aggregate_spec: str) -> tuple[dict, str, Field | None]:
    from .models import READ_GROUP_AGGREGATE, parse_read_group_spec  # noqa: PLC0415
    if aggregate_spec == '__count':
        return {'$sum': 1}, '__count', None
    fname, property_name, func = parse_read_group_spec(aggregate_spec)
    if property_name:
        raise ValueError(f"Invalid {aggregate_spec!r}, this dot notation is not supported")
    field = model._fields.get(fname)
    if field is None:
        raise ValueError(f"Invalid field {fname!r} on model {model._name!r} for {aggregate_spec!r}.")
    if not func:
        raise ValueError(f"Aggregate method is mandatory for {fname!r}")
    if func not in READ_GROUP_AGGREGATE:
        raise ValueError(f"Invalid aggregate method {func!r} for {aggregate_spec!r}.")
    if func == 'recordset' and not (field.relational or fname == 'id'):
        raise ValueError(f"Aggregate method {func!r} can be only used on relational field (or id) (for {aggregate_spec!r}).")
    path = f'${spec.target(fname)}'
    expr = {
        'sum': {'$sum': path}, 'avg': {'$avg': path}, 'max': {'$max': path}, 'min': {'$min': path},
        'bool_and': {'$min': path}, 'bool_or': {'$max': path},
        'array_agg': {'$push': path}, 'recordset': {'$push': path},
        'array_agg_distinct': {'$addToSet': path}, 'count_distinct': {'$addToSet': path},
        'count': {'$sum': {'$cond': [{'$ne': [path, None]}, 1, 0]}},
    }[func]
    return expr, func, field


def _group_value(field: Field | None, func: str | None, value):
    if func == 'count_distinct':
        return len([v for v in value if v is not None])
    if func in ('array_agg', 'array_agg_distinct', 'recordset'):
        return [from_bson(v, field) for v in value] if value else None
    if func in ('__count', 'count') or field is None or value is None:
        return value
    if isinstance(value, datetime.datetime) and field.type == 'date':
        return value.date()
    if field.type in ('float', 'monetary') or isinstance(value, Decimal128):
        return from_bson(value, field)
    return value


class _Desc:
    """ Sort key wrapper reversing the natural order. """
    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        return other.value < self.value

    def __eq__(self, other):
        return self.value == other.value

    __hash__ = None


def _having_filter(having: list, aggregates: list[str]):
    index = {aspec: i for i, aspec in enumerate(aggregates)}
    compare = {
        '=': lambda v, r: v == r, '!=': lambda v, r: v != r, '<': lambda v, r: v < r, '>': lambda v, r: v > r,
        '<=': lambda v, r: v <= r, '>=': lambda v, r: v >= r, 'in': lambda v, r: v in r, 'not in': lambda v, r: v not in r,
    }

    def accept(values):
        stack = []
        for item in reversed(having):
            if item == '!':
                stack.append(not stack.pop())
            elif item == '&':
                stack.append(stack.pop() & stack.pop())
            elif item == '|':
                stack.append(stack.pop() | stack.pop())
            elif isinstance(item, (list, tuple)) and len(item) == 3 and item[1] in compare:
                left, operator, right = item
                if left not in index:
                    raise ValueError(f"Invalid having clause {item!r}: {left!r} is not an aggregate")
                stack.append(compare[operator](values[index[left]], right))
            else:
                raise ValueError(f"Invalid having clause {item!r}: it should be a domain-like clause")
        while len(stack) > 1:
            stack.append(stack.pop() & stack.pop())
        return stack[0]
    return accept


def read_group_rows(model: BaseModel, query: MongoQuery, groupby: list[str], aggregates: list[str],
                    having: list, offset: int, limit: int | None, order: str | None) -> list[tuple]:
    """ The raw rows of ``_read_group`` (groupby values then aggregate values),
    sorted, with ``having``, ``offset`` and ``limit`` applied. """
    from .models import parse_read_group_spec, regex_order_part_read_group  # noqa: PLC0415
    env = model.env
    spec = store(model).storage(model)
    unwinds: list[dict] = []
    group_id = {f'g{i}': _group_key_expr(model, spec, gspec, query.filter, unwinds) for i, gspec in enumerate(groupby)}
    aggs = [_aggregate_expr(model, spec, aspec) for aspec in aggregates]
    pipeline = [*base_stages(model), *match_stages(query.filter), *unwinds,
                {'$group': {'_id': group_id, **{f'a{i}': expr for i, (expr, _, _) in enumerate(aggs)}}}]
    rows = []
    for doc in model_collection(model).aggregate(pipeline):
        groups = tuple(doc['_id'].get(f'g{i}') for i in range(len(groupby)))
        values = tuple(_group_value(field, func, doc[f'a{i}']) for i, (_, func, field) in enumerate(aggs))
        rows.append((groups, values))
    if having:
        accept = _having_filter(having, aggregates)
        rows = [(g, v) for g, v in rows if accept(v)]

    # ordering happens here so many2one, selection and translated groups follow
    # their own order (PostgreSQL joins the comodel; MongoDB cannot)
    terms = []
    for part in (order or ','.join(groupby)).split(','):
        if not part:
            continue
        match = regex_order_part_read_group.fullmatch(part)
        if not match:
            raise ValueError(f"Invalid order {order!r} for _read_group()")
        term, direction = match['term'], (match['direction'] or 'ASC').upper()
        nulls = (match['nulls'] or '').upper() or ('NULLS LAST' if direction == 'ASC' else 'NULLS FIRST')
        rank = None
        if term in groupby:
            kind, position = 'group', groupby.index(term)
            field = model._fields[parse_read_group_spec(term)[0]]
            if field.type == 'many2one' and env[field.comodel_name]._order != 'id':
                comodel = env[field.comodel_name]
                ids = [g[position] for g, _ in rows if g[position] is not None]
                rank = {id_: i for i, id_ in enumerate(ranked_ids(comodel, ids, comodel._order, False))}
            elif field.type == 'selection':
                rank = {key: i for i, key in enumerate(field.get_values(env))}
            elif field.translate:
                langs = StoredTranslations.fallback_langs(field.translation_lang(env))
                rank = lambda value, langs=langs: next((value[c] for c in langs if c in value), None) if isinstance(value, dict) else value
        elif term in aggregates:
            kind, position = 'agg', aggregates.index(term)
        else:
            raise ValueError(f"Order term {part!r} is not a valid aggregate nor valid groupby")
        terms.append((kind, position, rank, direction, nulls))

    def sort_key(row):
        key = []
        for kind, position, rank, direction, nulls in terms:
            value = row[0][position] if kind == 'group' else row[1][position]
            if isinstance(rank, dict):
                value = rank.get(value)
            elif rank is not None:
                value = rank(value)
            if isinstance(value, Decimal128):
                value = value.to_decimal()
            is_null = value is None
            key.append((is_null != (nulls == 'NULLS FIRST'), 0 if is_null else _Desc(value) if direction == 'DESC' else value))
        return key
    if terms:
        rows.sort(key=sort_key)
    if offset:
        rows = rows[offset:]
    if limit is not None:
        rows = rows[:limit]

    result = []
    for groups, values in rows:
        converted = [
            _group_value(model._fields[parse_read_group_spec(gspec)[0]], None, value)
            for gspec, value in zip(groupby, groups)
        ]
        for gspec, value in zip(groupby, converted):
            field = model._fields[parse_read_group_spec(gspec)[0]]
            if field.translate and isinstance(value, dict):
                langs = StoredTranslations.fallback_langs(field.translation_lang(env))
                converted[groupby.index(gspec)] = next((value[c] for c in langs if c in value), None)
        result.append((*converted, *values))
    return result


# ---------------------------------------------------------------------------
# parent_path (``_parent_store``)
# ---------------------------------------------------------------------------

def _set_paths(model: BaseModel, paths: dict[int, str]) -> None:
    if not paths:
        return
    st = store(model)
    spec = st.storage(model)
    coll = model_collection(model)
    target = spec.target('parent_path')
    if spec.embedded:
        for id_, path in paths.items():
            st.set_elements(model.env.cr, coll, spec.array_path, [id_], {target: path}, spec.key_target)
    else:
        st.update_docs(model.env.cr, coll, {id_: {target: path} for id_, path in paths.items()})
    field = model._fields['parent_path']
    for id_, path in paths.items():
        field._update_cache(model.browse(id_), path)


def parent_store_create(records: BaseModel) -> None:
    paths = {}
    for record in records:
        parent = record[records._parent_name]
        paths[record.id] = f"{parent.parent_path or ''}{record.id}/"
    _set_paths(records, paths)


def parent_store_update_prepare(records: BaseModel, vals_list: list[dict]) -> BaseModel:
    parent_name = records._parent_name
    st = store(records)
    path = st.storage(records).target(parent_name)
    # the cache already holds the new parent: compare against the stored one
    stored = {
        doc['_id']: doc.get(path) or False
        for doc in st.model_collection(records).find({'_id': {'$in': list(records._ids)}}, {path: 1})
    }
    changed = [
        record.id
        for record, vals in zip(records, vals_list)
        if parent_name in vals and stored.get(record.id, False) != (vals[parent_name] or False)
    ]
    return records.browse(changed)


def parent_store_update(records: BaseModel) -> None:
    from odoo.exceptions import UserError  # noqa: PLC0415
    model = records
    spec = store(model).storage(model)
    target = spec.target('parent_path')
    for parent, nodes in records.grouped(records._parent_name).items():
        prefix = parent.parent_path or ''
        if prefix:
            parent_ids = {int(label) for label in prefix.split('/')[:-1]}
            if not parent_ids.isdisjoint(nodes._ids):
                ir_model = model.env['ir.model']._get(model._name)
                raise UserError(model.env._(
                    "You are creating a loop in your '%s' records. "
                    "A record cannot be a child of itself or one of its own sub-items. "
                    "Please select a different parent.", ir_model.name))
        updated = {}
        for node in nodes:
            old_path = node.parent_path
            query = MongoQuery(model, {target: {'$regex': '^' + re.escape(old_path)}})
            for doc in query.run({target: 1}):
                updated[doc['_id']] = prefix + doc[target][len(old_path) - len(f'{node.id}/'):]
        _set_paths(model, updated)
        model.browse(list(updated)).modified(['parent_path'])


def parent_store_compute(model: BaseModel) -> None:
    spec = store(model).storage(model)
    parent_target = spec.target(model._parent_name)
    parents = {doc['_id']: doc.get(parent_target) for doc in MongoQuery(model).run({parent_target: 1})}
    paths: dict[int, str] = {}

    def path_of(id_, seen=()):
        if id_ in paths:
            return paths[id_]
        parent = parents.get(id_)
        prefix = path_of(parent, (*seen, id_)) if parent and parent in parents and parent not in seen else ''
        paths[id_] = f'{prefix}{id_}/'
        return paths[id_]
    for id_ in parents:
        path_of(id_)
    _set_paths(model, paths)
    model.invalidate_model(['parent_path'])
