# Model review: map-draft-2

## Your data in MongoDB

370 source tables become 224 collections: 150 hold one table each, and 74 also carry 146 smaller tables embedded inside their documents (145 as arrays, 1 as one subdocument; 103 of the arrays are link tables). The most common reason a table keeps its own collection: other tables also point at it, so it keeps its own collection (982 of 1047 references). The most common reason a table is embedded: a link table, kept as an array on this side (103 of 146 embeds). 151 tables stay on the source and are not migrated: account_account_account_merge_wizard_rel, account_accrued_orders_wizard, account_automatic_entry_wizard, account_automatic_entry_wizard_account_move_line_rel, account_autopost_bills_wizard, account_financial_year_op, account_merge_wizard, account_merge_wizard_line and 143 more.

### Examples

**Root document**: `ormSignalingAssets` is one `orm_signaling_assets` row per document.

```json
{
  "_id": 1,
  "date": {
    "$date": "2026-10-20T00:00:00Z"
  }
}
```

**Embedded child array**: each `accountFiscalPosition` document carries its `account_fiscal_position_account` rows in `account`.

```json
{
  "_id": 1,
  "sequence": 10,
  "companyId": 1,
  "countryId": 233,
  "createUid": 1,
  "writeUid": 1,
  "name": {
    "en_US": "Domestic"
  },
  "active": true,
  "autoApply": true,
  "isDomestic": true,
  "createDate": {
    "$date": "2026-10-20T00:00:00Z"
  },
  "writeDate": {
    "$date": "2026-10-20T00:00:00Z"
  },
  "account": [
    {
      "accountSrcId": 1,
      "accountDestId": 2,
      "id": 1,
      "companyId": 1,
      "createUid": 1,
      "writeUid": 1,
      "createDate": {
        "$date": "2026-10-20T00:00:00Z"
      },
      "writeDate": {
        "$date": "2026-10-20T00:00:00Z"
      }
    }
  ],
  "accountTaxRel": [
    {
      "accountTaxId": 1
    },
    {
      "accountTaxId": 2
    }
  ],
  "resCountryStateRel": [
    {
      "resCountryStateId": 9
    },
    {
      "resCountryStateId": 10
    }
  ]
}
```

**Link-table array**: `accountAccount` keeps its `account_account_account_tag` links as the `accountTag` array.

```json
{
  "_id": 185,
  "createUid": 1,
  "writeUid": 1,
  "accountType": "liability_payable",
  "parentPath": "185/",
  "name": {
    "en_US": "Object-based bifurcated alliance"
  },
  "codeStore": {
    "1": "POP000001"
  },
  "active": true,
  "reconcile": true,
  "nonTrade": false,
  "createDate": {
    "$date": "2026-10-20T00:00:00Z"
  },
  "writeDate": {
    "$date": "2026-10-20T00:00:00Z"
  },
  "accountTag": [
    {
      "accountAccountTagId": 11
    },
    {
      "accountAccountTagId": 9
    }
  ],
  "resCompanyRel": [
    {
      "resCompanyId": 1
    }
  ],
  "taxDefaultRel": []
}
```

**Reference**: `accountAccount.createUid` holds the key of a `resUsers` document; it is looked up, not copied.

```json
{
  "_id": 185,
  "createUid": 1,
  "writeUid": 1,
  "accountType": "liability_payable",
  "parentPath": "185/",
  "name": {
    "en_US": "Object-based bifurcated alliance"
  },
  "codeStore": {
    "1": "POP000001"
  },
  "active": true,
  "reconcile": true,
  "nonTrade": false,
  "createDate": {
    "$date": "2026-10-20T00:00:00Z"
  },
  "writeDate": {
    "$date": "2026-10-20T00:00:00Z"
  },
  "accountTag": [
    {
      "accountAccountTagId": 11
    },
    {
      "accountAccountTagId": 9
    }
  ],
  "resCompanyRel": [
    {
      "resCompanyId": 1
    }
  ],
  "taxDefaultRel": []
}
```

### Known limits

- 1220 of 1392 relationship choices follow the schema alone (assumed), not measured data or app code.
- 117 embedded arrays have no measured size bound (cardinality assumed).
- 0 questions are still open; they are listed below.
- Examples are from the local rehearsal load (fixture data), not production.

## Review

- **Draft:** 224 collections, 146 embedded tables, 151 tables excluded.
- **Evidence:** of 1392 relationship choices, 172 rest on measured data or app code and 0 on a recorded decision (`derived`); the rest follow the schema alone (`assumed`).
- **Decisions:** 0 kinds of question, 0 items. The draft already applies each proposal; answer each group with one line in `.migration/answers.txt` (template below).


**Answers template.** Copy it to `.migration/answers.txt` and replace each `<...>` with who decided and why. `accept` keeps the embeds and copied fields a rule proposed (from the schema alone), `reject` makes its embeds references, `except` exempts tables, `close` settles every question of a kind. Delete lines you are not ready to answer.

```
accept junction_array: <who said so, and why>  # 103 tables: account_account_account_tag, account_account_res_company_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tax_default_rel, account_analytic_line_stock_move_rel, account_bank_statement_ir_attachment_rel, account_cash_rounding_account_payment_method_line_rel, account_cash_rounding_res_currency_rel and 95 more
accept ownership: <who said so, and why>  # 14 tables: auth_totp_device, discuss_channel_last_interest_update, discuss_voice_metadata, iap_service_pack, ir_cron_progress, ir_exports_line, ir_module_module_exclusion, mail_message_schedule and 6 more
```

## accountAccount

From `account_account` with `account_account_account_tag`, `account_account_res_company_rel`, `account_account_tax_default_rel` embedded.

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
  accountTag: [{  // account_account_account_tag, 1:N assumed
    accountAccountTagId: int,  // account_account_tag_id
  }],
  resCompanyRel: [{  // account_account_res_company_rel, 1:N assumed
    resCompanyId: int,  // res_company_id
  }],
  taxDefaultRel: [{  // account_account_tax_default_rel, 1:N assumed
    taxId: int,  // tax_id
  }],
}
```

Why:
- account_account → account_account, account_analytic_line, account_journal, account_payment, account_payment_method_line, account_reconcile_model_line, account_tax, res_company, stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, res_currency → account_account: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account → account_account_account_tag, account_account_res_company_rel, account_account_tax_default_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_account_tag → account_account_account_tag: **reference**, a link table, embedded on the other side (assumed)
- res_company → account_account_res_company_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax → account_account_tax_default_rel: **reference**, a link table, embedded on the other side (assumed)
- account_account → account_fiscal_position_account, account_move_line, account_tax_repartition_line: **reference**, it is embedded under another parent; this one is referenced (derived)

## accountAccountTag

From `account_account_tag` with `account_account_tag_account_tax_repartition_line_rel` embedded.

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
  accountTaxRepartitionLineRel: [{  // account_account_tag_account_tax_repartition_line_rel, 1:N assumed
    accountTaxRepartitionLineId: int,  // account_tax_repartition_line_id
  }],
}
```

Why:
- account_account_tag → account_account_account_tag: **reference**, a link table, embedded on the other side (assumed)
- res_country, res_users → account_account_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account_tag → account_account_tag_account_move_line_rel, account_account_tag_product_template_rel: **reference**, a link table, kept as an array on this side (derived)
- account_tax_repartition_line → account_account_tag_account_tax_repartition_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_account_tag → account_account_tag_account_tax_repartition_line_rel: **embed**, a link table, kept as an array on this side (assumed)

## accountAnalyticLine

From `account_analytic_line` with `account_analytic_line_stock_move_rel` embedded.

```js
{
  _id: int,  // id
  accountId: int,  // account_id
  productUomId: int,  // product_uom_id
  partnerId: int,  // partner_id
  userId: int,  // user_id
  companyId: int,  // company_id
  currencyId: int,  // currency_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  category: string,  // category
  date: date,  // date
  amount: decimal,  // amount
  createDate: date,  // create_date
  writeDate: date,  // write_date
  unitAmount: double,  // unit_amount
  xPlan1Id: int,  // x_plan1_id
  xPlan2Id: int,  // x_plan2_id
  xPlan3Id: int,  // x_plan3_id
  productId: int,  // product_id
  generalAccountId: int,  // general_account_id
  journalId: int,  // journal_id
  moveLineId: int,  // move_line_id
  code: string,  // code
  ref: string,  // ref
  reinvoiceMoveId: int,  // reinvoice_move_id
  soLine: int,  // so_line
  orderId: int,  // order_id
  xPlan4Id: int,  // x_plan4_id
  stockMoveRel: [{  // account_analytic_line_stock_move_rel, 1:N assumed
    stockMoveId: int,  // stock_move_id
  }],
}
```

Why:
- account_analytic_account, res_company, res_users, res_currency, account_account, account_journal, account_move_line, sale_order, res_partner, product_product, uom_uom, account_move, sale_order_line → account_analytic_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_analytic_line → account_analytic_line_stock_move_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_move → account_analytic_line_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)

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
  irAttachmentRel: [{  // account_bank_statement_ir_attachment_rel, 1:N assumed
    irAttachmentId: int,  // ir_attachment_id
  }],
}
```

Why:
- res_company, res_users, res_currency, account_journal → account_bank_statement: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement → account_bank_statement_ir_attachment_rel: **embed**, a link table, kept as an array on this side (assumed)
- ir_attachment → account_bank_statement_ir_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- account_bank_statement → account_bank_statement_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)

## accountCashRounding

From `account_cash_rounding` with `account_cash_rounding_account_payment_method_line_rel`, `account_cash_rounding_res_currency_rel`, `account_cash_rounding_res_partner_category_rel` embedded.

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
  accountPaymentMethodLineRel: [{  // account_cash_rounding_account_payment_method_line_rel, 1:N assumed
    accountPaymentMethodLineId: int,  // account_payment_method_line_id
  }],
  resCurrencyRel: [{  // account_cash_rounding_res_currency_rel, 1:N assumed
    resCurrencyId: int,  // res_currency_id
  }],
  resPartnerCategoryRel: [{  // account_cash_rounding_res_partner_category_rel, 1:N assumed
    resPartnerCategoryId: int,  // res_partner_category_id
  }],
}
```

Why:
- res_company, res_users → account_cash_rounding: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment_method_line → account_cash_rounding_account_payment_method_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_cash_rounding → account_cash_rounding_account_payment_method_line_rel, account_cash_rounding_res_currency_rel, account_cash_rounding_res_partner_category_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_currency → account_cash_rounding_res_currency_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner_category → account_cash_rounding_res_partner_category_rel: **reference**, a link table, embedded on the other side (assumed)
- account_cash_rounding → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountFiscalPosition

From `account_fiscal_position` with `account_fiscal_position_account`, `account_fiscal_position_account_tax_rel`, `account_fiscal_position_res_country_state_rel` embedded.

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
  accountTaxRel: [{  // account_fiscal_position_account_tax_rel, 1:N assumed
    accountTaxId: int,  // account_tax_id
  }],
  resCountryStateRel: [{  // account_fiscal_position_res_country_state_rel, 1:N assumed
    resCountryStateId: int,  // res_country_state_id
  }],
}
```

Why:
- res_company, res_country_group, res_country, res_users → account_fiscal_position: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account, res_company, res_users → account_fiscal_position_account: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_fiscal_position → account_fiscal_position_account: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_fiscal_position → account_fiscal_position_account_tax_rel, account_fiscal_position_res_country_state_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_fiscal_position_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country_state → account_fiscal_position_res_country_state_rel: **reference**, a link table, embedded on the other side (assumed)
- account_fiscal_position → account_move, purchase_order, res_company, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

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
- account_journal → account_analytic_line, account_bank_statement, account_bank_statement_line, account_move, account_payment, account_payment_method_line, res_company, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_alias, res_partner_bank, res_company, res_users, res_currency, account_account, ir_act_report_xml, account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_journal → account_journal_account_reconcile_model_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_journal → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)

## accountMove

From `account_move` with `account_invoice_transaction_rel`, `account_move__account_payment`, `account_move_purchase_order_rel`, `adjusting_entries__account_move` embedded.

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
  accountInvoiceTransactionRel: [{  // account_invoice_transaction_rel, 1:N assumed
    transactionId: int,  // transaction_id
  }],
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
- account_move → account_analytic_line, account_bank_statement_line, account_move, account_partial_reconcile, account_payment, product_value, res_company, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move → account_invoice_transaction_rel, account_move__account_payment, account_move_purchase_order_rel, adjusting_entries__account_move: **embed**, a link table, kept as an array on this side (assumed)
- payment_transaction → account_invoice_transaction_rel: **reference**, a link table, embedded on the other side (assumed)
- utm_campaign, res_partner, res_company, res_users, res_currency, account_fiscal_position, ir_attachment, account_cash_rounding, account_incoterms, account_payment_term, account_journal, utm_medium, account_payment, res_partner_bank, account_payment_method_line, utm_source, account_bank_statement_line, account_partial_reconcile, crm_team → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- account_move → account_move_line: **reference**, the app reads it on its own (derived)
- purchase_order → account_move_purchase_order_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move → adjusting_entries__account_move, purchase_order_line_accrual_move_rel, sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)

## accountMoveLine

From `account_move_line` with `account_move_line_account_tax_rel`, `account_account_tag_account_move_line_rel` embedded.

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
  accountTaxRel: [{  // account_move_line_account_tax_rel, 1:N assumed
    accountTaxId: int,  // account_tax_id
  }],
  taxTagIds: [{  // account_account_tag_account_move_line_rel, 1:few derived
    accountAccountTagId: int,  // account_account_tag_id
  }],
}
```

Why:
- account_account_tag → account_account_tag_account_move_line_rel: **reference**, a link table, kept as an array on this side (derived)
- account_move_line → account_account_tag_account_move_line_rel: **embed**, a link table, embedded on the other side (derived)
- account_move_line → account_analytic_line, account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account, res_currency, res_company, res_users, account_full_reconcile, account_tax, account_journal, res_partner, account_payment, product_product, uom_uom, purchase_order_line, account_reconcile_model, account_bank_statement, account_bank_statement_line, stock_move, account_tax_group, account_tax_repartition_line → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_move_line → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_move → account_move_line: **reference**, the app reads it on its own (derived)
- account_move_line → account_move_line_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_move_line_account_tax_rel: **reference**, too many children per parent (measured) (derived)
- account_move_line → sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)

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
- account_payment → account_move, account_payment, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- account_payment → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_partner, res_company, res_users, res_currency, account_account, account_journal, ir_attachment, account_move, res_partner_bank, account_payment_method, account_payment_method_line, payment_token, payment_transaction → account_payment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment → account_payment_account_bank_statement_line_rel: **embed**, a link table, kept as an array on this side (assumed)

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
- res_company, res_users → account_payment_term: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_payment_term_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_payment_term → account_payment_term_line: **embed**, the app reads it with its parent (derived)

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
  resPartnerRel: [{  // account_reconcile_model_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
}
```

Why:
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_reconcile_model → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_company, res_users, res_partner, mail_activity_type → account_reconcile_model: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model → account_reconcile_model_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model → account_reconcile_model_res_partner_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → account_reconcile_model_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)

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
- account_account, res_company, res_users, account_reconcile_model, res_partner → account_reconcile_model_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model_line → account_reconcile_model_line_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_reconcile_model_line_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)

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
- res_country, res_users → account_report: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report → account_report, account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_act_window → account_report_column: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_report → account_report_column: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_report → account_report_section_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_report → account_report_section_rel: **reference**, a link table, embedded on the other side (assumed)

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
- res_users, account_report_line → account_report_expression: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report_line, res_company, res_users → account_report_external_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_report_expression → account_report_external_value: **embed**, owned by its parent (cascade delete or ordinal key) (derived)

## accountTax

From `account_tax` with `account_tax_alternatives`, `account_tax_filiation_rel`, `account_tax_repartition_line` embedded.

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
  repartitionLine: [{  // account_tax_repartition_line, 1:N derived
    id: int,  // id
    accountId: int,  // account_id
    companyId: int,  // company_id
    sequence: int,  // sequence
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    repartitionType: string,  // repartition_type
    documentType: string,  // document_type
    factorPercent: decimal,  // factor_percent
    useInTaxClosing: bool,  // use_in_tax_closing
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- account_tax → account_account_tax_default_rel, account_fiscal_position_account_tax_rel, account_reconcile_model_line_account_tax_rel, account_tax_alternatives, account_tax_filiation_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_tax → account_move_line_account_tax_rel: **reference**, too many children per parent (measured) (derived)
- account_account, res_company, res_country, res_users, res_city, l10n_us_res_county, res_country_state, account_tax_group → account_tax: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_tax → account_tax, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_tax → account_tax_alternatives, account_tax_filiation_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_tax_purchase_order_line_rel, account_tax_sale_order_line_rel, product_supplier_taxes_rel, product_taxes_rel: **reference**, a link table, kept as an array on this side (derived)
- account_account, res_company, res_users → account_tax_repartition_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_tax → account_tax_repartition_line: **embed**, the app reads it with its parent (derived)

## crmTeam

From `crm_team` with `team_favorite_user_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  companyId: int,  // company_id
  userId: int,  // user_id
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  teamFavoriteUserRel: [{  // team_favorite_user_rel, 1:N assumed
    userId: int,  // user_id
  }],
}
```

Why:
- crm_team → account_move, crm_team_member, res_users, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users → crm_team: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_team → team_favorite_user_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → team_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)

## digestDigest

From `digest_digest` with `digest_digest_res_users_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  periodicity: string,  // periodicity
  state: string,  // state
  nextRunDate: date,  // next_run_date
  name: object,  // name
  kpiResUsersConnected: bool,  // kpi_res_users_connected
  kpiMailMessageTotal: bool,  // kpi_mail_message_total
  createDate: date,  // create_date
  writeDate: date,  // write_date
  kpiAccountTotalRevenue: bool,  // kpi_account_total_revenue
  kpiStockDeliveryCount: bool,  // kpi_stock_delivery_count
  kpiStockReceiptCount: bool,  // kpi_stock_receipt_count
  resUsersRel: [{  // digest_digest_res_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- res_company, res_users → digest_digest: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- digest_digest → digest_digest_res_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → digest_digest_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

## digestTip

From `digest_tip` with `digest_tip_res_users_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  groupId: int,  // group_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  tipDescription: object,  // tip_description
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resUsersRel: [{  // digest_tip_res_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- res_users, res_groups → digest_tip: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- digest_tip → digest_tip_res_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → digest_tip_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

## discussCallHistory

From `discuss_call_history` with `mail_call_artifact` embedded.

```js
{
  _id: int,  // id
  channelId: int,  // channel_id
  startCallMessageId: int,  // start_call_message_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  startDt: date,  // start_dt
  endDt: date,  // end_dt
  createDate: date,  // create_date
  writeDate: date,  // write_date
  mailCallArtifact: [{  // mail_call_artifact, 1:N derived
    id: int,  // id
    recordingStartedById: int,  // recording_started_by_id
    startMs: int,  // start_ms
    endMs: int,  // end_ms
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    recordingUploadPending: bool,  // recording_upload_pending
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- discuss_channel, res_users, mail_message → discuss_call_history: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → mail_call_artifact: **reference**, it is embedded under another parent; this one is referenced (derived)
- discuss_call_history → mail_call_artifact: **embed**, owned by its parent (cascade delete or ordinal key) (derived)

## discussChannel

From `discuss_channel` with `discuss_channel_last_interest_update`, `discuss_channel_res_groups_rel` embedded.

```js
{
  _id: int,  // id
  discussCategoryId: int,  // discuss_category_id
  parentChannelId: int,  // parent_channel_id
  fromMessageId: int,  // from_message_id
  groupPublicId: int,  // group_public_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  channelType: string,  // channel_type
  defaultDisplayMode: string,  // default_display_mode
  memberIndices: string,  // member_indices
  sfuChannelUuid: string,  // sfu_channel_uuid
  sfuServerUrl: string,  // sfu_server_url
  uuid: string,  // uuid
  description: string,  // description
  active: bool,  // active
  isReadonly: bool,  // is_readonly
  lastInterestDt: date,  // last_interest_dt
  createDate: date,  // create_date
  writeDate: date,  // write_date
  lastInterestUpdate: [{  // discuss_channel_last_interest_update, 1:N assumed
    id: int,  // id
    lastInterestDt: date,  // last_interest_dt
  }],
  resGroupsRel: [{  // discuss_channel_res_groups_rel, 1:N assumed
    resGroupsId: int,  // res_groups_id
  }],
}
```

Why:
- discuss_channel → discuss_call_history, discuss_channel, discuss_channel_member, discuss_channel_rtc_session: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, discuss_category, mail_message, res_groups → discuss_channel: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_channel → discuss_channel_last_interest_update: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- discuss_channel → discuss_channel_res_groups_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → discuss_channel_res_groups_rel: **reference**, a link table, embedded on the other side (assumed)

## iapAccount

From `iap_account` with `iap_account_res_company_rel`, `iap_account_res_users_rel` embedded.

```js
{
  _id: int,  // id
  serviceId: int,  // service_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  accountToken: string,  // account_token
  state: string,  // state
  serviceLocked: bool,  // service_locked
  createDate: date,  // create_date
  writeDate: date,  // write_date
  balanceAmount: double,  // balance_amount
  warningThreshold: double,  // warning_threshold
  senderName: string,  // sender_name
  resCompanyRel: [{  // iap_account_res_company_rel, 1:N assumed
    resCompanyId: int,  // res_company_id
  }],
  resUsersRel: [{  // iap_account_res_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- res_users, iap_service → iap_account: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- iap_account → iap_account_res_company_rel, iap_account_res_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_company → iap_account_res_company_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → iap_account_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

## iapService

From `iap_service` with `iap_service_pack` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  technicalName: string,  // technical_name
  name: object,  // name
  description: object,  // description
  unitName: object,  // unit_name
  priceDescription: object,  // price_description
  integerBalance: bool,  // integer_balance
  createDate: date,  // create_date
  writeDate: date,  // write_date
  pack: [{  // iap_service_pack, 1:N assumed
    id: int,  // id
    iapServicePackIdentifier: int,  // iap_service_pack_identifier
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    name: string,  // name
    createDate: date,  // create_date
    writeDate: date,  // write_date
    credit: double,  // credit
    price: double,  // price
  }],
}
```

Why:
- iap_service → iap_account: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → iap_service: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → iap_service_pack: **reference**, it is embedded under another parent; this one is referenced (derived)
- iap_service → iap_service_pack: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

## irActServer

From `ir_act_server` with `ir_actions_server_history`, `ir_act_server_group_rel`, `ir_act_server_mail_message_subtype_rel`, `ir_act_server_res_partner_rel`, `ir_act_server_webhook_field_rel` embedded.

```js
{
  _id: int,  // id
  bindingModelId: int,  // binding_model_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  type: string,  // type
  path: string,  // path
  bindingType: string,  // binding_type
  bindingViewTypes: string,  // binding_view_types
  name: object,  // name
  help: object,  // help
  explanation: string,  // explanation
  createDate: date,  // create_date
  writeDate: date,  // write_date
  sequence: int,  // sequence
  modelId: int,  // model_id
  parentId: int,  // parent_id
  crudModelId: int,  // crud_model_id
  linkFieldId: int,  // link_field_id
  updateFieldId: int,  // update_field_id
  updateRelatedModelId: int,  // update_related_model_id
  sequenceId: int,  // sequence_id
  selectionValue: int,  // selection_value
  automatedName: string,  // automated_name
  usage: string,  // usage
  state: string,  // state
  updateProperty: string,  // update_property
  updatePath: string,  // update_path
  updateM2mOperation: string,  // update_m2m_operation
  updateBooleanValue: string,  // update_boolean_value
  evaluationType: string,  // evaluation_type
  resourceRef: string,  // resource_ref
  propertySelection: string,  // property_selection
  webhookUrl: string,  // webhook_url
  code: string,  // code
  value: string,  // value
  htmlValue: string,  // html_value
  activityUserId: int,  // activity_user_id
  activityTypeId: int,  // activity_type_id
  templateId: int,  // template_id
  activityPlanId: int,  // activity_plan_id
  activityDateDeadlineRange: int,  // activity_date_deadline_range
  activityRoleId: int,  // activity_role_id
  activitySummary: string,  // activity_summary
  followersType: string,  // followers_type
  followersPartnerFieldName: string,  // followers_partner_field_name
  activityDateDeadlineRangeType: string,  // activity_date_deadline_range_type
  activityUserType: string,  // activity_user_type
  activityUserFieldName: string,  // activity_user_field_name
  logNoteNote: object,  // log_note_note
  activityNote: string,  // activity_note
  mailPostAutofollow: bool,  // mail_post_autofollow
  smsTemplateId: int,  // sms_template_id
  irActionsServerHistory: [{  // ir_actions_server_history, 1:N derived
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    code: string,  // code
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  groupRel: [{  // ir_act_server_group_rel, 1:N assumed
    gid: int,  // gid
  }],
  mailMessageSubtypeRel: [{  // ir_act_server_mail_message_subtype_rel, 1:N assumed
    mailMessageSubtypeId: int,  // mail_message_subtype_id
  }],
  resPartnerRel: [{  // ir_act_server_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
  webhookFieldRel: [{  // ir_act_server_webhook_field_rel, 1:N assumed
    fieldId: int,  // field_id
  }],
}
```

Why:
- mail_activity_plan, res_role, mail_activity_type, res_users, ir_model, ir_model_fields, ir_model_fields_selection, ir_sequence, sms_template, mail_template → ir_act_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_server → ir_act_server, ir_cron: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_server → ir_act_server_group_rel, ir_act_server_mail_message_subtype_rel, ir_act_server_res_partner_rel, ir_act_server_webhook_field_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → ir_act_server_group_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_message_subtype → ir_act_server_mail_message_subtype_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → ir_act_server_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_model_fields → ir_act_server_webhook_field_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_act_server → ir_actions_server_history: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → ir_actions_server_history: **reference**, it is embedded under another parent; this one is referenced (derived)

## irActWindow

From `ir_act_window` with `ir_act_window_view`, `ir_act_window_group_rel` embedded.

```js
{
  _id: int,  // id
  bindingModelId: int,  // binding_model_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  type: string,  // type
  path: string,  // path
  bindingType: string,  // binding_type
  bindingViewTypes: string,  // binding_view_types
  name: object,  // name
  help: object,  // help
  explanation: string,  // explanation
  createDate: date,  // create_date
  writeDate: date,  // write_date
  viewId: int,  // view_id
  resId: int,  // res_id
  limit: int,  // limit
  searchViewId: int,  // search_view_id
  domain: string,  // domain
  context: string,  // context
  resModel: string,  // res_model
  target: string,  // target
  viewMode: string,  // view_mode
  mobileViewMode: string,  // mobile_view_mode
  usage: string,  // usage
  filter: bool,  // filter
  cache: bool,  // cache
  view: [{  // ir_act_window_view, 1:N derived
    id: int,  // id
    sequence: int,  // sequence
    viewId: int,  // view_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    viewMode: string,  // view_mode
    multi: bool,  // multi
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  groupRel: [{  // ir_act_window_group_rel, 1:N assumed
    gid: int,  // gid
  }],
}
```

Why:
- ir_act_window → account_report_column: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_model, res_users, ir_ui_view → ir_act_window: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_window → ir_act_window_group_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → ir_act_window_group_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_act_window → ir_act_window_view: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users, ir_ui_view → ir_act_window_view: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_act_window → ir_embedded_actions, mail_template, res_users_settings_embedded_action, sms_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irAttachment

From `ir_attachment` with `discuss_voice_metadata`, `product_document`, `activity_attachment_rel`, `email_template_attachment_rel`, `message_attachment_rel`, `scheduled_message_attachment_rel` embedded.

```js
{
  _id: int,  // id
  resId: int,  // res_id
  companyId: int,  // company_id
  fileSize: int,  // file_size
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  resModel: string,  // res_model
  resField: string,  // res_field
  type: string,  // type
  url: string,  // url
  accessToken: string,  // access_token
  storeFname: string,  // store_fname
  checksum: string,  // checksum
  mimetype: string,  // mimetype
  description: string,  // description
  indexContent: string,  // index_content
  public: bool,  // public
  createDate: date,  // create_date
  writeDate: date,  // write_date
  dbDatas: binData,  // db_datas
  originalId: int,  // original_id
  discussVoiceMetadata: [{  // discuss_voice_metadata, 1:N assumed
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  productDocument: [{  // product_document, 1:N derived
    id: int,  // id
    sequence: int,  // sequence
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    active: bool,  // active
    createDate: date,  // create_date
    writeDate: date,  // write_date
    attachedOnSale: string,  // attached_on_sale
  }],
  activityAttachmentRel: [{  // activity_attachment_rel, 1:N assumed
    activityId: int,  // activity_id
  }],
  emailTemplateAttachmentRel: [{  // email_template_attachment_rel, 1:N assumed
    emailTemplateId: int,  // email_template_id
  }],
  messageAttachmentRel: [{  // message_attachment_rel, 1:N assumed
    messageId: int,  // message_id
  }],
  scheduledMessageAttachmentRel: [{  // scheduled_message_attachment_rel, 1:N assumed
    scheduledMessageId: int,  // scheduled_message_id
  }],
}
```

Why:
- ir_attachment → account_bank_statement_ir_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_attachment → account_move, account_payment, ir_attachment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_activity → activity_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_attachment → activity_attachment_rel, email_template_attachment_rel, message_attachment_rel, scheduled_message_attachment_rel: **embed**, a link table, kept as an array on this side (assumed)
- ir_attachment → discuss_voice_metadata: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → discuss_voice_metadata: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_template → email_template_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users → ir_attachment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_message → message_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → product_document: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_attachment → product_document: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- mail_scheduled_message → scheduled_message_attachment_rel: **reference**, a link table, embedded on the other side (assumed)

## irCron

From `ir_cron` with `ir_cron_progress`, `ir_cron_trigger` embedded.

```js
{
  _id: int,  // id
  irActionsServerId: int,  // ir_actions_server_id
  userId: int,  // user_id
  intervalNumber: int,  // interval_number
  priority: int,  // priority
  failureCount: int,  // failure_count
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  cronName: string,  // cron_name
  intervalType: string,  // interval_type
  active: bool,  // active
  nextcall: date,  // nextcall
  lastcall: date,  // lastcall
  firstFailureDate: date,  // first_failure_date
  createDate: date,  // create_date
  writeDate: date,  // write_date
  progress: [{  // ir_cron_progress, 1:N assumed
    id: int,  // id
    remaining: int,  // remaining
    done: int,  // done
    timedOutCounter: int,  // timed_out_counter
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    deactivate: bool,  // deactivate
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  trigger: [{  // ir_cron_trigger, 1:N derived
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    callAt: date,  // call_at
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- res_users, ir_act_server → ir_cron: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → ir_cron_progress: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_cron → ir_cron_progress: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → ir_cron_trigger: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_cron → ir_cron_trigger: **embed**, owned by its parent (cascade delete or ordinal key) (derived)

## irEmbeddedActions

From `ir_embedded_actions` with `ir_embedded_actions_res_groups_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  parentActionId: int,  // parent_action_id
  parentResId: int,  // parent_res_id
  actionId: int,  // action_id
  userId: int,  // user_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  parentResModel: string,  // parent_res_model
  pythonMethod: string,  // python_method
  defaultViewMode: string,  // default_view_mode
  domain: string,  // domain
  context: string,  // context
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resGroupsRel: [{  // ir_embedded_actions_res_groups_rel, 1:N assumed
    resGroupsId: int,  // res_groups_id
  }],
}
```

Why:
- res_users, ir_act_window → ir_embedded_actions: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_embedded_actions → ir_embedded_actions_res_groups_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → ir_embedded_actions_res_groups_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_embedded_actions → ir_filters: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irExports

From `ir_exports` with `ir_exports_line`, `ir_exports_res_lang_rel` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  resource: string,  // resource
  createDate: date,  // create_date
  writeDate: date,  // write_date
  line: [{  // ir_exports_line, 1:N assumed
    id: int,  // id
    sequence: int,  // sequence
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    name: string,  // name
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  resLangRel: [{  // ir_exports_res_lang_rel, 1:N assumed
    resLangId: int,  // res_lang_id
  }],
}
```

Why:
- res_users → ir_exports: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → ir_exports_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_exports → ir_exports_line: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- ir_exports → ir_exports_res_lang_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_lang → ir_exports_res_lang_rel: **reference**, a link table, embedded on the other side (assumed)

## irFilters

From `ir_filters` with `ir_filters_res_users_rel` embedded.

```js
{
  _id: int,  // id
  actionId: int,  // action_id
  embeddedActionId: int,  // embedded_action_id
  embeddedParentResId: int,  // embedded_parent_res_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  sort: string,  // sort
  modelId: string,  // model_id
  domain: string,  // domain
  context: string,  // context
  isDefault: bool,  // is_default
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resUsersRel: [{  // ir_filters_res_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- res_users, ir_embedded_actions → ir_filters: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_filters → ir_filters_res_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → ir_filters_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

## irModel

From `ir_model` with `ir_model_spreadsheet_dashboard_rel` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  model: string,  // model
  order: string,  // order
  state: string,  // state
  foldName: string,  // fold_name
  name: object,  // name
  info: string,  // info
  explanation: string,  // explanation
  abstract: bool,  // abstract
  transient: bool,  // transient
  createDate: date,  // create_date
  writeDate: date,  // write_date
  isMailThread: bool,  // is_mail_thread
  isMailActivity: bool,  // is_mail_activity
  isMailBlacklist: bool,  // is_mail_blacklist
  spreadsheetDashboardRel: [{  // ir_model_spreadsheet_dashboard_rel, 1:N assumed
    spreadsheetDashboardId: int,  // spreadsheet_dashboard_id
  }],
}
```

Why:
- ir_model → fetchmail_server, ir_access, ir_act_report_xml, ir_act_server, ir_act_window, ir_model_constraint, ir_model_fields, ir_model_relation, mail_activity, mail_activity_plan, mail_alias, mail_template, sms_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model → ir_act_client, ir_act_url, ir_actions: **reference**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → ir_model: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model → ir_model_inherit: **reference**, it is embedded under another parent; this one is referenced (derived)
- spreadsheet_dashboard → ir_model_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_model → ir_model_spreadsheet_dashboard_rel: **embed**, a link table, kept as an array on this side (assumed)

## irModelFields

From `ir_model_fields` with `properties_base_definition`, `ir_model_fields_group_rel` embedded.

```js
{
  _id: int,  // id
  relationFieldId: int,  // relation_field_id
  modelId: int,  // model_id
  relatedFieldId: int,  // related_field_id
  size: int,  // size
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  model: string,  // model
  relation: string,  // relation
  relationField: string,  // relation_field
  relationModelField: string,  // relation_model_field
  ttype: string,  // ttype
  related: string,  // related
  index: string,  // index
  translate: string,  // translate
  state: string,  // state
  onDelete: string,  // on_delete
  domain: string,  // domain
  relationTable: string,  // relation_table
  column1: string,  // column1
  column2: string,  // column2
  depends: string,  // depends
  currencyField: string,  // currency_field
  fieldDescription: object,  // field_description
  help: object,  // help
  compute: string,  // compute
  copied: bool,  // copied
  required: bool,  // required
  readonly: bool,  // readonly
  companyDependent: bool,  // company_dependent
  groupExpand: bool,  // group_expand
  selectable: bool,  // selectable
  store: bool,  // store
  sanitize: bool,  // sanitize
  sanitizeOverridable: bool,  // sanitize_overridable
  sanitizeTags: bool,  // sanitize_tags
  sanitizeAttributes: bool,  // sanitize_attributes
  sanitizeStyle: bool,  // sanitize_style
  sanitizeForm: bool,  // sanitize_form
  stripStyle: bool,  // strip_style
  stripClasses: bool,  // strip_classes
  createDate: date,  // create_date
  writeDate: date,  // write_date
  tracking: int,  // tracking
  propertiesBaseDefinition: {  // properties_base_definition, 1:1 derived
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    propertiesDefinition: object,  // properties_definition
    createDate: date,  // create_date
    writeDate: date,  // write_date
  },
  groupRel: [{  // ir_model_fields_group_rel, 1:N assumed
    groupId: int,  // group_id
  }],
}
```

Why:
- ir_model_fields → ir_act_server, ir_default, ir_model_fields, ir_model_fields_selection: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model_fields → ir_act_server_webhook_field_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, ir_model → ir_model_fields: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model_fields → ir_model_fields_group_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → ir_model_fields_group_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_model_fields → ir_model_inherit: **reference**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → properties_base_definition: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_model_fields → properties_base_definition: **embed**, one-to-one with its parent (derived)

## irModuleModule

From `ir_module_module` with `ir_module_module_dependency`, `ir_module_module_exclusion`, `module_country` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  createDate: date,  // create_date
  writeDate: date,  // write_date
  writeUid: int,  // write_uid
  website: string,  // website
  summary: object,  // summary
  name: string,  // name
  author: string,  // author
  icon: string,  // icon
  state: string,  // state
  latestVersion: string,  // latest_version
  shortdesc: object,  // shortdesc
  categoryId: int,  // category_id
  description: object,  // description
  application: bool,  // application
  demo: bool,  // demo
  testData: bool,  // test_data
  web: bool,  // web
  license: string,  // license
  sequence: int,  // sequence
  autoInstall: bool,  // auto_install
  toBuy: bool,  // to_buy
  maintainer: string,  // maintainer
  publishedVersion: string,  // published_version
  url: string,  // url
  contributors: string,  // contributors
  menusByModule: string,  // menus_by_module
  reportsByModule: string,  // reports_by_module
  viewsByModule: string,  // views_by_module
  iapPaidService: bool,  // iap_paid_service
  moduleType: string,  // module_type
  imported: bool,  // imported
  dependency: [{  // ir_module_module_dependency, 1:N derived
    id: int,  // id
    name: string,  // name
    autoInstallRequired: bool,  // auto_install_required
  }],
  exclusion: [{  // ir_module_module_exclusion, 1:N assumed
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    name: string,  // name
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  moduleCountry: [{  // module_country, 1:N assumed
    countryId: int,  // country_id
  }],
}
```

Why:
- ir_module_module → ir_model_constraint, ir_model_relation, payment_provider: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_module_category, res_users → ir_module_module: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_module_module → ir_module_module_dependency: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → ir_module_module_exclusion: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_module_module → ir_module_module_exclusion: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_country → module_country: **reference**, a link table, embedded on the other side (assumed)
- ir_module_module → module_country: **embed**, a link table, kept as an array on this side (assumed)

## irUiMenu

From `ir_ui_menu` with `ir_ui_menu_group_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  parentId: int,  // parent_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  parentPath: string,  // parent_path
  webIcon: string,  // web_icon
  action: string,  // action
  name: object,  // name
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  groupRel: [{  // ir_ui_menu_group_rel, 1:N assumed
    gid: int,  // gid
  }],
}
```

Why:
- res_users → ir_ui_menu: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_ui_menu → ir_ui_menu: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_groups → ir_ui_menu_group_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_ui_menu → ir_ui_menu_group_rel: **embed**, a link table, kept as an array on this side (assumed)

## irUiView

From `ir_ui_view` with `ir_ui_view_group_rel` embedded.

```js
{
  _id: int,  // id
  priority: int,  // priority
  inheritId: int,  // inherit_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  model: string,  // model
  key: string,  // key
  type: string,  // type
  archFs: string,  // arch_fs
  mode: string,  // mode
  technicalUsage: string,  // technical_usage
  archDb: object,  // arch_db
  archPrev: string,  // arch_prev
  notes: string,  // notes
  archUpdated: bool,  // arch_updated
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  customizeShow: bool,  // customize_show
  groupRel: [{  // ir_ui_view_group_rel, 1:N assumed
    groupId: int,  // group_id
  }],
}
```

Why:
- ir_ui_view → ir_act_window, ir_ui_view, ir_ui_view_custom, payment_provider, report_layout, res_company, res_country: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_ui_view → ir_act_window_view: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → ir_ui_view: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_groups → ir_ui_view_group_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_ui_view → ir_ui_view_group_rel: **embed**, a link table, kept as an array on this side (assumed)

## mailActivityType

From `mail_activity_type` with `mail_activity_rel`, `mail_activity_type_mail_template_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  delayCount: int,  // delay_count
  suggestedNextTypeId: int,  // suggested_next_type_id
  defaultUserId: int,  // default_user_id
  defaultRoleId: int,  // default_role_id
  writeUid: int,  // write_uid
  delayUnit: string,  // delay_unit
  delayFrom: string,  // delay_from
  icon: string,  // icon
  decorationType: string,  // decoration_type
  resModel: string,  // res_model
  category: string,  // category
  kpiProviderVisibility: string,  // kpi_provider_visibility
  name: object,  // name
  summary: object,  // summary
  defaultNote: object,  // default_note
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  mailActivityRel: [{  // mail_activity_rel, 1:N assumed
    recommendedId: int,  // recommended_id
  }],
  mailTemplateRel: [{  // mail_activity_type_mail_template_rel, 1:N assumed
    mailTemplateId: int,  // mail_template_id
  }],
}
```

Why:
- mail_activity_type → account_reconcile_model, ir_act_server, mail_activity, mail_activity_plan_template, mail_activity_type, mail_message: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_activity_type → mail_activity_rel, mail_activity_type_mail_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- mail_activity_type → mail_activity_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, res_role → mail_activity_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_template → mail_activity_type_mail_template_rel: **reference**, a link table, embedded on the other side (assumed)

## mailCannedResponse

From `mail_canned_response` with `mail_canned_response_res_groups_rel` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  source: string,  // source
  substitution: string,  // substitution
  isShared: bool,  // is_shared
  lastUsed: date,  // last_used
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resGroupsRel: [{  // mail_canned_response_res_groups_rel, 1:N assumed
    resGroupsId: int,  // res_groups_id
  }],
}
```

Why:
- res_users → mail_canned_response: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_canned_response → mail_canned_response_res_groups_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → mail_canned_response_res_groups_rel: **reference**, a link table, embedded on the other side (assumed)

## mailFollowers

From `mail_followers` with `mail_followers_mail_message_subtype_rel` embedded.

```js
{
  _id: int,  // id
  resId: int,  // res_id
  partnerId: int,  // partner_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  resModel: string,  // res_model
  createDate: date,  // create_date
  writeDate: date,  // write_date
  mailMessageSubtypeRel: [{  // mail_followers_mail_message_subtype_rel, 1:N assumed
    mailMessageSubtypeId: int,  // mail_message_subtype_id
  }],
}
```

Why:
- res_users, res_partner → mail_followers: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_message_subtype → mail_followers_mail_message_subtype_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_followers → mail_followers_mail_message_subtype_rel: **embed**, a link table, kept as an array on this side (assumed)

## mailMail

From `mail_mail` with `mail_mail_res_partner_cc_rel`, `mail_mail_res_partner_rel` embedded.

```js
{
  _id: int,  // id
  mailMessageId: int,  // mail_message_id
  fetchmailServerId: int,  // fetchmail_server_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  emailCc: string,  // email_cc
  state: string,  // state
  failureType: string,  // failure_type
  bodyHtml: string,  // body_html
  references: string,  // references
  headers: string,  // headers
  emailTo: string,  // email_to
  failureReason: string,  // failure_reason
  isNotification: bool,  // is_notification
  autoDelete: bool,  // auto_delete
  scheduledDate: date,  // scheduled_date
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resPartnerCcRel: [{  // mail_mail_res_partner_cc_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
  resPartnerRel: [{  // mail_mail_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
}
```

Why:
- res_users, fetchmail_server, mail_message → mail_mail: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_mail → mail_mail_res_partner_cc_rel, mail_mail_res_partner_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → mail_mail_res_partner_cc_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → mail_mail_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_mail → mail_notification: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailMessage

From `mail_message` with `mail_message_schedule`, `mail_message_translation`, `mail_message_res_partner_bookmarked_rel`, `mail_message_res_partner_cc_rel`, `mail_message_res_partner_rel` embedded.

```js
{
  _id: int,  // id
  parentId: int,  // parent_id
  resId: int,  // res_id
  recordAliasDomainId: int,  // record_alias_domain_id
  recordCompanyId: int,  // record_company_id
  subtypeId: int,  // subtype_id
  mailActivityTypeId: int,  // mail_activity_type_id
  authorId: int,  // author_id
  authorGuestId: int,  // author_guest_id
  mailServerId: int,  // mail_server_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  subject: string,  // subject
  model: string,  // model
  messageType: string,  // message_type
  emailFrom: string,  // email_from
  incomingEmailCc: string,  // incoming_email_cc
  outgoingEmailTo: string,  // outgoing_email_to
  messageId: string,  // message_id
  replyTo: string,  // reply_to
  emailLayoutXmlid: string,  // email_layout_xmlid
  body: string,  // body
  incomingEmailTo: string,  // incoming_email_to
  isInternal: bool,  // is_internal
  replyToForceNew: bool,  // reply_to_force_new
  emailAddSignature: bool,  // email_add_signature
  date: date,  // date
  pinnedAt: date,  // pinned_at
  createDate: date,  // create_date
  writeDate: date,  // write_date
  schedule: [{  // mail_message_schedule, 1:N assumed
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    notificationParameters: string,  // notification_parameters
    scheduledDatetime: date,  // scheduled_datetime
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  translation: [{  // mail_message_translation, 1:N assumed
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    sourceLang: string,  // source_lang
    targetLang: string,  // target_lang
    body: string,  // body
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  resPartnerBookmarkedRel: [{  // mail_message_res_partner_bookmarked_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
  resPartnerCcRel: [{  // mail_message_res_partner_cc_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
  resPartnerRel: [{  // mail_message_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
}
```

Why:
- mail_message → discuss_call_history, discuss_channel, discuss_channel_member, mail_mail, mail_message, mail_message_link_preview, mail_message_reaction, mail_notification, mail_poll, sms_sms: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_guest, res_partner, res_users, mail_activity_type, ir_mail_server, mail_alias_domain, res_company, mail_message_subtype → mail_message: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_message → mail_message_res_partner_bookmarked_rel, mail_message_res_partner_cc_rel, mail_message_res_partner_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → mail_message_res_partner_bookmarked_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → mail_message_res_partner_cc_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → mail_message_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → mail_message_schedule: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_message → mail_message_schedule, mail_message_translation: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → mail_message_translation: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_message → message_attachment_rel: **reference**, a link table, embedded on the other side (assumed)

## mailNotification

From `mail_notification` with `sms_tracker` embedded.

```js
{
  _id: int,  // id
  authorId: int,  // author_id
  mailMessageId: int,  // mail_message_id
  mailMailId: int,  // mail_mail_id
  resPartnerId: int,  // res_partner_id
  mailEmailAddress: string,  // mail_email_address
  notificationType: string,  // notification_type
  notificationStatus: string,  // notification_status
  failureType: string,  // failure_type
  failureReason: string,  // failure_reason
  isRead: bool,  // is_read
  readDate: date,  // read_date
  smsIdInt: int,  // sms_id_int
  smsNumber: string,  // sms_number
  smsTracker: [{  // sms_tracker, 1:N assumed
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    smsUuid: string,  // sms_uuid
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- res_partner, mail_mail, mail_message → mail_notification: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → sms_tracker: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_notification → sms_tracker: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

## mailPushDevice

From `mail_push_device` with `mail_push` embedded.

```js
{
  _id: int,  // id
  partnerId: int,  // partner_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  endpoint: string,  // endpoint
  keys: string,  // keys
  expirationTime: date,  // expiration_time
  createDate: date,  // create_date
  writeDate: date,  // write_date
  mailPush: [{  // mail_push, 1:N assumed
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    payload: string,  // payload
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- res_users → mail_push: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_push_device → mail_push: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users, res_partner → mail_push_device: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailScheduledMessage

From `mail_scheduled_message` with `mail_scheduled_message_res_partner_cc_rel`, `mail_scheduled_message_res_partner_rel` embedded.

```js
{
  _id: int,  // id
  resId: int,  // res_id
  authorId: int,  // author_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  subject: string,  // subject
  compositionCommentOption: string,  // composition_comment_option
  model: string,  // model
  sendContext: object,  // send_context
  body: string,  // body
  notificationParameters: string,  // notification_parameters
  isNote: bool,  // is_note
  scheduledDate: date,  // scheduled_date
  createDate: date,  // create_date
  writeDate: date,  // write_date
  sendMethod: string,  // send_method
  resPartnerCcRel: [{  // mail_scheduled_message_res_partner_cc_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
  resPartnerRel: [{  // mail_scheduled_message_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
}
```

Why:
- res_partner, res_users → mail_scheduled_message: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_scheduled_message → mail_scheduled_message_res_partner_cc_rel, mail_scheduled_message_res_partner_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → mail_scheduled_message_res_partner_cc_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → mail_scheduled_message_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_scheduled_message → scheduled_message_attachment_rel: **reference**, a link table, embedded on the other side (assumed)

## mailTemplate

From `mail_template` with `mail_template_ir_actions_report_rel` embedded.

```js
{
  _id: int,  // id
  modelId: int,  // model_id
  userId: int,  // user_id
  mailServerId: int,  // mail_server_id
  refIrActWindow: int,  // ref_ir_act_window
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  templateFs: string,  // template_fs
  lang: string,  // lang
  model: string,  // model
  emailFrom: string,  // email_from
  emailTo: string,  // email_to
  partnerTo: string,  // partner_to
  emailCc: string,  // email_cc
  partnerCc: string,  // partner_cc
  replyTo: string,  // reply_to
  emailLayoutXmlid: string,  // email_layout_xmlid
  scheduledDate: string,  // scheduled_date
  name: object,  // name
  description: object,  // description
  subject: object,  // subject
  bodyHtml: object,  // body_html
  active: bool,  // active
  useDefaultTo: bool,  // use_default_to
  emailLayoutForceHeader: bool,  // email_layout_force_header
  emailLayoutForceFooter: bool,  // email_layout_force_footer
  autoDelete: bool,  // auto_delete
  createDate: date,  // create_date
  writeDate: date,  // write_date
  irActionsReportRel: [{  // mail_template_ir_actions_report_rel, 1:N assumed
    irActionsReportId: int,  // ir_actions_report_id
  }],
}
```

Why:
- mail_template → email_template_attachment_rel, mail_activity_type_mail_template_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_template → ir_act_server, res_company, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_mail_server, ir_model, ir_act_window → mail_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_report_xml → mail_template_ir_actions_report_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_template → mail_template_ir_actions_report_rel: **embed**, a link table, kept as an array on this side (assumed)

## onboardingOnboarding

From `onboarding_onboarding` with `onboarding_onboarding_onboarding_onboarding_step_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  routeName: string,  // route_name
  textCompleted: string,  // text_completed
  panelCloseActionName: string,  // panel_close_action_name
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  onboardingOnboardingStepRel: [{  // onboarding_onboarding_onboarding_onboarding_step_rel, 1:N assumed
    onboardingOnboardingStepId: int,  // onboarding_onboarding_step_id
  }],
}
```

Why:
- res_users → onboarding_onboarding: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- onboarding_onboarding_step → onboarding_onboarding_onboarding_onboarding_step_rel: **reference**, a link table, embedded on the other side (assumed)
- onboarding_onboarding → onboarding_onboarding_onboarding_onboarding_step_rel: **embed**, a link table, kept as an array on this side (assumed)
- onboarding_onboarding → onboarding_progress: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## onboardingProgress

From `onboarding_progress` with `onboarding_progress_onboarding_progress_step_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  onboardingId: int,  // onboarding_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  onboardingState: string,  // onboarding_state
  isOnboardingClosed: bool,  // is_onboarding_closed
  createDate: date,  // create_date
  writeDate: date,  // write_date
  onboardingProgressStepRel: [{  // onboarding_progress_onboarding_progress_step_rel, 1:N assumed
    onboardingProgressStepId: int,  // onboarding_progress_step_id
  }],
}
```

Why:
- res_company, res_users, onboarding_onboarding → onboarding_progress: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- onboarding_progress_step → onboarding_progress_onboarding_progress_step_rel: **reference**, a link table, embedded on the other side (assumed)
- onboarding_progress → onboarding_progress_onboarding_progress_step_rel: **embed**, a link table, kept as an array on this side (assumed)

## paymentMethod

From `payment_method` with `payment_method_res_country_rel`, `payment_method_res_currency_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  primaryPaymentMethodId: int,  // primary_payment_method_id
  providerId: int,  // provider_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  code: string,  // code
  supportManualCapture: string,  // support_manual_capture
  supportRefund: string,  // support_refund
  name: object,  // name
  active: bool,  // active
  supportTokenization: bool,  // support_tokenization
  supportExpressCheckout: bool,  // support_express_checkout
  allowAmountSelection: bool,  // allow_amount_selection
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resCountryRel: [{  // payment_method_res_country_rel, 1:N assumed
    resCountryId: int,  // res_country_id
  }],
  resCurrencyRel: [{  // payment_method_res_currency_rel, 1:N assumed
    resCurrencyId: int,  // res_currency_id
  }],
}
```

Why:
- res_users, payment_provider → payment_method: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- payment_method → payment_method, payment_token, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- payment_method → payment_method_res_country_rel, payment_method_res_currency_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_country → payment_method_res_country_rel: **reference**, a link table, embedded on the other side (assumed)
- res_currency → payment_method_res_currency_rel: **reference**, a link table, embedded on the other side (assumed)

## paymentProvider

From `payment_provider` with `payment_country_rel`, `payment_currency_rel`, `payment_provider_product_pricelist_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  companyId: int,  // company_id
  redirectFormViewId: int,  // redirect_form_view_id
  inlineFormViewId: int,  // inline_form_view_id
  tokenInlineFormViewId: int,  // token_inline_form_view_id
  expressCheckoutFormViewId: int,  // express_checkout_form_view_id
  moduleId: int,  // module_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  code: string,  // code
  name: object,  // name
  preMsg: object,  // pre_msg
  pendingMsg: object,  // pending_msg
  authMsg: object,  // auth_msg
  doneMsg: object,  // done_msg
  cancelMsg: object,  // cancel_msg
  minimumAmount: decimal,  // minimum_amount
  maximumAmount: decimal,  // maximum_amount
  isLive: bool,  // is_live
  isPublished: bool,  // is_published
  active: bool,  // active
  allowTokenization: bool,  // allow_tokenization
  allowExpressCheckout: bool,  // allow_express_checkout
  captureManually: bool,  // capture_manually
  createDate: date,  // create_date
  writeDate: date,  // write_date
  soReferenceType: string,  // so_reference_type
  paymentCountryRel: [{  // payment_country_rel, 1:N assumed
    countryId: int,  // country_id
  }],
  paymentCurrencyRel: [{  // payment_currency_rel, 1:N assumed
    currencyId: int,  // currency_id
  }],
  productPricelistRel: [{  // payment_provider_product_pricelist_rel, 1:N assumed
    productPricelistId: int,  // product_pricelist_id
  }],
}
```

Why:
- payment_provider → account_payment_method_line, payment_method, payment_token, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country → payment_country_rel: **reference**, a link table, embedded on the other side (assumed)
- payment_provider → payment_country_rel, payment_currency_rel, payment_provider_product_pricelist_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_currency → payment_currency_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, ir_ui_view, ir_module_module → payment_provider: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_pricelist → payment_provider_product_pricelist_rel: **reference**, a link table, embedded on the other side (assumed)

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
- product_category → account_analytic_applicability, account_analytic_distribution_model, product_category, product_pricelist_item, product_template, stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, product_removal → product_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_type → product_category_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category → product_category_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)

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
- res_company, res_users → product_combo: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo → product_combo_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo → product_combo_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_combo_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

## productTemplate

From `product_template` with `product_optional_rel`, `product_product`, `product_template_uom_uom_rel`, `product_taxes_rel`, `product_supplier_taxes_rel`, `product_tag_product_template_rel`, `product_attribute_product_template_rel`, `account_account_tag_product_template_rel`, `stock_route_product` embedded.

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
  productProduct: [{  // product_product, 1:N derived
    id: int,  // id
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
  }],
  uomUomRel: [{  // product_template_uom_uom_rel, 1:N assumed
    uomUomId: int,  // uom_uom_id
  }],
  taxesId: [{  // product_taxes_rel, 1:few derived
    taxId: int,  // tax_id
  }],
  supplierTaxesId: [{  // product_supplier_taxes_rel, 1:few derived
    taxId: int,  // tax_id
  }],
  productTagIds: [{  // product_tag_product_template_rel, 1:few derived
    productTagId: int,  // product_tag_id
  }],
  productAttributeIds: [{  // product_attribute_product_template_rel, 1:few derived
    productAttributeId: int,  // product_attribute_id
  }],
  accountTagIds: [{  // account_account_tag_product_template_rel, 1:few derived
    accountAccountTagId: int,  // account_account_tag_id
  }],
  routeIds: [{  // stock_route_product, 1:few derived
    routeId: int,  // route_id
  }],
}
```

Why:
- account_account_tag → account_account_tag_product_template_rel: **reference**, a link table, kept as an array on this side (derived)
- product_template → account_account_tag_product_template_rel, product_attribute_product_template_rel, product_supplier_taxes_rel, product_tag_product_template_rel, product_taxes_rel, stock_route_product: **embed**, a link table, embedded on the other side (derived)
- product_attribute → product_attribute_product_template_rel: **reference**, a link table, kept as an array on this side (derived)
- product_template → product_combo_product_template_rel, product_optional_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_optional_rel, product_template_uom_uom_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_pricelist_item, product_supplierinfo, product_template_attribute_line, product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_base_unit, res_users → product_product: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_template → product_product: **embed**, the app reads it with its parent (derived)
- account_tax → product_supplier_taxes_rel: **reference**, a link table, kept as an array on this side (derived)
- product_tag → product_tag_product_template_rel: **reference**, a link table, kept as an array on this side (derived)
- account_tax → product_taxes_rel: **reference**, a link table, kept as an array on this side (derived)
- product_base_unit, product_category, res_company, res_users, ir_sequence, uom_uom → product_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- uom_uom → product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_route_product: **reference**, a link table, kept as an array on this side (derived)

## productTemplateAttributeLine

From `product_template_attribute_line` with `product_attribute_value_product_template_attribute_line_rel` embedded.

```js
{
  _id: int,  // id
  productTmplId: int,  // product_tmpl_id
  sequence: int,  // sequence
  attributeId: int,  // attribute_id
  valueCount: int,  // value_count
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  valueIds: [{  // product_attribute_value_product_template_attribute_line_rel, 1:few derived
    productAttributeValueId: int,  // product_attribute_value_id
  }],
}
```

Why:
- product_template_attribute_line → product_attribute_value_product_template_attribute_line_rel: **embed**, a link table, embedded on the other side (derived)
- product_attribute_value → product_attribute_value_product_template_attribute_line_rel: **reference**, a link table, kept as an array on this side (derived)
- product_attribute, res_users, product_template → product_template_attribute_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_line → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productTemplateAttributeValue

From `product_template_attribute_value` with `product_template_attribute_excluded_value_ids_rel` embedded.

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
}
```

Why:
- product_template_attribute_value → product_attribute_custom_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel, product_variant_combination: **reference**, a link table, embedded on the other side (assumed)
- product_attribute_value, product_attribute, product_template_attribute_line, res_users, product_template → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_value → product_template_attribute_value_purchase_order_line_rel, product_template_attribute_value_sale_order_line_rel, template_attribute_value_stock_move_rel: **reference**, a link table, kept as an array on this side (derived)

## purchaseOrder

From `purchase_order` with `purchase_order_line`, `purchase_order_stock_picking_rel` embedded.

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
  line: [{  // purchase_order_line, 1:N derived
    id: int,  // id
    productId: int,  // product_id
    sequence: int,  // sequence
    uomId: int,  // uom_id
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
  }],
  stockPickingRel: [{  // purchase_order_stock_picking_rel, 1:N assumed
    stockPickingId: int,  // stock_picking_id
  }],
}
```

Why:
- purchase_order → account_move_purchase_order_rel, stock_reference_purchase_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, res_currency, res_partner, account_fiscal_position, account_incoterms, account_payment_term, stock_picking_type → purchase_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_location, stock_warehouse_orderpoint, res_partner, product_product, sale_order_line, uom_uom → purchase_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- purchase_order → purchase_order_line: **embed**, the app reads it with its parent (derived)
- purchase_order → purchase_order_stock_picking_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_picking → purchase_order_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)

## resCompany

From `res_company` with `res_company_spreadsheet_dashboard_rel` embedded.

```js
{
  _id: int,  // id
  name: string,  // name
  partnerId: int,  // partner_id
  currencyId: int,  // currency_id
  sequence: int,  // sequence
  createDate: date,  // create_date
  parentPath: string,  // parent_path
  parentId: int,  // parent_id
  paperformatId: int,  // paperformat_id
  externalReportLayoutId: int,  // external_report_layout_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  email: string,  // email
  phone: string,  // phone
  reportTablesId: string,  // report_tables_id
  font: string,  // font
  primaryColor: string,  // primary_color
  secondaryColor: string,  // secondary_color
  reportHeader: object,  // report_header
  reportFooter: object,  // report_footer
  companyDetails: object,  // company_details
  active: bool,  // active
  usesDefaultLogo: bool,  // uses_default_logo
  writeDate: date,  // write_date
  nomenclatureId: int,  // nomenclature_id
  resourceCalendarId: int,  // resource_calendar_id
  tz: string,  // tz
  aliasDomainId: int,  // alias_domain_id
  emailPrimaryColor: string,  // email_primary_color
  emailSecondaryColor: string,  // email_secondary_color
  iapEnrichAutoDone: bool,  // iap_enrich_auto_done
  payNowLabel: object,  // pay_now_label
  payLaterLabel: object,  // pay_later_label
  fiscalyearLastDay: int,  // fiscalyear_last_day
  transferAccountId: int,  // transfer_account_id
  defaultCashDifferenceIncomeAccountId: int,  // default_cash_difference_income_account_id
  defaultCashDifferenceExpenseAccountId: int,  // default_cash_difference_expense_account_id
  accountJournalSuspenseAccountId: int,  // account_journal_suspense_account_id
  accountJournalEarlyPayDiscountGainAccountId: int,  // account_journal_early_pay_discount_gain_account_id
  accountJournalEarlyPayDiscountLossAccountId: int,  // account_journal_early_pay_discount_loss_account_id
  accountSaleTaxId: int,  // account_sale_tax_id
  accountPurchaseTaxId: int,  // account_purchase_tax_id
  accountPurchaseReceiptFiscalPositionId: int,  // account_purchase_receipt_fiscal_position_id
  currencyExchangeJournalId: int,  // currency_exchange_journal_id
  incomeCurrencyExchangeAccountId: int,  // income_currency_exchange_account_id
  expenseCurrencyExchangeAccountId: int,  // expense_currency_exchange_account_id
  incotermId: int,  // incoterm_id
  batchPaymentSequenceId: int,  // batch_payment_sequence_id
  accountOpeningMoveId: int,  // account_opening_move_id
  accountDefaultPosReceivableAccountId: int,  // account_default_pos_receivable_account_id
  expenseAccrualAccountId: int,  // expense_accrual_account_id
  revenueAccrualAccountId: int,  // revenue_accrual_account_id
  automaticEntryDefaultJournalId: int,  // automatic_entry_default_journal_id
  domesticFiscalPositionId: int,  // domestic_fiscal_position_id
  accountFiscalCountryId: int,  // account_fiscal_country_id
  taxCashBasisJournalId: int,  // tax_cash_basis_journal_id
  accountCashBasisBaseAccountId: int,  // account_cash_basis_base_account_id
  accountDiscountIncomeAllocationId: int,  // account_discount_income_allocation_id
  accountDiscountExpenseAllocationId: int,  // account_discount_expense_allocation_id
  priceDifferenceAccountId: int,  // price_difference_account_id
  fiscalyearLastMonth: string,  // fiscalyear_last_month
  chartTemplate: string,  // chart_template
  bankAccountCodePrefix: string,  // bank_account_code_prefix
  cashAccountCodePrefix: string,  // cash_account_code_prefix
  transferAccountCodePrefix: string,  // transfer_account_code_prefix
  taxCalculationRoundingMethod: string,  // tax_calculation_rounding_method
  termsType: string,  // terms_type
  quickEditMode: string,  // quick_edit_mode
  accountPriceInclude: string,  // account_price_include
  inventoryPeriod: string,  // inventory_period
  fiscalyearLockDate: date,  // fiscalyear_lock_date
  taxLockDate: date,  // tax_lock_date
  saleLockDate: date,  // sale_lock_date
  purchaseLockDate: date,  // purchase_lock_date
  hardLockDate: date,  // hard_lock_date
  accountOpeningDate: date,  // account_opening_date
  invoiceTerms: object,  // invoice_terms
  invoiceTermsHtml: object,  // invoice_terms_html
  expectsChartOfAccounts: bool,  // expects_chart_of_accounts
  angloSaxonAccounting: bool,  // anglo_saxon_accounting
  qrCode: bool,  // qr_code
  linkQrCode: bool,  // link_qr_code
  displayInvoiceAmountTotalWords: bool,  // display_invoice_amount_total_words
  displayInvoiceTaxCompanyCurrency: bool,  // display_invoice_tax_company_currency
  accountUseCreditLimit: bool,  // account_use_credit_limit
  vatCheckVies: bool,  // vat_check_vies
  vatDisabled: bool,  // vat_disabled
  taxExigibility: bool,  // tax_exigibility
  accountStorno: bool,  // account_storno
  quickEditModeEnabled: bool,  // quick_edit_mode_enabled
  documentSequenceEditable: bool,  // document_sequence_editable
  setToReviewDocuments: bool,  // set_to_review_documents
  restrictiveAuditTrail: bool,  // restrictive_audit_trail
  autopostBills: bool,  // autopost_bills
  internalTransitLocationId: int,  // internal_transit_location_id
  stockMailConfirmationTemplateId: int,  // stock_mail_confirmation_template_id
  annualInventoryDay: int,  // annual_inventory_day
  horizonDays: int,  // horizon_days
  annualInventoryMonth: string,  // annual_inventory_month
  stockConfirmationType: string,  // stock_confirmation_type
  pickingPolicy: string,  // picking_policy
  stockMoveEmailValidation: bool,  // stock_move_email_validation
  stockTextConfirmation: bool,  // stock_text_confirmation
  poLock: string,  // po_lock
  poDoubleValidation: string,  // po_double_validation
  poDoubleValidationAmount: decimal,  // po_double_validation_amount
  accountProductionWipAccountId: int,  // account_production_wip_account_id
  accountProductionWipOverheadAccountId: int,  // account_production_wip_overhead_account_id
  stockSmsConfirmationTemplateId: int,  // stock_sms_confirmation_template_id
  hasReceivedWarningStockSms: bool,  // has_received_warning_stock_sms
  daysToPurchase: int,  // days_to_purchase
  quotationValidityDays: int,  // quotation_validity_days
  saleDiscountProductId: int,  // sale_discount_product_id
  downpaymentAccountId: int,  // downpayment_account_id
  saleOnboardingPaymentMethod: string,  // sale_onboarding_payment_method
  saleInvoicePolicy: string,  // sale_invoice_policy
  portalConfirmationSign: bool,  // portal_confirmation_sign
  portalConfirmationPay: bool,  // portal_confirmation_pay
  displayProductImagesOnSo: bool,  // display_product_images_on_so
  showSolNumbers: bool,  // show_sol_numbers
  saleAutomaticInvoice: bool,  // sale_automatic_invoice
  prepaymentPercent: double,  // prepayment_percent
  returnValidityDays: int,  // return_validity_days
  securityLead: int,  // security_lead
  allowSpontaneousReturns: bool,  // allow_spontaneous_returns
  spreadsheetDashboardRel: [{  // res_company_spreadsheet_dashboard_rel, 1:N assumed
    spreadsheetDashboardId: int,  // spreadsheet_dashboard_id
  }],
}
```

Why:
- res_company → account_account_res_company_rel, iap_account_res_company_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company → account_analytic_account, account_analytic_applicability, account_analytic_distribution_model, account_analytic_line, account_bank_statement, account_bank_statement_line, account_cash_rounding, account_fiscal_position, account_journal, account_lock_exception, account_move, account_partial_reconcile, account_payment, account_payment_term, account_reconcile_model, account_reconcile_model_line, account_tax, account_tax_group, crm_team, digest_digest, ir_attachment, ir_default, ir_sequence, mail_activity_plan, mail_message, onboarding_progress, onboarding_progress_step, payment_provider, payment_token, payment_transaction, product_category, product_combo, product_combo_item, product_pricelist, product_pricelist_item, product_supplierinfo, product_template, product_uom, product_value, purchase_order, res_company, res_partner, res_partner_bank, res_users, resource_calendar, resource_resource, sale_order, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_package_type, stock_picking, stock_picking_batch, stock_picking_type, stock_putaway_rule, stock_quant, stock_route, stock_rule, stock_storage_category, stock_warehouse, stock_warehouse_orderpoint, website: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company → account_fiscal_position_account, account_move_line, account_report_external_value, account_tax_repartition_line, purchase_order_line, res_currency_rate, resource_calendar_leaves, sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_account, res_country, account_move, account_fiscal_position, account_tax, mail_alias_domain, account_journal, ir_sequence, res_users, res_currency, ir_ui_view, account_incoterms, stock_location, barcode_nomenclature, report_paperformat, res_partner, resource_calendar, product_product, mail_template, sms_template → res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company → res_company_spreadsheet_dashboard_rel: **embed**, a link table, kept as an array on this side (assumed)
- spreadsheet_dashboard → res_company_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company → res_company_users_rel: **reference**, a link table, kept as an array on this side (derived)

## resCountry

From `res_country` with `res_country_res_country_group_rel` embedded.

```js
{
  _id: int,  // id
  addressViewId: int,  // address_view_id
  currencyId: int,  // currency_id
  phoneCode: int,  // phone_code
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  code: string,  // code
  namePosition: string,  // name_position
  zipApplicability: string,  // zip_applicability
  name: object,  // name
  vatLabel: object,  // vat_label
  addressFormat: string,  // address_format
  stateRequired: bool,  // state_required
  createDate: date,  // create_date
  writeDate: date,  // write_date
  enforceCities: bool,  // enforce_cities
  resCountryGroupRel: [{  // res_country_res_country_group_rel, 1:N assumed
    resCountryGroupId: int,  // res_country_group_id
  }],
}
```

Why:
- res_country → account_account_tag, account_fiscal_position, account_report, account_tax, account_tax_group, clearing_label, mail_guest, payment_transaction, res_city, res_company, res_country_state, res_partner, res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country → module_country, payment_country_rel, payment_method_res_country_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_ui_view, res_users, res_currency → res_country: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country_group → res_country_res_country_group_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country → res_country_res_country_group_rel: **embed**, a link table, kept as an array on this side (assumed)

## resCountryGroup

From `res_country_group` with `res_country_group_pricelist_rel`, `res_country_group_res_country_state_rel` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  code: string,  // code
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  pricelistRel: [{  // res_country_group_pricelist_rel, 1:N assumed
    pricelistId: int,  // pricelist_id
  }],
  resCountryStateRel: [{  // res_country_group_res_country_state_rel, 1:N assumed
    resCountryStateId: int,  // res_country_state_id
  }],
}
```

Why:
- res_country_group → account_fiscal_position: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → res_country_group: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_pricelist → res_country_group_pricelist_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country_group → res_country_group_pricelist_rel, res_country_group_res_country_state_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_country_state → res_country_group_res_country_state_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country_group → res_country_res_country_group_rel: **reference**, a link table, embedded on the other side (assumed)

## resGroups

From `res_groups` with `res_groups_implied_rel`, `res_groups_report_rel`, `res_groups_spreadsheet_dashboard_rel` embedded.

```js
{
  _id: int,  // id
  name: object,  // name
  sequence: int,  // sequence
  privilegeId: int,  // privilege_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  comment: object,  // comment
  share: bool,  // share
  createDate: date,  // create_date
  writeDate: date,  // write_date
  apiKeyDuration: double,  // api_key_duration
  impliedRel: [{  // res_groups_implied_rel, 1:N assumed
    hid: int,  // hid
  }],
  reportRel: [{  // res_groups_report_rel, 1:N assumed
    uid: int,  // uid
  }],
  spreadsheetDashboardRel: [{  // res_groups_spreadsheet_dashboard_rel, 1:N assumed
    spreadsheetDashboardId: int,  // spreadsheet_dashboard_id
  }],
}
```

Why:
- res_groups → digest_tip, discuss_channel, ir_access: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_groups → discuss_channel_res_groups_rel, ir_act_server_group_rel, ir_act_window_group_rel, ir_embedded_actions_res_groups_rel, ir_model_fields_group_rel, ir_ui_menu_group_rel, ir_ui_view_group_rel, mail_canned_response_res_groups_rel, res_groups_implied_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, res_groups_privilege → res_groups: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_groups → res_groups_implied_rel, res_groups_report_rel, res_groups_spreadsheet_dashboard_rel: **embed**, a link table, kept as an array on this side (assumed)
- ir_act_report_xml → res_groups_report_rel: **reference**, a link table, embedded on the other side (assumed)
- spreadsheet_dashboard → res_groups_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- res_groups → res_groups_users_rel: **reference**, a link table, kept as an array on this side (derived)

## resPartner

From `res_partner` with `res_partner_res_partner_category_rel`, `res_partner_stock_lot_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  createDate: date,  // create_date
  name: string,  // name
  parentId: int,  // parent_id
  userId: int,  // user_id
  stateId: int,  // state_id
  countryId: int,  // country_id
  industryId: int,  // industry_id
  color: int,  // color
  commercialPartnerId: int,  // commercial_partner_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  completeName: string,  // complete_name
  ref: string,  // ref
  lang: string,  // lang
  tz: string,  // tz
  vat: string,  // vat
  website: string,  // website
  function: string,  // function
  type: string,  // type
  street: string,  // street
  street2: string,  // street2
  zip: string,  // zip
  city: string,  // city
  email: string,  // email
  phone: string,  // phone
  commercialCompanyName: string,  // commercial_company_name
  properties: object,  // properties
  additionalIdentifiers: object,  // additional_identifiers
  barcode: object,  // barcode
  comment: string,  // comment
  partnerLatitude: decimal,  // partner_latitude
  partnerLongitude: decimal,  // partner_longitude
  active: bool,  // active
  employee: bool,  // employee
  isCompany: bool,  // is_company
  partnerShare: bool,  // partner_share
  writeDate: date,  // write_date
  cityId: int,  // city_id
  streetName: string,  // street_name
  streetNumber: string,  // street_number
  streetNumber2: string,  // street_number2
  messageBounce: int,  // message_bounce
  emailNormalized: string,  // email_normalized
  signupType: string,  // signup_type
  phoneSanitized: string,  // phone_sanitized
  specificPropertyProductPricelist: object,  // specific_property_product_pricelist
  invoiceTemplatePdfReportId: int,  // invoice_template_pdf_report_id
  supplierRank: int,  // supplier_rank
  customerRank: int,  // customer_rank
  autopostBills: string,  // autopost_bills
  qrCodeMethod: object,  // qr_code_method
  creditLimit: object,  // credit_limit
  propertyAccountPayableId: object,  // property_account_payable_id
  propertyAccountReceivableId: object,  // property_account_receivable_id
  propertyAccountPositionId: object,  // property_account_position_id
  propertyPaymentTermId: object,  // property_payment_term_id
  propertySupplierPaymentTermId: object,  // property_supplier_payment_term_id
  trust: object,  // trust
  ignoreAbnormalInvoiceDate: object,  // ignore_abnormal_invoice_date
  ignoreAbnormalInvoiceAmount: object,  // ignore_abnormal_invoice_amount
  invoiceSendingMethod: object,  // invoice_sending_method
  invoiceEdiFormatStore: object,  // invoice_edi_format_store
  propertyOutboundPaymentMethodLineId: object,  // property_outbound_payment_method_line_id
  propertyInboundPaymentMethodLineId: object,  // property_inbound_payment_method_line_id
  propertyStockCustomer: object,  // property_stock_customer
  propertyStockSupplier: object,  // property_stock_supplier
  pickingWarnMsg: string,  // picking_warn_msg
  routingScheme: string,  // routing_scheme
  routingEndpoint: string,  // routing_endpoint
  buyerId: int,  // buyer_id
  purchaseIncotermId: int,  // purchase_incoterm_id
  purchaseIncotermLocation: string,  // purchase_incoterm_location
  propertyPurchaseCurrencyId: object,  // property_purchase_currency_id
  receiptReminderEmail: object,  // receipt_reminder_email
  reminderDateBeforeReceipt: object,  // reminder_date_before_receipt
  purchaseWarnMsg: string,  // purchase_warn_msg
  suggestDays: int,  // suggest_days
  suggestPercent: int,  // suggest_percent
  suggestBasedOn: string,  // suggest_based_on
  groupRfq: string,  // group_rfq
  groupOn: string,  // group_on
  incotermId: int,  // incoterm_id
  incotermLocation: string,  // incoterm_location
  saleWarnMsg: string,  // sale_warn_msg
  resPartnerCategoryRel: [{  // res_partner_res_partner_category_rel, 1:N assumed
    categoryId: int,  // category_id
  }],
  stockLotRel: [{  // res_partner_stock_lot_rel, 1:N assumed
    stockLotId: int,  // stock_lot_id
  }],
}
```

Why:
- res_partner → account_analytic_account, account_analytic_distribution_model, account_analytic_line, account_bank_statement_line, account_move, account_payment, account_reconcile_model, account_reconcile_model_line, customer_product_reference, discuss_channel_member, discuss_channel_rtc_session, mail_followers, mail_message, mail_message_reaction, mail_notification, mail_push_device, mail_scheduled_message, payment_token, payment_transaction, product_supplierinfo, purchase_order, res_company, res_partner, res_partner_bank, res_users, res_users_settings_volumes, sale_order, sms_sms, stock_move, stock_move_line, stock_picking, stock_quant, stock_rule, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner → account_move_line, purchase_order_line, sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_partner → account_reconcile_model_res_partner_rel, ir_act_server_res_partner_rel, mail_mail_res_partner_cc_rel, mail_mail_res_partner_rel, mail_message_res_partner_bookmarked_rel, mail_message_res_partner_cc_rel, mail_message_res_partner_rel, mail_scheduled_message_res_partner_cc_rel, mail_scheduled_message_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, res_city, res_company, res_country, account_incoterms, res_partner_industry, ir_act_report_xml, res_country_state → res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner_category → res_partner_res_partner_category_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → res_partner_res_partner_category_rel, res_partner_stock_lot_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_lot → res_partner_stock_lot_rel: **reference**, a link table, embedded on the other side (assumed)

## resRole

From `res_role` with `res_role_res_users_rel` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  resUsersRel: [{  // res_role_res_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- res_role → ir_act_server, mail_activity, mail_activity_plan_template, mail_activity_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → res_role: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_role → res_role_res_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → res_role_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

## resUsers

From `res_users` with `auth_totp_device`, `res_users_apikeys`, `picking_type_favorite_user_rel`, `res_users_spreadsheet_dashboard_favorite_filters_rel`, `res_users_spreadsheet_dashboard_rel`, `res_users_web_tour_tour_rel`, `res_company_users_rel`, `res_groups_users_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  partnerId: int,  // partner_id
  active: bool,  // active
  createDate: date,  // create_date
  login: string,  // login
  password: string,  // password
  actionId: int,  // action_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  signature: string,  // signature
  share: bool,  // share
  writeDate: date,  // write_date
  totpLastCounter: int,  // totp_last_counter
  totpSecret: string,  // totp_secret
  tourEnabled: bool,  // tour_enabled
  notificationType: string,  // notification_type
  manualImStatus: string,  // manual_im_status
  outOfOfficeMessage: string,  // out_of_office_message
  outOfOfficeFrom: date,  // out_of_office_from
  outOfOfficeTo: date,  // out_of_office_to
  odoobotState: string,  // odoobot_state
  odoobotFailed: bool,  // odoobot_failed
  saleTeamId: int,  // sale_team_id
  propertyWarehouseId: object,  // property_warehouse_id
  authTotpDevice: [{  // auth_totp_device, 1:N assumed
    id: int,  // id
    name: string,  // name
    scope: string,  // scope
    expirationDate: date,  // expiration_date
    index: string,  // index
    key: string,  // key
    createDate: date,  // create_date
  }],
  apikeys: [{  // res_users_apikeys, 1:N assumed
    id: int,  // id
    name: string,  // name
    scope: string,  // scope
    expirationDate: date,  // expiration_date
    index: string,  // index
    key: string,  // key
    createDate: date,  // create_date
  }],
  pickingTypeFavoriteUserRel: [{  // picking_type_favorite_user_rel, 1:N assumed
    pickingTypeId: int,  // picking_type_id
  }],
  spreadsheetDashboardFavoriteFiltersRel: [{  // res_users_spreadsheet_dashboard_favorite_filters_rel, 1:N assumed
    spreadsheetDashboardFavoriteFiltersId: int,  // spreadsheet_dashboard_favorite_filters_id
  }],
  spreadsheetDashboardRel: [{  // res_users_spreadsheet_dashboard_rel, 1:N assumed
    spreadsheetDashboardId: int,  // spreadsheet_dashboard_id
  }],
  webTourTourRel: [{  // res_users_web_tour_tour_rel, 1:N assumed
    webTourTourId: int,  // web_tour_tour_id
  }],
  companyIds: [{  // res_company_users_rel, 1:few derived
    cid: int,  // cid
  }],
  groupIds: [{  // res_groups_users_rel, 1:few derived
    gid: int,  // gid
  }],
}
```

Why:
- res_users → account_account, account_account_tag, account_analytic_account, account_analytic_applicability, account_analytic_distribution_model, account_analytic_line, account_analytic_plan, account_bank_statement, account_bank_statement_line, account_cash_rounding, account_fiscal_position, account_full_reconcile, account_incoterms, account_journal, account_journal_group, account_lock_exception, account_move, account_partial_reconcile, account_payment, account_payment_method, account_payment_method_line, account_payment_term, account_reconcile_model, account_reconcile_model_line, account_report, account_report_expression, account_report_line, account_tax, account_tax_group, auth_passkey_key, barcode_nomenclature, barcode_rule, base_import_mapping, bus_bus, clearing_label, crm_tag, crm_team, crm_team_member, customer_product_reference, decimal_precision, digest_digest, digest_tip, discuss_call_history, discuss_category, discuss_channel, discuss_channel_member, discuss_channel_rtc_session, discuss_gif_favorite, fetchmail_server, html_editor_converter_test, html_editor_converter_test_sub, iap_account, iap_service, ir_access, ir_act_report_xml, ir_act_server, ir_act_window, ir_actions_todo, ir_asset, ir_attachment, ir_config_parameter, ir_cron, ir_default, ir_embedded_actions, ir_exports, ir_filters, ir_mail_server, ir_model, ir_model_constraint, ir_model_data, ir_model_fields, ir_model_fields_selection, ir_model_relation, ir_module_category, ir_module_module, ir_sequence, ir_ui_menu, ir_ui_view, ir_ui_view_custom, l10n_us_res_county, mail_activity, mail_activity_plan, mail_activity_plan_template, mail_activity_type, mail_alias, mail_alias_domain, mail_blacklist, mail_canned_response, mail_followers, mail_gateway_allowed, mail_guest, mail_ice_server, mail_link_preview, mail_mail, mail_message, mail_message_link_preview, mail_message_subtype, mail_poll, mail_poll_option, mail_poll_vote, mail_presence, mail_push_device, mail_scheduled_message, mail_template, onboarding_onboarding, onboarding_onboarding_step, onboarding_progress, onboarding_progress_step, payment_data, payment_method, payment_provider, payment_token, payment_transaction, phone_blacklist, portal_entry, privacy_log, product_attribute, product_attribute_custom_value, product_attribute_value, product_base_unit, product_category, product_combo, product_combo_item, product_pricelist, product_pricelist_item, product_removal, product_supplierinfo, product_tag, product_template, product_template_attribute_line, product_template_attribute_value, product_uom, product_value, purchase_order, report_layout, report_paperformat, res_city, res_company, res_country, res_country_group, res_country_state, res_currency, res_device_log, res_groups, res_groups_privilege, res_lang, res_partner, res_partner_bank, res_partner_category, res_partner_industry, res_role, res_users, res_users_deletion, res_users_log, res_users_settings, res_users_settings_embedded_action, res_users_settings_volumes, resource_calendar, resource_resource, return_reason, sale_order, sms_sms, sms_template, spreadsheet_dashboard, spreadsheet_dashboard_favorite_filters, spreadsheet_dashboard_group, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_package_type, stock_picking, stock_picking_batch, stock_picking_type, stock_putaway_rule, stock_quant, stock_reference, stock_route, stock_rule, stock_scrap_reason_tag, stock_storage_category, stock_storage_category_capacity, stock_warehouse, stock_warehouse_orderpoint, uom_uom, utm_campaign, utm_medium, utm_source, utm_stage, utm_tag, web_tour_tour, website: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_fiscal_position_account, account_move_line, account_payment_term_line, account_report_column, account_report_external_value, account_tax_repartition_line, discuss_voice_metadata, iap_service_pack, ir_act_client, ir_act_url, ir_act_window_view, ir_actions, ir_actions_server_history, ir_cron_progress, ir_cron_trigger, ir_exports_line, ir_module_module_exclusion, ir_sequence_date_range, mail_call_artifact, mail_message_schedule, mail_message_translation, mail_push, product_document, product_product, properties_base_definition, purchase_order_line, res_currency_rate, resource_calendar_attendance, resource_calendar_leaves, sale_order_line, sms_tracker, spreadsheet_dashboard_share, web_tour_tour_step: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → auth_totp_device, res_users_apikeys: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → digest_digest_res_users_rel, digest_tip_res_users_rel, iap_account_res_users_rel, ir_filters_res_users_rel, res_role_res_users_rel, spreadsheet_dashboard_allowed_users_rel, team_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking_type → picking_type_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → picking_type_favorite_user_rel, res_users_spreadsheet_dashboard_favorite_filters_rel, res_users_spreadsheet_dashboard_rel, res_users_web_tour_tour_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_company → res_company_users_rel: **reference**, a link table, kept as an array on this side (derived)
- res_users → res_company_users_rel, res_groups_users_rel: **embed**, a link table, embedded on the other side (derived)
- res_groups → res_groups_users_rel: **reference**, a link table, kept as an array on this side (derived)
- res_company, res_partner, crm_team → res_users: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- spreadsheet_dashboard_favorite_filters → res_users_spreadsheet_dashboard_favorite_filters_rel: **reference**, a link table, embedded on the other side (assumed)
- spreadsheet_dashboard → res_users_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- web_tour_tour → res_users_web_tour_tour_rel: **reference**, a link table, embedded on the other side (assumed)

## resourceCalendar

From `resource_calendar` with `resource_calendar_attendance`, `resource_calendar_leaves` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  referenceCalendarId: int,  // reference_calendar_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  calendarType: string,  // calendar_type
  daysPerWeek: decimal,  // days_per_week
  hoursPerDay: decimal,  // hours_per_day
  hoursPerWeek: decimal,  // hours_per_week
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  fullTimeRequiredHours: double,  // full_time_required_hours
  workTimeRate: double,  // work_time_rate
  attendance: [{  // resource_calendar_attendance, 1:N derived
    id: int,  // id
    sequence: int,  // sequence
    recurrencyInterval: int,  // recurrency_interval
    recurrencyCount: int,  // recurrency_count
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    dayPeriod: string,  // day_period
    dayofweek: string,  // dayofweek
    recurrencyType: string,  // recurrency_type
    recurrencyEndType: string,  // recurrency_end_type
    date: date,  // date
    recurrencyUntil: date,  // recurrency_until
    recurrencyExcludedOccurences: object,  // recurrency_excluded_occurences
    durationBased: bool,  // duration_based
    recurrency: bool,  // recurrency
    createDate: date,  // create_date
    writeDate: date,  // write_date
    hourFrom: double,  // hour_from
    hourTo: double,  // hour_to
    durationHours: double,  // duration_hours
  }],
  leaves: [{  // resource_calendar_leaves, 1:N derived
    id: int,  // id
    companyId: int,  // company_id
    resourceId: int,  // resource_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    name: string,  // name
    countAs: string,  // count_as
    dateFrom: date,  // date_from
    dateTo: date,  // date_to
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- resource_calendar → res_company, resource_calendar, resource_resource: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users → resource_calendar: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- resource_calendar → resource_calendar_attendance, resource_calendar_leaves: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → resource_calendar_attendance: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_company, res_users, resource_resource → resource_calendar_leaves: **reference**, it is embedded under another parent; this one is referenced (derived)

## saleOrder

From `sale_order` with `sale_order_line`, `sale_order_tag_rel`, `sale_order_transaction_rel` embedded.

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
  line: [{  // sale_order_line, 1:N derived
    id: int,  // id
    productId: int,  // product_id
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
  }],
  tagRel: [{  // sale_order_tag_rel, 1:N assumed
    tagId: int,  // tag_id
  }],
  transactionRel: [{  // sale_order_transaction_rel, 1:N assumed
    transactionId: int,  // transaction_id
  }],
}
```

Why:
- sale_order → account_analytic_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_analytic_account, utm_campaign, res_company, res_users, res_currency, account_fiscal_position, account_incoterms, account_journal, utm_medium, res_partner, account_payment_term, mail_template, account_payment_method_line, product_pricelist, utm_source, crm_team, stock_warehouse → sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo_item, res_company, res_users, res_currency, sale_order_line, res_partner, product_product, uom_uom, stock_warehouse → sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- sale_order → sale_order_line: **embed**, the app reads it with its parent (derived)
- sale_order → sale_order_tag_rel, sale_order_transaction_rel: **embed**, a link table, kept as an array on this side (assumed)
- crm_tag → sale_order_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- payment_transaction → sale_order_transaction_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order → stock_reference_sale_rel: **reference**, a link table, embedded on the other side (assumed)

## spreadsheetDashboard

From `spreadsheet_dashboard` with `spreadsheet_dashboard_share`, `spreadsheet_dashboard_allowed_users_rel` embedded.

```js
{
  _id: int,  // id
  dashboardGroupId: int,  // dashboard_group_id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  sampleDashboardFilePath: string,  // sample_dashboard_file_path
  name: object,  // name
  isPublished: bool,  // is_published
  createDate: date,  // create_date
  writeDate: date,  // write_date
  share: [{  // spreadsheet_dashboard_share, 1:N assumed
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    accessToken: string,  // access_token
    name: string,  // name
    active: bool,  // active
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  allowedUsersRel: [{  // spreadsheet_dashboard_allowed_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- spreadsheet_dashboard → ir_model_spreadsheet_dashboard_rel, res_company_spreadsheet_dashboard_rel, res_groups_spreadsheet_dashboard_rel, res_users_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, spreadsheet_dashboard_group → spreadsheet_dashboard: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- spreadsheet_dashboard → spreadsheet_dashboard_allowed_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → spreadsheet_dashboard_allowed_users_rel: **reference**, a link table, embedded on the other side (assumed)
- spreadsheet_dashboard → spreadsheet_dashboard_favorite_filters: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → spreadsheet_dashboard_share: **reference**, it is embedded under another parent; this one is referenced (derived)
- spreadsheet_dashboard → spreadsheet_dashboard_share: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

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
- stock_location → purchase_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_location → res_company, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_picking, stock_picking_type, stock_putaway_rule, stock_quant, stock_rule, stock_warehouse, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, product_removal, stock_storage_category, account_account, stock_warehouse → stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_type → stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_location → stock_location_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (assumed)

## stockMove

From `stock_move` with `stock_move_created_purchase_line_rel`, `stock_move_move_rel`, `stock_move_stock_scrap_reason_tag_rel`, `stock_route_move`, `template_attribute_value_stock_move_rel` embedded.

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
  createdPurchaseLineRel: [{  // stock_move_created_purchase_line_rel, 1:N assumed
    createdPurchaseLineId: int,  // created_purchase_line_id
  }],
  moveRel: [{  // stock_move_move_rel, 1:N assumed
    moveOrigId: int,  // move_orig_id
  }],
  stockScrapReasonTagRel: [{  // stock_move_stock_scrap_reason_tag_rel, 1:N assumed
    stockScrapReasonTagId: int,  // stock_scrap_reason_tag_id
  }],
  routeIds: [{  // stock_route_move, 1:few derived
    routeId: int,  // route_id
  }],
  neverProductTemplateAttributeValueIds: [{  // template_attribute_value_stock_move_rel, 1:few derived
    templateAttributeValueId: int,  // template_attribute_value_id
  }],
}
```

Why:
- stock_move → account_analytic_line_stock_move_rel, stock_move_move_rel, stock_reference_move_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_move → product_value, stock_move, stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move, res_company, res_users, stock_location, stock_warehouse_orderpoint, uom_uom, res_partner, stock_picking, stock_picking_type, product_product, purchase_order_line, stock_rule, sale_order_line, stock_warehouse → stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order_line → stock_move_created_purchase_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → stock_move_created_purchase_line_rel, stock_move_move_rel, stock_move_stock_scrap_reason_tag_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → stock_route_move, template_attribute_value_stock_move_rel: **embed**, a link table, embedded on the other side (derived)
- stock_route → stock_route_move: **reference**, a link table, kept as an array on this side (derived)
- product_template_attribute_value → template_attribute_value_stock_move_rel: **reference**, a link table, kept as an array on this side (derived)

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
- res_company, res_users, stock_location, stock_lot, stock_move, res_partner, stock_package_history, stock_package, stock_picking, product_product, uom_uom → stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_move_line → stock_move_line_consume_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_move_line → stock_move_line_consume_rel: **reference**, a link table, embedded on the other side (assumed)

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
- res_company, res_users, stock_location, stock_package → stock_package_history: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_package_history → stock_package_history_stock_picking_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_picking → stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)

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
- res_company, res_users, ir_sequence → stock_package_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_package_type → stock_package_type_stock_putaway_rule_rel, stock_package_type_stock_route_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_package_type_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)

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
- res_users → stock_reference: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_move → stock_reference_move_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_reference → stock_reference_move_rel, stock_reference_purchase_rel, stock_reference_sale_rel: **embed**, a link table, kept as an array on this side (assumed)
- purchase_order → stock_reference_purchase_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order → stock_reference_sale_rel: **reference**, a link table, embedded on the other side (assumed)

## stockRoute

From `stock_route` with `stock_route_categ`, `stock_route_warehouse` embedded.

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
  warehouse: [{  // stock_route_warehouse, 1:N assumed
    warehouseId: int,  // warehouse_id
  }],
}
```

Why:
- stock_route → sale_order_line_stock_route_rel, stock_package_type_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, stock_warehouse → stock_route: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_route_categ, stock_route_warehouse: **embed**, a link table, kept as an array on this side (assumed)
- stock_route → stock_route_move, stock_route_product: **reference**, a link table, kept as an array on this side (derived)
- stock_warehouse → stock_route_warehouse: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_rule, stock_warehouse, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

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
- stock_warehouse → sale_order, stock_location, stock_move, stock_picking_type, stock_route, stock_rule, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_warehouse → sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_warehouse → stock_route_warehouse, stock_wh_resupply_table: **reference**, a link table, embedded on the other side (assumed)
- stock_rule, res_company, res_users, stock_route, stock_picking_type, stock_location, res_partner → stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_warehouse → stock_wh_resupply_table: **embed**, a link table, kept as an array on this side (assumed)

## utmTag

From `utm_tag` with `utm_tag_rel` embedded.

```js
{
  _id: int,  // id
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  rel: [{  // utm_tag_rel, 1:N assumed
    tagId: int,  // tag_id
  }],
}
```

Why:
- res_users → utm_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- utm_tag → utm_tag_rel: **embed**, a link table, kept as an array on this side (assumed)
- utm_campaign → utm_tag_rel: **reference**, a link table, embedded on the other side (assumed)

## webTourTour

From `web_tour_tour` with `web_tour_tour_step` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  url: string,  // url
  rainbowManMessage: object,  // rainbow_man_message
  active: bool,  // active
  custom: bool,  // custom
  createDate: date,  // create_date
  writeDate: date,  // write_date
  step: [{  // web_tour_tour_step, 1:N assumed
    id: int,  // id
    sequence: int,  // sequence
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    trigger: string,  // trigger
    content: string,  // content
    tooltipPosition: string,  // tooltip_position
    run: string,  // run
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- web_tour_tour → res_users_web_tour_tour_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → web_tour_tour: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → web_tour_tour_step: **reference**, it is embedded under another parent; this one is referenced (derived)
- web_tour_tour → web_tour_tour_step: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

## accountAnalyticAccount

From `account_analytic_account`.

Why:
- res_company, res_users, res_partner, account_analytic_plan → account_analytic_account: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_analytic_account → account_analytic_line, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountAnalyticApplicability

From `account_analytic_applicability`.

Why:
- account_analytic_plan, res_company, res_users, product_category → account_analytic_applicability: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountAnalyticDistributionModel

From `account_analytic_distribution_model`.

Why:
- res_company, res_users, res_partner_category, res_partner, product_category, product_product → account_analytic_distribution_model: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountAnalyticPlan

From `account_analytic_plan`.

Why:
- account_analytic_plan → account_analytic_account, account_analytic_applicability, account_analytic_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_analytic_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountBankStatementLine

From `account_bank_statement_line`.

Why:
- res_company, res_users, res_currency, account_journal, account_move, res_partner, account_bank_statement → account_bank_statement_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)

## accountFullReconcile

From `account_full_reconcile`.

Why:
- res_users → account_full_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_full_reconcile → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_full_reconcile → account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountIncoterms

From `account_incoterms`.

Why:
- res_users → account_incoterms: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_incoterms → account_move, purchase_order, res_company, res_partner, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountJournalGroup

From `account_journal_group`.

Why:
- account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_journal_group: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountLockException

From `account_lock_exception`.

Why:
- res_company, res_users → account_lock_exception: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountPartialReconcile

From `account_partial_reconcile`.

Why:
- account_partial_reconcile → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_currency, account_move_line, account_move, account_full_reconcile → account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountPaymentMethod

From `account_payment_method`.

Why:
- account_payment_method → account_payment, account_payment_method_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_payment_method: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountPaymentMethodLine

From `account_payment_method_line`.

Why:
- account_payment_method_line → account_cash_rounding_account_payment_method_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment_method_line → account_move, account_payment, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, account_journal, account_account, account_payment_method, payment_provider → account_payment_method_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountReportLine

From `account_report_line`.

Why:
- account_report_line → account_report_expression, account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report_line → account_report_external_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users, account_report → account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountTaxGroup

From `account_tax_group`.

Why:
- account_tax_group → account_move_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_tax_group → account_tax: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_country, res_users → account_tax_group: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## authPasskeyKey

From `auth_passkey_key`.

Why:
- res_users → auth_passkey_key: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## barcodeNomenclature

From `barcode_nomenclature`.

Why:
- res_users → barcode_nomenclature: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- barcode_nomenclature → barcode_rule, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## barcodeRule

From `barcode_rule`.

Why:
- uom_uom, barcode_nomenclature, res_users → barcode_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## baseImportMapping

From `base_import_mapping`.

Why:
- res_users → base_import_mapping: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## busBus

From `bus_bus`.

Why:
- res_users → bus_bus: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## clearingLabel

From `clearing_label`.

Why:
- res_country, res_users → clearing_label: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- clearing_label → res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## crmTag

From `crm_tag`.

Why:
- res_users → crm_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_tag → sale_order_tag_rel: **reference**, a link table, embedded on the other side (assumed)

## crmTeamMember

From `crm_team_member`.

Why:
- res_users, crm_team → crm_team_member: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## customerProductReference

From `customer_product_reference`.

Why:
- res_users, res_partner, product_product → customer_product_reference: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## decimalPrecision

From `decimal_precision`.

Why:
- res_users → decimal_precision: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## discussCategory

From `discuss_category`.

Why:
- res_users → discuss_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_category → discuss_channel: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## discussChannelMember

From `discuss_channel_member`.

Why:
- discuss_channel, res_users, mail_guest, res_partner, discuss_channel_rtc_session, mail_message → discuss_channel_member: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_channel_member → discuss_channel_rtc_session: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## discussChannelRtcSession

From `discuss_channel_rtc_session`.

Why:
- discuss_channel_rtc_session → discuss_channel_member: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_channel, discuss_channel_member, res_users, res_partner → discuss_channel_rtc_session: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## discussGifFavorite

From `discuss_gif_favorite`.

Why:
- res_users → discuss_gif_favorite: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## fetchmailServer

From `fetchmail_server`.

Why:
- res_users, ir_model → fetchmail_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- fetchmail_server → mail_mail: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## htmlEditorConverterTest

From `html_editor_converter_test`.

Why:
- res_users, html_editor_converter_test_sub → html_editor_converter_test: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## htmlEditorConverterTestSub

From `html_editor_converter_test_sub`.

Why:
- html_editor_converter_test_sub → html_editor_converter_test: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → html_editor_converter_test_sub: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irAccess

From `ir_access`.

Why:
- res_users, res_groups, ir_model → ir_access: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irActReportXml

From `ir_act_report_xml`.

Why:
- ir_act_report_xml → account_journal, res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model, res_users, report_paperformat → ir_act_report_xml: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_report_xml → mail_template_ir_actions_report_rel, res_groups_report_rel: **reference**, a link table, embedded on the other side (assumed)

## irActionsTodo

From `ir_actions_todo`.

Why:
- res_users → ir_actions_todo: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irAsset

From `ir_asset`.

Why:
- res_users → ir_asset: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irConfigParameter

From `ir_config_parameter`.

Why:
- res_users → ir_config_parameter: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irDefault

From `ir_default`.

Why:
- res_company, res_users, ir_model_fields → ir_default: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irLogging

From `ir_logging`.

## irMailServer

From `ir_mail_server`.

Why:
- res_users → ir_mail_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_mail_server → mail_message, mail_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irModelConstraint

From `ir_model_constraint`.

Why:
- res_users, ir_model, ir_module_module → ir_model_constraint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irModelData

From `ir_model_data`.

Why:
- res_users → ir_model_data: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irModelFieldsSelection

From `ir_model_fields_selection`.

Why:
- ir_model_fields_selection → ir_act_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_model_fields → ir_model_fields_selection: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irModelRelation

From `ir_model_relation`.

Why:
- res_users, ir_model, ir_module_module → ir_model_relation: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irModuleCategory

From `ir_module_category`.

Why:
- res_users → ir_module_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_module_category → ir_module_category, ir_module_module, res_groups_privilege: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## irProfile

From `ir_profile`.

Why:
- ir_profile → ir_profile_query: **reference**, owned by its parent (cascade delete or ordinal key) (derived)

## irSequence

From `ir_sequence`.

Why:
- ir_sequence → ir_act_server, product_template, res_company, stock_package_type, stock_picking_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users → ir_sequence: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_sequence → ir_sequence_date_range: **reference**, no evidence either way (assumed)

## irSequenceDateRange

From `ir_sequence_date_range`.

Why:
- res_users → ir_sequence_date_range: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_sequence → ir_sequence_date_range: **reference**, no evidence either way (assumed)

## irUiViewCustom

From `ir_ui_view_custom`.

Why:
- res_users, ir_ui_view → ir_ui_view_custom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## l10nUsResCounty

From `l10n_us_res_county`.

Why:
- l10n_us_res_county → account_tax, res_city: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, res_country_state → l10n_us_res_county: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailActivity

From `mail_activity`.

Why:
- mail_activity → activity_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_activity_plan, mail_activity_plan_template, mail_activity_type, res_users, ir_model, res_role → mail_activity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailActivityPlan

From `mail_activity_plan`.

Why:
- mail_activity_plan → ir_act_server, mail_activity, mail_activity_plan_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, ir_model → mail_activity_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailActivityPlanTemplate

From `mail_activity_plan_template`.

Why:
- mail_activity_plan_template → mail_activity: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_activity_type, res_users, mail_activity_plan, res_role → mail_activity_plan_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailAlias

From `mail_alias`.

Why:
- mail_alias → account_journal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_alias_domain, ir_model, res_users → mail_alias: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailAliasDomain

From `mail_alias_domain`.

Why:
- mail_alias_domain → mail_alias, mail_message, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → mail_alias_domain: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailBlacklist

From `mail_blacklist`.

Why:
- res_users → mail_blacklist: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailGatewayAllowed

From `mail_gateway_allowed`.

Why:
- res_users → mail_gateway_allowed: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailGuest

From `mail_guest`.

Why:
- mail_guest → discuss_channel_member, mail_message, mail_message_reaction, mail_poll_vote, mail_presence: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country, res_users → mail_guest: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailIceServer

From `mail_ice_server`.

Why:
- res_users → mail_ice_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailLinkPreview

From `mail_link_preview`.

Why:
- res_users → mail_link_preview: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_link_preview → mail_message_link_preview: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailMessageLinkPreview

From `mail_message_link_preview`.

Why:
- res_users, mail_link_preview, mail_message → mail_message_link_preview: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailMessageReaction

From `mail_message_reaction`.

Why:
- mail_guest, mail_message, res_partner → mail_message_reaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailMessageSubtype

From `mail_message_subtype`.

Why:
- mail_message_subtype → ir_act_server_mail_message_subtype_rel, mail_followers_mail_message_subtype_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_message_subtype → mail_message, mail_message_subtype: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → mail_message_subtype: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailPoll

From `mail_poll`.

Why:
- res_users, mail_message → mail_poll: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_poll → mail_poll_option: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailPollOption

From `mail_poll_option`.

Why:
- res_users, mail_poll → mail_poll_option: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_poll_option → mail_poll_vote: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailPollVote

From `mail_poll_vote`.

Why:
- res_users, mail_guest, mail_poll_option → mail_poll_vote: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## mailPresence

From `mail_presence`.

Why:
- mail_guest, res_users → mail_presence: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## onboardingOnboardingStep

From `onboarding_onboarding_step`.

Why:
- onboarding_onboarding_step → onboarding_onboarding_onboarding_onboarding_step_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → onboarding_onboarding_step: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- onboarding_onboarding_step → onboarding_progress_step: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## onboardingProgressStep

From `onboarding_progress_step`.

Why:
- onboarding_progress_step → onboarding_progress_onboarding_progress_step_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, onboarding_onboarding_step → onboarding_progress_step: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## ormSignalingAssets

From `orm_signaling_assets`.

## ormSignalingDefault

From `orm_signaling_default`.

## ormSignalingGroups

From `orm_signaling_groups`.

## ormSignalingRegistry

From `orm_signaling_registry`.

## ormSignalingRouting

From `orm_signaling_routing`.

## ormSignalingStable

From `orm_signaling_stable`.

## ormSignalingTemplates

From `orm_signaling_templates`.

## paymentData

From `payment_data`.

Why:
- res_users, payment_transaction → payment_data: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## paymentToken

From `payment_token`.

Why:
- payment_token → account_payment, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_partner, payment_method, payment_provider → payment_token: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## paymentTransaction

From `payment_transaction`.

Why:
- payment_transaction → account_invoice_transaction_rel, sale_order_transaction_rel: **reference**, a link table, embedded on the other side (assumed)
- payment_transaction → account_payment, payment_data, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_currency, res_country, res_partner, res_country_state, account_payment, payment_method, payment_provider, payment_token → payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## phoneBlacklist

From `phone_blacklist`.

Why:
- res_users → phone_blacklist: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## portalEntry

From `portal_entry`.

Why:
- res_users → portal_entry: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## privacyLog

From `privacy_log`.

Why:
- res_users → privacy_log: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productAttribute

From `product_attribute`.

Why:
- res_users → product_attribute: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_attribute → product_attribute_product_template_rel: **reference**, a link table, kept as an array on this side (derived)
- product_attribute → product_attribute_value, product_template_attribute_line, product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productAttributeCustomValue

From `product_attribute_custom_value`.

Why:
- product_template_attribute_value, res_users, sale_order_line → product_attribute_custom_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productAttributeValue

From `product_attribute_value`.

Why:
- product_attribute, res_users → product_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_attribute_value → product_attribute_value_product_template_attribute_line_rel: **reference**, a link table, kept as an array on this side (derived)
- product_attribute_value → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productBaseUnit

From `product_base_unit`.

Why:
- res_users → product_base_unit: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_base_unit → product_product: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_base_unit → product_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productComboItem

From `product_combo_item`.

Why:
- product_combo, res_company, res_users, product_product → product_combo_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo_item → sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)

## productPricelist

From `product_pricelist`.

Why:
- product_pricelist → payment_provider_product_pricelist_rel, res_country_group_pricelist_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, res_currency → product_pricelist: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_pricelist → product_pricelist_item, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productPricelistItem

From `product_pricelist_item`.

Why:
- product_pricelist, product_category, res_company, res_users, res_currency, product_product, product_template, uom_uom → product_pricelist_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productProductUomUomRel

From `product_product_uom_uom_rel`.

Why:
- product_product → product_product_uom_uom_rel: **reference**, its parent is itself embedded, and arrays don't nest (assumed)
- uom_uom → product_product_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)

## productRemoval

From `product_removal`.

Why:
- product_removal → product_category, stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → product_removal: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productSupplierinfo

From `product_supplierinfo`.

Why:
- res_company, res_users, res_currency, res_partner, product_product, product_template, uom_uom → product_supplierinfo: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_supplierinfo → stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productTag

From `product_tag`.

Why:
- res_users → product_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_tag → product_tag_product_product_rel, product_tag_product_template_rel: **reference**, a link table, kept as an array on this side (derived)

## productUom

From `product_uom`.

Why:
- res_company, res_users, product_product, uom_uom → product_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productValue

From `product_value`.

Why:
- account_move, res_company, res_users, stock_lot, stock_move, product_product → product_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## productVariantCombination

From `product_variant_combination`.

Why:
- product_product → product_variant_combination: **reference**, its parent is itself embedded, and arrays don't nest (assumed)
- product_template_attribute_value → product_variant_combination: **reference**, a link table, embedded on the other side (assumed)

## purchaseOrderLineAccrualMoveRel

From `purchase_order_line_accrual_move_rel`.

Why:
- account_move → purchase_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- purchase_order_line → purchase_order_line_accrual_move_rel: **reference**, its parent is itself embedded, and arrays don't nest (assumed)

## reportLayout

From `report_layout`.

Why:
- res_users, ir_ui_view → report_layout: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## reportPaperformat

From `report_paperformat`.

Why:
- report_paperformat → ir_act_report_xml, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → report_paperformat: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resCity

From `res_city`.

Why:
- res_city → account_tax, res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country, res_users, l10n_us_res_county, res_country_state → res_city: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resCountryState

From `res_country_state`.

Why:
- res_country_state → account_fiscal_position_res_country_state_rel, res_country_group_res_country_state_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country_state → account_tax, l10n_us_res_county, payment_transaction, res_city, res_partner, res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country, res_users → res_country_state: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resCurrency

From `res_currency`.

Why:
- res_currency → account_account, account_analytic_line, account_bank_statement, account_bank_statement_line, account_journal, account_move, account_partial_reconcile, account_payment, payment_transaction, product_pricelist, product_pricelist_item, product_supplierinfo, purchase_order, res_company, res_country, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_currency → account_cash_rounding_res_currency_rel, payment_currency_rel, payment_method_res_currency_rel: **reference**, a link table, embedded on the other side (assumed)
- res_currency → account_move_line, sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → res_currency: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_currency → res_currency_rate: **reference**, no evidence either way (assumed)

## resCurrencyRate

From `res_currency_rate`.

Why:
- res_company, res_users → res_currency_rate: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_currency → res_currency_rate: **reference**, no evidence either way (assumed)

## resDeviceLog

From `res_device_log`.

Why:
- res_users → res_device_log: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resGroupsPrivilege

From `res_groups_privilege`.

Why:
- res_groups_privilege → res_groups: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_module_category, res_users → res_groups_privilege: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resLang

From `res_lang`.

Why:
- res_lang → ir_exports_res_lang_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → res_lang: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resPartnerBank

From `res_partner_bank`.

Why:
- res_partner_bank → account_journal, account_move, account_payment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- clearing_label, res_company, res_country, res_users, res_partner, res_country_state → res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resPartnerCategory

From `res_partner_category`.

Why:
- res_partner_category → account_analytic_distribution_model, res_partner_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner_category → account_cash_rounding_res_partner_category_rel, res_partner_res_partner_category_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → res_partner_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resPartnerIndustry

From `res_partner_industry`.

Why:
- res_partner_industry → res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → res_partner_industry: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resUsersDeletion

From `res_users_deletion`.

Why:
- res_users → res_users_deletion: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resUsersLog

From `res_users_log`.

Why:
- res_users → res_users_log: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resUsersSettings

From `res_users_settings`.

Why:
- res_users → res_users_settings: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users_settings → res_users_settings_embedded_action, res_users_settings_volumes: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resUsersSettingsEmbeddedAction

From `res_users_settings_embedded_action`.

Why:
- ir_act_window, res_users, res_users_settings → res_users_settings_embedded_action: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resUsersSettingsVolumes

From `res_users_settings_volumes`.

Why:
- res_users, res_partner, res_users_settings → res_users_settings_volumes: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## resourceResource

From `resource_resource`.

Why:
- resource_resource → resource_calendar_leaves: **reference**, it is embedded under another parent; this one is referenced (derived)
- resource_calendar, res_company, res_users → resource_resource: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## returnReason

From `return_reason`.

Why:
- res_users → return_reason: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- return_reason → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## saleOrderLineAccrualMoveRel

From `sale_order_line_accrual_move_rel`.

Why:
- account_move → sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → sale_order_line_accrual_move_rel: **reference**, its parent is itself embedded, and arrays don't nest (assumed)

## saleOrderLineInvoiceRel

From `sale_order_line_invoice_rel`.

Why:
- account_move_line → sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → sale_order_line_invoice_rel: **reference**, its parent is itself embedded, and arrays don't nest (assumed)

## saleOrderLineStockRouteRel

From `sale_order_line_stock_route_rel`.

Why:
- sale_order_line → sale_order_line_stock_route_rel: **reference**, its parent is itself embedded, and arrays don't nest (assumed)
- stock_route → sale_order_line_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)

## smsSms

From `sms_sms`.

Why:
- res_users, mail_message, res_partner → sms_sms: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## smsTemplate

From `sms_template`.

Why:
- sms_template → ir_act_server, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_model, ir_act_window → sms_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## spreadsheetDashboardFavoriteFilters

From `spreadsheet_dashboard_favorite_filters`.

Why:
- spreadsheet_dashboard_favorite_filters → res_users_spreadsheet_dashboard_favorite_filters_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, spreadsheet_dashboard → spreadsheet_dashboard_favorite_filters: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## spreadsheetDashboardGroup

From `spreadsheet_dashboard_group`.

Why:
- spreadsheet_dashboard_group → spreadsheet_dashboard: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → spreadsheet_dashboard_group: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockLot

From `stock_lot`.

Why:
- stock_lot → product_value, stock_move_line, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_lot → res_partner_stock_lot_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, stock_location, product_product → stock_lot: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockPackage

From `stock_package`.

Why:
- stock_package → stock_move_line, stock_package, stock_package_history, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_location, stock_package_type → stock_package: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockPicking

From `stock_picking`.

Why:
- stock_picking → purchase_order_stock_picking_rel, stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking → stock_move, stock_move_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_batch, res_company, res_users, stock_location, res_partner, stock_picking_type, return_reason, sale_order → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockPickingBatch

From `stock_picking_batch`.

Why:
- stock_picking_batch → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_picking_type → stock_picking_batch: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockPickingType

From `stock_picking_type`.

Why:
- stock_picking_type → picking_type_favorite_user_rel, product_category_stock_picking_type_rel, stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking_type → purchase_order, stock_move, stock_picking, stock_picking_batch, stock_picking_type, stock_rule, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_location, res_company, res_users, ir_sequence, stock_warehouse → stock_picking_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockPutawayRule

From `stock_putaway_rule`.

Why:
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category, res_company, res_users, stock_location, product_product, stock_storage_category → stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockQuant

From `stock_quant`.

Why:
- res_company, res_users, stock_location, stock_lot, res_partner, stock_package, product_product → stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockRule

From `stock_rule`.

Why:
- stock_rule → stock_move, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_location, res_partner, stock_picking_type, stock_route, stock_warehouse → stock_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockScrapReasonTag

From `stock_scrap_reason_tag`.

Why:
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → stock_scrap_reason_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockStorageCategory

From `stock_storage_category`.

Why:
- stock_storage_category → stock_location, stock_putaway_rule, stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users → stock_storage_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockStorageCategoryCapacity

From `stock_storage_category_capacity`.

Why:
- res_users, stock_package_type, product_product, stock_storage_category → stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## stockWarehouseOrderpoint

From `stock_warehouse_orderpoint`.

Why:
- stock_warehouse_orderpoint → purchase_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_warehouse_orderpoint → stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_location, product_product, uom_uom, stock_route, product_supplierinfo, stock_warehouse → stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## uomUom

From `uom_uom`.

Why:
- uom_uom → account_analytic_line, barcode_rule, product_pricelist_item, product_supplierinfo, product_template, product_uom, stock_move, stock_move_line, stock_warehouse_orderpoint, uom_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- uom_uom → account_move_line, purchase_order_line, sale_order_line: **reference**, it is embedded under another parent; this one is referenced (derived)
- uom_uom → product_product_uom_uom_rel, product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, stock_package_type → uom_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## utmCampaign

From `utm_campaign`.

Why:
- utm_campaign → account_move, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, utm_stage → utm_campaign: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- utm_campaign → utm_tag_rel: **reference**, a link table, embedded on the other side (assumed)

## utmMedium

From `utm_medium`.

Why:
- utm_medium → account_move, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → utm_medium: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## utmSource

From `utm_source`.

Why:
- utm_source → account_move, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → utm_source: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## utmStage

From `utm_stage`.

Why:
- utm_stage → utm_campaign: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → utm_stage: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## website

From `website`.

Why:
- res_company, res_users → website: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## accountTaxSaleOrderLineRel

From `account_tax_sale_order_line_rel`.

Why:
- account_tax → account_tax_sale_order_line_rel: **reference**, a link table, kept as an array on this side (derived)
- sale_order_line → account_tax_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)

## accountTaxPurchaseOrderLineRel

From `account_tax_purchase_order_line_rel`.

Why:
- account_tax → account_tax_purchase_order_line_rel: **reference**, a link table, kept as an array on this side (derived)
- purchase_order_line → account_tax_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)

## productTemplateAttributeValueSaleOrderLineRel

From `product_template_attribute_value_sale_order_line_rel`.

Why:
- product_template_attribute_value → product_template_attribute_value_sale_order_line_rel: **reference**, a link table, kept as an array on this side (derived)
- sale_order_line → product_template_attribute_value_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)

## productTemplateAttributeValuePurchaseOrderLineRel

From `product_template_attribute_value_purchase_order_line_rel`.

Why:
- product_template_attribute_value → product_template_attribute_value_purchase_order_line_rel: **reference**, a link table, kept as an array on this side (derived)
- purchase_order_line → product_template_attribute_value_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)

## productTagProductProductRel

From `product_tag_product_product_rel`.

Why:
- product_product → product_tag_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- product_tag → product_tag_product_product_rel: **reference**, a link table, kept as an array on this side (derived)

## irActClient

From `ir_act_client`.

Why:
- ir_model → ir_act_client: **reference**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → ir_act_client: **reference**, it is embedded under another parent; this one is referenced (derived)

## irActUrl

From `ir_act_url`.

Why:
- ir_model → ir_act_url: **reference**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → ir_act_url: **reference**, it is embedded under another parent; this one is referenced (derived)

## irActions

From `ir_actions`.

Why:
- ir_model → ir_actions: **reference**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → ir_actions: **reference**, it is embedded under another parent; this one is referenced (derived)

## irModelInherit

From `ir_model_inherit`.

Why:
- ir_model → ir_model_inherit: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_model_fields → ir_model_inherit: **reference**, owned by its parent (cascade delete or ordinal key) (derived)

## irProfileQuery

From `ir_profile_query`.

Why:
- ir_profile → ir_profile_query: **reference**, owned by its parent (cascade delete or ordinal key) (derived)
