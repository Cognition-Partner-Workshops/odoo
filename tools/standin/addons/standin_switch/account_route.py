"""Route account.account RPC reads and writes per request: source | reads | writes.

Only the outermost call of an HTTP request routes (nested ORM calls stay on PostgreSQL),
and every routed call writes one audit line. Position -> where each kind of call goes:
source: reads PG, writes PG; reads: reads MongoDB, writes PG (CDC carries them);
writes: reads MongoDB, writes MongoDB.
"""
import contextvars
import re
from datetime import datetime, timezone

from odoo import fields as odooFields
from odoo.exceptions import MissingError, UserError
from odoo.http import request_var

from . import slice_docs, switch_core

readOps = ("read", "search_read", "name_search")
writeOps = ("create", "write", "action_archive")
_inRoute = contextvars.ContextVar("standinInRoute", default=False)
_entries = {}


def entryFor(collectionName):
    if collectionName not in _entries:
        _entries[collectionName] = slice_docs.loadEntry(collectionName)
    return _entries[collectionName]


def currentRequest():
    req = request_var.get(None)
    if req is None:
        return None
    if not hasattr(req, "standinRequestId"):
        header = req.httprequest.headers.get("X-Standin-Request")
        req.standinRequestId = header or switch_core.newRequestId()
    return req


def target(position, op):
    if position == "source" or (position == "reads" and op in writeOps):
        return "source"
    return "mongo"


def routed(op, original):
    def wrapper(self, *args, **kwargs):
        req = currentRequest()
        if req is None or _inRoute.get():
            return original(self, *args, **kwargs)
        config = switch_core.loadConfig()
        sliceName, slice_ = switch_core.sliceForModel(config, self._name)
        position = slice_["position"] if slice_ else config.get("default", "source")
        route = target(position, op)
        token = _inRoute.set(True)
        try:
            if route == "source":
                result = original(self, *args, **kwargs)
            else:
                result = MongoSlice(self, sliceName, slice_, config).call(op, *args, **kwargs)
        except Exception as exc:
            switch_core.audit("route", config, request_id=req.standinRequestId, path=req.httprequest.path,
                              slice=sliceName, model=self._name, op=op, position=position, route=route,
                              error=type(exc).__name__)
            raise
        finally:
            _inRoute.reset(token)
        switch_core.audit("route", config, request_id=req.standinRequestId, path=req.httprequest.path,
                          slice=sliceName, model=self._name, op=op, position=position, route=route,
                          result=summary(result))
        return result
    wrapper.__name__ = op
    wrapper.__dict__.update(getattr(original, "__dict__", {}))
    return wrapper


def summary(result):
    if hasattr(result, "_ids"):
        return {"ids": list(result._ids)}
    if isinstance(result, list):
        ids = [r["id"] if isinstance(r, dict) else r[0] for r in result if isinstance(r, (dict, tuple, list))]
        return {"rows": len(result), "ids": ids[:20]}
    return result if result is None or isinstance(result, bool) else type(result).__name__


class MongoSlice:
    """The slice's collection seen through the mapping_spec entry."""

    def __init__(self, records, sliceName, slice_, config):
        self.records = records
        self.env = records.env
        self.entry = entryFor(slice_["collection"])
        self.coll = switch_core.mongoDatabase(config)[self.entry["collection"]]
        self.lang = self.env.lang or "en_US"
        self.companyKey = str(self.env.company.root_id.id)
        self.scalars = {f["source"]: f for f in self.entry["fields"]}
        self.embeds = {}
        for fname, field in records._fields.items():
            if field.type == "many2many":
                for embed in self.entry.get("embeds", []):
                    if embed["child_table"] == field.relation:
                        self.embeds[fname] = (embed["array_path"], embed["child_fields"][0]["target"])

    def call(self, op, *args, **kwargs):
        return getattr(self, op)(*args, **kwargs)

    # ---- paths and values
    def path(self, fname):
        if fname == "id":
            return "_id"
        if fname == "code":
            return f"codeStore.{self.companyKey}"
        if fname in self.embeds:
            arrayPath, leaf = self.embeds[fname]
            return f"{arrayPath}.{leaf}"
        if fname in self.scalars:
            spec = self.scalars[fname]
            translated = getattr(self.records._fields.get(fname), "translate", False)
            return f"{spec['target']}.{self.lang}" if translated else spec["target"]
        raise UserError(f"standin switch: {self.records._name}.{fname} is not in the {self.entry['collection']} mapping")

    def translatedValue(self, value):
        if isinstance(value, dict):
            return value.get(self.lang) or value.get("en_US") or next(iter(value.values()), False)
        return value or False

    def fieldValue(self, doc, fname):
        if fname == "id":
            return doc["_id"]
        if fname == "code":
            store = doc.get("codeStore") or {}
            return store.get(self.companyKey) or next(iter(store.values()), False)
        if fname == "display_name":
            code, name = self.fieldValue(doc, "code"), self.fieldValue(doc, "name")
            return f"{code} {name}" if code else name
        if fname in self.embeds:
            arrayPath, leaf = self.embeds[fname]
            return [elem[leaf] for elem in doc.get(arrayPath) or []]
        if fname not in self.scalars:
            raise UserError(f"standin switch: {self.records._name}.{fname} is not in the {self.entry['collection']} mapping")
        value = doc.get(self.scalars[fname]["target"])
        if self.scalars[fname]["bson_type"] == "object":
            return self.translatedValue(value)
        if isinstance(value, datetime):
            return odooFields.Datetime.to_string(value.astimezone(timezone.utc).replace(tzinfo=None))
        return False if value is None else value

    def defaultFields(self):
        return ["id", "display_name", "code"] + [f for f in self.scalars if f in self.records._fields] + list(self.embeds)

    # ---- domains
    def leaf(self, fname, operator, value):
        if fname == "display_name":
            return {"$or": [self.leaf("code", operator, value), self.leaf("name", operator, value)]}
        path = self.path(fname)
        if value is False and operator in ("=", "!="):
            return {path: None} if operator == "=" else {path: {"$ne": None}}
        if operator == "=":
            return {path: value}
        simple = {"!=": "$ne", "in": "$in", "not in": "$nin", "<": "$lt", ">": "$gt", "<=": "$lte", ">=": "$gte"}
        if operator in simple:
            return {path: {simple[operator]: list(value) if operator in ("in", "not in") else value}}
        if operator in ("ilike", "like", "not ilike", "not like", "=ilike", "=like"):
            if operator.startswith("="):
                pattern = "^" + re.escape(value).replace("%", ".*").replace("_", ".") + "$"
            else:
                pattern = re.escape(value)
            regex = {"$regex": pattern, "$options": "i" if "ilike" in operator else ""}
            return {path: {"$not": re.compile(pattern, re.I if "ilike" in operator else 0)}} if operator.startswith("not") else {path: regex}
        raise UserError(f"standin switch: operator {operator!r} is not supported on the MongoDB route")

    def filter(self, domain):
        items = [tuple(x) if isinstance(x, list) else x for x in (domain or [])]
        mentionsActive = any(isinstance(x, tuple) and x[0] == "active" for x in items)

        def parse(pos):
            item = items[pos]
            if item == "!":
                sub, nxt = parse(pos + 1)
                return {"$nor": [sub]}, nxt
            if item in ("&", "|"):
                left, nxt = parse(pos + 1)
                right, nxt = parse(nxt)
                return {"$and" if item == "&" else "$or": [left, right]}, nxt
            return self.leaf(*item), pos + 1

        clauses, pos = [], 0
        while pos < len(items):
            clause, pos = parse(pos)
            clauses.append(clause)
        if not mentionsActive and self.env.context.get("active_test", True):
            clauses.append({"active": True})
        if "company_ids" in self.embeds and not self.env.su:
            clauses.append({self.path("company_ids"): {"$in": self.env.companies.ids}})
        return {"$and": clauses} if clauses else {}

    def sort(self, order):
        keys = []
        for part in (order or "code").split(","):
            bits = part.strip().split()
            if bits:
                keys.append((self.path(bits[0]), -1 if len(bits) > 1 and bits[1].lower() == "desc" else 1))
        return keys + [("_id", 1)]

    # ---- reads
    def rows(self, docs, fieldNames):
        names = list(fieldNames or self.defaultFields())
        if "id" not in names:
            names.insert(0, "id")
        return [{f: self.fieldValue(doc, f) for f in names} for doc in docs]

    def read(self, fields=None, load="_classic_read"):
        ids = list(self.records._ids)
        docs = {d["_id"]: d for d in self.coll.find({"_id": {"$in": ids}})}
        missing = [i for i in ids if i not in docs]
        if missing:
            raise MissingError(f"standin switch: {self.entry['collection']} has no documents {missing}")
        return self.rows([docs[i] for i in ids], fields)

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kwargs):
        cursor = self.coll.find(self.filter(domain)).sort(self.sort(order)).skip(offset or 0)
        if limit:
            cursor = cursor.limit(limit)
        return self.rows(cursor, fields)

    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        full = list(domain or [])
        if name:
            full = ["&", ("display_name", operator, name)] + (full or [("id", "!=", False)])
        cursor = self.coll.find(self.filter(full)).sort(self.sort(None)).limit(limit or 0)
        return [(doc["_id"], self.fieldValue(doc, "display_name")) for doc in cursor]

    # ---- writes (position writes only)
    def setters(self, vals):
        sets, adds, pulls = {}, {}, {}
        for fname, value in vals.items():
            if fname in self.embeds:
                arrayPath, leaf = self.embeds[fname]
                for command in value if value and isinstance(value[0], (list, tuple)) else [(6, 0, value or [])]:
                    if command[0] == 6:
                        sets[arrayPath] = [{leaf: int(i)} for i in command[2]]
                    elif command[0] == 4:
                        adds.setdefault(arrayPath, []).append({leaf: int(command[1])})
                    elif command[0] == 3:
                        pulls.setdefault(arrayPath, []).append(int(command[1]))
                    else:
                        raise UserError(f"standin switch: x2many command {command[0]} is not supported on {fname}")
                continue
            field = self.records._fields.get(fname)
            path = self.path(fname)
            if field is not None and field.type == "many2one" and value:
                value = int(value)
            sets[path] = value if value is not False or (field and field.type == "boolean") else None
        stamp = datetime.now(timezone.utc).replace(microsecond=0)
        sets |= {"writeDate": stamp, "writeUid": self.env.uid}
        return sets, adds, pulls

    def nextId(self):
        self.env.cr.execute("SELECT COALESCE(max(id), 0) FROM account_account")
        sourceMax = self.env.cr.fetchone()[0]
        top = next(iter(self.coll.find({}, {"_id": 1}).sort("_id", -1).limit(1)), {"_id": 0})["_id"]
        return max(sourceMax, top) + 1

    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        ids = []
        for vals in vals_list:
            if not vals.get("name") or not vals.get("code"):
                raise UserError("standin switch: create needs name and code")
            newId = self.nextId()
            doc = {"_id": newId, **{f["target"]: None for f in self.entry["fields"]},
                   **{e["array_path"]: [] for e in self.entry.get("embeds", [])}}
            doc |= {"active": True, "reconcile": False, "nonTrade": False,
                    "accountType": vals.get("account_type") or "asset_current",
                    "createDate": datetime.now(timezone.utc).replace(microsecond=0), "createUid": self.env.uid}
            if "company_ids" not in vals:
                vals = {**vals, "company_ids": [(6, 0, [self.env.company.root_id.id])]}
            sets, adds, _pulls = self.setters(vals)
            for dotted, value in sets.items():
                head, _, tail = dotted.partition(".")
                if tail:
                    doc[head] = {**(doc.get(head) or {}), tail: value}
                else:
                    doc[head] = value
            for arrayPath, elems in adds.items():
                doc[arrayPath] = doc.get(arrayPath, []) + elems
            self.coll.insert_one(doc)
            ids.append(newId)
        return self.records.browse(ids)

    def write(self, vals):
        sets, adds, pulls = self.setters(vals)
        change = {"$set": sets}
        if adds:
            change["$addToSet"] = {path: {"$each": elems} for path, elems in adds.items()}
        if pulls:
            arrayLeaf = {self.embeds[f][0]: self.embeds[f][1] for f in self.embeds}
            change["$pull"] = {path: {arrayLeaf[path]: {"$in": ids}} for path, ids in pulls.items()}
        found = self.coll.update_many({"_id": {"$in": list(self.records._ids)}}, change).matched_count
        if found != len(self.records._ids):
            raise MissingError(f"standin switch: {self.entry['collection']} matched {found} of {len(self.records._ids)}")
        return True

    def action_archive(self):
        return self.write({"active": False})


def install(modelClass):
    for op in readOps + writeOps:
        own = modelClass.__dict__.get(op)
        if own is not None:
            original = own
        else:
            def original(self, *args, _op=op, **kwargs):
                return getattr(super(modelClass, self), _op)(*args, **kwargs)
            original.__dict__.update(getattr(modelClass, op).__dict__)
        setattr(modelClass, op, routed(op, original))
