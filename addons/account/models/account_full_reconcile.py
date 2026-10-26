# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command


class AccountFullReconcile(models.Model):
    _name = 'account.full.reconcile'
    _storage = 'mongodb'      # UNT14 wave 2 (w2-b04): documents in odoo_unt13.accountFullReconcile (signed spec map-draft-5)
    _description = "Full Reconcile"

    partial_reconcile_ids = fields.One2many('account.partial.reconcile', 'full_reconcile_id', string='Reconciliation Parts')
    reconciled_line_ids = fields.One2many('account.move.line', 'full_reconcile_id', string='Matched Journal Items')

    @api.model_create_multi
    def create(self, vals_list):
        def get_ids(commands):
            for command in commands:
                if command[0] == Command.LINK:
                    yield command[1]
                elif command[0] == Command.SET:
                    yield from command[2]
                else:
                    raise ValueError("Unexpected command: %s" % command)
        move_line_ids = [list(get_ids(vals.pop('reconciled_line_ids'))) for vals in vals_list]
        partial_ids = [list(get_ids(vals.pop('partial_reconcile_ids'))) for vals in vals_list]
        fulls = super().create(vals_list)

        self.env['account.move.line'].invalidate_model(['full_reconcile_id'])
        fulls.invalidate_recordset(['reconciled_line_ids'], flush=False)
        self._link_records(self.env['account.move.line'], fulls, move_line_ids)

        self.env['account.partial.reconcile'].invalidate_model(['full_reconcile_id'])
        fulls.invalidate_recordset(['partial_reconcile_ids'], flush=False)
        self._link_records(self.env['account.partial.reconcile'], fulls, partial_ids)

        self.env['account.partial.reconcile']._update_matching_number(fulls.reconciled_line_ids)
        return fulls

    @api.model
    def _link_records(self, model, fulls, ids_list):
        """ Set ``full_reconcile_id`` on the records of ``model`` listed per
        full reconcile, through the low-level ORM write: one column update
        per storage, no recompute and no ``modified()``, like the plain SQL
        UPDATE it replaces. The caller invalidates the cache beforehand.
        """
        ids, vals_list = [], []
        for full, record_ids in zip(fulls, ids_list):
            ids.extend(record_ids)
            vals_list.extend([{'full_reconcile_id': full.id}] * len(record_ids))
        model.browse(ids)._write_multi(vals_list)

    def unlink(self):
        # The default `ondelete='set null'` on `account_move_line.full_reconcile_id`
        # nulls the FK in PostgreSQL when the full reconcile is removed, but
        # `account_move_line.matching_number` is a plain Char that nobody
        # recomputes. Mirror the contract of `create()` (see the
        # `_update_matching_number` call right after the UPDATE above) on the
        # unlink path so each previously-linked line ends up with the correct
        # value (False, or 'P<n>' when partial reconciles survive as zombies).
        amls = self.reconciled_line_ids
        res = super().unlink()
        amls = amls.exists()
        if amls:
            self.env['account.partial.reconcile']._update_matching_number(amls)
        return res
