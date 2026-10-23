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
import decimal
import functools
import hashlib
import itertools
import json
import logging
import os
import re
import typing
from collections import defaultdict
from pathlib import Path

import psycopg2.errors

from odoo.tools import SQL, date_utils, split_every, sql
from odoo.tools.constants import IN_MAX

from .domains import DomainAnd, DomainBool, DomainCondition, DomainCustom, DomainNot, DomainOr

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
        spec, embed = _spec_tables().get(model._table), None
        if spec is None and (entry := _spec_children().get(model._table)):
            spec, embed = entry
        if spec is None:
            raise StorageError(f"{model._name}: table {model._table!r} is not in the signed mapping spec")
        if embed:
            columns = {f['source']: f for f in embed['child_fields'] + embed['parent_key_fields']}
        else:
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
        if embed:
            parent = embed['parent_key'][0]
            if parent not in paths:
                raise StorageError(f"{model._name}: {model._table!r} is embedded in {spec['root_table']!r}, so it needs the field {parent!r}")
            key = embed['key']['source']
            layout['indexes'] = []     # embedded documents are indexed with their parent
            layout['embed'] = {
                'array': embed['array_path'], 'parent': parent, 'parent_path': paths[parent],
                'id_path': columns['id']['target'],
                'key_paths': None if key == ['id'] else [columns[col]['target'] for col in key],
            }
        layouts[model._name] = (model._fields, layout)
    return layout


@functools.cache
def _spec_children() -> dict[str, tuple[dict, dict]]:
    """ Return the child tables the signed spec embeds as documents in the
    array of their parent's collection, with their collection and embed. """
    relations = _spec_relations()
    return {
        embed['child_table']: (coll, embed)
        for coll in _spec_tables().values()
        for embed in coll['embeds']
        if embed['child_table'] not in relations
    }


def _references(registry) -> dict[str, list[Field]]:
    """ Return the many2one fields of MongoDB models, by comodel name. """
    refs = registry.__dict__.get('_mongodb_references')
    if refs is None:
        refs = {}
        for model_cls in registry.models.values():
            if model_cls._storage == 'mongodb' and not model_cls._abstract:
                for field in model_cls._fields.values():
                    if field.type == 'many2one' and field.store and not field.company_dependent:
                        refs.setdefault(field.comodel_name, []).append(field)
        if registry.ready:
            registry._mongodb_references = refs
    return refs


def _pg_cascades(env) -> dict[str, list[Field]]:
    """ Return the ``ondelete='cascade'`` many2one fields of PostgreSQL models,
    by comodel name, whose cascaded records MongoDB documents may reference. """
    registry = env.registry
    cascades = registry.__dict__.get('_mongodb_pg_cascades')
    if cascades is None:
        refs = _references(registry)
        fields_ = [
            field
            for model_cls in registry.models.values()
            if model_cls._storage != 'mongodb' and not model_cls._abstract
            for field in model_cls._fields.values()
            if field.type == 'many2one' and field.store and field.ondelete == 'cascade'
        ]
        followed = {
            model_name for model_name, model_cls in registry.models.items()
            if refs.get(model_name) or any(
                field.type == 'many2many' and field.store and relation_layout(field, env)
                for field in model_cls._fields.values())
        }
        cascades = {}
        while todo := [f for f in fields_ if f.model_name in followed and f not in cascades.get(f.comodel_name, ())]:
            for field in todo:
                cascades.setdefault(field.comodel_name, []).append(field)
                followed.add(field.comodel_name)
        if registry.ready:
            registry._mongodb_pg_cascades = cascades
    return cascades


def _cascade_delete(records: BaseModel) -> None:
    """ Delete ``records`` like PostgreSQL's ``ON DELETE CASCADE``: their own
    dependents follow, but no ``unlink`` override or ``ondelete`` check runs. """
    for field in records._fields.values():
        records.env.remove_to_compute(field, records)
    records.flush_recordset()
    unlink_dependents(records)
    for sub_ids in split_every(IN_MAX, records.ids):
        records.env.cr.execute(SQL("DELETE FROM %s WHERE id IN %s", SQL.identifier(records._table), sub_ids))
        if records._storage == 'mongodb':
            delete(records, sub_ids)
    records.invalidate_recordset(flush=False)


def unlink_dependents(records: BaseModel) -> None:
    """ Apply ``ondelete`` of the many2one fields of MongoDB models that
    reference ``records`` through the ORM, so documents follow. PostgreSQL
    foreign keys on shadow columns would only change the shadow rows. """
    if records._storage == 'mongodb' and _layout(records).get('embed'):
        # lock the parents before the shadow rows are deleted, like child writes
        _lock_parents(records, {prior[0] for prior in _elements(records, records.ids).values()}, check=False)
    _unlink_links(records)
    for field in _references(records.pool).get(records._name, ()):
        dependents = records.env[field.model_name].sudo().with_context(active_test=False).search(
            [(field.name, 'in', records.ids)])
        if not dependents:
            continue
        if field.ondelete == 'cascade':
            _cascade_delete(dependents)
        elif field.ondelete == 'restrict':
            raise psycopg2.errors.ForeignKeyViolation(
                f"{records} is still referenced by {field} of {dependents}")
        else:
            # like PostgreSQL's foreign key: no write() overrides, no access log
            update(dependents, list(dependents._ids), [{field.name: None}] * len(dependents))
            if field.name in dependents._shadow_columns:
                records.env.cr.execute(SQL("UPDATE %s SET %s = NULL WHERE id IN %s", SQL.identifier(
                    dependents._table), SQL.identifier(field.name), tuple(dependents._ids)))
            dependents.invalidate_recordset([field.name], flush=False)
    for field in _pg_cascades(records.env).get(records._name, ()):
        # PostgreSQL deletes these through its foreign key, without the ORM
        if dependents := records.env[field.model_name].sudo().with_context(active_test=False).search(
                [(field.name, 'in', records.ids)]):
            unlink_dependents(dependents)


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
        return {'collection': coll['collection'], 'targets': targets, 'indexes': coll['indexes'],
                'mirror': _mirror_table(field, env)}
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
        'mirror': _mirror_table(field, env),
    }


def _mirrored_relations(registry) -> set[str]:
    """ Return the relation tables declared in ``_shadow_relations``: addon raw
    SQL reads them, so their links are also kept in PostgreSQL. """
    mirrored = registry.__dict__.get('_mongodb_mirrored_relations')
    if mirrored is None:
        mirrored = set()
        for model_cls in registry.models.values():
            for fname in model_cls._shadow_relations:
                field = model_cls._fields.get(fname)
                if field is None or field.type != 'many2many' or not field.store:
                    raise StorageError(f"{model_cls._name}: _shadow_relations entry {fname!r} is not a stored many2many")
                mirrored.add(field.relation)
        if registry.ready:
            registry._mongodb_mirrored_relations = mirrored
    return mirrored


def _mirror_table(field: Field, env) -> str | None:
    return field.relation if field.relation in _mirrored_relations(env.registry) else None


def _mirror_links(env, layout: dict, links: list[dict], add: bool) -> None:
    """ Apply ``links`` to the PostgreSQL mirror of the relation table; the
    transaction and its savepoints roll it back with the rest. """
    if not (table := layout['mirror']) or not links:
        return
    col1, col2 = sorted(links[0])
    pairs = SQL("SELECT * FROM UNNEST(%s::int4[], %s::int4[])", [link[col1] for link in links], [link[col2] for link in links])
    if add:
        query = SQL("INSERT INTO %s (%s, %s) %s ON CONFLICT DO NOTHING",
                    SQL.identifier(table), SQL.identifier(col1), SQL.identifier(col2), pairs)
    else:
        query = SQL("DELETE FROM %s WHERE (%s, %s) IN (%s)",
                    SQL.identifier(table), SQL.identifier(col1), SQL.identifier(col2), pairs)
    env.cr.execute(query)


def fill_relation_mirror(field: Field, env, layout: dict) -> None:
    """ Copy every MongoDB link of ``field`` into its PostgreSQL mirror, which
    writes keep current from then on. """
    table, col1, col2 = (SQL.identifier(name) for name in (field.relation, field.column1, field.column2))
    pairs = _all_links(env, layout, field.column1, field.column2)
    env.cr.execute(SQL("DELETE FROM %s", table))
    if pairs:
        # two array parameters, whatever the number of links
        env.cr.execute(SQL("INSERT INTO %s (%s, %s) SELECT * FROM UNNEST(%s::int4[], %s::int4[])",
                           table, col1, col2, [a for a, _ in pairs], [b for _, b in pairs]))


def relation_mirror_diff(field: Field, env) -> tuple[set, set]:
    """ Return the (column1, column2) links of ``field`` missing from its
    PostgreSQL mirror, and the mirror rows that MongoDB does not have. """
    layout = relation_layout(field, env)
    if not layout or not layout['mirror']:
        raise StorageError(f"{field}: {field.relation!r} has no PostgreSQL mirror")
    links = set(_all_links(env, layout, field.column1, field.column2))
    env.cr.execute(SQL("SELECT %s, %s FROM %s", SQL.identifier(field.column1), SQL.identifier(field.column2),
                       SQL.identifier(field.relation)))
    rows = set(env.cr.fetchall())
    return links - rows, rows - links


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


def _all_links(env, layout: dict, column1: str, column2: str) -> list[tuple[int, int]]:
    """ Return every link of the relation as (column1, column2) pairs. """
    collection = _relation_collection(env, layout)
    if 'targets' in layout:
        targets = layout['targets']
        docs = collection.find({}, dict.fromkeys(targets.values(), 1))
        return [(doc[targets[column1]], doc[targets[column2]]) for doc in docs]
    owner, array, element = layout['owner'], layout['array'], layout['element']
    return [
        (doc['_id'], item[element]) if column1 == owner else (item[element], doc['_id'])
        for doc in collection.find({f'{array}.0': {'$exists': True}}, {array: 1})
        for item in doc[array]
    ]


def links_sql(env, layout: dict, column1: str, column2: str) -> SQL:
    """ Return a SELECT of every link of the relation, with the relation
    table's columns, for PostgreSQL queries that join through it. """
    pairs = _all_links(env, layout, column1, column2)
    if not pairs:
        return SQL("(SELECT NULL::int4 AS %s, NULL::int4 AS %s WHERE FALSE)", SQL.identifier(column1), SQL.identifier(column2))
    return SQL("(SELECT * FROM (VALUES %s) AS links(%s, %s))", SQL(", ").join(SQL("(%s, %s)", a, b) for a, b in pairs),
               SQL.identifier(column1), SQL.identifier(column2))


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
    _mirror_links(env, layout, links, add=True)
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
    _mirror_links(env, layout, links, add=False)
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
    if model._parent_store and _layout(model).get('embed'):
        raise StorageError(f"{model._name}: _parent_store needs a root collection")
    shadow = [model._fields[fname] for fname in model._shadow_columns]
    for field in shadow:
        if not (field.store and field.column_type):
            raise StorageError(f"{field}: shadow columns must be stored column fields")
    _layout(model)  # fail before touching PostgreSQL

    cr = model.env.cr
    new_fields = _new_fields(model)
    if not sql.table_exists(cr, model._table):
        sql.create_model_table(cr, model._table, model._description, [
            (field.name, field.stored_sql_column_type, field.string) for field in shadow
        ])
    columns = sql.table_columns(cr, model._table)
    added = [field.name for field in shadow if field.name not in columns]
    for field in shadow:
        field.update_db(model, columns)
    for field in model._fields.values():
        if field.type == 'many2many' and field.store:   # relation tables outside the spec stay in PostgreSQL
            field.update_db(model, columns)
    queued = [(field, records) for field in new_fields if (records := _init_field_data(model, field))]
    if added:
        # mirror without running the queued computes: they write their shadow
        # columns when flushed, as other tables may not be set up yet
        for field, records in queued:
            model.env.remove_to_compute(field, records)
        mirror_columns(model, added)
        for field, records in queued:
            model.env.add_to_compute(field, records)
    if model._table_objects:
        _logger.warning("%s: SQL constraints and indexes are not applied on MongoDB storage: %s",
                        model._name, ", ".join(model._table_objects))
    ensure_indexes(model)


def _new_fields(model: BaseModel) -> list[Field]:
    """ Return the stored fields of ``model`` that are not reflected yet: like
    a new column in PostgreSQL, their existing documents must be initialized. """
    cr = model.env.cr
    if not sql.table_exists(cr, 'ir_model_fields'):
        return []
    cr.execute(SQL("SELECT name FROM ir_model_fields WHERE model = %s", model._name))
    known = {row[0] for row in cr.fetchall()}
    return [
        field for field in model._fields.values()
        if field.store and field.column_type and field.name != 'id' and field.name not in known
    ]


def _init_field_data(model: BaseModel, field: Field) -> BaseModel | None:
    """ Fill in the missing values of a new field in the existing documents,
    as ``Field._init_column_data`` does for a new PostgreSQL column. Method
    hooks (``init_storage`` given by name) update the column in SQL: a shadow
    column gets their result from PostgreSQL, and other fields are computed
    instead, as are stored related fields. Return the records whose compute
    was queued. """
    from .fields import Field, determine  # noqa: PLC0415
    init = field.init_storage
    if not (init or field.default or field.compute) or field.company_dependent:
        return None
    cr = model.env.cr
    cr.execute(SQL("SELECT id FROM %s ORDER BY id", SQL.identifier(model._table)))
    ids = [row[0] for row in cr.fetchall()]
    if not ids:
        return None
    path = _layout(model)['paths'][field.name]
    missing = []
    for chunk in split_every(GROUP_CHUNK, ids):
        docs = _fetch_docs(model, list(chunk), {path: 1})
        missing += [id_ for id_ in chunk if docs.get(id_, {}).get(path) is None]
    if isinstance(init, str) and field.name in model._shadow_columns:
        # Field.update_db ran the hook on the shadow column, and queued the
        # computes it asked for, which write the documents when flushed
        column = SQL.identifier(field.name)
        cr.execute(SQL("SELECT id, %s FROM %s WHERE id = ANY(%s) AND %s IS NOT NULL",
                       column, SQL.identifier(model._table), missing, column))
        if rows := cr.fetchall():
            update(model, [row[0] for row in rows], [{field.name: row[1]} for row in rows])
        return None
    to_compute = 'default'
    if init and not isinstance(init, str) and getattr(init, '__func__', None) is not Field._init_column_related:
        to_compute = determine(init, model)   # e.g. an explicit opt-out
    value = None
    if field.default:
        value = field.default(model)
        if value is not None and to_compute == 'default':
            to_compute = False
        value = field.convert_to_column_insert(field.convert_to_write(value, model), model)
        if hasattr(value, 'adapted'):
            value = value.adapted
        if field.translate is True and value is not None:
            value = (False, value)
    if value is False and field.type == 'boolean' and not field.required:
        value = None
    if value is not None and missing:
        _logger.debug("%s: setting default value of new field %s to %r", model._name, field.name, value)
        update(model, missing, [{field.name: value}] * len(missing))
    if to_compute and field.compute and missing:
        records = model.browse(missing)
        field._init_column_notify_compute(records)
        model.env.add_to_compute(field, records)
        return records
    return None


def mirror_columns(model: BaseModel, fnames: list[str]) -> None:
    """ Copy ``fnames`` from the documents into the shadow table. This is the
    hook of SQL reports over MongoDB models: a report adds the columns its
    SQL reads to ``_shadow_columns`` (through ``_inherit``), and the columns
    added to an existing table are filled from the documents here, then kept
    up to date by every write. """
    cr = model.env.cr
    cr.execute(SQL("SELECT id FROM %s ORDER BY id", SQL.identifier(model._table)))
    records = model.sudo().with_context(active_test=False)
    paths = _layout(model)['paths']
    # translated and company-dependent columns get the whole map of the document
    maps = [fname for fname in fnames if _multi_valued(model._fields[fname])]
    for ids in split_every(1000, [row[0] for row in cr.fetchall()]):
        docs = _fetch_docs(model, ids, {paths[fname]: 1 for fname in maps}) if maps else {}
        for record in records.browse(ids):
            values = [
                SQL("%s = %s::jsonb", SQL.identifier(fname), json.dumps(
                    docs.get(record.id, {}).get(paths[fname]) or None,
                    default=lambda value: float(value.to_decimal())))
                if fname in maps else
                SQL("%s = %s", SQL.identifier(fname), model._fields[fname].convert_to_column_insert(
                    model._fields[fname].convert_to_write(record[fname], record), record))
                for fname in fnames
            ]
            cr.execute(SQL("UPDATE %s SET %s WHERE id = %s",
                           SQL.identifier(model._table), SQL(", ").join(values), record.id))
        records.invalidate_model(fnames)


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
    if bson_type == 'object' and isinstance(value, dict):    # company ids as keys
        return {str(key): val for key, val in value.items()}
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
    if field.translate and not env.context.get('prefetch_langs'):
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
# embedded child documents
# ---------------------------------------------------------------------------
# A child record is an element of its parent document's array. Searches and
# reads see it as a "virtual document": the element with ``_id`` set to the
# record id and the parent key set to the parent document's ``_id``.

def _virtual_stages(layout: dict, ids: list[int] | None = None) -> list[dict]:
    match = [] if ids is None else [{'$match': {'_id': {'$in': ids}}}]
    if not (embed := layout.get('embed')):
        return match
    array, id_path = embed['array'], embed['id_path']
    return ([] if ids is None else [{'$match': {f'{array}.{id_path}': {'$in': ids}}}]) + [
        {'$unwind': f'${array}'},
        {'$replaceRoot': {'newRoot': {'$mergeObjects': [
            f'${array}', {'_id': f'${array}.{id_path}', embed['parent_path']: '$_id'},
        ]}}},
    ] + match


def _fetch_docs(model: BaseModel, ids: list[int], projection: dict | None = None) -> dict[int, dict]:
    """ Return the (virtual) documents of ``ids``. """
    stages = _virtual_stages(_layout(model), ids) + ([{'$project': projection}] if projection else [])
    return {doc['_id']: doc for doc in get_collection(model).aggregate(stages)}


def _element(embed: dict, doc: dict) -> dict:
    """ Return the array element of the virtual document ``doc``. """
    return {embed['id_path']: doc['_id']} | {
        path: value for path, value in doc.items() if path not in ('_id', embed['parent_path'])
    }


def _elements(model: BaseModel, ids: list[int]) -> dict[int, tuple[int, int, dict]]:
    """ Return the parent id, array index and array element of child ``ids``. """
    embed = _layout(model)['embed']
    array, id_path, wanted = embed['array'], embed['id_path'], set(ids)
    return {
        element[id_path]: (doc['_id'], index, element)
        for doc in get_collection(model).find({f'{array}.{id_path}': {'$in': ids}}, {array: 1})
        for index, element in enumerate(doc[array])
        if element[id_path] in wanted
    }


def _restore_elements(collection, embed: dict, priors: dict[int, tuple[int, int, dict]]) -> None:
    """ Put child elements back in their parent at their former index. """
    array, id_path, ids = embed['array'], embed['id_path'], list(priors)
    collection.update_many({f'{array}.{id_path}': {'$in': ids}}, {'$pull': {array: {id_path: {'$in': ids}}}})
    for parent_id, index, element in sorted(priors.values(), key=lambda prior: prior[1]):
        collection.update_one({'_id': parent_id}, {'$push': {array: {'$each': [element], '$position': index}}})


def _lock_parents(model: BaseModel, parent_ids: typing.Iterable, check: bool = True) -> None:
    """ Lock the parents' shadow rows: writers of one parent's array
    serialize there, parent first. With ``check``, like the parent foreign
    key, a missing or NULL parent raises. """
    embed = _layout(model)['embed']
    parent_ids = set(parent_ids)
    if check and None in parent_ids:
        raise psycopg2.errors.NotNullViolation(f"{model._name}: {embed['parent']} is required on MongoDB storage")
    parent_ids.discard(None)
    if not parent_ids:
        return
    table = model.env[model._fields[embed['parent']].comodel_name]._table
    model.env.cr.execute(SQL("SELECT id FROM %s WHERE id = ANY(%s) ORDER BY id FOR UPDATE",
                             SQL.identifier(table), sorted(parent_ids)))
    if check and (missing := parent_ids.difference(id_ for id_, in model.env.cr.fetchall())):
        raise psycopg2.errors.ForeignKeyViolation(f"{model._name}: no {table} rows {sorted(missing)}")


def _check_key(model: BaseModel, parent_ids: typing.Iterable[int]) -> None:
    """ Enforce the spec's unique key of the children within their parent,
    like the PostgreSQL unique constraint (skipping NULLs). """
    embed = _layout(model)['embed']
    if not (key_paths := embed['key_paths']):
        return
    array = embed['array']
    for doc in get_collection(model).find({'_id': {'$in': list(parent_ids)}}, {array: 1}):
        seen = set()
        for element in doc.get(array, ()):
            key = tuple(element.get(path) for path in key_paths)
            if None in key:
                continue
            if key in seen:
                raise psycopg2.errors.UniqueViolation(f"{model._name}: duplicate key {dict(zip(key_paths, key))!r}")
            seen.add(key)


def _insert_children(model: BaseModel, ids: list[int], rows: list[dict]) -> None:
    import pymongo  # noqa: PLC0415
    embed, collection = _layout(model)['embed'], get_collection(model)
    elements = defaultdict(list)
    for id_, row in zip(ids, rows, strict=True):
        doc = _document(model, id_, row)
        elements[doc.get(embed['parent_path'])].append(_element(embed, doc))
    _lock_parents(model, elements)
    array, id_path = embed['array'], embed['id_path']
    model.env.cr.add_undo(lambda: collection.update_many(
        {'_id': {'$in': list(elements)}}, {'$pull': {array: {id_path: {'$in': ids}}}}))
    result = collection.bulk_write([
        pymongo.UpdateOne({'_id': parent_id}, {'$push': {array: {'$each': children}}})
        for parent_id, children in elements.items()
    ])
    if result.matched_count != len(elements):
        raise StorageError(f"{model._name}: parent documents missing in MongoDB for {sorted(elements)}")
    _check_key(model, elements)


def _update_children(model: BaseModel, priors: dict[int, dict], changes: list[tuple[int, dict, dict]]) -> None:
    import pymongo  # noqa: PLC0415
    embed, collection = _layout(model)['embed'], get_collection(model)
    array, id_path, parent_path = embed['array'], embed['id_path'], embed['parent_path']
    ops, parents = [], set()
    for id_, to_set, to_unset in changes:
        doc = {path: value for path, value in priors[id_].items() if path not in to_unset} | to_set
        old_parent, new_parent = priors[id_][parent_path], doc.get(parent_path)
        element = _element(embed, doc)
        if new_parent == old_parent:
            ops.append(pymongo.UpdateOne({'_id': old_parent}, {'$set': {f'{array}.$[e]': element}},
                                         array_filters=[{f'e.{id_path}': id_}]))
        else:
            ops.append(pymongo.UpdateOne({'_id': old_parent}, {'$pull': {array: {id_path: id_}}}))
            ops.append(pymongo.UpdateOne({'_id': new_parent}, {'$push': {array: element}}))
        parents.update((old_parent, new_parent))
    if not ops:
        return
    before = _elements(model, [id_ for id_, _set, _unset in changes])
    model.env.cr.add_undo(lambda: _restore_elements(collection, embed, before))
    collection.bulk_write(ops, ordered=True)
    _check_key(model, parents)


def _delete_children(model: BaseModel, ids: list[int]) -> None:
    embed, collection = _layout(model)['embed'], get_collection(model)
    if not (priors := _elements(model, ids)):
        return
    _lock_parents(model, {parent_id for parent_id, _index, _element in priors.values()}, check=False)
    model.env.cr.add_undo(lambda: _restore_elements(collection, embed, priors))
    array, id_path = embed['array'], embed['id_path']
    collection.update_many({'_id': {'$in': [prior[0] for prior in priors.values()]}},
                           {'$pull': {array: {id_path: {'$in': list(priors)}}}})


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
    if _layout(model).get('embed'):
        return _insert_children(model, ids, rows)
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
    if embed := layout.get('embed'):   # lock parents first, like the parent's own writes
        new_parents = {vals[embed['parent']] for vals in vals_list if embed['parent'] in vals}
        _lock_parents(model, {prior[0] for prior in _elements(model, ids).values()} | new_parents, check=False)
        _lock_parents(model, new_parents)
    # lock the shadow rows: concurrent writers of a document serialize there
    model.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s FOR UPDATE",
                             SQL.identifier(model._table), tuple(ids)))
    priors = _fetch_docs(model, ids)
    if not embed:
        model.env.cr.add_undo(lambda: [collection.replace_one({'_id': doc['_id']}, doc) for doc in priors.values()])
    ops, changes, fallbacks = [], [], {}
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
            if field.company_dependent and value is not None:
                if fname not in fallbacks:
                    fallbacks[fname] = json.loads(model.env['ir.default']._get_field_column_fallbacks(model._name, fname))
                old = (priors.get(id_) or {}).get(path) or {}
                value = {
                    key: val for key, val in (old | _to_bson('object', value)).items()
                    if key in fallbacks[fname] and fallbacks[fname][key] != val
                } or None
            value = _to_bson(layout['types'][fname], value)
            if value is None:
                to_unset[path] = ''
            else:
                to_set[path] = value
        if embed:
            if to_set or to_unset:
                changes.append((id_, to_set, to_unset))
            continue
        change = {}
        if to_set:
            change['$set'] = to_set
        if to_unset:
            change['$unset'] = to_unset
        if change:
            ops.append(pymongo.UpdateOne({'_id': id_}, change))
    if embed:
        _update_children(model, priors, changes)
    elif ops:
        try:
            collection.bulk_write(ops, ordered=True)
        except pymongo.errors.BulkWriteError as e:
            _raise_unique_violation(model, e)



# ---------------------------------------------------------------------------
# translation imports (the raw SQL of TranslationImporter.save)
# ---------------------------------------------------------------------------

def _translation_targets(model: BaseModel, xmlids: list[str]) -> dict[str, tuple[int, bool]]:
    """ ``{xmlid: (res_id, noupdate)}`` of the ``xmlids`` naming records of ``model``. """
    rows = model.env.execute_query(SQL(
        "SELECT module || '.' || name, res_id, noupdate FROM ir_model_data"
        " WHERE model = %s AND (module, name) IN %s",
        model._name, tuple(tuple(xmlid.split('.', 1)) for xmlid in xmlids),
    ))
    return {xmlid: (res_id, noupdate) for xmlid, res_id, noupdate in rows}


def _lock_translation_rows(model: BaseModel, ids: list[int]) -> None:
    """ Lock the shadow rows of ``ids`` in id order before their translations
    are read, so concurrent imports merge into each other's languages. """
    if not ids:
        return
    if _layout(model).get('embed'):   # parents first, like ``update``
        _lock_parents(model, {prior[0] for prior in _elements(model, ids).values()}, check=False)
    model.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s ORDER BY id FOR UPDATE",
                             SQL.identifier(model._table), tuple(ids)))


def translation_rows(model: BaseModel, fname: str, xmlids: list[str]) -> list[tuple]:
    """ The ``(id, xmlid, translations, noupdate)`` rows that
    ``TranslationImporter.save`` reads from the table, from the documents. """
    targets = _translation_targets(model, xmlids)
    _lock_translation_rows(model, [res_id for res_id, _noupdate in targets.values()])
    path = _layout(model)['paths'][fname]
    docs = _fetch_docs(model, [res_id for res_id, _noupdate in targets.values()], {path: 1})
    return [
        (res_id, xmlid, docs[res_id].get(path), noupdate)
        for xmlid, (res_id, noupdate) in targets.items()
        if res_id in docs
    ]


def import_translations(model: BaseModel, fname: str, translations: dict[str, dict], mode: str) -> None:
    """ Merge ``{xmlid: {lang: value}}`` into ``fname`` like the SQL of
    ``TranslationImporter.save``; ``mode`` is 'force', 'overwrite' or 'keep'. """
    targets = _translation_targets(model, list(translations))
    merged = {}
    for xmlid, values in translations.items():
        if xmlid in targets:
            res_id, noupdate = targets[xmlid]
            merged.setdefault(res_id, ({}, {}))[0 if noupdate else 1].update(values)
    _lock_translation_rows(model, list(merged))
    path = _layout(model)['paths'][fname]
    docs = _fetch_docs(model, list(merged), {path: 1})
    rows = []
    for res_id, (noupdate_values, update_values) in merged.items():
        old = docs.get(res_id, {}).get(path)
        if old is None:     # like NULL || jsonb in PostgreSQL
            continue
        parts = {
            'force': (old, noupdate_values, update_values),
            'overwrite': (noupdate_values, old, update_values),
            'keep': (noupdate_values, update_values, old),
        }[mode]
        rows.append((res_id, {key: val for part in parts for key, val in part.items()}))
    write_translations(model, fname, rows)


def write_translations(model: BaseModel, fname: str, rows: list[tuple[int, dict]]) -> None:
    """ Store the whole translation maps of ``rows`` (``(id, {lang: value})``) in ``fname``. """
    if not rows:
        return
    field = model._fields[fname]
    update(model, [id_ for id_, _value in rows], [
        {fname: (False, value) if field.translate is True else value}
        for _id, value in rows
    ])
    if fname in model._shadow_columns:
        for id_, value in rows:
            model.env.cr.execute(SQL(
                "UPDATE %s SET %s = %s::jsonb WHERE id = %s",
                SQL.identifier(model._table), SQL.identifier(fname), json.dumps(value), id_,
            ))

def delete(model: BaseModel, ids: typing.Iterable[int]) -> None:
    """ Delete documents; run right after the shadow rows are deleted. """
    collection = get_collection(model)
    ids = list(ids)
    if _layout(model).get('embed'):
        return _delete_children(model, ids)
    priors = list(collection.find({'_id': {'$in': ids}}))
    if priors:
        model.env.cr.add_undo(lambda: collection.insert_many(priors))
    collection.delete_many({'_id': {'$in': ids}})


# ---------------------------------------------------------------------------
# parent paths and company-dependent many2ones
# ---------------------------------------------------------------------------

def parent_store_create(model: BaseModel) -> list[tuple[int, str]]:
    """ Set the parent_path of new records from their parent's, like
    ``_parent_store_create``, and return the new paths. """
    layout = _layout(model)
    parent, parent_path = layout['paths'][model._parent_name], layout['paths']['parent_path']
    docs = _fetch_docs(model, list(model._ids), {parent: 1})
    parents = _fetch_docs(model, list({doc.get(parent) for doc in docs.values()} - {None}), {parent_path: 1})
    updated = [
        (id_, (parents.get(doc.get(parent)) or {}).get(parent_path, '') + f'{id_}/')
        for id_, doc in docs.items()
    ]
    if updated:
        update(model, [id_ for id_, _path in updated], [{'parent_path': path} for _id, path in updated])
        _write_shadow(model, 'parent_path', updated)
    return updated


def parent_store_changed(model: BaseModel, parent_to_ids: dict) -> list[int]:
    """ Return the ids whose stored parent differs from the new one. """
    parent = _layout(model)['paths'][model._parent_name]
    changed = []
    for parent_id, ids in parent_to_ids.items():
        docs = _fetch_docs(model, ids, {parent: 1})
        changed.extend(id_ for id_ in ids if id_ in docs and docs[id_].get(parent) != (parent_id or None))
    return sorted(changed)


def parent_store_update(records: BaseModel, prefix: str) -> dict[int, str]:
    """ Move ``records`` and their descendants under ``prefix``, like
    ``_parent_store_update``, and return the new paths. """
    parent_path = _layout(records)['paths']['parent_path']
    collection = get_collection(records)
    subtrees = []
    for id_, node in _fetch_docs(records, list(records._ids), {parent_path: 1}).items():
        if old := node.get(parent_path):
            subtrees.append((len(old) - len(f'{id_}/'), {parent_path: {'$gte': old, '$lt': old[:-1] + '0'}}))

    def descendants():
        return [(start, doc) for start, query in subtrees for doc in collection.find(query, {parent_path: 1})]

    # lock the descendants, then read their paths again: a concurrent move
    # committed meanwhile may have taken some of them out of the subtree
    if ids := sorted({doc['_id'] for _start, doc in descendants()}):
        records.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s ORDER BY id FOR UPDATE",
                                   SQL.identifier(records._table), tuple(ids)))
    updated = {doc['_id']: prefix + doc[parent_path][start:] for start, doc in descendants()}
    if updated:
        update(records, list(updated), [{'parent_path': path} for path in updated.values()])
        _write_shadow(records, 'parent_path', updated.items())
    return updated


def _write_shadow(model: BaseModel, fname: str, rows: typing.Iterable[tuple[int, typing.Any]]) -> None:
    """ Copy ``(id, value)`` rows written without ``_write_multi`` into the
    shadow column of ``fname``, if PostgreSQL keeps one. """
    if fname in model._shadow_columns:
        for id_, value in rows:
            model.env.cr.execute(SQL("UPDATE %s SET %s = %s WHERE id = %s",
                                     SQL.identifier(model._table), SQL.identifier(fname), value, id_))


def _company_match(model: BaseModel, field: Field, ids) -> dict:
    path = _layout(model)['paths'][field.name]
    return {'$expr': {'$anyElementTrue': [{'$map': {
        'input': {'$objectToArray': {'$ifNull': [f'${path}', {}]}},
        'in': {'$in': ['$$this.v', list(ids)]},
    }}]}}


def company_dependent_restrict(model: BaseModel, field: Field, ids) -> list[tuple[int, dict]]:
    """ Return the first record whose company-dependent ``field`` holds one of ``ids``. """
    path = _layout(model)['paths'][field.name]
    for doc in get_collection(model).find(_company_match(model, field, ids), {path: 1}).sort('_id', 1):
        if _alive(model, [doc['_id']]):
            return [(doc['_id'], doc[path])]
    return []


def company_dependent_holders(model: BaseModel, field: Field, value) -> list[int]:
    """ Return the records storing ``value`` as their own value of ``field``
    for the current company, ignoring the ``ir.default`` fallback. """
    path = _layout(model)['paths'][field.name]
    ids = [doc['_id'] for doc in get_collection(model).find({f'{path}.{model.env.company.id}': value}, {'_id': 1})]
    return sorted(_alive(model, ids))


def company_dependent_set_null(model: BaseModel, field: Field, ids) -> None:
    """ Clear the company values of ``field`` that hold one of ``ids``. """
    path, ids = _layout(model)['paths'][field.name], set(ids)
    collection = get_collection(model)
    matched = [doc['_id'] for doc in collection.find(_company_match(model, field, ids), {'_id': 1})]
    if not matched:
        return
    model.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s FOR UPDATE",
                             SQL.identifier(model._table), tuple(matched)))
    priors = list(collection.find({'_id': {'$in': matched}}))
    model.env.cr.add_undo(lambda: [collection.replace_one({'_id': doc['_id']}, doc) for doc in priors])
    for doc in priors:
        values = {key: None if value in ids else value for key, value in (doc.get(path) or {}).items()}
        collection.update_one({'_id': doc['_id']}, {'$set': {path: values}})


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
    docs = _fetch_docs(model, ids, projection)
    if missing := [id_ for id_ in ids if id_ not in docs]:
        _logger.warning("%s: shadow rows without a MongoDB document: %s", model._name, missing)
    fetched = model.browse([id_ for id_ in ids if id_ in docs])
    for field in fields:
        path = layout['paths'][field.name]
        if field.company_dependent:
            company, fallback = str(model.env.company.id), _company_fallback(model, field)
            values = [(docs[id_].get(path) or {}).get(company, fallback) for id_ in fetched._ids]
        else:
            values = [_from_bson(field, docs[id_].get(path), model.env) for id_ in fetched._ids]
        field._insert_cache(fetched, values)
    return fetched


def _search_fnames(model: BaseModel, order: str | None, *domains) -> set[str]:
    """ Return the fields of ``model`` that ``domains`` and ``order`` read,
    which a search flushes first, as PostgreSQL flushes those of its query. """
    fnames = {cond.field_expr.split('.')[0] for domain in domains for cond in domain.iter_conditions()}
    for term in (order or '').split(','):
        if term := term.strip():
            fnames.add(term.split()[0].split('.')[0].split(':')[0])
    return {fname for fname in fnames if fname in model._fields}


def _read_group_fnames(model: BaseModel, groupby, aggregates, having, order) -> set[str]:
    """ Return the fields of ``model`` that the aggregation of a grouped read
    reads, which it flushes first, as PostgreSQL flushes those of its query. """
    specs = [*groupby, *aggregates, *(leaf[0] for leaf in having if isinstance(leaf, (list, tuple)))]
    specs += [part.split()[0] for part in (order or '').split(',') if part.strip()]
    fnames = set()
    for spec in specs:
        fname = spec.split(':')[0].split('.')[0]
        if field := model._fields.get(fname):
            fnames.add(field.related.split('.')[0] if field.related and not field.store else fname)
    return fnames


def search(model: BaseModel, domain, sec_domain, order: str | None, limit, offset) -> Query:
    """ Back end of ``_search`` once ``domain`` is fully optimized. """
    model.flush_model(_search_fnames(model, order, domain, sec_domain))
    match = to_filter(model, domain)
    if not sec_domain.is_true():
        self_sudo = model.sudo().with_context(active_test=False)
        sec_domain = sec_domain.optimize_full(self_sudo, search_domain=domain)
        if sec_domain.is_false():
            return model.browse()._as_query()
        match = {'$and': [match, to_filter(self_sudo, sec_domain)]}
    pipeline = _virtual_stages(_layout(model))
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


# ---------------------------------------------------------------------------
# grouped reads
# ---------------------------------------------------------------------------

_DATE_PARTS = {
    'year_number': '$year', 'month_number': '$month', 'iso_week_number': '$isoWeek',
    'day_of_year': '$dayOfYear', 'day_of_month': '$dayOfMonth',
    'hour_number': '$hour', 'minute_number': '$minute',
}
GROUP_CHUNK = 100_000      # ids per aggregation, far below the 16 MB command limit
_MERGE = {
    '$sum': lambda a, b: a + b,
    '$min': lambda a, b: b if a is None else a if b is None else min(a, b),
    '$max': lambda a, b: b if a is None else a if b is None else max(a, b),
    '$push': lambda a, b: a + b,
    '$addToSet': lambda a, b: a + [item for item in b if item not in a],
}
_WEEKDAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')


class SpecProbe:
    """ Table given to ``_read_group_select`` to learn how a model aggregates a
    spec: the base method returns the spec unchanged, so an override that
    rewrites it (like ``value:sum`` into ``id:recordset``) reveals the rewrite. """
    def __init__(self, model: BaseModel):
        self._alias = model._table


def aggregate_spec(model: BaseModel, spec: str) -> str:
    """ Return the spec the model's ``_read_group_select`` aggregates ``spec``
    as, or ``spec`` itself when an override answers with SQL instead. """
    rewritten = model._read_group_select(SpecProbe(model), spec)
    return rewritten if isinstance(rewritten, str) else spec


def read_group(model: BaseModel, domain, groupby, aggregates, having, offset, limit, order) -> list[tuple]:
    """ Back end of ``_read_group``: return the rows PostgreSQL would return
    (raw groupby values then aggregate values), grouped by an aggregation over
    the records of ``domain``; having, order and paging apply to the groups. """
    from .models import regex_order_part_read_group  # noqa: PLC0415
    groupby, aggregates, having = list(groupby), list(aggregates), list(having or ())
    if not (groupby or aggregates):
        raise ValueError(model.env._("Need groupby or aggregates."))
    # the aggregation reads groupby and aggregated fields from the documents
    model.flush_model(_read_group_fnames(model, groupby, aggregates, having, order))
    terms = []
    for part in (order or ','.join(groupby)).split(','):
        if not part.strip():
            continue
        if not (match := regex_order_part_read_group.fullmatch(part)):
            raise ValueError(f"Invalid order {order!r} for _read_group()")
        terms.append((match['term'], (match['direction'] or 'ASC').upper(), (match['nulls'] or '').upper()))
    paths = [_related_spec(model, spec) for spec in groupby]
    sudo = {i for i, spec in enumerate(groupby) if paths[i] != spec and _spec_field(model, spec).compute_sudo}
    keys = {f'g{i}': _groupby_expr(model.sudo() if i in sudo else model, path) for i, path in enumerate(paths)}
    extra = [term for term, _dir, _nulls in terms if term not in groupby] if groupby else []
    extra += [item[0] for item in having if isinstance(item, (list, tuple))] if groupby else []
    accumulators, getters = {}, {}
    for i, spec in enumerate(dict.fromkeys(aggregates + extra)):
        accumulator, getters[spec] = _aggregate(model, spec, f'a{i}')
        accumulators.update(accumulator)

    ids = list(model._search(domain).get_result_ids())
    # aggregate the ids by chunks, and merge the partial groups
    groups = {}
    for chunk in map(list, split_every(GROUP_CHUNK, ids)):
        stages = _virtual_stages(_layout(model), chunk) + [{'$group': {'_id': keys or None, **accumulators}}]
        with get_collection(model).aggregate(stages, allowDiskUse=True) as cursor:
            for group in map(_native, cursor):
                gkey = tuple(sorted((group['_id'] or {}).items()))
                if (prior := groups.get(gkey)) is None:
                    groups[gkey] = group
                    continue
                for name, accumulator in accumulators.items():
                    (op,) = accumulator
                    prior[name] = _MERGE[op](prior[name], group[name])
    if dotted := {i: path for i, path in enumerate(paths) if '.' in path.split(':')[0]}:
        groups = _regroup(model, groups, dotted, accumulators, sudo)
    rows = []
    for group in groups.values():
        key = group['_id'] or {}
        row = {spec: _group_value(model, paths[i], key.get(f'g{i}')) for i, spec in enumerate(groupby)}
        rows.append(row | {spec: get(group) for spec, get in getters.items()})
    if not groupby:     # like SQL, an aggregate without groups returns one row
        if not ids:     # unpaged, like _read_group on an empty query
            return [(None,) * len(aggregates)]
        terms = ()
    if having and groupby:
        rows = [row for row in rows if _having(having, row) is True]
    for term, direction, nulls in reversed(terms):
        rank = _group_rank(model, term, rows, traverse_many2one=bool(order))
        valued = [row for row in rows if rank(row) is not None]
        empty = [row for row in rows if rank(row) is None]
        valued.sort(key=rank, reverse=direction == 'DESC')
        nulls_first = nulls == 'NULLS FIRST' if nulls else direction == 'DESC'   # PostgreSQL defaults
        rows = empty + valued if nulls_first else valued + empty
    rows = rows[offset or 0:]
    if limit is not None:   # LIMIT 0 returns no row
        rows = rows[:limit]
    return [tuple(row[spec] for spec in groupby + aggregates) for row in rows]


def _native(group: dict) -> dict:
    """ Turn the Decimal128 values of ``group`` into ``decimal.Decimal``,
    which Python can hash (group keys) and merge across chunks. """
    from bson.decimal128 import Decimal128  # noqa: PLC0415

    def native(value):
        return value.to_decimal() if isinstance(value, Decimal128) else value

    group = {key: native(value) for key, value in group.items()}
    if isinstance(group['_id'], dict):
        group['_id'] = {key: native(value) for key, value in group['_id'].items()}
    return group


def _spec_field(model: BaseModel, spec: str) -> Field | None:
    from .models import parse_read_group_spec  # noqa: PLC0415
    return model._fields.get(parse_read_group_spec(spec)[0])


def _related_spec(model: BaseModel, spec: str) -> str:
    """ Return the groupby ``spec`` of a non-stored related field as the path
    it follows, which is what its SQL expression joins. """
    from .models import parse_read_group_spec  # noqa: PLC0415
    fname, chain, granularity = parse_read_group_spec(spec)
    field = model._fields.get(fname)
    if not (field and field.related and not field.store):
        return spec
    model.check_field_access(field, 'read')
    path = '.'.join(filter(None, [field.related, chain]))
    return f"{path}:{granularity}" if granularity else path


def _regroup(model: BaseModel, groups: dict, dotted: dict[int, str], accumulators: dict, sudo: set[int] = frozenset()) -> dict:
    """ Replace the many2one ids of the dotted groupby specs by the raw values
    of their comodel's groupby, like the SQL join would: a multi-valued path
    puts the group in each of its values, then groups with the same key merge.
    The specs at the indexes in ``sudo`` follow a related field read as
    superuser. """
    from .models import BaseModel, parse_read_group_spec  # noqa: PLC0415
    mapping = {}
    for i, spec in dotted.items():
        fname, chain, granularity = parse_read_group_spec(spec)
        field = model._fields[fname]
        comodel = model.env[field.comodel_name].with_context(active_test=False)
        if i in sudo:
            comodel = comodel.sudo()
        elif field.compute_sudo or field.delegate:    # Many2one.join skips the comodel's rules
            comodel_hop = comodel
            for name in chain.split('.'):
                cofield = comodel_hop._fields[name]
                comodel_hop.check_field_access(cofield, 'read')
                if cofield.relational:
                    comodel_hop = model.env[cofield.comodel_name]
            comodel = comodel.sudo()
        ids = {dict(gkey).get(f'g{i}') for gkey in groups} - {None}
        cofield = comodel._fields[chain.split('.')[0]]
        values = defaultdict(list)
        for record, value in comodel._read_group([('id', 'in', list(ids))], ['id', f"{chain}:{granularity}" if granularity else chain]):
            if isinstance(value, BaseModel):
                value = value.id or None
            elif value is False and cofield.type != 'boolean':
                value = None
            values[record.id].append(value)
        mapping[i] = values
    merged = {}
    for gkey, group in groups.items():
        key = dict(gkey)
        options = [[(f'g{i}', value) for value in values.get(key.get(f'g{i}')) or [None]]
                   for i, values in mapping.items()]
        for combination in itertools.product(*options):
            new_key = key | dict(combination)
            if (prior := merged.get(gkey := tuple(sorted(new_key.items())))) is None:
                merged[gkey] = group | {'_id': new_key}
                continue
            for name, accumulator in accumulators.items():
                (op,) = accumulator
                prior[name] = _MERGE[op](prior[name], group[name])
    return merged


def _field_expr(model: BaseModel, field: Field):
    if _multi_valued(field):
        return _translated_expr(model, field.name)
    return '$' + _layout(model)['paths'][field.name]


def _groupby_expr(model: BaseModel, spec: str):
    from .models import parse_read_group_spec  # noqa: PLC0415
    fname, chain, granularity = parse_read_group_spec(spec)
    if fname not in model._fields:
        raise ValueError(f"Invalid field {fname!r} on model {model._name!r}")
    field = model._fields[fname]
    model.check_field_access(field, 'read')
    if (chain and field.type != 'many2one') or field.type in ('many2many', 'properties') \
            or not (field.store and field.column_type):
        raise NotImplementedError(f"{model._name}: cannot group by {spec!r} on MongoDB storage yet")
    expr = _field_expr(model, field)
    if chain:   # grouped by the many2one, then regrouped by the comodel's value
        return expr
    if field.type in ('date', 'datetime'):
        if not granularity:
            raise ValueError(f"Granularity not set on a date(time) field: {spec!r}")
        return _granularity_expr(model, field, expr, granularity)
    if granularity:
        raise ValueError(f"Granularity set on a no-datetime field or property: {spec!r}")
    if field.type == 'boolean':
        return {'$ifNull': [expr, False]}
    return expr


def _granularity_expr(model: BaseModel, field: Field, expr, granularity: str):
    from odoo.tools.misc import get_lang  # noqa: PLC0415
    from .utils import READ_GROUP_TIME_GRANULARITY  # noqa: PLC0415
    tz = model.env.context.get('tz')
    if field.type == 'datetime' and tz:
        if tz in date_utils.all_timezones:
            # like timezone(tz, timezone('UTC', value)): local wall time
            units = ('year', 'month', 'day', 'hour', 'minute', 'second', 'millisecond')
            expr = {'$cond': [{'$eq': [{'$ifNull': [expr, None]}, None]}, None, {'$let': {
                'vars': {'parts': {'$dateToParts': {'date': expr, 'timezone': tz}}},
                'in': {'$dateFromParts': {unit: f'$$parts.{unit}' for unit in units}},
            }}]}
        else:
            _logger.warning("Grouping in unknown / legacy timezone %r", tz)
    if granularity in READ_GROUP_TIME_GRANULARITY:
        trunc = {'date': expr, 'unit': granularity}
        if granularity == 'week':
            trunc['startOfWeek'] = _WEEKDAYS[int(get_lang(model.env).week_start) - 1]
        return {'$dateTrunc': trunc}
    if granularity == 'quarter_number':
        return {'$ceil': {'$divide': [{'$month': expr}, 3]}}
    if granularity == 'day_of_week':      # PostgreSQL dow: 0 is Sunday
        return {'$subtract': [{'$dayOfWeek': expr}, 1]}
    if granularity == 'second_number':    # with its fraction, like date_part()
        return {'$add': [{'$second': expr}, {'$divide': [{'$millisecond': expr}, 1000]}]}
    if granularity in _DATE_PARTS:
        return {_DATE_PARTS[granularity]: expr}
    raise ValueError(f"Error when processing the granularity {granularity} is not supported.")


def _plain(field: Field, value):
    from bson.decimal128 import Decimal128  # noqa: PLC0415
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, decimal.Decimal):
        return float(value)
    if field.type == 'date' and isinstance(value, dt.datetime):
        return value.date()
    return value


def _group_value(model: BaseModel, spec: str, value):
    from .models import parse_read_group_spec  # noqa: PLC0415
    from .utils import READ_GROUP_NUMBER_GRANULARITY  # noqa: PLC0415
    fname, chain, granularity = parse_read_group_spec(spec)
    if chain:   # already the comodel's raw value
        return value
    if granularity in READ_GROUP_NUMBER_GRANULARITY:   # date_part() is a double
        return None if value is None else float(value)
    return _plain(model._fields[fname], value)


_COMPUTED_AGGREGABLE = ('integer', 'float', 'monetary', 'boolean', 'date', 'datetime')


def _computed_aggregate(model: BaseModel, field: Field, func: str, key: str, group: dict):
    """ Aggregate the non-stored computed ``field`` over the records of
    ``group``, from the values its compute method gives them. """
    records = model.browse(sorted(group[key]))
    values = [None if value is False and field.type != 'boolean' else value for value in records.mapped(field.name)]
    present = [value for value in values if value is not None]
    match func:
        case 'sum':
            return sum(present) if present else None
        case 'avg':
            return sum(present) / len(present) if present else None
        case 'max' | 'min':
            return (max if func == 'max' else min)(present) if present else None
        case 'bool_and' | 'bool_or':
            return (all if func == 'bool_and' else any)(present) if present else None
        case 'count':
            return len(present)
        case 'count_distinct':
            return len(set(present))
        case 'array_agg_distinct':
            return sorted(set(values), key=lambda item: (item is None, item))
        case _:     # array_agg and recordset, ordered by id
            return values


def _aggregate(model: BaseModel, spec: str, key: str) -> tuple[dict, typing.Callable]:
    """ Return the ``$group`` accumulators of the aggregate ``spec`` and the
    function turning their result into the value PostgreSQL returns. """
    from .models import READ_GROUP_AGGREGATE, parse_read_group_spec  # noqa: PLC0415
    if spec == '__count':
        return {key: {'$sum': 1}}, lambda group: group[key]
    fname, chain, func = parse_read_group_spec(spec)
    if chain:
        raise ValueError(f"Invalid {spec!r}, this dot notation is not supported")
    if fname not in model._fields:
        raise ValueError(f"Invalid field {fname!r} on model {model._name!r} for {spec!r}.")
    if not func:
        raise ValueError(f"Aggregate method is mandatory for {fname!r}")
    field = model._fields[fname]
    model.check_field_access(field, 'read')
    if func != 'sum_currency' and func not in READ_GROUP_AGGREGATE:
        raise ValueError(f"Invalid aggregate method {func!r} for {spec!r}.")
    if func == 'recordset' and not (field.relational or fname == 'id'):
        raise ValueError(f"Aggregate method {func!r} can be only used on relational field (or id) (for {spec!r}).")
    if func != 'sum_currency' and not field.store and field.compute and field.type in _COMPUTED_AGGREGABLE:
        return {key: {'$push': '$_id'}}, functools.partial(_computed_aggregate, model, field, func, key)
    if func == 'sum_currency' or field.type == 'many2many' or not (field.store and field.column_type):
        raise NotImplementedError(f"{model._name}: cannot aggregate {spec!r} on MongoDB storage yet")
    expr = _field_expr(model, field)
    value = {'$ifNull': [expr, None]}
    present = {'$sum': {'$cond': [{'$eq': [value, None]}, 0, 1]}}
    match func:
        case 'sum' | 'max' | 'min':     # NULL when no value, like SQL
            return ({key: {f'${func}': expr}, f'{key}_n': present},
                    lambda group: _plain(field, group[key]) if group[f'{key}_n'] else None)
        case 'avg':     # sum / count, so that partial groups merge
            return ({key: {'$sum': expr}, f'{key}_n': present},
                    lambda group: _plain(field, group[key]) / group[f'{key}_n'] if group[f'{key}_n'] else None)
        case 'bool_and' | 'bool_or':
            return {key: {'$min' if func == 'bool_and' else '$max': expr}}, lambda group: group[key]
        case 'count':
            return {key: present}, lambda group: group[key]
        case 'count_distinct':
            return {key: {'$addToSet': expr}}, lambda group: sum(item is not None for item in group[key])
        case 'array_agg_distinct':
            return {key: {'$addToSet': value}}, lambda group: sorted(
                (_plain(field, item) for item in group[key]), key=lambda item: (item is None, item))
        case _:     # array_agg and recordset, ordered by id
            return {key: {'$push': {'id': '$_id', 'value': value}}}, lambda group: [
                _plain(field, item['value']) for item in sorted(group[key], key=lambda item: item['id'])]


def _having(having: list, row: dict) -> bool | None:
    """ Evaluate a having domain on ``row`` with SQL's three-valued logic. """
    import operator  # noqa: PLC0415
    comparators = {
        '=': operator.eq, '!=': operator.ne, '<': operator.lt, '>': operator.gt,
        '<=': operator.le, '>=': operator.ge,
        'in': lambda a, b: a in b, 'not in': lambda a, b: a not in b,
    }
    stack = []
    for item in reversed(having):
        if item == '!':
            value = stack.pop()
            stack.append(None if value is None else not value)
        elif item in ('&', '|'):
            values = (stack.pop(), stack.pop())
            decisive = item == '|'
            stack.append(decisive if decisive in values else None if None in values else not decisive)
        elif isinstance(item, (list, tuple)) and len(item) == 3:
            left, op, right = item
            if op not in comparators:
                raise ValueError(f"Invalid having clause {item!r}: supported comparators are {tuple(comparators)}")
            stack.append(None if row[left] is None else comparators[op](row[left], right))
        else:
            raise ValueError(f"Invalid having clause {item!r}: it should be a domain-like clause")
    result = True
    for value in stack:     # implicit AND
        result = False if False in (result, value) else None if None in (result, value) else True
    return result


def _group_rank(model: BaseModel, term: str, rows: list[dict], traverse_many2one: bool) -> typing.Callable:
    """ Return the sort key of the order ``term`` over grouped ``rows``, as
    ``_read_group_orderby`` orders them; None sorts as NULL. """
    from odoo.tools.misc import get_lang  # noqa: PLC0415
    from .models import parse_read_group_spec  # noqa: PLC0415
    fname, _chain, granularity = parse_read_group_spec(term)
    field = model._fields.get(term)
    if field and field.type == 'many2one' and traverse_many2one:
        comodel = model.env[field.comodel_name]
        if comodel._order != 'id':
            ids = {row[term] for row in rows} - {None}
            ordered = comodel.sudo().with_context(active_test=False).search([('id', 'in', list(ids))], order=comodel._order)
            ranks = {id_: index for index, id_ in enumerate(ordered._ids)}
            return lambda row: ranks.get(row[term], len(ranks)) if row[term] is not None else None
    if field and field.type == 'selection':
        keys = list(field.get_values(model.env))
        return lambda row: keys.index(row[term]) if row[term] in keys else None
    if granularity == 'day_of_week':
        first_week_day = int(get_lang(model.env).week_start)
        return lambda row: None if row[term] is None else (7 - first_week_day + int(row[term])) % 7
    return lambda row: row[term]


def _alive(model: BaseModel, ids: list[int]) -> set[int]:
    alive = set()
    for sub_ids in split_every(IN_MAX, ids):
        model.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s", SQL.identifier(model._table), tuple(sub_ids)))
        alive.update(id_ for id_, in model.env.cr.fetchall())
    return alive


def _translated_fields(model, domain, sec_domain, order) -> list[str]:
    names = {cond.field_expr for dom in (domain, sec_domain) for cond in dom.iter_conditions()}
    names.update(part.split()[0] for part in (order or '').split(',') if part.strip())
    paths = _layout(model)['paths']
    return sorted(n for n in names if n in paths and n in model._fields and _multi_valued(model._fields[n]))


def _multi_valued(field: Field) -> bool:
    """ Whether the field stores one value per language or per company. """
    return bool(field.translate) or field.company_dependent


def _company_fallback(model: BaseModel, field: Field):
    fallback = field.get_company_dependent_fallback(model)
    return field.convert_to_column(field.convert_to_write(fallback, model), model)


def _translated_expr(model: BaseModel, fname: str) -> dict:
    """ Return the value of a translated field in the current language, or
    of a company-dependent field in the current company. """
    from .fields_textual import StoredTranslations  # noqa: PLC0415
    field, path = model._fields[fname], _layout(model)['paths'][fname]
    if field.company_dependent:     # like COALESCE(column->company, fallback)
        value = f'${path}.{model.env.company.id}'
        return {'$cond': [{'$eq': [{'$type': value}, 'missing']}, _company_fallback(model, field), value]}
    langs = StoredTranslations.fallback_langs(field.translation_lang(model.env))
    return {'$ifNull': [f'${path}.{lang}' for lang in langs] + [None]}


def _path(model: BaseModel, field: Field) -> str:
    if _multi_valued(field):
        return TRANSLATED_PREFIX + field.name
    return _layout(model)['paths'][field.name]


def _outside_order(model: BaseModel, field: Field, part: str) -> tuple[str, list[int], list[int]]:
    """ Rank an order term on a field the document doesn't hold: the parent
    model orders an inherited field, PostgreSQL orders the others over the
    shadow rows (computed SQL). Return the path, the ids and their ranks. """
    from .query import Query  # noqa: PLC0415
    records = model.sudo().with_context(active_test=False)
    if field.inherited:
        parent_field = model._fields[field.related.split('.')[0]]
        parent_ids = records.env[parent_field.comodel_name].search([], order=part)._ids
        return '$' + _path(model, parent_field), list(parent_ids), list(range(len(parent_ids)))
    # equal values share a rank, so that the next order terms break the ties
    query = Query(records)
    rows = records.env.execute_query(query.select(
        query.table.id, SQL("DENSE_RANK() OVER (ORDER BY %s)", records._order_to_sql(query.table, part)),
    ))
    return '$_id', [id_ for id_, _rank in rows], [rank for _id, rank in rows]


def _sort_stages(model: BaseModel, order: str | None) -> list[dict]:
    from .models import regex_order  # noqa: PLC0415
    if not order:
        return []
    ranks, flags, sort = {}, {}, {}
    for i, part in enumerate(order.split(',')):
        match = regex_order.match(part)
        if not match:
            raise ValueError(f"Invalid order {order!r}")
        fname, direction, nulls = match['field'], (match['direction'] or 'ASC').upper(), (match['nulls'] or '').upper()
        field = model._fields.get(fname)
        many2one = field is not None and field.type == 'many2one'
        if field is None or field.type in ('one2many', 'many2many') or match['property'] not in (None, *(['id'] if many2one else [])):
            raise NotImplementedError(f"{model._name}: cannot order by {part.strip()!r} on MongoDB storage")
        if field.name != 'id' and field.name not in _layout(model)['paths']:
            if not (field.inherited or field.compute_sql):
                raise NotImplementedError(f"{model._name}: cannot order by {part.strip()!r} on MongoDB storage")
            path, ids, positions = _outside_order(model, field, part.strip())
            ranks[f'__rank{i}'] = {'$let': {'vars': {'at': {'$indexOfArray': [ids, path]}},
                                            'in': {'$cond': [{'$gte': ['$$at', 0]},
                                                             {'$arrayElemAt': [positions, '$$at']}, -1]}}}
            sort[f'__rank{i}'] = 1
            continue
        path = _path(model, field)
        comodel = model.env[field.comodel_name] if many2one else None
        if many2one and not match['property'] and comodel._order != 'id':
            seen = model.env.context.get('__m2o_order_seen', ())
            if field in seen:   # a cycle of many2one orders adds no term, as in PostgreSQL
                continue
            # rank by the comodel's order, wherever the comodel is stored
            coids = list(comodel.sudo().with_context(
                active_test=False, __m2o_order_seen=frozenset((field, *seen)),
            ).search([], order=comodel._order)._ids)
            ranks[f'__rank{i}'] = {'$let': {'vars': {'rank': {'$indexOfArray': [coids, f'${path}']}},
                                            'in': {'$cond': [{'$gte': ['$$rank', 0]}, '$$rank', None]}}}
            path = f'__rank{i}'
        step = 1 if direction == 'ASC' else -1
        # PostgreSQL puts NULLs last ascending and first descending
        nulls_last = nulls == 'NULLS LAST' if nulls else step == 1
        flags[f'__null{i}'] = {'$cond': [{'$eq': [{'$ifNull': [f'${path}', None]}, None]}, 1, 0]}
        sort[f'__null{i}'] = 1 if nulls_last else -1
        sort[path] = step
    sort.setdefault('_id', 1)
    return ([{'$addFields': ranks}] if ranks else []) + [{'$addFields': flags}, {'$sort': sort}]


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
    if isinstance(domain, DomainCustom):
        # raw SQL: PostgreSQL evaluates it over the shadow rows
        from .query import Query  # noqa: PLC0415
        query = Query(model)
        query.add_where(domain._to_sql(query.table))
        return {'_id': {'$in': list(query.get_result_ids())}}
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
        elif isinstance(value, SQL):   # a subquery of comodel ids, as PostgreSQL runs it
            rows = [id_ for id_, in model.env.execute_query(value)]
            ids = [id_ for id_ in rows if id_ is not None]
            if len(ids) < len(rows) and operator.startswith('not') and not inverse:
                # NOT IN over a NULL is never true; only an empty many2one still matches
                return {'_id': {'$in': []}} if field.name == 'id' else {_path(model, field): None}
        else:
            raise unsupported
        if inverse:
            ids = comodel.sudo().browse(ids)[inverse]._ids
        path = '_id' if inverse or field.name == 'id' else _path(model, field)
        return {path: {'$nin' if operator.startswith('not') else '$in': list(ids)}}

    if field.compute_sql and not field.store:
        # computed in SQL: PostgreSQL evaluates it over the shadow rows
        query = Query(model)
        query.add_where(cond._to_sql(query.table))
        return {'_id': {'$in': list(query.get_result_ids())}}
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
        # like PostgreSQL: NULL and the field's falsy value match each other
        if (falsy := field.falsy_value) is not None:
            if None in values:
                values.append(to_value(falsy))
            elif to_value(falsy) in values:
                values.append(None)
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

    if operator.endswith('like') and (bson_type == 'string' or _multi_valued(field)):
        pattern = str(value) if '=' in operator else f'%{value}%'
        regex = _like_regex(pattern, operator.endswith('ilike'))
        return {path: {'$not': regex}} if operator.startswith('not') else {path: regex}

    raise unsupported


def _many2many_condition(model: BaseModel, field: Field, operator: str, value, unsupported) -> dict:
    from .domains import Domain  # noqa: PLC0415
    from .query import Query  # noqa: PLC0415
    if (layout := relation_layout(field, model.env)) is None:
        # the relation table stays in PostgreSQL: match the shadow rows there
        query = Query(model)
        query.add_where(field.condition_to_sql(query.table, field.name, operator, value))
        return {'_id': {'$in': list(query.get_result_ids())}}
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
