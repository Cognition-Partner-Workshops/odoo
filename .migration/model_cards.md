# Model review: map-draft-1

## Review

- **Draft:** 65 collections, 77 embedded tables, 379 tables excluded.
- **Evidence:** of 357 relationship choices, 283 rest on measured data or app code and 0 on a recorded decision (`derived`); the rest follow the schema alone (`assumed`).
- **Decisions:** 10 kinds of question, 580 items. The draft already applies each proposal; answer each group with one line in `.migration/answers.txt` (template below).

1. **many_to_many_junction** (56): junction embedded via read evidence as an array in account_account; confirm the other side never needs the reverse lookup (else add a multikey index or keep a reference)  
   Applies to: account_account_account_tag, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_account_tax_default_rel, account_cash_rounding_account_payment_method_line_rel, account_fiscal_position_account_tax_rel, account_journal_account_reconcile_model_rel and 48 more
2. **embed_unbounded** (8): 1:N embed: confirm the fan-out bound and document size (16 MB) against data, or bucket/reference  
   Applies to: account_cash_rounding_res_currency_rel, account_cash_rounding_res_partner_category_rel, account_fiscal_position_res_country_state_rel, account_reconcile_model_res_partner_rel, customer_product_reference, sale_order_transaction_rel, account_analytic_line_stock_move_rel, picking_type_favorite_user_rel
3. **transient_tables** (1): 88 table(s) back transient models, scratch state the framework deletes on a timer, so they are not migrated: account_account_account_merge_wizard_rel, account_accrued_orders_wizard, account_automatic_entry_wizard, account_automatic_entry_wizard_account_move_line_rel, account_autopost_bills_wizard, account_financial_year_op, account_merge_wizard, account_merge_wizard_line, account_move_account_move_send_batch_wizard_rel, account_move_account_resequence_wizard_rel, account_move_reversal, account_move_reversal_move, account_move_reversal_new_move, account_move_send_batch_wizard, account_move_send_wizard, account_move_send_wizard_res_partner_rel, account_move_validate_account_move_rel, account_payment_register, account_payment_register_move_line_rel, account_resequence_wizard, account_secure_entries_wizard, account_setup_bank_manual_config, base_document_layout, bill_to_po_wizard, lot_label_layout, lot_label_layout_stock_lot_rel, lot_label_layout_stock_move_line_rel, mail_compose_message, mail_compose_message_ir_attachments_rel, mail_compose_message_res_partner_cc_rel, mail_compose_message_res_partner_rel, payment_link_wizard, picking_label_type, picking_label_type_stock_picking_rel, product_label_layout, product_label_layout_product_product_rel, product_label_layout_product_template_rel, product_label_layout_product_uom_rel, product_label_layout_stock_move_rel, product_replenish, product_supplierinfo_stock_replenishment_info_rel, res_config_settings, sale_advance_payment_inv, sale_advance_payment_inv_sale_order_rel, sale_mass_cancel_orders, sale_order_discount, sale_order_mass_cancel_wizard_rel, stock_add_to_wave, stock_add_to_wave_stock_move_line_rel, stock_add_to_wave_stock_picking_rel, stock_backorder_confirmation, stock_backorder_confirmation_line, stock_conflict_quant_rel, stock_inventory_adjustment_name, stock_inventory_adjustment_name_stock_quant_rel, stock_inventory_conflict, stock_inventory_conflict_stock_quant_rel, stock_inventory_warning, stock_inventory_warning_stock_quant_rel, stock_location_label_layout, stock_move_line_stock_package_destination_rel, stock_move_line_stock_put_in_pack_rel, stock_orderpoint_snooze, stock_orderpoint_snooze_stock_warehouse_orderpoint_rel, stock_orderpoint_suggest, stock_orderpoint_suggest_stock_warehouse_orderpoint_rel, stock_package_destination, stock_package_label_layout, stock_package_stock_put_in_pack_rel, stock_picking_backorder_rel, stock_picking_stock_zero_demand_confirmation_rel, stock_picking_to_batch, stock_picking_type_label_layout, stock_put_in_pack, stock_quant_relocate, stock_quant_stock_quant_relocate_rel, stock_quant_stock_request_count_rel, stock_replenishment_info, stock_replenishment_option, stock_request_count, stock_route_stock_rules_report_rel, stock_rules_report, stock_rules_report_stock_warehouse_rel, stock_traceability_report, stock_warn_insufficient_qty_scrap, stock_zero_demand_confirmation, update_product_attribute_value, validate_account_move; confirm none must survive cutover
4. **extended_reference_candidate** (269): app reads account_account_tag with every account_account_account_tag: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference  
   Applies to: account_account_account_tag, account_account_tax_default_rel, account_account, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_bank_statement, account_bank_statement_line and 94 more
5. **source_index_not_exercised** (122): source index not exercised by any confirmed access pattern; keep or drop  
   Applies to: account_account, account_account_account_tag, account_account_tax_default_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_bank_statement, account_bank_statement_ir_attachment_rel and 80 more
6. **fanout_unmeasured** (49): account_account_tax_default_rel has no rows per account_account in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding  
   Applies to: account_account_tax_default_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_cash_rounding_res_currency_rel, account_cash_rounding_res_partner_category_rel, account_cash_rounding_account_payment_method_line_rel, account_fiscal_position_account and 41 more
7. **cascade_into_embed** (44): account_account_tax_default_rel is embedded in account_account, but deleting a account_tax row cascades to its account_account_tax_default_rel: the app must pull them from every account_account document, or keep account_account_tax_default_rel separate  
   Applies to: account_account_tax_default_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_cash_rounding_account_payment_method_line_rel, account_fiscal_position_account_tax_rel, account_journal_account_reconcile_model_rel, account_move__account_payment and 36 more
8. **lob** (13): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)  
   Applies to: account_account, account_journal, account_move, account_move_line, account_report_expression, product_template, purchase_order, purchase_order_line and 5 more
9. **single_valued_index_key** (11): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan  
   Applies to: account_bank_statement, account_bank_statement_line, account_move, product_product, product_template, product_template_attribute_line, purchase_order, stock_quant and 2 more
10. **nullable_unique_key** (7): source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

**Answers template.** Copy it to `.migration/answers.txt` and replace each `<...>` with who decided and why. `accept` keeps the embeds and copied fields a rule proposed (from the schema alone), `reject` makes its embeds references, `except` exempts tables, `close` settles every question of a kind. Delete lines you are not ready to answer.

```
accept ownership: <who said so, and why>  # 8 tables: account_analytic_line_stock_move_rel, account_cash_rounding_res_currency_rel, account_cash_rounding_res_partner_category_rel, account_fiscal_position_res_country_state_rel, account_reconcile_model_res_partner_rel, customer_product_reference, picking_type_favorite_user_rel, sale_order_transaction_rel
close many_to_many_junction: <who said so, and why>  # 56 questions
close embed_unbounded: <who said so, and why>  # 8 questions
close transient_tables: <who said so, and why>  # 1 questions
close extended_reference_candidate: <who said so, and why>  # 269 questions
close source_index_not_exercised: <who said so, and why>  # 122 questions
close fanout_unmeasured: <who said so, and why>  # 49 questions
close cascade_into_embed: <who said so, and why>  # 44 questions
close lob: <who said so, and why>  # 13 questions
close single_valued_index_key: <who said so, and why>  # 11 questions
close nullable_unique_key: <who said so, and why>  # 7 questions
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
  accountTag: [{  // account_account_account_tag, 1:N derived
    accountAccountTagId: int,  // account_account_tag_id
  }],
  taxDefaultRel: [{  // account_account_tax_default_rel, 1:N derived
    taxId: int,  // tax_id
  }],
}
```

Why:
- account_account → account_account, account_journal, account_move_line, account_tax, stock_location: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_account → account_account_account_tag, account_account_tax_default_rel: **embed**, a link table, kept as an array on this side (derived)
- account_account_tag → account_account_account_tag: **reference**, a link table, embedded on the other side (assumed)
- account_account → account_account_res_company_rel: **embed**, the app reads it with its parent (derived)
- account_tax → account_account_tax_default_rel: **reference**, a link table, embedded on the other side (assumed)
- account_account → account_fiscal_position_account, account_payment, account_payment_method_line, account_reconcile_model_line, account_tax_repartition_line: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (11):
- **fanout_unmeasured** (account_account_tax_default_rel): account_account_tax_default_rel has no rows per account_account in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_account_account_tag): app reads account_account_tag with every account_account_account_tag: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_account_tax_default_rel): app reads account_tax with every account_account_tax_default_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_account): app reads account_account with every account_account: copy up to 5 read fields of account_account into account_account documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_account): app reads account_account with every account_account: copy up to 5 read fields of account_account into account_account documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_account): app reads account_account with every account_account: copy up to 5 read fields of account_account into account_account documents (extended reference) or keep the $lookup
- **cascade_into_embed** (account_account_tax_default_rel): account_account_tax_default_rel is embedded in account_account, but deleting a account_tax row cascades to its account_account_tax_default_rel: the app must pull them from every account_account document, or keep account_account_tax_default_rel separate
- **lob** (account_account): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (account_account): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_account_account_tag): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_account_tax_default_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  accountMoveLineRel: [{  // account_account_tag_account_move_line_rel, 1:N derived
    accountMoveLineId: int,  // account_move_line_id
  }],
  accountTaxRepartitionLineRel: [{  // account_account_tag_account_tax_repartition_line_rel, 1:N derived
    accountTaxRepartitionLineId: int,  // account_tax_repartition_line_id
  }],
  productTemplateRel: [{  // account_account_tag_product_template_rel, 1:N derived
    productTemplateId: int,  // product_template_id
  }],
}
```

Why:
- account_account_tag → account_account_account_tag: **reference**, a link table, embedded on the other side (assumed)
- account_account_tag → account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel: **embed**, a link table, kept as an array on this side (derived)
- account_move_line → account_account_tag_account_move_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax_repartition_line → account_account_tag_account_tax_repartition_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → account_account_tag_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (13):
- **fanout_unmeasured** (account_account_tag_account_move_line_rel): account_account_tag_account_move_line_rel has no rows per account_account_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_account_tag_account_tax_repartition_line_rel): account_account_tag_account_tax_repartition_line_rel has no rows per account_account_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_account_tag_product_template_rel): account_account_tag_product_template_rel has no rows per account_account_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_account_tag_account_move_line_rel): app reads account_move_line with every account_account_tag_account_move_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_account_tag_account_tax_repartition_line_rel): app reads account_tax_repartition_line with every account_account_tag_account_tax_repartition_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_account_tag_product_template_rel): app reads product_template with every account_account_tag_product_template_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (account_account_tag_account_move_line_rel): account_account_tag_account_move_line_rel is embedded in account_account_tag, but deleting a account_move_line row cascades to its account_account_tag_account_move_line_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_account_move_line_rel separate
- **cascade_into_embed** (account_account_tag_account_tax_repartition_line_rel): account_account_tag_account_tax_repartition_line_rel is embedded in account_account_tag, but deleting a account_tax_repartition_line row cascades to its account_account_tag_account_tax_repartition_line_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_account_tax_repartition_line_rel separate
- **cascade_into_embed** (account_account_tag_product_template_rel): account_account_tag_product_template_rel is embedded in account_account_tag, but deleting a product_template row cascades to its account_account_tag_product_template_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_product_template_rel separate
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (account_account_tag_account_move_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_account_tag_account_tax_repartition_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_account_tag_product_template_rel): source index not exercised by any confirmed access pattern; keep or drop

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
- account_journal → account_bank_statement: **reference**, the app reads it on its own (derived)
- account_bank_statement → account_bank_statement_ir_attachment_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_bank_statement → account_bank_statement_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_bank_statement → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (5):
- **extended_reference_candidate** (account_bank_statement): app reads account_journal with every account_bank_statement: copy up to 5 read fields of account_journal into account_bank_statement documents (extended reference) or keep the $lookup
- **single_valued_index_key** (account_bank_statement): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **single_valued_index_key** (account_bank_statement): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (account_bank_statement): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_bank_statement_ir_attachment_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  resCurrencyRel: [{  // account_cash_rounding_res_currency_rel, 1:N assumed
    resCurrencyId: int,  // res_currency_id
  }],
  resPartnerCategoryRel: [{  // account_cash_rounding_res_partner_category_rel, 1:N assumed
    resPartnerCategoryId: int,  // res_partner_category_id
  }],
  accountPaymentMethodLineRel: [{  // account_cash_rounding_account_payment_method_line_rel, 1:N derived
    accountPaymentMethodLineId: int,  // account_payment_method_line_id
  }],
}
```

Why:
- account_payment_method_line → account_cash_rounding_account_payment_method_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_cash_rounding → account_cash_rounding_account_payment_method_line_rel: **embed**, a link table, kept as an array on this side (derived)
- account_cash_rounding → account_cash_rounding_res_currency_rel, account_cash_rounding_res_partner_category_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- account_cash_rounding → account_move: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (8):
- **fanout_unmeasured** (account_cash_rounding_res_currency_rel): account_cash_rounding_res_currency_rel has no rows per account_cash_rounding in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_cash_rounding_res_partner_category_rel): account_cash_rounding_res_partner_category_rel has no rows per account_cash_rounding in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_cash_rounding_account_payment_method_line_rel): account_cash_rounding_account_payment_method_line_rel has no rows per account_cash_rounding in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_cash_rounding_account_payment_method_line_rel): app reads account_payment_method_line with every account_cash_rounding_account_payment_method_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (account_cash_rounding_account_payment_method_line_rel): account_cash_rounding_account_payment_method_line_rel is embedded in account_cash_rounding, but deleting a account_payment_method_line row cascades to its account_cash_rounding_account_payment_method_line_rel: the app must pull them from every account_cash_rounding document, or keep account_cash_rounding_account_payment_method_line_rel separate
- **source_index_not_exercised** (account_cash_rounding_account_payment_method_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_cash_rounding_res_currency_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_cash_rounding_res_partner_category_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  resCountryStateRel: [{  // account_fiscal_position_res_country_state_rel, 1:N assumed
    resCountryStateId: int,  // res_country_state_id
  }],
  accountTaxRel: [{  // account_fiscal_position_account_tax_rel, 1:N derived
    accountTaxId: int,  // account_tax_id
  }],
}
```

Why:
- account_account → account_fiscal_position_account: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_fiscal_position → account_fiscal_position_account: **embed**, the app reads it with its parent (derived)
- account_fiscal_position → account_fiscal_position_account_tax_rel: **embed**, a link table, kept as an array on this side (derived)
- account_tax → account_fiscal_position_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)
- account_fiscal_position → account_fiscal_position_res_country_state_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- account_fiscal_position → account_move: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_fiscal_position → purchase_order, sale_order: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (8):
- **fanout_unmeasured** (account_fiscal_position_account): account_fiscal_position_account has no rows per account_fiscal_position in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_fiscal_position_res_country_state_rel): account_fiscal_position_res_country_state_rel has no rows per account_fiscal_position in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_fiscal_position_account): app reads account_account with every account_fiscal_position_account: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_fiscal_position_account): app reads account_account with every account_fiscal_position_account: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_fiscal_position_account_tax_rel): app reads account_tax with every account_fiscal_position_account_tax_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (account_fiscal_position_account_tax_rel): account_fiscal_position_account_tax_rel is embedded in account_fiscal_position, but deleting a account_tax row cascades to its account_fiscal_position_account_tax_rel: the app must pull them from every account_fiscal_position document, or keep account_fiscal_position_account_tax_rel separate
- **source_index_not_exercised** (account_fiscal_position_account_tax_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_fiscal_position_res_country_state_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  accountReconcileModelRel: [{  // account_journal_account_reconcile_model_rel, 1:N derived
    accountReconcileModelId: int,  // account_reconcile_model_id
  }],
}
```

Why:
- account_journal → account_bank_statement: **reference**, the app reads it on its own (derived)
- account_journal → account_bank_statement_line, account_move, account_payment, account_payment_method_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_account, account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_journal → account_journal_account_reconcile_model_rel: **embed**, a link table, kept as an array on this side (derived)
- account_journal → account_move_line, sale_order: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (12):
- **fanout_unmeasured** (account_journal_account_reconcile_model_rel): account_journal_account_reconcile_model_rel has no rows per account_journal in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_journal_account_reconcile_model_rel): app reads account_reconcile_model with every account_journal_account_reconcile_model_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_journal): app reads account_account with every account_journal: copy up to 5 read fields of account_account into account_journal documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_journal): app reads account_journal_group with every account_journal: copy up to 5 read fields of account_journal_group into account_journal documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_journal): app reads account_account with every account_journal: copy up to 5 read fields of account_account into account_journal documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_journal): app reads account_account with every account_journal: copy up to 5 read fields of account_account into account_journal documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_journal): app reads account_account with every account_journal: copy up to 5 read fields of account_account into account_journal documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_journal): app reads account_account with every account_journal: copy up to 5 read fields of account_account into account_journal documents (extended reference) or keep the $lookup
- **cascade_into_embed** (account_journal_account_reconcile_model_rel): account_journal_account_reconcile_model_rel is embedded in account_journal, but deleting a account_reconcile_model row cascades to its account_journal_account_reconcile_model_rel: the app must pull them from every account_journal document, or keep account_journal_account_reconcile_model_rel separate
- **lob** (account_journal): LOB column(s) sequence_override_regex measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (account_journal): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_journal_account_reconcile_model_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  accountPayment: [{  // account_move__account_payment, 1:N derived
    paymentId: int,  // payment_id
  }],
  purchaseOrderRel: [{  // account_move_purchase_order_rel, 1:N derived
    purchaseOrderId: int,  // purchase_order_id
  }],
  adjustingEntriesAccountMove: [{  // adjusting_entries__account_move, 1:N derived
    moveId: int,  // move_id
  }],
}
```

Why:
- account_move → account_bank_statement_line, account_payment: **reference**, the app reads it on its own (derived)
- account_move → account_move, account_partial_reconcile: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_fiscal_position, account_cash_rounding, account_incoterms, account_payment_term, account_journal, account_payment, account_payment_method_line, account_partial_reconcile → account_move: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_bank_statement_line → account_move: **reference**, the app reads it on its own (derived)
- account_move → account_move__account_payment, account_move_purchase_order_rel, adjusting_entries__account_move: **embed**, a link table, kept as an array on this side (derived)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- account_move → account_move_line, product_value, stock_move: **reference**, other tables also point at it, so it keeps its own collection (derived)
- purchase_order → account_move_purchase_order_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move → adjusting_entries__account_move, purchase_order_line_accrual_move_rel, sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (36):
- **fanout_unmeasured** (account_move__account_payment): account_move__account_payment has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_move_purchase_order_rel): account_move_purchase_order_rel has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (adjusting_entries__account_move): adjusting_entries__account_move has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_move__account_payment): app reads account_payment with every account_move__account_payment: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_move_purchase_order_rel): app reads purchase_order with every account_move_purchase_order_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (adjusting_entries__account_move): app reads account_move with every adjusting_entries__account_move: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_move): app reads account_move with every account_move: copy up to 5 read fields of account_move into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_fiscal_position with every account_move: copy up to 5 read fields of account_fiscal_position into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_cash_rounding with every account_move: copy up to 5 read fields of account_cash_rounding into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_incoterms with every account_move: copy up to 5 read fields of account_incoterms into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_payment_term with every account_move: copy up to 5 read fields of account_payment_term into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_journal with every account_move: copy up to 5 read fields of account_journal into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_payment with every account_move: copy up to 5 read fields of account_payment into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_payment_method_line with every account_move: copy up to 5 read fields of account_payment_method_line into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_move with every account_move: copy up to 5 read fields of account_move into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_bank_statement_line with every account_move: copy up to 5 read fields of account_bank_statement_line into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): copy the parent fields this read uses into the child (extended reference); parent has no hot/warm writer
- **extended_reference_candidate** (account_move): app reads account_move with every account_move: copy up to 5 read fields of account_move into account_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move): app reads account_partial_reconcile with every account_move: copy up to 5 read fields of account_partial_reconcile into account_move documents (extended reference) or keep the $lookup
- **cascade_into_embed** (account_move__account_payment): account_move__account_payment is embedded in account_move, but deleting a account_payment row cascades to its account_move__account_payment: the app must pull them from every account_move document, or keep account_move__account_payment separate
- **cascade_into_embed** (account_move_purchase_order_rel): account_move_purchase_order_rel is embedded in account_move, but deleting a purchase_order row cascades to its account_move_purchase_order_rel: the app must pull them from every account_move document, or keep account_move_purchase_order_rel separate
- **lob** (account_move): LOB column(s) narration measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **single_valued_index_key** (account_move): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move__account_payment): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move_purchase_order_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (adjusting_entries__account_move): source index not exercised by any confirmed access pattern; keep or drop

## accountMoveLine

From `account_move_line` with `account_move_line_account_tax_rel`, `account_partial_reconcile` embedded.

```js
{
  _id: int,  // id
  productId: int,  // product_id
  moveId: int,  // move_id
  journalId: int,  // journal_id
  companyId: int,  // company_id
  companyCurrencyId: int,  // company_currency_id
  sequence: int,  // sequence
  accountId: int,  // account_id
  currencyId: int,  // currency_id
  partnerId: int,  // partner_id
  reconcileModelId: int,  // reconcile_model_id
  paymentId: int,  // payment_id
  statementLineId: int,  // statement_line_id
  statementId: int,  // statement_id
  groupTaxId: int,  // group_tax_id
  taxLineId: int,  // tax_line_id
  taxGroupId: int,  // tax_group_id
  taxRepartitionLineId: int,  // tax_repartition_line_id
  fullReconcileId: int,  // full_reconcile_id
  productUomId: int,  // product_uom_id
  cogsOriginId: int,  // cogs_origin_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  moveName: string,  // move_name
  parentState: string,  // parent_state
  ref: string,  // ref
  matchingNumber: string,  // matching_number
  displayType: string,  // display_type
  date: date,  // date
  invoiceDate: date,  // invoice_date
  dateMaturity: date,  // date_maturity
  discountDate: date,  // discount_date
  analyticDistribution: object,  // analytic_distribution
  extraTaxData: object,  // extra_tax_data
  name: string,  // name
  debit: decimal,  // debit
  credit: decimal,  // credit
  balance: decimal,  // balance
  amountCurrency: decimal,  // amount_currency
  taxBaseAmount: decimal,  // tax_base_amount
  amountResidual: decimal,  // amount_residual
  amountResidualCurrency: decimal,  // amount_residual_currency
  quantity: decimal,  // quantity
  priceUnit: decimal,  // price_unit
  priceSubtotal: decimal,  // price_subtotal
  priceTotal: decimal,  // price_total
  discount: decimal,  // discount
  discountAmountCurrency: decimal,  // discount_amount_currency
  discountBalance: decimal,  // discount_balance
  isStorno: bool,  // is_storno
  isImported: bool,  // is_imported
  reconciled: bool,  // reconciled
  collapseComposition: bool,  // collapse_composition
  collapsePrices: bool,  // collapse_prices
  noFollowup: bool,  // no_followup
  createDate: date,  // create_date
  writeDate: date,  // write_date
  deductiblePercentage: double,  // deductible_percentage
  purchaseLineId: int,  // purchase_line_id
  isDownpayment: bool,  // is_downpayment
  stockMoveId: int,  // stock_move_id
  accountTaxRel: [{  // account_move_line_account_tax_rel, 1:N derived
    accountTaxId: int,  // account_tax_id
  }],
  accountPartialReconcile: [{  // account_partial_reconcile, 1:N derived
    id: int,  // id
    creditMoveId: int,  // credit_move_id
    fullReconcileId: int,  // full_reconcile_id
    exchangeMoveId: int,  // exchange_move_id
    debitCurrencyId: int,  // debit_currency_id
    creditCurrencyId: int,  // credit_currency_id
    companyId: int,  // company_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    maxDate: date,  // max_date
    draftCabaMoveVals: object,  // draft_caba_move_vals
    amount: decimal,  // amount
    debitAmountCurrency: decimal,  // debit_amount_currency
    creditAmountCurrency: decimal,  // credit_amount_currency
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- account_move_line → account_account_tag_account_move_line_rel, sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)
- account_account, account_full_reconcile, account_tax, account_journal, account_move, account_payment, product_product, uom_uom, purchase_order_line, account_reconcile_model, account_bank_statement, account_bank_statement_line, stock_move, account_tax_group, account_tax_repartition_line → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_move_line → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_move_line → account_move_line_account_tax_rel: **embed**, a link table, kept as an array on this side (derived)
- account_tax → account_move_line_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move_line → account_partial_reconcile: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_move_line → account_partial_reconcile: **embed**, the app reads it with its parent (derived)
- account_move, account_full_reconcile → account_partial_reconcile: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (29):
- **fanout_unmeasured** (account_partial_reconcile): account_partial_reconcile has no rows per account_move_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_move_line_account_tax_rel): app reads account_tax with every account_move_line_account_tax_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_partial_reconcile): app reads account_move_line with every account_partial_reconcile: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_partial_reconcile): app reads account_move with every account_partial_reconcile: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_partial_reconcile): app reads account_full_reconcile with every account_partial_reconcile: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_move_line): app reads account_account with every account_move_line: copy up to 5 read fields of account_account into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_move_line with every account_move_line: copy up to 5 read fields of account_move_line into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_full_reconcile with every account_move_line: copy up to 5 read fields of account_full_reconcile into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_tax with every account_move_line: copy up to 5 read fields of account_tax into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_move with every account_move_line: copy up to 5 read fields of account_move into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_payment with every account_move_line: copy up to 5 read fields of account_payment into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads product_product with every account_move_line: copy up to 5 read fields of product_product into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads uom_uom with every account_move_line: copy up to 5 read fields of uom_uom into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads purchase_order_line with every account_move_line: copy up to 5 read fields of purchase_order_line into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_reconcile_model with every account_move_line: copy up to 5 read fields of account_reconcile_model into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_bank_statement_line with every account_move_line: copy up to 5 read fields of account_bank_statement_line into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads stock_move with every account_move_line: copy up to 5 read fields of stock_move into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_tax with every account_move_line: copy up to 5 read fields of account_tax into account_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_move_line): app reads account_tax_repartition_line with every account_move_line: copy up to 5 read fields of account_tax_repartition_line into account_move_line documents (extended reference) or keep the $lookup
- **cascade_into_embed** (account_move_line_account_tax_rel): account_move_line_account_tax_rel is embedded in account_move_line, but deleting a account_tax row cascades to its account_move_line_account_tax_rel: the app must pull them from every account_move_line document, or keep account_move_line_account_tax_rel separate
- **lob** (account_move_line): LOB column(s) name measured max 56 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (account_move_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_move_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_partial_reconcile): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_partial_reconcile): source index not exercised by any confirmed access pattern; keep or drop

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
  accountBankStatementLineRel: [{  // account_payment_account_bank_statement_line_rel, 1:N derived
    accountBankStatementLineId: int,  // account_bank_statement_line_id
  }],
}
```

Why:
- account_payment → account_move, account_payment: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- account_payment → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_account, account_journal, account_payment_method, account_payment_method_line → account_payment: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_move → account_payment: **reference**, the app reads it on its own (derived)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment → account_payment_account_bank_statement_line_rel: **embed**, a link table, kept as an array on this side (derived)

Open questions (14):
- **fanout_unmeasured** (account_payment_account_bank_statement_line_rel): account_payment_account_bank_statement_line_rel has no rows per account_payment in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_payment_account_bank_statement_line_rel): app reads account_bank_statement_line with every account_payment_account_bank_statement_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_payment): app reads account_account with every account_payment: copy up to 5 read fields of account_account into account_payment documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_payment): app reads account_journal with every account_payment: copy up to 5 read fields of account_journal into account_payment documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_payment): app reads account_move with every account_payment: copy up to 5 read fields of account_move into account_payment documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_payment): app reads account_account with every account_payment: copy up to 5 read fields of account_account into account_payment documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_payment): app reads account_payment with every account_payment: copy up to 5 read fields of account_payment into account_payment documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_payment): app reads account_payment_method_line with every account_payment: copy up to 5 read fields of account_payment_method_line into account_payment documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_payment): app reads account_payment with every account_payment: copy up to 5 read fields of account_payment into account_payment documents (extended reference) or keep the $lookup
- **cascade_into_embed** (account_payment_account_bank_statement_line_rel): account_payment_account_bank_statement_line_rel is embedded in account_payment, but deleting a account_bank_statement_line row cascades to its account_payment_account_bank_statement_line_rel: the app must pull them from every account_payment document, or keep account_payment_account_bank_statement_line_rel separate
- **source_index_not_exercised** (account_payment): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_payment): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_payment): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_payment_account_bank_statement_line_rel): source index not exercised by any confirmed access pattern; keep or drop

## accountPaymentMethod

From `account_payment_method` with `account_payment_method_line` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  code: string,  // code
  paymentType: string,  // payment_type
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  line: [{  // account_payment_method_line, 1:N derived
    id: int,  // id
    sequence: int,  // sequence
    paymentAccountId: int,  // payment_account_id
    journalId: int,  // journal_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    name: string,  // name
    createDate: date,  // create_date
    writeDate: date,  // write_date
    paymentProviderId: int,  // payment_provider_id
  }],
}
```

Why:
- account_payment_method → account_payment: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_journal, account_account → account_payment_method_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_payment_method → account_payment_method_line: **embed**, the app reads it with its parent (derived)

Open questions (3):
- **extended_reference_candidate** (account_payment_method_line): app reads account_journal with every account_payment_method_line: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_payment_method_line): app reads account_account with every account_payment_method_line: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **source_index_not_exercised** (account_payment_method_line): source index not exercised by any confirmed access pattern; keep or drop

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
- account_payment_term → account_move: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_payment_term → account_payment_term_line: **embed**, the app reads it with its parent (derived)
- account_payment_term → purchase_order, sale_order: **reference**, other tables also point at it, so it keeps its own collection (derived)

## accountReconcileModel

From `account_reconcile_model` with `account_reconcile_model_res_partner_rel`, `account_reconcile_model_line` embedded.

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
  resPartnerRel: [{  // account_reconcile_model_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
  line: [{  // account_reconcile_model_line, 1:N derived
    id: int,  // id
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
  }],
}
```

Why:
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_reconcile_model → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_account → account_reconcile_model_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_reconcile_model → account_reconcile_model_line: **embed**, the app reads it with its parent (derived)
- account_reconcile_model → account_reconcile_model_res_partner_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

Open questions (4):
- **fanout_unmeasured** (account_reconcile_model_res_partner_rel): account_reconcile_model_res_partner_rel has no rows per account_reconcile_model in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_reconcile_model_line): app reads account_account with every account_reconcile_model_line: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (account_reconcile_model_line): account_reconcile_model_line is embedded in account_reconcile_model, but deleting a account_account row cascades to its account_reconcile_model_line: the app must pull them from every account_reconcile_model document, or keep account_reconcile_model_line separate
- **source_index_not_exercised** (account_reconcile_model_res_partner_rel): source index not exercised by any confirmed access pattern; keep or drop

## accountReport

From `account_report` with `account_report_column`, `account_report_line`, `account_report_section_rel` embedded.

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
  line: [{  // account_report_line, 1:N derived
    id: int,  // id
    hierarchyLevel: int,  // hierarchy_level
    parentId: int,  // parent_id
    sequence: int,  // sequence
    actionId: int,  // action_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    groupby: string,  // groupby
    userGroupby: string,  // user_groupby
    code: string,  // code
    foldability: string,  // foldability
    horizontalSplitSide: string,  // horizontal_split_side
    name: object,  // name
    printOnNewPage: bool,  // print_on_new_page
    hideIfZero: bool,  // hide_if_zero
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  sectionRel: [{  // account_report_section_rel, 1:N derived
    subReportId: int,  // sub_report_id
  }],
}
```

Why:
- account_report → account_report: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report → account_report_column, account_report_line: **embed**, the app reads it with its parent (derived)
- account_report_line → account_report_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_report → account_report_section_rel: **embed**, a link table, kept as an array on this side (derived)
- account_report → account_report_section_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (7):
- **fanout_unmeasured** (account_report_line): account_report_line has no rows per account_report in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_report_section_rel): account_report_section_rel has no rows per account_report in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_report_line): app reads account_report_line with every account_report_line: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_report_section_rel): app reads account_report with every account_report_section_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_report): app reads account_report with every account_report: copy up to 5 read fields of account_report into account_report documents (extended reference) or keep the $lookup
- **source_index_not_exercised** (account_report_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_report_section_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  alternatives: [{  // account_tax_alternatives, 1:N derived
    srcTaxId: int,  // src_tax_id
  }],
  filiationRel: [{  // account_tax_filiation_rel, 1:N derived
    parentTax: int,  // parent_tax
  }],
  purchaseOrderLineRel: [{  // account_tax_purchase_order_line_rel, 1:N derived
    purchaseOrderLineId: int,  // purchase_order_line_id
  }],
  saleOrderLineRel: [{  // account_tax_sale_order_line_rel, 1:N derived
    saleOrderLineId: int,  // sale_order_line_id
  }],
  productSupplierTaxesRel: [{  // product_supplier_taxes_rel, 1:N derived
    prodId: int,  // prod_id
  }],
  productTaxesRel: [{  // product_taxes_rel, 1:N derived
    prodId: int,  // prod_id
  }],
}
```

Why:
- account_tax → account_account_tax_default_rel, account_fiscal_position_account_tax_rel, account_move_line_account_tax_rel, account_reconcile_model_line_account_tax_rel, account_tax_alternatives, account_tax_filiation_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax → account_move_line, account_tax: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_account, account_tax_group → account_tax: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_tax → account_tax_alternatives, account_tax_filiation_rel, account_tax_purchase_order_line_rel, account_tax_sale_order_line_rel, product_supplier_taxes_rel, product_taxes_rel: **embed**, a link table, kept as an array on this side (derived)
- purchase_order_line → account_tax_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax → account_tax_repartition_line: **reference**, the app reads it on its own (derived)
- sale_order_line → account_tax_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_supplier_taxes_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_taxes_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (22):
- **fanout_unmeasured** (account_tax_filiation_rel): account_tax_filiation_rel has no rows per account_tax in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (account_tax_alternatives): app reads account_tax with every account_tax_alternatives: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_tax_filiation_rel): app reads account_tax with every account_tax_filiation_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_tax_purchase_order_line_rel): app reads purchase_order_line with every account_tax_purchase_order_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_tax_sale_order_line_rel): app reads sale_order_line with every account_tax_sale_order_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_supplier_taxes_rel): app reads product_template with every product_supplier_taxes_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_taxes_rel): app reads product_template with every product_taxes_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (account_tax): app reads account_account with every account_tax: copy up to 5 read fields of account_account into account_tax documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_tax): app reads account_tax with every account_tax: copy up to 5 read fields of account_tax into account_tax documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_tax): app reads account_tax with every account_tax: copy up to 5 read fields of account_tax into account_tax documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_tax): app reads account_tax_group with every account_tax: copy up to 5 read fields of account_tax_group into account_tax documents (extended reference) or keep the $lookup
- **cascade_into_embed** (account_tax_purchase_order_line_rel): account_tax_purchase_order_line_rel is embedded in account_tax, but deleting a purchase_order_line row cascades to its account_tax_purchase_order_line_rel: the app must pull them from every account_tax document, or keep account_tax_purchase_order_line_rel separate
- **cascade_into_embed** (account_tax_sale_order_line_rel): account_tax_sale_order_line_rel is embedded in account_tax, but deleting a sale_order_line row cascades to its account_tax_sale_order_line_rel: the app must pull them from every account_tax document, or keep account_tax_sale_order_line_rel separate
- **cascade_into_embed** (product_supplier_taxes_rel): product_supplier_taxes_rel is embedded in account_tax, but deleting a product_template row cascades to its product_supplier_taxes_rel: the app must pull them from every account_tax document, or keep product_supplier_taxes_rel separate
- **cascade_into_embed** (product_taxes_rel): product_taxes_rel is embedded in account_tax, but deleting a product_template row cascades to its product_taxes_rel: the app must pull them from every account_tax document, or keep product_taxes_rel separate
- **source_index_not_exercised** (account_tax): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_alternatives): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_purchase_order_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_sale_order_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_supplier_taxes_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_taxes_rel): source index not exercised by any confirmed access pattern; keep or drop

## productAttribute

From `product_attribute` with `product_attribute_product_template_rel`, `product_attribute_value` embedded.

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
  productTemplateRel: [{  // product_attribute_product_template_rel, 1:N derived
    productTemplateId: int,  // product_template_id
  }],
  value: [{  // product_attribute_value, 1:N derived
    id: int,  // id
    sequence: int,  // sequence
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
  }],
}
```

Why:
- product_attribute → product_attribute_product_template_rel: **embed**, a link table, kept as an array on this side (derived)
- product_template → product_attribute_product_template_rel: **reference**, a link table, embedded on the other side (assumed)
- product_attribute → product_attribute_value: **embed**, the app reads it with its parent (derived)
- product_attribute → product_template_attribute_line, product_template_attribute_value: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (3):
- **extended_reference_candidate** (product_attribute_product_template_rel): app reads product_template with every product_attribute_product_template_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (product_attribute_product_template_rel): product_attribute_product_template_rel is embedded in product_attribute, but deleting a product_template row cascades to its product_attribute_product_template_rel: the app must pull them from every product_attribute document, or keep product_attribute_product_template_rel separate
- **source_index_not_exercised** (product_attribute_product_template_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  stockPickingTypeRel: [{  // product_category_stock_picking_type_rel, 1:N derived
    stockPickingTypeId: int,  // stock_picking_type_id
  }],
}
```

Why:
- product_category → product_category, product_template: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_removal → product_category: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_picking_type → product_category_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category → product_category_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (derived)
- product_category → product_pricelist_item: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_category → stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)

Open questions (7):
- **fanout_unmeasured** (product_category_stock_picking_type_rel): product_category_stock_picking_type_rel has no rows per product_category in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (product_category_stock_picking_type_rel): app reads stock_picking_type with every product_category_stock_picking_type_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_category): app reads product_category with every product_category: copy up to 5 read fields of product_category into product_category documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_category): app reads product_removal with every product_category: copy up to 5 read fields of product_removal into product_category documents (extended reference) or keep the $lookup
- **cascade_into_embed** (product_category_stock_picking_type_rel): product_category_stock_picking_type_rel is embedded in product_category, but deleting a stock_picking_type row cascades to its product_category_stock_picking_type_rel: the app must pull them from every product_category document, or keep product_category_stock_picking_type_rel separate
- **source_index_not_exercised** (product_category): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_category_stock_picking_type_rel): source index not exercised by any confirmed access pattern; keep or drop

## productCombo

From `product_combo` with `product_combo_item`, `product_combo_product_template_rel` embedded.

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
  item: [{  // product_combo_item, 1:N derived
    id: int,  // id
    companyId: int,  // company_id
    productId: int,  // product_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    extraPrice: decimal,  // extra_price
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  productTemplateRel: [{  // product_combo_product_template_rel, 1:N derived
    productTemplateId: int,  // product_template_id
  }],
}
```

Why:
- product_combo → product_combo_item: **embed**, the app reads it with its parent (derived)
- product_product → product_combo_item: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_combo → product_combo_product_template_rel: **embed**, a link table, kept as an array on this side (derived)
- product_template → product_combo_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **extended_reference_candidate** (product_combo_item): app reads product_product with every product_combo_item: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_combo_product_template_rel): app reads product_template with every product_combo_product_template_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (product_combo_product_template_rel): product_combo_product_template_rel is embedded in product_combo, but deleting a product_template row cascades to its product_combo_product_template_rel: the app must pull them from every product_combo document, or keep product_combo_product_template_rel separate
- **source_index_not_exercised** (product_combo_product_template_rel): source index not exercised by any confirmed access pattern; keep or drop

## productProduct

From `product_product` with `customer_product_reference`, `product_product_uom_uom_rel`, `product_uom`, `product_variant_combination` embedded.

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
  customerProductReference: [{  // customer_product_reference, 1:N assumed
    partnerId: int,  // partner_id
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    customerProductReference: string,  // customer_product_reference
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  uomUomRel: [{  // product_product_uom_uom_rel, 1:N derived
    uomUomId: int,  // uom_uom_id
  }],
  productUom: [{  // product_uom, 1:N derived
    id: int,  // id
    uomId: int,  // uom_id
    companyId: int,  // company_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    barcode: string,  // barcode
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  productVariantCombination: [{  // product_variant_combination, 1:N derived
    productTemplateAttributeValueId: int,  // product_template_attribute_value_id
  }],
}
```

Why:
- product_product → account_move_line, product_supplierinfo, product_value, stock_lot, stock_move, stock_move_line, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_product → customer_product_reference: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- product_product → product_combo_item, product_pricelist_item, purchase_order_line, sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_base_unit → product_product: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template → product_product: **reference**, the app reads it on its own (derived)
- product_product → product_product_uom_uom_rel, product_variant_combination: **embed**, a link table, kept as an array on this side (derived)
- uom_uom → product_product_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- product_product → product_tag_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- product_product → product_uom: **embed**, the app reads it with its parent (derived)
- uom_uom → product_uom: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template_attribute_value → product_variant_combination: **reference**, a link table, embedded on the other side (assumed)
- product_product → stock_putaway_rule, stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_product → stock_warehouse_orderpoint: **reference**, the app reads it on its own (derived)

Open questions (17):
- **fanout_unmeasured** (customer_product_reference): customer_product_reference has no rows per product_product in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (product_product_uom_uom_rel): product_product_uom_uom_rel has no rows per product_product in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (product_uom): product_uom has no rows per product_product in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (product_product_uom_uom_rel): app reads uom_uom with every product_product_uom_uom_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_uom): app reads uom_uom with every product_uom: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_variant_combination): app reads product_template_attribute_value with every product_variant_combination: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_product): app reads product_base_unit with every product_product: copy up to 5 read fields of product_base_unit into product_product documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_product): app reads product_template with every product_product: copy up to 5 read fields of product_template into product_product documents (extended reference) or keep the $lookup
- **cascade_into_embed** (product_product_uom_uom_rel): product_product_uom_uom_rel is embedded in product_product, but deleting a uom_uom row cascades to its product_product_uom_uom_rel: the app must pull them from every product_product document, or keep product_product_uom_uom_rel separate
- **cascade_into_embed** (product_uom): product_uom is embedded in product_product, but deleting a uom_uom row cascades to its product_uom: the app must pull them from every product_product document, or keep product_uom separate
- **single_valued_index_key** (product_product): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (product_product): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_product): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_product_uom_uom_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_uom): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_uom): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_variant_combination): source index not exercised by any confirmed access pattern; keep or drop

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
  productProductRel: [{  // product_tag_product_product_rel, 1:N derived
    productProductId: int,  // product_product_id
  }],
  productTemplateRel: [{  // product_tag_product_template_rel, 1:N derived
    productTemplateId: int,  // product_template_id
  }],
}
```

Why:
- product_product → product_tag_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- product_tag → product_tag_product_product_rel, product_tag_product_template_rel: **embed**, a link table, kept as an array on this side (derived)
- product_template → product_tag_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (8):
- **fanout_unmeasured** (product_tag_product_product_rel): product_tag_product_product_rel has no rows per product_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (product_tag_product_template_rel): product_tag_product_template_rel has no rows per product_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (product_tag_product_product_rel): app reads product_product with every product_tag_product_product_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_tag_product_template_rel): app reads product_template with every product_tag_product_template_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (product_tag_product_product_rel): product_tag_product_product_rel is embedded in product_tag, but deleting a product_product row cascades to its product_tag_product_product_rel: the app must pull them from every product_tag document, or keep product_tag_product_product_rel separate
- **cascade_into_embed** (product_tag_product_template_rel): product_tag_product_template_rel is embedded in product_tag, but deleting a product_template row cascades to its product_tag_product_template_rel: the app must pull them from every product_tag document, or keep product_tag_product_template_rel separate
- **source_index_not_exercised** (product_tag_product_product_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_tag_product_template_rel): source index not exercised by any confirmed access pattern; keep or drop

## productTemplate

From `product_template` with `product_optional_rel`, `product_template_attribute_line`, `product_template_uom_uom_rel` embedded.

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
  productOptionalRel: [{  // product_optional_rel, 1:N derived
    srcId: int,  // src_id
  }],
  attributeLine: [{  // product_template_attribute_line, 1:N derived
    id: int,  // id
    sequence: int,  // sequence
    attributeId: int,  // attribute_id
    valueCount: int,  // value_count
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    active: bool,  // active
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  uomUomRel: [{  // product_template_uom_uom_rel, 1:N derived
    uomUomId: int,  // uom_uom_id
  }],
}
```

Why:
- product_template → account_account_tag_product_template_rel, product_attribute_product_template_rel, product_combo_product_template_rel, product_optional_rel, product_supplier_taxes_rel, product_tag_product_template_rel, product_taxes_rel, stock_route_product: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_optional_rel, product_template_uom_uom_rel: **embed**, a link table, kept as an array on this side (derived)
- product_template → product_pricelist_item, product_template_attribute_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template → product_product: **reference**, the app reads it on its own (derived)
- product_template → product_supplierinfo: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_base_unit, product_category, uom_uom → product_template: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_attribute → product_template_attribute_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template → product_template_attribute_line: **embed**, the app reads it with its parent (derived)
- uom_uom → product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (14):
- **fanout_unmeasured** (product_template_uom_uom_rel): product_template_uom_uom_rel has no rows per product_template in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (product_optional_rel): app reads product_template with every product_optional_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_template_attribute_line): app reads product_attribute with every product_template_attribute_line: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_template_uom_uom_rel): app reads uom_uom with every product_template_uom_uom_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_template): app reads product_base_unit with every product_template: copy up to 5 read fields of product_base_unit into product_template documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_template): app reads product_category with every product_template: copy up to 5 read fields of product_category into product_template documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_template): app reads uom_uom with every product_template: copy up to 5 read fields of uom_uom into product_template documents (extended reference) or keep the $lookup
- **cascade_into_embed** (product_template_uom_uom_rel): product_template_uom_uom_rel is embedded in product_template, but deleting a uom_uom row cascades to its product_template_uom_uom_rel: the app must pull them from every product_template document, or keep product_template_uom_uom_rel separate
- **lob** (product_template): LOB column(s) purchase_line_warn_msg, sale_line_warn_msg measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **single_valued_index_key** (product_template): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **single_valued_index_key** (product_template_attribute_line): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (product_optional_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_template): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_template_uom_uom_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  productTemplateAttributeExcludedValueIdsRel: [{  // product_template_attribute_excluded_value_ids_rel, 1:N derived
    productTemplateAttributeValueId: int,  // product_template_attribute_value_id
  }],
  purchaseOrderLineRel: [{  // product_template_attribute_value_purchase_order_line_rel, 1:N derived
    purchaseOrderLineId: int,  // purchase_order_line_id
  }],
  saleOrderLineRel: [{  // product_template_attribute_value_sale_order_line_rel, 1:N derived
    saleOrderLineId: int,  // sale_order_line_id
  }],
  templateAttributeValueStockMoveRel: [{  // template_attribute_value_stock_move_rel, 1:N derived
    moveId: int,  // move_id
  }],
}
```

Why:
- product_template_attribute_value → product_attribute_custom_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel, product_template_attribute_value_purchase_order_line_rel, product_template_attribute_value_sale_order_line_rel, template_attribute_value_stock_move_rel: **embed**, a link table, kept as an array on this side (derived)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel, product_variant_combination: **reference**, a link table, embedded on the other side (assumed)
- product_attribute_value, product_attribute, product_template → product_template_attribute_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template_attribute_line → product_template_attribute_value: **reference**, the app reads it on its own (derived)
- purchase_order_line → product_template_attribute_value_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → product_template_attribute_value_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → template_attribute_value_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (17):
- **fanout_unmeasured** (product_template_attribute_value_purchase_order_line_rel): product_template_attribute_value_purchase_order_line_rel has no rows per product_template_attribute_value in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (product_template_attribute_value_sale_order_line_rel): product_template_attribute_value_sale_order_line_rel has no rows per product_template_attribute_value in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (template_attribute_value_stock_move_rel): template_attribute_value_stock_move_rel has no rows per product_template_attribute_value in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (product_template_attribute_excluded_value_ids_rel): app reads product_template_attribute_value with every product_template_attribute_excluded_value_ids_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_template_attribute_value_purchase_order_line_rel): app reads purchase_order_line with every product_template_attribute_value_purchase_order_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_template_attribute_value_sale_order_line_rel): app reads sale_order_line with every product_template_attribute_value_sale_order_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (template_attribute_value_stock_move_rel): app reads stock_move with every template_attribute_value_stock_move_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (product_template_attribute_value): app reads product_attribute_value with every product_template_attribute_value: copy up to 5 read fields of product_attribute_value into product_template_attribute_value documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_template_attribute_value): app reads product_template_attribute_line with every product_template_attribute_value: copy up to 5 read fields of product_template_attribute_line into product_template_attribute_value documents (extended reference) or keep the $lookup
- **cascade_into_embed** (product_template_attribute_value_purchase_order_line_rel): product_template_attribute_value_purchase_order_line_rel is embedded in product_template_attribute_value, but deleting a purchase_order_line row cascades to its product_template_attribute_value_purchase_order_line_rel: the app must pull them from every product_template_attribute_value document, or keep product_template_attribute_value_purchase_order_line_rel separate
- **cascade_into_embed** (product_template_attribute_value_sale_order_line_rel): product_template_attribute_value_sale_order_line_rel is embedded in product_template_attribute_value, but deleting a sale_order_line row cascades to its product_template_attribute_value_sale_order_line_rel: the app must pull them from every product_template_attribute_value document, or keep product_template_attribute_value_sale_order_line_rel separate
- **cascade_into_embed** (template_attribute_value_stock_move_rel): template_attribute_value_stock_move_rel is embedded in product_template_attribute_value, but deleting a stock_move row cascades to its template_attribute_value_stock_move_rel: the app must pull them from every product_template_attribute_value document, or keep template_attribute_value_stock_move_rel separate
- **source_index_not_exercised** (product_template_attribute_excluded_value_ids_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_template_attribute_value): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_template_attribute_value_purchase_order_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_template_attribute_value_sale_order_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (template_attribute_value_stock_move_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  stockPickingRel: [{  // purchase_order_stock_picking_rel, 1:N derived
    stockPickingId: int,  // stock_picking_id
  }],
}
```

Why:
- purchase_order → account_move_purchase_order_rel, stock_reference_purchase_rel: **reference**, a link table, embedded on the other side (assumed)
- account_fiscal_position, account_incoterms, account_payment_term, stock_picking_type → purchase_order: **reference**, other tables also point at it, so it keeps its own collection (derived)
- purchase_order → purchase_order_line: **reference**, the app reads it on its own (derived)
- purchase_order → purchase_order_stock_picking_rel: **embed**, a link table, kept as an array on this side (derived)
- stock_picking → purchase_order_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (14):
- **extended_reference_candidate** (purchase_order_stock_picking_rel): app reads stock_picking with every purchase_order_stock_picking_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (purchase_order): app reads account_fiscal_position with every purchase_order: copy up to 5 read fields of account_fiscal_position into purchase_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order): app reads account_incoterms with every purchase_order: copy up to 5 read fields of account_incoterms into purchase_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order): app reads account_payment_term with every purchase_order: copy up to 5 read fields of account_payment_term into purchase_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order): app reads stock_picking_type with every purchase_order: copy up to 5 read fields of stock_picking_type into purchase_order documents (extended reference) or keep the $lookup
- **cascade_into_embed** (purchase_order_stock_picking_rel): purchase_order_stock_picking_rel is embedded in purchase_order, but deleting a stock_picking row cascades to its purchase_order_stock_picking_rel: the app must pull them from every purchase_order document, or keep purchase_order_stock_picking_rel separate
- **lob** (purchase_order): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **single_valued_index_key** (purchase_order): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (purchase_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (purchase_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (purchase_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (purchase_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (purchase_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (purchase_order_stock_picking_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  accrualMoveRel: [{  // purchase_order_line_accrual_move_rel, 1:N derived
    moveId: int,  // move_id
  }],
}
```

Why:
- purchase_order_line → account_move_line, stock_move: **reference**, other tables also point at it, so it keeps its own collection (derived)
- purchase_order_line → account_tax_purchase_order_line_rel, product_template_attribute_value_purchase_order_line_rel, stock_move_created_purchase_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_location, stock_warehouse_orderpoint, product_product, sale_order_line, uom_uom → purchase_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- purchase_order → purchase_order_line: **reference**, the app reads it on its own (derived)
- account_move → purchase_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- purchase_order_line → purchase_order_line_accrual_move_rel: **embed**, a link table, kept as an array on this side (derived)

Open questions (12):
- **fanout_unmeasured** (purchase_order_line_accrual_move_rel): purchase_order_line_accrual_move_rel has no rows per purchase_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (purchase_order_line_accrual_move_rel): app reads account_move with every purchase_order_line_accrual_move_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (purchase_order_line): app reads stock_location with every purchase_order_line: copy up to 5 read fields of stock_location into purchase_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order_line): app reads purchase_order with every purchase_order_line: copy up to 5 read fields of purchase_order into purchase_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order_line): app reads stock_warehouse_orderpoint with every purchase_order_line: copy up to 5 read fields of stock_warehouse_orderpoint into purchase_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order_line): app reads product_product with every purchase_order_line: copy up to 5 read fields of product_product into purchase_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order_line): app reads sale_order_line with every purchase_order_line: copy up to 5 read fields of sale_order_line into purchase_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (purchase_order_line): app reads uom_uom with every purchase_order_line: copy up to 5 read fields of uom_uom into purchase_order_line documents (extended reference) or keep the $lookup
- **cascade_into_embed** (purchase_order_line_accrual_move_rel): purchase_order_line_accrual_move_rel is embedded in purchase_order_line, but deleting a account_move row cascades to its purchase_order_line_accrual_move_rel: the app must pull them from every purchase_order_line document, or keep purchase_order_line_accrual_move_rel separate
- **lob** (purchase_order_line): LOB column(s) name measured max 25 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (purchase_order_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (purchase_order_line_accrual_move_rel): source index not exercised by any confirmed access pattern; keep or drop

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
- account_fiscal_position, account_incoterms, account_journal, account_payment_term, account_payment_method_line, product_pricelist, stock_warehouse → sale_order: **reference**, other tables also point at it, so it keeps its own collection (derived)
- sale_order → sale_order_line: **reference**, the app reads it on its own (derived)
- sale_order → sale_order_tag_rel: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- sale_order → sale_order_transaction_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- sale_order → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (derived)
- sale_order → stock_reference_sale_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (17):
- **fanout_unmeasured** (sale_order_transaction_rel): sale_order_transaction_rel has no rows per sale_order in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (sale_order): app reads account_fiscal_position with every sale_order: copy up to 5 read fields of account_fiscal_position into sale_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order): app reads account_incoterms with every sale_order: copy up to 5 read fields of account_incoterms into sale_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order): app reads account_journal with every sale_order: copy up to 5 read fields of account_journal into sale_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order): app reads account_payment_term with every sale_order: copy up to 5 read fields of account_payment_term into sale_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order): app reads account_payment_method_line with every sale_order: copy up to 5 read fields of account_payment_method_line into sale_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order): app reads product_pricelist with every sale_order: copy up to 5 read fields of product_pricelist into sale_order documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order): app reads stock_warehouse with every sale_order: copy up to 5 read fields of stock_warehouse into sale_order documents (extended reference) or keep the $lookup
- **lob** (sale_order): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (sale_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order_tag_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order_transaction_rel): source index not exercised by any confirmed access pattern; keep or drop

## saleOrderLine

From `sale_order_line` with `product_attribute_custom_value`, `sale_order_line_accrual_move_rel`, `sale_order_line_invoice_rel`, `sale_order_line_stock_route_rel` embedded.

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
  productAttributeCustomValue: [{  // product_attribute_custom_value, 1:N derived
    id: int,  // id
    customProductTemplateAttributeValueId: int,  // custom_product_template_attribute_value_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    customValue: string,  // custom_value
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  accrualMoveRel: [{  // sale_order_line_accrual_move_rel, 1:N derived
    moveId: int,  // move_id
  }],
  invoiceRel: [{  // sale_order_line_invoice_rel, 1:N derived
    invoiceLineId: int,  // invoice_line_id
  }],
  stockRouteRel: [{  // sale_order_line_stock_route_rel, 1:N derived
    stockRouteId: int,  // stock_route_id
  }],
}
```

Why:
- sale_order_line → account_tax_sale_order_line_rel, product_template_attribute_value_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template_attribute_value → product_attribute_custom_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- sale_order_line → product_attribute_custom_value: **embed**, the app reads it with its parent (derived)
- sale_order_line → purchase_order_line, sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_combo_item, product_product, uom_uom, stock_warehouse → sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- sale_order → sale_order_line: **reference**, the app reads it on its own (derived)
- account_move → sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → sale_order_line_accrual_move_rel, sale_order_line_invoice_rel, sale_order_line_stock_route_rel: **embed**, a link table, kept as an array on this side (derived)
- account_move_line → sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → sale_order_line_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → stock_move: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (23):
- **fanout_unmeasured** (product_attribute_custom_value): product_attribute_custom_value has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (sale_order_line_accrual_move_rel): sale_order_line_accrual_move_rel has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (sale_order_line_invoice_rel): sale_order_line_invoice_rel has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (sale_order_line_stock_route_rel): sale_order_line_stock_route_rel has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (product_attribute_custom_value): app reads product_template_attribute_value with every product_attribute_custom_value: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (sale_order_line_accrual_move_rel): app reads account_move with every sale_order_line_accrual_move_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (sale_order_line_invoice_rel): app reads account_move_line with every sale_order_line_invoice_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (sale_order_line_stock_route_rel): app reads stock_route with every sale_order_line_stock_route_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (sale_order_line): app reads product_combo_item with every sale_order_line: copy up to 5 read fields of product_combo_item into sale_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order_line): app reads sale_order_line with every sale_order_line: copy up to 5 read fields of sale_order_line into sale_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order_line): app reads sale_order with every sale_order_line: copy up to 5 read fields of sale_order into sale_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order_line): app reads product_product with every sale_order_line: copy up to 5 read fields of product_product into sale_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order_line): app reads uom_uom with every sale_order_line: copy up to 5 read fields of uom_uom into sale_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order_line): app reads uom_uom with every sale_order_line: copy up to 5 read fields of uom_uom into sale_order_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (sale_order_line): app reads stock_warehouse with every sale_order_line: copy up to 5 read fields of stock_warehouse into sale_order_line documents (extended reference) or keep the $lookup
- **cascade_into_embed** (sale_order_line_accrual_move_rel): sale_order_line_accrual_move_rel is embedded in sale_order_line, but deleting a account_move row cascades to its sale_order_line_accrual_move_rel: the app must pull them from every sale_order_line document, or keep sale_order_line_accrual_move_rel separate
- **cascade_into_embed** (sale_order_line_invoice_rel): sale_order_line_invoice_rel is embedded in sale_order_line, but deleting a account_move_line row cascades to its sale_order_line_invoice_rel: the app must pull them from every sale_order_line document, or keep sale_order_line_invoice_rel separate
- **lob** (sale_order_line): LOB column(s) name measured max 45 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (sale_order_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order_line_accrual_move_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order_line_invoice_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (sale_order_line_stock_route_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  stockPickingTypeRel: [{  // stock_location_stock_picking_type_rel, 1:N derived
    stockPickingTypeId: int,  // stock_picking_type_id
  }],
}
```

Why:
- stock_location → purchase_order_line, stock_rule, stock_warehouse_orderpoint: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_location → stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_picking, stock_picking_type, stock_quant, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_removal, stock_storage_category, account_account, stock_warehouse → stock_location: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_picking_type → stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_location → stock_location_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (derived)
- stock_location → stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (12):
- **fanout_unmeasured** (stock_location_stock_picking_type_rel): stock_location_stock_picking_type_rel has no rows per stock_location in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_location_stock_picking_type_rel): app reads stock_picking_type with every stock_location_stock_picking_type_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_location): app reads stock_location with every stock_location: copy up to 5 read fields of stock_location into stock_location documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_location): app reads product_removal with every stock_location: copy up to 5 read fields of product_removal into stock_location documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_location): app reads stock_storage_category with every stock_location: copy up to 5 read fields of stock_storage_category into stock_location documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_location): app reads account_account with every stock_location: copy up to 5 read fields of account_account into stock_location documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_location): app reads stock_warehouse with every stock_location: copy up to 5 read fields of stock_warehouse into stock_location documents (extended reference) or keep the $lookup
- **cascade_into_embed** (stock_location_stock_picking_type_rel): stock_location_stock_picking_type_rel is embedded in stock_location, but deleting a stock_picking_type row cascades to its stock_location_stock_picking_type_rel: the app must pull them from every stock_location document, or keep stock_location_stock_picking_type_rel separate
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (stock_location): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_location): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_location_stock_picking_type_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  createdPurchaseLineRel: [{  // stock_move_created_purchase_line_rel, 1:N derived
    createdPurchaseLineId: int,  // created_purchase_line_id
  }],
  moveRel: [{  // stock_move_move_rel, 1:N derived
    moveOrigId: int,  // move_orig_id
  }],
  stockScrapReasonTagRel: [{  // stock_move_stock_scrap_reason_tag_rel, 1:N derived
    stockScrapReasonTagId: int,  // stock_scrap_reason_tag_id
  }],
}
```

Why:
- stock_move → account_analytic_line_stock_move_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- stock_move → account_move_line, product_value, stock_move, stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_move, stock_location, stock_warehouse_orderpoint, uom_uom, stock_picking, stock_picking_type, product_product, purchase_order_line, stock_rule, sale_order_line, stock_warehouse → stock_move: **reference**, other tables also point at it, so it keeps its own collection (derived)
- purchase_order_line → stock_move_created_purchase_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → stock_move_created_purchase_line_rel, stock_move_move_rel, stock_move_stock_scrap_reason_tag_rel: **embed**, a link table, kept as an array on this side (derived)
- stock_move → stock_move_move_rel, stock_reference_move_rel, stock_route_move, template_attribute_value_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (29):
- **fanout_unmeasured** (account_analytic_line_stock_move_rel): account_analytic_line_stock_move_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_move_created_purchase_line_rel): stock_move_created_purchase_line_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_move_move_rel): stock_move_move_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_move_stock_scrap_reason_tag_rel): stock_move_stock_scrap_reason_tag_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_move_created_purchase_line_rel): app reads purchase_order_line with every stock_move_created_purchase_line_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_move_move_rel): app reads stock_move with every stock_move_move_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_move_stock_scrap_reason_tag_rel): app reads stock_scrap_reason_tag with every stock_move_stock_scrap_reason_tag_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_move): app reads account_move with every stock_move: copy up to 5 read fields of account_move into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_location with every stock_move: copy up to 5 read fields of stock_location into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_location with every stock_move: copy up to 5 read fields of stock_location into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_location with every stock_move: copy up to 5 read fields of stock_location into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_warehouse_orderpoint with every stock_move: copy up to 5 read fields of stock_warehouse_orderpoint into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_move with every stock_move: copy up to 5 read fields of stock_move into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads uom_uom with every stock_move: copy up to 5 read fields of uom_uom into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_picking with every stock_move: copy up to 5 read fields of stock_picking into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_picking_type with every stock_move: copy up to 5 read fields of stock_picking_type into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads product_product with every stock_move: copy up to 5 read fields of product_product into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads purchase_order_line with every stock_move: copy up to 5 read fields of purchase_order_line into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_rule with every stock_move: copy up to 5 read fields of stock_rule into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads sale_order_line with every stock_move: copy up to 5 read fields of sale_order_line into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads uom_uom with every stock_move: copy up to 5 read fields of uom_uom into stock_move documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move): app reads stock_warehouse with every stock_move: copy up to 5 read fields of stock_warehouse into stock_move documents (extended reference) or keep the $lookup
- **cascade_into_embed** (stock_move_created_purchase_line_rel): stock_move_created_purchase_line_rel is embedded in stock_move, but deleting a purchase_order_line row cascades to its stock_move_created_purchase_line_rel: the app must pull them from every stock_move document, or keep stock_move_created_purchase_line_rel separate
- **cascade_into_embed** (stock_move_stock_scrap_reason_tag_rel): stock_move_stock_scrap_reason_tag_rel is embedded in stock_move, but deleting a stock_scrap_reason_tag row cascades to its stock_move_stock_scrap_reason_tag_rel: the app must pull them from every stock_move document, or keep stock_move_stock_scrap_reason_tag_rel separate
- **lob** (stock_move): LOB column(s) description_picking_manual measured max 49 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (account_analytic_line_stock_move_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_move_created_purchase_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_move_move_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_move_stock_scrap_reason_tag_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  consumeRel: [{  // stock_move_line_consume_rel, 1:N derived
    produceLineId: int,  // produce_line_id
  }],
}
```

Why:
- stock_location, stock_lot, stock_move, stock_package_history, stock_package, stock_picking, product_product, uom_uom → stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_move_line → stock_move_line_consume_rel: **embed**, a link table, kept as an array on this side (derived)
- stock_move_line → stock_move_line_consume_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (13):
- **fanout_unmeasured** (stock_move_line_consume_rel): stock_move_line_consume_rel has no rows per stock_move_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_move_line_consume_rel): app reads stock_move_line with every stock_move_line_consume_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_move_line): app reads stock_location with every stock_move_line: copy up to 5 read fields of stock_location into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads stock_location with every stock_move_line: copy up to 5 read fields of stock_location into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads stock_lot with every stock_move_line: copy up to 5 read fields of stock_lot into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads stock_move with every stock_move_line: copy up to 5 read fields of stock_move into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads stock_package_history with every stock_move_line: copy up to 5 read fields of stock_package_history into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads stock_package with every stock_move_line: copy up to 5 read fields of stock_package into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads stock_picking with every stock_move_line: copy up to 5 read fields of stock_picking into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads product_product with every stock_move_line: copy up to 5 read fields of product_product into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads stock_package with every stock_move_line: copy up to 5 read fields of stock_package into stock_move_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_move_line): app reads uom_uom with every stock_move_line: copy up to 5 read fields of uom_uom into stock_move_line documents (extended reference) or keep the $lookup
- **source_index_not_exercised** (stock_move_line_consume_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  stockPickingRel: [{  // stock_package_history_stock_picking_rel, 1:N derived
    stockPickingId: int,  // stock_picking_id
  }],
}
```

Why:
- stock_package_history → stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_location, stock_package → stock_package_history: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_package_history → stock_package_history_stock_picking_rel: **embed**, a link table, kept as an array on this side (derived)
- stock_picking → stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (10):
- **fanout_unmeasured** (stock_package_history_stock_picking_rel): stock_package_history_stock_picking_rel has no rows per stock_package_history in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_package_history_stock_picking_rel): app reads stock_picking with every stock_package_history_stock_picking_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_package_history): app reads stock_location with every stock_package_history: copy up to 5 read fields of stock_location into stock_package_history documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package_history): app reads stock_location with every stock_package_history: copy up to 5 read fields of stock_location into stock_package_history documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package_history): app reads stock_package with every stock_package_history: copy up to 5 read fields of stock_package into stock_package_history documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package_history): app reads stock_package with every stock_package_history: copy up to 5 read fields of stock_package into stock_package_history documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package_history): app reads stock_package with every stock_package_history: copy up to 5 read fields of stock_package into stock_package_history documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package_history): app reads stock_package with every stock_package_history: copy up to 5 read fields of stock_package into stock_package_history documents (extended reference) or keep the $lookup
- **cascade_into_embed** (stock_package_history_stock_picking_rel): stock_package_history_stock_picking_rel is embedded in stock_package_history, but deleting a stock_picking row cascades to its stock_package_history_stock_picking_rel: the app must pull them from every stock_package_history document, or keep stock_package_history_stock_picking_rel separate
- **source_index_not_exercised** (stock_package_history_stock_picking_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  stockPutawayRuleRel: [{  // stock_package_type_stock_putaway_rule_rel, 1:N derived
    stockPutawayRuleId: int,  // stock_putaway_rule_id
  }],
  stockRouteRel: [{  // stock_package_type_stock_route_rel, 1:N derived
    stockRouteId: int,  // stock_route_id
  }],
}
```

Why:
- stock_package_type → stock_package, uom_uom: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_package_type → stock_package_type_stock_putaway_rule_rel, stock_package_type_stock_route_rel: **embed**, a link table, kept as an array on this side (derived)
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_package_type_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_package_type → stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (9):
- **fanout_unmeasured** (stock_package_type_stock_putaway_rule_rel): stock_package_type_stock_putaway_rule_rel has no rows per stock_package_type in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_package_type_stock_route_rel): stock_package_type_stock_route_rel has no rows per stock_package_type in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_package_type_stock_putaway_rule_rel): app reads stock_putaway_rule with every stock_package_type_stock_putaway_rule_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_package_type_stock_route_rel): app reads stock_route with every stock_package_type_stock_route_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (stock_package_type_stock_putaway_rule_rel): stock_package_type_stock_putaway_rule_rel is embedded in stock_package_type, but deleting a stock_putaway_rule row cascades to its stock_package_type_stock_putaway_rule_rel: the app must pull them from every stock_package_type document, or keep stock_package_type_stock_putaway_rule_rel separate
- **cascade_into_embed** (stock_package_type_stock_route_rel): stock_package_type_stock_route_rel is embedded in stock_package_type, but deleting a stock_route row cascades to its stock_package_type_stock_route_rel: the app must pull them from every stock_package_type document, or keep stock_package_type_stock_route_rel separate
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (stock_package_type_stock_putaway_rule_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_package_type_stock_route_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  pickingTypeFavoriteUserRel: [{  // picking_type_favorite_user_rel, 1:N assumed
    userId: int,  // user_id
  }],
}
```

Why:
- stock_picking_type → picking_type_favorite_user_rel: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- stock_picking_type → product_category_stock_picking_type_rel, stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking_type → purchase_order, stock_move, stock_picking, stock_picking_batch, stock_picking_type, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_location, stock_warehouse → stock_picking_type: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_picking_type → stock_rule: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (7):
- **fanout_unmeasured** (picking_type_favorite_user_rel): picking_type_favorite_user_rel has no rows per stock_picking_type in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_picking_type): app reads stock_location with every stock_picking_type: copy up to 5 read fields of stock_location into stock_picking_type documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking_type): app reads stock_location with every stock_picking_type: copy up to 5 read fields of stock_location into stock_picking_type documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking_type): app reads stock_location with every stock_picking_type: copy up to 5 read fields of stock_location into stock_picking_type documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking_type): app reads stock_picking_type with every stock_picking_type: copy up to 5 read fields of stock_picking_type into stock_picking_type documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking_type): app reads stock_warehouse with every stock_picking_type: copy up to 5 read fields of stock_warehouse into stock_picking_type documents (extended reference) or keep the $lookup
- **source_index_not_exercised** (picking_type_favorite_user_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  moveRel: [{  // stock_reference_move_rel, 1:N derived
    moveId: int,  // move_id
  }],
  purchaseRel: [{  // stock_reference_purchase_rel, 1:N derived
    purchaseId: int,  // purchase_id
  }],
  saleRel: [{  // stock_reference_sale_rel, 1:N derived
    saleId: int,  // sale_id
  }],
}
```

Why:
- stock_move → stock_reference_move_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_reference → stock_reference_move_rel, stock_reference_purchase_rel, stock_reference_sale_rel: **embed**, a link table, kept as an array on this side (derived)
- purchase_order → stock_reference_purchase_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order → stock_reference_sale_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (9):
- **extended_reference_candidate** (stock_reference_move_rel): app reads stock_move with every stock_reference_move_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_reference_purchase_rel): app reads purchase_order with every stock_reference_purchase_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_reference_sale_rel): app reads sale_order with every stock_reference_sale_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (stock_reference_move_rel): stock_reference_move_rel is embedded in stock_reference, but deleting a stock_move row cascades to its stock_reference_move_rel: the app must pull them from every stock_reference document, or keep stock_reference_move_rel separate
- **cascade_into_embed** (stock_reference_purchase_rel): stock_reference_purchase_rel is embedded in stock_reference, but deleting a purchase_order row cascades to its stock_reference_purchase_rel: the app must pull them from every stock_reference document, or keep stock_reference_purchase_rel separate
- **cascade_into_embed** (stock_reference_sale_rel): stock_reference_sale_rel is embedded in stock_reference, but deleting a sale_order row cascades to its stock_reference_sale_rel: the app must pull them from every stock_reference document, or keep stock_reference_sale_rel separate
- **source_index_not_exercised** (stock_reference_move_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_reference_purchase_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_reference_sale_rel): source index not exercised by any confirmed access pattern; keep or drop

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
  categ: [{  // stock_route_categ, 1:N derived
    categId: int,  // categ_id
  }],
  move: [{  // stock_route_move, 1:N derived
    moveId: int,  // move_id
  }],
  product: [{  // stock_route_product, 1:N derived
    productId: int,  // product_id
  }],
  warehouse: [{  // stock_route_warehouse, 1:N derived
    warehouseId: int,  // warehouse_id
  }],
}
```

Why:
- stock_route → sale_order_line_stock_route_rel, stock_package_type_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_warehouse → stock_route: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_route_categ, stock_route_move, stock_route_product, stock_route_warehouse: **embed**, a link table, kept as an array on this side (derived)
- stock_move → stock_route_move: **reference**, a link table, embedded on the other side (assumed)
- product_template → stock_route_product: **reference**, a link table, embedded on the other side (assumed)
- stock_warehouse → stock_route_warehouse: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_rule: **reference**, the app reads it on its own (derived)
- stock_route → stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_route → stock_warehouse_orderpoint: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (18):
- **fanout_unmeasured** (stock_route_categ): stock_route_categ has no rows per stock_route in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_route_move): stock_route_move has no rows per stock_route in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_route_product): stock_route_product has no rows per stock_route in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_route_categ): app reads product_category with every stock_route_categ: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_route_move): app reads stock_move with every stock_route_move: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_route_product): app reads product_template with every stock_route_product: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_route_warehouse): app reads stock_warehouse with every stock_route_warehouse: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_route): app reads stock_warehouse with every stock_route: copy up to 5 read fields of stock_warehouse into stock_route documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_route): app reads stock_warehouse with every stock_route: copy up to 5 read fields of stock_warehouse into stock_route documents (extended reference) or keep the $lookup
- **cascade_into_embed** (stock_route_categ): stock_route_categ is embedded in stock_route, but deleting a product_category row cascades to its stock_route_categ: the app must pull them from every stock_route document, or keep stock_route_categ separate
- **cascade_into_embed** (stock_route_move): stock_route_move is embedded in stock_route, but deleting a stock_move row cascades to its stock_route_move: the app must pull them from every stock_route document, or keep stock_route_move separate
- **cascade_into_embed** (stock_route_product): stock_route_product is embedded in stock_route, but deleting a product_template row cascades to its stock_route_product: the app must pull them from every stock_route document, or keep stock_route_product separate
- **cascade_into_embed** (stock_route_warehouse): stock_route_warehouse is embedded in stock_route, but deleting a stock_warehouse row cascades to its stock_route_warehouse: the app must pull them from every stock_route document, or keep stock_route_warehouse separate
- **single_valued_index_key** (stock_route): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (stock_route_categ): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_route_move): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_route_product): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_route_warehouse): source index not exercised by any confirmed access pattern; keep or drop

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
  stockWhResupplyTable: [{  // stock_wh_resupply_table, 1:N derived
    supplierWhId: int,  // supplier_wh_id
  }],
}
```

Why:
- stock_warehouse → sale_order, stock_location, stock_move, stock_picking_type, stock_route: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_warehouse → sale_order_line, stock_rule, stock_warehouse_orderpoint: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_warehouse → stock_route_warehouse, stock_wh_resupply_table: **reference**, a link table, embedded on the other side (assumed)
- stock_rule, stock_route, stock_picking_type, stock_location → stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_warehouse → stock_wh_resupply_table: **embed**, a link table, kept as an array on this side (derived)

Open questions (22):
- **fanout_unmeasured** (stock_wh_resupply_table): stock_wh_resupply_table has no rows per stock_warehouse in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (stock_wh_resupply_table): app reads stock_warehouse with every stock_wh_resupply_table: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (stock_warehouse): app reads stock_rule with every stock_warehouse: copy up to 5 read fields of stock_rule into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_route with every stock_warehouse: copy up to 5 read fields of stock_route into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_location with every stock_warehouse: copy up to 5 read fields of stock_location into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_rule with every stock_warehouse: copy up to 5 read fields of stock_rule into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_route with every stock_warehouse: copy up to 5 read fields of stock_route into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_location with every stock_warehouse: copy up to 5 read fields of stock_location into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_location with every stock_warehouse: copy up to 5 read fields of stock_location into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_location with every stock_warehouse: copy up to 5 read fields of stock_location into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_location with every stock_warehouse: copy up to 5 read fields of stock_location into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_location with every stock_warehouse: copy up to 5 read fields of stock_location into stock_warehouse documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse): app reads stock_picking_type with every stock_warehouse: copy up to 5 read fields of stock_picking_type into stock_warehouse documents (extended reference) or keep the $lookup
- **single_valued_index_key** (stock_warehouse): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (stock_wh_resupply_table): source index not exercised by any confirmed access pattern; keep or drop

## accountBankStatementLine

From `account_bank_statement_line`.

Why:
- account_journal, account_bank_statement → account_bank_statement_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_move → account_bank_statement_line: **reference**, the app reads it on its own (derived)
- account_bank_statement_line → account_move: **reference**, the app reads it on its own (derived)
- account_bank_statement_line → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (6):
- **extended_reference_candidate** (account_bank_statement_line): app reads account_journal with every account_bank_statement_line: copy up to 5 read fields of account_journal into account_bank_statement_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_bank_statement_line): app reads account_move with every account_bank_statement_line: copy up to 5 read fields of account_move into account_bank_statement_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_bank_statement_line): app reads account_bank_statement with every account_bank_statement_line: copy up to 5 read fields of account_bank_statement into account_bank_statement_line documents (extended reference) or keep the $lookup
- **single_valued_index_key** (account_bank_statement_line): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (account_bank_statement_line): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_bank_statement_line): source index not exercised by any confirmed access pattern; keep or drop

## accountFullReconcile

From `account_full_reconcile`.

Why:
- account_full_reconcile → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_full_reconcile → account_partial_reconcile: **reference**, it is embedded under another parent; this one is referenced (derived)

## accountIncoterms

From `account_incoterms`.

Why:
- account_incoterms → account_move: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_incoterms → purchase_order, sale_order: **reference**, other tables also point at it, so it keeps its own collection (derived)

## accountJournalGroup

From `account_journal_group`.

Why:
- account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (derived)

## accountLockException

From `account_lock_exception`.

## accountReconcileModelLineAccountTaxRel

From `account_reconcile_model_line_account_tax_rel`.

Why:
- account_reconcile_model_line → account_reconcile_model_line_account_tax_rel: **reference**, its parent is itself embedded, and arrays don't nest (derived)
- account_tax → account_reconcile_model_line_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)

## accountReportExpression

From `account_report_expression`.

Why:
- account_report_line → account_report_expression: **reference**, its parent is itself embedded, and arrays don't nest (derived)
- account_report_expression → account_report_external_value: **reference**, its parent is itself embedded, and arrays don't nest (assumed)

Open questions (1):
- **lob** (account_report_expression): LOB column(s) formula, subformula: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## accountReportExternalValue

From `account_report_external_value`.

Why:
- account_report_line → account_report_external_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_report_expression → account_report_external_value: **reference**, its parent is itself embedded, and arrays don't nest (assumed)

Open questions (1):
- **extended_reference_candidate** (account_report_external_value): app reads account_report_line with every account_report_external_value: copy up to 5 read fields of account_report_line into account_report_external_value documents (extended reference) or keep the $lookup

## accountTaxGroup

From `account_tax_group`.

Why:
- account_tax_group → account_move_line, account_tax: **reference**, other tables also point at it, so it keeps its own collection (derived)

## accountTaxRepartitionLine

From `account_tax_repartition_line`.

Why:
- account_tax_repartition_line → account_account_tag_account_tax_repartition_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax_repartition_line → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_account → account_tax_repartition_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_tax → account_tax_repartition_line: **reference**, the app reads it on its own (derived)

Open questions (2):
- **extended_reference_candidate** (account_tax_repartition_line): app reads account_account with every account_tax_repartition_line: copy up to 5 read fields of account_account into account_tax_repartition_line documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (account_tax_repartition_line): app reads account_tax with every account_tax_repartition_line: copy up to 5 read fields of account_tax into account_tax_repartition_line documents (extended reference) or keep the $lookup

## productAttributeValueProductTemplateAttributeLineRel

From `product_attribute_value_product_template_attribute_line_rel`.

Why:
- product_template_attribute_line → product_attribute_value_product_template_attribute_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_attribute_value → product_attribute_value_product_template_attribute_line_rel: **reference**, its parent is itself embedded, and arrays don't nest (derived)

## productBaseUnit

From `product_base_unit`.

Why:
- product_base_unit → product_product: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_base_unit → product_template: **reference**, other tables also point at it, so it keeps its own collection (derived)

## productDocument

From `product_document`.

## productPricelist

From `product_pricelist`.

Why:
- product_pricelist → product_pricelist_item: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_pricelist → product_pricelist_item: **reference**, the app reads it on its own (derived)
- product_pricelist → sale_order: **reference**, other tables also point at it, so it keeps its own collection (derived)

## productPricelistItem

From `product_pricelist_item`.

Why:
- product_pricelist, product_category, product_product, product_template, uom_uom → product_pricelist_item: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_pricelist → product_pricelist_item: **reference**, the app reads it on its own (derived)

Open questions (7):
- **extended_reference_candidate** (product_pricelist_item): app reads product_pricelist with every product_pricelist_item: copy up to 5 read fields of product_pricelist into product_pricelist_item documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_pricelist_item): app reads product_category with every product_pricelist_item: copy up to 5 read fields of product_category into product_pricelist_item documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_pricelist_item): app reads product_pricelist with every product_pricelist_item: copy up to 5 read fields of product_pricelist into product_pricelist_item documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_pricelist_item): app reads product_product with every product_pricelist_item: copy up to 5 read fields of product_product into product_pricelist_item documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_pricelist_item): app reads product_template with every product_pricelist_item: copy up to 5 read fields of product_template into product_pricelist_item documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_pricelist_item): app reads uom_uom with every product_pricelist_item: copy up to 5 read fields of uom_uom into product_pricelist_item documents (extended reference) or keep the $lookup
- **source_index_not_exercised** (product_pricelist_item): source index not exercised by any confirmed access pattern; keep or drop

## productRemoval

From `product_removal`.

Why:
- product_removal → product_category, stock_location: **reference**, other tables also point at it, so it keeps its own collection (derived)

## productSupplierinfo

From `product_supplierinfo`.

Why:
- product_product, product_template, uom_uom → product_supplierinfo: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_supplierinfo → stock_warehouse_orderpoint: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (3):
- **extended_reference_candidate** (product_supplierinfo): app reads product_product with every product_supplierinfo: copy up to 5 read fields of product_product into product_supplierinfo documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_supplierinfo): app reads product_template with every product_supplierinfo: copy up to 5 read fields of product_template into product_supplierinfo documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_supplierinfo): app reads uom_uom with every product_supplierinfo: copy up to 5 read fields of uom_uom into product_supplierinfo documents (extended reference) or keep the $lookup

## productValue

From `product_value`.

Why:
- account_move, stock_lot, stock_move, product_product → product_value: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (4):
- **extended_reference_candidate** (product_value): app reads account_move with every product_value: copy up to 5 read fields of account_move into product_value documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_value): app reads stock_lot with every product_value: copy up to 5 read fields of stock_lot into product_value documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_value): app reads stock_move with every product_value: copy up to 5 read fields of stock_move into product_value documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (product_value): app reads product_product with every product_value: copy up to 5 read fields of product_product into product_value documents (extended reference) or keep the $lookup

## returnReason

From `return_reason`.

Why:
- return_reason → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (derived)

## stockLot

From `stock_lot`.

Why:
- stock_lot → product_value, stock_move_line, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_location, product_product → stock_lot: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (3):
- **extended_reference_candidate** (stock_lot): app reads stock_location with every stock_lot: copy up to 5 read fields of stock_location into stock_lot documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_lot): app reads product_product with every stock_lot: copy up to 5 read fields of product_product into stock_lot documents (extended reference) or keep the $lookup
- **lob** (stock_lot): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## stockPackage

From `stock_package`.

Why:
- stock_package → stock_move_line, stock_package, stock_package_history, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_location, stock_package_type → stock_package: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (5):
- **extended_reference_candidate** (stock_package): app reads stock_location with every stock_package: copy up to 5 read fields of stock_location into stock_package documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package): app reads stock_package with every stock_package: copy up to 5 read fields of stock_package into stock_package documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package): app reads stock_package_type with every stock_package: copy up to 5 read fields of stock_package_type into stock_package documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_package): app reads stock_package with every stock_package: copy up to 5 read fields of stock_package into stock_package documents (extended reference) or keep the $lookup
- **source_index_not_exercised** (stock_package): source index not exercised by any confirmed access pattern; keep or drop

## stockPicking

From `stock_picking`.

Why:
- stock_picking → purchase_order_stock_picking_rel, stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking → stock_move, stock_move_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_picking_batch, stock_location, stock_picking_type, return_reason, sale_order → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (13):
- **extended_reference_candidate** (stock_picking): app reads stock_picking with every stock_picking: copy up to 5 read fields of stock_picking into stock_picking documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking): app reads stock_picking_batch with every stock_picking: copy up to 5 read fields of stock_picking_batch into stock_picking documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking): app reads stock_location with every stock_picking: copy up to 5 read fields of stock_location into stock_picking documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking): app reads stock_location with every stock_picking: copy up to 5 read fields of stock_location into stock_picking documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking): app reads stock_picking_type with every stock_picking: copy up to 5 read fields of stock_picking_type into stock_picking documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking): app reads stock_picking with every stock_picking: copy up to 5 read fields of stock_picking into stock_picking documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking): app reads return_reason with every stock_picking: copy up to 5 read fields of return_reason into stock_picking documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_picking): app reads sale_order with every stock_picking: copy up to 5 read fields of sale_order into stock_picking documents (extended reference) or keep the $lookup
- **lob** (stock_picking): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (stock_picking): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_picking): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (stock_picking): source index not exercised by any confirmed access pattern; keep or drop

## stockPickingBatch

From `stock_picking_batch`.

Why:
- stock_picking_batch → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_picking_type → stock_picking_batch: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (2):
- **extended_reference_candidate** (stock_picking_batch): app reads stock_picking_type with every stock_picking_batch: copy up to 5 read fields of stock_picking_type into stock_picking_batch documents (extended reference) or keep the $lookup
- **source_index_not_exercised** (stock_picking_batch): source index not exercised by any confirmed access pattern; keep or drop

## stockPutawayRule

From `stock_putaway_rule`.

Why:
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category, stock_location, product_product, stock_storage_category → stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (5):
- **extended_reference_candidate** (stock_putaway_rule): app reads product_category with every stock_putaway_rule: copy up to 5 read fields of product_category into stock_putaway_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_putaway_rule): app reads stock_location with every stock_putaway_rule: copy up to 5 read fields of stock_location into stock_putaway_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_putaway_rule): app reads stock_location with every stock_putaway_rule: copy up to 5 read fields of stock_location into stock_putaway_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_putaway_rule): app reads product_product with every stock_putaway_rule: copy up to 5 read fields of product_product into stock_putaway_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_putaway_rule): app reads stock_storage_category with every stock_putaway_rule: copy up to 5 read fields of stock_storage_category into stock_putaway_rule documents (extended reference) or keep the $lookup

## stockQuant

From `stock_quant`.

Why:
- stock_location, stock_lot, stock_package, product_product → stock_quant: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (6):
- **extended_reference_candidate** (stock_quant): app reads stock_location with every stock_quant: copy up to 5 read fields of stock_location into stock_quant documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_quant): app reads stock_lot with every stock_quant: copy up to 5 read fields of stock_lot into stock_quant documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_quant): app reads stock_package with every stock_quant: copy up to 5 read fields of stock_package into stock_quant documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_quant): app reads product_product with every stock_quant: copy up to 5 read fields of product_product into stock_quant documents (extended reference) or keep the $lookup
- **single_valued_index_key** (stock_quant): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (stock_quant): source index not exercised by any confirmed access pattern; keep or drop

## stockRule

From `stock_rule`.

Why:
- stock_rule → stock_move, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_location, stock_picking_type, stock_warehouse → stock_rule: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_route → stock_rule: **reference**, the app reads it on its own (derived)

Open questions (5):
- **extended_reference_candidate** (stock_rule): app reads stock_location with every stock_rule: copy up to 5 read fields of stock_location into stock_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_rule): app reads stock_location with every stock_rule: copy up to 5 read fields of stock_location into stock_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_rule): app reads stock_picking_type with every stock_rule: copy up to 5 read fields of stock_picking_type into stock_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_rule): app reads stock_route with every stock_rule: copy up to 5 read fields of stock_route into stock_rule documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_rule): app reads stock_warehouse with every stock_rule: copy up to 5 read fields of stock_warehouse into stock_rule documents (extended reference) or keep the $lookup

## stockScrapReasonTag

From `stock_scrap_reason_tag`.

Why:
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)

## stockStorageCategory

From `stock_storage_category`.

Why:
- stock_storage_category → stock_location: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_storage_category → stock_putaway_rule, stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockStorageCategoryCapacity

From `stock_storage_category_capacity`.

Why:
- stock_package_type, product_product, stock_storage_category → stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (5):
- **extended_reference_candidate** (stock_storage_category_capacity): app reads stock_package_type with every stock_storage_category_capacity: copy up to 5 read fields of stock_package_type into stock_storage_category_capacity documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_storage_category_capacity): app reads product_product with every stock_storage_category_capacity: copy up to 5 read fields of product_product into stock_storage_category_capacity documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_storage_category_capacity): app reads stock_storage_category with every stock_storage_category_capacity: copy up to 5 read fields of stock_storage_category into stock_storage_category_capacity documents (extended reference) or keep the $lookup
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockWarehouseOrderpoint

From `stock_warehouse_orderpoint`.

Why:
- stock_warehouse_orderpoint → purchase_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_warehouse_orderpoint → stock_move: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_location, uom_uom, stock_route, product_supplierinfo, stock_warehouse → stock_warehouse_orderpoint: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_product → stock_warehouse_orderpoint: **reference**, the app reads it on its own (derived)

Open questions (6):
- **extended_reference_candidate** (stock_warehouse_orderpoint): app reads stock_location with every stock_warehouse_orderpoint: copy up to 5 read fields of stock_location into stock_warehouse_orderpoint documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse_orderpoint): app reads product_product with every stock_warehouse_orderpoint: copy up to 5 read fields of product_product into stock_warehouse_orderpoint documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse_orderpoint): app reads uom_uom with every stock_warehouse_orderpoint: copy up to 5 read fields of uom_uom into stock_warehouse_orderpoint documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse_orderpoint): app reads stock_route with every stock_warehouse_orderpoint: copy up to 5 read fields of stock_route into stock_warehouse_orderpoint documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse_orderpoint): app reads product_supplierinfo with every stock_warehouse_orderpoint: copy up to 5 read fields of product_supplierinfo into stock_warehouse_orderpoint documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (stock_warehouse_orderpoint): app reads stock_warehouse with every stock_warehouse_orderpoint: copy up to 5 read fields of stock_warehouse into stock_warehouse_orderpoint documents (extended reference) or keep the $lookup

## uomUom

From `uom_uom`.

Why:
- uom_uom → account_move_line, product_supplierinfo, product_template, stock_move, stock_move_line, uom_uom: **reference**, other tables also point at it, so it keeps its own collection (derived)
- uom_uom → product_pricelist_item, product_uom, purchase_order_line, sale_order_line, stock_warehouse_orderpoint: **reference**, it is embedded under another parent; this one is referenced (derived)
- uom_uom → product_product_uom_uom_rel, product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_package_type → uom_uom: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (4):
- **extended_reference_candidate** (uom_uom): app reads stock_package_type with every uom_uom: copy up to 5 read fields of stock_package_type into uom_uom documents (extended reference) or keep the $lookup
- **extended_reference_candidate** (uom_uom): app reads uom_uom with every uom_uom: copy up to 5 read fields of uom_uom into uom_uom documents (extended reference) or keep the $lookup
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (uom_uom): source index not exercised by any confirmed access pattern; keep or drop
