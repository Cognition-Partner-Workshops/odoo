#!/usr/bin/env python3
"""Show or flip the stand-in switch; every flip is one audit line.

Usage: switch.py init                  copy the committed switch.json to $STANDIN_SWITCH_CONFIG
       switch.py show
       switch.py set <slice> <source|reads|writes> --reason TEXT
The running Odoo re-reads the file per request, so a flip applies from the next request.
"""
import argparse
import getpass
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "addons" / "standin_switch"))
import switch_core  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("show")
    flip = sub.add_parser("set")
    flip.add_argument("slice")
    flip.add_argument("position", choices=switch_core.positions)
    flip.add_argument("--reason", required=True)
    args = parser.parse_args()

    path = switch_core.configPath()
    if args.cmd == "init":
        if path == switch_core.committedConfig:
            sys.exit("set STANDIN_SWITCH_CONFIG to a runtime path first; the committed file stays all-source")
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(switch_core.committedConfig, path)
        switch_core.audit("init", switch_core.loadConfig(), config_path=str(path), user=getpass.getuser())
    elif args.cmd == "set":
        if path == switch_core.committedConfig:
            sys.exit("set STANDIN_SWITCH_CONFIG to the runtime copy (switch.py init) before flipping")
        config = switch_core.loadConfig()
        if args.slice not in config["slices"]:
            sys.exit(f"unknown slice {args.slice}; known: {sorted(config['slices'])}")
        before = config["slices"][args.slice]["position"]
        updated = json.loads(json.dumps(config))
        updated["slices"][args.slice]["position"] = args.position
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(updated, indent=2) + "\n")
        os.replace(tmp, path)
        switch_core.audit("flip", updated, slice=args.slice, before=before, after=args.position,
                          reason=args.reason, user=getpass.getuser(), config_path=str(path))
    print(json.dumps(switch_core.loadConfig(), indent=2))


if __name__ == "__main__":
    main()
