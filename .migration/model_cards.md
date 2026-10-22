# Model review: map-draft-1

## Your data in MongoDB

142 source tables become 71 collections: 36 hold one table each, and 35 also carry 71 smaller tables embedded inside their documents (71 as arrays, 0 as one subdocument; 55 of the arrays are link tables). The most common reason a table keeps its own collection: other tables also point at it, so it keeps its own collection (223 of 224 references). The most common reason a table is embedded: a link table, kept as an array on this side (56 of 72 embeds). 379 tables stay on the source and are not migrated: account_account_account_merge_wizard_rel, account_accrued_orders_wizard, account_analytic_account, account_analytic_applicability, account_analytic_distribution_model, account_analytic_line, account_analytic_plan, account_automatic_entry_wizard and 371 more.

### Examples

_No rehearsal sample for Root document: re-render with --samples (schema-modeling step 7)._

_No rehearsal sample for Embedded child array: re-render with --samples (schema-modeling step 7)._

_No rehearsal sample for Link-table array: re-render with --samples (schema-modeling step 7)._

_No rehearsal sample for Reference: re-render with --samples (schema-modeling step 7)._

### Known limits

- 336 of 357 relationship choices follow the schema alone (assumed), not measured data or app code.
- 57 embedded arrays have no measured size bound (cardinality assumed).
- 202 questions are still open; they are listed below.
- No rehearsal sample yet: examples appear once the page is re-rendered with --samples.

## Review

- **Draft:** 71 collections, 71 embedded tables, 379 tables excluded.
- **Evidence:** of 357 relationship choices, 21 rest on measured data or app code and 0 on a recorded decision (`derived`); the rest follow the schema alone (`assumed`).
- **Decisions:** 8 kinds of question, 202 items. The draft already applies each proposal; answer each group with one line in `.migration/answers.txt` (template below).

1. **many_to_many_junction** (56): proposed as an array in account_account (junction name); confirm the side, that neither side's list grows without bound or past the 16 MB document limit, and add a multikey index for the reverse lookup — or keep a reference  
   Applies to: account_account_account_tag, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_account_tax_default_rel, account_cash_rounding_account_payment_method_line_rel, account_fiscal_position_account_tax_rel, account_journal_account_reconcile_model_rel and 48 more
2. **embed_unbounded** (2): 1:N embed: confirm the fan-out bound and document size (16 MB) against data, or bucket/reference  
   Applies to: sale_order_transaction_rel, account_analytic_line_stock_move_rel
3. **transient_tables** (1): 88 table(s) back transient models, scratch state the framework deletes on a timer, so they are not migrated: account_account_account_merge_wizard_rel, account_accrued_orders_wizard, account_automatic_entry_wizard, account_automatic_entry_wizard_account_move_line_rel, account_autopost_bills_wizard, account_financial_year_op, account_merge_wizard, account_merge_wizard_line, account_move_account_move_send_batch_wizard_rel, account_move_account_resequence_wizard_rel, account_move_reversal, account_move_reversal_move, account_move_reversal_new_move, account_move_send_batch_wizard, account_move_send_wizard, account_move_send_wizard_res_partner_rel, account_move_validate_account_move_rel, account_payment_register, account_payment_register_move_line_rel, account_resequence_wizard, account_secure_entries_wizard, account_setup_bank_manual_config, base_document_layout, bill_to_po_wizard, lot_label_layout, lot_label_layout_stock_lot_rel, lot_label_layout_stock_move_line_rel, mail_compose_message, mail_compose_message_ir_attachments_rel, mail_compose_message_res_partner_cc_rel, mail_compose_message_res_partner_rel, payment_link_wizard, picking_label_type, picking_label_type_stock_picking_rel, product_label_layout, product_label_layout_product_product_rel, product_label_layout_product_template_rel, product_label_layout_product_uom_rel, product_label_layout_stock_move_rel, product_replenish, product_supplierinfo_stock_replenishment_info_rel, res_config_settings, sale_advance_payment_inv, sale_advance_payment_inv_sale_order_rel, sale_mass_cancel_orders, sale_order_discount, sale_order_mass_cancel_wizard_rel, stock_add_to_wave, stock_add_to_wave_stock_move_line_rel, stock_add_to_wave_stock_picking_rel, stock_backorder_confirmation, stock_backorder_confirmation_line, stock_conflict_quant_rel, stock_inventory_adjustment_name, stock_inventory_adjustment_name_stock_quant_rel, stock_inventory_conflict, stock_inventory_conflict_stock_quant_rel, stock_inventory_warning, stock_inventory_warning_stock_quant_rel, stock_location_label_layout, stock_move_line_stock_package_destination_rel, stock_move_line_stock_put_in_pack_rel, stock_orderpoint_snooze, stock_orderpoint_snooze_stock_warehouse_orderpoint_rel, stock_orderpoint_suggest, stock_orderpoint_suggest_stock_warehouse_orderpoint_rel, stock_package_destination, stock_package_label_layout, stock_package_stock_put_in_pack_rel, stock_picking_backorder_rel, stock_picking_stock_zero_demand_confirmation_rel, stock_picking_to_batch, stock_picking_type_label_layout, stock_put_in_pack, stock_quant_relocate, stock_quant_stock_quant_relocate_rel, stock_quant_stock_request_count_rel, stock_replenishment_info, stock_replenishment_option, stock_request_count, stock_route_stock_rules_report_rel, stock_rules_report, stock_rules_report_stock_warehouse_rel, stock_traceability_report, stock_warn_insufficient_qty_scrap, stock_zero_demand_confirmation, update_product_attribute_value, validate_account_move; confirm none must survive cutover
4. **no_access_evidence** (71): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged  
   Applies to: account_account, account_account_tag, account_bank_statement, account_bank_statement_line, account_cash_rounding, account_fiscal_position, account_full_reconcile, account_incoterms and 63 more
5. **cascade_into_embed** (43): account_account_tax_default_rel is embedded in account_account, but deleting a account_tax row cascades to its account_account_tax_default_rel: the app must pull them from every account_account document, or keep account_account_tax_default_rel separate  
   Applies to: account_account_tax_default_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_cash_rounding_account_payment_method_line_rel, account_fiscal_position_account_tax_rel, account_journal_account_reconcile_model_rel, account_move__account_payment and 35 more
6. **lob** (13): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)  
   Applies to: account_account, account_journal, account_move, account_move_line, account_report_expression, product_template, purchase_order, purchase_order_line and 5 more
7. **nullable_unique_key** (9): source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
8. **fanout_unmeasured** (7): adjusting_entries__account_move has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding  
   Applies to: adjusting_entries__account_move, account_payment_account_bank_statement_line_rel, purchase_order_line_accrual_move_rel, sale_order_transaction_rel, sale_order_line_accrual_move_rel, account_analytic_line_stock_move_rel, stock_move_line_consume_rel

**Answers template.** Copy it to `.migration/answers.txt` and replace each `<...>` with who decided and why. `accept` keeps the embeds and copied fields a rule proposed (from the schema alone), `reject` makes its embeds references, `except` exempts tables, `close` settles every question of a kind. Delete lines you are not ready to answer.

```
accept junction_array: <who said so, and why>  # 56 tables: account_account_account_tag, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_account_tax_default_rel, account_cash_rounding_account_payment_method_line_rel, account_fiscal_position_account_tax_rel, account_journal_account_reconcile_model_rel and 48 more
accept ownership: <who said so, and why>  # 2 tables: account_analytic_line_stock_move_rel, sale_order_transaction_rel
close many_to_many_junction: <who said so, and why>  # 56 questions
close embed_unbounded: <who said so, and why>  # 2 questions
close transient_tables: <who said so, and why>  # 1 questions
close no_access_evidence: <who said so, and why>  # 71 questions
close cascade_into_embed: <who said so, and why>  # 43 questions
close lob: <who said so, and why>  # 13 questions
close nullable_unique_key: <who said so, and why>  # 9 questions
close fanout_unmeasured: <who said so, and why>  # 7 questions
```

## accountAccount

From `account_account` with `account_account_res_company_rel`, `account_account_account_tag`, `account_account_tax_default_rel` embedded.

```js
{
  _id: int,  // id
  currencyId: int,  // currency_id
  parentId: int,  // parent_id
  accountStockVariationId: int,  // account_stock_variation_id
  accountStockExpenseId: int,  // account_stock_expense_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  accountType: string,  // account_type
  parentPath: string,  // parent_path
  name: object,  // name
  description: object,  // description
  codeStore: object,  // code_store
  note: string,  // note
  active: bool,  // active
  reconcile: bool,  // reconcile
  nonTrade: bool,  // non_trade
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resCompanyRel: [{  // account_account_res_company_rel, 1:N derived
    resCompanyId: int,  // res_company_id
  }],
  accountTag: [{  // account_account_account_tag, 1:N assumed
    accountAccountTagId: int,  // account_account_tag_id
  }],
  taxDefaultRel: [{  // account_account_tax_default_rel, 1:N assumed
    taxId: int,  // tax_id
  }],
}
```

Why:
- account_account → account_account, account_journal, account_move_line, account_payment, account_payment_method_line, account_reconcile_model_line, account_tax, account_tax_repartition_line, stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account → account_account_account_tag, account_account_tax_default_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_account_tag → account_account_account_tag: **reference**, a link table, embedded on the other side (assumed)
- account_account → account_account_res_company_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_tax → account_account_tax_default_rel: **reference**, a link table, embedded on the other side (assumed)
- account_account → account_fiscal_position_account: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (3):
- **cascade_into_embed** (account_account_tax_default_rel): account_account_tax_default_rel is embedded in account_account, but deleting a account_tax row cascades to its account_account_tax_default_rel: the app must pull them from every account_account document, or keep account_account_tax_default_rel separate
- **no_access_evidence** (account_account): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_account): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## accountAccountTag

From `account_account_tag` with `account_account_tag_account_move_line_rel`, `account_account_tag_account_tax_repartition_line_rel`, `account_account_tag_product_template_rel` embedded.

```js
{
  _id: int,  // id
  color: int,  // color
  countryId: int,  // country_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  applicability: string,  // applicability
  name: object,  // name
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  accountMoveLineRel: [{  // account_account_tag_account_move_line_rel, 1:N assumed
    accountMoveLineId: int,  // account_move_line_id
  }],
  accountTaxRepartitionLineRel: [{  // account_account_tag_account_tax_repartition_line_rel, 1:N assumed
    accountTaxRepartitionLineId: int,  // account_tax_repartition_line_id
  }],
  productTemplateRel: [{  // account_account_tag_product_template_rel, 1:N assumed
    productTemplateId: int,  // product_template_id
  }],
}
```

Why:
- account_account_tag → account_account_account_tag: **reference**, a link table, embedded on the other side (assumed)
- account_account_tag → account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_move_line → account_account_tag_account_move_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax_repartition_line → account_account_tag_account_tax_repartition_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → account_account_tag_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **cascade_into_embed** (account_account_tag_account_move_line_rel): account_account_tag_account_move_line_rel is embedded in account_account_tag, but deleting a account_move_line row cascades to its account_account_tag_account_move_line_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_account_move_line_rel separate
- **cascade_into_embed** (account_account_tag_account_tax_repartition_line_rel): account_account_tag_account_tax_repartition_line_rel is embedded in account_account_tag, but deleting a account_tax_repartition_line row cascades to its account_account_tag_account_tax_repartition_line_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_account_tax_repartition_line_rel separate
- **cascade_into_embed** (account_account_tag_product_template_rel): account_account_tag_product_template_rel is embedded in account_account_tag, but deleting a product_template row cascades to its account_account_tag_product_template_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_product_template_rel separate
- **no_access_evidence** (account_account_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## accountBankStatement

From `account_bank_statement` with `account_bank_statement_ir_attachment_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  currencyId: int,  // currency_id
  journalId: int,  // journal_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  reference: string,  // reference
  firstLineIndex: string,  // first_line_index
  date: date,  // date
  balanceStart: decimal,  // balance_start
  balanceEnd: decimal,  // balance_end
  balanceEndReal: decimal,  // balance_end_real
  isComplete: bool,  // is_complete
  isStatementPosted: bool,  // is_statement_posted
  createDate: date,  // create_date
  writeDate: date,  // write_date
  irAttachmentRel: [{  // account_bank_statement_ir_attachment_rel, 1:N derived
    irAttachmentId: int,  // ir_attachment_id
  }],
}
```

Why:
- account_journal → account_bank_statement: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement → account_bank_statement_ir_attachment_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_bank_statement → account_bank_statement_line, account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_bank_statement): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountCashRounding

From `account_cash_rounding` with `account_cash_rounding_res_currency_rel`, `account_cash_rounding_res_partner_category_rel`, `account_cash_rounding_account_payment_method_line_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  roundingMethod: string,  // rounding_method
  strategy: string,  // strategy
  name: object,  // name
  profitAccountId: object,  // profit_account_id
  lossAccountId: object,  // loss_account_id
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  rounding: double,  // rounding
  resCurrencyRel: [{  // account_cash_rounding_res_currency_rel, 1:N derived
    resCurrencyId: int,  // res_currency_id
  }],
  resPartnerCategoryRel: [{  // account_cash_rounding_res_partner_category_rel, 1:N derived
    resPartnerCategoryId: int,  // res_partner_category_id
  }],
  accountPaymentMethodLineRel: [{  // account_cash_rounding_account_payment_method_line_rel, 1:N assumed
    accountPaymentMethodLineId: int,  // account_payment_method_line_id
  }],
}
```

Why:
- account_payment_method_line → account_cash_rounding_account_payment_method_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_cash_rounding → account_cash_rounding_account_payment_method_line_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_cash_rounding → account_cash_rounding_res_currency_rel, account_cash_rounding_res_partner_category_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_cash_rounding → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **cascade_into_embed** (account_cash_rounding_account_payment_method_line_rel): account_cash_rounding_account_payment_method_line_rel is embedded in account_cash_rounding, but deleting a account_payment_method_line row cascades to its account_cash_rounding_account_payment_method_line_rel: the app must pull them from every account_cash_rounding document, or keep account_cash_rounding_account_payment_method_line_rel separate
- **no_access_evidence** (account_cash_rounding): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountFiscalPosition

From `account_fiscal_position` with `account_fiscal_position_account`, `account_fiscal_position_res_country_state_rel`, `account_fiscal_position_account_tax_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  companyId: int,  // company_id
  countryId: int,  // country_id
  countryGroupId: int,  // country_group_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  zipFrom: string,  // zip_from
  zipTo: string,  // zip_to
  foreignVat: string,  // foreign_vat
  name: object,  // name
  note: object,  // note
  active: bool,  // active
  autoApply: bool,  // auto_apply
  vatRequired: bool,  // vat_required
  isDomestic: bool,  // is_domestic
  createDate: date,  // create_date
  writeDate: date,  // write_date
  account: [{  // account_fiscal_position_account, 1:N derived
    accountSrcId: int,  // account_src_id
    accountDestId: int,  // account_dest_id
    id: int,  // id
    companyId: int,  // company_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  resCountryStateRel: [{  // account_fiscal_position_res_country_state_rel, 1:N derived
    resCountryStateId: int,  // res_country_state_id
  }],
  accountTaxRel: [{  // account_fiscal_position_account_tax_rel, 1:N assumed
    accountTaxId: int,  // account_tax_id
  }],
}
```

Why:
- account_account → account_fiscal_position_account: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_fiscal_position → account_fiscal_position_account, account_fiscal_position_res_country_state_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_fiscal_position → account_fiscal_position_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_fiscal_position_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)
- account_fiscal_position → account_move, purchase_order, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **cascade_into_embed** (account_fiscal_position_account_tax_rel): account_fiscal_position_account_tax_rel is embedded in account_fiscal_position, but deleting a account_tax row cascades to its account_fiscal_position_account_tax_rel: the app must pull them from every account_fiscal_position document, or keep account_fiscal_position_account_tax_rel separate
- **no_access_evidence** (account_fiscal_position): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountJournal

From `account_journal` with `account_journal_account_reconcile_model_rel` embedded.

```js
{
  _id: int,  // id
  aliasId: int,  // alias_id
  defaultAccountId: int,  // default_account_id
  suspenseAccountId: int,  // suspense_account_id
  nonDeductibleAccountId: int,  // non_deductible_account_id
  sequence: int,  // sequence
  currencyId: int,  // currency_id
  companyId: int,  // company_id
  invoiceTemplatePdfReportId: int,  // invoice_template_pdf_report_id
  profitAccountId: int,  // profit_account_id
  lossAccountId: int,  // loss_account_id
  bankAccountId: int,  // bank_account_id
  journalGroupId: int,  // journal_group_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  color: int,  // color
  accessToken: string,  // access_token
  code: string,  // code
  type: string,  // type
  invoiceReferenceType: string,  // invoice_reference_type
  invoiceReferenceModel: string,  // invoice_reference_model
  bankStatementsSource: string,  // bank_statements_source
  incomingEinvoiceNotificationEmail: string,  // incoming_einvoice_notification_email
  name: object,  // name
  sequenceOverrideRegex: string,  // sequence_override_regex
  active: bool,  // active
  isSelfBilling: bool,  // is_self_billing
  restrictModeHashTable: bool,  // restrict_mode_hash_table
  refundSequence: bool,  // refund_sequence
  paymentSequence: bool,  // payment_sequence
  showOnDashboard: bool,  // show_on_dashboard
  disableDashboardGraph: bool,  // disable_dashboard_graph
  createDate: date,  // create_date
  writeDate: date,  // write_date
  accountReconcileModelRel: [{  // account_journal_account_reconcile_model_rel, 1:N assumed
    accountReconcileModelId: int,  // account_reconcile_model_id
  }],
}
```

Why:
- account_journal → account_bank_statement, account_bank_statement_line, account_move, account_move_line, account_payment, account_payment_method_line, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account, account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_journal → account_journal_account_reconcile_model_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (3):
- **cascade_into_embed** (account_journal_account_reconcile_model_rel): account_journal_account_reconcile_model_rel is embedded in account_journal, but deleting a account_reconcile_model row cascades to its account_journal_account_reconcile_model_rel: the app must pull them from every account_journal document, or keep account_journal_account_reconcile_model_rel separate
- **no_access_evidence** (account_journal): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_journal): LOB column(s) sequence_override_regex measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## accountMove

From `account_move` with `account_move__account_payment`, `account_move_purchase_order_rel`, `adjusting_entries__account_move` embedded.

```js
{
  _id: int,  // id
  sequenceNumber: int,  // sequence_number
  messageMainAttachmentId: int,  // message_main_attachment_id
  journalId: int,  // journal_id
  companyId: int,  // company_id
  originPaymentId: int,  // origin_payment_id
  statementLineId: int,  // statement_line_id
  taxCashBasisRecId: int,  // tax_cash_basis_rec_id
  taxCashBasisOriginMoveId: int,  // tax_cash_basis_origin_move_id
  autoPostOriginId: int,  // auto_post_origin_id
  secureSequenceNumber: int,  // secure_sequence_number
  invoicePaymentTermId: int,  // invoice_payment_term_id
  partnerId: int,  // partner_id
  commercialPartnerId: int,  // commercial_partner_id
  partnerShippingId: int,  // partner_shipping_id
  partnerBankId: int,  // partner_bank_id
  fiscalPositionId: int,  // fiscal_position_id
  preferredPaymentMethodLineId: int,  // preferred_payment_method_line_id
  currencyId: int,  // currency_id
  reversedEntryId: int,  // reversed_entry_id
  invoiceUserId: int,  // invoice_user_id
  importSourceAttachmentId: int,  // import_source_attachment_id
  invoiceIncotermId: int,  // invoice_incoterm_id
  invoiceCashRoundingId: int,  // invoice_cash_rounding_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  sequencePrefix: string,  // sequence_prefix
  accessToken: string,  // access_token
  name: string,  // name
  ref: string,  // ref
  state: string,  // state
  moveType: string,  // move_type
  autoPost: string,  // auto_post
  reviewState: string,  // review_state
  inalterableHash: string,  // inalterable_hash
  paymentReference: string,  // payment_reference
  qrCodeMethod: string,  // qr_code_method
  paymentState: string,  // payment_state
  documentTaxMode: string,  // document_tax_mode
  invoiceSourceEmail: string,  // invoice_source_email
  invoicePartnerDisplayName: string,  // invoice_partner_display_name
  invoiceOrigin: string,  // invoice_origin
  incotermLocation: string,  // incoterm_location
  date: date,  // date
  autoPostUntil: date,  // auto_post_until
  invoiceDate: date,  // invoice_date
  invoiceDateDue: date,  // invoice_date_due
  deliveryDate: date,  // delivery_date
  taxableSupplyDate: date,  // taxable_supply_date
  sendingData: object,  // sending_data
  narration: string,  // narration
  invoiceCurrencyRate: decimal,  // invoice_currency_rate
  amountUntaxed: decimal,  // amount_untaxed
  amountTax: decimal,  // amount_tax
  amountTotal: decimal,  // amount_total
  amountResidual: decimal,  // amount_residual
  amountUntaxedSigned: decimal,  // amount_untaxed_signed
  amountUntaxedInCurrencySigned: decimal,  // amount_untaxed_in_currency_signed
  amountTaxSigned: decimal,  // amount_tax_signed
  amountTotalSigned: decimal,  // amount_total_signed
  amountTotalInCurrencySigned: decimal,  // amount_total_in_currency_signed
  amountResidualSigned: decimal,  // amount_residual_signed
  quickEditTotalAmount: decimal,  // quick_edit_total_amount
  alwaysTaxExigible: bool,  // always_tax_exigible
  postedBefore: bool,  // posted_before
  inventoryClosing: bool,  // inventory_closing
  madeSequenceGap: bool,  // made_sequence_gap
  isManuallyModified: bool,  // is_manually_modified
  isMoveSent: bool,  // is_move_sent
  createDate: date,  // create_date
  writeDate: date,  // write_date
  hasGroupedLines: bool,  // has_grouped_lines
  closingDatetime: date,  // closing_datetime
  campaignId: int,  // campaign_id
  sourceId: int,  // source_id
  mediumId: int,  // medium_id
  teamId: int,  // team_id
  utmReference: string,  // utm_reference
  accountPayment: [{  // account_move__account_payment, 1:N assumed
    paymentId: int,  // payment_id
  }],
  purchaseOrderRel: [{  // account_move_purchase_order_rel, 1:N assumed
    purchaseOrderId: int,  // purchase_order_id
  }],
  adjustingEntriesAccountMove: [{  // adjusting_entries__account_move, 1:N assumed
    moveId: int,  // move_id
  }],
}
```

Why:
- account_move → account_bank_statement_line, account_move, account_move_line, account_partial_reconcile, account_payment, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_fiscal_position, account_cash_rounding, account_incoterms, account_payment_term, account_journal, account_payment, account_payment_method_line, account_bank_statement_line, account_partial_reconcile → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move → account_move__account_payment, account_move_purchase_order_rel, adjusting_entries__account_move: **embed**, a link table, kept as an array on this side (assumed)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- purchase_order → account_move_purchase_order_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move → adjusting_entries__account_move, purchase_order_line_accrual_move_rel, sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (5):
- **fanout_unmeasured** (adjusting_entries__account_move): adjusting_entries__account_move has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_move__account_payment): account_move__account_payment is embedded in account_move, but deleting a account_payment row cascades to its account_move__account_payment: the app must pull them from every account_move document, or keep account_move__account_payment separate
- **cascade_into_embed** (account_move_purchase_order_rel): account_move_purchase_order_rel is embedded in account_move, but deleting a purchase_order row cascades to its account_move_purchase_order_rel: the app must pull them from every account_move document, or keep account_move_purchase_order_rel separate
- **no_access_evidence** (account_move): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_move): LOB column(s) narration measured max 209 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## accountPayment

From `account_payment` with `account_payment_account_bank_statement_line_rel` embedded.

```js
{
  _id: int,  // id
  messageMainAttachmentId: int,  // message_main_attachment_id
  moveId: int,  // move_id
  journalId: int,  // journal_id
  companyId: int,  // company_id
  partnerBankId: int,  // partner_bank_id
  returnPartnerBankId: int,  // return_partner_bank_id
  pairedInternalTransferPaymentId: int,  // paired_internal_transfer_payment_id
  paymentMethodLineId: int,  // payment_method_line_id
  paymentMethodId: int,  // payment_method_id
  currencyId: int,  // currency_id
  partnerId: int,  // partner_id
  commercialPartnerId: int,  // commercial_partner_id
  outstandingAccountId: int,  // outstanding_account_id
  destinationAccountId: int,  // destination_account_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  state: string,  // state
  transactionUuid: string,  // transaction_uuid
  paymentType: string,  // payment_type
  partnerType: string,  // partner_type
  memo: string,  // memo
  paymentReference: string,  // payment_reference
  date: date,  // date
  amount: decimal,  // amount
  amountCompanyCurrencySigned: decimal,  // amount_company_currency_signed
  isReconciled: bool,  // is_reconciled
  isMatched: bool,  // is_matched
  isSent: bool,  // is_sent
  createDate: date,  // create_date
  writeDate: date,  // write_date
  paymentTransactionId: int,  // payment_transaction_id
  paymentTokenId: int,  // payment_token_id
  sourcePaymentId: int,  // source_payment_id
  accountBankStatementLineRel: [{  // account_payment_account_bank_statement_line_rel, 1:N assumed
    accountBankStatementLineId: int,  // account_bank_statement_line_id
  }],
}
```

Why:
- account_payment → account_move, account_move_line, account_payment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- account_account, account_journal, account_move, account_payment_method, account_payment_method_line → account_payment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment → account_payment_account_bank_statement_line_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (3):
- **fanout_unmeasured** (account_payment_account_bank_statement_line_rel): account_payment_account_bank_statement_line_rel has no rows per account_payment in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_payment_account_bank_statement_line_rel): account_payment_account_bank_statement_line_rel is embedded in account_payment, but deleting a account_bank_statement_line row cascades to its account_payment_account_bank_statement_line_rel: the app must pull them from every account_payment document, or keep account_payment_account_bank_statement_line_rel separate
- **no_access_evidence** (account_payment): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountPaymentTerm

From `account_payment_term` with `account_payment_term_line` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  sequence: int,  // sequence
  discountDays: int,  // discount_days
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  earlyPayDiscountComputation: string,  // early_pay_discount_computation
  name: object,  // name
  note: object,  // note
  active: bool,  // active
  displayOnInvoice: bool,  // display_on_invoice
  earlyDiscount: bool,  // early_discount
  createDate: date,  // create_date
  writeDate: date,  // write_date
  discountPercentage: double,  // discount_percentage
  line: [{  // account_payment_term_line, 1:N derived
    id: int,  // id
    nbDays: int,  // nb_days
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    value: string,  // value
    delayType: string,  // delay_type
    daysNextMonth: string,  // days_next_month
    valueAmount: decimal,  // value_amount
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- account_payment_term → account_move, purchase_order, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment_term → account_payment_term_line: **embed**, owned by its parent (cascade delete or ordinal key) (derived)

Open questions (1):
- **no_access_evidence** (account_payment_term): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountReconcileModel

From `account_reconcile_model` with `account_reconcile_model_res_partner_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  companyId: int,  // company_id
  nextActivityTypeId: int,  // next_activity_type_id
  mappedPartnerId: int,  // mapped_partner_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  trigger: string,  // trigger
  matchAmount: string,  // match_amount
  matchLabel: string,  // match_label
  matchLabelParam: string,  // match_label_param
  paymentToleranceType: string,  // payment_tolerance_type
  matchingOrder: string,  // matching_order
  ruleType: string,  // rule_type
  name: object,  // name
  active: bool,  // active
  canBeProposed: bool,  // can_be_proposed
  createDate: date,  // create_date
  writeDate: date,  // write_date
  matchAmountMin: double,  // match_amount_min
  matchAmountMax: double,  // match_amount_max
  paymentTolerance: double,  // payment_tolerance
  resPartnerRel: [{  // account_reconcile_model_res_partner_rel, 1:N derived
    resPartnerId: int,  // res_partner_id
  }],
}
```

Why:
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_reconcile_model → account_move_line, account_reconcile_model_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model → account_reconcile_model_res_partner_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)

Open questions (1):
- **no_access_evidence** (account_reconcile_model): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountReconcileModelLine

From `account_reconcile_model_line` with `account_reconcile_model_line_account_tax_rel` embedded.

```js
{
  _id: int,  // id
  modelId: int,  // model_id
  companyId: int,  // company_id
  sequence: int,  // sequence
  accountId: int,  // account_id
  partnerId: int,  // partner_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  amountType: string,  // amount_type
  amountString: string,  // amount_string
  analyticDistribution: object,  // analytic_distribution
  label: object,  // label
  createDate: date,  // create_date
  writeDate: date,  // write_date
  amount: double,  // amount
  accountTaxRel: [{  // account_reconcile_model_line_account_tax_rel, 1:N assumed
    accountTaxId: int,  // account_tax_id
  }],
}
```

Why:
- account_account, account_reconcile_model → account_reconcile_model_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model_line → account_reconcile_model_line_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_reconcile_model_line_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (account_reconcile_model_line_account_tax_rel): account_reconcile_model_line_account_tax_rel is embedded in account_reconcile_model_line, but deleting a account_tax row cascades to its account_reconcile_model_line_account_tax_rel: the app must pull them from every account_reconcile_model_line document, or keep account_reconcile_model_line_account_tax_rel separate
- **no_access_evidence** (account_reconcile_model_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountReport

From `account_report` with `account_report_column`, `account_report_section_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  rootReportId: int,  // root_report_id
  countryId: int,  // country_id
  loadMoreLimit: int,  // load_more_limit
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  groupby: string,  // groupby
  userGroupby: string,  // user_groupby
  chartTemplate: string,  // chart_template
  availabilityCondition: string,  // availability_condition
  integerRounding: string,  // integer_rounding
  defaultOpeningDateFilter: string,  // default_opening_date_filter
  currencyTranslation: string,  // currency_translation
  filterMultiCompany: string,  // filter_multi_company
  filterHide0Lines: string,  // filter_hide_0_lines
  filterHierarchy: string,  // filter_hierarchy
  filterAccountType: string,  // filter_account_type
  name: object,  // name
  activeSelection: object,  // active_selection
  activeFallback: bool,  // active_fallback
  useSections: bool,  // use_sections
  onlyTaxExigible: bool,  // only_tax_exigible
  searchBar: bool,  // search_bar
  allowForeignVat: bool,  // allow_foreign_vat
  useFiscalPeriods: bool,  // use_fiscal_periods
  enableSnapshots: bool,  // enable_snapshots
  filterDateRange: bool,  // filter_date_range
  filterShowDraft: bool,  // filter_show_draft
  filterUnreconciled: bool,  // filter_unreconciled
  filterUnfoldAll: bool,  // filter_unfold_all
  filterPeriodComparison: bool,  // filter_period_comparison
  filterGrowthComparison: bool,  // filter_growth_comparison
  filterLineComparison: bool,  // filter_line_comparison
  filterJournals: bool,  // filter_journals
  filterPartner: bool,  // filter_partner
  filterAmlIrFilters: bool,  // filter_aml_ir_filters
  filterBudgets: bool,  // filter_budgets
  createDate: date,  // create_date
  writeDate: date,  // write_date
  column: [{  // account_report_column, 1:N derived
    id: int,  // id
    sequence: int,  // sequence
    customAuditActionId: int,  // custom_audit_action_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    expressionLabel: string,  // expression_label
    figureType: string,  // figure_type
    name: object,  // name
    sortable: bool,  // sortable
    blankIfZero: bool,  // blank_if_zero
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  sectionRel: [{  // account_report_section_rel, 1:N assumed
    subReportId: int,  // sub_report_id
  }],
}
```

Why:
- account_report → account_report, account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report → account_report_column: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_report → account_report_section_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_report → account_report_section_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (1):
- **no_access_evidence** (account_report): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountReportExpression

From `account_report_expression` with `account_report_external_value` embedded.

```js
{
  _id: int,  // id
  reportLineId: int,  // report_line_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  label: string,  // label
  engine: string,  // engine
  dateScope: string,  // date_scope
  figureType: string,  // figure_type
  carryoverTarget: string,  // carryover_target
  formula: string,  // formula
  subformula: string,  // subformula
  greenOnPositive: bool,  // green_on_positive
  blankIfZero: bool,  // blank_if_zero
  auditable: bool,  // auditable
  createDate: date,  // create_date
  writeDate: date,  // write_date
  accountReportExternalValue: [{  // account_report_external_value, 1:N derived
    id: int,  // id
    companyId: int,  // company_id
    carryoverOriginReportLineId: int,  // carryover_origin_report_line_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    name: string,  // name
    textValue: string,  // text_value
    carryoverOriginExpressionLabel: string,  // carryover_origin_expression_label
    date: date,  // date
    createDate: date,  // create_date
    writeDate: date,  // write_date
    value: double,  // value
  }],
}
```

Why:
- account_report_line → account_report_expression: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report_line → account_report_external_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_report_expression → account_report_external_value: **embed**, owned by its parent (cascade delete or ordinal key) (derived)

Open questions (2):
- **no_access_evidence** (account_report_expression): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_report_expression): LOB column(s) formula, subformula measured max 45 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## accountTax

From `account_tax` with `account_tax_alternatives`, `account_tax_filiation_rel`, `account_tax_purchase_order_line_rel`, `account_tax_sale_order_line_rel`, `product_supplier_taxes_rel`, `product_taxes_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  sequence: int,  // sequence
  taxGroupId: int,  // tax_group_id
  cashBasisTransitionAccountId: int,  // cash_basis_transition_account_id
  countryId: int,  // country_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  typeTaxUse: string,  // type_tax_use
  taxScope: string,  // tax_scope
  amountType: string,  // amount_type
  priceIncludeOverride: string,  // price_include_override
  taxExigibility: string,  // tax_exigibility
  name: object,  // name
  description: object,  // description
  invoiceLabel: object,  // invoice_label
  invoiceLegalNotes: object,  // invoice_legal_notes
  amount: decimal,  // amount
  isDomestic: bool,  // is_domestic
  active: bool,  // active
  includeBaseAmount: bool,  // include_base_amount
  isBaseAffected: bool,  // is_base_affected
  analytic: bool,  // analytic
  createDate: date,  // create_date
  writeDate: date,  // write_date
  ublCiiTaxCategoryCode: string,  // ubl_cii_tax_category_code
  ublCiiTaxExemptionReason: string,  // ubl_cii_tax_exemption_reason
  ublCiiTaxExemptionReasonCode: string,  // ubl_cii_tax_exemption_reason_code
  l10nUsStateId: int,  // l10n_us_state_id
  l10nUsCountyId: int,  // l10n_us_county_id
  l10nUsCityId: int,  // l10n_us_city_id
  l10nUsExemptParentTaxId: int,  // l10n_us_exempt_parent_tax_id
  l10nUsNontaxableParentTaxId: int,  // l10n_us_nontaxable_parent_tax_id
  l10nUsJurisdictionType: string,  // l10n_us_jurisdiction_type
  alternatives: [{  // account_tax_alternatives, 1:N assumed
    srcTaxId: int,  // src_tax_id
  }],
  filiationRel: [{  // account_tax_filiation_rel, 1:N assumed
    parentTax: int,  // parent_tax
  }],
  purchaseOrderLineRel: [{  // account_tax_purchase_order_line_rel, 1:N assumed
    purchaseOrderLineId: int,  // purchase_order_line_id
  }],
  saleOrderLineRel: [{  // account_tax_sale_order_line_rel, 1:N assumed
    saleOrderLineId: int,  // sale_order_line_id
  }],
  productSupplierTaxesRel: [{  // product_supplier_taxes_rel, 1:N assumed
    prodId: int,  // prod_id
  }],
  productTaxesRel: [{  // product_taxes_rel, 1:N assumed
    prodId: int,  // prod_id
  }],
}
```

Why:
- account_tax → account_account_tax_default_rel, account_fiscal_position_account_tax_rel, account_reconcile_model_line_account_tax_rel, account_tax_alternatives, account_tax_filiation_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax → account_move_line, account_tax, account_tax_repartition_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_tax → account_move_line_account_tax_rel: **reference**, too many children per parent (measured) (derived)
- account_account, account_tax_group → account_tax: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_tax → account_tax_alternatives, account_tax_filiation_rel, account_tax_purchase_order_line_rel, account_tax_sale_order_line_rel, product_supplier_taxes_rel, product_taxes_rel: **embed**, a link table, kept as an array on this side (assumed)
- purchase_order_line → account_tax_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → account_tax_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_supplier_taxes_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_taxes_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **cascade_into_embed** (account_tax_purchase_order_line_rel): account_tax_purchase_order_line_rel is embedded in account_tax, but deleting a purchase_order_line row cascades to its account_tax_purchase_order_line_rel: the app must pull them from every account_tax document, or keep account_tax_purchase_order_line_rel separate
- **cascade_into_embed** (account_tax_sale_order_line_rel): account_tax_sale_order_line_rel is embedded in account_tax, but deleting a sale_order_line row cascades to its account_tax_sale_order_line_rel: the app must pull them from every account_tax document, or keep account_tax_sale_order_line_rel separate
- **cascade_into_embed** (product_supplier_taxes_rel): product_supplier_taxes_rel is embedded in account_tax, but deleting a product_template row cascades to its product_supplier_taxes_rel: the app must pull them from every account_tax document, or keep product_supplier_taxes_rel separate
- **cascade_into_embed** (product_taxes_rel): product_taxes_rel is embedded in account_tax, but deleting a product_template row cascades to its product_taxes_rel: the app must pull them from every account_tax document, or keep product_taxes_rel separate
- **no_access_evidence** (account_tax): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productAttribute

From `product_attribute` with `product_attribute_product_template_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  createVariant: string,  // create_variant
  displayType: string,  // display_type
  name: object,  // name
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  productTemplateRel: [{  // product_attribute_product_template_rel, 1:N assumed
    productTemplateId: int,  // product_template_id
  }],
}
```

Why:
- product_attribute → product_attribute_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_attribute_product_template_rel: **reference**, a link table, embedded on the other side (assumed)
- product_attribute → product_attribute_value, product_template_attribute_line, product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **cascade_into_embed** (product_attribute_product_template_rel): product_attribute_product_template_rel is embedded in product_attribute, but deleting a product_template row cascades to its product_attribute_product_template_rel: the app must pull them from every product_attribute document, or keep product_attribute_product_template_rel separate
- **no_access_evidence** (product_attribute): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productAttributeValue

From `product_attribute_value` with `product_attribute_value_product_template_attribute_line_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  attributeId: int,  // attribute_id
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  htmlColor: string,  // html_color
  name: object,  // name
  isCustom: bool,  // is_custom
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  defaultExtraPrice: double,  // default_extra_price
  productTemplateAttributeLineRel: [{  // product_attribute_value_product_template_attribute_line_rel, 1:N assumed
    productTemplateAttributeLineId: int,  // product_template_attribute_line_id
  }],
}
```

Why:
- product_attribute → product_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_line → product_attribute_value_product_template_attribute_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_attribute_value → product_attribute_value_product_template_attribute_line_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_attribute_value → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **cascade_into_embed** (product_attribute_value_product_template_attribute_line_rel): product_attribute_value_product_template_attribute_line_rel is embedded in product_attribute_value, but deleting a product_template_attribute_line row cascades to its product_attribute_value_product_template_attribute_line_rel: the app must pull them from every product_attribute_value document, or keep product_attribute_value_product_template_attribute_line_rel separate
- **no_access_evidence** (product_attribute_value): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productCategory

From `product_category` with `product_category_stock_picking_type_rel` embedded.

```js
{
  _id: int,  // id
  parentId: int,  // parent_id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  parentPath: string,  // parent_path
  name: object,  // name
  productPropertiesDefinition: object,  // product_properties_definition
  createDate: date,  // create_date
  writeDate: date,  // write_date
  propertyAccountIncomeCategId: object,  // property_account_income_categ_id
  propertyAccountExpenseCategId: object,  // property_account_expense_categ_id
  propertyValuation: object,  // property_valuation
  propertyStockValuationAccountId: object,  // property_stock_valuation_account_id
  propertyStockJournal: object,  // property_stock_journal
  propertyCostMethod: object,  // property_cost_method
  propertyPriceDifferenceAccountId: object,  // property_price_difference_account_id
  removalStrategyId: int,  // removal_strategy_id
  packagingReserveMethod: string,  // packaging_reserve_method
  propertyAccountBillsToReceiveId: object,  // property_account_bills_to_receive_id
  propertyAccountBilledNotReceivedId: object,  // property_account_billed_not_received_id
  propertyAccountInvoicesToIssueId: object,  // property_account_invoices_to_issue_id
  propertyAccountInvoicedNotDeliveredId: object,  // property_account_invoiced_not_delivered_id
  stockPickingTypeRel: [{  // product_category_stock_picking_type_rel, 1:N assumed
    stockPickingTypeId: int,  // stock_picking_type_id
  }],
}
```

Why:
- product_category → product_category, product_pricelist_item, product_template, stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_removal → product_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_type → product_category_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category → product_category_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (product_category_stock_picking_type_rel): product_category_stock_picking_type_rel is embedded in product_category, but deleting a stock_picking_type row cascades to its product_category_stock_picking_type_rel: the app must pull them from every product_category document, or keep product_category_stock_picking_type_rel separate
- **no_access_evidence** (product_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productCombo

From `product_combo` with `product_combo_product_template_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  productTemplateRel: [{  // product_combo_product_template_rel, 1:N assumed
    productTemplateId: int,  // product_template_id
  }],
}
```

Why:
- product_combo → product_combo_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo → product_combo_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_combo_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (product_combo_product_template_rel): product_combo_product_template_rel is embedded in product_combo, but deleting a product_template row cascades to its product_combo_product_template_rel: the app must pull them from every product_combo document, or keep product_combo_product_template_rel separate
- **no_access_evidence** (product_combo): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productProduct

From `product_product` with `customer_product_reference`, `product_value`, `product_product_uom_uom_rel`, `product_variant_combination` embedded.

```js
{
  _id: int,  // id
  productTmplId: int,  // product_tmpl_id
  baseUnitId: int,  // base_unit_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  defaultCode: string,  // default_code
  barcode: string,  // barcode
  combinationIndices: string,  // combination_indices
  standardPrice: object,  // standard_price
  qtyAvailable: object,  // qty_available
  lstPrice: decimal,  // lst_price
  volume: decimal,  // volume
  weight: decimal,  // weight
  baseUnitCount: decimal,  // base_unit_count
  active: bool,  // active
  canImageVariant1024BeZoomed: bool,  // can_image_variant_1024_be_zoomed
  isFavorite: bool,  // is_favorite
  writeDate: date,  // write_date
  createDate: date,  // create_date
  lotPropertiesDefinition: object,  // lot_properties_definition
  customerProductReference: [{  // customer_product_reference, 1:N derived
    partnerId: int,  // partner_id
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    customerProductReference: string,  // customer_product_reference
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  productValue: [{  // product_value, 1:N derived
    id: int,  // id
    lotId: int,  // lot_id
    moveId: int,  // move_id
    companyId: int,  // company_id
    userId: int,  // user_id
    accountMoveId: int,  // account_move_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    description: string,  // description
    quantity: decimal,  // quantity
    oldCost: decimal,  // old_cost
    newCost: decimal,  // new_cost
    oldValue: decimal,  // old_value
    newValue: decimal,  // new_value
    value: decimal,  // value
    date: date,  // date
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  uomUomRel: [{  // product_product_uom_uom_rel, 1:N assumed
    uomUomId: int,  // uom_uom_id
  }],
  productVariantCombination: [{  // product_variant_combination, 1:N assumed
    productTemplateAttributeValueId: int,  // product_template_attribute_value_id
  }],
}
```

Why:
- product_product → account_move_line, product_combo_item, product_pricelist_item, product_supplierinfo, product_uom, purchase_order_line, sale_order_line, stock_lot, stock_move, stock_move_line, stock_putaway_rule, stock_quant, stock_storage_category_capacity, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_product → customer_product_reference, product_value: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- product_base_unit, product_template → product_product: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_product → product_product_uom_uom_rel, product_variant_combination: **embed**, a link table, kept as an array on this side (assumed)
- uom_uom → product_product_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- product_product → product_tag_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move, stock_lot, stock_move → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template_attribute_value → product_variant_combination: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (product_product_uom_uom_rel): product_product_uom_uom_rel is embedded in product_product, but deleting a uom_uom row cascades to its product_product_uom_uom_rel: the app must pull them from every product_product document, or keep product_product_uom_uom_rel separate
- **no_access_evidence** (product_product): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productTag

From `product_tag` with `product_tag_product_product_rel`, `product_tag_product_template_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  color: string,  // color
  name: object,  // name
  visibleToCustomers: bool,  // visible_to_customers
  createDate: date,  // create_date
  writeDate: date,  // write_date
  productProductRel: [{  // product_tag_product_product_rel, 1:N assumed
    productProductId: int,  // product_product_id
  }],
  productTemplateRel: [{  // product_tag_product_template_rel, 1:N assumed
    productTemplateId: int,  // product_template_id
  }],
}
```

Why:
- product_product → product_tag_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- product_tag → product_tag_product_product_rel, product_tag_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_tag_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **cascade_into_embed** (product_tag_product_product_rel): product_tag_product_product_rel is embedded in product_tag, but deleting a product_product row cascades to its product_tag_product_product_rel: the app must pull them from every product_tag document, or keep product_tag_product_product_rel separate
- **cascade_into_embed** (product_tag_product_template_rel): product_tag_product_template_rel is embedded in product_tag, but deleting a product_template row cascades to its product_tag_product_template_rel: the app must pull them from every product_tag document, or keep product_tag_product_template_rel separate
- **no_access_evidence** (product_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productTemplate

From `product_template` with `product_optional_rel`, `product_template_uom_uom_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  categId: int,  // categ_id
  uomId: int,  // uom_id
  companyId: int,  // company_id
  color: int,  // color
  baseUnitId: int,  // base_unit_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  type: string,  // type
  serviceTracking: string,  // service_tracking
  barcode: string,  // barcode
  defaultCode: string,  // default_code
  name: object,  // name
  description: object,  // description
  descriptionPurchase: object,  // description_purchase
  descriptionSale: object,  // description_sale
  productProperties: object,  // product_properties
  listPrice: decimal,  // list_price
  volume: decimal,  // volume
  weight: decimal,  // weight
  baseUnitCount: decimal,  // base_unit_count
  isStorable: bool,  // is_storable
  saleOk: bool,  // sale_ok
  purchaseOk: bool,  // purchase_ok
  active: bool,  // active
  canImage1024BeZoomed: bool,  // can_image_1024_be_zoomed
  hasConfigurableAttributes: bool,  // has_configurable_attributes
  isFavorite: bool,  // is_favorite
  createDate: date,  // create_date
  writeDate: date,  // write_date
  propertyAccountIncomeId: object,  // property_account_income_id
  propertyAccountExpenseId: object,  // property_account_expense_id
  lotSequenceId: int,  // lot_sequence_id
  tracking: string,  // tracking
  responsibleId: object,  // responsible_id
  propertyStockProduction: object,  // property_stock_production
  propertyStockInventory: object,  // property_stock_inventory
  descriptionPicking: object,  // description_picking
  descriptionPickingout: object,  // description_pickingout
  descriptionPickingin: object,  // description_pickingin
  purchaseMethod: string,  // purchase_method
  purchaseLineWarnMsg: string,  // purchase_line_warn_msg
  lotValuated: bool,  // lot_valuated
  serviceType: string,  // service_type
  reinvoicePolicy: string,  // reinvoice_policy
  invoicePolicy: string,  // invoice_policy
  saleDelay: object,  // sale_delay
  saleLineWarnMsg: string,  // sale_line_warn_msg
  productOptionalRel: [{  // product_optional_rel, 1:N assumed
    srcId: int,  // src_id
  }],
  uomUomRel: [{  // product_template_uom_uom_rel, 1:N assumed
    uomUomId: int,  // uom_uom_id
  }],
}
```

Why:
- product_template → account_account_tag_product_template_rel, product_attribute_product_template_rel, product_combo_product_template_rel, product_optional_rel, product_supplier_taxes_rel, product_tag_product_template_rel, product_taxes_rel, stock_route_product: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_optional_rel, product_template_uom_uom_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_pricelist_item, product_product, product_supplierinfo, product_template_attribute_line, product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_base_unit, product_category, uom_uom → product_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- uom_uom → product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **cascade_into_embed** (product_template_uom_uom_rel): product_template_uom_uom_rel is embedded in product_template, but deleting a uom_uom row cascades to its product_template_uom_uom_rel: the app must pull them from every product_template document, or keep product_template_uom_uom_rel separate
- **no_access_evidence** (product_template): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (product_template): LOB column(s) purchase_line_warn_msg, sale_line_warn_msg measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## productTemplateAttributeValue

From `product_template_attribute_value` with `product_template_attribute_excluded_value_ids_rel`, `product_template_attribute_value_purchase_order_line_rel`, `product_template_attribute_value_sale_order_line_rel`, `template_attribute_value_stock_move_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  productAttributeValueId: int,  // product_attribute_value_id
  attributeLineId: int,  // attribute_line_id
  productTmplId: int,  // product_tmpl_id
  attributeId: int,  // attribute_id
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  priceExtra: decimal,  // price_extra
  ptavActive: bool,  // ptav_active
  showPriceExtra: bool,  // show_price_extra
  createDate: date,  // create_date
  writeDate: date,  // write_date
  productTemplateAttributeExcludedValueIdsRel: [{  // product_template_attribute_excluded_value_ids_rel, 1:N assumed
    productTemplateAttributeValueId: int,  // product_template_attribute_value_id
  }],
  purchaseOrderLineRel: [{  // product_template_attribute_value_purchase_order_line_rel, 1:N assumed
    purchaseOrderLineId: int,  // purchase_order_line_id
  }],
  saleOrderLineRel: [{  // product_template_attribute_value_sale_order_line_rel, 1:N assumed
    saleOrderLineId: int,  // sale_order_line_id
  }],
  templateAttributeValueStockMoveRel: [{  // template_attribute_value_stock_move_rel, 1:N assumed
    moveId: int,  // move_id
  }],
}
```

Why:
- product_template_attribute_value → product_attribute_custom_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel, product_template_attribute_value_purchase_order_line_rel, product_template_attribute_value_sale_order_line_rel, template_attribute_value_stock_move_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel, product_variant_combination: **reference**, a link table, embedded on the other side (assumed)
- product_attribute_value, product_attribute, product_template_attribute_line, product_template → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order_line → product_template_attribute_value_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → product_template_attribute_value_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → template_attribute_value_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **cascade_into_embed** (product_template_attribute_value_purchase_order_line_rel): product_template_attribute_value_purchase_order_line_rel is embedded in product_template_attribute_value, but deleting a purchase_order_line row cascades to its product_template_attribute_value_purchase_order_line_rel: the app must pull them from every product_template_attribute_value document, or keep product_template_attribute_value_purchase_order_line_rel separate
- **cascade_into_embed** (product_template_attribute_value_sale_order_line_rel): product_template_attribute_value_sale_order_line_rel is embedded in product_template_attribute_value, but deleting a sale_order_line row cascades to its product_template_attribute_value_sale_order_line_rel: the app must pull them from every product_template_attribute_value document, or keep product_template_attribute_value_sale_order_line_rel separate
- **cascade_into_embed** (template_attribute_value_stock_move_rel): template_attribute_value_stock_move_rel is embedded in product_template_attribute_value, but deleting a stock_move row cascades to its template_attribute_value_stock_move_rel: the app must pull them from every product_template_attribute_value document, or keep template_attribute_value_stock_move_rel separate
- **no_access_evidence** (product_template_attribute_value): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## purchaseOrder

From `purchase_order` with `purchase_order_stock_picking_rel` embedded.

```js
{
  _id: int,  // id
  partnerId: int,  // partner_id
  destAddressId: int,  // dest_address_id
  currencyId: int,  // currency_id
  invoiceCount: int,  // invoice_count
  fiscalPositionId: int,  // fiscal_position_id
  paymentTermId: int,  // payment_term_id
  incotermId: int,  // incoterm_id
  userId: int,  // user_id
  companyId: int,  // company_id
  reminderDateBeforeReceipt: int,  // reminder_date_before_receipt
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  accessToken: string,  // access_token
  name: string,  // name
  priority: string,  // priority
  origin: string,  // origin
  partnerRef: string,  // partner_ref
  state: string,  // state
  invoiceStatus: string,  // invoice_status
  documentTaxMode: string,  // document_tax_mode
  incotermLocation: string,  // incoterm_location
  receiptStatus: string,  // receipt_status
  note: string,  // note
  amountUntaxed: decimal,  // amount_untaxed
  amountTax: decimal,  // amount_tax
  amountTotal: decimal,  // amount_total
  amountTotalCc: decimal,  // amount_total_cc
  currencyRate: decimal,  // currency_rate
  locked: bool,  // locked
  acknowledged: bool,  // acknowledged
  receiptReminderEmail: bool,  // receipt_reminder_email
  dateOrder: date,  // date_order
  dateApprove: date,  // date_approve
  datePlanned: date,  // date_planned
  dateCalendarStart: date,  // date_calendar_start
  createDate: date,  // create_date
  writeDate: date,  // write_date
  pickingTypeId: int,  // picking_type_id
  effectiveDate: date,  // effective_date
  datePromised: date,  // date_promised
  stockPickingRel: [{  // purchase_order_stock_picking_rel, 1:N assumed
    stockPickingId: int,  // stock_picking_id
  }],
}
```

Why:
- purchase_order → account_move_purchase_order_rel, stock_reference_purchase_rel: **reference**, a link table, embedded on the other side (assumed)
- account_fiscal_position, account_incoterms, account_payment_term, stock_picking_type → purchase_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order → purchase_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order → purchase_order_stock_picking_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_picking → purchase_order_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **cascade_into_embed** (purchase_order_stock_picking_rel): purchase_order_stock_picking_rel is embedded in purchase_order, but deleting a stock_picking row cascades to its purchase_order_stock_picking_rel: the app must pull them from every purchase_order document, or keep purchase_order_stock_picking_rel separate
- **no_access_evidence** (purchase_order): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (purchase_order): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## purchaseOrderLine

From `purchase_order_line` with `purchase_order_line_accrual_move_rel` embedded.

```js
{
  _id: int,  // id
  productId: int,  // product_id
  sequence: int,  // sequence
  uomId: int,  // uom_id
  orderId: int,  // order_id
  companyId: int,  // company_id
  partnerId: int,  // partner_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  qtyReceivedMethod: string,  // qty_received_method
  displayType: string,  // display_type
  analyticDistribution: object,  // analytic_distribution
  name: string,  // name
  productQty: decimal,  // product_qty
  discount: decimal,  // discount
  priceUnit: decimal,  // price_unit
  priceUnitProductUom: decimal,  // price_unit_product_uom
  priceSubtotal: decimal,  // price_subtotal
  priceTotal: decimal,  // price_total
  qtyInvoiced: decimal,  // qty_invoiced
  qtyReceived: decimal,  // qty_received
  qtyReceivedManual: decimal,  // qty_received_manual
  qtyToInvoice: decimal,  // qty_to_invoice
  qtyToInvoiceRaw: decimal,  // qty_to_invoice_raw
  isDownpayment: bool,  // is_downpayment
  datePlanned: date,  // date_planned
  createDate: date,  // create_date
  writeDate: date,  // write_date
  productUomQty: double,  // product_uom_qty
  priceTax: double,  // price_tax
  nonDeductibleTax: double,  // non_deductible_tax
  technicalPriceUnit: double,  // technical_price_unit
  orderpointId: int,  // orderpoint_id
  forecastedLocationId: int,  // forecasted_location_id
  productDescriptionVariants: string,  // product_description_variants
  propagateCancel: bool,  // propagate_cancel
  datePromised: date,  // date_promised
  saleLineId: int,  // sale_line_id
  accrualMoveRel: [{  // purchase_order_line_accrual_move_rel, 1:N assumed
    moveId: int,  // move_id
  }],
}
```

Why:
- purchase_order_line → account_move_line, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order_line → account_tax_purchase_order_line_rel, product_template_attribute_value_purchase_order_line_rel, stock_move_created_purchase_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_location, purchase_order, stock_warehouse_orderpoint, product_product, sale_order_line, uom_uom → purchase_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move → purchase_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- purchase_order_line → purchase_order_line_accrual_move_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (4):
- **fanout_unmeasured** (purchase_order_line_accrual_move_rel): purchase_order_line_accrual_move_rel has no rows per purchase_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (purchase_order_line_accrual_move_rel): purchase_order_line_accrual_move_rel is embedded in purchase_order_line, but deleting a account_move row cascades to its purchase_order_line_accrual_move_rel: the app must pull them from every purchase_order_line document, or keep purchase_order_line_accrual_move_rel separate
- **no_access_evidence** (purchase_order_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (purchase_order_line): LOB column(s) name measured max 38 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## saleOrder

From `sale_order` with `sale_order_tag_rel`, `sale_order_transaction_rel` embedded.

```js
{
  _id: int,  // id
  campaignId: int,  // campaign_id
  sourceId: int,  // source_id
  mediumId: int,  // medium_id
  companyId: int,  // company_id
  partnerId: int,  // partner_id
  pendingEmailTemplateId: int,  // pending_email_template_id
  journalId: int,  // journal_id
  partnerInvoiceId: int,  // partner_invoice_id
  partnerShippingId: int,  // partner_shipping_id
  fiscalPositionId: int,  // fiscal_position_id
  paymentTermId: int,  // payment_term_id
  preferredPaymentMethodLineId: int,  // preferred_payment_method_line_id
  pricelistId: int,  // pricelist_id
  currencyId: int,  // currency_id
  userId: int,  // user_id
  teamId: int,  // team_id
  incoterm: int,  // incoterm
  analyticAccountId: int,  // analytic_account_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  utmReference: string,  // utm_reference
  accessToken: string,  // access_token
  name: string,  // name
  state: string,  // state
  clientOrderRef: string,  // client_order_ref
  origin: string,  // origin
  reference: string,  // reference
  signedBy: string,  // signed_by
  documentTaxMode: string,  // document_tax_mode
  incotermLocation: string,  // incoterm_location
  invoiceStatus: string,  // invoice_status
  deliveryStatus: string,  // delivery_status
  validityDate: date,  // validity_date
  note: string,  // note
  currencyRate: decimal,  // currency_rate
  amountUntaxed: decimal,  // amount_untaxed
  amountTax: decimal,  // amount_tax
  amountTotal: decimal,  // amount_total
  amountUnpaid: decimal,  // amount_unpaid
  locked: bool,  // locked
  invoicingClosed: bool,  // invoicing_closed
  requireSignature: bool,  // require_signature
  invoiceOverages: bool,  // invoice_overages
  createDate: date,  // create_date
  commitmentDate: date,  // commitment_date
  dateOrder: date,  // date_order
  signedOn: date,  // signed_on
  writeDate: date,  // write_date
  prepaymentPercent: double,  // prepayment_percent
  warehouseId: int,  // warehouse_id
  pickingPolicy: string,  // picking_policy
  effectiveDate: date,  // effective_date
  tagRel: [{  // sale_order_tag_rel, 1:N derived
    tagId: int,  // tag_id
  }],
  transactionRel: [{  // sale_order_transaction_rel, 1:N assumed
    transactionId: int,  // transaction_id
  }],
}
```

Why:
- account_fiscal_position, account_incoterms, account_journal, account_payment_term, account_payment_method_line, product_pricelist, stock_warehouse → sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- sale_order → sale_order_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- sale_order → sale_order_tag_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- sale_order → sale_order_transaction_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- sale_order → stock_reference_sale_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (sale_order_transaction_rel): sale_order_transaction_rel has no rows per sale_order in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (sale_order): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (sale_order): LOB column(s) note measured max 182 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## saleOrderLine

From `sale_order_line` with `sale_order_line_accrual_move_rel`, `sale_order_line_invoice_rel`, `sale_order_line_stock_route_rel` embedded.

```js
{
  _id: int,  // id
  productId: int,  // product_id
  orderId: int,  // order_id
  sequence: int,  // sequence
  companyId: int,  // company_id
  currencyId: int,  // currency_id
  orderPartnerId: int,  // order_partner_id
  salesmanId: int,  // salesman_id
  productUomId: int,  // product_uom_id
  linkedLineId: int,  // linked_line_id
  comboItemId: int,  // combo_item_id
  customerLead: int,  // customer_lead
  sectionUomId: int,  // section_uom_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  state: string,  // state
  displayType: string,  // display_type
  virtualId: string,  // virtual_id
  linkedVirtualId: string,  // linked_virtual_id
  qtyDeliveredMethod: string,  // qty_delivered_method
  invoiceStatus: string,  // invoice_status
  analyticDistribution: object,  // analytic_distribution
  extraTaxData: object,  // extra_tax_data
  name: string,  // name
  productUomQty: decimal,  // product_uom_qty
  priceUnit: decimal,  // price_unit
  discount: decimal,  // discount
  priceSubtotal: decimal,  // price_subtotal
  priceTotal: decimal,  // price_total
  priceReduceTaxexcl: decimal,  // price_reduce_taxexcl
  priceReduceTaxinc: decimal,  // price_reduce_taxinc
  qtyDelivered: decimal,  // qty_delivered
  qtyInvoiced: decimal,  // qty_invoiced
  qtyToInvoice: decimal,  // qty_to_invoice
  untaxedAmountInvoiced: decimal,  // untaxed_amount_invoiced
  untaxedAmountToInvoice: decimal,  // untaxed_amount_to_invoice
  sectionQty: decimal,  // section_qty
  isDownpayment: bool,  // is_downpayment
  isExpense: bool,  // is_expense
  collapsePrices: bool,  // collapse_prices
  collapseComposition: bool,  // collapse_composition
  createDate: date,  // create_date
  writeDate: date,  // write_date
  technicalPriceUnit: double,  // technical_price_unit
  priceTax: double,  // price_tax
  ediCustomerProductRef: string,  // edi_customer_product_ref
  warehouseId: int,  // warehouse_id
  accrualMoveRel: [{  // sale_order_line_accrual_move_rel, 1:N assumed
    moveId: int,  // move_id
  }],
  invoiceRel: [{  // sale_order_line_invoice_rel, 1:N assumed
    invoiceLineId: int,  // invoice_line_id
  }],
  stockRouteRel: [{  // sale_order_line_stock_route_rel, 1:N assumed
    stockRouteId: int,  // stock_route_id
  }],
}
```

Why:
- sale_order_line → account_tax_sale_order_line_rel, product_template_attribute_value_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → product_attribute_custom_value, purchase_order_line, sale_order_line, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo_item, sale_order, product_product, uom_uom, stock_warehouse → sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move → sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → sale_order_line_accrual_move_rel, sale_order_line_invoice_rel, sale_order_line_stock_route_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_move_line → sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → sale_order_line_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **fanout_unmeasured** (sale_order_line_accrual_move_rel): sale_order_line_accrual_move_rel has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (sale_order_line_accrual_move_rel): sale_order_line_accrual_move_rel is embedded in sale_order_line, but deleting a account_move row cascades to its sale_order_line_accrual_move_rel: the app must pull them from every sale_order_line document, or keep sale_order_line_accrual_move_rel separate
- **cascade_into_embed** (sale_order_line_invoice_rel): sale_order_line_invoice_rel is embedded in sale_order_line, but deleting a account_move_line row cascades to its sale_order_line_invoice_rel: the app must pull them from every sale_order_line document, or keep sale_order_line_invoice_rel separate
- **no_access_evidence** (sale_order_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (sale_order_line): LOB column(s) name measured max 45 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## stockLocation

From `stock_location` with `stock_location_stock_picking_type_rel` embedded.

```js
{
  _id: int,  // id
  locationId: int,  // location_id
  companyId: int,  // company_id
  removalStrategyId: int,  // removal_strategy_id
  cyclicInventoryFrequency: int,  // cyclic_inventory_frequency
  warehouseId: int,  // warehouse_id
  storageCategoryId: int,  // storage_category_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  completeName: string,  // complete_name
  usage: string,  // usage
  parentPath: string,  // parent_path
  barcode: string,  // barcode
  lastInventoryDate: date,  // last_inventory_date
  nextInventoryDate: date,  // next_inventory_date
  active: bool,  // active
  replenishLocation: bool,  // replenish_location
  createDate: date,  // create_date
  writeDate: date,  // write_date
  valuationAccountId: int,  // valuation_account_id
  stockPickingTypeRel: [{  // stock_location_stock_picking_type_rel, 1:N assumed
    stockPickingTypeId: int,  // stock_picking_type_id
  }],
}
```

Why:
- stock_location → purchase_order_line, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_picking, stock_picking_type, stock_putaway_rule, stock_quant, stock_rule, stock_warehouse, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_removal, stock_storage_category, account_account, stock_warehouse → stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_type → stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_location → stock_location_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (3):
- **cascade_into_embed** (stock_location_stock_picking_type_rel): stock_location_stock_picking_type_rel is embedded in stock_location, but deleting a stock_picking_type row cascades to its stock_location_stock_picking_type_rel: the app must pull them from every stock_location document, or keep stock_location_stock_picking_type_rel separate
- **no_access_evidence** (stock_location): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockMove

From `stock_move` with `account_analytic_line_stock_move_rel`, `stock_move_created_purchase_line_rel`, `stock_move_move_rel`, `stock_move_stock_scrap_reason_tag_rel` embedded.

```js
{
  _id: int,  // id
  productId: int,  // product_id
  sequence: int,  // sequence
  companyId: int,  // company_id
  uomId: int,  // uom_id
  locationId: int,  // location_id
  locationDestId: int,  // location_dest_id
  forecastedLocationId: int,  // forecasted_location_id
  partnerId: int,  // partner_id
  pickingId: int,  // picking_id
  ruleId: int,  // rule_id
  pickingTypeId: int,  // picking_type_id
  originReturnedMoveId: int,  // origin_returned_move_id
  restrictPartnerId: int,  // restrict_partner_id
  warehouseId: int,  // warehouse_id
  nextSerialCount: int,  // next_serial_count
  orderpointId: int,  // orderpoint_id
  packagingUomId: int,  // packaging_uom_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  priority: string,  // priority
  state: string,  // state
  origin: string,  // origin
  procureMethod: string,  // procure_method
  inventoryName: string,  // inventory_name
  reference: string,  // reference
  nextSerial: string,  // next_serial
  reservationDate: date,  // reservation_date
  descriptionPickingManual: string,  // description_picking_manual
  productQty: decimal,  // product_qty
  productUomQty: decimal,  // product_uom_qty
  quantity: decimal,  // quantity
  quantityProductUom: decimal,  // quantity_product_uom
  picked: bool,  // picked
  isScrap: bool,  // is_scrap
  propagateCancel: bool,  // propagate_cancel
  isInventory: bool,  // is_inventory
  additional: bool,  // additional
  shouldReplenishScrapped: bool,  // should_replenish_scrapped
  date: date,  // date
  dateDeadline: date,  // date_deadline
  delayAlertDate: date,  // delay_alert_date
  createDate: date,  // create_date
  writeDate: date,  // write_date
  priceUnit: double,  // price_unit
  packagingUomQty: double,  // packaging_uom_qty
  accountMoveId: int,  // account_move_id
  value: decimal,  // value
  toRefund: bool,  // to_refund
  isIn: bool,  // is_in
  isOut: bool,  // is_out
  isDropship: bool,  // is_dropship
  purchaseLineId: int,  // purchase_line_id
  saleLineId: int,  // sale_line_id
  accountAnalyticLineStockMoveRel: [{  // account_analytic_line_stock_move_rel, 1:N assumed
    accountAnalyticLineId: int,  // account_analytic_line_id
  }],
  createdPurchaseLineRel: [{  // stock_move_created_purchase_line_rel, 1:N assumed
    createdPurchaseLineId: int,  // created_purchase_line_id
  }],
  moveRel: [{  // stock_move_move_rel, 1:N assumed
    moveOrigId: int,  // move_orig_id
  }],
  stockScrapReasonTagRel: [{  // stock_move_stock_scrap_reason_tag_rel, 1:N assumed
    stockScrapReasonTagId: int,  // stock_scrap_reason_tag_id
  }],
}
```

Why:
- stock_move → account_analytic_line_stock_move_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- stock_move → account_move_line, stock_move, stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_move → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_move, stock_location, stock_warehouse_orderpoint, uom_uom, stock_picking, stock_picking_type, product_product, purchase_order_line, stock_rule, sale_order_line, stock_warehouse → stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order_line → stock_move_created_purchase_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → stock_move_created_purchase_line_rel, stock_move_move_rel, stock_move_stock_scrap_reason_tag_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_move → stock_move_move_rel, stock_reference_move_rel, stock_route_move, template_attribute_value_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **fanout_unmeasured** (account_analytic_line_stock_move_rel): account_analytic_line_stock_move_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (stock_move_created_purchase_line_rel): stock_move_created_purchase_line_rel is embedded in stock_move, but deleting a purchase_order_line row cascades to its stock_move_created_purchase_line_rel: the app must pull them from every stock_move document, or keep stock_move_created_purchase_line_rel separate
- **cascade_into_embed** (stock_move_stock_scrap_reason_tag_rel): stock_move_stock_scrap_reason_tag_rel is embedded in stock_move, but deleting a stock_scrap_reason_tag row cascades to its stock_move_stock_scrap_reason_tag_rel: the app must pull them from every stock_move document, or keep stock_move_stock_scrap_reason_tag_rel separate
- **no_access_evidence** (stock_move): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (stock_move): LOB column(s) description_picking_manual measured max 49 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## stockMoveLine

From `stock_move_line` with `stock_move_line_consume_rel` embedded.

```js
{
  _id: int,  // id
  pickingId: int,  // picking_id
  moveId: int,  // move_id
  companyId: int,  // company_id
  productId: int,  // product_id
  uomId: int,  // uom_id
  packageId: int,  // package_id
  lotId: int,  // lot_id
  resultPackageId: int,  // result_package_id
  packageHistoryId: int,  // package_history_id
  ownerId: int,  // owner_id
  locationId: int,  // location_id
  locationDestId: int,  // location_dest_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  lotName: string,  // lot_name
  state: string,  // state
  quantity: decimal,  // quantity
  quantityProductUom: decimal,  // quantity_product_uom
  picked: bool,  // picked
  isEntirePack: bool,  // is_entire_pack
  date: date,  // date
  createDate: date,  // create_date
  writeDate: date,  // write_date
  consumeRel: [{  // stock_move_line_consume_rel, 1:N assumed
    produceLineId: int,  // produce_line_id
  }],
}
```

Why:
- stock_location, stock_lot, stock_move, stock_package_history, stock_package, stock_picking, product_product, uom_uom → stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_move_line → stock_move_line_consume_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_move_line → stock_move_line_consume_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **fanout_unmeasured** (stock_move_line_consume_rel): stock_move_line_consume_rel has no rows per stock_move_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (stock_move_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockPackageHistory

From `stock_package_history` with `stock_package_history_stock_picking_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  locationId: int,  // location_id
  locationDestId: int,  // location_dest_id
  packageId: int,  // package_id
  parentOrigId: int,  // parent_orig_id
  parentDestId: int,  // parent_dest_id
  outermostDestId: int,  // outermost_dest_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  packageName: string,  // package_name
  parentOrigName: string,  // parent_orig_name
  parentDestName: string,  // parent_dest_name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  stockPickingRel: [{  // stock_package_history_stock_picking_rel, 1:N assumed
    stockPickingId: int,  // stock_picking_id
  }],
}
```

Why:
- stock_package_history → stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_location, stock_package → stock_package_history: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_package_history → stock_package_history_stock_picking_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_picking → stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (stock_package_history_stock_picking_rel): stock_package_history_stock_picking_rel is embedded in stock_package_history, but deleting a stock_picking row cascades to its stock_package_history_stock_picking_rel: the app must pull them from every stock_package_history document, or keep stock_package_history_stock_picking_rel separate
- **no_access_evidence** (stock_package_history): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockPackageType

From `stock_package_type` with `stock_package_type_stock_putaway_rule_rel`, `stock_package_type_stock_route_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  sequenceId: int,  // sequence_id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  barcode: string,  // barcode
  packageUse: string,  // package_use
  createDate: date,  // create_date
  writeDate: date,  // write_date
  height: double,  // height
  width: double,  // width
  packagingLength: double,  // packaging_length
  baseWeight: double,  // base_weight
  maxWeight: double,  // max_weight
  stockPutawayRuleRel: [{  // stock_package_type_stock_putaway_rule_rel, 1:N assumed
    stockPutawayRuleId: int,  // stock_putaway_rule_id
  }],
  stockRouteRel: [{  // stock_package_type_stock_route_rel, 1:N assumed
    stockRouteId: int,  // stock_route_id
  }],
}
```

Why:
- stock_package_type → stock_package, stock_storage_category_capacity, uom_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_package_type → stock_package_type_stock_putaway_rule_rel, stock_package_type_stock_route_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_package_type_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **cascade_into_embed** (stock_package_type_stock_putaway_rule_rel): stock_package_type_stock_putaway_rule_rel is embedded in stock_package_type, but deleting a stock_putaway_rule row cascades to its stock_package_type_stock_putaway_rule_rel: the app must pull them from every stock_package_type document, or keep stock_package_type_stock_putaway_rule_rel separate
- **cascade_into_embed** (stock_package_type_stock_route_rel): stock_package_type_stock_route_rel is embedded in stock_package_type, but deleting a stock_route row cascades to its stock_package_type_stock_route_rel: the app must pull them from every stock_package_type document, or keep stock_package_type_stock_route_rel separate
- **no_access_evidence** (stock_package_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockPickingType

From `stock_picking_type` with `picking_type_favorite_user_rel` embedded.

```js
{
  _id: int,  // id
  color: int,  // color
  sequence: int,  // sequence
  sequenceId: int,  // sequence_id
  defaultLocationSrcId: int,  // default_location_src_id
  defaultLocationDestId: int,  // default_location_dest_id
  allocatedLocationId: int,  // allocated_location_id
  returnPickingTypeId: int,  // return_picking_type_id
  warehouseId: int,  // warehouse_id
  reservationDaysBefore: int,  // reservation_days_before
  reservationDaysBeforePriority: int,  // reservation_days_before_priority
  companyId: int,  // company_id
  batchMaxLines: int,  // batch_max_lines
  batchMaxPickings: int,  // batch_max_pickings
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  code: string,  // code
  reservationMethod: string,  // reservation_method
  productLabelFormat: string,  // product_label_format
  lotLabelFormat: string,  // lot_label_format
  packageLabelToPrint: string,  // package_label_to_print
  barcode: string,  // barcode
  createBackorder: string,  // create_backorder
  moveType: string,  // move_type
  waveDateGranularity: string,  // wave_date_granularity
  name: object,  // name
  pickingPropertiesDefinition: object,  // picking_properties_definition
  batchPropertiesDefinition: object,  // batch_properties_definition
  showEntirePacks: bool,  // show_entire_packs
  setPackageType: bool,  // set_package_type
  active: bool,  // active
  useCreateLots: bool,  // use_create_lots
  useExistingLots: bool,  // use_existing_lots
  printLabel: bool,  // print_label
  autoShowAllocationReport: bool,  // auto_show_allocation_report
  autoPrintDeliverySlip: bool,  // auto_print_delivery_slip
  autoPrintReturnSlip: bool,  // auto_print_return_slip
  autoPrintProductLabels: bool,  // auto_print_product_labels
  autoPrintLotLabels: bool,  // auto_print_lot_labels
  autoPrintReceptionReport: bool,  // auto_print_reception_report
  autoPrintReceptionReportLabels: bool,  // auto_print_reception_report_labels
  autoPrintPackages: bool,  // auto_print_packages
  autoPrintPackageLabel: bool,  // auto_print_package_label
  autoBatch: bool,  // auto_batch
  batchGroupByPartner: bool,  // batch_group_by_partner
  batchGroupByDestination: bool,  // batch_group_by_destination
  batchGroupBySrcLoc: bool,  // batch_group_by_src_loc
  batchGroupByDestLoc: bool,  // batch_group_by_dest_loc
  waveGroupByProduct: bool,  // wave_group_by_product
  waveGroupByCategory: bool,  // wave_group_by_category
  waveGroupByLocation: bool,  // wave_group_by_location
  waveGroupByDate: bool,  // wave_group_by_date
  batchAutoConfirm: bool,  // batch_auto_confirm
  createDate: date,  // create_date
  writeDate: date,  // write_date
  pickingTypeFavoriteUserRel: [{  // picking_type_favorite_user_rel, 1:N derived
    userId: int,  // user_id
  }],
}
```

Why:
- stock_picking_type → picking_type_favorite_user_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- stock_picking_type → product_category_stock_picking_type_rel, stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking_type → purchase_order, stock_move, stock_picking, stock_picking_batch, stock_picking_type, stock_rule, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_location, stock_warehouse → stock_picking_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_picking_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockReference

From `stock_reference` with `stock_reference_move_rel`, `stock_reference_purchase_rel`, `stock_reference_sale_rel` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  moveRel: [{  // stock_reference_move_rel, 1:N assumed
    moveId: int,  // move_id
  }],
  purchaseRel: [{  // stock_reference_purchase_rel, 1:N assumed
    purchaseId: int,  // purchase_id
  }],
  saleRel: [{  // stock_reference_sale_rel, 1:N assumed
    saleId: int,  // sale_id
  }],
}
```

Why:
- stock_move → stock_reference_move_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_reference → stock_reference_move_rel, stock_reference_purchase_rel, stock_reference_sale_rel: **embed**, a link table, kept as an array on this side (assumed)
- purchase_order → stock_reference_purchase_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order → stock_reference_sale_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **cascade_into_embed** (stock_reference_move_rel): stock_reference_move_rel is embedded in stock_reference, but deleting a stock_move row cascades to its stock_reference_move_rel: the app must pull them from every stock_reference document, or keep stock_reference_move_rel separate
- **cascade_into_embed** (stock_reference_purchase_rel): stock_reference_purchase_rel is embedded in stock_reference, but deleting a purchase_order row cascades to its stock_reference_purchase_rel: the app must pull them from every stock_reference document, or keep stock_reference_purchase_rel separate
- **cascade_into_embed** (stock_reference_sale_rel): stock_reference_sale_rel is embedded in stock_reference, but deleting a sale_order row cascades to its stock_reference_sale_rel: the app must pull them from every stock_reference document, or keep stock_reference_sale_rel separate
- **no_access_evidence** (stock_reference): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockRoute

From `stock_route` with `stock_route_categ`, `stock_route_move`, `stock_route_product`, `stock_route_warehouse` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  suppliedWhId: int,  // supplied_wh_id
  supplierWhId: int,  // supplier_wh_id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  active: bool,  // active
  productSelectable: bool,  // product_selectable
  productCategSelectable: bool,  // product_categ_selectable
  warehouseSelectable: bool,  // warehouse_selectable
  packageTypeSelectable: bool,  // package_type_selectable
  createDate: date,  // create_date
  writeDate: date,  // write_date
  saleSelectable: bool,  // sale_selectable
  categ: [{  // stock_route_categ, 1:N assumed
    categId: int,  // categ_id
  }],
  move: [{  // stock_route_move, 1:N assumed
    moveId: int,  // move_id
  }],
  product: [{  // stock_route_product, 1:N assumed
    productId: int,  // product_id
  }],
  warehouse: [{  // stock_route_warehouse, 1:N assumed
    warehouseId: int,  // warehouse_id
  }],
}
```

Why:
- stock_route → sale_order_line_stock_route_rel, stock_package_type_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_warehouse → stock_route: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_route_categ, stock_route_move, stock_route_product, stock_route_warehouse: **embed**, a link table, kept as an array on this side (assumed)
- stock_move → stock_route_move: **reference**, a link table, embedded on the other side (assumed)
- product_template → stock_route_product: **reference**, a link table, embedded on the other side (assumed)
- stock_warehouse → stock_route_warehouse: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_rule, stock_warehouse, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (5):
- **cascade_into_embed** (stock_route_categ): stock_route_categ is embedded in stock_route, but deleting a product_category row cascades to its stock_route_categ: the app must pull them from every stock_route document, or keep stock_route_categ separate
- **cascade_into_embed** (stock_route_move): stock_route_move is embedded in stock_route, but deleting a stock_move row cascades to its stock_route_move: the app must pull them from every stock_route document, or keep stock_route_move separate
- **cascade_into_embed** (stock_route_product): stock_route_product is embedded in stock_route, but deleting a product_template row cascades to its stock_route_product: the app must pull them from every stock_route document, or keep stock_route_product separate
- **cascade_into_embed** (stock_route_warehouse): stock_route_warehouse is embedded in stock_route, but deleting a stock_warehouse row cascades to its stock_route_warehouse: the app must pull them from every stock_route document, or keep stock_route_warehouse separate
- **no_access_evidence** (stock_route): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockWarehouse

From `stock_warehouse` with `stock_wh_resupply_table` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  partnerId: int,  // partner_id
  viewLocationId: int,  // view_location_id
  lotStockId: int,  // lot_stock_id
  whInputStockLocId: int,  // wh_input_stock_loc_id
  whQcStockLocId: int,  // wh_qc_stock_loc_id
  whOutputStockLocId: int,  // wh_output_stock_loc_id
  whPackStockLocId: int,  // wh_pack_stock_loc_id
  mtoPullId: int,  // mto_pull_id
  pickTypeId: int,  // pick_type_id
  packTypeId: int,  // pack_type_id
  outTypeId: int,  // out_type_id
  inTypeId: int,  // in_type_id
  intTypeId: int,  // int_type_id
  qcTypeId: int,  // qc_type_id
  storeTypeId: int,  // store_type_id
  xdockTypeId: int,  // xdock_type_id
  receptionRouteId: int,  // reception_route_id
  deliveryRouteId: int,  // delivery_route_id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  code: string,  // code
  receptionSteps: string,  // reception_steps
  deliverySteps: string,  // delivery_steps
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  buyPullId: int,  // buy_pull_id
  stockWhResupplyTable: [{  // stock_wh_resupply_table, 1:N assumed
    supplierWhId: int,  // supplier_wh_id
  }],
}
```

Why:
- stock_warehouse → sale_order, sale_order_line, stock_location, stock_move, stock_picking_type, stock_route, stock_rule, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_warehouse → stock_route_warehouse, stock_wh_resupply_table: **reference**, a link table, embedded on the other side (assumed)
- stock_rule, stock_route, stock_picking_type, stock_location → stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_warehouse → stock_wh_resupply_table: **embed**, a link table, kept as an array on this side (assumed)

Open questions (1):
- **no_access_evidence** (stock_warehouse): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountBankStatementLine

From `account_bank_statement_line`.

Why:
- account_journal, account_move, account_bank_statement → account_bank_statement_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_move, account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (1):
- **no_access_evidence** (account_bank_statement_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountFullReconcile

From `account_full_reconcile`.

Why:
- account_full_reconcile → account_move_line, account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_full_reconcile): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountIncoterms

From `account_incoterms`.

Why:
- account_incoterms → account_move, purchase_order, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_incoterms): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountJournalGroup

From `account_journal_group`.

Why:
- account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_journal_group): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountLockException

From `account_lock_exception`.

Open questions (1):
- **no_access_evidence** (account_lock_exception): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountMoveLine

From `account_move_line`.

Why:
- account_move_line → account_account_tag_account_move_line_rel, sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)
- account_account, account_full_reconcile, account_tax, account_journal, account_move, account_payment, product_product, uom_uom, purchase_order_line, account_reconcile_model, account_bank_statement, account_bank_statement_line, stock_move, account_tax_group, account_tax_repartition_line → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move_line → account_move_line, account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move_line → account_move_line_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (2):
- **no_access_evidence** (account_move_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_move_line): LOB column(s) name measured max 67 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## accountMoveLineAccountTaxRel

From `account_move_line_account_tax_rel`.

Why:
- account_move_line → account_move_line_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_move_line_account_tax_rel: **reference**, too many children per parent (measured) (derived)

Open questions (1):
- **no_access_evidence** (account_move_line_account_tax_rel): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountPartialReconcile

From `account_partial_reconcile`.

Why:
- account_partial_reconcile → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move_line, account_move, account_full_reconcile → account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_partial_reconcile): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountPaymentMethod

From `account_payment_method`.

Why:
- account_payment_method → account_payment, account_payment_method_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_payment_method): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountPaymentMethodLine

From `account_payment_method_line`.

Why:
- account_payment_method_line → account_cash_rounding_account_payment_method_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment_method_line → account_move, account_payment, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_journal, account_account, account_payment_method → account_payment_method_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_payment_method_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountReportLine

From `account_report_line`.

Why:
- account_report_line → account_report_expression, account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report_line → account_report_external_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_report → account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (account_report_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## accountTaxGroup

From `account_tax_group`.

Why:
- account_tax_group → account_move_line, account_tax: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_tax_group): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountTaxRepartitionLine

From `account_tax_repartition_line`.

Why:
- account_tax_repartition_line → account_account_tag_account_tax_repartition_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax_repartition_line → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account, account_tax → account_tax_repartition_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_tax_repartition_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productAttributeCustomValue

From `product_attribute_custom_value`.

Why:
- product_template_attribute_value, sale_order_line → product_attribute_custom_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (product_attribute_custom_value): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## productBaseUnit

From `product_base_unit`.

Why:
- product_base_unit → product_product, product_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_base_unit): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productComboItem

From `product_combo_item`.

Why:
- product_combo, product_product → product_combo_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo_item → sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_combo_item): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productDocument

From `product_document`.

Open questions (1):
- **no_access_evidence** (product_document): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productPricelist

From `product_pricelist`.

Why:
- product_pricelist → product_pricelist_item, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_pricelist): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productPricelistItem

From `product_pricelist_item`.

Why:
- product_pricelist, product_category, product_product, product_template, uom_uom → product_pricelist_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_pricelist_item): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productRemoval

From `product_removal`.

Why:
- product_removal → product_category, stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_removal): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productSupplierinfo

From `product_supplierinfo`.

Why:
- product_product, product_template, uom_uom → product_supplierinfo: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_supplierinfo → stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_supplierinfo): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productTemplateAttributeLine

From `product_template_attribute_line`.

Why:
- product_template_attribute_line → product_attribute_value_product_template_attribute_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_attribute, product_template → product_template_attribute_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_line → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_template_attribute_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productUom

From `product_uom`.

Why:
- product_product, uom_uom → product_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_uom): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## returnReason

From `return_reason`.

Why:
- return_reason → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (return_reason): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockLot

From `stock_lot`.

Why:
- stock_lot → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_location, product_product → stock_lot: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_lot → stock_move_line, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (stock_lot): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (stock_lot): LOB column(s) note measured max 53 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## stockPackage

From `stock_package`.

Why:
- stock_package → stock_move_line, stock_package, stock_package_history, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_location, stock_package_type → stock_package: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_package): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockPicking

From `stock_picking`.

Why:
- stock_picking → purchase_order_stock_picking_rel, stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking → stock_move, stock_move_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_batch, stock_location, stock_picking_type, return_reason, sale_order → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (stock_picking): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (stock_picking): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockPickingBatch

From `stock_picking_batch`.

Why:
- stock_picking_batch → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_type → stock_picking_batch: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_picking_batch): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockPutawayRule

From `stock_putaway_rule`.

Why:
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category, stock_location, product_product, stock_storage_category → stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_putaway_rule): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockQuant

From `stock_quant`.

Why:
- stock_location, stock_lot, stock_package, product_product → stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_quant): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockRule

From `stock_rule`.

Why:
- stock_rule → stock_move, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_location, stock_picking_type, stock_route, stock_warehouse → stock_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_rule): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockScrapReasonTag

From `stock_scrap_reason_tag`.

Why:
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (1):
- **no_access_evidence** (stock_scrap_reason_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockStorageCategory

From `stock_storage_category`.

Why:
- stock_storage_category → stock_location, stock_putaway_rule, stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_storage_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockStorageCategoryCapacity

From `stock_storage_category_capacity`.

Why:
- stock_package_type, product_product, stock_storage_category → stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (stock_storage_category_capacity): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockWarehouseOrderpoint

From `stock_warehouse_orderpoint`.

Why:
- stock_warehouse_orderpoint → purchase_order_line, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_location, product_product, uom_uom, stock_route, product_supplierinfo, stock_warehouse → stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_warehouse_orderpoint): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## uomUom

From `uom_uom`.

Why:
- uom_uom → account_move_line, product_pricelist_item, product_supplierinfo, product_template, product_uom, purchase_order_line, sale_order_line, stock_move, stock_move_line, stock_warehouse_orderpoint, uom_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- uom_uom → product_product_uom_uom_rel, product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_package_type → uom_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (uom_uom): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
