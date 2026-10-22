import datetime as dt

import pytz

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('at_install', '-post_install')
class TestReadGroupMongodb(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attribute = cls.env['test_orm_mongodb.attribute']
        cls.Value = cls.env['test_orm_mongodb.attribute_value']
        cls.color, cls.size = cls.Attribute.create([
            {'name': 'Color', 'sequence': 2, 'value_ids': [
                Command.create({'name': 'Red', 'sequence': 3, 'default_extra_price': 1.5,
                                'is_custom': True, 'html_color': '#f00'}),
                Command.create({'name': 'Blue', 'sequence': 1, 'default_extra_price': 2.5, 'html_color': '#00f'}),
                Command.create({'name': 'Green', 'sequence': 2, 'html_color': '#f00'}),
            ]},
            {'name': 'Size', 'sequence': 1, 'value_ids': [
                Command.create({'name': 'Large', 'sequence': 5, 'is_custom': True}),
            ]},
        ])
        cls.red, cls.blue, cls.green = cls.color.value_ids.sorted('id')
        cls.large = cls.size.value_ids
        cls.domain = [('id', 'in', (cls.color.value_ids + cls.large).ids)]

    def test_aggregates(self):
        rows = self.Value._read_group(self.domain, ['attribute_id'], [
            '__count', 'sequence:sum', 'sequence:max', 'default_extra_price:avg', 'html_color:count',
            'html_color:count_distinct', 'id:recordset', 'sequence:array_agg', 'is_custom:bool_or',
            'is_custom:bool_and',
        ])
        self.assertEqual(rows, [
            (self.color, 3, 6, 3, 2.0, 3, 2, self.red + self.blue + self.green, [3, 1, 2], True, True),
            (self.size, 1, 5, 5, False, 0, 0, self.large, [5], True, True),   # unset values are NULL
        ])
        self.assertEqual(self.Value._read_group(self.domain, [], ['__count', 'sequence:min']), [(4, 1)])
        self.assertEqual(self.Value._read_group([('id', '=', 0)], [], ['__count', 'sequence:sum']), [(0, False)])
        self.assertEqual(self.Value._read_group(self.domain, [], ['__count'], offset=1), [])
        self.assertEqual(self.Value._read_group(self.domain, ['sequence'], ['__count'], limit=0), [])
        self.assertEqual(self.Attribute._read_group([('id', 'in', (self.color + self.size).ids)], ['sequence'], ['__count']),
                         [(1, 1), (2, 1)])

    def test_groups_order_having_paging(self):
        Value = self.Value
        self.assertEqual(Value._read_group(self.domain, ['attribute_id'], ['__count'], order='attribute_id'),
                         [(self.size, 1), (self.color, 3)])     # by the comodel's order
        self.assertEqual(Value._read_group(self.domain, ['html_color'], ['__count'], order='__count desc, html_color'),
                         [('#f00', 2), ('#00f', 1), (False, 1)])
        self.assertEqual(Value._read_group(self.domain, ['attribute_id'], ['__count'], having=[('__count', '>', 1)]),
                         [(self.color, 3)])
        self.assertEqual(Value._read_group(self.domain, ['sequence'], ['__count'], order='sequence desc', limit=2, offset=1),
                         [(3, 1), (2, 1)])
        self.assertEqual(Value._read_group(self.domain, ['is_custom'], ['__count']), [(False, 2), (True, 2)])
        self.assertEqual([name for name, in Value._read_group(self.domain, ['name'])], ['Blue', 'Green', 'Large', 'Red'])
        self.assertEqual(Value._read_group(self.domain, ['attribute_id.name'], ['__count']),
                         [('Color', 3), ('Size', 1)])     # through the comodel, like a join
        self.assertEqual(Value._read_group(self.domain, ['attribute_id.sequence'], ['__count'], order='__count'),
                         [(1, 1), (2, 3)])

    def test_date_granularities(self):
        now = self.red.create_date
        rows = self.Value.with_context(tz='UTC')._read_group(
            self.domain, ['create_date:day', 'create_date:year_number', 'create_date:day_of_week'], ['__count'])
        self.assertEqual(rows, [(dt.datetime(now.year, now.month, now.day), float(now.year), float(now.isoweekday() % 7), 4)])
        rows = self.Value.with_context(tz='UTC')._read_group(self.domain, ['create_date:second_number'], ['__count'])
        self.assertEqual(rows, [(now.second + now.microsecond // 1000 / 1000, 4)])
        local = pytz.utc.localize(now).astimezone(pytz.timezone('Pacific/Kiritimati')).replace(tzinfo=None)
        rows = self.Value.with_context(tz='Pacific/Kiritimati')._read_group(self.domain, ['create_date:hour'], ['__count'])
        self.assertEqual(rows, [(local.replace(minute=0, second=0, microsecond=0), 4)])

    def test_day_of_week_order(self):
        from odoo.orm import storage_mongodb  # noqa: PLC0415
        self.env['res.lang']._activate_lang('en_US').week_start = '1'     # weeks start on Monday
        term = 'create_date:day_of_week'
        rows = [{term: float(dow)} for dow in range(7)]     # date_part('dow'): 0 is Sunday
        rank = storage_mongodb._group_rank(self.Value, term, rows, traverse_many2one=False)
        self.assertEqual([row[term] for row in sorted(rows, key=rank)], [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.0])

    def test_chunked_aggregation_merges_groups(self):
        from odoo.orm import storage_mongodb  # noqa: PLC0415
        specs = ['__count', 'sequence:sum', 'sequence:max', 'default_extra_price:avg', 'html_color:count_distinct',
                 'id:recordset', 'sequence:array_agg', 'is_custom:bool_and']
        expected = self.Value._read_group(self.domain, ['attribute_id'], specs)
        with patch.object(storage_mongodb, 'GROUP_CHUNK', 1):
            self.assertEqual(self.Value._read_group(self.domain, ['attribute_id'], specs), expected)

    def test_chunked_decimal_aggregates(self):
        from odoo.orm import storage_mongodb  # noqa: PLC0415
        Category = self.env['test_orm_mongodb.storage_category']
        categories = Category.create([{'name': 'a', 'max_weight': 1.5}, {'name': 'b', 'max_weight': 2.5}])
        specs = ['max_weight:sum', 'max_weight:avg', 'max_weight:min', 'max_weight:max']
        with patch.object(storage_mongodb, 'GROUP_CHUNK', 1):
            self.assertEqual(Category._read_group([('id', 'in', categories.ids)], [], specs), [(4.0, 2.0, 1.5, 2.5)])

    def test_dotted_groupby_many2many(self):
        Lock = self.env['test_orm_mongodb.lock_exception']
        group_a, group_b = self.env['res.groups'].create([{'name': 'A'}, {'name': 'B'}])
        both = new_test_user(self.env, 'both', groups='base.group_user')
        both.group_ids += group_a + group_b
        only_a = new_test_user(self.env, 'only_a', groups='base.group_user')
        only_a.group_ids += group_a
        company = self.env.company
        locks = Lock.create([{'company_id': company.id, 'user_id': user.id} for user in (both, only_a)]
                            + [{'company_id': company.id}])
        rows = dict(Lock._read_group([('id', 'in', locks.ids)], ['user_id.group_ids'], ['__count']))
        self.assertEqual((rows[group_a], rows[group_b]), (2, 1))    # each user counts in every group
        self.assertEqual(rows[self.env['res.groups']], 1)          # no user: the outer join's null group

    def test_dotted_groupby_checks_field_access(self):
        Lock = self.env['test_orm_mongodb.lock_exception']
        user = new_test_user(self.env, 'basic', groups='base.group_user')
        lock = Lock.create({'company_id': self.env.company.id, 'user_id': user.id})
        self.patch(self.env['res.users']._fields['login'], 'groups', 'base.group_system')
        with self.assertRaises(AccessError):
            Lock.with_user(user)._read_group([('id', '=', lock.id)], ['user_id.login'], ['__count'])
