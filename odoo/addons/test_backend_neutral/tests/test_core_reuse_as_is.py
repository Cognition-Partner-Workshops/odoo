""" ``core.reuse_as_is``: classes of ``test_base/tests/test_orm`` that are
already backend-neutral, collected under the neutral tag by subclassing.

Each class here is ``class <Upstream>Neutral(<Upstream>, NeutralCase)`` with
``allow_inherited_tests_method = True``: the upstream ``setUpClass``/``setUp``
run their fixtures on top of the harness (``NeutralCase`` replaces
``TransactionCase`` in the MRO), and the test methods are the upstream ones.
The lint of the inherited code is ``TestNeutralLint.test_reused_code_is_neutral``.
"""
from odoo import Command
from odoo.tests.common import tagged

from odoo.addons.test_backend_neutral.harness import NEUTRAL_TAG, NeutralCase
from odoo.addons.test_base.tests.test_orm.test_access import TestAccess
from odoo.addons.test_base.tests.test_orm.test_acl import TestACL
from odoo.addons.test_base.tests.test_orm.test_action_bindings import TestActionBindings
from odoo.addons.test_base.tests.test_orm.test_config_settings import TestConfigSettings
from odoo.addons.test_base.tests.test_orm.test_copy import TestCopyTranslations
from odoo.addons.test_base.tests.test_orm.test_create import TestCreate
from odoo.addons.test_base.tests.test_orm.test_ir_qweb_fields import (
    TestCharExport,
    TestCurrencyExport,
    TestDateExport,
    TestDatetimeExport,
    TestDurationExport,
    TestFloatExport,
    TestHTMLExport,
    TestImageExport,
    TestIntegerExport,
    TestMany2OneExport,
    TestRelativeDatetime,
    TestSelectionExport,
    TestTextExport,
)
from odoo.addons.test_base.tests.test_orm.test_json_field import JsonFieldTest
from odoo.addons.test_base.tests.test_orm.test_prefetch import TestPrefecth
from odoo.addons.test_base.tests.test_orm.test_views import TestDefaultView, TestViewGroups

neutral = tagged(NEUTRAL_TAG, 'post_install', '-at_install')


# test_access.py
@neutral
class TestAccessNeutral(TestAccess, NeutralCase):
    allow_inherited_tests_method = True


# test_acl.py: the sample names one test of TestACL
@neutral
class TestACLNeutral(TestACL, NeutralCase):
    test_field_visibility_restriction = TestACL.test_field_visibility_restriction


# test_copy.py
@neutral
class TestCopyTranslationsNeutral(TestCopyTranslations, NeutralCase):
    allow_inherited_tests_method = True


# test_create.py
@neutral
class TestCreateNeutral(TestCreate, NeutralCase):
    allow_inherited_tests_method = True


# test_prefetch.py
@neutral
class TestPrefetchNeutral(TestPrefecth, NeutralCase):
    allow_inherited_tests_method = True


# test_views.py
@neutral
class TestDefaultViewNeutral(TestDefaultView, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestViewGroupsNeutral(TestViewGroups, NeutralCase):
    allow_inherited_tests_method = True


# test_check_access.py: upstream TestAccess is an HttpCase (it starts an HTTP
# server the tests never use); the fixture and the two tests are copied as is
# onto NeutralCase
@neutral
class TestCheckAccessNeutral(NeutralCase):
    def setUp(self):
        super().setUp()

        self.portal_user = self.env['res.users'].create({
            'login': 'P',
            'name': 'P',
            'group_ids': [Command.set([self.env.ref('base.group_portal').id])],
        })
        # a partner that can't be read by the portal user, would typically be a user's
        self.internal_user_partner = self.env['res.partner'].create({'name': 'I'})

        self.document = self.env['test_access_right.ticket'].create({
            'name': 'Need help here',
            'message_partner_ids': [Command.set([self.portal_user.partner_id.id,
                                            self.internal_user_partner.id])],
        })

    def test_check_access(self):
        """Typically, a document consulted by a portal user P
           will point to other records that P cannot read.
           For example, if P wants to consult a ticket of his,
           the ticket will have a reviewer or assigned user that is internal,
           and which partner cannot be read by P.
           This should not block P from accessing the ticket.
        """
        document = self.document.with_user(self.portal_user)
        # at this point, some fields might already be loaded in cache.
        # if so, it means we would bypass the ACL when trying to read the field
        # while this is bad, this is not the object of this test
        self.internal_user_partner.invalidate_model(['active'])
        # from portal's _document_check_access:
        document.check_access('read')
        # no raise, because we are supposed to be able to read our ticket

    def test_name_search_with_sudo(self):
        """Check that _name_search return correct values with sudo
        """
        no_access_user = self.env['res.users'].create({
            'login': 'no_access',
            'name': 'no_access',
            'group_ids': [Command.clear()],
        })
        document = self.env['test_access_right.ticket'].with_user(no_access_user)
        res = document.sudo().name_search('Need help here')
        self.assertEqual(res[0][1], "Need help here")


# test_config_settings.py
@neutral
class TestConfigSettingsNeutral(TestConfigSettings, NeutralCase):
    allow_inherited_tests_method = True


# test_json_field.py
@neutral
class TestJsonFieldNeutral(JsonFieldTest, NeutralCase):
    allow_inherited_tests_method = True


# test_ir_qweb_fields.py: TestExport is the fixture base, its subclasses hold the tests
@neutral
class TestCharExportNeutral(TestCharExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestIntegerExportNeutral(TestIntegerExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestFloatExportNeutral(TestFloatExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestCurrencyExportNeutral(TestCurrencyExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestTextExportNeutral(TestTextExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestMany2OneExportNeutral(TestMany2OneExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestImageExportNeutral(TestImageExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestSelectionExportNeutral(TestSelectionExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestHTMLExportNeutral(TestHTMLExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestDateExportNeutral(TestDateExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestDatetimeExportNeutral(TestDatetimeExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestDurationExportNeutral(TestDurationExport, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestRelativeDatetimeNeutral(TestRelativeDatetime, NeutralCase):
    allow_inherited_tests_method = True


# test_action_bindings.py
@neutral
class TestActionBindingsNeutral(TestActionBindings, NeutralCase):
    allow_inherited_tests_method = True


# test_autovacuum.py: TestAutovacuum.test_api_autovacuum is left out, it runs
# the cron inside `registry_test_mode()` (rule F3 / BN003).
