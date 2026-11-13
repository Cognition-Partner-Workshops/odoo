""" Neutral tests of aggregation (``_read_group``, ``read_group``,
``formatted_read_group``), hierarchy (``child_of`` / ``parent_of`` /
``parent_path``) and text search semantics, on the targets of the
``aggregation_hierarchy`` category of ``backend_neutral_tests/sample.yaml``.

Every expected value is replayed in Python from the fixture data of the test
(``_group()`` and the hierarchy walkers below); none is copied from a
database output.
"""
from collections import Counter
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from odoo import Command
from odoo.tools import get_lang

from odoo.addons.test_backend_neutral.harness import NeutralCase
from odoo.addons.test_backend_neutral.harness.errors import UserError, ValidationError

UTC = ZoneInfo('UTC')


# ----------------------------------------------------------------------
# Python replays
# ----------------------------------------------------------------------

def _group(records, key):
    """ Return ``{key(record): recordset}`` for the given records, the
    recordsets in the order of ``records``. The key of a many2one is the
    target record, and an empty recordset for an empty value, like the
    groups of ``_read_group``. """
    groups = {}
    for record in records:
        groups[key(record)] = groups.get(key(record), records.browse()) + record
    return groups


def _typed(value):
    """ Key that keeps an integer group value distinct from the empty group,
    since ``0 == False`` in Python. """
    return (value is False, value)


def _as_dict(groups, nkeys=1):
    """ ``_read_group`` result as ``{group values: aggregate values}``. """
    result = {}
    for row in groups:
        keyValues = row[0] if nkeys == 1 else row[:nkeys]
        assert keyValues not in result, f"duplicated group {keyValues!r}"
        result[keyValues] = row[nkeys:]
    return result


def _descendants(record, parentField, universe):
    """ ``record`` and every record of ``universe`` below it, following
    ``parentField`` with a plain Python breadth-first walk. """
    result = frontier = record
    while frontier:
        frontier = universe.filtered(lambda r: r[parentField] in frontier) - result
        result = result | frontier
    return result


def _ancestors(record, parentField):
    """ The ancestors of ``record``, root first, then ``record`` itself. """
    chain = []
    while record:
        chain.insert(0, record)
        record = record[parentField]
    return chain


def _expected_parent_path(record, parentField):
    return ''.join(f'{node.id}/' for node in _ancestors(record, parentField))


def _week_start(env, day):
    """ First day of the week of ``day`` for the week start of the user's language. """
    firstWeekDay = int(get_lang(env).week_start)  # 1 = Monday ... 7 = Sunday
    return day - timedelta(days=(day.isoweekday() - firstWeekDay) % 7)


def _truncate(value, granularity, env):
    """ Python replay of the ``field:granularity`` groupby on a date or a
    (naive, UTC) datetime, in the timezone of the context when there is one. """
    isDatetime = isinstance(value, datetime)
    if isDatetime and (tz := env.context.get('tz')):
        value = value.replace(tzinfo=UTC).astimezone(ZoneInfo(tz)).replace(tzinfo=None)
    day = value.date() if isDatetime else value
    if granularity == 'hour':
        start = value.replace(minute=0, second=0, microsecond=0)
    elif granularity == 'day':
        start = day
    elif granularity == 'week':
        start = _week_start(env, day)
    elif granularity == 'month':
        start = day.replace(day=1)
    elif granularity == 'quarter':
        start = day.replace(month=3 * ((day.month - 1) // 3) + 1, day=1)
    elif granularity == 'year':
        start = day.replace(month=1, day=1)
    else:
        raise ValueError(granularity)
    if isDatetime and not isinstance(start, datetime):
        start = datetime.combine(start, datetime.min.time())
    return start


def _date_part(value, part):
    """ Python replay of the integer date parts of a groupby. """
    return {
        'year_number': value.year,
        'quarter_number': (value.month - 1) // 3 + 1,
        'month_number': value.month,
        'iso_week_number': value.isocalendar()[1],
        'day_of_year': value.timetuple().tm_yday,
        'day_of_month': value.day,
        'day_of_week': value.isoweekday() % 7,
        'hour_number': getattr(value, 'hour', 0),
    }[part]


# ----------------------------------------------------------------------
# aggregation.read_group_core
# ----------------------------------------------------------------------

class TestReadGroupCore(NeutralCase):
    """ ``_read_group`` on the harness item model: many2one groupby, every
    aggregate, having, ordering, limit/offset, empty results, and the two
    public wrappers. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Item = cls.env['test_backend_neutral.item']
        cls.parent1, cls.parent2 = cls.Item.create([
            {'name': 'Parent 1', 'code': 'P1'},
            {'name': 'Parent 2', 'code': 'P2'},
        ])
        cls.items = cls.Item.create([
            {'name': 'a', 'code': 'A', 'quantity': 4, 'parent_id': cls.parent1.id},
            {'name': 'b', 'code': 'B', 'quantity': 4, 'parent_id': cls.parent1.id},
            {'name': 'c', 'quantity': 1, 'parent_id': cls.parent1.id},
            {'name': 'd', 'code': 'D', 'quantity': 10, 'parent_id': cls.parent2.id},
            {'name': 'e', 'quantity': 0, 'parent_id': cls.parent2.id},
            {'name': 'f', 'code': 'F', 'quantity': 7},
            {'name': 'g', 'code': 'G', 'quantity': 1},
        ])
        cls.domain = [('id', 'in', cls.items.ids)]

    def _by_parent(self):
        return _group(self.items, lambda item: item.parent_id)

    def test_groupby_many2one_with_every_aggregate(self):
        aggregates = ['quantity:sum', 'quantity:avg', 'quantity:min', 'quantity:max',
                      '__count', 'code:count', 'code:count_distinct']
        groups = _as_dict(self.Item._read_group(self.domain, ['parent_id'], aggregates))
        expected = self._by_parent()
        self.assertEqual(set(groups), set(expected))
        self.assertIn(self.Item, groups, "items without parent form the empty group")
        for parent, records in expected.items():
            quantities = records.mapped('quantity')
            total, avg, low, high, count, codeCount, codeDistinct = groups[parent]
            self.assertEqual(total, sum(quantities))
            self.assertAlmostEqual(float(avg), sum(quantities) / len(quantities))
            self.assertEqual(low, min(quantities))
            self.assertEqual(high, max(quantities))
            self.assertEqual(count, len(records))
            self.assertEqual(codeCount, len([r for r in records if r.code]))
            self.assertEqual(codeDistinct, len({r.code for r in records if r.code}))

    def test_array_agg_and_recordset(self):
        groups = _as_dict(self.Item._read_group(
            self.domain, ['parent_id'], ['quantity:array_agg', 'id:recordset', 'code:array_agg', 'code:array_agg_distinct'],
        ))
        for parent, records in self._by_parent().items():
            quantities, recordset, codes, distinctCodes = groups[parent]
            # array_agg follows the default order of the model, the creation order here
            self.assertEqual(quantities, records.mapped('quantity'))
            self.assertEqual(recordset, records)
            self.assertEqual(codes, [record.code or None for record in records])
            # array_agg_distinct keeps one empty value when some records have none
            self.assertEqual(set(distinctCodes), {record.code or None for record in records})
            self.assertEqual(len(distinctCodes), len(set(distinctCodes)))

    def test_no_groupby_gives_the_totals(self):
        quantities = self.items.mapped('quantity')
        [(total, count, high, codeDistinct)] = self.Item._read_group(
            self.domain, [], ['quantity:sum', '__count', 'quantity:max', 'code:count_distinct'],
        )
        self.assertEqual((total, count, high), (sum(quantities), len(self.items), max(quantities)))
        self.assertEqual(codeDistinct, len({item.code for item in self.items if item.code}))

    def test_having(self):
        expected = self._by_parent()
        groups = self.Item._read_group(
            self.domain, ['parent_id'], ['quantity:sum'], having=[('quantity:sum', '>', 9)],
        )
        self.assertEqual(_as_dict(groups), {
            parent: (sum(records.mapped('quantity')),)
            for parent, records in expected.items() if sum(records.mapped('quantity')) > 9
        })
        groups = self.Item._read_group(
            self.domain, ['parent_id'], ['__count', 'quantity:max'],
            having=[('__count', '>=', 3), ('quantity:max', '<', 100)],
        )
        self.assertEqual(_as_dict(groups), {
            parent: (len(records), max(records.mapped('quantity')))
            for parent, records in expected.items() if len(records) >= 3
        })
        self.assertEqual(
            self.Item._read_group(self.domain, ['parent_id'], ['__count'], having=[('__count', '>', 1000)]),
            [],
        )

    def test_order_by_aggregate_with_limit_and_offset(self):
        expected = self._by_parent()
        sums = {parent: sum(records.mapped('quantity')) for parent, records in expected.items()}
        self.assertEqual(len(set(sums.values())), len(sums), "the fixture needs distinct sums to assert an order")
        bySumDesc = [(parent, total) for parent, total in sorted(sums.items(), key=lambda item: -item[1])]

        groups = self.Item._read_group(self.domain, ['parent_id'], ['quantity:sum'], order='quantity:sum desc')
        self.assertEqual(groups, bySumDesc)
        groups = self.Item._read_group(self.domain, ['parent_id'], ['quantity:sum'], order='quantity:sum asc')
        self.assertEqual(groups, bySumDesc[::-1])
        groups = self.Item._read_group(
            self.domain, ['parent_id'], ['quantity:sum'], order='quantity:sum desc', limit=2, offset=1,
        )
        self.assertEqual(groups, bySumDesc[1:3])
        groups = self.Item._read_group(self.domain, ['parent_id'], ['quantity:sum'], order='quantity:sum desc', limit=1)
        self.assertEqual(groups, bySumDesc[:1])

    def test_order_by_groupby_field_with_nulls(self):
        byCode = _group(self.items, lambda item: item.code)
        codes = sorted(code for code in byCode if code)
        counts = {code: (len(records),) for code, records in byCode.items()}
        nullGroup = (False, counts[False][0])

        groups = self.Item._read_group(self.domain, ['code'], ['__count'], order='code asc nulls first')
        self.assertEqual(groups, [nullGroup] + [(code, *counts[code]) for code in codes])
        groups = self.Item._read_group(self.domain, ['code'], ['__count'], order='code desc nulls last')
        self.assertEqual(groups, [(code, *counts[code]) for code in reversed(codes)] + [nullGroup])
        groups = self.Item._read_group(self.domain, ['code'], ['__count'], order='code asc nulls last')
        self.assertEqual(groups, [(code, *counts[code]) for code in codes] + [nullGroup])

    def test_order_by_many2one_follows_the_comodel_order(self):
        # the order of the item model is its id: parent1 was created before parent2
        groups = self.Item._read_group(
            self.domain + [('parent_id', '!=', False)], ['parent_id'], ['__count'], order='parent_id',
        )
        self.assertEqual([parent for parent, _count in groups], [self.parent1, self.parent2])
        groups = self.Item._read_group(
            self.domain + [('parent_id', '!=', False)], ['parent_id'], ['__count'], order='parent_id desc',
        )
        self.assertEqual([parent for parent, _count in groups], [self.parent2, self.parent1])

    def test_multiple_groupby(self):
        groups = self.Item._read_group(self.domain, ['parent_id', 'code'], ['__count', 'quantity:sum'])
        expected = _group(self.items, lambda item: (item.parent_id, item.code))
        self.assertEqual(_as_dict(groups, nkeys=2), {
            key: (len(records), sum(records.mapped('quantity'))) for key, records in expected.items()
        })

    def test_empty_results(self):
        for domain in ([('code', '=', 'no such code')], [('id', 'in', [])]):
            with self.subTest(domain=domain):
                self.assertEqual(self.Item._read_group(domain, ['parent_id'], ['__count']), [])
                [(count, codeCount)] = self.Item._read_group(domain, [], ['__count', 'code:count'])
                self.assertEqual((count, codeCount), (0, 0))

    def test_pending_writes_are_aggregated(self):
        a, b, _c, *_rest = self.items
        a.quantity = 100
        b.unlink()
        self.Item.create({'name': 'h', 'quantity': 1000, 'parent_id': self.parent1.id})
        groups = _as_dict(self.Item._read_group([('parent_id', '=', self.parent1.id)], ['parent_id'], ['quantity:sum', '__count']))
        self.assertEqual(groups[self.parent1], (100 + 1 + 1000, 3))

    def test_public_read_group_returns_ids(self):
        groups = self.Item.read_group(self.domain, ['parent_id'], ['id:recordset', '__count'])
        self.assertEqual(_as_dict(groups), {
            parent.id if parent else False: (records.ids, len(records))
            for parent, records in self._by_parent().items()
        })

    def test_formatted_read_group(self):
        groups = self.Item.formatted_read_group(self.domain, ['parent_id'], ['quantity:sum', '__count'])
        expected = self._by_parent()
        self.assertEqual(len(groups), len(expected))
        for group in groups:
            value = group['parent_id']
            parent = self.Item.browse(value[0]) if value else self.Item
            records = expected[parent]
            self.assertEqual(value, (parent.id, parent.display_name) if parent else False)
            self.assertEqual(group['__count'], len(records))
            self.assertEqual(group['quantity:sum'], sum(records.mapped('quantity')))
            # the extra domain of a group selects exactly the records of the group
            self.assertEqual(self.Item.search(self.domain + group['__extra_domain']), records)


# ----------------------------------------------------------------------
# aggregation.read_group_core on base models: selection, many2many,
# several groupbys, multi-company
# ----------------------------------------------------------------------

class TestReadGroupPartner(NeutralCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env['res.company']
        cls.root = Company.create({'name': 'Neutral Group'})
        cls.branch = Company.create({'name': 'Neutral Branch', 'parent_id': cls.root.id})
        cls.other = Company.create({'name': 'Neutral Other'})
        cls.tag1, cls.tag2 = cls.env['res.partner.category'].create([{'name': 'Neutral Tag 1'}, {'name': 'Neutral Tag 2'}])
        cls.Partner = cls.env['res.partner']
        cls.partners = cls.Partner.create([
            {'name': 'N1', 'type': 'contact', 'company_id': cls.root.id, 'color': 1, 'category_id': [Command.set((cls.tag1 + cls.tag2).ids)]},
            {'name': 'N2', 'type': 'invoice', 'company_id': cls.root.id, 'color': 2, 'category_id': [Command.set(cls.tag1.ids)]},
            {'name': 'N3', 'type': 'delivery', 'company_id': cls.branch.id, 'color': 3},
            {'name': 'N4', 'type': 'contact', 'company_id': cls.other.id, 'color': 4, 'category_id': [Command.set(cls.tag2.ids)]},
            {'name': 'N5', 'type': 'other', 'color': 5, 'category_id': [Command.set(cls.tag2.ids)]},
            {'name': 'N6', 'type': 'contact', 'color': 6},
        ])
        cls.domain = [('id', 'in', cls.partners.ids)]

    def test_groupby_selection_in_definition_order(self):
        groups = self.Partner._read_group(self.domain, ['type'], ['__count', 'color:sum'])
        byType = _group(self.partners, lambda partner: partner.type)
        self.assertEqual(_as_dict(groups), {
            value: (len(records), sum(records.mapped('color'))) for value, records in byType.items()
        })
        definitionOrder = [value for value, _label in self.Partner.fields_get(['type'])['type']['selection']]
        self.assertEqual(
            [value for value, *_aggregates in groups],
            [value for value in definitionOrder if value in byType],
            "groups of a selection follow the order of the selection definition",
        )

    def test_groupby_many2many_counts_a_record_in_each_of_its_groups(self):
        groups = _as_dict(self.Partner._read_group(self.domain, ['category_id'], ['__count', 'id:recordset']))
        expected = {}
        for partner in self.partners:
            for tag in partner.category_id or [self.env['res.partner.category']]:
                expected[tag] = expected.get(tag, self.Partner) + partner
        self.assertEqual(groups, {tag: (len(records), records) for tag, records in expected.items()})
        self.assertGreater(
            sum(count for count, _records in groups.values()), len(self.partners),
            "a partner with two tags is counted twice",
        )

    def test_groupby_company_and_type(self):
        groups = self.Partner._read_group(self.domain, ['company_id', 'type'], ['__count', 'color:max'])
        expected = _group(self.partners, lambda partner: (partner.company_id, partner.type))
        self.assertEqual(_as_dict(groups, nkeys=2), {
            key: (len(records), max(records.mapped('color'))) for key, records in expected.items()
        })

    def test_groupby_company_in_a_company_subtree(self):
        companies = self.root + self.branch + self.other
        inRoot = _descendants(self.root, 'parent_id', companies)
        self.assertEqual(inRoot, self.root + self.branch)
        groups = self.Partner._read_group(
            self.domain + [('company_id', 'child_of', self.root.id)], ['company_id'], ['__count', 'color:sum'],
        )
        expected = _group(self.partners.filtered(lambda p: p.company_id in inRoot), lambda p: p.company_id)
        self.assertEqual(set(expected), set(inRoot))
        self.assertEqual(_as_dict(groups), {
            company: (len(records), sum(records.mapped('color'))) for company, records in expected.items()
        })
        groups = self.Partner._read_group(
            self.domain + [('company_id', 'child_of', self.branch.id)], ['company_id'], ['__count'],
        )
        self.assertEqual(groups, [(self.branch, len(self.partners.filtered(lambda p: p.company_id == self.branch)))])

    def test_formatted_read_group_extra_domains(self):
        for groupby in (['type'], ['category_id'], ['company_id'], ['company_id', 'type']):
            with self.subTest(groupby=groupby):
                groups = self.Partner.formatted_read_group(self.domain, groupby, ['__count'])
                total = 0
                for group in groups:
                    members = self.Partner.search(self.domain + group['__extra_domain'])
                    self.assertEqual(len(members), group['__count'])
                    total += group['__count']
                expected = sum(len(partner.category_id) or 1 for partner in self.partners) if groupby == ['category_id'] else len(self.partners)
                self.assertEqual(total, expected)


# ----------------------------------------------------------------------
# aggregation.read_group_core: date granularities, multi-currency
# ----------------------------------------------------------------------

class TestReadGroupCurrencyRates(NeutralCase):

    RATES = {
        'XNA': [
            ('2021-12-31', 1.5),
            ('2022-01-29', 1.1),  # Saturday
            ('2022-01-30', 1.2),  # Sunday
            ('2022-01-31', 1.3),  # Monday
            ('2022-02-01', 1.4),
            ('2022-05-29', 1.6),
            ('2023-01-29', 1.7),
        ],
        'XNB': [
            ('2022-01-30', 20.0),
            ('2022-03-15', 25.0),
            ('2023-06-01', 30.0),
        ],
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rate = cls.env['res.currency.rate']
        cls.currencies = cls.env['res.currency'].create([
            {'name': name, 'symbol': name.lower(), 'rounding': 0.01} for name in cls.RATES
        ])
        cls.rates = cls.Rate.create([
            {'currency_id': currency.id, 'name': day, 'rate': rate, 'company_id': cls.env.company.id}
            for currency in cls.currencies
            for day, rate in cls.RATES[currency.name]
        ])
        cls.domain = [('id', 'in', cls.rates.ids)]

    def test_groupby_currency(self):
        groups = _as_dict(self.Rate._read_group(
            self.domain, ['currency_id'], ['rate:min', 'rate:max', 'rate:avg', 'rate:sum', '__count', 'name:max'],
        ))
        expected = _group(self.rates, lambda rate: rate.currency_id)
        self.assertEqual(set(groups), set(self.currencies))
        for currency, records in expected.items():
            values = records.mapped('rate')
            low, high, avg, total, count, lastDay = groups[currency]
            self.assertAlmostEqual(low, min(values))
            self.assertAlmostEqual(high, max(values))
            self.assertAlmostEqual(avg, sum(values) / len(values))
            self.assertAlmostEqual(total, sum(values))
            self.assertEqual(count, len(records))
            self.assertEqual(lastDay, max(records.mapped('name')))

    def test_groupby_date_granularities(self):
        for granularity in ('day', 'week', 'month', 'quarter', 'year'):
            with self.subTest(granularity=granularity):
                groups = self.Rate._read_group(self.domain, [f'name:{granularity}'], ['__count', 'rate:array_agg'])
                expected = _group(self.rates, lambda rate: _truncate(rate.name, granularity, self.env))
                self.assertEqual(_as_dict(groups), {
                    start: (len(records), records.mapped('rate')) for start, records in expected.items()
                })
                self.assertTrue(all(isinstance(start, date) and not isinstance(start, datetime) for start, *_ in groups))
                self.assertEqual([start for start, *_ in groups], sorted(expected), "groups come in date order")

    def test_groupby_week_follows_the_week_start_of_the_language(self):
        saturday, sunday, monday = (date(2022, 1, 29), date(2022, 1, 30), date(2022, 1, 31))
        self.assertEqual((saturday.isoweekday(), sunday.isoweekday(), monday.isoweekday()), (6, 7, 1))
        groups = _as_dict(self.Rate._read_group(
            self.domain + [('currency_id', '=', self.currencies[0].id), ('name', 'in', [saturday, sunday, monday])],
            ['name:week'], ['name:array_agg'],
        ))
        expected = {}
        for day in (saturday, sunday, monday):
            expected.setdefault(_week_start(self.env, day), []).append(day)
        self.assertEqual({start: days for start, (days,) in groups.items()}, expected)

    def test_groupby_date_parts(self):
        for part in ('year_number', 'quarter_number', 'month_number', 'iso_week_number', 'day_of_year', 'day_of_month', 'day_of_week'):
            with self.subTest(part=part):
                groups = self.Rate._read_group(self.domain, [f'name:{part}'], ['__count'])
                expected = Counter(_date_part(rate.name, part) for rate in self.rates)
                self.assertEqual({_typed(number): count for number, count in groups}, {_typed(number): count for number, count in expected.items()})
                self.assertEqual([number for number, _count in groups], sorted(expected))

    def test_groupby_currency_and_year(self):
        groups = self.Rate._read_group(self.domain, ['currency_id', 'name:year'], ['rate:sum', '__count'])
        expected = _group(self.rates, lambda rate: (rate.currency_id, date(rate.name.year, 1, 1)))
        self.assertEqual(set(_as_dict(groups, nkeys=2)), set(expected))
        for currency, year, total, count in groups:
            records = expected[(currency, year)]
            self.assertAlmostEqual(total, sum(records.mapped('rate')))
            self.assertEqual(count, len(records))

    def test_formatted_read_group_date_extra_domains(self):
        for granularity in ('day', 'week', 'month', 'quarter', 'year'):
            with self.subTest(granularity=granularity):
                groups = self.Rate.formatted_read_group(self.domain, [f'name:{granularity}'], ['__count'])
                total = 0
                for group in groups:
                    self.assertEqual(self.Rate.search_count(self.domain + group['__extra_domain']), group['__count'])
                    total += group['__count']
                self.assertEqual(total, len(self.rates))


# ----------------------------------------------------------------------
# aggregation.project_task_subtasks, datetime granularities
# ----------------------------------------------------------------------

class TestReadGroupProjectTask(NeutralCase):

    DEADLINES = [
        '2024-03-30 23:30:00',  # still March 30 in New York, March 31 in Brussels
        '2024-03-31 00:30:00',
        '2024-03-31 12:00:00',
        '2024-03-31 22:30:00',  # April 1 in Brussels (summer time started that day)
        '2024-06-30 23:45:00',
        '2025-01-01 00:00:00',
        False,
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Neutral Project User',
            'login': 'neutral_project_user',
            'group_ids': [Command.set(cls.env.ref('project.group_project_user').ids)],
        })
        cls.project = cls.env['project.project'].create({'name': 'Neutral Project'})
        cls.Task = cls.env['project.task']
        cls.tasks = cls.Task.create([
            {'name': f'Task {index}', 'project_id': cls.project.id, 'date_deadline': deadline, 'user_ids': [Command.set(cls.user.ids)]}
            for index, deadline in enumerate(cls.DEADLINES)
        ])
        cls.domain = [('id', 'in', cls.tasks.ids)]

    def _assert_datetime_groups(self, Task, granularity):
        groups = Task._read_group(self.domain, [f'date_deadline:{granularity}'], ['__count', 'id:recordset'])
        expected = _group(self.tasks, lambda task: _truncate(task.date_deadline, granularity, Task.env) if task.date_deadline else False)
        self.assertEqual(_as_dict(groups), {start: (len(records), records) for start, records in expected.items()})

    def test_groupby_datetime_in_utc(self):
        Task = self.Task.with_context(tz='UTC')
        for granularity in ('hour', 'day', 'week', 'month', 'quarter', 'year'):
            with self.subTest(granularity=granularity):
                self._assert_datetime_groups(Task, granularity)

    def test_groupby_datetime_in_user_timezone(self):
        for tz in ('Europe/Brussels', 'America/New_York'):
            Task = self.Task.with_context(tz=tz)
            for granularity in ('hour', 'day', 'month', 'year'):
                with self.subTest(tz=tz, granularity=granularity):
                    self._assert_datetime_groups(Task, granularity)
        # the day groups differ between timezones for the fixture
        brussels = {start for start, *_ in self.Task.with_context(tz='Europe/Brussels')._read_group(self.domain, ['date_deadline:day'], ['__count'])}
        newYork = {start for start, *_ in self.Task.with_context(tz='America/New_York')._read_group(self.domain, ['date_deadline:day'], ['__count'])}
        self.assertNotEqual(brussels, newYork)

    def test_groupby_datetime_parts_in_user_timezone(self):
        for tz in ('UTC', 'Europe/Brussels'):
            Task = self.Task.with_context(tz=tz)
            for part in ('day_of_month', 'day_of_week', 'hour_number', 'month_number'):
                with self.subTest(tz=tz, part=part):
                    groups = Task._read_group(self.domain, [f'date_deadline:{part}'], ['__count'])
                    # count on typed keys: a Counter would merge the part 0 with the empty group
                    expected = Counter(
                        _typed(_date_part(task.date_deadline.replace(tzinfo=UTC).astimezone(ZoneInfo(tz)), part) if task.date_deadline else False)
                        for task in self.tasks
                    )
                    self.assertEqual({_typed(number): count for number, count in groups}, dict(expected))
                    self.assertIn(False, [number for number, _count in groups], "the task without deadline is its own group")

    def test_aggregate_datetime(self):
        deadlines = [task.date_deadline for task in self.tasks if task.date_deadline]
        [(low, high, count)] = self.Task._read_group(self.domain, [], ['date_deadline:min', 'date_deadline:max', 'date_deadline:count'])
        self.assertEqual((low, high, count), (min(deadlines), max(deadlines), len(deadlines)))

    def test_subtask_count_follows_the_children(self):
        parent, *_rest = self.tasks
        children = self.Task.create([
            {'name': f'Child {index}', 'project_id': self.project.id, 'parent_id': parent.id} for index in range(3)
        ])
        parent.invalidate_recordset()
        self.assertEqual((parent.subtask_count, parent.closed_subtask_count), (len(parent.child_ids), 0))
        children[0].state = '1_done'
        children[1].state = '1_canceled'
        parent.invalidate_recordset()
        self.assertEqual(
            (parent.subtask_count, parent.closed_subtask_count),
            (len(parent.child_ids), len(parent.child_ids.filtered(lambda c: c.state in ('1_done', '1_canceled')))),
        )
        children[2].unlink()
        children[0].parent_id = False
        parent.invalidate_recordset()
        self.assertEqual(parent.child_ids, children[1])
        self.assertEqual((parent.subtask_count, parent.closed_subtask_count), (1, 1))
        self.assertEqual(
            self.Task._read_group([('parent_id', '=', parent.id)], ['parent_id'], ['__count']),
            [(parent, 1)],
        )

    def test_project_task_counts(self):
        def expected():
            tasks = self.project.task_ids
            return (
                len(tasks),
                len(tasks.filtered(lambda t: t.state in self.Task.OPEN_STATES)),
                len(tasks.filtered(lambda t: t.state not in self.Task.OPEN_STATES)),
            )

        def actual():
            self.project.invalidate_recordset()
            return (self.project.task_count, self.project.open_task_count, self.project.closed_task_count)

        self.assertEqual(actual(), expected())
        self.assertEqual(actual()[2], 0)
        self.tasks[0].state = '1_done'
        self.tasks[1].state = '1_canceled'
        self.assertEqual(actual(), expected())
        self.assertEqual(actual()[2], 2)
        self.tasks[2].unlink()
        self.assertEqual(actual(), expected())
        self.assertEqual(actual()[0], len(self.tasks) - 1)

    def test_groupby_personal_stage_with_model_override(self):
        Task = self.Task.with_user(self.user)
        stages = self.env['project.task.type'].search([('user_id', '=', self.user.id)])
        self.assertGreater(len(stages), 2, "the user got personal stages when tasks were assigned")
        todayStage = stages[1]
        self.tasks[0].with_user(self.user).personal_stage_type_id = todayStage
        self.tasks[1].with_user(self.user).personal_stage_type_id = todayStage
        self.env.flush_all()
        self.env.invalidate_all()
        expected = Counter(task.with_user(self.user).personal_stage_type_id for task in self.tasks)
        self.assertEqual(expected[todayStage], 2)

        groups = Task._read_group(self.domain, ['personal_stage_type_id'], ['__count'])
        self.assertEqual(_as_dict(groups), {stage: (count,) for stage, count in expected.items()})

        groups = Task.with_context(read_group_expand=True).formatted_read_group(self.domain, ['personal_stage_type_id'], ['__count'])
        # group_expand returns every personal stage of the user, the empty ones too
        self.assertEqual({group['personal_stage_type_id'][0] for group in groups}, set(stages.ids))
        self.assertEqual(
            {stage.id: group['__count'] for group in groups for stage in [stages.browse(group['personal_stage_type_id'][0])]},
            {stage.id: expected.get(stage, 0) for stage in stages},
        )
        for group in groups:
            self.assertEqual(Task.search_count(self.domain + group['__extra_domain']), group['__count'])


# ----------------------------------------------------------------------
# aggregation.stock_product_quantities
# ----------------------------------------------------------------------

class TestStockQuantities(NeutralCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].create({'name': 'Neutral Warehouse', 'code': 'NWH'})
        cls.Location = cls.env['stock.location']
        cls.stock = cls.warehouse.lot_stock_id
        cls.shelf = cls.Location.create({'name': 'Shelf', 'location_id': cls.stock.id, 'usage': 'internal'})
        cls.bin = cls.Location.create({'name': 'Bin', 'location_id': cls.shelf.id, 'usage': 'internal'})
        cls.elsewhere = cls.Location.create({'name': 'Elsewhere', 'usage': 'internal'})
        cls.product, cls.emptyProduct = cls.env['product.product'].create([
            {'name': 'Neutral Stored', 'is_storable': True},
            {'name': 'Neutral Empty', 'is_storable': True},
        ])
        cls.quantities = {cls.stock: 5.0, cls.shelf: 3.0, cls.bin: 2.0, cls.elsewhere: 7.0}
        Quant = cls.env['stock.quant']
        for location, quantity in cls.quantities.items():
            Quant._update_available_quantity(cls.product, location, quantity)

    def _in_subtree(self, location):
        universe = self.Location.concat(self.quantities)
        return sum(self.quantities[loc] for loc in _descendants(location, 'location_id', universe) if loc in self.quantities)

    def test_qty_available_sums_the_subtree_of_the_location(self):
        self.assertEqual(self._in_subtree(self.warehouse.view_location_id), 10.0)
        for location in (self.warehouse.view_location_id, self.stock, self.shelf, self.bin, self.elsewhere):
            with self.subTest(location=location.name):
                product = self.product.with_context(location=location.id)
                product.invalidate_recordset()
                self.assertEqual(product.qty_available, self._in_subtree(location))
        self.assertEqual(
            self.product.with_context(warehouse_id=self.warehouse.id).qty_available,
            self._in_subtree(self.warehouse.view_location_id),
        )
        self.assertEqual(self.emptyProduct.with_context(location=self.stock.id).qty_available, 0.0)

    def test_search_qty_available(self):
        products = self.product + self.emptyProduct
        Product = self.env['product.product'].with_context(location=self.stock.id)
        self.assertEqual(Product.search([('id', 'in', products.ids), ('qty_available', '>', 0)]), self.product)
        self.assertEqual(Product.search([('id', 'in', products.ids), ('qty_available', '=', 0)]), self.emptyProduct)
        self.assertEqual(Product.search([('id', 'in', products.ids), ('qty_available', '>', self._in_subtree(self.stock))]), Product.browse())
        self.assertEqual(Product.search([('id', 'in', products.ids), ('qty_available', '>=', self._in_subtree(self.stock))]), self.product)
        Product = self.env['product.product'].with_context(location=self.bin.id)
        self.assertEqual(Product.search([('id', 'in', products.ids), ('qty_available', '>', self.quantities[self.bin])]), Product.browse())

    def test_read_group_quants_in_location_subtree(self):
        Quant = self.env['stock.quant']
        for root in (self.warehouse.view_location_id, self.shelf, self.elsewhere):
            with self.subTest(root=root.name):
                groups = Quant._read_group(
                    [('product_id', '=', self.product.id), ('location_id', 'child_of', root.id)],
                    ['location_id'], ['quantity:sum'],
                )
                universe = self.Location.concat(self.quantities)
                expected = {
                    location: (self.quantities[location],)
                    for location in _descendants(root, 'location_id', universe) if location in self.quantities
                }
                self.assertEqual(_as_dict(groups), expected)

    def test_unlink_location_removes_its_subtree(self):
        top = self.Location.create({'name': 'Neutral Top', 'usage': 'internal'})
        mid = self.Location.create({'name': 'Neutral Mid', 'location_id': top.id, 'usage': 'internal'})
        leaves = self.Location.create([
            {'name': 'Neutral Leaf 1', 'location_id': mid.id, 'usage': 'internal'},
            {'name': 'Neutral Leaf 2', 'location_id': top.id, 'usage': 'internal'},
        ])
        tree = top + mid + leaves
        self.assertEqual(self.Location.search([('id', 'child_of', top.id)]), tree)
        top.unlink()
        self.env.invalidate_all()
        self.assertFalse(tree.exists())
        self.assertFalse(self.Location.search([('id', 'in', tree.ids)]))


# ----------------------------------------------------------------------
# aggregation.account_account_hierarchy
# ----------------------------------------------------------------------

class TestAccountHierarchy(NeutralCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env['res.company']
        cls.root = Company.create({'name': 'Neutral Accounting'})
        cls.env['account.chart.template'].try_loading('generic_coa', company=cls.root, install_demo=False)
        cls.branch = Company.create({'name': 'Neutral Accounting Branch', 'parent_id': cls.root.id})
        Account = cls.env['account.account'].with_company(cls.root)
        cls.receivable = Account.search([('company_ids', 'in', cls.root.id), ('account_type', '=', 'asset_receivable')], limit=1)
        cls.income = Account.search([('company_ids', 'in', cls.root.id), ('account_type', '=', 'income')], limit=1)
        cls.journal = cls.env['account.journal'].search([('company_id', '=', cls.root.id), ('type', '=', 'general')], limit=1)

    def _entry(self, company, amount, post=True):
        move = self.env['account.move'].with_company(company).create({
            'move_type': 'entry',
            'journal_id': self.journal.id,
            'line_ids': [
                Command.create({'account_id': self.receivable.id, 'debit': amount, 'credit': 0}),
                Command.create({'account_id': self.income.id, 'debit': 0, 'credit': amount}),
            ],
        })
        if post:
            move.action_post()
        return move

    def test_current_balance_sums_posted_lines_of_the_company_and_its_branches(self):
        rootMove = self._entry(self.root, 100)
        branchMove = self._entry(self.branch, 30)
        draftMove = self._entry(self.root, 1000, post=False)
        self.assertEqual(rootMove.company_id, self.root)
        self.assertEqual(branchMove.company_id, self.branch)
        self.assertEqual((rootMove.state, branchMove.state, draftMove.state), ('posted', 'posted', 'draft'))
        self.env.invalidate_all()
        self.assertEqual(self.receivable.with_company(self.root).current_balance, 100 + 30)
        self.assertEqual(self.receivable.with_company(self.branch).current_balance, 30)
        self.assertEqual(self.income.with_company(self.root).current_balance, -(100 + 30))
        groups = _as_dict(self.env['account.move.line']._read_group(
            [('move_id', 'in', (rootMove + branchMove + draftMove).ids), ('parent_state', '=', 'posted'), ('company_id', 'child_of', self.root.id)],
            ['company_id'], ['balance:sum', '__count'],
        ))
        self.assertEqual(groups, {self.root: (0.0, 2), self.branch: (0.0, 2)})

    def test_partner_invoice_count_includes_child_contacts(self):
        Partner = self.env['res.partner']
        company = Partner.create({'name': 'Neutral Customer', 'is_company': True})
        contact = Partner.create({'name': 'Neutral Contact', 'parent_id': company.id})
        stranger = Partner.create({'name': 'Neutral Stranger'})
        Move = self.env['account.move'].with_company(self.root)
        invoices = Move.create([
            {
                'move_type': moveType,
                'partner_id': partner.id,
                'invoice_date': '2024-01-15',
                'invoice_line_ids': [Command.create({'name': 'line', 'quantity': 1, 'price_unit': 10, 'account_id': self.income.id})],
            }
            for partner, moveType in ((contact, 'out_invoice'), (contact, 'out_refund'), (company, 'out_invoice'), (stranger, 'out_invoice'))
        ])
        self._entry(self.root, 5)  # not an invoice
        self.assertEqual(len(invoices), 4)
        partners = company + contact + stranger
        partners.invalidate_recordset()
        expected = {
            partner: len(invoices.filtered(lambda inv: inv.partner_id in _descendants(partner, 'parent_id', partners)))
            for partner in partners
        }
        self.assertEqual(expected, {company: 3, contact: 2, stranger: 1})
        self.assertEqual({partner: partner.account_move_count for partner in partners}, expected)


# ----------------------------------------------------------------------
# aggregation.hr_leave_mail_pos: counts and sums inside computes and constraints
# ----------------------------------------------------------------------

class TestDiscussChannelCounts(NeutralCase):

    def test_member_and_message_counts(self):
        channel = self.env['discuss.channel'].create({'name': 'Neutral Channel', 'channel_type': 'channel'})
        partners = self.env['res.partner'].create([{'name': f'Neutral Member {index}'} for index in range(3)])
        channel._add_members(partners=partners)
        channel.invalidate_recordset()
        self.assertEqual(channel.member_count, len(channel.channel_member_ids))
        self.assertEqual(len(channel.channel_member_ids), 1 + len(partners))

        channel.message_post(body='first', message_type='comment', subtype_xmlid='mail.mt_comment')
        channel.message_post(body='second', message_type='comment', subtype_xmlid='mail.mt_comment')
        channel.message_post(body='joined', message_type='notification', subtype_xmlid='mail.mt_note')
        channel.invalidate_recordset()
        counted = channel.message_ids.filtered(lambda message: message.message_type not in ('notification', 'user_notification'))
        self.assertEqual(len(counted), 2)
        self.assertEqual(channel.message_count, len(counted))

        channel.channel_member_ids.filtered(lambda member: member.partner_id == partners[0]).unlink()
        channel.invalidate_recordset()
        self.assertEqual(channel.member_count, len(partners))


class TestLeaveAllocationNegativeSum(NeutralCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({'name': 'Neutral Employee'})
        cls.leaveType = cls.env['hr.work.entry.type'].create({
            'name': 'Neutral Leave',
            'code': 'NLV',
            'requires_allocation': True,
            'allows_negative': True,
            'max_allowed_negative': 20,
        })
        cls.Allocation = cls.env['hr.leave.allocation']

    def _allocate(self, days):
        return self.Allocation.create({
            'name': 'Neutral allocation',
            'employee_id': self.employee.id,
            'work_entry_type_id': self.leaveType.id,
            'number_of_days': days,
            'date_from': '2024-01-01',
        })

    def test_negative_allocations_are_summed_against_the_maximum(self):
        first = self._allocate(-1)
        second = self._allocate(-1)
        self.assertEqual((first.state, second.state), ('confirm', 'confirm'))
        self.assertEqual(sum((first + second).mapped('number_of_hours')), -16)
        with self.assertRaises(ValidationError):
            self._allocate(-1)  # -24 hours in total, above the 20 allowed
        self.env.invalidate_all()
        self.assertEqual(self.Allocation.search([('employee_id', '=', self.employee.id)]), first + second)
        positive = self._allocate(5)
        self.assertEqual(positive.number_of_days, 5)
        [(total,)] = self.Allocation._read_group([('employee_id', '=', self.employee.id)], [], ['number_of_days:sum'])
        self.assertEqual(total, -1 - 1 + 5)


# ----------------------------------------------------------------------
# hierarchy.parent_store_models, sql_views.recursive_cte
# ----------------------------------------------------------------------

class HierarchyCase(NeutralCase):
    """ Helpers shared by the hierarchy tests. """

    def _tree(self, create):
        """ root -> (a -> (a1 -> a1x, a2), b) """
        nodes = {}
        nodes['root'] = create('Neutral root', None)
        nodes['a'] = create('Neutral a', nodes['root'])
        nodes['b'] = create('Neutral b', nodes['root'])
        nodes['a1'] = create('Neutral a1', nodes['a'])
        nodes['a2'] = create('Neutral a2', nodes['a'])
        nodes['a1x'] = create('Neutral a1x', nodes['a1'])
        self.env.flush_all()
        self.env.invalidate_all()
        return nodes

    def _check_against_python(self, Model, parentField, nodes, parentPath=True):
        universe = Model.concat(nodes.values())
        search = Model.with_context(active_test=False).search
        for name, node in nodes.items():
            with self.subTest(node=name):
                descendants = _descendants(node, parentField, universe)
                ancestors = Model.concat(_ancestors(node, parentField))
                self.assertEqual(search([('id', 'child_of', node.id)]), descendants)
                self.assertEqual(search([('id', 'child_of', node.ids)]), descendants)
                self.assertEqual(search([('id', 'parent_of', node.id)]), ancestors)
                self.assertEqual(search([('id', 'in', universe.ids), '!', ('id', 'child_of', node.id)]), universe - descendants)
                self.assertEqual(search([('id', 'in', universe.ids), '!', ('id', 'parent_of', node.id)]), universe - ancestors)
                self.assertEqual(
                    search([('id', 'in', universe.ids), ('id', 'child_of', node.id), ('id', 'parent_of', node.id)]), node,
                )
                self.assertEqual(search([(parentField, 'in', descendants.ids)]), descendants - node)
                if parentPath:
                    self.assertEqual(node.parent_path, _expected_parent_path(node, parentField))
        a, b = nodes['a'], nodes['b']
        self.assertEqual(
            search([('id', 'child_of', [a.id, b.id])]),
            _descendants(a, parentField, universe) | _descendants(b, parentField, universe),
        )
        self.assertEqual(
            search([('id', 'child_of', nodes['root'].id), ('id', 'parent_of', nodes['a1x'].id)]),
            Model.concat(_ancestors(nodes['a1x'], parentField)) & _descendants(nodes['root'], parentField, universe),
        )
        self.assertEqual(search([('id', 'child_of', nodes['a1x'].id)]), nodes['a1x'])


class TestParentStoreHierarchy(HierarchyCase):
    """ ``child_of`` / ``parent_of`` / ``parent_path`` on the parent-store
    models of the sample, against a plain Python walk of the parent field.

    A write that would create a cycle is refused by the ORM with UserError; a
    model may also declare its own constraint and raise ValidationError
    first, so both classes are accepted. """

    def _models(self, reparentable=False):
        Category = self.env['res.partner.category']
        Company = self.env['res.company']
        ProductCategory = self.env['product.category']
        Location = self.env['stock.location']

        def parent(record):
            return record.id if record else False

        models = {
            'res.partner.category': ('parent_id', lambda name, p: Category.create({'name': name, 'parent_id': parent(p)})),
            'product.category': ('parent_id', lambda name, p: ProductCategory.create({'name': name, 'parent_id': parent(p)})),
            'stock.location': ('location_id', lambda name, p: Location.create({'name': name, 'usage': 'internal', 'location_id': parent(p)})),
        }
        if not reparentable:
            # the parent of a company is fixed once created, see test_company_hierarchy_is_fixed
            models['res.company'] = ('parent_id', lambda name, p: Company.create({'name': name, 'parent_id': parent(p)}))
        return models

    def test_child_of_parent_of_and_parent_path(self):
        for modelName, (parentField, create) in self._models().items():
            with self.subTest(model=modelName):
                Model = self.env[modelName]
                nodes = self._tree(create)
                self._check_against_python(Model, parentField, nodes)
                # a full rebuild of the paths gives the same paths
                Model._parent_store_compute()
                self.env.invalidate_all()
                self._check_against_python(Model, parentField, nodes)

    def test_reparenting_moves_the_whole_subtree(self):
        for modelName, (parentField, create) in self._models(reparentable=True).items():
            with self.subTest(model=modelName):
                Model = self.env[modelName]
                nodes = self._tree(create)
                universe = Model.concat(nodes.values())
                a, b, a1, a1x = nodes['a'], nodes['b'], nodes['a1'], nodes['a1x']
                self.assertIn(a1x, Model.search([('id', 'child_of', a.id)]))

                a1[parentField] = b
                self.env.flush_all()
                self.env.invalidate_all()
                self.assertEqual(a1x[parentField], a1, "the grandchild keeps its parent")
                self._check_against_python(Model, parentField, nodes)
                self.assertEqual(Model.search([('id', 'child_of', a.id)]), a + nodes['a2'])
                self.assertEqual(Model.search([('id', 'child_of', b.id)]), b + a1 + a1x)
                self.assertEqual(a1x.parent_path, f'{nodes["root"].id}/{b.id}/{a1.id}/{a1x.id}/')

                # detach a1 as a new root
                a1[parentField] = False
                self.env.flush_all()
                self.env.invalidate_all()
                self._check_against_python(Model, parentField, nodes)
                self.assertEqual(Model.search([('id', 'child_of', nodes['root'].id)]), universe - a1 - a1x)
                self.assertEqual(Model.search([('id', 'parent_of', a1x.id)]), a1 + a1x)
                self.assertEqual(a1.parent_path, f'{a1.id}/')

    def test_cycles_are_refused(self):
        for modelName, (parentField, create) in self._models(reparentable=True).items():
            with self.subTest(model=modelName):
                Model = self.env[modelName]
                nodes = self._tree(create)
                root, a, a1x = nodes['root'], nodes['a'], nodes['a1x']
                for node, newParent in ((root, a1x), (a, a), (a, a1x), (root, root)):
                    with self.assertRaises((UserError, ValidationError)):
                        node[parentField] = newParent
                        self.env.flush_all()
                self.env.invalidate_all()
                self.assertFalse(root[parentField])
                self.assertEqual(a[parentField], root)
                self._check_against_python(Model, parentField, nodes)

    def test_company_hierarchy_is_fixed(self):
        Company = self.env['res.company']
        root = Company.create({'name': 'Neutral fixed root'})
        branch = Company.create({'name': 'Neutral fixed branch', 'parent_id': root.id})
        other = Company.create({'name': 'Neutral fixed other'})
        self.assertEqual(Company.search([('id', 'child_of', root.id)]), root + branch)
        self.assertEqual(branch.parent_path, f'{root.id}/{branch.id}/')
        self.assertEqual(branch.parent_ids, root + branch)
        self.assertEqual(root.parent_ids, root)
        for company, newParent in ((branch, other), (branch, False), (other, root)):
            with self.assertRaises(UserError):
                company.parent_id = newParent
                self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(branch.parent_id, root)
        self.assertFalse(other.parent_id)


class TestHierarchyWithoutParentStore(HierarchyCase):
    """ ``child_of`` / ``parent_of`` on models that only have a parent field
    (res.partner, project.task): same results as with a parent store. """

    def _models(self):
        Partner = self.env['res.partner']
        Task = self.env['project.task']
        project = self.env['project.project'].create({'name': 'Neutral Hierarchy Project'})

        def parent(record):
            return record.id if record else False

        return {
            'res.partner': ('parent_id', lambda name, p: Partner.create({'name': name, 'is_company': True, 'parent_id': parent(p)})),
            'project.task': ('parent_id', lambda name, p: Task.create({'name': name, 'project_id': project.id, 'parent_id': parent(p)})),
        }

    def test_child_of_and_parent_of(self):
        for modelName, (parentField, create) in self._models().items():
            with self.subTest(model=modelName):
                Model = self.env[modelName]
                nodes = self._tree(create)
                self._check_against_python(Model, parentField, nodes, parentPath=False)
                a1, b = nodes['a1'], nodes['b']
                a1[parentField] = b
                self.env.flush_all()
                self.env.invalidate_all()
                self._check_against_python(Model, parentField, nodes, parentPath=False)
                self.assertEqual(Model.search([('id', 'child_of', b.id)]), b + a1 + nodes['a1x'])

    def test_cycles_are_refused(self):
        for modelName, (parentField, create) in self._models().items():
            with self.subTest(model=modelName):
                Model = self.env[modelName]
                nodes = self._tree(create)
                root, a, a1x = nodes['root'], nodes['a'], nodes['a1x']
                for node, newParent in ((root, a1x), (a, a), (root, root)):
                    # project.task refuses a task as its own parent with UserError before its cycle constraint
                    with self.assertRaises((UserError, ValidationError)):
                        node[parentField] = newParent
                        self.env.flush_all()
                self.env.invalidate_all()
                self.assertFalse(root[parentField])
                self._check_against_python(Model, parentField, nodes, parentPath=False)


class TestHasCycle(NeutralCase):
    """ ``_has_cycle`` against a Python depth-first search, on a model that
    does not refuse cycles (the harness item) and on the task dependency
    graph, which does. """

    @staticmethod
    def _python_has_cycle(records, nextRecords):
        for start in records:
            seen = start.browse()
            frontier = start
            while frontier:
                frontier = nextRecords(frontier) - seen
                if start in frontier:
                    return True
                seen |= frontier
        return False

    def test_has_cycle_on_parent_field(self):
        Item = self.env['test_backend_neutral.item']
        a, b, c, d = Item.create([{'name': name} for name in 'abcd'])
        b.parent_id = a
        c.parent_id = b
        d.parent_id = b
        items = a + b + c + d
        self.env.flush_all()
        self.assertFalse(items._has_cycle())
        self.assertFalse(items._has_cycle('parent_id'))
        self.assertFalse(self._python_has_cycle(items, lambda recs: recs.parent_id))

        a.parent_id = c  # a -> c -> b -> a
        self.env.flush_all()
        self.assertTrue(self._python_has_cycle(items, lambda recs: recs.parent_id))
        self.assertTrue(items._has_cycle())
        self.assertTrue(a._has_cycle())
        self.assertTrue(b._has_cycle())
        # d hangs below the loop without being part of it: not a cycle of d
        self.assertEqual(d._has_cycle(), self._python_has_cycle(d, lambda recs: recs.parent_id))
        self.assertFalse(d._has_cycle())
        self.assertFalse(Item.create({'name': 'alone'})._has_cycle())
        self.assertFalse(Item.create({'name': 'leaf', 'parent_id': Item.create({'name': 'top'}).id})._has_cycle())

        a.parent_id = False
        self.env.flush_all()
        self.assertFalse(items._has_cycle())
        self.assertFalse(self._python_has_cycle(items, lambda recs: recs.parent_id))

    def test_has_cycle_on_many2many_dependencies(self):
        project = self.env['project.project'].create({'name': 'Neutral Dependencies', 'allow_task_dependencies': True})
        Task = self.env['project.task']
        t1, t2, t3 = Task.create([{'name': f'Dep {index}', 'project_id': project.id} for index in range(3)])
        t2.depend_on_ids = t1
        t3.depend_on_ids = t2
        self.env.flush_all()
        tasks = t1 + t2 + t3
        self.assertFalse(tasks._has_cycle('depend_on_ids'))
        self.assertFalse(self._python_has_cycle(tasks, lambda recs: recs.depend_on_ids))
        with self.assertRaises(ValidationError):
            t1.depend_on_ids = t3
            self.env.flush_all()
        self.env.invalidate_all()
        self.assertFalse(t1.depend_on_ids)
        self.assertFalse(tasks._has_cycle('depend_on_ids'))
        with self.assertRaises(ValidationError):
            t1.depend_on_ids = t1
            self.env.flush_all()


class TestRecursiveWalks(NeutralCase):
    """ Methods that walk a tree in one query: subtask ids per task, view
    inheritance, location ancestry. Each is compared with a Python walk. """

    def test_subtask_ids_per_task(self):
        project = self.env['project.project'].create({'name': 'Neutral Subtasks'})
        Task = self.env['project.task']

        def create(name, parent):
            return Task.create({'name': name, 'project_id': project.id, 'parent_id': parent.id if parent else False})

        root = create('Neutral root', None)
        a = create('Neutral a', root)
        b = create('Neutral b', root)
        a1 = create('Neutral a1', a)
        a1x = create('Neutral a1x', a1)
        archived = create('Neutral archived', b)
        archived.active = False
        self.env.flush_all()
        self.env.invalidate_all()
        tasks = root + a + b + a1 + a1x + archived

        def expectedSubtasks(task, universe):
            return _descendants(task, 'parent_id', universe) - task

        active = tasks.filtered('active')
        self.assertEqual(active, tasks - archived)
        for task in tasks:
            with self.subTest(task=task.name):
                self.assertEqual(set(task._get_subtask_ids_per_task_id()[task.id]), set(expectedSubtasks(task, active).ids))
                self.assertEqual(task._get_all_subtasks(), expectedSubtasks(task, active))
                self.assertEqual(
                    set(task.with_context(active_test=False)._get_subtask_ids_per_task_id()[task.id]),
                    set(expectedSubtasks(task, tasks).ids),
                )
        perTask = (root + a + b)._get_subtask_ids_per_task_id()
        self.assertEqual(set(perTask), set((root + a + b).ids))
        self.assertEqual({task: set(ids) for task, ids in perTask.items()}, {
            task.id: set(expectedSubtasks(task, active).ids) for task in root + a + b
        })
        self.assertEqual((root + b)._get_all_subtasks(), expectedSubtasks(root, active))
        self.assertEqual((a + b).with_context(active_test=False)._get_all_subtasks(), a1 + a1x + archived)

    def test_inheriting_views(self):
        View = self.env['ir.ui.view']
        base = View.create({
            'name': 'neutral base', 'model': 'res.partner', 'type': 'form', 'priority': 10,
            'arch': '<form><field name="name"/></form>',
        })

        def extend(name, parent, priority, **values):
            return View.create({
                'name': name, 'model': 'res.partner', 'inherit_id': parent.id, 'priority': priority,
                'arch': '<field name="name" position="after"><field name="ref"/></field>',
                **values,
            })

        late = extend('neutral late', base, 30)
        early = extend('neutral early', base, 5)
        grandchild = extend('neutral grandchild', late, 1)
        inactive = extend('neutral inactive', base, 2, active=False)
        underInactive = extend('neutral under inactive', inactive, 1)
        primary = extend('neutral primary', base, 3, mode='primary')
        underPrimary = extend('neutral under primary', primary, 1)
        self.env.flush_all()
        self.env.invalidate_all()
        universe = base + late + early + grandchild + inactive + underInactive + primary + underPrimary

        def expectedInheriting(views):
            # follow inherit_id through active extension views of the same model only
            result = frontier = views.filtered('active')
            while frontier:
                frontier = universe.filtered(
                    lambda v: v.inherit_id in frontier and v.active and v.mode == 'extension' and v.model == v.inherit_id.model,
                ) - result
                result |= frontier
            return result.sorted(lambda v: (v.priority, v.id))

        self.assertEqual(expectedInheriting(base), base + early + late + grandchild)
        for views in (base, late, early, grandchild, inactive, primary, base + primary, late + primary):
            with self.subTest(views=views.mapped('name')):
                found = views._get_inheriting_views()
                expected = expectedInheriting(views)
                self.assertEqual(found.ids, expected.ids, "inheriting views come ordered by priority then id")
        self.assertEqual(View.browse()._get_inheriting_views(), View.browse())
        inactive.active = True
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(base._get_inheriting_views().ids, expectedInheriting(base).ids)
        self.assertIn(underInactive, base._get_inheriting_views())

    def test_location_ancestry(self):
        Location = self.env['stock.location']
        top = Location.create({'name': 'Neutral Top', 'usage': 'internal'})
        mid = Location.create({'name': 'Neutral Mid', 'usage': 'internal', 'location_id': top.id})
        leaf = Location.create({'name': 'Neutral Leaf', 'usage': 'internal', 'location_id': mid.id})
        other = Location.create({'name': 'Neutral Other', 'usage': 'internal', 'location_id': top.id})
        self.env.flush_all()
        self.env.invalidate_all()
        for location in (top, mid, leaf, other):
            ancestors = Location.concat(_ancestors(location, 'location_id'))
            for candidate in (top, mid, leaf, other):
                with self.subTest(location=location.name, candidate=candidate.name):
                    self.assertEqual(location._child_of(candidate), candidate in ancestors)
        self.assertEqual(Location.search([('id', 'parent_of', leaf.id)]), top + mid + leaf)
        self.assertEqual(top.child_internal_location_ids, top + mid + leaf + other)
        self.assertEqual(mid.child_internal_location_ids, mid + leaf)
        other.location_id = mid
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertTrue(other._child_of(mid))
        self.assertEqual(mid.child_internal_location_ids, mid + leaf + other)


# ----------------------------------------------------------------------
# sql_views.lateral_rates: latest row per key
# ----------------------------------------------------------------------

class TestLatestRowPerKey(NeutralCase):

    def test_currency_rates_at_a_date(self):
        company = self.env.company
        Currency = self.env['res.currency']
        Rate = self.env['res.currency.rate']
        xna, xnb, xnc = Currency.create([
            {'name': name, 'symbol': name.lower(), 'rounding': 0.01} for name in ('XNA', 'XNB', 'XNC')
        ])
        ratesByCurrency = {
            xna: [(date(2022, 1, 10), 1.1), (date(2022, 1, 20), 1.2), (date(2022, 2, 1), 1.3)],
            xnb: [(date(2022, 1, 15), 20.0)],
            xnc: [],
        }
        Rate.create([
            {'currency_id': currency.id, 'name': day, 'rate': rate, 'company_id': company.id}
            for currency, rates in ratesByCurrency.items()
            for day, rate in rates
        ])
        self.env.flush_all()

        def expectedRate(currency, day):
            before = [(d, r) for d, r in ratesByCurrency[currency] if d < day]
            if before:
                return max(before)[1], max(before)[0]
            if ratesByCurrency[currency]:
                return min(ratesByCurrency[currency])[1], min(ratesByCurrency[currency])[0]
            return 1.0, None

        currencies = xna + xnb + xnc
        for day in (date(2021, 12, 31), date(2022, 1, 10), date(2022, 1, 11), date(2022, 1, 20), date(2022, 1, 21), date(2022, 3, 1)):
            with self.subTest(date=day):
                rates = currencies._get_rates(company, day)
                self.assertEqual(set(rates), set(currencies.ids))
                for currency in currencies:
                    rate, rateDate = rates[currency.id]
                    expectedValue, expectedDate = expectedRate(currency, day)
                    self.assertAlmostEqual(rate, expectedValue)
                    self.assertEqual(rateDate, expectedDate)
                    # the stored rate of the currency at that date comes from the same lookup
                    currencyAtDate = currency.with_context(date=day, company_id=company.id)
                    currencyAtDate.invalidate_recordset(['rate', 'rate_date'])
                    companyRate, _companyRateDate = rates.get(company.currency_id.id, (1.0, None))
                    self.assertAlmostEqual(currencyAtDate.rate, expectedValue / companyRate)
                    self.assertEqual(currencyAtDate.rate_date, expectedDate or False)

    def test_channel_last_message(self):
        Channel = self.env['discuss.channel']
        channels = Channel.create([{'name': f'Neutral Last {index}', 'channel_type': 'channel'} for index in range(3)])
        busy, quiet, _silent = channels
        for body in ('one', 'two', 'three'):
            busy.message_post(body=body, message_type='comment', subtype_xmlid='mail.mt_comment')
        quiet.message_post(body='only', message_type='comment', subtype_xmlid='mail.mt_comment')
        busy.message_post(body='note', message_type='notification', subtype_xmlid='mail.mt_note')
        self.env.flush_all()
        self.env.invalidate_all()

        def expectedLast(channel):
            return max(channel.message_ids, key=lambda message: message.id, default=self.env['mail.message'])

        lastMessages = channels._get_last_messages()
        self.assertEqual(lastMessages, expectedLast(busy) + expectedLast(quiet))
        self.assertEqual(len(busy.message_ids), 4)
        self.assertEqual(expectedLast(busy).body, '<p>note</p>')
        self.assertEqual(busy._get_last_messages(), expectedLast(busy))
        self.assertEqual(quiet._get_last_messages().body, '<p>only</p>')
        self.assertFalse(channels[2]._get_last_messages())
        expectedLast(busy).unlink()
        self.env.invalidate_all()
        self.assertEqual(busy._get_last_messages(), expectedLast(busy))
        self.assertEqual(busy._get_last_messages().body, '<p>three</p>')


# ----------------------------------------------------------------------
# text search semantics and ordering with nulls
# ----------------------------------------------------------------------

class TestTextSearch(NeutralCase):
    """ ``like`` / ``ilike`` / ``=like`` / ``=ilike`` and their negations,
    against the same pattern applied in Python.

    Accents: whether a search without accents also finds the accented
    record depends on how the database is configured, which the ORM does
    not show; the tests only use patterns that give the same result with
    and without accent folding, and assert that an accented record is
    always found by its own accented text. """

    NAMES = ['Ntx Café Zoë', 'ntx cafe zoe', 'NTX CAFE', 'Zoe Ntx Café Bar', 'Ntx Decaf', 'Ntx Tea', 'Ntx 100% Pure']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.partners = cls.Partner.create([{'name': name} for name in cls.NAMES])
        cls.domain = [('id', 'in', cls.partners.ids)]

    def _search(self, operator, value):
        return self.Partner.search(self.domain + [('name', operator, value)])

    def _matching(self, predicate):
        return self.partners.filtered(lambda partner: predicate(partner.name))

    def test_ilike_is_a_case_insensitive_substring(self):
        self.assertEqual(self._search('ilike', 'ntx caf'), self._matching(lambda name: 'ntx caf' in name.lower()))
        self.assertEqual(self._search('ilike', 'NTX CAF'), self._matching(lambda name: 'ntx caf' in name.lower()))
        self.assertEqual(len(self._search('ilike', 'ntx caf')), 4)
        self.assertEqual(self._search('not ilike', 'caf'), self._matching(lambda name: 'caf' not in name.lower()))
        self.assertEqual(self._search('ilike', ''), self.partners)
        self.assertFalse(self._search('ilike', 'no such name'))

    def test_like_is_case_sensitive(self):
        self.assertEqual(self._search('like', 'Ntx Caf'), self._matching(lambda name: 'Ntx Caf' in name))
        self.assertEqual(len(self._search('like', 'Ntx Caf')), 2)
        self.assertEqual(self._search('like', 'ntx caf'), self._matching(lambda name: 'ntx caf' in name))
        self.assertEqual(self._search('not like', 'Ntx'), self._matching(lambda name: 'Ntx' not in name))

    def test_anchored_patterns(self):
        self.assertEqual(self._search('=ilike', 'ntx caf%'), self._matching(lambda name: name.lower().startswith('ntx caf')))
        self.assertEqual(len(self._search('=ilike', 'ntx caf%')), 3)
        self.assertEqual(self._search('=like', 'Ntx %'), self._matching(lambda name: name.startswith('Ntx ')))
        self.assertEqual(self._search('=like', '%Bar'), self._matching(lambda name: name.endswith('Bar')))
        self.assertEqual(self._search('=ilike', 'ntx tea'), self._matching(lambda name: name.lower() == 'ntx tea'))
        self.assertEqual(self._search('=ilike', 'ntx te_'), self._matching(lambda name: name.lower() == 'ntx tea'))
        self.assertFalse(self._search('=ilike', 'caf%'), "an anchored pattern does not match in the middle")

    def test_equality_is_exact(self):
        accented, plain, *_rest = self.partners
        self.assertEqual(self._search('=', 'Ntx Café Zoë'), accented)
        self.assertEqual(self._search('=', 'ntx cafe zoe'), plain)
        self.assertFalse(self._search('=', 'ntx café zoë'))
        self.assertEqual(self._search('in', ['Ntx Café Zoë', 'ntx cafe zoe', 'nobody']), accented + plain)
        self.assertEqual(self._search('!=', 'Ntx Tea'), self._matching(lambda name: name != 'Ntx Tea'))

    def test_accented_text_finds_the_accented_record(self):
        accented = self.partners[0]
        self.assertIn(accented, self._search('ilike', 'Café Zoë'))
        self.assertIn(accented, self._search('ilike', 'café zoë'))
        self.assertIn(accented, self._search('=ilike', 'ntx café zoë'))
        self.assertIn(accented, self._search('like', 'Café'))
        self.assertEqual(self._search('ilike', 'Decaf'), self._matching(lambda name: 'decaf' in name.lower()))

    def test_percent_in_the_data_is_plain_text_for_equality(self):
        percent = self.partners[-1]
        self.assertEqual(self._search('=', 'Ntx 100% Pure'), percent)
        self.assertEqual(self._search('ilike', '100%'), self._matching(lambda name: '100' in name))
        self.assertEqual(self._search('ilike', '% pure'), self._matching(lambda name: ' pure' in name.lower()))

    def test_search_fetch_and_count_agree_with_search(self):
        found = self._search('ilike', 'ntx')
        self.assertEqual(self.Partner.search_count(self.domain + [('name', 'ilike', 'ntx')]), len(found))
        fetched = self.Partner.search_fetch(self.domain + [('name', 'ilike', 'ntx')], ['name'])
        self.assertEqual(fetched, found)
        self.assertEqual(set(fetched.mapped('name')), {name for name in self.NAMES if 'ntx' in name.lower()})


class TestOrderingWithNulls(NeutralCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Item = cls.env['test_backend_neutral.item']
        cls.items = cls.Item.create([
            {'name': 'one', 'code': 'M', 'quantity': 3},
            {'name': 'two', 'quantity': 1},
            {'name': 'three', 'code': 'A', 'quantity': 2},
            {'name': 'four', 'quantity': 5},
            {'name': 'five', 'code': 'Z', 'quantity': 4},
        ])
        cls.domain = [('id', 'in', cls.items.ids)]

    def _sorted(self, nullsFirst, reverse=False):
        withCode = sorted((item for item in self.items if item.code), key=lambda item: item.code, reverse=reverse)
        # records without a code keep the default order of the model, their id
        withoutCode = [item for item in self.items if not item.code]
        ordered = withoutCode + withCode if nullsFirst else withCode + withoutCode
        return self.Item.concat(ordered)

    def assertOrdered(self, order, expected):
        found = self.Item.search(self.domain, order=order)
        self.assertEqual(found.ids, expected.ids, order)
        self.assertEqual(self.Item.search_fetch(self.domain, ['code'], order=order).ids, expected.ids, order)

    def test_explicit_nulls_placement(self):
        self.assertOrdered('code asc nulls first, id', self._sorted(nullsFirst=True))
        self.assertOrdered('code asc nulls last, id', self._sorted(nullsFirst=False))
        self.assertOrdered('code desc nulls first, id', self._sorted(nullsFirst=True, reverse=True))
        self.assertOrdered('code desc nulls last, id', self._sorted(nullsFirst=False, reverse=True))

    def test_order_by_several_fields(self):
        (self.items[1] + self.items[4]).write({'quantity': 3})  # ties with 'one'
        self.env.flush_all()
        self.assertEqual(sorted(self.items.mapped('quantity')), [2, 3, 3, 3, 5])
        expected = sorted(
            self.items, key=lambda item: (-item.quantity, not item.code, item.code or '', item.id),
        )
        found = self.Item.search(self.domain, order='quantity desc, code asc nulls last, id')
        self.assertEqual(found.ids, [item.id for item in expected])
        expected = sorted(
            self.items, key=lambda item: (-item.quantity, item.code is not False, item.code or '', item.id),
        )
        found = self.Item.search(self.domain, order='quantity desc, code asc nulls first, id')
        self.assertEqual(found.ids, [item.id for item in expected])
        found = self.Item.search(self.domain, order='quantity desc, id desc', limit=2)
        self.assertEqual(found.ids, [item.id for item in sorted(self.items, key=lambda item: (-item.quantity, -item.id))][:2])
