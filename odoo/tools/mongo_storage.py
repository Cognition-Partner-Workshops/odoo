# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Per-request storage switch for units migrated to MongoDB.

The switch is a JSON file named by the ``mongo_storage_switch`` config option
(or the ``ODOO_MONGO_STORAGE_SWITCH`` environment variable). It is re-read
whenever it changes, so a mode flip takes effect on the next request without
a restart::

    {"database": "odoo_unt16", "uri_env": "MONGO_LOCAL_URI",
     "units": {"ormSignalingAssets": "reads"},
     "cdc_checkpoints": {"ormSignalingAssets": "0/16B3748"}}

Modes per unit: ``source`` (default: PostgreSQL only), ``reads`` (read-only
requests read MongoDB once its CDC checkpoint has passed this process's last
source write for the unit; otherwise PostgreSQL), ``writes`` (MongoDB is the
store; writes are applied after the PostgreSQL commit of the request).
"""
import json
import logging
import os
import threading

from .config import config

_logger = logging.getLogger(__name__)

SOURCE, READS, WRITES = 'source', 'reads', 'writes'
MODES = (SOURCE, READS, WRITES)

_lock = threading.RLock()
_switch = {'path': None, 'mtime': None, 'data': {}}
_clients = {}
_last_source_write = {}


def _switch_path():
    return config.get('mongo_storage_switch') or os.environ.get('ODOO_MONGO_STORAGE_SWITCH')


def _load_switch():
    path = _switch_path()
    if not path:
        return {}
    try:
        mtime = os.stat(path).st_mtime_ns
    except OSError:
        _logger.warning("mongo storage switch %s is unreadable, using source", path)
        return {}
    with _lock:
        if _switch['path'] != path or _switch['mtime'] != mtime:
            try:
                with open(path, encoding='utf-8') as stream:
                    data = json.load(stream)
            except (OSError, ValueError):
                _logger.warning("mongo storage switch %s is invalid, using source", path)
                data = {}
            _switch.update(path=path, mtime=mtime, data=data)
        return _switch['data']


def unit_mode(unit):
    """Return the current mode of ``unit``; anything unknown is ``source``."""
    mode = _load_switch().get('units', {}).get(unit, SOURCE)
    return mode if mode in MODES else SOURCE


def _parse_lsn(lsn):
    high, low = str(lsn).split('/')
    return (int(high, 16) << 32) + int(low, 16)


def record_source_write(cr, unit):
    """Remember the source WAL position of a write to ``unit`` (``reads`` mode)."""
    cr.execute("SELECT pg_current_wal_lsn()::text")
    _last_source_write[unit] = cr.fetchone()[0]


def reads_target(unit):
    """Whether a read of ``unit`` goes to MongoDB in the current mode."""
    mode = unit_mode(unit)
    if mode == WRITES:
        return True
    if mode != READS:
        return False
    checkpoint = _load_switch().get('cdc_checkpoints', {}).get(unit)
    written = _last_source_write.get(unit)
    if checkpoint is None:
        return False
    try:
        return written is None or _parse_lsn(checkpoint) >= _parse_lsn(written)
    except ValueError:
        return False


def collection(name):
    """Return the MongoDB collection ``name`` of the switch's target database."""
    import pymongo  # noqa: PLC0415

    data = _load_switch()
    uri_env = data.get('uri_env', 'MONGO_LOCAL_URI')
    database = data.get('database', 'odoo_unt16')
    uri = os.environ.get(uri_env)
    if not uri:
        raise RuntimeError(f"mongo storage switch: environment variable {uri_env} is not set")
    with _lock:
        client = _clients.get(uri_env)
        if client is None:
            client = _clients[uri_env] = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client[database][name]


def _utcnow_ms():
    import datetime  # noqa: PLC0415

    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


def signal_max_id(unit):
    """``max(id)`` of a signaling unit's collection, ``None`` when empty."""
    last = collection(unit).find_one({}, sort=[('_id', -1)], projection={'_id': 1})
    return last['_id'] if last else None


def signal_append(unit, attempts=10):
    """Append one signal (``INSERT ... DEFAULT VALUES``) and return its id."""
    from pymongo.errors import DuplicateKeyError  # noqa: PLC0415

    target = collection(unit)
    for _attempt in range(attempts):
        next_id = (signal_max_id(unit) or 0) + 1
        try:
            target.insert_one({'_id': next_id, 'date': _utcnow_ms()})
            return next_id
        except DuplicateKeyError:
            continue
    raise RuntimeError(f"could not allocate a signal id in {unit}")


def signal_prune(unit, keep=10, hours=1):
    """Same retention as ``ir.autovacuum._gc_orm_signaling``."""
    import datetime  # noqa: PLC0415

    last = signal_max_id(unit)
    if last is None:
        return 0
    cutoff = _utcnow_ms() - datetime.timedelta(hours=hours)
    return collection(unit).delete_many(
        {'_id': {'$lt': last - (keep - 1)}, 'date': {'$lt': cutoff}}).deleted_count
