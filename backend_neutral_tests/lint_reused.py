#!/usr/bin/env python
"""Lint the upstream code the neutral suite's ``core.*`` classes inherit.

A ``class TestAccessNeutral(TestAccess, NeutralCase)`` runs method bodies that
``lint_neutral.py odoo/addons/test_backend_neutral/tests`` never sees. This
script imports the three ``test_core_reuse_*`` modules (no database needed),
walks the MRO of every neutral class and lints the inherited class bodies,
ignoring the methods the neutral class overrides or leaves out. Run it with
the Odoo virtualenv from the repository root:

    /home/ubuntu/.venvs/odoo/bin/python backend_neutral_tests/lint_reused.py

Exit status 1 on any finding in inherited code. Module-level findings of the
upstream files (imports, module helpers) are listed for review and do not fail.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import odoo  # noqa: E402, F401  (sets up the odoo.addons import path)

from odoo.addons.test_backend_neutral.harness.lint import lint_inherited, neutral_test_classes  # noqa: E402
from odoo.addons.test_backend_neutral.tests import (  # noqa: E402
    test_core_reuse_as_is,
    test_core_reuse_split_by_class,
    test_core_reuse_with_edits,
)


def main():
    classes = neutral_test_classes(test_core_reuse_as_is, test_core_reuse_with_edits, test_core_reuse_split_by_class)
    findings, module_level = lint_inherited(classes)
    upstream = set()
    for cls in classes:
        for base in cls.__mro__:
            if base.__module__.startswith('odoo.addons.') and not base.__module__.startswith('odoo.addons.test_backend_neutral'):
                upstream.add(f"{base.__module__}.{base.__name__}")
    print(f"{len(classes)} neutral classes, {len(upstream)} inherited upstream classes:")
    for name in sorted(upstream):
        print(f"  {name}")
    for line in findings:
        print(line)
    print(f"{len(findings)} finding(s) in inherited code")
    if module_level:
        print(f"{len(module_level)} module-level finding(s) in the upstream files (for review, not inherited):")
        for line in module_level:
            print(f"  {line}")
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
