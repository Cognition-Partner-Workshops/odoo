""" ``core.reuse_split_by_class``: files of ``test_base/tests/test_orm`` that
mix behavioural classes with SQL-asserting ones. The behavioural classes are
subclassed on ``NeutralCase`` (see ``test_core_reuse_as_is.py``); the
SQL-asserting classes named in the sample (``TestComputeQueries``,
``TestModifiedPerformance``, ``TestSubqueries``, ``TestQueries``,
``TestFlushSearch``) are not imported. Methods flagged by the neutral lint are
overridden with an edited copy or set to ``None`` with the reason.
"""
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, LockError, UserError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.test_backend_neutral.harness import NEUTRAL_TAG, NeutralCase
from odoo.addons.test_base.tests.test_orm.test_domain_expression import (
    TestExpression,
    TestMany2many,
    TestMany2one,
    TestOne2many,
)
from odoo.addons.test_base.tests.test_orm.test_fields import (
    TestCompanyDependent,
    TestRequiredMany2one,
    TestSelectionOndelete,
    TestUnlinkConstraints,
)
from odoo.addons.test_base.tests.test_orm.test_fields import TestParentStore as TestFieldsParentStore
from odoo.addons.test_base.tests.test_orm.test_models import TestORM, TestRecordset
from odoo.addons.test_base.tests.test_orm.test_properties import PropertiesCase, PropertiesSearchCase
from odoo.addons.test_base.tests.test_orm.test_read_group_private import TestPrivateReadGroup, TestPublicReadGroup
from odoo.addons.test_base.tests.test_orm.test_search import TestSearch

neutral = tagged(NEUTRAL_TAG, 'post_install', '-at_install')


# test_fields.py
@neutral
class TestFieldsParentStoreNeutral(TestFieldsParentStore, NeutralCase):
    allow_inherited_tests_method = True

    def test_compute_depend_parent_path(self):
        self.assertEqual(self.cats(7).depth, 3)
        self.assertEqual(self.cats(8).depth, 3)
        self.assertEqual(self.cats(9).depth, 3)

        # change parent of node to have 2 parents
        self.cats(7).parent = self.cats(2)
        self.assertEqual(self.cats(7).depth, 2)

        # change parent of node to root
        self.cats(7).parent = False
        self.assertEqual(self.cats(7).depth, 0)

        # change grand-parent of nodes
        self.cats(6).parent = self.cats(0)
        self.assertEqual(self.cats(8).depth, 2)
        self.assertEqual(self.cats(9).depth, 2)

        # warmup
        self.cats().create({'name': 'warmup'})
        # add a new node: one query to INSERT, one query to UPDATE parent_path
        cat = self.cats().create({'name': '10', 'parent': self.cats(6).id})
        self.assertEqual(cat.depth, 2)


@neutral
class TestSelectionOndeleteNeutral(TestSelectionOndelete, NeutralCase):
    allow_inherited_tests_method = True

    def setUp(self):
        # upstream setUp patches `self.registry` directly: skip it and ask the harness
        super(TestSelectionOndelete, self).setUp()
        # enable unlinking ir.model.fields.selection
        self.patch_registry('ready', False)


@neutral
class TestUnlinkConstraintsNeutral(TestUnlinkConstraints, NeutralCase):
    allow_inherited_tests_method = True

    def test_unlink_uninstall(self):
        self.patch_registry('uninstalling_modules', {'test_base'})

        self.assertTrue(self.deletable_foo.unlink())
        self.assertTrue(self.deletable_bar.unlink())

        # should fail since it's at_uninstall=True
        with self.assertRaises(ValueError, msg="You didn't say if you wanted it crudo or cotto..."):
            self.undeletable_foo.unlink()

        # should succeed since it's at_uninstall=False
        self.assertTrue(self.undeletable_bar.unlink())


@neutral
class TestRequiredMany2oneNeutral(TestRequiredMany2one, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestCompanyDependentNeutral(TestCompanyDependent, NeutralCase):
    allow_inherited_tests_method = True

    # the models are enumerated through ir.model instead of the registry
    def test_orm_ondelete_restrict(self):
        # model_A
        #  | field_a                           company dependent many2one is
        #  | company dependent many2one        stored as jsonb and doesn't
        #  | (ondelete='restrict')             have db ON DELETE action
        #  v
        # model_B
        #  | field_b                           if a row for model_B is deleted
        #  | many2one (ondelete='cascade')     because of ON DELETE CASCADE,
        #  v                                   model_A will reference a deleted
        # model_C                              row and logically be NULL when read
        #
        #                                      this test asks you to move the
        #                                      ON DELETE CASCADE logic of model_B
        #                                      to ORM and remove ondelete='cascade'

        for model_name in self.env['ir.model'].search([]).mapped('model'):
            model = self.env[model_name]
            for field in model._fields.values():
                if field.company_dependent and field.type == 'many2one' and field.ondelete.lower() == 'restrict':
                    for comodel_field in self.env[field.comodel_name]._fields.values():
                        if comodel_field.type != 'many2one':
                            continue
                        self.assertNotEqual(
                            comodel_field.ondelete, 'cascade',
                            (f'when a row for {comodel_field.comodel_name} is deleted, a row for {comodel_field.model_name} '
                             f'may also be deleted for sake of on delete cascade field {comodel_field}, which will '
                             f'bypass the ORM ondelete="restrict" check for a company dependent many2one field {field}. '
                             f'Please override the unlink method of {comodel_field.comodel_name} and do the ORM on '
                             f'delete cascade logic and remove/override the ondelete="cascade" of {comodel_field}'),
                        )


# test_search.py: TestSearchAny and TestSearchRelated are left out as whole
# classes, every one of their tests asserts the SQL text of a search only
# (assertQueries); TestSubqueries and TestFlushSearch are excluded by the sample
@neutral
class TestSearchNeutral(TestSearch, NeutralCase):
    allow_inherited_tests_method = True

    @mute_logger('odoo.models')
    def test_search_count(self):
        # the SQL COUNT(*) cross-check is replaced by a Python count of the same records
        sql_count = len([partner for partner in self.partners if partner.active])
        self.assertTrue(sql_count)
        self.assertIsInstance(sql_count, int)

        search_count = self.env['test_orm.partner'].search_count([('id', 'in', self.partners.ids)])
        self.assertTrue(search_count)
        self.assertIsInstance(search_count, int)

        self.assertEqual(sql_count, search_count)


# test_domain_expression.py
@neutral
class TestExpressionNeutral(TestExpression, NeutralCase):
    allow_inherited_tests_method = True

    def _unlinked_id(self, model, **values):
        """ The id of a record that no longer exists, instead of `max(ids) + n`. """
        record = model.create({'name': 'unlinked', **values})
        record.unlink()
        return record.id

    test_accent = None  # left out: branches on the backend's unaccent feature (registry.has_unaccent) and patches it

    def test_10_equivalent_id(self):
        # equivalent queries
        Partner = self.env['test_orm.partner']
        non_partner_id = self._unlinked_id(Partner)
        res_0 = self._search(Partner, [])
        res_1 = self._search(Partner, [('name', 'not like', 'probably_unexisting_name')])
        self.assertEqual(res_0, res_1)
        res_2 = self._search(Partner, [('id', 'not in', [non_partner_id])])
        self.assertEqual(res_0, res_2)
        res_3 = self._search(Partner, [('id', 'not in', [])])
        self.assertEqual(res_0, res_3)
        res_4 = self._search(Partner, [('id', '!=', False)])
        self.assertEqual(res_0, res_4)

        # equivalent queries, integer and string
        all_partners = self._search(Partner, [])
        self.assertGreater(len(all_partners), 1)
        one = all_partners[0]
        others = all_partners - one

        res_1 = self._search(Partner, [('id', '=', one.id)])
        self.assertEqual(one, res_1)
        # Partner.search([('id', '!=', others)]) # not permitted
        res_2 = self._search(Partner, [('id', 'not in', others.ids)])
        self.assertEqual(one, res_2)
        res_3 = self._search(Partner, ['!', ('id', '!=', one.id)])
        self.assertEqual(one, res_3)
        res_4 = self._search(Partner, ['!', ('id', 'in', others.ids)])
        self.assertEqual(one, res_4)
        res_5 = self._search(Partner, [('id', 'in', one.id)])
        self.assertEqual(one, res_5)
        res_6 = self._search(Partner, [('id', 'in', [one.id])])
        self.assertEqual(one, res_6)
        res_7 = self._search(Partner, [('name', '=', one.name)])
        self.assertEqual(one, res_7)
        res_8 = self._search(Partner, [('name', 'in', [one.name])])
        self.assertEqual(one, res_8)

    def test_15_m2o(self):
        Partner = self.env['test_orm.partner']

        # testing equality with False
        partners = Partner._search([('parent_id', '=', False)])
        self.assertTrue(partners)

        # testing equality with name
        partners = self._search(Partner, [('parent_id', '=', 'Pepper Street')])
        self.assertTrue(partners)

        # testing the in operator with name
        partners = self._search(Partner, [('parent_id', 'in', 'Pepper Street')])
        self.assertTrue(partners)

        # testing the in operator with a list of names
        partners = self._search(Partner, [('parent_id', 'in', ['Pepper Street', 'Inner Works'])])
        self.assertTrue(partners)

        # check if many2one works with empty search list
        partners = self._search(Partner, [('business_id', 'in', [])])
        self.assertFalse(partners)

        # testing the in operator with a list that includes False
        partners = Partner._search([('parent_id', 'in', [False])])
        self.assertTrue(partners)

        # create new business with partners, and partners with no business
        business2 = self.env['test_orm.business'].create({
            'name': 'Acme 2',
            'partner_id': self.env['test_orm.partner'].create({'name': 'Acme 2'}).id,
        })
        for i in range(4):
            Partner.create({'name': 'P of Acme %s' % i, 'business_id': business2.id})
            Partner.create({'name': 'P of All %s' % i, 'business_id': False})

        # check if many2one works with negative empty list
        all_partners = Partner.search([])
        res_partners = self._search(Partner, ['|', ('business_id', 'not in', []), ('business_id', '=', False)])
        self.assertEqual(all_partners, res_partners, "not in [] fails")

        # check that many2one will pick the correct records with a list
        partners = self._search(Partner, [('business_id', 'in', [False])])
        self.assertTrue(len(partners) >= 4, "We should have at least 4 partners with no business")

        # check that many2one will exclude the correct records with a list
        partners = self._search(Partner, [('business_id', 'not in', [1])])
        self.assertTrue(len(partners) >= 4, "We should have at least 4 partners not related to business #1")

        # check that many2one will exclude the correct records with a list and False
        partners = self._search(Partner, ['|', ('business_id', 'not in', [1]),
                                        ('business_id', '=', False)])
        self.assertTrue(len(partners) >= 8, "We should have at least 8 partners not related to business #1")

        # check that multi-level expressions also work
        partners = self._search(Partner, [('business_id.partner_id', 'in', [])])
        self.assertFalse(partners)

        # check multi-level expressions with magic columns
        partners = self._search(Partner, [('create_uid.active', '=', True)])

        # check that multi-level expressions with negative op work
        all_partners = self._search(Partner, [('business_id', '!=', False)])

        # check with empty list
        res_partners = self._search(Partner, [('business_id.partner_id', 'not in', [])])
        self.assertEqual(all_partners, res_partners, "not in [] fails")

        # Test the '(not) like/in' behavior. test_orm.partner and its parent_id
        # column are used because parent_id is a many2one, allowing to test the
        # Null value, and there are actually some null and non-null values in
        # the demo data.
        all_partners = self._search(Partner, [])
        non_partner_id = self._unlinked_id(Partner)

        with_parent = all_partners.filtered(lambda p: p.parent_id)
        without_parent = all_partners.filtered(lambda p: not p.parent_id)
        with_website = all_partners.filtered(lambda p: p.website)

        # We treat null values differently than in SQL. For instance in SQL:
        #   SELECT id FROM test_orm_partner WHERE parent_id NOT IN (0)
        # will return only the records with non-null parent_id.
        #   SELECT id FROM test_orm_partner WHERE parent_id IN (0)
        # will return expectedly nothing (our ids always begin at 1).
        # This means the union of those two results will give only some
        # records, but not all present in database.
        #
        # When using domains and the ORM's search method, we think it is
        # more intuitive that the union returns all the records, and that
        # a domain like ('parent_id', 'not in', [0]) will return all
        # the records. For instance, if you perform a search for the companies
        # that don't have OpenERP has a parent company, you expect to find,
        # among others, the companies that don't have parent company.
        #

        # existing values be treated similarly if we simply check that some
        # existing value belongs to them.
        res_0 = self._search(Partner, [('parent_id', 'not like', 'probably_unexisting_name')])  # get all rows, included null parent_id
        self.assertEqual(res_0, all_partners)
        res_1 = self._search(Partner, [('parent_id', 'not in', [non_partner_id])])  # get all rows, included null parent_id
        self.assertEqual(res_1, all_partners)
        res_2 = self._search(Partner, [('parent_id', '!=', False)])  # get rows with not null parent_id, deprecated syntax
        self.assertEqual(res_2, with_parent)
        res_3 = self._search(Partner, [('parent_id', 'not in', [])])  # get all rows, included null parent_id
        self.assertEqual(res_3, all_partners)
        res_4 = self._search(Partner, [('parent_id', 'not in', [False])])  # get rows with not null parent_id
        self.assertEqual(res_4, with_parent)
        res_4b = self._search(Partner, [('parent_id', 'not ilike', '')])  # get only rows without parent
        self.assertEqual(res_4b, without_parent)

        # The results of these queries, when combined with queries 0..4 must
        # give the whole set of ids.
        res_5 = self._search(Partner, [('parent_id', 'like', 'probably_unexisting_name')])
        self.assertFalse(res_5)
        res_6 = self._search(Partner, [('parent_id', 'in', [non_partner_id])])
        self.assertFalse(res_6)
        res_7 = self._search(Partner, [('parent_id', '=', False)])
        self.assertEqual(res_7, without_parent)
        res_8 = self._search(Partner, [('parent_id', 'in', [])])
        self.assertFalse(res_8)
        res_9 = self._search(Partner, [('parent_id', 'in', [False])])
        self.assertEqual(res_9, without_parent)
        res_9b = self._search(Partner, [('parent_id', 'ilike', '')])  # get those with a parent
        self.assertEqual(res_9b, with_parent)

        # These queries must return exactly the results than the queries 0..4,
        # i.e. not ... in ... must be the same as ... not in ... .
        res_10 = self._search(Partner, ['!', ('parent_id', 'like', 'probably_unexisting_name')])
        self.assertEqual(res_0, res_10)
        res_11 = self._search(Partner, ['!', ('parent_id', 'in', [non_partner_id])])
        self.assertEqual(res_1, res_11)
        res_12 = self._search(Partner, ['!', ('parent_id', '=', False)])
        self.assertEqual(res_2, res_12)
        res_13 = self._search(Partner, ['!', ('parent_id', 'in', [])])
        self.assertEqual(res_3, res_13)
        res_14 = self._search(Partner, ['!', ('parent_id', 'in', [False])])
        self.assertEqual(res_4, res_14)

        # Testing many2one field is not enough, a regular char field is tested
        res_15 = self._search(Partner, [('website', 'in', [])])
        self.assertFalse(res_15)
        res_16 = self._search(Partner, [('website', 'not in', [])])
        self.assertEqual(res_16, all_partners)
        res_17 = self._search(Partner, [('website', '!=', False)])
        self.assertEqual(res_17, with_website)

        # check behavior for required many2one fields: currency_id is required
        business = self.env['test_orm.business'].search([])
        res_101 = self._search(business, [('partner_id', 'not ilike', '')])  # get no business
        self.assertFalse(res_101)
        res_102 = self._search(business, [('partner_id', 'ilike', '')])  # get all business
        self.assertEqual(res_102, business)

    def test_15_equivalent_one2many_2(self):
        Country = self.env['test_orm.domain_expression.country']
        State = self.env['test_orm.domain_expression.country.state']

        country_be, country_fr = Country.create([
            {'name': 'Belgium'},
            {'name': 'France'},
        ])

        State.create([
            {
                'name': 'Antwerp',
                'country_id': country_be.id,
            }, {
                'name': 'Normandie',
                'country_id': country_fr.id,
            }, {
                'name': 'Bretagne',
                'country_id': country_fr.id,
            },
        ])

        # create a country and a state
        State.create({
            'name': 'Catalonia',
            'country_id': Country.create({'name': 'Spain'}).id,
        })
        non_country_id = self._unlinked_id(State, country_id=country_fr.id)

        # search the country via its rates one2many (the one2many must point back at the country)
        country_state1 = self._search(State, [('country_id', 'not like', 'probably_unexisting_name')])
        country_state2 = self._search(State, [('id', 'not in', [non_country_id])])
        self.assertEqual(country_state1, country_state2)
        country_state3 = self._search(State, [('id', 'not in', [])])
        self.assertEqual(country_state1, country_state3)

        # one2many towards another model
        self.assertEqual(country_fr, self._search(Country, [('state_ids', 'in', country_fr.state_ids.ids)]))
        self.assertEqual(country_fr, self._search(Country, [('state_ids', 'in', country_fr.state_ids[0].ids)]))
        self.assertEqual(country_fr, self._search(Country, [('state_ids', 'in', country_fr.state_ids[0].id)]))

        self.assertFalse(self._search(Country, [('state_ids', 'like', 'probably_unexisting_name')]))
        with self.assertRaises(ValueError):
            Country.search([('state_ids', 'unexisting_op', 'probably_unexisting_name')])  # noqa: OLS03009 (Invalid comparison operator)

        # get the countries referenced by some state using a weird negative domain
        expected = self._search(Country, [('state_ids', 'not like', 'probably_unexisting_name')])

        self.assertEqual(expected, self._search(Country, [('state_ids', 'not in', [non_country_id])]))
        self.assertEqual(expected, self._search(Country, [('state_ids', '!=', False)]))
        self.assertEqual(expected, self._search(Country, [('state_ids', 'not in', [])]))

    def test_filtered_domain_any_operator(self):
        Partner = self.env['test_orm.partner']

        all_partner = self._search(Partner, [])
        partner = self.partners[0]

        children_partner_1 = self._search(Partner, [('parent_id', 'any', [('name', '=', partner.name)])])
        self.assertEqual(children_partner_1, partner.child_ids)

        children_other_partners = self._search(Partner, [('parent_id', 'not any', [('name', '=', partner.name)])])
        self.assertEqual(children_other_partners, all_partner - partner.child_ids)

        one_child_partner = partner.child_ids[0]
        parent_partner = self._search(Partner, [('child_ids', 'any', [('name', '=', one_child_partner.name)])])
        self.assertEqual(parent_partner, partner)

        other_partners = self._search(Partner, [('child_ids', 'not any', [('name', '=', one_child_partner.name)])])
        self.assertEqual(other_partners, all_partner - partner)

        # check if we perform the check in batch
        PartnerClass = type(self.env['test_orm.partner'])
        with patch.object(PartnerClass, 'filtered_domain', autospec=True, side_effect=PartnerClass.filtered_domain) as patched:
            all_partner.filtered_domain([('child_ids', 'any', [('name', '=', partner.name)])])
            self.assertEqual(patched.call_count, 2, "should be called here and only once for the any operator")

    def test_invalid(self):
        """ verify that invalid expressions are refused, even for magic fields """
        Country = self.env['test_orm.country']

        with self.assertRaisesRegex(ValueError, r"^Invalid field.*'abcdefg'"):
            Country.search([('abcdefg', 'in', ['foo'])])

        with self.assertRaisesRegex(ValueError, r"^Invalid field.*\"Et plouf\"'"):
            Country.search([('name."Et plouf"', 'ilike', 'foo')])  # noqa: OLS03013 (Invalid dot notation)

        with self.assertRaisesRegex(ValueError, r"^Invalid field.*\"Et plouf\"'"):
            Country.search([('name."Et plouf"', 'in', ['foo'])])  # noqa: OLS03013 (Invalid dot notation)

        with self.assertRaisesRegex(ValueError, r"'does_not_exist'"):
            Country.search([]).filtered_domain([('does_not_exist', '=', 'foo')])

        with self.assertRaisesRegex(ValueError, r"^Invalid operator.*\('create_date', '>>', 'foo'\)$"):
            Country.search([('create_date', '>>', 'foo')])  # noqa: OLS03009 (Invalid comparison operator)

        with self.assertRaisesRegex(ValueError, r"^Invalid operator"):
            Country.search([]).filtered_domain([('create_date', '>>', 'foo')])  # noqa: OLS03009 (Invalid comparison operator)

        with self.assertRaisesRegex(ValueError, r"Invalid isoformat string"):
            Country.search([('create_date', '=', "1970-01-01'); --")])


@neutral
class TestMany2oneNeutral(TestMany2one, NeutralCase):
    allow_inherited_tests_method = True

    test_inherited = None  # left out: its only assertion is the SQL text (assertQueries)
    test_regular = None  # left out: its only assertion is the SQL text (assertQueries)
    test_complement_regular = None  # left out: its only assertion is the SQL text (assertQueries)
    test_explicit_subquery = None  # left out: asserts the SQL text of an explicit subquery (assertQueries)
    test_bypass_search_access = None  # left out: its only assertion is the SQL text (assertQueries)

    def test_name_search(self):
        self.Partner.search([('business_id', 'like', self.business.name)])

        self.Partner.search([('business_id', 'like', self.business.name)])

        self.Partner.search([('business_id', 'not like', "blablabla")])

    def test_name_search_undefined(self):
        """Check that if the _rec_name is not defined, we do not restrict anything.

        This way the model continues to work in the web interface inside many2one fields.
        """
        PartnerClass = type(self.env['test_orm.partner'])
        with (
            patch.object(PartnerClass, '_rec_name', ''),
            patch.object(PartnerClass, '_rec_names_search', []),
            mute_logger('odoo.models'),
        ):
            self.assertGreater(len(self.Partner.name_search()), 0)
            self.assertGreater(len(self.Partner.name_search('test')), 0)


@neutral
class TestOne2manyNeutral(TestOne2many, NeutralCase):
    allow_inherited_tests_method = True

    test_regular = None  # left out: its only assertion is the SQL text (assertQueries)
    test_bypass_search_access = None  # left out: its only assertion is the SQL text (assertQueries)
    testbypass_search_access_mixed = None  # left out: its only assertion is the SQL text (assertQueries)
    test_empty = None  # left out: its only assertion is the SQL text (assertQueries)

    def test_name_search(self):
        # Warm-up
        self.Partner.search([('bank_ids', 'like', '12')])

        self.Partner.search([('bank_ids', 'like', '12')])


@neutral
class TestMany2manyNeutral(TestMany2many, NeutralCase):
    allow_inherited_tests_method = True

    test_regular = None  # left out: its only assertion is the SQL text (assertQueries)
    test_regular_in_false = None  # left out: its only assertion is the SQL text (assertQueries)
    test_bypass_search_access = None  # left out: its only assertion is the SQL text (assertQueries)
    test_empty = None  # left out: its only assertion is the SQL text (assertQueries)

    def test_name_search(self):
        # Warm-up
        self.Partner.search([('category_id', 'like', 'foo')], order='id')

        self.Partner.search([('category_id', 'like', 'foo')], order='id')


# test_read_group_private.py
@neutral
class TestPrivateReadGroupNeutral(TestPrivateReadGroup, NeutralCase):
    allow_inherited_tests_method = True

    def test_simple_private_read_group(self):
        Model = self.env['test_read_group.aggregate']
        partner_1 = self.env['test_read_group.partner'].create({'name': 'z_one'})
        partner_2 = self.env['test_read_group.partner'].create({'name': 'a_two'})
        Model.create({'key': 1, 'partner_id': partner_1.id, 'value': 1})
        Model.create({'key': 1, 'partner_id': partner_1.id, 'value': 2})
        Model.create({'key': 1, 'partner_id': partner_2.id, 'value': 3})
        Model.create({'key': 2, 'partner_id': partner_2.id, 'value': 4})
        Model.create({'key': 2, 'partner_id': partner_2.id})
        Model.create({'key': 2, 'value': 5})
        Model.create({'partner_id': partner_2.id, 'value': 5})
        Model.create({'value': 6})
        Model.create({})

        self.assertEqual(
            Model._read_group([], groupby=['key'], aggregates=['value:sum']),
            [
                (1, 1 + 2 + 3),
                (2, 4 + 5),
                (False, 5 + 6),
            ],
        )

        # Forcing order with many2one, traverse use the order of the comodel (test_read_group.partner)
        self.assertEqual(
            Model._read_group([], groupby=['key', 'partner_id'], aggregates=['value:sum'], order="key, partner_id"),
            [
                (1, partner_2, 3),
                (1, partner_1, 1 + 2),
                (2, partner_2, 4),
                (2, self.env['test_read_group.partner'], 5),
                (False, partner_2, 5),
                (False, self.env['test_read_group.partner'], 6),
            ],
        )

        # Same than before but with private method, the order doesn't traverse
        # many2one order, then the order is based on id of partner
        self.assertEqual(
            Model._read_group([], groupby=['key', 'partner_id'], aggregates=['value:sum']),
            [
                (1, partner_1, 1 + 2),
                (1, partner_2, 3),
                (2, partner_2, 4),
                (2, self.env['test_read_group.partner'], 5),
                (False, partner_2, 5),
                (False, self.env['test_read_group.partner'], 6),
            ],
        )

    def test_falsy_domain(self):
        Model = self.env['test_read_group.aggregate']

        result = Model._read_group([('id', 'in', [])], groupby=['partner_id'], aggregates=[])
        self.assertEqual(result, [])

        result = Model._read_group(
            [('id', 'in', [])],
            groupby=[],
            aggregates=['__count', 'partner_id:count', 'partner_id:count_distinct'],
        )
        # When there are no groupby, postgresql return always one row, check
        # that it is the case when the domain is falsy and the query is not
        # made at all
        self.assertEqual(result, [(0, 0, 0)])

    def test_prefetch_for_records(self):
        Model = self.env['test_read_group.aggregate']
        Partner = self.env['test_read_group.partner']
        partner_1 = Partner.create({'name': 'z_one'})
        partner_2 = Partner.create({'name': 'a_two'})
        Model.create({'key': 1, 'partner_id': partner_1.id})
        Model.create({'key': 2, 'partner_id': partner_2.id})

        self.env.invalidate_all()

        result = Model._read_group([], ['partner_id'], [])

        # partner_1 and partner_2 are records
        self.assertEqual(result, [(partner_1,), (partner_2,)])
        [[value1], [value2]] = result
        value1.name
        value2.name

        self.env.invalidate_all()

        result = Model._read_group([], ['key'], ['partner_id:recordset'])
        self.assertEqual(result, [(1, partner_1), (2, partner_2)])
        [[__, value1], [__, value2]] = result
        value1.name
        value2.name

    def test_ambiguous_field_name(self):
        """ Check that _read_group doesn't generate ambiguous (display_name) alias for the backend
        """
        Model = self.env['test_read_group.aggregate']
        partner_1 = self.env['test_read_group.partner'].create({'name': 'z_one'})
        Model.create({'key': 1, 'partner_id': partner_1.id, 'value': 1, 'display_name': 'blabla'})

        result = Model._read_group(
            [],
            groupby=['display_name', 'partner_id'],
            aggregates=['__count'],
            order="partner_id DESC",
        )
        self.assertEqual(result, [('blabla', partner_1, 1)])

    def test_having_clause(self):
        Model = self.env['test_read_group.aggregate']
        Model.create({'key': 1, 'value': 8})
        Model.create({'key': 1, 'value': 2})
        Model.create({'key': 2, 'value': 5})
        Model.create({'key': 3, 'value': 2})
        Model.create({'key': 3, 'value': 4})
        Model.create({'key': 3, 'value': 1})

        self.assertEqual(
            Model._read_group(
                [],
                groupby=['key'],
                aggregates=['value:sum'],
                having=[('value:sum', '>', 8)],
            ),
            [(1, 2 + 8)],
        )

        self.assertEqual(
            Model._read_group(
                [],
                groupby=['key'],
                aggregates=['value:sum', '__count'],
                having=[('__count', '<', 3), ("value:sum", '>', 4)],
            ),
            [
                (1, 2 + 8, 2),
                (2, 5, 1),
            ],
        )

    def test_groupby_many2many(self):
        User = self.env['test_read_group.user']
        mario, luigi = User.create([{'name': 'Mario'}, {'name': 'Luigi'}])
        tasks = self.env['test_read_group.task'].create([
            {   # both users
                'name': "Super Mario Bros.",
                'user_ids': [Command.set((mario + luigi).ids)],
            },
            {   # mario only
                'name': "Paper Mario",
                'user_ids': [Command.set(mario.ids)],
            },
            {   # luigi only
                'name': "Luigi's Mansion",
                'user_ids': [Command.set(luigi.ids)],
            },
            {   # no user
                'name': 'Donkey Kong',
            },
        ])

        # TODO: should we order by the relation and not by the id also for many2many
        # (same than many2one) ? for public methods ?
        self.assertEqual(tasks._read_group(
                [('id', 'in', tasks.ids)],
                ['user_ids'],
                ['name:array_agg'],
            ),
            [
                (mario, ["Super Mario Bros.", "Paper Mario"]),      # tasks of Mario
                (luigi, ["Super Mario Bros.", "Luigi's Mansion"]),  # tasks of Luigi
                (User, ["Donkey Kong"]),                            # tasks of nobody
            ],
        )

        # Inverse the order, only inverse depending of id (see TODO above)
        self.assertEqual(tasks._read_group(
                [('id', 'in', tasks.ids)],
                ['user_ids'],
                ['name:array_agg'],
                order='user_ids DESC',
            ),
            [
                (User, ["Donkey Kong"]),                            # tasks of nobody
                (luigi, ["Super Mario Bros.", "Luigi's Mansion"]),  # tasks of Luigi
                (mario, ["Super Mario Bros.", "Paper Mario"]),      # tasks of Mario
            ],
        )

        # group tasks with some ir.access on users
        users_model = self.env['ir.model']._get(mario._name)
        self.env['ir.access'].create({
            'name': "Only The Lone Wanderer allowed",
            'model_id': users_model.id,
            'operation': 'crud',
            'domain': [('id', '=', mario.id)],
        })
        # as demo user, ir.access should apply
        tasks = tasks.with_user(self.base_user)

        # warming up various caches; this avoids extra queries
        tasks._read_group([], groupby=['user_ids'], aggregates=['name:array_agg'])

        self.assertEqual(
            tasks._read_group([], groupby=['user_ids'], aggregates=['name:array_agg']),
            [
                (mario, ['Super Mario Bros.', 'Paper Mario']),
                (User, ["Luigi's Mansion", 'Donkey Kong']),
            ],
        )

    def test_groupby_many2many_active_test_domain(self):
        Tag = self.env['test_read_group.tag']
        active_tag, archive_tag = Tag.create([
            {'name': 'Active tag', 'active': True},
            {'name': 'Archive tag', 'active': False},
        ])
        tasks = self.env['test_read_group.task'].create([
            {
                'name': "Both tags",
                'tag_ids': [Command.set((active_tag + archive_tag).ids)],
            },
            {
                'name': "Active tag",
                'tag_ids': [Command.set(active_tag.ids)],
            },
            {
                'name': "Archive tag",
                'tag_ids': [Command.set(archive_tag.ids)],
            },
            {
                'name': "No tag",
            },
        ])

        self.assertEqual(
            tasks._read_group(
                [('id', 'in', tasks.ids)],
                ['tag_ids'],
                ['name:array_agg'],
            ),
            [
                (active_tag, ["Both tags", "Active tag"]),
                (Tag, ["Archive tag", "No tag"]),
            ],
        )

        self.assertEqual(
            tasks._read_group(
                [('id', 'in', tasks.ids)],
                ['active_tag_ids'],
                ['name:array_agg'],
            ),
            [
                (active_tag, ["Both tags", "Active tag"]),
                (Tag, ["Archive tag", "No tag"]),
            ],
        )

        self.assertEqual(
            tasks._read_group(
                [('id', 'in', tasks.ids)],
                ['all_tag_ids'],
                ['name:array_agg'],
            ),
            [
                (active_tag, ["Both tags", "Active tag"]),
                (archive_tag, ["Both tags", "Archive tag"]),
                (Tag, ["No tag"]),
            ],
        )

    def test_related(self):
        RelatedBar = self.env['test_read_group.related_bar']
        RelatedFoo = self.env['test_read_group.related_foo']
        RelatedBase = self.env['test_read_group.related_base']

        bars = RelatedBar.create([
            {'name': 'bar_a'},
            {'name': False},
        ])

        foos = RelatedFoo.create([
            {'name': 'foo_a_bar_a', 'bar_id': bars[0].id},
            {'name': 'foo_b_bar_false', 'bar_id': bars[1].id},
            {'name': False, 'bar_id': bars[0].id},
            {'name': False},
        ])

        RelatedBase.create([
            {'name': 'base_foo_a_1', 'foo_id': foos[0].id},
            {'name': 'base_foo_a_2', 'foo_id': foos[0].id},
            {'name': 'base_foo_b_bar_false', 'foo_id': foos[1].id},
            {'name': 'base_false_foo_bar_a', 'foo_id': foos[2].id},
            {'name': 'base_false_foo', 'foo_id': foos[3].id},
        ])

        # env.su => false
        RelatedBase = RelatedBase.with_user(self.base_user)

        field_info = RelatedBase.fields_get(
            ['foo_id_name', 'foo_id_name_sudo', 'foo_id_bar_id_name', 'foo_id_bar_name', 'foo_id_bar_name_sudo'],
            ['groupable', 'aggregator'],
        )
        self.assertTrue(field_info['foo_id_name']['groupable'])
        self.assertNotIn('aggregator', field_info['foo_id_name'])

        self.assertTrue(field_info['foo_id_name_sudo']['groupable'])
        self.assertNotIn('aggregator', field_info['foo_id_name_sudo'])

        self.assertTrue(field_info['foo_id_bar_id_name']['groupable'])
        self.assertEqual(field_info['foo_id_bar_id_name']['aggregator'], 'count_distinct')

        self.assertTrue(field_info['foo_id_bar_name']['groupable'])
        self.assertEqual(field_info['foo_id_bar_name']['aggregator'], 'count_distinct')

        self.assertTrue(field_info['foo_id_bar_name_sudo']['groupable'])
        self.assertEqual(field_info['foo_id_bar_name_sudo']['aggregator'], 'count_distinct')

        RelatedBase._read_group([], ['foo_id_name'], ['__count'])
        self.assertEqual(
            RelatedBase._read_group([], ['foo_id_name_sudo'], ['__count']),
            [('foo_a_bar_a', 2), ('foo_b_bar_false', 1), (False, 2)],
        )

        # Same query generated by grouping foo_id_bar_id_name/foo_id_bar_name/foo_id_bar_name_sudo

        self.assertEqual(
            RelatedBase._read_group([], ['foo_id_bar_id_name'], ['__count']),
            [('bar_a', 3), (False, 2)],
        )
        RelatedBase._read_group([], ['foo_id_bar_name'], ['__count'])
        RelatedBase._read_group([], ['foo_id_bar_name_sudo'], ['__count'])

        self.assertEqual(
            RelatedBase._read_group([], aggregates=['foo_id_bar_id_name:count_distinct']),
            [(1,)],
        )

        # Cannot groupby on foo_names_sudo because it traverse One2many
        with self.assertRaises(ValueError):
            RelatedBar._read_group([], ['foo_names_sudo'])

    def test_inherited(self):
        RelatedBase = self.env['test_read_group.related_base']
        RelatedInherits = self.env['test_read_group.related_inherits']

        bases = RelatedBase.create([
            {'name': 'a', 'value': 1},
            {'name': 'a', 'value': 2},
            {'name': 'b', 'value': 3},
            {'name': False, 'value': 4},
        ])
        RelatedInherits.create([
            {'base_id': bases[0].id},
            {'base_id': bases[0].id},
            {'base_id': bases[1].id},
            {'base_id': bases[2].id},
            {'base_id': bases[3].id},
        ])

        # env.su => false
        RelatedInherits = RelatedInherits.with_user(self.base_user)

        field_info = RelatedInherits.fields_get(
            ['name', 'foo_id_name', 'foo_id_name_sudo', 'value'],
            ['groupable', 'aggregator'],
        )
        self.assertTrue(field_info['name']['groupable'])
        self.assertTrue(field_info['foo_id_name']['groupable'])
        self.assertTrue(field_info['foo_id_name_sudo']['groupable'])
        self.assertEqual(field_info['value']['aggregator'], 'sum')

        # warmup
        RelatedInherits._read_group([], ['name'], ['__count'])
        self.assertEqual(
            RelatedInherits._read_group([], ['name'], ['__count']),
            [('a', 3), ('b', 1), (False, 1)],
        )

        self.assertEqual(
            RelatedInherits._read_group([], ['name'], ['value:sum']),
            [('a', 1 + 1 + 2), ('b', 3), (False, 4)],
        )

        # warmup
        RelatedInherits._read_group([], ['foo_id_name'], ['__count'])
        RelatedInherits._read_group([], ['foo_id_name_sudo'], ['__count'])
        RelatedInherits._read_group([], ['foo_id_name'], ['__count'])  # warmup
        self.assertEqual(
            RelatedInherits._read_group([], ['foo_id_name'], ['__count']),
            [(False, 5)],
        )
        self.assertEqual(
            RelatedInherits._read_group([], ['foo_id_name_sudo'], ['__count']),
            [(False, 5)],
        )

    def test_related_many2many_groupby(self):
        RelatedFoo = self.env['test_read_group.related_foo'].with_user(self.base_user)

        # warmup
        RelatedFoo._read_group([], ['bar_base_ids'], ['__count'])
        RelatedFoo._read_group([], ['bar_base_ids'], ['__count'])

        field_info = RelatedFoo.fields_get(['bar_base_ids'], ['groupable'])
        self.assertTrue(field_info['bar_base_ids']['groupable'])

        # With access domain on the comodel of the many2many
        access = self.env.ref('test_base.access_test_read_group_related_base')
        access.domain = "[('id', '=', 161)]"

        # warmup
        RelatedFoo._read_group([], ['bar_base_ids'], ['__count'])
        # The related_sudo=True should not bypass ir_rule of the comodel
        RelatedFoo._read_group([], ['bar_base_ids'], ['__count'])

        # Test chain of fields have the same result than the related one (no ir.rule)
        self.assertEqual(
            RelatedFoo._read_group([], ['bar_base_ids'], ['__count']),
            RelatedFoo._read_group([], ['bar_id.base_ids'], ['__count']),
        )

    def test_groupby_chain_fnames_many2one(self):
        RelatedBar = self.env['test_read_group.related_bar']
        RelatedFoo = self.env['test_read_group.related_foo']
        RelatedBase = self.env['test_read_group.related_base']

        bars = RelatedBar.create([
            {'name': 'bar_a'},
            {'name': False},
        ])

        foos = RelatedFoo.create([
            {'name': 'foo_a_bar_a', 'bar_id': bars[0].id},
            {'name': 'foo_b_bar_false', 'bar_id': bars[1].id},
            {'name': False, 'bar_id': bars[0].id},
            {'name': False},
        ])

        RelatedBase.create([
            {'name': 'base_foo_a_1', 'foo_id': foos[0].id},
            {'name': 'base_foo_a_2', 'foo_id': foos[0].id},
            {'name': 'base_foo_b_bar_false', 'foo_id': foos[1].id},
            {'name': 'base_false_foo_bar_a', 'foo_id': foos[2].id},
            {'name': 'base_false_foo', 'foo_id': foos[3].id},
        ])

        # warmup ormcache
        RelatedBase._read_group([], ['foo_id.bar_id'], ['__count'])

        self.assertEqual(
            RelatedBase._read_group([], ['foo_id.bar_id'], ['__count']),
            [(bars[0], 3), (bars[1], 1), (RelatedBar, 1)],
        )

        # Test without sudo but without ir_rules
        RelatedBase = RelatedBase.with_user(self.base_user)

        # warmup ormcache
        RelatedBase._read_group([], ['foo_id.bar_id'], ['__count'])

        self.assertEqual(
            RelatedBase._read_group([], ['foo_id.bar_id'], ['__count']),
            [(bars[0], 3), (bars[1], 1), (RelatedBar, 1)],
        )

        # Test without sudo + ir_rules
        users_model = self.env['ir.model']._get(RelatedFoo._name)
        self.env['ir.access'].create({
            'name': "Only The Lone Wanderer allowed",
            'model_id': users_model.id,
            'operation': 'crud',
            'domain': [('id', 'in', foos[1:].ids)],
        })
        RelatedBase = RelatedBase.with_user(self.base_user)

        # warmup ormcache
        RelatedBase._read_group([], ['foo_id.bar_id'], ['__count'])

        self.assertEqual(
            RelatedBase._read_group([], ['foo_id.bar_id'], ['__count']),
            [(bars[0], 1), (bars[1], 1), (RelatedBar, 3)],
        )

    def test_groupby_chain_fnames_char(self):
        RelatedBar = self.env['test_read_group.related_bar']
        RelatedFoo = self.env['test_read_group.related_foo']
        RelatedBase = self.env['test_read_group.related_base']

        bars = RelatedBar.create([
            {'name': 'bar_a'},
            {'name': False},
        ])

        foos = RelatedFoo.create([
            {'name': 'foo_a_bar_a', 'bar_id': bars[0].id},
            {'name': 'foo_b_bar_false', 'bar_id': bars[1].id},
            {'name': False, 'bar_id': bars[0].id},
            {'name': False},
        ])

        RelatedBase.create([
            {'name': 'base_foo_a_1', 'foo_id': foos[0].id},
            {'name': 'base_foo_a_2', 'foo_id': foos[0].id},
            {'name': 'base_foo_b_bar_false', 'foo_id': foos[1].id},
            {'name': 'base_false_foo_bar_a', 'foo_id': foos[2].id},
            {'name': 'base_false_foo', 'foo_id': foos[3].id},
        ])

        # Warmup ormcache
        RelatedBase._read_group([], ['foo_id.bar_id.name'], ['__count'])

        # Same query generated by grouping foo_id.bar_id.name/foo_id.bar_name/foo_id.bar_name_sudo
        for fname_chain in ['foo_id.bar_id.name', 'foo_id.bar_name_sudo', 'foo_id.bar_name']:
            self.assertEqual(
                RelatedBase._read_group([], [fname_chain], ['__count']),
                [('bar_a', 3), (False, 2)],
            )

        # Cannot groupby on foo_ids.name because it traverse One2many
        with self.assertRaises(ValueError):
            RelatedBar._read_group([], ['foo_ids.name'])

        # Test without sudo but without ir_rules
        RelatedBase = RelatedBase.with_user(self.base_user)

        # Warmup ormcache
        RelatedBase._read_group([], ['foo_id.bar_id.name'], ['__count'])

        # Same query generated by grouping foo_id.bar_id.name/foo_id.bar_name_sudo
        # and foo_id.bar_name (unsudoed, but no record rules)
        for fname_chain in ['foo_id.bar_id.name', 'foo_id.bar_name_sudo', 'foo_id.bar_name']:
            self.assertEqual(
                RelatedBase._read_group([], [fname_chain], ['__count']),
                [('bar_a', 3), (False, 2)],
            )

        # Test without sudo + ir_rules
        users_model = self.env['ir.model']._get(RelatedFoo._name)
        self.env['ir.access'].create({
            'name': "Only The Lone Wanderer allowed",
            'model_id': users_model.id,
            'operation': 'crud',
            'domain': [('id', 'in', foos[1:].ids)],
        })

        # Warmup ormcache
        RelatedBase._read_group([], ['foo_id.bar_id.name'], ['__count'])

        for fname_chain in ['foo_id.bar_id.name', 'foo_id.bar_name_sudo']:
            # foos[0] not accessible, then bar_a is only exist via foos[2]
            self.assertEqual(
                RelatedBase._read_group([], [fname_chain], ['__count']),
                [('bar_a', 1), (False, 4)],
            )


@neutral
class TestPublicReadGroupNeutral(TestPublicReadGroup, NeutralCase):
    allow_inherited_tests_method = True


# test_properties.py
@neutral
class TestPropertiesCaseNeutral(PropertiesCase, NeutralCase):
    allow_inherited_tests_method = True

    # the two helpers of TestPropertiesMixin read the stored JSON with a raw
    # SELECT; here they return the value the ORM fetched for the field after
    # its cache was dropped, which is the stored value in cache format
    def _get_sql_properties(self, message):
        self.env.flush_all()
        message.invalidate_recordset(['attributes'])
        message.fetch(['attributes'])
        return message._cache['attributes']

    def _get_sql_definition(self, discussion):
        self.env.flush_all()
        discussion.invalidate_recordset(['attributes_definition'])
        discussion.fetch(['attributes_definition'])
        value = discussion._cache['attributes_definition']
        self.assertTrue(value)
        return value

    test_properties_field_many2one_model_removed = None  # left out: writes an invalid definition behind the ORM with a raw UPDATE
    test_properties_field_domain = None  # left out: writes an invalid domain behind the ORM with a raw UPDATE
    test_properties_field_many2many_basic = None  # left out: writes duplicated ids behind the ORM with a raw UPDATE

    def test_base_properties_model_access(self):
        with self.assertRaises(AccessError):
            self.env['test_orm.properties'].with_user(self.test_user).create({
                'name': 'test', 'properties': [{'name': 'test', 'type': 'char', 'definition_changed': True}]})

        definition_record = self.env['properties.base.definition']._get_definition_for_property_field('test_orm.properties', 'properties')
        self.assertEqual(definition_record.properties_definition, [])

        field = self.env["ir.model.fields"].sudo()._get('test_orm.emailmessage', 'properties')
        with self.assertIntegrityError():
            self.env['properties.base.definition'].create({'properties_field_id': field.id})

        with self.assertRaises(AccessError):
            # Even in SUDO, we can not change the field
            definition_record.sudo().properties_field_id = field.id

        with self.assertRaises(AccessError):
            definition_record.with_user(self.test_user).unlink()

        record_0 = self.env['test_orm.properties'].create([{'properties': [{'name': 'test', 'type': 'char', 'definition_changed': True, 'value': 'test'}], 'name': 'test'}, {'name': 'test'}])[0]
        self.assertEqual(record_0.properties_base_definition_id, definition_record)
        self.assertEqual(definition_record.properties_definition, [{'name': 'test', 'type': 'char'}])

        record_2 = self.env['test_orm.emailmessage'].create([{}, {}])[0]
        record_2.write({'properties': [{'name': 'test_2', 'type': 'char', 'definition_changed': True, 'value': 'test'}]})
        self.assertNotEqual(definition_record, record_2.properties_base_definition_id)
        self.assertEqual(record_2.properties_base_definition_id.properties_definition, [{'name': 'test_2', 'type': 'char'}])
        self.assertEqual(definition_record.properties_definition, [{'name': 'test', 'type': 'char'}])

        with self.assertRaises(AccessError):
            self.env['test_orm.properties'].with_user(self.test_user).create({
                'name': 'test', 'properties': [{'name': 'test', 'type': 'char', 'definition_deleted': True}]})

    @mute_logger('odoo.models.unlink', 'odoo.fields')
    def test_properties_field_read_batch(self):
        values = self.message_1.read(['attributes'])[0]['attributes']
        self.assertEqual(len(values), 2)
        self.assertEqual(values[0]['type'], 'char')
        self.assertEqual(values[1]['type'], 'many2one')

        self.message_2.attributes = [{
            'name': 'discussion_color_code',
            'type': 'char',
            'string': 'Color Code',
            'default': 'blue',
            'value': 'Test',
        }, {
            'name': 'moderator_partner_id',
            'type': 'many2one',
            'string': 'Partner',
            'comodel': 'test_orm.partner',
            'value': (self.partner_2.id, "Bob"),
        }]

        self.env.invalidate_all()
        self.message_1.read(['attributes'])

        # read in batch a lot of records
        discussions = [self.discussion_1, self.discussion_2]
        partners = self.env['test_orm.partner'].create([{'name': f'Test {i}'} for i in range(50)])
        messages = self.env['test_orm.message'].create([{
            'name': f'Test Message {i}',
            'discussion': discussions[i % 2].id,
            'author': self.user.id,
            'attributes': [{
                'name': 'partner_id',
                'type': 'many2one',
                'comodel': 'test_orm.partner',
                'value': partner.id,
                'definition_changed': True,
            }],
        } for i, partner in enumerate(partners)])

        self.env.invalidate_all()

        values = messages.read(['attributes'])

        # remove some partners in the list
        partners[:20].unlink()
        self.env.invalidate_all()
        # 5 queries instead of 25 queries, thanks to the cache values that has been
        # cleaned (the properties field can trust the cached value, the deleted ids
        # are not in the cache even if they still exists in the database)
        values = messages.read(['attributes'])

    @mute_logger('odoo.fields')
    def test_properties_field_create_batch(self):
        # first create to cache the access rights
        self.env['test_orm.message'].create({'name': 'test'})

        messages = self.env['test_orm.message'].create([{
            'name': 'Test Message',
            'discussion': False,
            'author': self.user.id,
        }, {
            'name': 'Test Message',
            'discussion': False,
            'author': self.user.id,
        }])

        self.env.invalidate_all()
        messages = self.env['test_orm.message'].create([{
            'name': 'Test Message',
            'discussion': self.discussion_1.id,
            'author': self.user.id,
            'attributes': [{
                # no name, should be automatically generated
                'string': 'Discussion Color code',
                'type': 'char',
                'default': 'blue',
                'value': 'purple',
                'definition_changed': True,
            }, {
                # the name is already set and shouldn't be re-generated
                'name': 'moderator_partner_id',
                'string': 'Partner',
                'type': 'many2one',
                'comodel': 'test_orm.partner',
                'value': self.partner.id,
                'definition_changed': True,
            }],
        }, {
            'name': 'Test Message',
            'discussion': self.discussion_2.id,
            'author': self.user.id,
            'attributes': [{
                'type': 'selection',
                'string': 'Status',
                'selection': [
                    ('draft', 'Draft'),
                    ('progress', 'In Progress'),
                    ('done', 'Done'),
                ],
                'default': 'draft',
                'definition_changed': True,
            }],
        }])

        self.env.invalidate_all()
        sql_definition = self._get_sql_definition(self.discussion_1)
        self.assertEqual(len(sql_definition), 2)

        # check the generated name
        property_color_name = sql_definition[0]['name']
        self.assertTrue(property_color_name, msg="Property name must have been generated")

        self.assertEqual(sql_definition, [
            {
                'name': property_color_name,
                'default': 'blue',
                'string': 'Discussion Color code',
                'type': 'char',
            }, {
                'name': 'moderator_partner_id',
                'type': 'many2one',
                'comodel': 'test_orm.partner',
                'string': 'Partner',
            },
        ])

        self.assertEqual(
            self.discussion_1.attributes_definition[0]['string'], 'Discussion Color code',
            msg='Should have updated the definition record')

        self.assertEqual(len(messages), 2)

        sql_properties_1 = self._get_sql_properties(messages[0])
        self.assertEqual(
            sql_properties_1,
            {'moderator_partner_id': self.partner.id,
             property_color_name: 'purple'})
        sql_properties_2 = self._get_sql_properties(messages[1])
        status_name = self.discussion_2.attributes_definition[0]['name']
        self.assertEqual(
            sql_properties_2,
            {status_name: 'draft'})

        properties_values_1 = messages[0].attributes
        properties_values_2 = messages[1].attributes

        self.assertEqual(len(properties_values_1), 2, msg='Discussion 1 has 2 properties')
        self.assertEqual(len(properties_values_2), 1, msg='Discussion 2 has 1 property')

        self.assertEqual(properties_values_1, {
            'moderator_partner_id': self.partner.id,
            property_color_name: 'purple',
        })
        self.assertEqual(properties_values_2, {status_name: 'draft'},
                         msg='Should have taken the default value')

    @mute_logger('odoo.models.unlink', 'odoo.fields')
    def test_properties_field_many2one_unlink(self):
        """Test the case where we unlink the many2one record."""
        self.message_2.attributes = [{
            'name': 'moderator_partner_id',
            'value': self.partner.id,
        }]

        # remove the partner on message 2
        self.partner.unlink()
        self.assertIs(self.message_2.read(['attributes'])[0]['attributes'][0].get('value'), None)

        # remove the partner, and use the read method
        self.message_2.attributes = [{
            'name': 'moderator_partner_id',
            'value': self.partner_2.id,
        }]
        self.partner_2.unlink()

        value = self.message_2.read(['attributes'])
        value = value[0]['attributes']
        self.assertFalse(value[1]['value'])
        self.assertEqual(value[1]['comodel'], 'test_orm.partner')

        # many2one properties in a default value
        partner = self.env['test_orm.partner'].create({'name': 'test unlink'})
        self.message_2.attributes = [{
            'name': 'moderator_partner_id',
            'type': 'many2one',
            'comodel': 'test_orm.partner',
            'default': [partner.id, 'Bob'],
            'definition_changed': True,
        }]
        self.assertEqual(
            self.message_2.read(['attributes'])[0]['attributes'],
            [{
                'name': 'moderator_partner_id',
                'type': 'many2one',
                'comodel': 'test_orm.partner',
                'default': (partner.id, partner.display_name),
            }],
        )
        partner.unlink()
        self.assertEqual(
            self.message_2.read(['attributes'])[0]['attributes'],
            [{
                'name': 'moderator_partner_id',
                'type': 'many2one',
                'comodel': 'test_orm.partner',
                'default': False,
            }],
        )

    def test_properties_field_performance(self):
        self.env.invalidate_all()
        self.message_1.read(['attributes'])

        self.message_1.attributes

        self.message_1.attributes = [
            {
                "name": "discussion_color_code",
                "type": "char",
                "string": "Color Code",
                "default": "blue",
                "value": "red",
            },
            {
                "name": "moderator_partner_id",
                "type": "many2one",
                "string": "Partner",
                "comodel": "test_orm.partner",
                "value": None,
            },
        ]
        self.message_1.flush_recordset()

        last_message_id = self.env['test_orm.message'].search([], order="id DESC", limit=1).id
        # based on batch optimization, _read_format should not crash on non existing records
        values = self.env['test_orm.message'].browse((self.message_1.id, last_message_id + 1))._read_format(['attributes'])
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['id'], self.message_1.id)

    def test_getitem_property(self):
        # read a property that exist nowhere
        with self.assertRaises(KeyError):
            self.message_3['attributes']['____']

        # read a property that exists, but on the wrong record
        with self.assertRaises(KeyError):
            self.message_3['attributes']['moderator_partner_id']

        # read many types
        self.assertEqual(self.message_1['attributes']['discussion_color_code'], 'Test')
        self.assertEqual(self.message_1['attributes']['moderator_partner_id'], self.partner)

        self.assertEqual(self.message_2['attributes']['discussion_color_code'], 'blue')
        self.assertEqual(self.message_2['attributes']['moderator_partner_id'], self.env['test_orm.partner'])

        with self.assertRaises(KeyError):
            self.message_1['attributes']['state']
        with self.assertRaises(KeyError):
            self.message_2['attributes']['state']
        self.assertEqual(self.message_3['attributes']['state'], 'draft')
        self.assertEqual(self.message_3.with_context(property_selection_get_label=True)['attributes']['state'], 'Draft')

        self.message_1.attributes = [{
            'name': 'tags',
            'type': 'tags',
            'tags': [['a', 'A', 0], ['b', 'B', 1], ['c', 'C', 2]],
            'value': ['a', 'b', 'e'],
            'definition_changed': True,
        }]
        self.assertEqual(self.message_1['attributes']['tags'], 'A, B')
        self.assertEqual(self.message_2['attributes']['tags'], False)
        with self.assertRaises(KeyError):
            self.message_3['attributes']['tags']

        self.message_1.attributes = [{
            'name': 'many2many',
            'type': 'many2many',
            'comodel': 'test_orm.partner',
            'value': (self.partner | self.partner_2).ids,
            'definition_changed': True,
        }]
        self.assertEqual(self.message_1['attributes']['many2many'], self.partner | self.partner_2)
        self.assertEqual(self.message_2['attributes']['many2many'], self.env['test_orm.partner'])
        with self.assertRaises(KeyError):
            self.message_3['attributes']['many2many']

        self.message_1.attributes = [{
            # no comodel
            'name': 'many2many',
            'type': 'many2many',
            'value': (self.partner | self.partner_2).ids,
            'definition_changed': True,
        }]
        self.assertEqual(self.message_1['attributes']['many2many'], False)
        self.assertEqual(self.message_2['attributes']['many2many'], False)
        with self.assertRaises(KeyError):
            self.message_3['attributes']['many2many']

        # call __getitem__ on an empty recordset
        self.assertEqual(self.env['test_orm.message']['attributes']['many2many'], False)

        # Test the prefetch on the returned records
        partner_3 = self.env['test_orm.partner'].create({'name': 'bob'})
        self.message_1.attributes = [{
            'name': 'many2many',
            'comodel': 'test_orm.partner',
            'type': 'many2many',
            'value': self.partner.ids,
            'default': partner_3.ids,
            'definition_changed': True,
        }]
        self.message_2['attributes'] = [{
            'name': 'many2many',
            'comodel': 'test_orm.partner',
            'type': 'many2many',
            'value': self.partner_2.ids,
        }]
        messages = self.message_1 | self.message_2 | self.message_3
        self.env.invalidate_all()

        messages[0]['attributes']['many2many']
        messages[1]['attributes']['many2many']


@neutral
class TestPropertiesSearchCaseNeutral(PropertiesSearchCase, NeutralCase):
    allow_inherited_tests_method = True

    _get_sql_properties = TestPropertiesCaseNeutral._get_sql_properties
    _get_sql_definition = TestPropertiesCaseNeutral._get_sql_definition

    test_properties_field_search_char = None  # left out: sets the stored value to an empty / NULL document with a raw UPDATE
    test_properties_field_search_unaccent = None  # left out: branches on the backend's unaccent feature (registry.has_unaccent)

    def test_properties_field_search_order_injection(self):
        """Check the restriction on the property name."""
        self.message_1.attributes = [{
            'name': 'myinteger',
            'type': 'integer',
            'value': 22,
            'definition_changed': True,
        }]

        for c in '! ()"\'.':
            orders = (
                f'attributes.myinteger{c} ASC',
                f'attributes.my{c}integer ASC',
                f'attribut{c}es.myinteger ASC',
            )

            if c == ' ':
                # allow multiple spaces after the property name
                orders = orders[1:]

            for order in orders:
                with self.assertRaises(UserError):
                    self.env['test_orm.message'].search(domain=[], order=order)


# test_models.py
@neutral
class TestORMNeutral(TestORM, NeutralCase):
    allow_inherited_tests_method = True

    def test_exists(self):
        partner = self.env['test_orm.partner']
        partner.create({'name': 'MyPartner1'})

        # check that records obtained from search exist
        recs = partner.search([])
        self.assertTrue(recs)
        self.assertEqual(recs.exists(), recs)

        # check that new records exist by convention
        recs = partner.new({})
        self.assertTrue(recs.exists())

        # check that there is no record with id -1
        # (it is technically valid, but should not exist)
        recs = partner.browse([-1])
        self.assertFalse(recs.exists())

    # test_lock_for_update / test_try_lock_for_update: the second transaction
    # is `concurrent_session()` instead of `self.env.registry.cursor()`
    def test_lock_for_update(self):
        partner = self.env['test_orm.partner']
        p1, p2 = partner.search([], limit=2)

        # lock p1
        p1.lock_for_update(allow_referencing=True)
        p1.lock_for_update(allow_referencing=False)

        with self.concurrent_session() as other:
            recs = (p1 + p2).with_env(other.env)
            with self.assertRaises(LockError):
                recs.lock_for_update()
            sub_p2 = recs[1]
            sub_p2.lock_for_update()

            # parent transaction and read, but cannot lock the p2 records
            p2.invalidate_model()
            self.assertTrue(p2.name)
            with self.assertRaises(LockError):
                p2.lock_for_update()

            # can still read from parent after locks and lock failures
            p1.invalidate_model()
            self.assertTrue(p1.name)

        # can lock p2 now
        p2.lock_for_update()

        # cannot lock inexisting record
        inexisting = partner.create({'name': 'inexisting'})
        inexisting.unlink()
        self.assertFalse(inexisting.exists())
        with self.assertRaises(LockError):
            inexisting.lock_for_update()

    def test_try_lock_for_update(self):
        partner = self.env['test_orm.partner']
        p1, p2, *_other = recs = partner.search([], limit=4)

        # lock p1
        self.assertEqual(p1.try_lock_for_update(allow_referencing=True), p1)
        self.assertEqual(p1.try_lock_for_update(allow_referencing=False), p1)

        with self.concurrent_session() as other:
            sub_recs = (p1 + p2).with_env(other.env)
            self.assertEqual(sub_recs.try_lock_for_update(), sub_recs[1])

        self.assertEqual(recs.try_lock_for_update(limit=1), p1)
        self.assertEqual(recs.try_lock_for_update(), recs)

        # check that order is preserved when limiting
        self.assertEqual(recs[::-1].try_lock_for_update(limit=1), recs[-1])


@neutral
class TestRecordsetNeutral(TestRecordset, NeutralCase):
    allow_inherited_tests_method = True

    def check_cache_consistency(self):
        """ Compare the cached values of stored column fields with the values
        the backend holds, read back with `_read_group` (upstream runs one
        SELECT per field). Fields whose cache depends on the context are not
        compared. """
        env = self.env
        invalids = []
        for field, field_cache in list(env.transaction.field_data.items()):
            # check column fields only
            if not field.store or not field.column_type or field.translate or field.company_dependent:
                continue
            if field._depends_context:
                continue
            # ignore new records and records to flush
            dirty_ids = env.transaction.field_dirty.get(field, ())
            ids = [id_ for id_ in field_cache if id_ and id_ not in dirty_ids]
            if not ids:
                continue
            model = env[field.model_name]
            fetched = model._read_group([('id', 'in', ids)], ['id'], [f'{field.name}:array_agg'])
            for record, [value] in fetched:
                cached = field_cache[record.id]
                if value == cached or (not value and not cached):
                    continue
                invalids.append((record, field, {'cached': cached, 'fetched': value}))
        self.assertFalse(invalids)

    def test_recordset_grouped(self):
        partners = self.partners
        partners[0].email = '@guest.com'
        partners[1].email = '@host.com'
        partners[2].email = '@guest.com'

        partners_grouped = partners.grouped('email')
        self.assertEqual(partners_grouped['@guest.com'].mapped('name'), ['Inner Works', 'AnalytIQ'])

        _ = partners_grouped['@host.com'].name

    @mute_logger('odoo.models')
    @mute_logger('odoo.addons.base.models.ir_model')
    def test_recordset_environment(self):
        partners = self.partners.filtered_domain([('name', 'ilike', 'j')])
        self.assertTrue(partners)

        # Partners and reachable records are attached to self.env
        self.assertEqual(partners.env, self.env)
        for record in (partners, partners[0], partners[0].country_id):
            self.assertEqual(record.env, self.env)
        for partner in partners:
            self.assertEqual(partner.env, self.env)

        # Create a new environment
        demo = self.env['res.users'].create({
            'name': 'test_environment_demo',
            'login': 'test_environment_demo',
            'password': 'test_environment_demo',
        })
        # the combined addon installs mail, whose `with_user` override adds a
        # context key: build the expected environment the same way
        demo_env = self.env['base'].with_user(demo).env
        self.assertNotEqual(demo_env, self.env)

        # Partners and reachable records are still attached to self.env
        self.assertEqual(partners.env, self.env)
        for record in (partners, partners[0], partners[0].country_id):
            self.assertEqual(record.env, self.env)
        for partner in partners:
            self.assertEqual(partner.env, self.env)

        # Create record instances attached to demo_env
        demo_partners = partners.with_user(demo)
        self.assertEqual(demo_partners.env, demo_env)
        for x in (demo_partners, demo_partners[0], demo_partners[0].country_id):
            self.assertEqual(x.env, demo_env)
        for p in demo_partners:
            self.assertEqual(p.env, demo_env)
