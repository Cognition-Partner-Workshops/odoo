from pathlib import Path

from odoo.tests.common import BaseCase, tagged

from odoo.addons.test_backend_neutral.harness import NEUTRAL_TAG
from odoo.addons.test_backend_neutral.harness.lint import lint_findings


@tagged(NEUTRAL_TAG)
class TestNeutralLint(BaseCase):

    def test_tests_are_neutral(self):
        """ The tests of this addon respect lint rules BN001-BN011; the
        harness is the one place that is not checked. """
        findings = lint_findings(Path(__file__).parent)
        self.assertFalse(findings, "Neutral lint findings:\n" + "\n".join(findings))
