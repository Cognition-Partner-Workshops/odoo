""" ``core.reuse_with_edits``: classes of ``test_base/tests/test_orm`` whose
only backend-specific lines are ``assertQueryCount`` / ``assertQueries``
guards, a raw SQL cross-check or a registry access.

Each class subclasses the upstream one on ``NeutralCase`` with
``allow_inherited_tests_method = True`` (see ``test_core_reuse_as_is.py``).
The methods that the neutral lint flags upstream are overridden here with a
copy whose query guard is removed and whose behavioural assertions are kept,
or set to ``None`` (not collected) when nothing but the guard remains; the
reason is next to each one. ``type(self.env[model])`` replaces
``self.registry[model]`` to patch a model class.
"""
from itertools import combinations
from unittest.mock import patch

from odoo import Command
from odoo.fields import Domain
from odoo.tests.common import tagged
from odoo.tools import OrderedSet

from odoo.addons.test_backend_neutral.harness import NEUTRAL_TAG, NeutralCase
from odoo.addons.test_base.tests.test_orm.test_access_feedback import (
    TestACLFeedback,
    TestFieldGroupFeedback,
    TestIRRuleFeedback,
    TestSudo,
)
from odoo.addons.test_base.tests.test_orm.test_company_checks import TestCompanyCheck
from odoo.addons.test_base.tests.test_orm.test_domain import TestDomain, TestDomainComplement, TestDomainOptimize
from odoo.addons.test_base.tests.test_orm.test_inherits import TestInherits, test_inherits
from odoo.addons.test_base.tests.test_orm.test_ir_rules import TestRules
from odoo.addons.test_base.tests.test_orm.test_many2many import Many2manyCase
from odoo.addons.test_base.tests.test_orm.test_one2many import One2manyCase
from odoo.addons.test_base.tests.test_orm.test_parent_store import TestParentStore
from odoo.addons.test_base.tests.test_orm.test_search_order import TestSearch as TestSearchOrder
from odoo.addons.test_base.tests.test_orm.test_sort import TestSort

neutral = tagged(NEUTRAL_TAG, 'post_install', '-at_install')


# test_domain.py
@neutral
class TestDomainNeutral(TestDomain, NeutralCase):
    allow_inherited_tests_method = True

    # test_empty_int / test_empty_char: the raw SELECT of the stored column is
    # dropped, the searches and reads next to it are kept
    def test_empty_int(self):
        EmptyInt = self.env['test_orm.empty_int']
        records = EmptyInt.create([
            {'number': 42},     # stored as 42
            {'number': 0},      # stored as 0
            {'number': False},  # stored as 0
            {},                 # stored as NULL
        ])
        # check read (NULL is returned as 0)
        self.assertListEqual(records.mapped('number'), [42, 0, 0, 0])

        self.env.flush_all()

        self.assertListEqual(self._search(EmptyInt, [('number', '=', 42)]).mapped('number'), [42])
        self.assertListEqual(self._search(EmptyInt, [('number', '!=', 42)]).mapped('number'), [0, 0, 0])

        self.assertListEqual(self._search(EmptyInt, [('number', '=', 0)]).mapped('number'), [0, 0, 0])
        self.assertListEqual(self._search(EmptyInt, [('number', '!=', 0)]).mapped('number'), [42])

        self.assertListEqual(self._search(EmptyInt, [('number', '=', False)]).mapped('number'), [0, 0, 0])
        self.assertListEqual(self._search(EmptyInt, [('number', '!=', False)]).mapped('number'), [42])

        self.assertListEqual(self._search(EmptyInt, [('number', '<', 1)]).mapped('number'), [0, 0, 0])
        self.assertListEqual(self._search(EmptyInt, [('number', '>', -1)]).mapped('number'), [42, 0, 0, 0])
        self.assertListEqual(self._search(EmptyInt, [('number', '<=', 0)]).mapped('number'), [0, 0, 0])
        self.assertListEqual(self._search(EmptyInt, [('number', '>=', 0)]).mapped('number'), [42, 0, 0, 0])
        self.assertListEqual(self._search(EmptyInt, [('number', '>', 1)]).mapped('number'), [42])
        self.assertListEqual(self._search(EmptyInt, [('number', '<', -1)]).mapped('number'), [])

        # check ('number', 'in', subset) for every subset of {42, 0, False}
        values = [42, 0, False]
        for length in range(len(values) + 1):
            for subset in combinations(values, length):
                self.assertEqual(
                    self._search(EmptyInt, [('number', 'in', list(subset))]),
                    records.filtered(lambda record: record.number in subset),
                    f"Incorrect result for search([('number', 'in', {sorted(subset)})])",
                )
                self.assertEqual(
                    self._search(EmptyInt, [('number', 'not in', list(subset))]),
                    records.filtered(lambda record: record.number not in subset),
                    f"Incorrect result for search([('number', 'not in', {sorted(subset)})])",
                )

    def test_empty_char(self):
        EmptyChar = self.env['test_orm.empty_char']
        records = EmptyChar.create([
            {'name': 'name'},
            {'name': ''},      # stored as ''
            {'name': False},   # stored as null (explicitly asked)
            {},                # stored as null
        ])
        # check read
        self.assertListEqual(records.mapped('name'), ['name', '', False, False])

        self.env.flush_all()

        self.assertListEqual(self._search(EmptyChar, [('name', '=', 'name')]).mapped('name'), ['name'])
        self.assertListEqual(self._search(EmptyChar, [('name', '!=', 'name')]).mapped('name'), ['', False, False])
        self.assertListEqual(self._search(EmptyChar, [('name', 'ilike', 'name')]).mapped('name'), ['name'])
        self.assertListEqual(self._search(EmptyChar, [('name', 'not ilike', 'name')]).mapped('name'), ['', False, False])

        self.assertListEqual(self._search(EmptyChar, [('name', '=', '')]).mapped('name'), ['', False, False])
        self.assertListEqual(self._search(EmptyChar, [('name', '!=', '')]).mapped('name'), ['name'])
        self.assertListEqual(self._search(EmptyChar, [('name', 'ilike', '')]).mapped('name'), ['name', '', False, False])
        self.assertListEqual(self._search(EmptyChar, [('name', 'not ilike', '')]).mapped('name'), [])

        self.assertListEqual(self._search(EmptyChar, [('name', '=', False)]).mapped('name'), ['', False, False])
        self.assertListEqual(self._search(EmptyChar, [('name', '!=', False)]).mapped('name'), ['name'])
        self.assertListEqual(self._search(EmptyChar, [('name', 'ilike', False)]).mapped('name'), ['name', '', False, False])
        self.assertListEqual(self._search(EmptyChar, [('name', 'not ilike', False)]).mapped('name'), [])

        values = ['name', '', False]
        for length in range(len(values) + 1):
            for subset in combinations(values, length):
                # check against a subset containg both values for empty strings
                subset_check = set(subset)
                if {False, ""} & subset_check:
                    subset_check |= {False, ""}
                self.assertEqual(
                    self._search(EmptyChar, [('name', 'in', list(subset))]),
                    records.filtered(lambda record: record.name in subset_check),
                    f"Incorrect result for search([('name', 'in', {list(subset)})])",
                )
                self.assertEqual(
                    self._search(EmptyChar, [('name', 'not in', list(subset))]),
                    records.filtered(lambda record: record.name not in subset_check),
                    f"Incorrect result for search([('name', 'not in', {list(subset)})])",
                )

        # =like check
        self.assertListEqual(self._search(EmptyChar, [('name', '=like', 'na%')]).mapped('name'), ['name'])
        self.assertListEqual(self._search(EmptyChar, ['!', ('name', '=like', 'na%')]).mapped('name'), ['', False, False])

    def test_any_in_search_field(self):
        Message = type(self.env['test_orm.message'])
        model = self.env[Message._name]
        with patch.object(Message, '_search_author_partner', side_effect=Message._search_author_partner, autospec=True) as mock:
            # using _search_author_partner
            domain = Domain('author_partner', 'any', [('name', '=', 'demo')]).optimize_full(model)
            call_args = mock.call_args.args
            self.assertEqual(call_args[1], 'any')
            sub_domain = call_args[2]
            self.assertIsInstance(sub_domain, Domain)
            # (the check that the sub-domain value is a Query object is dropped)

            self.assertEqual(domain.field_expr, 'author')
            u_domain = domain.value
            self.assertEqual(u_domain.field_expr, 'partner_id')
            self.assertEqual(u_domain.operator, 'any!')
            self.assertIs(u_domain.value, sub_domain.value, "The query should be used as-is")


@neutral
class TestDomainComplementNeutral(TestDomainComplement, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestDomainOptimizeNeutral(TestDomainOptimize, NeutralCase):
    allow_inherited_tests_method = True

    # test_condition_methods: the `Domain.custom(to_sql=...)` case is dropped
    def test_condition_methods(self):
        dom = Domain.TRUE
        conditions = list(dom.iter_conditions())
        self.assertEqual(len(conditions), 0)
        self.assertFalse(dom.is_condition())

        dom = Domain('a', '>=', 1)
        conditions = list(dom.iter_conditions())
        self.assertEqual(len(conditions), 1)
        self.assertIs(conditions[0], dom)
        self.assertTrue(dom.is_condition())
        self.assertTrue(dom.is_condition('a', '>='))
        self.assertTrue(dom.is_condition(operator=('>=', 'in')))
        self.assertTrue(dom.is_condition(value=int))
        self.assertTrue(dom.is_condition(value=(int, float)))
        self.assertFalse(dom.is_condition('b', '>='))
        self.assertFalse(dom.is_condition(operator='='))
        self.assertFalse(dom.is_condition(value=str))

        dom = dom & Domain('b', '=', 1)
        conditions = list(dom.iter_conditions())
        self.assertEqual(len(conditions), 2)
        self.assertFalse(dom.is_condition())
        self.assertTrue(all(c.is_condition() for c in dom.iter_conditions()))

    def test_optimize_level_by_level(self):
        def search_foo(model, operator, value):
            # groups values to check that it is called once
            return [('name', '=', str(tuple(value)))]

        self.patch(type(self.env['test_orm.bar']), '_search_foo', search_foo)
        bar = self.env['test_orm.bar']
        domain = Domain('foo', '=', 4) | Domain('foo', '=', 5)
        domain = domain.optimize_full(bar)
        self.assertEqual(domain, Domain('name', 'in', OrderedSet(['(4, 5)'])))


# test_parent_store.py
@neutral
class TestParentStoreNeutral(TestParentStore, NeutralCase):
    allow_inherited_tests_method = True

    def test_missing_parent(self):
        """ Missing parent id should not raise an error. """
        # Missing parent with _parent_store
        new_cat0 = self.cat0.copy()
        records = new_cat0.search([('parent_id', 'parent_of', 999999999)])
        self.assertEqual(len(records), 0)

        # Missing parent without _parent_store
        category = self.env['test_orm.partner.category']
        self.patch(type(self.env['test_orm.partner.category']), '_parent_store', False)
        records = category.search([('parent_id', 'child_of', 999999999)])
        self.assertEqual(len(records), 0)

    def test_missing_child(self):
        """ Missing child id should not raise an error. """
        # Missing child with _parent_store
        new_cat0 = self.cat0.copy()
        records = new_cat0.search([('parent_id', 'child_of', 999999999)])
        self.assertEqual(len(records), 0)

        # Missing child without _parent_store
        category = self.env['test_orm.partner.category']
        self.patch(type(self.env['test_orm.partner.category']), '_parent_store', False)
        records = category.search([('parent_id', 'child_of', 999999999)])
        self.assertEqual(len(records), 0)


# test_many2many.py: no backend-specific line (`test_not_in_relation_as_query`
# passes the result of `_search` to a domain, an ORM-level value)
@neutral
class TestMany2manyCaseNeutral(Many2manyCase, NeutralCase):
    allow_inherited_tests_method = True


# test_one2many.py
@neutral
class TestOne2manyCaseNeutral(One2manyCase, NeutralCase):
    allow_inherited_tests_method = True

    def test_cache_invalidation(self):
        """ Cache invalidation for one2many with integer inverse. """
        record0 = self.env['test_orm.attachment.host'].create({})
        self.assertFalse(record0.attachment_ids, "inconsistent cache")

        # creating attachment must compute name and invalidate attachment_ids
        attachment = self.env['test_orm.attachment'].create({
            'res_model': record0._name,
            'res_id': record0.id,
        })
        self.env.flush_all()
        self.assertEqual(attachment.name, record0.display_name,
                         "field should be computed")
        self.assertEqual(record0.attachment_ids, attachment, "inconsistent cache")

        # creating a host should not attempt to recompute attachment.name
        record1 = self.env['test_orm.attachment.host'].create({})
        attachment.res_id
        self.assertFalse(record1.attachment_ids, "inconsistent cache")

        # writing on res_id must recompute name and invalidate attachment_ids
        attachment.res_id = record1.id
        self.env.flush_all()
        self.assertEqual(attachment.name, record1.display_name,
                         "field should be recomputed")
        self.assertEqual(record1.attachment_ids, attachment, "inconsistent cache")
        self.assertFalse(record0.attachment_ids, "inconsistent cache")

    def test_create_with_commands(self):
        # create lines and warm up caches
        order = self.env['test_orm.order'].create({
            'line_ids': [Command.create({'product': name}) for name in ('set', 'sept')],
        })
        line1, line2 = order.line_ids

        # INSERT, UPDATE of line1
        self.env['test_orm.order'].create({
            'line_ids': [Command.set(line1.ids)],
        })

        # INSERT order, INSERT thief, UPDATE of line1+line2
        order = self.env['test_orm.order'].create({
            'line_ids': [Command.set(line1.ids)],
        })
        thief = self.env['test_orm.order'].create({
            'line_ids': [Command.set((line1 + line2).ids)],
        })

        # the lines have been stolen by thief
        self.assertFalse(order.line_ids)
        self.assertEqual(thief.line_ids, line1 + line2)


# test_inherits.py
@neutral
class TestInheritsLegacyNeutral(test_inherits, NeutralCase):
    allow_inherited_tests_method = True

    test_access_rights_on_parent = None  # left out: its only assertion is the SQL text of the search (assertQueries)

    def test_display_name(self):
        """ Check the 'display_name' of an inherited translated 'name'. """
        self.env['res.lang']._activate_lang('fr_FR')

        # concrete check
        pallet_en = self.env['test.pallet'].create({'name': 'Bread'})
        pallet_fr = pallet_en.with_context(lang='fr_FR')
        pallet_fr.box_id.unit_id.name = 'Pain'
        self.assertEqual(pallet_en.display_name, 'Bread')
        self.assertEqual(pallet_fr.display_name, 'Pain')

        # check model (the registry's field_depends_context check is dropped)
        Unit = type(self.env['test.unit'])
        self.assertTrue(Unit.name.translate)



@neutral
class TestInheritsNeutral(TestInherits, NeutralCase):
    allow_inherited_tests_method = True


# test_ir_rules.py
@neutral
class TestRulesNeutral(TestRules, NeutralCase):
    allow_inherited_tests_method = True

    test_access_rule_performance = None  # left out: its only assertion is assertQueryCount(0)


# test_company_checks.py
@neutral
class TestCompanyCheckNeutral(TestCompanyCheck, NeutralCase):
    allow_inherited_tests_method = True

    # the query count is dropped, the check that _check_company runs once in batch is kept
    def test_check_company_write_performance(self):
        child = self.env['test_orm.model_child'].create({
            'name': 'M1',
            'company_id': self.company_b.id,
        })
        self.env.invalidate_all()

        ChildModel = type(self.env['test_orm.model_child'])
        _check_company = ChildModel._check_company  # noqa: RUF052
        with patch.object(ChildModel, '_check_company', autospec=True, side_effect=_check_company) as spy:
            child.parent_id = self.parent_b

        spy.assert_called_once_with(child, ['parent_id', 'write_uid', 'write_date'])


# test_search_order.py
@neutral
class TestSearchOrderNeutral(TestSearchOrder, NeutralCase):
    allow_inherited_tests_method = True

    def patch_order(self, model, order):
        self.patch(type(self.env[model]), '_order', order)

    test_22_like_folding = None  # left out: its only assertion is the SQL text of the search (assertQueries)


# test_sort.py
@neutral
class TestSortNeutral(TestSort, NeutralCase):
    allow_inherited_tests_method = True

    test_prefetch = None  # left out: its only assertion is a query count (prefetch of sorted records)

    def test_basic(self):
        db_result = self.env['test_orm.country'].search([])
        # 1 query to fetch the fields, in practice it is already prefetched
        self.countries.invalidate_model()
        self.assertEqual(db_result.ids, self.countries.sorted().ids)
        self.assertEqual(db_result[::-1].ids, self.countries.sorted(reverse=True).ids)
        self.assertEqual(
            self.countries.sorted().mapped('name'),
            ['A', 'B', 'C'],
        )

    def test_basic_m2o(self):
        db_result = self.env['test_orm.city'].search([])
        self.assertEqual(db_result.ids, self.cities.sorted().ids)
        self.assertEqual(db_result[::-1].ids, self.cities.sorted(reverse=True).ids)
        self.assertEqual(
            self.cities.sorted().mapped('name'),
            ['a1', 'a2', 'b1', 'b2', 'c1', 'c2'],
        )

    def test_basic_boolean(self):
        records = self.env['test_orm.model_active_field'].create([{'name': v} for v in 'abc'])
        records[1].active = False
        t_records = records.filtered('active')
        f_records = records - t_records
        records.sorted('active, name')
        self.assertEqual(f_records + t_records, records.sorted('active, name'))
        self.assertEqual(t_records + f_records, records.sorted('active DESC, name'))

    def test_custom_m2o(self):
        order = 'country_id DESC, id ASC'
        db_result = self.env['test_orm.city'].search([], order=order)
        self.assertEqual(db_result.ids, self.cities.sorted(order).ids)
        self.assertEqual(db_result[::-1].ids, self.cities.sorted(order, reverse=True).ids)
        self.assertEqual(
            self.cities.sorted(order).mapped('name'),
            ['c2', 'c1', 'b1', 'b2', 'a1', 'a2'],
        )


# test_access_feedback.py: no backend-specific line
@neutral
class TestSudoNeutral(TestSudo, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestACLFeedbackNeutral(TestACLFeedback, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestIRRuleFeedbackNeutral(TestIRRuleFeedback, NeutralCase):
    allow_inherited_tests_method = True


@neutral
class TestFieldGroupFeedbackNeutral(TestFieldGroupFeedback, NeutralCase):
    allow_inherited_tests_method = True
