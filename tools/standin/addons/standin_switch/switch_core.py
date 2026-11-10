"""Per-request source | reads | writes switch: config, audit log, MongoDB handle.

Config is a JSON file (STANDIN_SWITCH_CONFIG, else the committed tools/standin/switch.json)
re-read whenever it changes, so a flip applies from the next request. Every routing decision
and every flip appends one JSON line to the audit log.
"""
import json
import os
import socket
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

positions = ("source", "reads", "writes")
databaseName = "odoo_unt16"
committedConfig = Path(__file__).resolve().parents[2] / "switch.json"

_lock = threading.Lock()
_cache = {"path": None, "mtime": None, "config": None}
_mongo = {"client": None}


def configPath():
    return Path(os.environ.get("STANDIN_SWITCH_CONFIG") or committedConfig).expanduser()


def validate(config):
    for sliceName, slice_ in config["slices"].items():
        if slice_["position"] not in positions:
            raise ValueError(f"slice {sliceName}: position {slice_['position']!r} not in {positions}")
    return config


def loadConfig():
    path = configPath()
    mtime = path.stat().st_mtime_ns
    with _lock:
        if _cache["path"] != path or _cache["mtime"] != mtime:
            _cache.update(path=path, mtime=mtime, config=validate(json.loads(path.read_text())))
        return _cache["config"]


def auditPath(config=None):
    config = config or loadConfig()
    return Path(config.get("audit_log", "~/standin-run/switch_audit.log")).expanduser()


def audit(event, config=None, **fields):
    line = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "event": event, "host": socket.gethostname(), "pid": os.getpid(), **fields}
    path = auditPath(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock, open(path, "a") as fh:
        fh.write(json.dumps(line, default=str, sort_keys=True) + "\n")
    return line


def sliceForModel(config, modelName):
    for sliceName, slice_ in config["slices"].items():
        if slice_["model"] == modelName:
            return sliceName, slice_
    return None, None


def newRequestId():
    return uuid.uuid4().hex[:12]


def mongoDatabase(config=None):
    config = config or loadConfig()
    if _mongo["client"] is None:
        from pymongo import MongoClient
        uriEnv = config.get("mongo_uri_env", "STANDIN_MONGO_URI")
        uri = os.environ.get(uriEnv) or "mongodb://localhost:27017"
        _mongo["client"] = MongoClient(uri, serverSelectionTimeoutMS=5000, tz_aware=True)
    return _mongo["client"][databaseName]
