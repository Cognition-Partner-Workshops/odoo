#!/usr/bin/env python3
"""Scripted account.account traffic against the stand-in Odoo, through the ORM over JSON-RPC.

Each cycle: search_read, read, name_search, create, write, action_archive. Every call is its own
HTTP request with an X-Standin-Request id, so audit lines join back to driver output.

Usage: driver.py [--url http://localhost:8070] [--db odoo_unt16_prod] [--cycles 1] [--sleep 0]
The Odoo password is read from the env var named by --password-env (default STANDIN_ODOO_PASSWORD,
falling back to the demo database's admin password).
"""
import argparse
import json
import os
import time
import uuid

import requests


class Client:
    def __init__(self, url, db, login, password):
        self.url, self.session = url.rstrip("/"), requests.Session()
        self.post("/web/session/authenticate", {"db": db, "login": login, "password": password})

    def post(self, path, params, requestId=None):
        headers = {"X-Standin-Request": requestId} if requestId else {}
        body = {"jsonrpc": "2.0", "method": "call", "id": 1, "params": params}
        reply = self.session.post(self.url + path, json=body, headers=headers, timeout=60).json()
        if reply.get("error"):
            raise RuntimeError(json.dumps(reply["error"].get("data", {}).get("message") or reply["error"]))
        return reply["result"]

    def call(self, method, args, kwargs=None, tag=""):
        requestId = f"drv-{tag}-{uuid.uuid4().hex[:6]}"
        result = self.post(f"/web/dataset/call_kw/account.account/{method}",
                           {"model": "account.account", "method": method, "args": args, "kwargs": kwargs or {}},
                           requestId)
        print(json.dumps({"request_id": requestId, "method": method, "result": result}, default=str)[:400])
        return result


def cycle(client, n):
    tag = f"c{n}"
    rows = client.call("search_read", [[["account_type", "=", "asset_current"]]],
                       {"fields": ["id", "code", "name", "account_type", "active"], "limit": 5}, tag)
    if rows:
        client.call("read", [[rows[0]["id"]], ["code", "name", "company_ids"]], tag=tag)
    client.call("name_search", [], {"name": "Bank", "limit": 5}, tag)
    stamp = time.strftime("%H%M%S")
    newId = client.call("create", [[{"name": f"Stand-in driver {stamp}-{n}", "code": f"9{stamp}{n % 10}",
                                     "account_type": "asset_current"}]], tag=tag)
    newId = newId[0] if isinstance(newId, list) else newId
    client.call("write", [[newId], {"name": f"Stand-in driver {stamp}-{n} (edited)", "reconcile": True}], tag=tag)
    client.call("action_archive", [[newId]], tag=tag)
    return newId


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8070")
    parser.add_argument("--db", default="odoo_unt16_prod")
    parser.add_argument("--login", default="admin")
    parser.add_argument("--password-env", default="STANDIN_ODOO_PASSWORD")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=0)
    args = parser.parse_args()
    client = Client(args.url, args.db, args.login, os.environ.get(args.password_env, "admin"))
    for n in range(args.cycles):
        cycle(client, n)
        if args.sleep:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
