"""MongoDB storage for models that declare ``_storage = 'mongodb'``.

The ORM API is unchanged. PostgreSQL keeps an id-only shadow table per model,
plus the fields listed in ``_shadow_columns``, so sequences, foreign keys and
framework joins keep working. Every stored column lives in one MongoDB document
per record, laid out by the signed mapping spec (``.migration/mapping_spec.json``).

MongoDB writes happen at flush time. Each write first registers its inverse on
the cursor's undo log (see ``odoo.sql_db``), so a rollback or a savepoint
rollback in PostgreSQL also undoes the matching MongoDB writes.

Environment:
    ODOO_MONGODB_URI                connection string (default: local server)
    ODOO_MONGODB_DATABASE           must be ``DATABASE``; anything else fails closed
    ODOO_MONGODB_PG_DATABASE        the one PostgreSQL database that owns the spec's
                                    collection names; any other PostgreSQL database
                                    (tests, clones) gets ``<dbname>__``-prefixed ones
"""
from __future__ import annotations

import datetime as dt
import functools
import hashlib
import json
import logging
import os
import re
import typing
from collections import defaultdict
from pathlib import Path

import psycopg2.errors

from odoo.tools import SQL, split_every, sql
from odoo.tools.constants import IN_MAX

from .domains import DomainAnd, DomainBool, DomainCondition, DomainNot, DomainOr

if typing.TYPE_CHECKING:
    from .fields import Field
    from .models import BaseModel
    from .query import Query

_logger = logging.getLogger(__name__)

DATABASE = 'odoo_unt13'     # the only target in .migration/allowed_targets.json
SPEC_PATH = Path(__file__).resolve().parents[2] / '.migration' / 'mapping_spec.json'
SPEC_SHA256 = 'f372de32464a1b029016d82939230bb64c6b35f84777c1bf5edca30bfe565c50'
DEFAULT_URI = 'mongodb://localhost:27017'

TRANSLATED_PREFIX = '__lang_'


class StorageError(Exception):
    """ The model or the configuration does not match the storage contract. """


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

@functools.cache
def _spec_tables() -> dict[str, dict]:
    raw = SPEC_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SPEC_SHA256:
        raise StorageError(f"{SPEC_PATH} has sha256 {digest}, expected the signed {SPEC_SHA256}")
    return {coll['root_table']: coll for coll in json.loads(raw)['collections']}


@functools.cache
def _client(uri: str):
    import pymongo  # noqa: PLC0415
    return pymongo.MongoClient(uri, tz_aware=False, appname='odoo', connect=False)


def get_database():
    name = os.environ.get('ODOO_MONGODB_DATABASE', DATABASE)
    if name != DATABASE:
        raise StorageError(f"MongoDB database {name!r} is not allowed, only {DATABASE!r} is")
    return _client(os.environ.get('ODOO_MONGODB_URI', DEFAULT_URI)).get_database('odoo_unt13')


def collection_prefix(dbname: str) -> str:
    return '' if dbname == os.environ.get('ODOO_MONGODB_PG_DATABASE') else f'{dbname}__'


def get_collection(model: BaseModel):
    prefix = collection_prefix(model.env.cr.dbname)
    return get_database().get_collection(prefix + _layout(model)['collection'])


def _layout(model: BaseModel) -> dict:
    """ Return the spec entry of the model's table, with ``paths``
    (field name -> document path) and ``types`` (field name -> BSON type). """
    layouts = model.pool.__dict__.setdefault('_mongodb_layouts', {})
    fields, layout = layouts.get(model._name, (None, None))
    if fields is not model._fields:     # fields change while modules load
        spec = _spec_tables().get(model._table)
        if spec is None:
            raise StorageError(f"{model._name}: table {model._table!r} is not in the signed mapping spec")
        columns = {f['source']: f for f in spec['fields']}
        paths, types = {'id': '_id'}, {'id': 'int'}
        for field in model._fields.values():
            if not (field.store and field.column_type) or field.name == 'id':
                continue
            if field.name not in columns:
                raise StorageError(f"{model._name}: column {field.name!r} is not in the signed mapping of {model._table!r}")
            paths[field.name] = columns[field.name]['target']
            types[field.name] = columns[field.name]['bson_type']
        layout = {'collection': spec['collection'], 'indexes': spec['indexes'], 'paths': paths, 'types': types}
        layouts[model._name] = (model._fields, layout)
    return layout


def _references(registry) -> dict[str, list[Field]]:
    """ Return the many2one fields of MongoDB models, by comodel name. """
    refs = registry.__dict__.get('_mongodb_references')
    if refs is None:
        refs = {}
        for model_cls in registry.models.values():
            if model_cls._storage == 'mongodb' and not model_cls._abstract:
                for field in model_cls._fields.values():
                    if field.type == 'many2one' and field.store:
                        refs.setdefault(field.comodel_name, []).append(field)
        if registry.ready:
            registry._mongodb_references = refs
    return refs


def unlink_dependents(records: BaseModel) -> None:
    """ Apply ``ondelete`` of the many2one fields of MongoDB models that
    reference ``records`` through the ORM, so documents follow. PostgreSQL
    foreign keys on shadow columns would only change the shadow rows. """
    _unlink_links(records)
    for field in _references(records.pool).get(records._name, ()):
        dependents = records.env[field.model_name].sudo().with_context(active_test=False).search(
            [(field.name, 'in', records.ids)])
        if not dependents:
            continue
        if field.ondelete == 'cascade':
            dependents.unlink()
        elif field.ondelete == 'restrict':
            raise psycopg2.errors.ForeignKeyViolation(
                f"{records} is still referenced by {field} of {dependents}")
        else:
            dependents.write({field.name: False})


# ---------------------------------------------------------------------------
# many2many relations
# ---------------------------------------------------------------------------

@functools.cache
def _spec_relations() -> dict[str, tuple[dict, dict | None]]:
    """ Return the many2many relation tables of the signed spec, with their
    collection and their junction array (None for a root junction collection). """
    relations = {}
    for coll in _spec_tables().values():
        if isinstance(coll['key']['target'], list) and not coll['fields']:
            relations[coll['root_table']] = (coll, None)
        for embed in coll['embeds']:
            if not embed['fields'] and len(embed['child_fields']) == 1 and len(embed['parent_key']) == 1:
                relations[embed['child_table']] = (coll, embed)
    return relations


def relation_layout(field: Field, env) -> dict | None:
    """ Return how the relation table of the many2many ``field`` is stored in
    MongoDB, or None if it stays in PostgreSQL. Links are dicts mapping the
    relation's two columns to record ids. """
    model, comodel = env[field.model_name], env[field.comodel_name]
    if 'mongodb' not in (model._storage, comodel._storage):
        return None
    if (entry := _spec_relations().get(field.relation)) is None:
        return None
    coll, embed = entry
    columns = {field.column1, field.column2}
    if embed is None:
        targets = dict(zip(coll['key']['source'], coll['key']['target'], strict=True))
        if set(targets) != columns:
            raise StorageError(f"{field}: columns {sorted(columns)} are not the signed key of {field.relation!r}")
        return {'collection': coll['collection'], 'targets': targets, 'indexes': coll['indexes']}
    owner, other = embed['parent_key'][0], embed['child_fields'][0]['source']
    if {owner, other} != columns:
        raise StorageError(f"{field}: columns {sorted(columns)} are not the signed columns of {field.relation!r}")
    owner_model = model if field.column1 == owner else comodel
    if owner_model._table != coll['root_table']:
        raise StorageError(f"{field}: {field.relation!r} is embedded in {coll['root_table']!r}, not {owner_model._table!r}")
    if owner_model._storage != 'mongodb':
        return None
    return {
        'collection': coll['collection'], 'owner': owner, 'other': other,
        'array': embed['array_path'], 'element': embed['child_fields'][0]['target'],
    }


def _relation_collection(env, layout: dict):
    return get_database().get_collection(collection_prefix(env.cr.dbname) + layout['collection'])


def ensure_relation_indexes(env, layout: dict) -> None:
    """ Create the indexes of a root junction collection; junction arrays are
    indexed with their owner collection. """
    if 'targets' in layout:
        _create_indexes(_relation_collection(env, layout), layout['indexes'])


def find_links(env, layout: dict, column: str, ids: typing.Iterable[int]) -> list[dict]:
    """ Return the links whose ``column`` is in ``ids``. """
    collection, ids = _relation_collection(env, layout), list(ids)
    if 'targets' in layout:
        targets = layout['targets']
        projection = dict.fromkeys(targets.values(), 1)
        return [
            {col: doc[path] for col, path in targets.items()}
            for doc in collection.find({targets[column]: {'$in': ids}}, projection)
        ]
    owner, array, element = layout['owner'], layout['array'], layout['element']
    if column == owner:
        query, wanted = {'_id': {'$in': ids}}, None
    else:
        query, wanted = {f'{array}.{element}': {'$in': ids}}, set(ids)
    return [
        {owner: doc['_id'], layout['other']: item[element]}
        for doc in collection.find(query, {array: 1})
        for item in doc.get(array, ())
        if wanted is None or item[element] in wanted
    ]


def linked_ids(env, layout: dict, column: str, other: str, other_ids: typing.Iterable[int]) -> list[int]:
    """ Return the distinct ids in ``column`` of the links whose ``other``
    column is in ``other_ids``. """
    collection = _relation_collection(env, layout)
    if 'targets' in layout:
        targets = layout['targets']
        return collection.distinct(targets[column], {targets[other]: {'$in': list(other_ids)}})
    if column == layout['owner']:
        return collection.distinct('_id', {f"{layout['array']}.{layout['element']}": {'$in': list(other_ids)}})
    return list({link[column] for link in find_links(env, layout, other, other_ids)})


def _apply_to_arrays(collection, layout: dict, links: list[dict], add: bool) -> None:
    import pymongo  # noqa: PLC0415
    array, element = layout['array'], layout['element']
    others = defaultdict(list)
    for link in links:
        others[link[layout['owner']]].append(link[layout['other']])
    collection.bulk_write([
        pymongo.UpdateOne({'_id': owner_id}, {'$addToSet': {array: {'$each': [{element: id_} for id_ in ids]}}}
                          if add else {'$pull': {array: {element: {'$in': ids}}}})
        for owner_id, ids in others.items()
    ])


def lock_links(field: Field, env, layout: dict, links: list[dict], check: bool) -> None:
    """ Lock the shadow rows of the links' records, like the foreign keys of
    the relation table: rows of the column that owns the links FOR UPDATE, so
    writers of the same links serialize and their undo stays correct, the
    other rows FOR KEY SHARE. Both columns of a relation on one table lock
    their union FOR UPDATE in id order, so opposite links cannot deadlock.
    With ``check``, a missing record raises. """
    tables = {field.column1: env[field.model_name]._table, field.column2: env[field.comodel_name]._table}
    serial = layout['owner'] if 'owner' in layout else next(iter(layout['targets']))
    if tables[field.column1] == tables[field.column2]:
        locks = [(tables[serial], {link[column] for link in links for column in tables}, SQL("FOR UPDATE"))]
    else:
        locks = [
            (tables[column], {link[column] for link in links}, SQL("FOR UPDATE") if column == serial else SQL("FOR KEY SHARE"))
            for column in sorted(tables, key=lambda column: column != serial)
        ]
    for table, ids, lock in locks:
        env.cr.execute(SQL("SELECT id FROM %s WHERE id = ANY(%s) ORDER BY id %s", SQL.identifier(table), sorted(ids), lock))
        if check and (missing := ids.difference(id_ for id_, in env.cr.fetchall())):
            raise psycopg2.errors.ForeignKeyViolation(f"{field}: no {table} rows {sorted(missing)}")


def add_links(env, layout: dict, links: list[dict]) -> None:
    """ Add new links, like the relation table's INSERT. """
    import pymongo.errors  # noqa: PLC0415
    from bson import ObjectId  # noqa: PLC0415
    collection = _relation_collection(env, layout)
    if 'owner' in layout:
        env.cr.add_undo(lambda: _apply_to_arrays(collection, layout, links, add=False))
        _apply_to_arrays(collection, layout, links, add=True)
        return
    docs = [{'_id': ObjectId()} | {path: link[col] for col, path in layout['targets'].items()} for link in links]
    env.cr.add_undo(lambda: collection.delete_many({'_id': {'$in': [doc['_id'] for doc in docs]}}))
    try:
        collection.insert_many(docs, ordered=False)
    except pymongo.errors.BulkWriteError as e:
        # like ON CONFLICT DO NOTHING on the relation's primary key
        if any(error['code'] != 11000 for error in e.details['writeErrors']):
            raise


def remove_links(env, layout: dict, links: list[dict]) -> None:
    """ Remove links, like the relation table's DELETE. """
    collection = _relation_collection(env, layout)
    if 'owner' in layout:
        env.cr.add_undo(lambda: _apply_to_arrays(collection, layout, links, add=True))
        _apply_to_arrays(collection, layout, links, add=False)
        return
    targets = layout['targets']
    priors = list(collection.find({'$or': [{path: link[col] for col, path in targets.items()} for link in links]}))
    if priors:
        env.cr.add_undo(lambda: collection.insert_many(priors))
        collection.delete_many({'_id': {'$in': [doc['_id'] for doc in priors]}})


def _relation_fields(registry) -> list[Field]:
    """ Return the stored many2many fields whose relation is in the spec. """
    fields = registry.__dict__.get('_mongodb_relation_fields')
    if fields is None:
        relations = _spec_relations()
        fields = [
            field
            for model_cls in registry.models.values()
            if not model_cls._abstract
            for field in model_cls._fields.values()
            if field.type == 'many2many' and field.store and field.relation in relations
        ]
        if registry.ready:
            registry._mongodb_relation_fields = fields
    return fields


def _unlink_links(records: BaseModel) -> None:
    """ Apply ``ondelete`` to the MongoDB links of ``records``, as the
    foreign keys of a relation table would. """
    sides = []
    for field in _relation_fields(records.pool):
        for column, model_name, ondelete in (
            (field.column1, field.model_name, 'cascade'),
            (field.column2, field.comodel_name, field.ondelete),
        ):
            if model_name == records._name and (layout := relation_layout(field, records.env)):
                if column != layout.get('owner'):   # owner documents are deleted with records
                    sides.append((ondelete != 'restrict', field, layout, column))
    for cascade, field, layout, column in sorted(sides, key=lambda side: side[0]):
        if not (links := find_links(records.env, layout, column, records.ids)):
            continue
        if not cascade:
            raise psycopg2.errors.ForeignKeyViolation(f"{records} is still linked through {field}")
        remove_links(records.env, layout, links)


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------

def auto_init(model: BaseModel) -> None:
    """ Create the PostgreSQL shadow table and the MongoDB indexes. """
    if not model._auto or model._abstract:
        raise StorageError(f"{model._name}: MongoDB storage requires a regular stored model")
    if model._parent_store:
        raise NotImplementedError(f"{model._name}: _parent_store is not supported on MongoDB storage yet")
    for field in model._fields.values():
        if field.store and field.company_dependent:
            raise NotImplementedError(f"{field}: company-dependent fields are not supported on MongoDB storage yet")
    shadow = [model._fields[fname] for fname in model._shadow_columns]
    for field in shadow:
        if not (field.store and field.column_type):
            raise StorageError(f"{field}: shadow columns must be stored column fields")
    _layout(model)  # fail before touching PostgreSQL

    cr = model.env.cr
    if not sql.table_exists(cr, model._table):
        sql.create_model_table(cr, model._table, model._description, [
            (field.name, field.stored_sql_column_type, field.string) for field in shadow
        ])
    columns = sql.table_columns(cr, model._table)
    for field in shadow:
        field.update_db(model, columns)
    if model._table_objects:
        _logger.warning("%s: SQL constraints and indexes are not applied on MongoDB storage: %s",
                        model._name, ", ".join(model._table_objects))
    ensure_indexes(model)


def ensure_indexes(model: BaseModel) -> None:
    """ Create the indexes of the signed spec. Unique indexes skip documents
    missing a key, like PostgreSQL unique constraints skip NULLs. """
    _create_indexes(get_collection(model), _layout(model)['indexes'])


def _create_indexes(collection, indexes: list[dict]) -> None:
    for index in indexes:
        keys = [(path, direction) for path, direction in index['keys']]
        if keys == [('_id', 1)]:
            continue
        options = {}
        if index.get('unique'):
            options['unique'] = True
            options['partialFilterExpression'] = {path: {'$exists': True} for path, _ in keys}
        collection.create_index(keys, **options)


# ---------------------------------------------------------------------------
# value conversion
# ---------------------------------------------------------------------------

def _to_bson(bson_type: str, value):
    from bson.decimal128 import Decimal128  # noqa: PLC0415
    if value is None:
        return None
    if hasattr(value, 'adapted'):       # psycopg2 Json wrapper
        value = value.adapted
    if bson_type == 'decimal':
        return Decimal128(str(value))
    if bson_type == 'double':
        return float(value)
    if bson_type == 'date':
        if not isinstance(value, dt.datetime):
            value = dt.datetime.combine(value, dt.time.min)
        return value.replace(microsecond=value.microsecond // 1000 * 1000)
    return value


def _from_bson(field: Field, value, env):
    from bson.decimal128 import Decimal128  # noqa: PLC0415
    if value is None:
        return None
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if field.type == 'date' and isinstance(value, dt.datetime):
        return value.date()
    if field.translate is True and not env.context.get('prefetch_langs'):
        from .fields_textual import StoredTranslations  # noqa: PLC0415
        for lang in StoredTranslations.fallback_langs(field.translation_lang(env)):
            if value.get(lang) is not None:
                return value[lang]
        return None
    return value


def _document(model: BaseModel, id_: int, values: dict) -> dict:
    layout = _layout(model)
    doc = {'_id': id_}
    for fname, value in values.items():
        value = _to_bson(layout['types'][fname], value)
        if value is not None:       # null_missing_equiv: NULL is stored as a missing key
            doc[layout['paths'][fname]] = value
    return doc


# ---------------------------------------------------------------------------
# writes
# ---------------------------------------------------------------------------

def _raise_unique_violation(model: BaseModel, error) -> typing.NoReturn:
    write_errors = error.details.get('writeErrors') or [{}]
    if write_errors[0].get('code') == 11000:
        raise psycopg2.errors.UniqueViolation(
            f"{model._name}: duplicate key {write_errors[0].get('keyValue')!r}") from error
    raise error


def insert(model: BaseModel, ids: list[int], rows: list[dict]) -> None:
    """ Insert one document per new record; ``rows`` hold column values. """
    import pymongo.errors  # noqa: PLC0415
    collection = get_collection(model)
    model.env.cr.add_undo(lambda: collection.delete_many({'_id': {'$in': ids}}))
    try:
        collection.insert_many([_document(model, id_, row) for id_, row in zip(ids, rows, strict=True)])
    except pymongo.errors.BulkWriteError as e:
        _raise_unique_violation(model, e)


def update(model: BaseModel, ids: list[int], vals_list: list[dict]) -> None:
    """ Apply column updates (as computed by ``_write_multi``) to documents. """
    import pymongo  # noqa: PLC0415
    import pymongo.errors  # noqa: PLC0415
    layout = _layout(model)
    collection = get_collection(model)
    # lock the shadow rows: concurrent writers of a document serialize there
    model.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s FOR UPDATE",
                             SQL.identifier(model._table), tuple(ids)))
    priors = {doc['_id']: doc for doc in collection.find({'_id': {'$in': ids}})}
    model.env.cr.add_undo(lambda: [collection.replace_one({'_id': doc['_id']}, doc) for doc in priors.values()])
    ops = []
    for id_, vals in zip(ids, vals_list, strict=True):
        to_set, to_unset = {}, {}
        for fname, value in vals.items():
            field, path = model._fields[fname], layout['paths'][fname]
            if hasattr(value, 'adapted'):
                value = value.adapted
            if field.translate is True and value is not None:
                partial, translations = value
                old = (priors.get(id_) or {}).get(path)
                if partial:
                    value = (old or {'en_US': next(iter(translations.values()))}) | translations
                else:
                    value = translations
            value = _to_bson(layout['types'][fname], value)
            if value is None:
                to_unset[path] = ''
            else:
                to_set[path] = value
        change = {}
        if to_set:
            change['$set'] = to_set
        if to_unset:
            change['$unset'] = to_unset
        if change:
            ops.append(pymongo.UpdateOne({'_id': id_}, change))
    if ops:
        try:
            collection.bulk_write(ops, ordered=True)
        except pymongo.errors.BulkWriteError as e:
            _raise_unique_violation(model, e)


def delete(model: BaseModel, ids: typing.Iterable[int]) -> None:
    """ Delete documents; run right after the shadow rows are deleted. """
    collection = get_collection(model)
    ids = list(ids)
    priors = list(collection.find({'_id': {'$in': ids}}))
    if priors:
        model.env.cr.add_undo(lambda: collection.insert_many(priors))
    collection.delete_many({'_id': {'$in': ids}})


# ---------------------------------------------------------------------------
# reads
# ---------------------------------------------------------------------------

def fetch(model: BaseModel, query: Query, fields: typing.Iterable[Field]) -> BaseModel:
    """ Read ``fields`` of the records of ``query`` into the cache. """
    fields = list(fields)
    if translated := [field.name for field in fields if field.translate]:
        model.flush_model(translated)
    ids = list(query.get_result_ids())
    if not ids:
        return model.browse()
    layout = _layout(model)
    projection = {layout['paths'][field.name]: 1 for field in fields}
    docs = {doc['_id']: doc for doc in get_collection(model).find({'_id': {'$in': ids}}, projection)}
    if missing := [id_ for id_ in ids if id_ not in docs]:
        _logger.warning("%s: shadow rows without a MongoDB document: %s", model._name, missing)
    fetched = model.browse([id_ for id_ in ids if id_ in docs])
    for field in fields:
        path = layout['paths'][field.name]
        field._insert_cache(fetched, [_from_bson(field, docs[id_].get(path), model.env) for id_ in fetched._ids])
    return fetched


def search(model: BaseModel, domain, sec_domain, order: str | None, limit, offset) -> Query:
    """ Back end of ``_search`` once ``domain`` is fully optimized. """
    model.flush_model()
    match = to_filter(model, domain)
    if not sec_domain.is_true():
        self_sudo = model.sudo().with_context(active_test=False)
        sec_domain = sec_domain.optimize_full(self_sudo, search_domain=domain)
        if sec_domain.is_false():
            return model.browse()._as_query()
        match = {'$and': [match, to_filter(self_sudo, sec_domain)]}
    pipeline = []
    if translated := _translated_fields(model, domain, sec_domain, order):
        pipeline.append({'$addFields': {
            TRANSLATED_PREFIX + fname: _translated_expr(model, fname) for fname in translated
        }})
    pipeline.append({'$match': match})
    pipeline.extend(_sort_stages(model, order))
    # read offset + limit ids (a bounded top-k sort), dropping documents
    # without a shadow row (no committed record) before paging; read further
    # only when such documents left the page short
    bound = (offset or 0) + limit if limit else None
    while True:
        stages = pipeline + ([{'$limit': bound}] if bound else []) + [{'$project': {'_id': 1}}]
        read, ids, orphans = 0, [], []
        with get_collection(model).aggregate(stages, batchSize=IN_MAX) as cursor:
            for batch in split_every(IN_MAX, (doc['_id'] for doc in cursor)):
                read += len(batch)
                alive = _alive(model, batch)
                orphans.extend(id_ for id_ in batch if id_ not in alive)
                ids.extend(id_ for id_ in batch if id_ in alive)
        if not (bound and orphans and read == bound and len(ids) < (offset or 0) + limit):
            break
        bound += len(orphans)
    if orphans:
        _logger.warning("%s: MongoDB documents without a shadow row: %s", model._name, orphans)
    ids = ids[offset or 0:]
    if limit:
        ids = ids[:limit]
    return model.browse(ids)._as_query(ordered=bool(order))


def _alive(model: BaseModel, ids: list[int]) -> set[int]:
    alive = set()
    for sub_ids in split_every(IN_MAX, ids):
        model.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s", SQL.identifier(model._table), tuple(sub_ids)))
        alive.update(id_ for id_, in model.env.cr.fetchall())
    return alive


def _translated_fields(model, domain, sec_domain, order) -> list[str]:
    names = {cond.field_expr for dom in (domain, sec_domain) for cond in dom.iter_conditions()}
    names.update(part.split()[0] for part in (order or '').split(',') if part.strip())
    return sorted(n for n in names if n in model._fields and model._fields[n].translate is True)


def _translated_expr(model: BaseModel, fname: str) -> dict:
    from .fields_textual import StoredTranslations  # noqa: PLC0415
    field, path = model._fields[fname], _layout(model)['paths'][fname]
    langs = StoredTranslations.fallback_langs(field.translation_lang(model.env))
    return {'$ifNull': [f'${path}.{lang}' for lang in langs] + [None]}


def _path(model: BaseModel, field: Field) -> str:
    if field.translate is True:
        return TRANSLATED_PREFIX + field.name
    return _layout(model)['paths'][field.name]


def _sort_stages(model: BaseModel, order: str | None) -> list[dict]:
    from .models import regex_order  # noqa: PLC0415
    if not order:
        return []
    flags, sort = {}, {}
    for i, part in enumerate(order.split(',')):
        match = regex_order.match(part)
        if not match:
            raise ValueError(f"Invalid order {order!r}")
        fname, direction, nulls = match['field'], (match['direction'] or 'ASC').upper(), (match['nulls'] or '').upper()
        field = model._fields.get(fname)
        if field is None or not (field.store and field.column_type) or match['property']:
            raise NotImplementedError(f"{model._name}: cannot order by {part.strip()!r} on MongoDB storage")
        path = _path(model, field)
        step = 1 if direction == 'ASC' else -1
        # PostgreSQL puts NULLs last ascending and first descending
        nulls_last = nulls == 'NULLS LAST' if nulls else step == 1
        flags[f'__null{i}'] = {'$cond': [{'$eq': [{'$ifNull': [f'${path}', None]}, None]}, 1, 0]}
        sort[f'__null{i}'] = 1 if nulls_last else -1
        sort[path] = step
    sort.setdefault('_id', 1)
    return [{'$addFields': flags}, {'$sort': sort}]


# ---------------------------------------------------------------------------
# domain translation
# ---------------------------------------------------------------------------

def _like_regex(pattern: str, ilike: bool):
    regex = ''.join('.*' if c == '%' else '.' if c == '_' else re.escape(c) for c in pattern)
    return re.compile(f'^{regex}$', re.DOTALL | (re.IGNORECASE if ilike else 0))


def to_filter(model: BaseModel, domain) -> dict:
    """ Translate a fully optimized domain into a MongoDB filter. """
    if isinstance(domain, DomainBool):
        return {} if domain.value else {'_id': {'$in': []}}
    if isinstance(domain, DomainNot):
        return {'$nor': [to_filter(model, domain.child)]}
    if isinstance(domain, DomainAnd):
        return {'$and': [to_filter(model, child) for child in domain.children]}
    if isinstance(domain, DomainOr):
        return {'$or': [to_filter(model, child) for child in domain.children]}
    if isinstance(domain, DomainCondition):
        return _condition(model, domain)
    raise NotImplementedError(f"{model._name}: domain {domain} cannot run on MongoDB storage")


def _condition(model: BaseModel, cond: DomainCondition) -> dict:
    from .domains import Domain  # noqa: PLC0415
    from .query import Query  # noqa: PLC0415
    operator, value = cond.operator, cond.value
    unsupported = NotImplementedError(f"{model._name}: condition {cond} cannot run on MongoDB storage")
    if '.' in cond.field_expr:
        raise unsupported
    field = cond._field(model)
    model.check_field_access(field, 'read')

    if field.type == 'many2many' and operator in ('any', 'not any', 'any!', 'not any!'):
        return _many2many_condition(model, field, operator, value, unsupported)
    if operator in ('any', 'not any', 'any!', 'not any!'):
        inverse = None
        if field.name == 'id':
            comodel = model
        elif field.type == 'many2one':
            comodel = model.env[field.comodel_name]
        elif field.type == 'one2many':
            comodel, inverse = model.env[field.comodel_name].with_context(**field.context), field.inverse_name
        else:
            raise unsupported
        if operator.endswith('!'):
            comodel = comodel.sudo()
        if isinstance(value, Query):
            ids = value.get_result_ids()
        elif isinstance(value, Domain) and inverse:
            ids = comodel._search(value & Domain(inverse, 'not in', {False})).get_result_ids()
        elif isinstance(value, Domain):
            ids = comodel.with_context(active_test=False)._search(value).get_result_ids()
        else:
            raise unsupported
        if inverse:
            ids = comodel.sudo().browse(ids)[inverse]._ids
        path = '_id' if inverse or field.name == 'id' else _path(model, field)
        return {path: {'$nin' if operator.startswith('not') else '$in': list(ids)}}

    if field.name != 'id' and not (field.store and field.column_type):
        raise unsupported
    path = '_id' if field.name == 'id' else _path(model, field)
    bson_type = _layout(model)['types'][field.name]

    def to_value(v):
        if (v is False and field.type != 'boolean') or v is None:
            return None
        return _to_bson(bson_type, field.convert_to_column(v, model, validate=False))

    if operator in ('in', 'not in'):
        values = [to_value(v) for v in value]
        if None in values and (falsy := field.falsy_value) is not None:
            values.append(to_value(falsy))
        if field.type == 'boolean' and False in values:
            values.append(None)     # a NULL boolean reads as False
        return {path: {'$in' if operator == 'in' else '$nin': values}}

    if operator in ('<', '>', '<=', '>='):
        mongo_op = {'<': '$lt', '>': '$gt', '<=': '$lte', '>=': '$gte'}[operator]
        if (falsy := field.falsy_value) is None:
            return {path: {mongo_op: to_value(value)}}
        # like PostgreSQL: an unset value compares as the field's falsy value
        value = field.convert_to_cache(value, model) or falsy
        accept_null = {'<': falsy < value, '>': falsy > value, '<=': falsy <= value, '>=': falsy >= value}[operator]
        condition = {path: {mongo_op: to_value(value)}}
        return {'$or': [condition, {path: None}]} if accept_null else condition

    if operator.endswith('like') and (bson_type == 'string' or field.translate is True):
        pattern = str(value) if '=' in operator else f'%{value}%'
        regex = _like_regex(pattern, operator.endswith('ilike'))
        return {path: {'$not': regex}} if operator.startswith('not') else {path: regex}

    raise unsupported


def _many2many_condition(model: BaseModel, field: Field, operator: str, value, unsupported) -> dict:
    from .domains import Domain  # noqa: PLC0415
    from .query import Query  # noqa: PLC0415
    if (layout := relation_layout(field, model.env)) is None:
        raise unsupported
    comodel = model.env[field.comodel_name].with_context(**field.context)
    if operator.endswith('!'):
        comodel = comodel.sudo()
    if isinstance(value, Query):
        coids = value.get_result_ids()
    elif isinstance(value, Domain):
        owner_side = field.column1 == layout.get('owner')
        coids = None if owner_side and value.is_true() else comodel._search(value).get_result_ids()
    else:
        raise unsupported
    negate = operator.startswith('not')
    if field.column1 == layout.get('owner'):
        if coids is None:   # any link at all, like the relation table's foreign key
            linked = {f"{layout['array']}.0": {'$exists': True}}
            return {'$nor': [linked]} if negate else linked
        return {f"{layout['array']}.{layout['element']}": {'$nin' if negate else '$in': list(coids)}}
    ids = linked_ids(model.env, layout, field.column1, field.column2, coids)
    return {'_id': {'$nin' if negate else '$in': ids}}
