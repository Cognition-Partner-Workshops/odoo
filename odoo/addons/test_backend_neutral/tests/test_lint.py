import logging
from pathlib import Path

from odoo.tests.common import BaseCase, tagged

from odoo.addons.test_backend_neutral.harness import NEUTRAL_TAG
from odoo.addons.test_backend_neutral.harness.lint import lint_findings, lint_inherited, neutral_test_classes

from . import test_core_reuse_as_is, test_core_reuse_split_by_class, test_core_reuse_with_edits

_logger = logging.getLogger(__name__)


@tagged(NEUTRAL_TAG)
class TestNeutralLint(BaseCase):

    def test_tests_are_neutral(self):
        """ The tests of this addon respect lint rules BN001-BN011; the
        harness is the one place that is not checked. """
        findings = lint_findings(Path(__file__).parent)
        self.assertFalse(findings, "Neutral lint findings:\n" + "\n".join(findings))

    def test_reused_code_is_neutral(self):
        """ The upstream ``test_orm`` code that the ``core.*`` classes inherit
        and run (fixtures, helpers, collected test methods) respects the lint
        rules too; the methods overridden or left out here are not counted. """
        classes = neutral_test_classes(test_core_reuse_as_is, test_core_reuse_with_edits, test_core_reuse_split_by_class)
        self.assertTrue(classes)
        findings, module_level = lint_inherited(classes)
        _logger.info("inherited lint: %s classes, %s module-level findings in upstream files (reviewed, not inherited)",
                     len(classes), len(module_level))
        self.assertFalse(findings, "Neutral lint findings in inherited code:\n" + "\n".join(findings))
