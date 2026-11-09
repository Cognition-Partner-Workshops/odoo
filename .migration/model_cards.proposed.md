# Model review: map-draft-2

## Your data in MongoDB

557 source tables become 322 collections: 197 hold one table each, and 125 also carry 235 smaller tables embedded inside their documents (234 as arrays, 1 as one subdocument; 191 of the arrays are link tables). The most common reason a table keeps its own collection: other tables also point at it, so it keeps its own collection (1617 of 1648 references). The most common reason a table is embedded: a link table, kept as an array on this side (191 of 235 embeds). 221 tables stay on the source and are not migrated: account_account_account_merge_wizard_rel, account_accrued_orders_wizard, account_automatic_entry_wizard, account_automatic_entry_wizard_account_move_line_rel, account_autopost_bills_wizard, account_financial_year_op, account_merge_wizard, account_merge_wizard_line and 213 more.

### Examples

_No rehearsal sample for Root document: re-render with --samples (schema-modeling step 7)._

_No rehearsal sample for Embedded child array: re-render with --samples (schema-modeling step 7)._

_No rehearsal sample for Link-table array: re-render with --samples (schema-modeling step 7)._

_No rehearsal sample for Reference: re-render with --samples (schema-modeling step 7)._

### Known limits

- 1915 of 2186 relationship choices follow the schema alone (assumed), not measured data or app code.
- 205 embedded arrays have no measured size bound (cardinality assumed).
- 1026 questions are still open; they are listed below.
- No rehearsal sample yet: examples appear once the page is re-rendered with --samples.

## Review

- **Draft:** 322 collections, 235 embedded tables, 221 tables excluded.
- **Evidence:** of 2186 relationship choices, 271 rest on measured data or app code and 0 on a recorded decision (`derived`); the rest follow the schema alone (`assumed`).
- **Decisions:** 16 kinds of question, 1026 items. The draft already applies each proposal; answer each group with one line in `.migration/answers.txt` (template below).

1. **many_to_many_junction** (191): proposed as an array in account_account (junction name); confirm the side, that neither side's list grows without bound or past the 16 MB document limit, and add a multikey index for the reverse lookup — or keep a reference  
   Applies to: account_account_account_tag, account_account_res_company_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_account_tax_default_rel, account_analytic_line_stock_move_rel, account_bank_statement_ir_attachment_rel and 183 more
2. **embed_unbounded** (22): 1:N embed: confirm the fan-out bound and document size (16 MB) against data, or bucket/reference  
   Applies to: account_fiscal_position_account, account_report_external_value, discuss_channel_last_interest_update, event_registration_answer, hr_leave_accrual_level, hr_time_rule_allocation_log, iap_service_pack, discuss_voice_metadata and 14 more
3. **embed_null_pointer_rows** (5): rows whose binding_model_id IS NULL or matches no parent row have no parent document and are dropped; scope the embed with child_where (remainder recorded) or keep the table as a collection  
   Applies to: ir_act_client, ir_act_url, ir_actions, ir_model_inherit, survey_question_answer
4. **date_format_assumed** (3): unmeasurable in this profile  
   Applies to: hr_leave_accrual_plan, hr_leave_accrual_level, mail_template
5. **transient_tables** (1): 221 table(s) back transient models, scratch state the framework deletes on a timer, so they are not migrated: account_account_account_merge_wizard_rel, account_accrued_orders_wizard, account_automatic_entry_wizard, account_automatic_entry_wizard_account_move_line_rel, account_autopost_bills_wizard, account_financial_year_op, account_merge_wizard, account_merge_wizard_line, account_move_account_move_send_batch_wizard_rel, account_move_account_resequence_wizard_rel, account_move_reversal, account_move_reversal_move, account_move_reversal_new_move, account_move_send_batch_wizard, account_move_send_wizard, account_move_send_wizard_res_partner_rel, account_move_validate_account_move_rel, account_payment_register, account_payment_register_move_line_rel, account_resequence_wizard, account_secure_entries_wizard, account_setup_bank_manual_config, account_tax_hr_expense_split_rel, auth_passkey_key_create, auth_totp_rate_limit_log, auth_totp_wizard, base_document_layout, base_enable_profiling_wizard, base_import_import, base_import_module, base_language_export, base_language_import, base_language_install, base_module_install_request, base_module_install_review, base_module_uninstall, base_module_uninstall_ir_module_module_rel, base_module_update, base_module_upgrade, base_partner_merge_automatic_wizard, base_partner_merge_automatic_wizard_res_partner_rel, base_partner_merge_line, bill_to_po_wizard, calendar_event_archive_or_unlink_wizard, calendar_event_archive_or_unlink_wizard_res_partner_rel, calendar_event_multi_archive_or_unlink_wizard, calendar_event_multi_archive_or_unlink_wizard_rel, change_password_own, change_password_user, change_password_wizard, confirm_stock_sms, crm_convert_lead_mass_lead_rel, crm_lead2opportunity_partner_mass, crm_lead2opportunity_partner_mass_res_users_rel, crm_lead_crm_lead2opportunity_partner_mass_rel, crm_lead_crm_lead_lost_rel, crm_lead_duplicate_domain_rel, crm_lead_lost, crm_lead_pls_update, crm_lead_pls_update_crm_lead_scoring_frequency_field_rel, crm_merge_opportunity, crm_quotation_partner, digest_test, digest_test_res_users_rel, event_event_configurator, expense_attachment_selection_wizard, fleet_vehicle_fleet_vehicle_send_mail_rel, fleet_vehicle_mail_compose_message_ir_attachments_rel, fleet_vehicle_send_mail, gamification_badge_user_wizard, gamification_goal_wizard, homework_location_wizard, hr_bank_account_allocation_wizard, hr_bank_account_allocation_wizard_line, hr_employee_create_version_wizard, hr_employee_cv_wizard, hr_employee_delete_wizard, hr_employee_hr_employee_cv_wizard_rel, hr_employee_hr_employee_delete_wizard_rel, hr_employee_hr_leave_allocation_generate_multi_wizard_rel, hr_employee_hr_leave_generate_multi_wizard_rel, hr_expense_approve_duplicate, hr_expense_hr_expense_approve_duplicate_rel, hr_expense_hr_expense_refuse_wizard_rel, hr_expense_refuse_wizard, hr_expense_split, hr_expense_split_wizard, hr_export_work_entries, hr_export_work_entries_employee, hr_export_work_entries_employee_hr_version_rel, hr_holidays_cancel_leave, hr_holidays_summary_employee, hr_leave_allocation_generate_multi_wizard, hr_leave_generate_multi_wizard, hr_work_entry_type_load_public_holiday_wizard_line_rel, ir_demo, ir_demo_failure, ir_demo_failure_wizard, load_public_holiday_wizard, load_public_holiday_wizard_line, lot_label_layout, lot_label_layout_stock_lot_rel, lot_label_layout_stock_move_line_rel, mail_activity_plan_mail_activity_schedule_rel, mail_activity_schedule, mail_activity_schedule_line, mail_activity_todo_create, mail_blacklist_remove, mail_compose_message, mail_compose_message_ir_attachments_rel, mail_compose_message_res_partner_cc_rel, mail_compose_message_res_partner_rel, mail_followers_edit, mail_followers_edit_res_partner_rel, mail_template_mail_template_reset_rel, mail_template_preview, mail_template_reset, merge_opportunity_rel, payment_capture_wizard, payment_capture_wizard_payment_transaction_rel, payment_link_wizard, payment_refund_wizard, phone_blacklist_remove, picking_label_type, picking_label_type_stock_picking_rel, portal_share, portal_share_res_partner_rel, portal_wizard, portal_wizard_res_partner_rel, portal_wizard_user, privacy_lookup_wizard, privacy_lookup_wizard_line, product_label_layout, product_label_layout_product_product_rel, product_label_layout_product_template_rel, product_label_layout_product_uom_rel, product_label_layout_stock_move_rel, product_replenish, product_supplierinfo_stock_replenishment_info_rel, project_project_project_task_type_delete_wizard_rel, project_project_stage_delete_wizard, project_project_stage_project_project_stage_delete_wizard_rel, project_share_collaborator_wizard, project_share_wizard, project_share_wizard_res_partner_rel, project_task_type_delete_wizard, project_task_type_project_task_type_delete_wizard_rel, project_template_create_wizard, project_template_role_to_users_map, project_template_role_to_users_map_res_users_rel, registration_editor, registration_editor_line, rel_modules_langexport, res_config, res_config_settings, res_lang_install_rel, res_partner_task_share_wizard_rel, res_users_apikeys_description, res_users_identitycheck, reset_view_arch_wizard, sale_advance_payment_inv, sale_advance_payment_inv_sale_order_rel, sale_mass_cancel_orders, sale_order_discount, sale_order_mass_cancel_wizard_rel, server_action_history_wizard, sms_account_code, sms_account_phone, sms_account_sender, sms_composer, sms_template_preview, sms_template_reset, sms_template_sms_template_reset_rel, stock_add_to_wave, stock_add_to_wave_stock_move_line_rel, stock_add_to_wave_stock_picking_rel, stock_backorder_confirmation, stock_backorder_confirmation_line, stock_conflict_quant_rel, stock_inventory_adjustment_name, stock_inventory_adjustment_name_stock_quant_rel, stock_inventory_conflict, stock_inventory_conflict_stock_quant_rel, stock_inventory_warning, stock_inventory_warning_stock_quant_rel, stock_location_label_layout, stock_move_line_stock_package_destination_rel, stock_move_line_stock_put_in_pack_rel, stock_orderpoint_snooze, stock_orderpoint_snooze_stock_warehouse_orderpoint_rel, stock_orderpoint_suggest, stock_orderpoint_suggest_stock_warehouse_orderpoint_rel, stock_package_destination, stock_package_label_layout, stock_package_stock_put_in_pack_rel, stock_picking_backorder_rel, stock_picking_sms_rel, stock_picking_stock_zero_demand_confirmation_rel, stock_picking_to_batch, stock_picking_type_label_layout, stock_put_in_pack, stock_quant_relocate, stock_quant_stock_quant_relocate_rel, stock_quant_stock_request_count_rel, stock_replenishment_info, stock_replenishment_option, stock_request_count, stock_route_stock_rules_report_rel, stock_rules_report, stock_rules_report_stock_warehouse_rel, stock_traceability_report, stock_warn_insufficient_qty_scrap, stock_zero_demand_confirmation, summary_emp_rel, survey_invite, survey_invite_partner_ids, survey_mail_compose_message_ir_attachments_rel, task_share_wizard, update_product_attribute_value, validate_account_move, wizard_ir_model_menu_create; confirm none must survive cutover
6. **no_access_evidence** (298): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged  
   Applies to: account_account, account_account_tag, account_analytic_account, account_analytic_applicability, account_analytic_distribution_model, account_analytic_line, account_analytic_plan, account_bank_statement and 290 more
7. **cascade_into_embed** (175): account_account_res_company_rel is embedded in account_account, but deleting a res_company row cascades to its account_account_res_company_rel: the app must pull them from every account_account document, or keep account_account_res_company_rel separate  
   Applies to: account_account_res_company_rel, account_account_tax_default_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_analytic_line_stock_move_rel, account_bank_statement_ir_attachment_rel, account_cash_rounding_account_payment_method_line_rel and 167 more
8. **fanout_unmeasured** (130): account_account_tax_default_rel has no rows per account_account in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding  
   Applies to: account_account_tax_default_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_analytic_line_stock_move_rel, account_cash_rounding_account_payment_method_line_rel, account_cash_rounding_res_currency_rel, account_cash_rounding_res_partner_category_rel and 122 more
9. **lob** (88): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)  
   Applies to: account_account, account_analytic_plan, account_journal, account_move, account_move_line, account_report_expression, calendar_alarm, calendar_event and 80 more
10. **source_index_not_exercised** (57): source index not exercised by any confirmed access pattern; keep or drop  
   Applies to: account_tax, account_tax_alternatives, account_tax_filiation_rel, account_tax_purchase_order_line_rel, account_tax_sale_order_line_rel, account_tax_sale_order_template_line_rel, expense_tax, product_supplier_taxes_rel and 35 more
11. **nullable_unique_key** (39): source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
12. **extended_reference_candidate** (9): app reads hr_expense with every expense_tax: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference  
   Applies to: expense_tax, fleet_vehicle_vehicle_tag_rel, lunch_alert_lunch_location_rel, lunch_location_lunch_supplier_rel, lunch_order_topping, maintenance_request_res_users_rel, maintenance_stage_maintenance_team_rel, survey_question_answer and 1 more
13. **single_valued_index_key** (3): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan  
   Applies to: fleet_vehicle_model, survey_question, survey_question_answer
14. **date_as_string** (2)  
   Applies to: hr_leave_accrual_plan, mail_template
15. **repeating_group** (2): collapse each numbered series into one array field; needs app evidence, mapped 1:1 until then  
   Applies to: ir_model_fields, lunch_supplier
16. **csv_list** (1)  
   Applies to: res_company

**Answers template.** Copy it to `.migration/answers.txt` and replace each `<...>` with who decided and why. `accept` keeps the embeds and copied fields a rule proposed (from the schema alone), `reject` makes its embeds references, `except` exempts tables, `close` settles every question of a kind. Delete lines you are not ready to answer.

```
accept junction_array: <who said so, and why>  # 183 tables: account_account_account_tag, account_account_res_company_rel, account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel, account_account_tax_default_rel, account_analytic_line_stock_move_rel, account_bank_statement_ir_attachment_rel and 175 more
accept ownership: <who said so, and why>  # 22 tables: account_analytic_line_calendar_employee, account_fiscal_position_account, account_report_external_value, auth_totp_device, discuss_channel_last_interest_update, discuss_voice_metadata, event_registration_answer, hr_leave_accrual_level and 14 more
close many_to_many_junction: <who said so, and why>  # 191 questions
close embed_unbounded: <who said so, and why>  # 22 questions
close embed_null_pointer_rows: <who said so, and why>  # 5 questions
close date_format_assumed: <who said so, and why>  # 3 questions
close transient_tables: <who said so, and why>  # 1 questions
close no_access_evidence: <who said so, and why>  # 298 questions
close cascade_into_embed: <who said so, and why>  # 175 questions
close fanout_unmeasured: <who said so, and why>  # 130 questions
close lob: <who said so, and why>  # 88 questions
close source_index_not_exercised: <who said so, and why>  # 57 questions
close nullable_unique_key: <who said so, and why>  # 39 questions
close extended_reference_candidate: <who said so, and why>  # 9 questions
close single_valued_index_key: <who said so, and why>  # 3 questions
close date_as_string: <who said so, and why>  # 2 questions
close repeating_group: <who said so, and why>  # 2 questions
close csv_list: <who said so, and why>  # 1 questions
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
  isVehicleAccount: bool,  // is_vehicle_account
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
- account_account → account_account, account_analytic_line, account_journal, account_move_line, account_payment, account_payment_method_line, account_reconcile_model_line, account_tax, account_tax_repartition_line, res_company, stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, res_currency → account_account: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account → account_account_account_tag, account_account_res_company_rel, account_account_tax_default_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_account_tag → account_account_account_tag: **reference**, a link table, embedded on the other side (assumed)
- res_company → account_account_res_company_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax → account_account_tax_default_rel: **reference**, a link table, embedded on the other side (assumed)
- account_account → account_fiscal_position_account: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_account → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (5):
- **fanout_unmeasured** (account_account_tax_default_rel): account_account_tax_default_rel has no rows per account_account in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_account_res_company_rel): account_account_res_company_rel is embedded in account_account, but deleting a res_company row cascades to its account_account_res_company_rel: the app must pull them from every account_account document, or keep account_account_res_company_rel separate
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
- res_country, res_users → account_account_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account_tag → account_account_tag_account_move_line_rel, account_account_tag_account_tax_repartition_line_rel, account_account_tag_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_move_line → account_account_tag_account_move_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax_repartition_line → account_account_tag_account_tax_repartition_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → account_account_tag_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (8):
- **fanout_unmeasured** (account_account_tag_account_move_line_rel): account_account_tag_account_move_line_rel has no rows per account_account_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_account_tag_account_tax_repartition_line_rel): account_account_tag_account_tax_repartition_line_rel has no rows per account_account_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_account_tag_product_template_rel): account_account_tag_product_template_rel has no rows per account_account_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_account_tag_account_move_line_rel): account_account_tag_account_move_line_rel is embedded in account_account_tag, but deleting a account_move_line row cascades to its account_account_tag_account_move_line_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_account_move_line_rel separate
- **cascade_into_embed** (account_account_tag_account_tax_repartition_line_rel): account_account_tag_account_tax_repartition_line_rel is embedded in account_account_tag, but deleting a account_tax_repartition_line row cascades to its account_account_tag_account_tax_repartition_line_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_account_tax_repartition_line_rel separate
- **cascade_into_embed** (account_account_tag_product_template_rel): account_account_tag_product_template_rel is embedded in account_account_tag, but deleting a product_template row cascades to its account_account_tag_product_template_rel: the app must pull them from every account_account_tag document, or keep account_account_tag_product_template_rel separate
- **no_access_evidence** (account_account_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

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
  taskId: int,  // task_id
  parentTaskId: int,  // parent_task_id
  projectId: int,  // project_id
  employeeId: int,  // employee_id
  departmentId: int,  // department_id
  managerId: int,  // manager_id
  sequence: int,  // sequence
  reinvoiceMoveId: int,  // reinvoice_move_id
  soLine: int,  // so_line
  orderId: int,  // order_id
  holidayId: int,  // holiday_id
  globalLeaveId: int,  // global_leave_id
  billableType: string,  // billable_type
  categoryReport: string,  // category_report
  isSoLineEdited: bool,  // is_so_line_edited
  stockMoveRel: [{  // account_analytic_line_stock_move_rel, 1:N assumed
    stockMoveId: int,  // stock_move_id
  }],
}
```

Why:
- account_analytic_account, res_company, res_users, res_currency, hr_department, hr_employee, account_account, resource_calendar_leaves, hr_leave, account_journal, account_move_line, sale_order, project_task, res_partner, product_product, uom_uom, project_project, account_move, sale_order_line → account_analytic_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_analytic_line → account_analytic_line_stock_move_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_move → account_analytic_line_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (account_analytic_line_stock_move_rel): account_analytic_line_stock_move_rel has no rows per account_analytic_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_analytic_line_stock_move_rel): account_analytic_line_stock_move_rel is embedded in account_analytic_line, but deleting a stock_move row cascades to its account_analytic_line_stock_move_rel: the app must pull them from every account_analytic_line document, or keep account_analytic_line_stock_move_rel separate
- **no_access_evidence** (account_analytic_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
- account_bank_statement → account_bank_statement_line, account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **cascade_into_embed** (account_bank_statement_ir_attachment_rel): account_bank_statement_ir_attachment_rel is embedded in account_bank_statement, but deleting a ir_attachment row cascades to its account_bank_statement_ir_attachment_rel: the app must pull them from every account_bank_statement document, or keep account_bank_statement_ir_attachment_rel separate
- **no_access_evidence** (account_bank_statement): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (7):
- **fanout_unmeasured** (account_cash_rounding_account_payment_method_line_rel): account_cash_rounding_account_payment_method_line_rel has no rows per account_cash_rounding in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_cash_rounding_res_currency_rel): account_cash_rounding_res_currency_rel has no rows per account_cash_rounding in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_cash_rounding_res_partner_category_rel): account_cash_rounding_res_partner_category_rel has no rows per account_cash_rounding in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_cash_rounding_account_payment_method_line_rel): account_cash_rounding_account_payment_method_line_rel is embedded in account_cash_rounding, but deleting a account_payment_method_line row cascades to its account_cash_rounding_account_payment_method_line_rel: the app must pull them from every account_cash_rounding document, or keep account_cash_rounding_account_payment_method_line_rel separate
- **cascade_into_embed** (account_cash_rounding_res_currency_rel): account_cash_rounding_res_currency_rel is embedded in account_cash_rounding, but deleting a res_currency row cascades to its account_cash_rounding_res_currency_rel: the app must pull them from every account_cash_rounding document, or keep account_cash_rounding_res_currency_rel separate
- **cascade_into_embed** (account_cash_rounding_res_partner_category_rel): account_cash_rounding_res_partner_category_rel is embedded in account_cash_rounding, but deleting a res_partner_category row cascades to its account_cash_rounding_res_partner_category_rel: the app must pull them from every account_cash_rounding document, or keep account_cash_rounding_res_partner_category_rel separate
- **no_access_evidence** (account_cash_rounding): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
  account: [{  // account_fiscal_position_account, 1:N assumed
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
- account_fiscal_position → account_fiscal_position_account: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- account_fiscal_position → account_fiscal_position_account_tax_rel, account_fiscal_position_res_country_state_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_fiscal_position_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country_state → account_fiscal_position_res_country_state_rel: **reference**, a link table, embedded on the other side (assumed)
- account_fiscal_position → account_move, purchase_order, res_company, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (5):
- **fanout_unmeasured** (account_fiscal_position_account): account_fiscal_position_account has no rows per account_fiscal_position in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_fiscal_position_res_country_state_rel): account_fiscal_position_res_country_state_rel has no rows per account_fiscal_position in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_fiscal_position_account_tax_rel): account_fiscal_position_account_tax_rel is embedded in account_fiscal_position, but deleting a account_tax row cascades to its account_fiscal_position_account_tax_rel: the app must pull them from every account_fiscal_position document, or keep account_fiscal_position_account_tax_rel separate
- **cascade_into_embed** (account_fiscal_position_res_country_state_rel): account_fiscal_position_res_country_state_rel is embedded in account_fiscal_position, but deleting a res_country_state row cascades to its account_fiscal_position_res_country_state_rel: the app must pull them from every account_fiscal_position document, or keep account_fiscal_position_res_country_state_rel separate
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
- account_journal → account_analytic_line, account_bank_statement, account_bank_statement_line, account_move, account_move_line, account_payment, account_payment_method_line, res_company, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_alias, res_partner_bank, res_company, res_users, res_currency, account_account, ir_act_report_xml, account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_journal → account_journal_account_reconcile_model_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (4):
- **fanout_unmeasured** (account_journal_account_reconcile_model_rel): account_journal_account_reconcile_model_rel has no rows per account_journal in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_journal_account_reconcile_model_rel): account_journal_account_reconcile_model_rel is embedded in account_journal, but deleting a account_reconcile_model row cascades to its account_journal_account_reconcile_model_rel: the app must pull them from every account_journal document, or keep account_journal_account_reconcile_model_rel separate
- **no_access_evidence** (account_journal): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_journal): LOB column(s) sequence_override_regex measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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
- account_move → account_analytic_line, account_bank_statement_line, account_move, account_move_line, account_partial_reconcile, account_payment, res_company, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move → account_invoice_transaction_rel, account_move__account_payment, account_move_purchase_order_rel, adjusting_entries__account_move: **embed**, a link table, kept as an array on this side (assumed)
- payment_transaction → account_invoice_transaction_rel: **reference**, a link table, embedded on the other side (assumed)
- utm_campaign, res_partner, res_company, res_users, res_currency, account_fiscal_position, ir_attachment, account_cash_rounding, account_incoterms, account_payment_term, account_journal, utm_medium, account_payment, res_partner_bank, account_payment_method_line, utm_source, account_bank_statement_line, account_partial_reconcile, crm_team → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- purchase_order → account_move_purchase_order_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move → adjusting_entries__account_move, purchase_order_line_accrual_move_rel, sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_move → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (9):
- **fanout_unmeasured** (account_invoice_transaction_rel): account_invoice_transaction_rel has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_move__account_payment): account_move__account_payment has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_move_purchase_order_rel): account_move_purchase_order_rel has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (adjusting_entries__account_move): adjusting_entries__account_move has no rows per account_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_invoice_transaction_rel): account_invoice_transaction_rel is embedded in account_move, but deleting a payment_transaction row cascades to its account_invoice_transaction_rel: the app must pull them from every account_move document, or keep account_invoice_transaction_rel separate
- **cascade_into_embed** (account_move__account_payment): account_move__account_payment is embedded in account_move, but deleting a account_payment row cascades to its account_move__account_payment: the app must pull them from every account_move document, or keep account_move__account_payment separate
- **cascade_into_embed** (account_move_purchase_order_rel): account_move_purchase_order_rel is embedded in account_move, but deleting a purchase_order row cascades to its account_move_purchase_order_rel: the app must pull them from every account_move document, or keep account_move_purchase_order_rel separate
- **no_access_evidence** (account_move): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_move): LOB column(s) narration measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## accountMoveLine

From `account_move_line` with `account_move_line_account_tax_rel` embedded.

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
  vehicleId: int,  // vehicle_id
  expenseId: int,  // expense_id
  purchaseLineId: int,  // purchase_line_id
  isDownpayment: bool,  // is_downpayment
  stockMoveId: int,  // stock_move_id
  accountTaxRel: [{  // account_move_line_account_tax_rel, 1:N assumed
    accountTaxId: int,  // account_tax_id
  }],
}
```

Why:
- account_move_line → account_account_tag_account_move_line_rel, sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move_line → account_analytic_line, account_move_line, account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account, res_currency, res_company, res_users, hr_expense, account_full_reconcile, account_tax, account_journal, account_move, res_partner, account_payment, product_product, uom_uom, purchase_order_line, account_reconcile_model, account_bank_statement, account_bank_statement_line, stock_move, account_tax_group, account_tax_repartition_line, fleet_vehicle → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move_line → account_move_line_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_move_line_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move_line → fleet_vehicle_log_services: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (3):
- **cascade_into_embed** (account_move_line_account_tax_rel): account_move_line_account_tax_rel is embedded in account_move_line, but deleting a account_tax row cascades to its account_move_line_account_tax_rel: the app must pull them from every account_move_line document, or keep account_move_line_account_tax_rel separate
- **no_access_evidence** (account_move_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_move_line): LOB column(s) name measured max 56 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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
- account_payment → account_move, account_move_line, account_payment, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment → account_move__account_payment: **reference**, a link table, embedded on the other side (assumed)
- res_partner, res_company, res_users, res_currency, account_account, account_journal, ir_attachment, account_move, res_partner_bank, account_payment_method, account_payment_method_line, payment_token, payment_transaction → account_payment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment → account_payment_account_bank_statement_line_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (3):
- **fanout_unmeasured** (account_payment_account_bank_statement_line_rel): account_payment_account_bank_statement_line_rel has no rows per account_payment in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_payment_account_bank_statement_line_rel): account_payment_account_bank_statement_line_rel is embedded in account_payment, but deleting a account_bank_statement_line row cascades to its account_payment_account_bank_statement_line_rel: the app must pull them from every account_payment document, or keep account_payment_account_bank_statement_line_rel separate
- **no_access_evidence** (account_payment): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountPaymentMethodLine

From `account_payment_method_line` with `account_payment_method_line_res_company_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  paymentMethodId: int,  // payment_method_id
  paymentAccountId: int,  // payment_account_id
  journalId: int,  // journal_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  paymentProviderId: int,  // payment_provider_id
  resCompanyRel: [{  // account_payment_method_line_res_company_rel, 1:N assumed
    resCompanyId: int,  // res_company_id
  }],
}
```

Why:
- account_payment_method_line → account_cash_rounding_account_payment_method_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment_method_line → account_move, account_payment, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, account_journal, account_account, account_payment_method, payment_provider → account_payment_method_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_payment_method_line → account_payment_method_line_res_company_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_company → account_payment_method_line_res_company_rel: **reference**, a link table, embedded on the other side (assumed)
- account_payment_method_line → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (3):
- **fanout_unmeasured** (account_payment_method_line_res_company_rel): account_payment_method_line_res_company_rel has no rows per account_payment_method_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_payment_method_line_res_company_rel): account_payment_method_line_res_company_rel is embedded in account_payment_method_line, but deleting a res_company row cascades to its account_payment_method_line_res_company_rel: the app must pull them from every account_payment_method_line document, or keep account_payment_method_line_res_company_rel separate
- **no_access_evidence** (account_payment_method_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
  resPartnerRel: [{  // account_reconcile_model_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
}
```

Why:
- account_reconcile_model → account_journal_account_reconcile_model_rel: **reference**, a link table, embedded on the other side (assumed)
- account_reconcile_model → account_move_line, account_reconcile_model_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_partner, mail_activity_type → account_reconcile_model: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model → account_reconcile_model_res_partner_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → account_reconcile_model_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (account_reconcile_model_res_partner_rel): account_reconcile_model_res_partner_rel has no rows per account_reconcile_model in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (account_reconcile_model_res_partner_rel): account_reconcile_model_res_partner_rel is embedded in account_reconcile_model, but deleting a res_partner row cascades to its account_reconcile_model_res_partner_rel: the app must pull them from every account_reconcile_model document, or keep account_reconcile_model_res_partner_rel separate
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
- account_account, res_company, res_users, account_reconcile_model, res_partner → account_reconcile_model_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_reconcile_model_line → account_reconcile_model_line_account_tax_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_tax → account_reconcile_model_line_account_tax_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (account_reconcile_model_line_account_tax_rel): account_reconcile_model_line_account_tax_rel has no rows per account_reconcile_model_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
- res_country, res_users → account_report: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report → account_report, account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_act_window → account_report_column: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_report → account_report_column: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- account_report → account_report_section_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_report → account_report_section_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **fanout_unmeasured** (account_report_section_rel): account_report_section_rel has no rows per account_report in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
  accountReportExternalValue: [{  // account_report_external_value, 1:N assumed
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
- account_report_expression → account_report_external_value: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

Open questions (3):
- **fanout_unmeasured** (account_report_external_value): account_report_external_value has no rows per account_report_expression in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (account_report_expression): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_report_expression): LOB column(s) formula, subformula: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## accountTax

From `account_tax` with `account_tax_alternatives`, `account_tax_filiation_rel`, `account_tax_purchase_order_line_rel`, `account_tax_sale_order_line_rel`, `account_tax_sale_order_template_line_rel`, `expense_tax`, `product_supplier_taxes_rel`, `product_taxes_rel` embedded.

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
  saleOrderTemplateLineRel: [{  // account_tax_sale_order_template_line_rel, 1:N assumed
    saleOrderTemplateLineId: int,  // sale_order_template_line_id
  }],
  expenseTax: [{  // expense_tax, 1:N derived
    expenseId: int,  // expense_id
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
- account_tax → account_account_tax_default_rel, account_fiscal_position_account_tax_rel, account_move_line_account_tax_rel, account_reconcile_model_line_account_tax_rel, account_tax_alternatives, account_tax_filiation_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax → account_move_line, account_tax, account_tax_repartition_line, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account, res_company, res_country, res_users, res_city, l10n_us_res_county, res_country_state, account_tax_group → account_tax: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_tax → account_tax_alternatives, account_tax_filiation_rel, account_tax_purchase_order_line_rel, account_tax_sale_order_line_rel, account_tax_sale_order_template_line_rel, product_supplier_taxes_rel, product_taxes_rel: **embed**, a link table, kept as an array on this side (assumed)
- purchase_order_line → account_tax_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → account_tax_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_template_line → account_tax_sale_order_template_line_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_expense → expense_tax: **reference**, a link table, embedded on the other side (assumed)
- account_tax → expense_tax: **embed**, a link table, kept as an array on this side (derived)
- product_template → product_supplier_taxes_rel: **reference**, a link table, embedded on the other side (assumed)
- product_template → product_taxes_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (19):
- **fanout_unmeasured** (account_tax_filiation_rel): account_tax_filiation_rel has no rows per account_tax in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (account_tax_sale_order_template_line_rel): account_tax_sale_order_template_line_rel has no rows per account_tax in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (expense_tax): app reads hr_expense with every expense_tax: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (account_tax_purchase_order_line_rel): account_tax_purchase_order_line_rel is embedded in account_tax, but deleting a purchase_order_line row cascades to its account_tax_purchase_order_line_rel: the app must pull them from every account_tax document, or keep account_tax_purchase_order_line_rel separate
- **cascade_into_embed** (account_tax_sale_order_line_rel): account_tax_sale_order_line_rel is embedded in account_tax, but deleting a sale_order_line row cascades to its account_tax_sale_order_line_rel: the app must pull them from every account_tax document, or keep account_tax_sale_order_line_rel separate
- **cascade_into_embed** (account_tax_sale_order_template_line_rel): account_tax_sale_order_template_line_rel is embedded in account_tax, but deleting a sale_order_template_line row cascades to its account_tax_sale_order_template_line_rel: the app must pull them from every account_tax document, or keep account_tax_sale_order_template_line_rel separate
- **cascade_into_embed** (expense_tax): expense_tax is embedded in account_tax, but deleting a hr_expense row cascades to its expense_tax: the app must pull them from every account_tax document, or keep expense_tax separate
- **cascade_into_embed** (product_supplier_taxes_rel): product_supplier_taxes_rel is embedded in account_tax, but deleting a product_template row cascades to its product_supplier_taxes_rel: the app must pull them from every account_tax document, or keep product_supplier_taxes_rel separate
- **cascade_into_embed** (product_taxes_rel): product_taxes_rel is embedded in account_tax, but deleting a product_template row cascades to its product_taxes_rel: the app must pull them from every account_tax document, or keep product_taxes_rel separate
- **source_index_not_exercised** (account_tax): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_alternatives): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_filiation_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_purchase_order_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_sale_order_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (account_tax_sale_order_template_line_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (expense_tax): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_supplier_taxes_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (product_taxes_rel): source index not exercised by any confirmed access pattern; keep or drop

## calendarAlarm

From `calendar_alarm` with `calendar_alarm_calendar_event_rel` embedded.

```js
{
  _id: int,  // id
  duration: int,  // duration
  durationMinutes: int,  // duration_minutes
  mailTemplateId: int,  // mail_template_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  alarmType: string,  // alarm_type
  interval: string,  // interval
  name: object,  // name
  body: string,  // body
  notifyResponsible: bool,  // notify_responsible
  createDate: date,  // create_date
  writeDate: date,  // write_date
  smsTemplateId: int,  // sms_template_id
  calendarEventRel: [{  // calendar_alarm_calendar_event_rel, 1:N assumed
    calendarEventId: int,  // calendar_event_id
  }],
}
```

Why:
- res_users, mail_template, sms_template → calendar_alarm: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- calendar_alarm → calendar_alarm_calendar_event_rel: **embed**, a link table, kept as an array on this side (assumed)
- calendar_event → calendar_alarm_calendar_event_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **cascade_into_embed** (calendar_alarm_calendar_event_rel): calendar_alarm_calendar_event_rel is embedded in calendar_alarm, but deleting a calendar_event row cascades to its calendar_alarm_calendar_event_rel: the app must pull them from every calendar_alarm document, or keep calendar_alarm_calendar_event_rel separate
- **no_access_evidence** (calendar_alarm): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (calendar_alarm): LOB column(s) body measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## calendarEvent

From `calendar_event` with `calendar_event_res_partner_rel`, `meeting_category_rel` embedded.

```js
{
  _id: int,  // id
  calendarId: int,  // calendar_id
  userId: int,  // user_id
  videocallChannelId: int,  // videocall_channel_id
  resId: int,  // res_id
  resModelId: int,  // res_model_id
  recurrenceId: int,  // recurrence_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  location: string,  // location
  videocallLocation: string,  // videocall_location
  accessToken: string,  // access_token
  privacy: string,  // privacy
  showAs: string,  // show_as
  resModel: string,  // res_model
  startDate: date,  // start_date
  stopDate: date,  // stop_date
  description: string,  // description
  notes: string,  // notes
  isDraft: bool,  // is_draft
  active: bool,  // active
  allday: bool,  // allday
  recurrency: bool,  // recurrency
  followRecurrence: bool,  // follow_recurrence
  start: date,  // start
  stop: date,  // stop
  createDate: date,  // create_date
  writeDate: date,  // write_date
  duration: double,  // duration
  opportunityId: int,  // opportunity_id
  resPartnerRel: [{  // calendar_event_res_partner_rel, 1:N assumed
    resPartnerId: int,  // res_partner_id
  }],
  meetingCategoryRel: [{  // meeting_category_rel, 1:N assumed
    typeId: int,  // type_id
  }],
}
```

Why:
- calendar_event → calendar_alarm_calendar_event_rel: **reference**, a link table, embedded on the other side (assumed)
- calendar_event → calendar_attendee, calendar_recurrence, hr_leave, mail_activity: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- calendar_calendar, res_users, crm_lead, calendar_recurrence, ir_model, discuss_channel → calendar_event: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- calendar_event → calendar_event_res_partner_rel, meeting_category_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → calendar_event_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- calendar_event_type → meeting_category_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **cascade_into_embed** (calendar_event_res_partner_rel): calendar_event_res_partner_rel is embedded in calendar_event, but deleting a res_partner row cascades to its calendar_event_res_partner_rel: the app must pull them from every calendar_event document, or keep calendar_event_res_partner_rel separate
- **cascade_into_embed** (meeting_category_rel): meeting_category_rel is embedded in calendar_event, but deleting a calendar_event_type row cascades to its meeting_category_rel: the app must pull them from every calendar_event document, or keep meeting_category_rel separate
- **no_access_evidence** (calendar_event): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (calendar_event): LOB column(s) description, notes measured max 438 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## crmIapLeadIndustry

From `crm_iap_lead_industry` with `crm_iap_lead_industry_crm_iap_lead_mining_request_rel` embedded.

```js
{
  _id: int,  // id
  sicGroup: int,  // sic_group
  divisionId: int,  // division_id
  color: int,  // color
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  crmIapLeadMiningRequestRel: [{  // crm_iap_lead_industry_crm_iap_lead_mining_request_rel, 1:N assumed
    crmIapLeadMiningRequestId: int,  // crm_iap_lead_mining_request_id
  }],
}
```

Why:
- res_users, crm_iap_lead_industry_division → crm_iap_lead_industry: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_iap_lead_mining_request → crm_iap_lead_industry_crm_iap_lead_mining_request_rel: **reference**, a link table, embedded on the other side (assumed)
- crm_iap_lead_industry → crm_iap_lead_industry_crm_iap_lead_mining_request_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (3):
- **fanout_unmeasured** (crm_iap_lead_industry_crm_iap_lead_mining_request_rel): crm_iap_lead_industry_crm_iap_lead_mining_request_rel has no rows per crm_iap_lead_industry in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (crm_iap_lead_industry_crm_iap_lead_mining_request_rel): crm_iap_lead_industry_crm_iap_lead_mining_request_rel is embedded in crm_iap_lead_industry, but deleting a crm_iap_lead_mining_request row cascades to its crm_iap_lead_industry_crm_iap_lead_mining_request_rel: the app must pull them from every crm_iap_lead_industry document, or keep crm_iap_lead_industry_crm_iap_lead_mining_request_rel separate
- **no_access_evidence** (crm_iap_lead_industry): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmIapLeadMiningRequest

From `crm_iap_lead_mining_request` with `crm_iap_lead_mining_request_crm_tag_rel`, `crm_iap_lead_mining_request_res_country_rel`, `crm_iap_lead_mining_request_res_country_state_rel` embedded.

```js
{
  _id: int,  // id
  leadNumber: int,  // lead_number
  teamId: int,  // team_id
  userId: int,  // user_id
  companySizeMin: int,  // company_size_min
  companySizeMax: int,  // company_size_max
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  state: string,  // state
  errorType: string,  // error_type
  leadType: string,  // lead_type
  filterOnSize: bool,  // filter_on_size
  createDate: date,  // create_date
  writeDate: date,  // write_date
  crmTagRel: [{  // crm_iap_lead_mining_request_crm_tag_rel, 1:N assumed
    crmTagId: int,  // crm_tag_id
  }],
  resCountryRel: [{  // crm_iap_lead_mining_request_res_country_rel, 1:N assumed
    resCountryId: int,  // res_country_id
  }],
  resCountryStateRel: [{  // crm_iap_lead_mining_request_res_country_state_rel, 1:N assumed
    resCountryStateId: int,  // res_country_state_id
  }],
}
```

Why:
- crm_iap_lead_mining_request → crm_iap_lead_industry_crm_iap_lead_mining_request_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, crm_team → crm_iap_lead_mining_request: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_iap_lead_mining_request → crm_iap_lead_mining_request_crm_tag_rel, crm_iap_lead_mining_request_res_country_rel, crm_iap_lead_mining_request_res_country_state_rel: **embed**, a link table, kept as an array on this side (assumed)
- crm_tag → crm_iap_lead_mining_request_crm_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country → crm_iap_lead_mining_request_res_country_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country_state → crm_iap_lead_mining_request_res_country_state_rel: **reference**, a link table, embedded on the other side (assumed)
- crm_iap_lead_mining_request → crm_lead: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (7):
- **fanout_unmeasured** (crm_iap_lead_mining_request_crm_tag_rel): crm_iap_lead_mining_request_crm_tag_rel has no rows per crm_iap_lead_mining_request in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (crm_iap_lead_mining_request_res_country_rel): crm_iap_lead_mining_request_res_country_rel has no rows per crm_iap_lead_mining_request in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (crm_iap_lead_mining_request_res_country_state_rel): crm_iap_lead_mining_request_res_country_state_rel has no rows per crm_iap_lead_mining_request in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (crm_iap_lead_mining_request_crm_tag_rel): crm_iap_lead_mining_request_crm_tag_rel is embedded in crm_iap_lead_mining_request, but deleting a crm_tag row cascades to its crm_iap_lead_mining_request_crm_tag_rel: the app must pull them from every crm_iap_lead_mining_request document, or keep crm_iap_lead_mining_request_crm_tag_rel separate
- **cascade_into_embed** (crm_iap_lead_mining_request_res_country_rel): crm_iap_lead_mining_request_res_country_rel is embedded in crm_iap_lead_mining_request, but deleting a res_country row cascades to its crm_iap_lead_mining_request_res_country_rel: the app must pull them from every crm_iap_lead_mining_request document, or keep crm_iap_lead_mining_request_res_country_rel separate
- **cascade_into_embed** (crm_iap_lead_mining_request_res_country_state_rel): crm_iap_lead_mining_request_res_country_state_rel is embedded in crm_iap_lead_mining_request, but deleting a res_country_state row cascades to its crm_iap_lead_mining_request_res_country_state_rel: the app must pull them from every crm_iap_lead_mining_request document, or keep crm_iap_lead_mining_request_res_country_state_rel separate
- **no_access_evidence** (crm_iap_lead_mining_request): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmLead

From `crm_lead` with `crm_lead_event_registration_rel` embedded.

```js
{
  _id: int,  // id
  campaignId: int,  // campaign_id
  sourceId: int,  // source_id
  mediumId: int,  // medium_id
  messageBounce: int,  // message_bounce
  userId: int,  // user_id
  teamId: int,  // team_id
  companyId: int,  // company_id
  stageId: int,  // stage_id
  color: int,  // color
  recurringPlan: int,  // recurring_plan
  partnerId: int,  // partner_id
  langId: int,  // lang_id
  stateId: int,  // state_id
  countryId: int,  // country_id
  lostReasonId: int,  // lost_reason_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  utmReference: string,  // utm_reference
  phoneSanitized: string,  // phone_sanitized
  emailNormalized: string,  // email_normalized
  name: string,  // name
  referred: string,  // referred
  type: string,  // type
  priority: string,  // priority
  contactName: string,  // contact_name
  partnerName: string,  // partner_name
  function: string,  // function
  emailFrom: string,  // email_from
  emailDomainCriterion: string,  // email_domain_criterion
  phone: string,  // phone
  phoneState: string,  // phone_state
  emailState: string,  // email_state
  website: string,  // website
  street: string,  // street
  street2: string,  // street2
  zip: string,  // zip
  city: string,  // city
  wonStatus: string,  // won_status
  dateDeadline: date,  // date_deadline
  durationTracking: object,  // duration_tracking
  leadProperties: object,  // lead_properties
  description: string,  // description
  expectedRevenue: decimal,  // expected_revenue
  proratedRevenue: decimal,  // prorated_revenue
  recurringRevenue: decimal,  // recurring_revenue
  recurringRevenueMonthly: decimal,  // recurring_revenue_monthly
  recurringRevenueMonthlyProrated: decimal,  // recurring_revenue_monthly_prorated
  recurringRevenueProrated: decimal,  // recurring_revenue_prorated
  active: bool,  // active
  dateClosed: date,  // date_closed
  dateAutomationLast: date,  // date_automation_last
  dateOpen: date,  // date_open
  dateLastStageUpdate: date,  // date_last_stage_update
  dateConversion: date,  // date_conversion
  createDate: date,  // create_date
  writeDate: date,  // write_date
  dayOpen: double,  // day_open
  dayClose: double,  // day_close
  probability: double,  // probability
  automatedProbability: double,  // automated_probability
  eventLeadRuleId: int,  // event_lead_rule_id
  eventId: int,  // event_id
  revealId: string,  // reveal_id
  iapEnrichDone: bool,  // iap_enrich_done
  leadMiningRequestId: int,  // lead_mining_request_id
  eventRegistrationRel: [{  // crm_lead_event_registration_rel, 1:N assumed
    eventRegistrationId: int,  // event_registration_id
  }],
}
```

Why:
- crm_lead → calendar_event, project_project, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- utm_campaign, res_company, res_country, res_users, event_event, event_lead_rule, res_lang, crm_iap_lead_mining_request, crm_lost_reason, utm_medium, res_partner, crm_recurring_plan, utm_source, crm_stage, res_country_state, crm_team → crm_lead: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_lead → crm_lead_event_registration_rel: **embed**, a link table, kept as an array on this side (assumed)
- event_registration → crm_lead_event_registration_rel: **reference**, a link table, embedded on the other side (assumed)
- crm_lead → crm_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- crm_lead → survey_user_input: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (3):
- **cascade_into_embed** (crm_lead_event_registration_rel): crm_lead_event_registration_rel is embedded in crm_lead, but deleting a event_registration row cascades to its crm_lead_event_registration_rel: the app must pull them from every crm_lead document, or keep crm_lead_event_registration_rel separate
- **no_access_evidence** (crm_lead): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (crm_lead): LOB column(s) description measured max 106 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## crmStage

From `crm_stage` with `crm_stage_crm_team_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  rottingThresholdDays: int,  // rotting_threshold_days
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  requirements: string,  // requirements
  isWon: bool,  // is_won
  fold: bool,  // fold
  createDate: date,  // create_date
  writeDate: date,  // write_date
  crmTeamRel: [{  // crm_stage_crm_team_rel, 1:N assumed
    crmTeamId: int,  // crm_team_id
  }],
}
```

Why:
- crm_stage → crm_lead: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → crm_stage: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_stage → crm_stage_crm_team_rel: **embed**, a link table, kept as an array on this side (assumed)
- crm_team → crm_stage_crm_team_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (crm_stage_crm_team_rel): crm_stage_crm_team_rel has no rows per crm_stage in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (crm_stage): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (crm_stage): LOB column(s) requirements measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## crmTag

From `crm_tag` with `crm_tag_event_lead_rule_rel`, `crm_tag_rel` embedded.

```js
{
  _id: int,  // id
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  eventLeadRuleRel: [{  // crm_tag_event_lead_rule_rel, 1:N assumed
    eventLeadRuleId: int,  // event_lead_rule_id
  }],
  rel: [{  // crm_tag_rel, 1:N assumed
    leadId: int,  // lead_id
  }],
}
```

Why:
- crm_tag → crm_iap_lead_mining_request_crm_tag_rel, sale_order_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → crm_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_tag → crm_tag_event_lead_rule_rel, crm_tag_rel: **embed**, a link table, kept as an array on this side (assumed)
- event_lead_rule → crm_tag_event_lead_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- crm_lead → crm_tag_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **cascade_into_embed** (crm_tag_event_lead_rule_rel): crm_tag_event_lead_rule_rel is embedded in crm_tag, but deleting a event_lead_rule row cascades to its crm_tag_event_lead_rule_rel: the app must pull them from every crm_tag document, or keep crm_tag_event_lead_rule_rel separate
- **cascade_into_embed** (crm_tag_rel): crm_tag_rel is embedded in crm_tag, but deleting a crm_lead row cascades to its crm_tag_rel: the app must pull them from every crm_tag document, or keep crm_tag_rel separate
- **no_access_evidence** (crm_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmTeam

From `crm_team` with `crm_lead_scoring_frequency`, `crm_team_sale_order_template_rel`, `team_favorite_user_rel` embedded.

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
  aliasId: int,  // alias_id
  assignmentDomain: string,  // assignment_domain
  leadPropertiesDefinition: object,  // lead_properties_definition
  useLeads: bool,  // use_leads
  useOpportunities: bool,  // use_opportunities
  assignmentOptout: bool,  // assignment_optout
  crmLeadScoringFrequency: [{  // crm_lead_scoring_frequency, 1:N derived
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    variable: string,  // variable
    value: string,  // value
    wonCount: decimal,  // won_count
    lostCount: decimal,  // lost_count
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  saleOrderTemplateRel: [{  // crm_team_sale_order_template_rel, 1:N assumed
    saleOrderTemplateId: int,  // sale_order_template_id
  }],
  teamFavoriteUserRel: [{  // team_favorite_user_rel, 1:N assumed
    userId: int,  // user_id
  }],
}
```

Why:
- crm_team → account_move, crm_iap_lead_mining_request, crm_lead, crm_team_member, event_lead_rule, res_users, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → crm_lead_scoring_frequency: **reference**, it is embedded under another parent; this one is referenced (derived)
- crm_team → crm_lead_scoring_frequency: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- crm_team → crm_stage_crm_team_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_alias, res_company, res_users → crm_team: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- crm_team → crm_team_sale_order_template_rel, team_favorite_user_rel: **embed**, a link table, kept as an array on this side (assumed)
- sale_order_template → crm_team_sale_order_template_rel: **reference**, a link table, embedded on the other side (assumed)
- crm_team → survey_survey: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_users → team_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (crm_team_sale_order_template_rel): crm_team_sale_order_template_rel has no rows per crm_team in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (crm_team_sale_order_template_rel): crm_team_sale_order_template_rel is embedded in crm_team, but deleting a sale_order_template row cascades to its crm_team_sale_order_template_rel: the app must pull them from every crm_team document, or keep crm_team_sale_order_template_rel separate
- **cascade_into_embed** (team_favorite_user_rel): team_favorite_user_rel is embedded in crm_team, but deleting a res_users row cascades to its team_favorite_user_rel: the app must pull them from every crm_team document, or keep team_favorite_user_rel separate
- **no_access_evidence** (crm_team): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
  kpiCrmLeadCreated: bool,  // kpi_crm_lead_created
  kpiCrmOpportunitiesWon: bool,  // kpi_crm_opportunities_won
  kpiNbrOfRegistrations: bool,  // kpi_nbr_of_registrations
  kpiProjectTaskOpened: bool,  // kpi_project_task_opened
  kpiStockDeliveryCount: bool,  // kpi_stock_delivery_count
  kpiStockReceiptCount: bool,  // kpi_stock_receipt_count
  kpiNbrOfAnswers: bool,  // kpi_nbr_of_answers
  kpiNbrOfCertifiedParticipants: bool,  // kpi_nbr_of_certified_participants
  kpiAllSaleTotal: bool,  // kpi_all_sale_total
  resUsersRel: [{  // digest_digest_res_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- res_company, res_users → digest_digest: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- digest_digest → digest_digest_res_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → digest_digest_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (digest_digest_res_users_rel): digest_digest_res_users_rel is embedded in digest_digest, but deleting a res_users row cascades to its digest_digest_res_users_rel: the app must pull them from every digest_digest document, or keep digest_digest_res_users_rel separate
- **no_access_evidence** (digest_digest): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (3):
- **fanout_unmeasured** (digest_tip_res_users_rel): digest_tip_res_users_rel has no rows per digest_tip in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (digest_tip_res_users_rel): digest_tip_res_users_rel is embedded in digest_tip, but deleting a res_users row cascades to its digest_tip_res_users_rel: the app must pull them from every digest_tip document, or keep digest_tip_res_users_rel separate
- **no_access_evidence** (digest_tip): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (2):
- **no_access_evidence** (discuss_call_history): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## discussChannel

From `discuss_channel` with `discuss_channel_last_interest_update`, `discuss_channel_hr_department_rel`, `discuss_channel_res_groups_rel` embedded.

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
  hrDepartmentRel: [{  // discuss_channel_hr_department_rel, 1:N assumed
    hrDepartmentId: int,  // hr_department_id
  }],
  resGroupsRel: [{  // discuss_channel_res_groups_rel, 1:N assumed
    resGroupsId: int,  // res_groups_id
  }],
}
```

Why:
- discuss_channel → calendar_event, discuss_call_history, discuss_channel, discuss_channel_member, discuss_channel_rtc_session, gamification_challenge: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, discuss_category, mail_message, res_groups → discuss_channel: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_channel → discuss_channel_hr_department_rel, discuss_channel_res_groups_rel: **embed**, a link table, kept as an array on this side (assumed)
- hr_department → discuss_channel_hr_department_rel: **reference**, a link table, embedded on the other side (assumed)
- discuss_channel → discuss_channel_last_interest_update: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_groups → discuss_channel_res_groups_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (8):
- **fanout_unmeasured** (discuss_channel_last_interest_update): discuss_channel_last_interest_update has no rows per discuss_channel in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (discuss_channel_hr_department_rel): discuss_channel_hr_department_rel has no rows per discuss_channel in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (discuss_channel_hr_department_rel): discuss_channel_hr_department_rel is embedded in discuss_channel, but deleting a hr_department row cascades to its discuss_channel_hr_department_rel: the app must pull them from every discuss_channel document, or keep discuss_channel_hr_department_rel separate
- **cascade_into_embed** (discuss_channel_res_groups_rel): discuss_channel_res_groups_rel is embedded in discuss_channel, but deleting a res_groups row cascades to its discuss_channel_res_groups_rel: the app must pull them from every discuss_channel document, or keep discuss_channel_res_groups_rel separate
- **no_access_evidence** (discuss_channel): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (discuss_channel): LOB column(s) description measured max 76 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## eventEvent

From `event_event` with `event_event_event_question_rel`, `event_event_event_tag_rel` embedded.

```js
{
  _id: int,  // id
  userId: int,  // user_id
  companyId: int,  // company_id
  organizerId: int,  // organizer_id
  eventTypeId: int,  // event_type_id
  stageId: int,  // stage_id
  seatsMax: int,  // seats_max
  addressId: int,  // address_id
  countryId: int,  // country_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  kanbanState: string,  // kanban_state
  dateTz: string,  // date_tz
  eventUrl: string,  // event_url
  lang: string,  // lang
  badgeFormat: string,  // badge_format
  name: object,  // name
  description: object,  // description
  registrationPropertiesDefinition: object,  // registration_properties_definition
  ticketInstructions: object,  // ticket_instructions
  note: string,  // note
  active: bool,  // active
  seatsLimited: bool,  // seats_limited
  isMultiSlots: bool,  // is_multi_slots
  dateBegin: date,  // date_begin
  dateEnd: date,  // date_end
  createDate: date,  // create_date
  writeDate: date,  // write_date
  eventQuestionRel: [{  // event_event_event_question_rel, 1:N assumed
    eventQuestionId: int,  // event_question_id
  }],
  eventTagRel: [{  // event_event_event_tag_rel, 1:N assumed
    eventTagId: int,  // event_tag_id
  }],
}
```

Why:
- event_event → crm_lead, event_event_ticket, event_lead_request, event_lead_rule, event_mail, event_registration, event_slot, hr_resume_line, sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner, res_company, res_country, res_users, event_type, event_stage → event_event: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_event → event_event_event_question_rel, event_event_event_tag_rel: **embed**, a link table, kept as an array on this side (assumed)
- event_question → event_event_event_question_rel: **reference**, a link table, embedded on the other side (assumed)
- event_tag → event_event_event_tag_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **cascade_into_embed** (event_event_event_question_rel): event_event_event_question_rel is embedded in event_event, but deleting a event_question row cascades to its event_event_event_question_rel: the app must pull them from every event_event document, or keep event_event_event_question_rel separate
- **cascade_into_embed** (event_event_event_tag_rel): event_event_event_tag_rel is embedded in event_event, but deleting a event_tag row cascades to its event_event_event_tag_rel: the app must pull them from every event_event document, or keep event_event_event_tag_rel separate
- **no_access_evidence** (event_event): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (event_event): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## eventEventTicket

From `event_event_ticket` with `event_event_ticket_product_product_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  eventTypeId: int,  // event_type_id
  seatsMax: int,  // seats_max
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  eventId: int,  // event_id
  entryLimit: int,  // entry_limit
  limitMaxPerOrder: int,  // limit_max_per_order
  color: string,  // color
  name: object,  // name
  description: object,  // description
  seatsLimited: bool,  // seats_limited
  createDate: date,  // create_date
  writeDate: date,  // write_date
  startSaleDatetime: date,  // start_sale_datetime
  endSaleDatetime: date,  // end_sale_datetime
  productId: int,  // product_id
  price: decimal,  // price
  productProductRel: [{  // event_event_ticket_product_product_rel, 1:N assumed
    productProductId: int,  // product_product_id
  }],
}
```

Why:
- res_users, event_event, event_type, product_product → event_event_ticket: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_event_ticket → event_event_ticket_product_product_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_product → event_event_ticket_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- event_event_ticket → event_registration, sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **fanout_unmeasured** (event_event_ticket_product_product_rel): event_event_ticket_product_product_rel has no rows per event_event_ticket in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (event_event_ticket_product_product_rel): event_event_ticket_product_product_rel is embedded in event_event_ticket, but deleting a product_product row cascades to its event_event_ticket_product_product_rel: the app must pull them from every event_event_ticket document, or keep event_event_ticket_product_product_rel separate
- **no_access_evidence** (event_event_ticket): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventLeadRequest

From `event_lead_request` with `event_lead_request_event_lead_rule_rel` embedded.

```js
{
  _id: int,  // id
  eventId: int,  // event_id
  processedRegistrationId: int,  // processed_registration_id
  eventLeadRuleRel: [{  // event_lead_request_event_lead_rule_rel, 1:N assumed
    eventLeadRuleId: int,  // event_lead_rule_id
  }],
}
```

Why:
- event_event → event_lead_request: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_lead_request → event_lead_request_event_lead_rule_rel: **embed**, a link table, kept as an array on this side (assumed)
- event_lead_rule → event_lead_request_event_lead_rule_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (event_lead_request_event_lead_rule_rel): event_lead_request_event_lead_rule_rel has no rows per event_lead_request in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (event_lead_request_event_lead_rule_rel): event_lead_request_event_lead_rule_rel is embedded in event_lead_request, but deleting a event_lead_rule row cascades to its event_lead_request_event_lead_rule_rel: the app must pull them from every event_lead_request document, or keep event_lead_request_event_lead_rule_rel separate
- **no_access_evidence** (event_lead_request): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventLeadRule

From `event_lead_rule` with `event_lead_rule_event_type_rel` embedded.

```js
{
  _id: int,  // id
  eventId: int,  // event_id
  companyId: int,  // company_id
  leadSalesTeamId: int,  // lead_sales_team_id
  leadUserId: int,  // lead_user_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  leadCreationBasis: string,  // lead_creation_basis
  leadCreationTrigger: string,  // lead_creation_trigger
  leadType: string,  // lead_type
  name: object,  // name
  eventRegistrationFilter: string,  // event_registration_filter
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  eventTypeRel: [{  // event_lead_rule_event_type_rel, 1:N assumed
    eventTypeId: int,  // event_type_id
  }],
}
```

Why:
- event_lead_rule → crm_lead: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_lead_rule → crm_tag_event_lead_rule_rel, event_lead_request_event_lead_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, event_event, crm_team → event_lead_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_lead_rule → event_lead_rule_event_type_rel: **embed**, a link table, kept as an array on this side (assumed)
- event_type → event_lead_rule_event_type_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (event_lead_rule_event_type_rel): event_lead_rule_event_type_rel has no rows per event_lead_rule in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (event_lead_rule_event_type_rel): event_lead_rule_event_type_rel is embedded in event_lead_rule, but deleting a event_type row cascades to its event_lead_rule_event_type_rel: the app must pull them from every event_lead_rule document, or keep event_lead_rule_event_type_rel separate
- **no_access_evidence** (event_lead_rule): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (event_lead_rule): LOB column(s) event_registration_filter measured max 35 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## eventQuestion

From `event_question` with `event_question_event_type_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  questionType: string,  // question_type
  title: object,  // title
  active: bool,  // active
  isDefault: bool,  // is_default
  isReusable: bool,  // is_reusable
  oncePerOrder: bool,  // once_per_order
  isMandatoryAnswer: bool,  // is_mandatory_answer
  createDate: date,  // create_date
  writeDate: date,  // write_date
  eventTypeRel: [{  // event_question_event_type_rel, 1:N assumed
    eventTypeId: int,  // event_type_id
  }],
}
```

Why:
- event_question → event_event_event_question_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → event_question: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_question → event_question_answer: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_question → event_question_event_type_rel: **embed**, a link table, kept as an array on this side (assumed)
- event_type → event_question_event_type_rel: **reference**, a link table, embedded on the other side (assumed)
- event_question → event_registration_answer: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (2):
- **cascade_into_embed** (event_question_event_type_rel): event_question_event_type_rel is embedded in event_question, but deleting a event_type row cascades to its event_question_event_type_rel: the app must pull them from every event_question document, or keep event_question_event_type_rel separate
- **no_access_evidence** (event_question): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventRegistration

From `event_registration` with `event_registration_answer` embedded.

```js
{
  _id: int,  // id
  eventId: int,  // event_id
  eventSlotId: int,  // event_slot_id
  eventTicketId: int,  // event_ticket_id
  utmCampaignId: int,  // utm_campaign_id
  utmSourceId: int,  // utm_source_id
  utmMediumId: int,  // utm_medium_id
  partnerId: int,  // partner_id
  companyId: int,  // company_id
  mainRegistrationId: int,  // main_registration_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  barcode: string,  // barcode
  name: string,  // name
  email: string,  // email
  phone: string,  // phone
  companyName: string,  // company_name
  state: string,  // state
  registrationProperties: object,  // registration_properties
  active: bool,  // active
  dateClosed: date,  // date_closed
  eventBeginDate: date,  // event_begin_date
  createDate: date,  // create_date
  writeDate: date,  // write_date
  saleStatus: string,  // sale_status
  saleOrderId: int,  // sale_order_id
  saleOrderLineId: int,  // sale_order_line_id
  answer: [{  // event_registration_answer, 1:N assumed
    id: int,  // id
    questionId: int,  // question_id
    valueAnswerId: int,  // value_answer_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    valueTextBox: string,  // value_text_box
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- event_registration → crm_lead_event_registration_rel: **reference**, a link table, embedded on the other side (assumed)
- event_registration → event_mail, event_mail_registration, event_mail_slot, event_registration: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, event_event, event_slot, event_event_ticket, res_partner, sale_order, sale_order_line, utm_campaign, utm_medium, utm_source → event_registration: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, event_question, event_question_answer → event_registration_answer: **reference**, it is embedded under another parent; this one is referenced (derived)
- event_registration → event_registration_answer: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

Open questions (4):
- **fanout_unmeasured** (event_registration_answer): event_registration_answer has no rows per event_registration in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (event_registration): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (event_registration_answer): LOB column(s) value_text_box: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## eventTag

From `event_tag` with `event_tag_event_type_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  categoryId: int,  // category_id
  categorySequence: int,  // category_sequence
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  eventTypeRel: [{  // event_tag_event_type_rel, 1:N assumed
    eventTypeId: int,  // event_type_id
  }],
}
```

Why:
- event_tag → event_event_event_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- event_tag_category, res_users → event_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_tag → event_tag_event_type_rel: **embed**, a link table, kept as an array on this side (assumed)
- event_type → event_tag_event_type_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (event_tag_event_type_rel): event_tag_event_type_rel has no rows per event_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (event_tag_event_type_rel): event_tag_event_type_rel is embedded in event_tag, but deleting a event_type row cascades to its event_tag_event_type_rel: the app must pull them from every event_tag document, or keep event_tag_event_type_rel separate
- **no_access_evidence** (event_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventType

From `event_type` with `event_type_mail` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  seatsMax: int,  // seats_max
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  defaultTimezone: string,  // default_timezone
  name: object,  // name
  ticketInstructions: object,  // ticket_instructions
  note: string,  // note
  hasSeatsLimitation: bool,  // has_seats_limitation
  createDate: date,  // create_date
  writeDate: date,  // write_date
  mail: [{  // event_type_mail, 1:N derived
    id: int,  // id
    intervalNbr: int,  // interval_nbr
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    intervalUnit: string,  // interval_unit
    intervalType: string,  // interval_type
    templateRef: string,  // template_ref
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- event_type → event_event, event_event_ticket, event_type_ticket: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_type → event_lead_rule_event_type_rel, event_question_event_type_rel, event_tag_event_type_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → event_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → event_type_mail: **reference**, it is embedded under another parent; this one is referenced (derived)
- event_type → event_type_mail: **embed**, owned by its parent (cascade delete or ordinal key) (derived)

Open questions (2):
- **no_access_evidence** (event_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (event_type): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## eventTypeTicket

From `event_type_ticket` with `event_type_ticket_product_product_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  eventTypeId: int,  // event_type_id
  seatsMax: int,  // seats_max
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  description: object,  // description
  seatsLimited: bool,  // seats_limited
  createDate: date,  // create_date
  writeDate: date,  // write_date
  productId: int,  // product_id
  price: decimal,  // price
  productProductRel: [{  // event_type_ticket_product_product_rel, 1:N assumed
    productProductId: int,  // product_product_id
  }],
}
```

Why:
- res_users, event_type, product_product → event_type_ticket: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_type_ticket → event_type_ticket_product_product_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_product → event_type_ticket_product_product_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (event_type_ticket_product_product_rel): event_type_ticket_product_product_rel has no rows per event_type_ticket in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (event_type_ticket_product_product_rel): event_type_ticket_product_product_rel is embedded in event_type_ticket, but deleting a product_product row cascades to its event_type_ticket_product_product_rel: the app must pull them from every event_type_ticket document, or keep event_type_ticket_product_product_rel separate
- **no_access_evidence** (event_type_ticket): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## fleetServiceType

From `fleet_service_type` with `fleet_service_type_fleet_vehicle_log_contract_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  category: string,  // category
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  fleetVehicleLogContractRel: [{  // fleet_service_type_fleet_vehicle_log_contract_rel, 1:N assumed
    fleetVehicleLogContractId: int,  // fleet_vehicle_log_contract_id
  }],
}
```

Why:
- res_company, res_users → fleet_service_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- fleet_vehicle_log_contract → fleet_service_type_fleet_vehicle_log_contract_rel: **reference**, a link table, embedded on the other side (assumed)
- fleet_service_type → fleet_service_type_fleet_vehicle_log_contract_rel: **embed**, a link table, kept as an array on this side (assumed)
- fleet_service_type → fleet_vehicle_log_contract: **reference**, other tables also point at it, so it keeps its own collection (derived)
- fleet_service_type → fleet_vehicle_log_services: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (2):
- **cascade_into_embed** (fleet_service_type_fleet_vehicle_log_contract_rel): fleet_service_type_fleet_vehicle_log_contract_rel is embedded in fleet_service_type, but deleting a fleet_vehicle_log_contract row cascades to its fleet_service_type_fleet_vehicle_log_contract_rel: the app must pull them from every fleet_service_type document, or keep fleet_service_type_fleet_vehicle_log_contract_rel separate
- **no_access_evidence** (fleet_service_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## fleetVehicle

From `fleet_vehicle` with `fleet_vehicle_log_services`, `fleet_vehicle_vehicle_tag_rel` embedded.

```js
{
  _id: int,  // id
  managerId: int,  // manager_id
  companyId: int,  // company_id
  driverId: int,  // driver_id
  futureDriverId: int,  // future_driver_id
  modelId: int,  // model_id
  brandId: int,  // brand_id
  stateId: int,  // state_id
  seats: int,  // seats
  doors: int,  // doors
  categoryId: int,  // category_id
  vehicleRange: int,  // vehicle_range
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  licensePlate: string,  // license_plate
  vinSn: string,  // vin_sn
  color: string,  // color
  location: string,  // location
  modelYear: string,  // model_year
  odometerUnit: string,  // odometer_unit
  transmission: string,  // transmission
  fuelType: string,  // fuel_type
  powerUnit: string,  // power_unit
  co2EmissionUnit: string,  // co2_emission_unit
  co2Standard: string,  // co2_standard
  frameType: string,  // frame_type
  rangeUnit: string,  // range_unit
  nextAssignationDate: date,  // next_assignation_date
  orderDate: date,  // order_date
  acquisitionDate: date,  // acquisition_date
  writeOffDate: date,  // write_off_date
  contractDateStart: date,  // contract_date_start
  vehicleProperties: object,  // vehicle_properties
  description: string,  // description
  active: bool,  // active
  trailerHook: bool,  // trailer_hook
  planToChangeVehicle: bool,  // plan_to_change_vehicle
  electricAssistance: bool,  // electric_assistance
  createDate: date,  // create_date
  writeDate: date,  // write_date
  horsepower: double,  // horsepower
  power: double,  // power
  co2: double,  // co2
  carValue: double,  // car_value
  netCarValue: double,  // net_car_value
  residualValue: double,  // residual_value
  frameSize: double,  // frame_size
  driverEmployeeId: int,  // driver_employee_id
  futureDriverEmployeeId: int,  // future_driver_employee_id
  logServices: [{  // fleet_vehicle_log_services, 1:N derived
    id: int,  // id
    modelId: int,  // model_id
    brandId: int,  // brand_id
    managerId: int,  // manager_id
    odometerId: int,  // odometer_id
    companyId: int,  // company_id
    purchaserId: int,  // purchaser_id
    vendorId: int,  // vendor_id
    serviceTypeId: int,  // service_type_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    description: string,  // description
    invRef: string,  // inv_ref
    state: string,  // state
    dateFrom: date,  // date_from
    dateTo: date,  // date_to
    notes: string,  // notes
    amount: decimal,  // amount
    active: bool,  // active
    createDate: date,  // create_date
    writeDate: date,  // write_date
    accountMoveLineId: int,  // account_move_line_id
    purchaserEmployeeId: int,  // purchaser_employee_id
  }],
  vehicleTagRel: [{  // fleet_vehicle_vehicle_tag_rel, 1:N derived
    tagId: int,  // tag_id
  }],
}
```

Why:
- fleet_vehicle → account_move_line, fleet_vehicle_odometer: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- fleet_vehicle_model_brand, fleet_vehicle_model_category, res_company, res_users, hr_employee, res_partner, fleet_vehicle_model, fleet_vehicle_state → fleet_vehicle: **reference**, other tables also point at it, so it keeps its own collection (derived)
- fleet_vehicle → fleet_vehicle_assignation_log: **reference**, the app reads it on its own (derived)
- fleet_vehicle → fleet_vehicle_log_contract, maintenance_equipment: **reference**, other tables also point at it, so it keeps its own collection (derived)
- account_move_line, fleet_vehicle_model_brand, res_company, res_users, fleet_vehicle_model, fleet_vehicle_odometer, hr_employee, res_partner, fleet_service_type → fleet_vehicle_log_services: **reference**, it is embedded under another parent; this one is referenced (derived)
- fleet_vehicle → fleet_vehicle_log_services: **embed**, read alongside its parent (derived)
- fleet_vehicle_tag → fleet_vehicle_vehicle_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- fleet_vehicle → fleet_vehicle_vehicle_tag_rel: **embed**, a link table, kept as an array on this side (derived)

Open questions (10):
- **extended_reference_candidate** (fleet_vehicle_vehicle_tag_rel): app reads fleet_vehicle_tag with every fleet_vehicle_vehicle_tag_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (fleet_vehicle_vehicle_tag_rel): fleet_vehicle_vehicle_tag_rel is embedded in fleet_vehicle, but deleting a fleet_vehicle_tag row cascades to its fleet_vehicle_vehicle_tag_rel: the app must pull them from every fleet_vehicle document, or keep fleet_vehicle_vehicle_tag_rel separate
- **lob** (fleet_vehicle): LOB column(s) description measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (fleet_vehicle_log_services): LOB column(s) notes measured max 24 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (fleet_vehicle): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (fleet_vehicle): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (fleet_vehicle_log_services): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (fleet_vehicle_log_services): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (fleet_vehicle_vehicle_tag_rel): source index not exercised by any confirmed access pattern; keep or drop

## fleetVehicleModel

From `fleet_vehicle_model` with `fleet_vehicle_model_vendors` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  brandId: int,  // brand_id
  categoryId: int,  // category_id
  seats: int,  // seats
  doors: int,  // doors
  vehicleRange: int,  // vehicle_range
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  vehicleType: string,  // vehicle_type
  transmission: string,  // transmission
  modelYear: string,  // model_year
  co2Standard: string,  // co2_standard
  defaultFuelType: string,  // default_fuel_type
  powerUnit: string,  // power_unit
  rangeUnit: string,  // range_unit
  driveType: string,  // drive_type
  vehiclePropertiesDefinition: object,  // vehicle_properties_definition
  active: bool,  // active
  electricAssistance: bool,  // electric_assistance
  createDate: date,  // create_date
  writeDate: date,  // write_date
  defaultCo2: double,  // default_co2
  power: double,  // power
  horsepower: double,  // horsepower
  vendors: [{  // fleet_vehicle_model_vendors, 1:N assumed
    partnerId: int,  // partner_id
  }],
}
```

Why:
- fleet_vehicle_model → fleet_vehicle: **reference**, other tables also point at it, so it keeps its own collection (derived)
- fleet_vehicle_model → fleet_vehicle_log_services: **reference**, it is embedded under another parent; this one is referenced (derived)
- fleet_vehicle_model_brand, fleet_vehicle_model_category, res_company, res_users → fleet_vehicle_model: **reference**, other tables also point at it, so it keeps its own collection (derived)
- fleet_vehicle_model → fleet_vehicle_model_vendors: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → fleet_vehicle_model_vendors: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (fleet_vehicle_model_vendors): fleet_vehicle_model_vendors has no rows per fleet_vehicle_model in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (fleet_vehicle_model_vendors): fleet_vehicle_model_vendors is embedded in fleet_vehicle_model, but deleting a res_partner row cascades to its fleet_vehicle_model_vendors: the app must pull them from every fleet_vehicle_model document, or keep fleet_vehicle_model_vendors separate
- **single_valued_index_key** (fleet_vehicle_model): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (fleet_vehicle_model_vendors): source index not exercised by any confirmed access pattern; keep or drop

## gamificationBadge

From `gamification_badge` with `badge_unlocked_definition_rel`, `gamification_badge_rule_badge_rel`, `rel_badge_auth_users` embedded.

```js
{
  _id: int,  // id
  ruleMaxNumber: int,  // rule_max_number
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  level: string,  // level
  ruleAuth: string,  // rule_auth
  name: object,  // name
  description: object,  // description
  active: bool,  // active
  ruleMax: bool,  // rule_max
  createDate: date,  // create_date
  writeDate: date,  // write_date
  surveyId: int,  // survey_id
  badgeUnlockedDefinitionRel: [{  // badge_unlocked_definition_rel, 1:N assumed
    gamificationGoalDefinitionId: int,  // gamification_goal_definition_id
  }],
  ruleBadgeRel: [{  // gamification_badge_rule_badge_rel, 1:N assumed
    badge2Id: int,  // badge2_id
  }],
  relBadgeAuthUsers: [{  // rel_badge_auth_users, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- gamification_badge → badge_unlocked_definition_rel, gamification_badge_rule_badge_rel, rel_badge_auth_users: **embed**, a link table, kept as an array on this side (assumed)
- gamification_goal_definition → badge_unlocked_definition_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, survey_survey → gamification_badge: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- gamification_badge → gamification_badge_rule_badge_rel: **reference**, a link table, embedded on the other side (assumed)
- gamification_badge → gamification_badge_user, gamification_challenge: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → rel_badge_auth_users: **reference**, a link table, embedded on the other side (assumed)
- gamification_badge → survey_survey: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (6):
- **fanout_unmeasured** (badge_unlocked_definition_rel): badge_unlocked_definition_rel has no rows per gamification_badge in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (gamification_badge_rule_badge_rel): gamification_badge_rule_badge_rel has no rows per gamification_badge in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (rel_badge_auth_users): rel_badge_auth_users has no rows per gamification_badge in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (badge_unlocked_definition_rel): badge_unlocked_definition_rel is embedded in gamification_badge, but deleting a gamification_goal_definition row cascades to its badge_unlocked_definition_rel: the app must pull them from every gamification_badge document, or keep badge_unlocked_definition_rel separate
- **cascade_into_embed** (rel_badge_auth_users): rel_badge_auth_users is embedded in gamification_badge, but deleting a res_users row cascades to its rel_badge_auth_users: the app must pull them from every gamification_badge document, or keep rel_badge_auth_users separate
- **no_access_evidence** (gamification_badge): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## gamificationChallenge

From `gamification_challenge` with `gamification_challenge_users_rel`, `gamification_invited_user_ids_rel` embedded.

```js
{
  _id: int,  // id
  managerId: int,  // manager_id
  rewardId: int,  // reward_id
  rewardFirstId: int,  // reward_first_id
  rewardSecondId: int,  // reward_second_id
  rewardThirdId: int,  // reward_third_id
  reportMessageGroupId: int,  // report_message_group_id
  reportTemplateId: int,  // report_template_id
  remindUpdateDelay: int,  // remind_update_delay
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  state: string,  // state
  userDomain: string,  // user_domain
  period: string,  // period
  visibilityMode: string,  // visibility_mode
  reportMessageFrequency: string,  // report_message_frequency
  challengeCategory: string,  // challenge_category
  startDate: date,  // start_date
  endDate: date,  // end_date
  lastReportDate: date,  // last_report_date
  nextReportDate: date,  // next_report_date
  name: object,  // name
  description: object,  // description
  rewardFailure: bool,  // reward_failure
  rewardRealtime: bool,  // reward_realtime
  createDate: date,  // create_date
  writeDate: date,  // write_date
  usersRel: [{  // gamification_challenge_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
  gamificationInvitedUserIdsRel: [{  // gamification_invited_user_ids_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- gamification_challenge → gamification_badge_user, gamification_challenge_line, gamification_goal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, discuss_channel, mail_template, gamification_badge → gamification_challenge: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- gamification_challenge → gamification_challenge_users_rel, gamification_invited_user_ids_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → gamification_challenge_users_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → gamification_invited_user_ids_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (gamification_invited_user_ids_rel): gamification_invited_user_ids_rel has no rows per gamification_challenge in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (gamification_challenge_users_rel): gamification_challenge_users_rel is embedded in gamification_challenge, but deleting a res_users row cascades to its gamification_challenge_users_rel: the app must pull them from every gamification_challenge document, or keep gamification_challenge_users_rel separate
- **cascade_into_embed** (gamification_invited_user_ids_rel): gamification_invited_user_ids_rel is embedded in gamification_challenge, but deleting a res_users row cascades to its gamification_invited_user_ids_rel: the app must pull them from every gamification_challenge document, or keep gamification_invited_user_ids_rel separate
- **no_access_evidence** (gamification_challenge): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrDepartment

From `hr_department` with `hr_department_hr_leave_mandatory_day_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  parentId: int,  // parent_id
  managerId: int,  // manager_id
  color: int,  // color
  masterDepartmentId: int,  // master_department_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  parentPath: string,  // parent_path
  name: object,  // name
  note: string,  // note
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  hrLeaveMandatoryDayRel: [{  // hr_department_hr_leave_mandatory_day_rel, 1:N assumed
    hrLeaveMandatoryDayId: int,  // hr_leave_mandatory_day_id
  }],
}
```

Why:
- hr_department → account_analytic_line, hr_department, hr_job, hr_leave, hr_leave_allocation, hr_resume_line, hr_version, mail_activity_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_department → discuss_channel_hr_department_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, hr_employee → hr_department: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_department → hr_department_hr_leave_mandatory_day_rel: **embed**, a link table, kept as an array on this side (assumed)
- hr_leave_mandatory_day → hr_department_hr_leave_mandatory_day_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_department → hr_expense, maintenance_equipment: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (4):
- **fanout_unmeasured** (hr_department_hr_leave_mandatory_day_rel): hr_department_hr_leave_mandatory_day_rel has no rows per hr_department in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (hr_department_hr_leave_mandatory_day_rel): hr_department_hr_leave_mandatory_day_rel is embedded in hr_department, but deleting a hr_leave_mandatory_day row cascades to its hr_department_hr_leave_mandatory_day_rel: the app must pull them from every hr_department document, or keep hr_department_hr_leave_mandatory_day_rel separate
- **no_access_evidence** (hr_department): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (hr_department): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## hrEmployee

From `hr_employee` with `employee_bank_account_rel`, `employee_category_rel`, `hr_employee_hr_skill_rel` embedded.

```js
{
  _id: int,  // id
  resourceId: int,  // resource_id
  companyId: int,  // company_id
  messageMainAttachmentId: int,  // message_main_attachment_id
  currentVersionId: int,  // current_version_id
  contractTemplateId: int,  // contract_template_id
  userId: int,  // user_id
  workContactId: int,  // work_contact_id
  countryOfBirth: int,  // country_of_birth
  parentId: int,  // parent_id
  coachId: int,  // coach_id
  color: int,  // color
  mondayLocationId: int,  // monday_location_id
  tuesdayLocationId: int,  // tuesday_location_id
  wednesdayLocationId: int,  // wednesday_location_id
  thursdayLocationId: int,  // thursday_location_id
  fridayLocationId: int,  // friday_location_id
  saturdayLocationId: int,  // saturday_location_id
  sundayLocationId: int,  // sunday_location_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  phoneSanitized: string,  // phone_sanitized
  name: string,  // name
  workPhone: string,  // work_phone
  mobilePhone: string,  // mobile_phone
  workEmail: string,  // work_email
  legalName: string,  // legal_name
  privatePhone: string,  // private_phone
  privateEmail: string,  // private_email
  lang: string,  // lang
  placeOfBirth: string,  // place_of_birth
  birthdayMonth: string,  // birthday_month
  permitNo: string,  // permit_no
  visaNo: string,  // visa_no
  certificate: string,  // certificate
  studyField: string,  // study_field
  emergencyContact: string,  // emergency_contact
  emergencyPhone: string,  // emergency_phone
  barcode: string,  // barcode
  pin: string,  // pin
  idCardName: string,  // id_card_name
  drivingLicenseName: string,  // driving_license_name
  todayLocationName: string,  // today_location_name
  birthday: date,  // birthday
  visaExpire: date,  // visa_expire
  workPermitExpirationDate: date,  // work_permit_expiration_date
  firstContractDate: date,  // first_contract_date
  salaryDistribution: object,  // salary_distribution
  employeeProperties: object,  // employee_properties
  additionalNote: string,  // additional_note
  hourlyCost: decimal,  // hourly_cost
  active: bool,  // active
  birthdayPublicDisplay: bool,  // birthday_public_display
  workPermitScheduledActivity: bool,  // work_permit_scheduled_activity
  createDate: date,  // create_date
  writeDate: date,  // write_date
  expenseManagerId: int,  // expense_manager_id
  externalCode: string,  // external_code
  leaveManagerId: int,  // leave_manager_id
  employeeBankAccountRel: [{  // employee_bank_account_rel, 1:N assumed
    bankAccountId: int,  // bank_account_id
  }],
  employeeCategoryRel: [{  // employee_category_rel, 1:N assumed
    categoryId: int,  // category_id
  }],
  hrSkillRel: [{  // hr_employee_hr_skill_rel, 1:N assumed
    hrSkillId: int,  // hr_skill_id
  }],
}
```

Why:
- hr_employee → account_analytic_line, gamification_badge_user, hr_department, hr_employee, hr_employee_departure, hr_employee_skill, hr_job, hr_leave, hr_leave_allocation, hr_resume_line, hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_employee → account_analytic_line_calendar_employee, fleet_vehicle_log_services, hr_user_work_entry_employee, project_sale_line_employee_map: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_partner_bank → employee_bank_account_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_employee → employee_bank_account_rel, employee_category_rel, hr_employee_hr_skill_rel: **embed**, a link table, kept as an array on this side (assumed)
- hr_employee_category → employee_category_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_employee → fleet_vehicle, hr_expense, maintenance_equipment, maintenance_request: **reference**, other tables also point at it, so it keeps its own collection (derived)
- hr_employee → fleet_vehicle_assignation_log: **reference**, another parent owns it; this one is referenced (derived)
- res_company, hr_version, res_country, res_users, hr_work_location, ir_attachment, resource_resource, res_partner → hr_employee: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_skill → hr_employee_hr_skill_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_employee → hr_employee_location: **reference**, no evidence either way (assumed)

Open questions (8):
- **fanout_unmeasured** (employee_bank_account_rel): employee_bank_account_rel has no rows per hr_employee in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (employee_bank_account_rel): employee_bank_account_rel is embedded in hr_employee, but deleting a res_partner_bank row cascades to its employee_bank_account_rel: the app must pull them from every hr_employee document, or keep employee_bank_account_rel separate
- **cascade_into_embed** (employee_category_rel): employee_category_rel is embedded in hr_employee, but deleting a hr_employee_category row cascades to its employee_category_rel: the app must pull them from every hr_employee document, or keep employee_category_rel separate
- **cascade_into_embed** (hr_employee_hr_skill_rel): hr_employee_hr_skill_rel is embedded in hr_employee, but deleting a hr_skill row cascades to its hr_employee_hr_skill_rel: the app must pull them from every hr_employee document, or keep hr_employee_hr_skill_rel separate
- **no_access_evidence** (hr_employee): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (hr_employee): LOB column(s) additional_note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## hrExpenseProductJobPositionLimit

From `hr_expense_product_job_position_limit` with `hr_expense_product_job_position_limit_hr_job_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  productId: int,  // product_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  limitAmount: decimal,  // limit_amount
  createDate: date,  // create_date
  writeDate: date,  // write_date
  hrJobRel: [{  // hr_expense_product_job_position_limit_hr_job_rel, 1:N assumed
    hrJobId: int,  // hr_job_id
  }],
}
```

Why:
- res_users, product_product → hr_expense_product_job_position_limit: **reference**, other tables also point at it, so it keeps its own collection (derived)
- hr_expense_product_job_position_limit → hr_expense_product_job_position_limit_hr_job_rel: **embed**, a link table, kept as an array on this side (assumed)
- hr_job → hr_expense_product_job_position_limit_hr_job_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (hr_expense_product_job_position_limit_hr_job_rel): hr_expense_product_job_position_limit_hr_job_rel has no rows per hr_expense_product_job_position_limit in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (hr_expense_product_job_position_limit_hr_job_rel): hr_expense_product_job_position_limit_hr_job_rel is embedded in hr_expense_product_job_position_limit, but deleting a hr_job row cascades to its hr_expense_product_job_position_limit_hr_job_rel: the app must pull them from every hr_expense_product_job_position_limit document, or keep hr_expense_product_job_position_limit_hr_job_rel separate
- **source_index_not_exercised** (hr_expense_product_job_position_limit_hr_job_rel): source index not exercised by any confirmed access pattern; keep or drop

## hrJob

From `hr_job` with `hr_job_hr_leave_mandatory_day_rel`, `hr_job_hr_skill_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  noOfRecruitment: int,  // no_of_recruitment
  recruiterId: int,  // recruiter_id
  departmentId: int,  // department_id
  companyId: int,  // company_id
  employeeTypeId: int,  // employee_type_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  description: string,  // description
  requirements: string,  // requirements
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  hrLeaveMandatoryDayRel: [{  // hr_job_hr_leave_mandatory_day_rel, 1:N assumed
    hrLeaveMandatoryDayId: int,  // hr_leave_mandatory_day_id
  }],
  hrSkillRel: [{  // hr_job_hr_skill_rel, 1:N assumed
    hrSkillId: int,  // hr_skill_id
  }],
}
```

Why:
- hr_job → hr_expense_product_job_position_limit_hr_job_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, hr_department, hr_employee_type, hr_employee → hr_job: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_leave_mandatory_day → hr_job_hr_leave_mandatory_day_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_job → hr_job_hr_leave_mandatory_day_rel, hr_job_hr_skill_rel: **embed**, a link table, kept as an array on this side (assumed)
- hr_skill → hr_job_hr_skill_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_job → hr_job_skill, hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (6):
- **fanout_unmeasured** (hr_job_hr_leave_mandatory_day_rel): hr_job_hr_leave_mandatory_day_rel has no rows per hr_job in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (hr_job_hr_leave_mandatory_day_rel): hr_job_hr_leave_mandatory_day_rel is embedded in hr_job, but deleting a hr_leave_mandatory_day row cascades to its hr_job_hr_leave_mandatory_day_rel: the app must pull them from every hr_job document, or keep hr_job_hr_leave_mandatory_day_rel separate
- **cascade_into_embed** (hr_job_hr_skill_rel): hr_job_hr_skill_rel is embedded in hr_job, but deleting a hr_skill row cascades to its hr_job_hr_skill_rel: the app must pull them from every hr_job document, or keep hr_job_hr_skill_rel separate
- **no_access_evidence** (hr_job): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (hr_job): LOB column(s) description, requirements measured max 1184 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## hrLeaveAccrualPlan

From `hr_leave_accrual_plan` with `hr_leave_accrual_level` embedded.

```js
{
  _id: int,  // id
  workEntryTypeId: int,  // work_entry_type_id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  transitionMode: string,  // transition_mode
  accruedGainTime: string,  // accrued_gain_time
  carryoverDate: date,  // carryover_date
  carryoverDay: string,  // carryover_day
  carryoverMonth: string,  // carryover_month
  addedValueType: string,  // added_value_type
  active: bool,  // active
  isBasedOnWorkedTime: bool,  // is_based_on_worked_time
  canBeCarryover: bool,  // can_be_carryover
  createDate: date,  // create_date
  writeDate: date,  // write_date
  hrLeaveAccrualLevel: [{  // hr_leave_accrual_level, 1:N assumed
    id: int,  // id
    sequence: int,  // sequence
    startCount: int,  // start_count
    maxCarriedoverDuration: int,  // max_carriedover_duration
    accrualValidityCount: int,  // accrual_validity_count
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    startType: string,  // start_type
    milestoneDate: date,  // milestone_date
    addedValueType: string,  // added_value_type
    frequency: string,  // frequency
    weekDay: string,  // week_day
    firstDay: string,  // first_day
    secondDay: string,  // second_day
    firstMonthDay: string,  // first_month_day
    firstMonth: string,  // first_month
    secondMonthDay: string,  // second_month_day
    secondMonth: string,  // second_month
    yearlyMonth: string,  // yearly_month
    yearlyDay: string,  // yearly_day
    actionWithUnusedAccruals: string,  // action_with_unused_accruals
    carryoverOptions: string,  // carryover_options
    accrualValidityType: string,  // accrual_validity_type
    addedValue: decimal,  // added_value
    maximumLeave: decimal,  // maximum_leave
    maximumLeaveYearly: decimal,  // maximum_leave_yearly
    capAccruedTime: bool,  // cap_accrued_time
    capAccruedTimeYearly: bool,  // cap_accrued_time_yearly
    accrualValidity: bool,  // accrual_validity
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
}
```

Why:
- hr_leave_accrual_plan → hr_leave_accrual_level: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → hr_leave_accrual_level: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_company, res_users, hr_work_entry_type → hr_leave_accrual_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_leave_accrual_plan → hr_leave_allocation, resource_calendar: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **fanout_unmeasured** (hr_leave_accrual_level): hr_leave_accrual_level has no rows per hr_leave_accrual_plan in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (hr_leave_accrual_plan): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **date_as_string** (hr_leave_accrual_plan)

## hrLeaveAllocation

From `hr_leave_allocation` with `hr_time_rule_allocation_log` embedded.

```js
{
  _id: int,  // id
  workEntryTypeId: int,  // work_entry_type_id
  employeeId: int,  // employee_id
  employeeCompanyId: int,  // employee_company_id
  managerId: int,  // manager_id
  approverId: int,  // approver_id
  secondApproverId: int,  // second_approver_id
  departmentId: int,  // department_id
  accrualPlanId: int,  // accrual_plan_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  state: string,  // state
  dateFrom: date,  // date_from
  dateTo: date,  // date_to
  lastAccrual: date,  // last_accrual
  lastcall: date,  // lastcall
  nextcall: date,  // nextcall
  carriedOverDaysExpirationDate: date,  // carried_over_days_expiration_date
  notes: string,  // notes
  createDate: date,  // create_date
  writeDate: date,  // write_date
  numberOfDays: double,  // number_of_days
  numberOfHours: double,  // number_of_hours
  yearlyAccruedDays: double,  // yearly_accrued_days
  previousCarryoverNumberOfDays: double,  // previous_carryover_number_of_days
  hrTimeRuleAllocationLog: [{  // hr_time_rule_allocation_log, 1:N assumed
    id: int,  // id
    resId: int,  // res_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    resModel: string,  // res_model
    createDate: date,  // create_date
    writeDate: date,  // write_date
    days: double,  // days
  }],
}
```

Why:
- hr_leave_accrual_plan, hr_employee, res_users, hr_department, res_company, hr_work_entry_type → hr_leave_allocation: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_leave_allocation → hr_time_rule_allocation_log: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → hr_time_rule_allocation_log: **reference**, it is embedded under another parent; this one is referenced (derived)
- hr_leave_allocation → hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **fanout_unmeasured** (hr_time_rule_allocation_log): hr_time_rule_allocation_log has no rows per hr_leave_allocation in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (hr_leave_allocation): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (hr_leave_allocation): LOB column(s) notes measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## hrTimeRule

From `hr_time_rule` with `hr_time_rule_condition_work_entry_type_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  countryId: int,  // country_id
  companyId: int,  // company_id
  resourceCalendarId: int,  // resource_calendar_id
  workEntryTypeId: int,  // work_entry_type_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  employeeDomain: string,  // employee_domain
  thresholdOperator: string,  // threshold_operator
  workingHoursMode: string,  // working_hours_mode
  calendarSource: string,  // calendar_source
  quantityPeriod: string,  // quantity_period
  weekStart: string,  // week_start
  description: string,  // description
  active: bool,  // active
  applyMonday: bool,  // apply_monday
  applyTuesday: bool,  // apply_tuesday
  applyWednesday: bool,  // apply_wednesday
  applyThursday: bool,  // apply_thursday
  applyFriday: bool,  // apply_friday
  applySaturday: bool,  // apply_saturday
  applySunday: bool,  // apply_sunday
  applyOnPublicHolidays: bool,  // apply_on_public_holidays
  createDate: date,  // create_date
  writeDate: date,  // write_date
  expectedHours: double,  // expected_hours
  timingStart: double,  // timing_start
  timingStop: double,  // timing_stop
  employeeTolerance: double,  // employee_tolerance
  employerTolerance: double,  // employer_tolerance
  amountRate: double,  // amount_rate
  allocationTypeId: int,  // allocation_type_id
  leaveCompensationRate: double,  // leave_compensation_rate
  conditionWorkEntryTypeRel: [{  // hr_time_rule_condition_work_entry_type_rel, 1:N assumed
    hrWorkEntryTypeId: int,  // hr_work_entry_type_id
  }],
}
```

Why:
- hr_time_rule → hr_leave: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_work_entry_type, res_company, res_country, res_users, resource_calendar → hr_time_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_work_entry_type → hr_time_rule_condition_work_entry_type_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_time_rule → hr_time_rule_condition_work_entry_type_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (3):
- **cascade_into_embed** (hr_time_rule_condition_work_entry_type_rel): hr_time_rule_condition_work_entry_type_rel is embedded in hr_time_rule, but deleting a hr_work_entry_type row cascades to its hr_time_rule_condition_work_entry_type_rel: the app must pull them from every hr_time_rule document, or keep hr_time_rule_condition_work_entry_type_rel separate
- **no_access_evidence** (hr_time_rule): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (hr_time_rule): LOB column(s) description measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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

Open questions (5):
- **fanout_unmeasured** (iap_account_res_company_rel): iap_account_res_company_rel has no rows per iap_account in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (iap_account_res_users_rel): iap_account_res_users_rel has no rows per iap_account in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (iap_account_res_company_rel): iap_account_res_company_rel is embedded in iap_account, but deleting a res_company row cascades to its iap_account_res_company_rel: the app must pull them from every iap_account document, or keep iap_account_res_company_rel separate
- **cascade_into_embed** (iap_account_res_users_rel): iap_account_res_users_rel is embedded in iap_account, but deleting a res_users row cascades to its iap_account_res_users_rel: the app must pull them from every iap_account document, or keep iap_account_res_users_rel separate
- **no_access_evidence** (iap_account): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (2):
- **fanout_unmeasured** (iap_service_pack): iap_service_pack has no rows per iap_service in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (iap_service): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (10):
- **fanout_unmeasured** (ir_act_server_res_partner_rel): ir_act_server_res_partner_rel has no rows per ir_act_server in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (ir_act_server_webhook_field_rel): ir_act_server_webhook_field_rel has no rows per ir_act_server in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (ir_act_server_group_rel): ir_act_server_group_rel is embedded in ir_act_server, but deleting a res_groups row cascades to its ir_act_server_group_rel: the app must pull them from every ir_act_server document, or keep ir_act_server_group_rel separate
- **cascade_into_embed** (ir_act_server_mail_message_subtype_rel): ir_act_server_mail_message_subtype_rel is embedded in ir_act_server, but deleting a mail_message_subtype row cascades to its ir_act_server_mail_message_subtype_rel: the app must pull them from every ir_act_server document, or keep ir_act_server_mail_message_subtype_rel separate
- **cascade_into_embed** (ir_act_server_res_partner_rel): ir_act_server_res_partner_rel is embedded in ir_act_server, but deleting a res_partner row cascades to its ir_act_server_res_partner_rel: the app must pull them from every ir_act_server document, or keep ir_act_server_res_partner_rel separate
- **cascade_into_embed** (ir_act_server_webhook_field_rel): ir_act_server_webhook_field_rel is embedded in ir_act_server, but deleting a ir_model_fields row cascades to its ir_act_server_webhook_field_rel: the app must pull them from every ir_act_server document, or keep ir_act_server_webhook_field_rel separate
- **no_access_evidence** (ir_act_server): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_act_server): LOB column(s) explanation, code, value, html_value, activity_note measured max 865 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (ir_actions_server_history): LOB column(s) code measured max 865 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

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
- ir_act_window → gamification_goal_definition, ir_embedded_actions, mail_template, res_users_settings_embedded_action, sms_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model, res_users, ir_ui_view → ir_act_window: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_window → ir_act_window_group_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → ir_act_window_group_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_act_window → ir_act_window_view: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users, ir_ui_view → ir_act_window_view: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (4):
- **cascade_into_embed** (ir_act_window_group_rel): ir_act_window_group_rel is embedded in ir_act_window, but deleting a res_groups row cascades to its ir_act_window_group_rel: the app must pull them from every ir_act_window document, or keep ir_act_window_group_rel separate
- **no_access_evidence** (ir_act_window): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_act_window): LOB column(s) explanation measured max 180 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## irAttachment

From `ir_attachment` with `discuss_voice_metadata`, `activity_attachment_rel`, `email_template_attachment_rel`, `message_attachment_rel`, `scheduled_message_attachment_rel` embedded.

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
- ir_attachment → account_move, account_payment, hr_employee, hr_leave, ir_attachment, product_document, project_task, quotation_document: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_activity → activity_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_attachment → activity_attachment_rel, email_template_attachment_rel, message_attachment_rel, scheduled_message_attachment_rel: **embed**, a link table, kept as an array on this side (assumed)
- ir_attachment → discuss_voice_metadata: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → discuss_voice_metadata: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_template → email_template_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_attachment → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_company, res_users → ir_attachment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_message → message_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_scheduled_message → scheduled_message_attachment_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (10):
- **fanout_unmeasured** (discuss_voice_metadata): discuss_voice_metadata has no rows per ir_attachment in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (activity_attachment_rel): activity_attachment_rel has no rows per ir_attachment in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (email_template_attachment_rel): email_template_attachment_rel has no rows per ir_attachment in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (scheduled_message_attachment_rel): scheduled_message_attachment_rel has no rows per ir_attachment in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (activity_attachment_rel): activity_attachment_rel is embedded in ir_attachment, but deleting a mail_activity row cascades to its activity_attachment_rel: the app must pull them from every ir_attachment document, or keep activity_attachment_rel separate
- **cascade_into_embed** (email_template_attachment_rel): email_template_attachment_rel is embedded in ir_attachment, but deleting a mail_template row cascades to its email_template_attachment_rel: the app must pull them from every ir_attachment document, or keep email_template_attachment_rel separate
- **cascade_into_embed** (message_attachment_rel): message_attachment_rel is embedded in ir_attachment, but deleting a mail_message row cascades to its message_attachment_rel: the app must pull them from every ir_attachment document, or keep message_attachment_rel separate
- **cascade_into_embed** (scheduled_message_attachment_rel): scheduled_message_attachment_rel is embedded in ir_attachment, but deleting a mail_scheduled_message row cascades to its scheduled_message_attachment_rel: the app must pull them from every ir_attachment document, or keep scheduled_message_attachment_rel separate
- **no_access_evidence** (ir_attachment): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_attachment): LOB column(s) description, index_content measured max 8509 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## irCron

From `ir_cron` with `ir_cron_progress` embedded.

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
}
```

Why:
- res_users, ir_act_server → ir_cron: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → ir_cron_progress: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_cron → ir_cron_progress: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- ir_cron → ir_cron_trigger, lunch_alert, lunch_supplier: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **fanout_unmeasured** (ir_cron_progress): ir_cron_progress has no rows per ir_cron in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (ir_cron): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (2):
- **cascade_into_embed** (ir_embedded_actions_res_groups_rel): ir_embedded_actions_res_groups_rel is embedded in ir_embedded_actions, but deleting a res_groups row cascades to its ir_embedded_actions_res_groups_rel: the app must pull them from every ir_embedded_actions document, or keep ir_embedded_actions_res_groups_rel separate
- **no_access_evidence** (ir_embedded_actions): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
  line: [{  // ir_exports_line, 1:N derived
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
- ir_exports → ir_exports_line: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- ir_exports → ir_exports_res_lang_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_lang → ir_exports_res_lang_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (ir_exports_res_lang_rel): ir_exports_res_lang_rel has no rows per ir_exports in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (ir_exports_res_lang_rel): ir_exports_res_lang_rel is embedded in ir_exports, but deleting a res_lang row cascades to its ir_exports_res_lang_rel: the app must pull them from every ir_exports document, or keep ir_exports_res_lang_rel separate
- **no_access_evidence** (ir_exports): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (4):
- **fanout_unmeasured** (ir_filters_res_users_rel): ir_filters_res_users_rel has no rows per ir_filters in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (ir_filters_res_users_rel): ir_filters_res_users_rel is embedded in ir_filters, but deleting a res_users row cascades to its ir_filters_res_users_rel: the app must pull them from every ir_filters document, or keep ir_filters_res_users_rel separate
- **no_access_evidence** (ir_filters): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_filters): LOB column(s) domain, context measured max 213 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## irModel

From `ir_model` with `ir_act_client`, `ir_act_url`, `ir_actions`, `ir_model_spreadsheet_dashboard_rel` embedded.

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
  irActClient: [{  // ir_act_client, 1:N assumed
    id: int,  // id
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
    tag: string,  // tag
    target: string,  // target
    resModel: string,  // res_model
    context: string,  // context
    paramsStore: string,  // params_store
  }],
  irActUrl: [{  // ir_act_url, 1:N assumed
    id: int,  // id
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
    target: string,  // target
    url: string,  // url
  }],
  irActions: [{  // ir_actions, 1:N derived
    id: int,  // id
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
  }],
  spreadsheetDashboardRel: [{  // ir_model_spreadsheet_dashboard_rel, 1:N assumed
    spreadsheetDashboardId: int,  // spreadsheet_dashboard_id
  }],
}
```

Why:
- ir_model → calendar_event, fetchmail_server, gamification_goal_definition, ir_access, ir_act_report_xml, ir_act_server, ir_act_window, ir_model_constraint, ir_model_fields, ir_model_relation, mail_activity, mail_activity_plan, mail_alias, mail_template, rating_rating, sms_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model → ir_act_client, ir_act_url: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_users → ir_act_client: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → ir_act_url: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_model → ir_actions: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → ir_actions: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → ir_model: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model → ir_model_inherit: **reference**, it is embedded under another parent; this one is referenced (derived)
- spreadsheet_dashboard → ir_model_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_model → ir_model_spreadsheet_dashboard_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (8):
- **fanout_unmeasured** (ir_act_client): ir_act_client has no rows per ir_model in the profiled source (child_rows=12); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (ir_act_url): ir_act_url has no rows per ir_model in the profiled source (child_rows=4); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (ir_model_spreadsheet_dashboard_rel): ir_model_spreadsheet_dashboard_rel is embedded in ir_model, but deleting a spreadsheet_dashboard row cascades to its ir_model_spreadsheet_dashboard_rel: the app must pull them from every ir_model document, or keep ir_model_spreadsheet_dashboard_rel separate
- **no_access_evidence** (ir_model): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_model): LOB column(s) info, explanation measured max 1976 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (ir_act_client): LOB column(s) explanation, params_store measured max 42 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (ir_act_url): LOB column(s) explanation, url measured max 35 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (ir_actions): LOB column(s) explanation measured max 180 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## irModelFields

From `ir_model_fields` with `crm_lead_scoring_frequency_field`, `ir_model_inherit`, `properties_base_definition`, `ir_model_fields_group_rel` embedded.

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
  crmLeadScoringFrequencyField: [{  // crm_lead_scoring_frequency_field, 1:N derived
    id: int,  // id
    color: int,  // color
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  irModelInherit: [{  // ir_model_inherit, 1:N derived
    id: int,  // id
    modelId: int,  // model_id
    parentId: int,  // parent_id
  }],
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
- res_users → crm_lead_scoring_frequency_field: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_model_fields → crm_lead_scoring_frequency_field, ir_model_inherit: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- ir_model_fields → gamification_goal_definition, ir_act_server, ir_default, ir_model_fields, ir_model_fields_selection: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model_fields → ir_act_server_webhook_field_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, ir_model → ir_model_fields: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model_fields → ir_model_fields_group_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_groups → ir_model_fields_group_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_model → ir_model_inherit: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → properties_base_definition: **reference**, it is embedded under another parent; this one is referenced (derived)
- ir_model_fields → properties_base_definition: **embed**, one-to-one with its parent (derived)

Open questions (5):
- **cascade_into_embed** (ir_model_fields_group_rel): ir_model_fields_group_rel is embedded in ir_model_fields, but deleting a res_groups row cascades to its ir_model_fields_group_rel: the app must pull them from every ir_model_fields document, or keep ir_model_fields_group_rel separate
- **cascade_into_embed** (ir_model_inherit): ir_model_inherit is embedded in ir_model_fields, but deleting a ir_model row cascades to its ir_model_inherit: the app must pull them from every ir_model_fields document, or keep ir_model_inherit separate
- **no_access_evidence** (ir_model_fields): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **repeating_group** (ir_model_fields): collapse each numbered series into one array field; needs app evidence, mapped 1:1 until then
- **lob** (ir_model_fields): LOB column(s) compute measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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

Open questions (4):
- **fanout_unmeasured** (ir_module_module_exclusion): ir_module_module_exclusion has no rows per ir_module_module in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (module_country): module_country is embedded in ir_module_module, but deleting a res_country row cascades to its module_country: the app must pull them from every ir_module_module document, or keep module_country separate
- **no_access_evidence** (ir_module_module): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_module_module): LOB column(s) contributors, menus_by_module, reports_by_module, views_by_module measured max 2124 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## irProfile

From `ir_profile` with `ir_profile_query` embedded.

```js
{
  _id: int,  // id
  sqlCount: int,  // sql_count
  entryCount: int,  // entry_count
  session: string,  // session
  name: string,  // name
  initStackTrace: string,  // init_stack_trace
  sql: string,  // sql
  tracesAsync: string,  // traces_async
  others: string,  // others
  qweb: string,  // qweb
  duration: decimal,  // duration
  cpuDuration: decimal,  // cpu_duration
  createDate: date,  // create_date
  query: [{  // ir_profile_query, 1:N assumed
    id: int,  // id
    query: string,  // query
    fullQuery: string,  // full_query
    plan: string,  // plan
    time: decimal,  // time
  }],
}
```

Why:
- ir_profile → ir_profile_query: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)

Open questions (4):
- **fanout_unmeasured** (ir_profile_query): ir_profile_query has no rows per ir_profile in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (ir_profile): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_profile): LOB column(s) init_stack_trace, sql, traces_async, others, qweb: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit
- **lob** (ir_profile_query): LOB column(s) query, full_query, plan: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

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

Open questions (2):
- **cascade_into_embed** (ir_ui_menu_group_rel): ir_ui_menu_group_rel is embedded in ir_ui_menu, but deleting a res_groups row cascades to its ir_ui_menu_group_rel: the app must pull them from every ir_ui_menu document, or keep ir_ui_menu_group_rel separate
- **no_access_evidence** (ir_ui_menu): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (3):
- **cascade_into_embed** (ir_ui_view_group_rel): ir_ui_view_group_rel is embedded in ir_ui_view, but deleting a res_groups row cascades to its ir_ui_view_group_rel: the app must pull them from every ir_ui_view document, or keep ir_ui_view_group_rel separate
- **no_access_evidence** (ir_ui_view): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_ui_view): LOB column(s) arch_prev, notes measured max 14368 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## lunchAlert

From `lunch_alert` with `lunch_alert_lunch_location_rel` embedded.

```js
{
  _id: int,  // id
  cronId: int,  // cron_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  mode: string,  // mode
  recipients: string,  // recipients
  tz: string,  // tz
  until: date,  // until
  name: object,  // name
  message: object,  // message
  mon: bool,  // mon
  tue: bool,  // tue
  wed: bool,  // wed
  thu: bool,  // thu
  fri: bool,  // fri
  sat: bool,  // sat
  sun: bool,  // sun
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  notificationTime: double,  // notification_time
  lunchLocationRel: [{  // lunch_alert_lunch_location_rel, 1:N derived
    lunchLocationId: int,  // lunch_location_id
  }],
}
```

Why:
- res_users, ir_cron → lunch_alert: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- lunch_alert → lunch_alert_lunch_location_rel: **embed**, a link table, kept as an array on this side (derived)
- lunch_location → lunch_alert_lunch_location_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **extended_reference_candidate** (lunch_alert_lunch_location_rel): app reads lunch_location with every lunch_alert_lunch_location_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (lunch_alert_lunch_location_rel): lunch_alert_lunch_location_rel is embedded in lunch_alert, but deleting a lunch_location row cascades to its lunch_alert_lunch_location_rel: the app must pull them from every lunch_alert document, or keep lunch_alert_lunch_location_rel separate
- **source_index_not_exercised** (lunch_alert_lunch_location_rel): source index not exercised by any confirmed access pattern; keep or drop

## lunchLocation

From `lunch_location` with `lunch_location_lunch_supplier_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  address: string,  // address
  createDate: date,  // create_date
  writeDate: date,  // write_date
  lunchSupplierRel: [{  // lunch_location_lunch_supplier_rel, 1:N derived
    lunchSupplierId: int,  // lunch_supplier_id
  }],
}
```

Why:
- lunch_location → lunch_alert_lunch_location_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users → lunch_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- lunch_location → lunch_location_lunch_supplier_rel: **embed**, a link table, kept as an array on this side (derived)
- lunch_supplier → lunch_location_lunch_supplier_rel: **reference**, a link table, embedded on the other side (assumed)
- lunch_location → lunch_order: **reference**, other tables also point at it, so it keeps its own collection (derived)
- lunch_location → res_users: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (4):
- **extended_reference_candidate** (lunch_location_lunch_supplier_rel): app reads lunch_supplier with every lunch_location_lunch_supplier_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (lunch_location_lunch_supplier_rel): lunch_location_lunch_supplier_rel is embedded in lunch_location, but deleting a lunch_supplier row cascades to its lunch_location_lunch_supplier_rel: the app must pull them from every lunch_location document, or keep lunch_location_lunch_supplier_rel separate
- **lob** (lunch_location): LOB column(s) address measured max 42 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (lunch_location_lunch_supplier_rel): source index not exercised by any confirmed access pattern; keep or drop

## lunchOrder

From `lunch_order` with `lunch_order_topping` embedded.

```js
{
  _id: int,  // id
  productId: int,  // product_id
  categoryId: int,  // category_id
  supplierId: int,  // supplier_id
  userId: int,  // user_id
  lunchLocationId: int,  // lunch_location_id
  companyId: int,  // company_id
  currencyId: int,  // currency_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  state: string,  // state
  date: date,  // date
  note: string,  // note
  displayToppings: string,  // display_toppings
  price: decimal,  // price
  active: bool,  // active
  notified: bool,  // notified
  createDate: date,  // create_date
  writeDate: date,  // write_date
  quantity: double,  // quantity
  topping: [{  // lunch_order_topping, 1:N derived
    toppingId: int,  // topping_id
  }],
}
```

Why:
- lunch_product_category, res_company, res_users, res_currency, lunch_location, lunch_product, lunch_supplier → lunch_order: **reference**, other tables also point at it, so it keeps its own collection (derived)
- lunch_order → lunch_order_topping: **embed**, a link table, kept as an array on this side (derived)
- lunch_topping → lunch_order_topping: **reference**, a link table, embedded on the other side (assumed)

Open questions (6):
- **fanout_unmeasured** (lunch_order_topping): lunch_order_topping has no rows per lunch_order in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (lunch_order_topping): app reads lunch_topping with every lunch_order_topping: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (lunch_order_topping): lunch_order_topping is embedded in lunch_order, but deleting a lunch_topping row cascades to its lunch_order_topping: the app must pull them from every lunch_order document, or keep lunch_order_topping separate
- **lob** (lunch_order): LOB column(s) note, display_toppings measured max 1 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (lunch_order): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (lunch_order_topping): source index not exercised by any confirmed access pattern; keep or drop

## lunchProduct

From `lunch_product` with `lunch_product_favorite_user_rel` embedded.

```js
{
  _id: int,  // id
  categoryId: int,  // category_id
  supplierId: int,  // supplier_id
  companyId: int,  // company_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  newUntil: date,  // new_until
  name: object,  // name
  description: object,  // description
  price: decimal,  // price
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  favoriteUserRel: [{  // lunch_product_favorite_user_rel, 1:N assumed
    userId: int,  // user_id
  }],
}
```

Why:
- lunch_product → lunch_order: **reference**, other tables also point at it, so it keeps its own collection (derived)
- lunch_product_category, res_company, res_users, lunch_supplier → lunch_product: **reference**, other tables also point at it, so it keeps its own collection (derived)
- lunch_product → lunch_product_favorite_user_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → lunch_product_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (lunch_product_favorite_user_rel): lunch_product_favorite_user_rel has no rows per lunch_product in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (lunch_product_favorite_user_rel): lunch_product_favorite_user_rel is embedded in lunch_product, but deleting a res_users row cascades to its lunch_product_favorite_user_rel: the app must pull them from every lunch_product document, or keep lunch_product_favorite_user_rel separate
- **source_index_not_exercised** (lunch_product): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (lunch_product_favorite_user_rel): source index not exercised by any confirmed access pattern; keep or drop

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

Open questions (4):
- **fanout_unmeasured** (mail_activity_rel): mail_activity_rel has no rows per mail_activity_type in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (mail_activity_type_mail_template_rel): mail_activity_type_mail_template_rel has no rows per mail_activity_type in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (mail_activity_type_mail_template_rel): mail_activity_type_mail_template_rel is embedded in mail_activity_type, but deleting a mail_template row cascades to its mail_activity_type_mail_template_rel: the app must pull them from every mail_activity_type document, or keep mail_activity_type_mail_template_rel separate
- **no_access_evidence** (mail_activity_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (3):
- **cascade_into_embed** (mail_canned_response_res_groups_rel): mail_canned_response_res_groups_rel is embedded in mail_canned_response, but deleting a res_groups row cascades to its mail_canned_response_res_groups_rel: the app must pull them from every mail_canned_response document, or keep mail_canned_response_res_groups_rel separate
- **no_access_evidence** (mail_canned_response): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_canned_response): LOB column(s) substitution measured max 35 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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

Open questions (3):
- **cascade_into_embed** (mail_followers_mail_message_subtype_rel): mail_followers_mail_message_subtype_rel is embedded in mail_followers, but deleting a mail_message_subtype row cascades to its mail_followers_mail_message_subtype_rel: the app must pull them from every mail_followers document, or keep mail_followers_mail_message_subtype_rel separate
- **no_access_evidence** (mail_followers): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

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

Open questions (5):
- **fanout_unmeasured** (mail_mail_res_partner_cc_rel): mail_mail_res_partner_cc_rel has no rows per mail_mail in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (mail_mail_res_partner_cc_rel): mail_mail_res_partner_cc_rel is embedded in mail_mail, but deleting a res_partner row cascades to its mail_mail_res_partner_cc_rel: the app must pull them from every mail_mail document, or keep mail_mail_res_partner_cc_rel separate
- **cascade_into_embed** (mail_mail_res_partner_rel): mail_mail_res_partner_rel is embedded in mail_mail, but deleting a res_partner row cascades to its mail_mail_res_partner_rel: the app must pull them from every mail_mail document, or keep mail_mail_res_partner_rel separate
- **no_access_evidence** (mail_mail): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_mail): LOB column(s) body_html, references, headers, email_to, failure_reason measured max 2839 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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
  schedule: [{  // mail_message_schedule, 1:N derived
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
- mail_message → discuss_call_history, discuss_channel, discuss_channel_member, mail_mail, mail_message, mail_message_link_preview, mail_message_reaction, mail_notification, mail_poll, rating_rating, sms_sms: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_guest, res_partner, res_users, mail_activity_type, ir_mail_server, mail_alias_domain, res_company, mail_message_subtype → mail_message: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_message → mail_message_res_partner_bookmarked_rel, mail_message_res_partner_cc_rel, mail_message_res_partner_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_partner → mail_message_res_partner_bookmarked_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → mail_message_res_partner_cc_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → mail_message_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → mail_message_schedule: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_message → mail_message_schedule: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → mail_message_translation: **reference**, it is embedded under another parent; this one is referenced (derived)
- mail_message → mail_message_translation: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- mail_message → message_attachment_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (10):
- **fanout_unmeasured** (mail_message_translation): mail_message_translation has no rows per mail_message in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (mail_message_res_partner_bookmarked_rel): mail_message_res_partner_bookmarked_rel has no rows per mail_message in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (mail_message_res_partner_cc_rel): mail_message_res_partner_cc_rel has no rows per mail_message in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (mail_message_res_partner_bookmarked_rel): mail_message_res_partner_bookmarked_rel is embedded in mail_message, but deleting a res_partner row cascades to its mail_message_res_partner_bookmarked_rel: the app must pull them from every mail_message document, or keep mail_message_res_partner_bookmarked_rel separate
- **cascade_into_embed** (mail_message_res_partner_cc_rel): mail_message_res_partner_cc_rel is embedded in mail_message, but deleting a res_partner row cascades to its mail_message_res_partner_cc_rel: the app must pull them from every mail_message document, or keep mail_message_res_partner_cc_rel separate
- **cascade_into_embed** (mail_message_res_partner_rel): mail_message_res_partner_rel is embedded in mail_message, but deleting a res_partner row cascades to its mail_message_res_partner_rel: the app must pull them from every mail_message document, or keep mail_message_res_partner_rel separate
- **no_access_evidence** (mail_message): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_message): LOB column(s) body, incoming_email_to measured max 1763 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (mail_message_schedule): LOB column(s) notification_parameters measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (mail_message_translation): LOB column(s) body: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

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

Open questions (3):
- **fanout_unmeasured** (sms_tracker): sms_tracker has no rows per mail_notification in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (mail_notification): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_notification): LOB column(s) failure_reason measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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

Open questions (3):
- **fanout_unmeasured** (mail_push): mail_push has no rows per mail_push_device in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (mail_push_device): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_push): LOB column(s) payload: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

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

Open questions (6):
- **fanout_unmeasured** (mail_scheduled_message_res_partner_cc_rel): mail_scheduled_message_res_partner_cc_rel has no rows per mail_scheduled_message in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (mail_scheduled_message_res_partner_rel): mail_scheduled_message_res_partner_rel has no rows per mail_scheduled_message in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (mail_scheduled_message_res_partner_cc_rel): mail_scheduled_message_res_partner_cc_rel is embedded in mail_scheduled_message, but deleting a res_partner row cascades to its mail_scheduled_message_res_partner_cc_rel: the app must pull them from every mail_scheduled_message document, or keep mail_scheduled_message_res_partner_cc_rel separate
- **cascade_into_embed** (mail_scheduled_message_res_partner_rel): mail_scheduled_message_res_partner_rel is embedded in mail_scheduled_message, but deleting a res_partner row cascades to its mail_scheduled_message_res_partner_rel: the app must pull them from every mail_scheduled_message document, or keep mail_scheduled_message_res_partner_rel separate
- **no_access_evidence** (mail_scheduled_message): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_scheduled_message): LOB column(s) body, notification_parameters: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

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
  scheduledDate: date,  // scheduled_date
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
- mail_template → calendar_alarm, gamification_challenge, ir_act_server, project_project_stage, project_task_type, res_company, sale_order, sale_order_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_template → email_template_attachment_rel, mail_activity_type_mail_template_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, ir_mail_server, ir_model, ir_act_window → mail_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_report_xml → mail_template_ir_actions_report_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_template → mail_template_ir_actions_report_rel: **embed**, a link table, kept as an array on this side (assumed)
- mail_template → survey_survey: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (3):
- **cascade_into_embed** (mail_template_ir_actions_report_rel): mail_template_ir_actions_report_rel is embedded in mail_template, but deleting a ir_act_report_xml row cascades to its mail_template_ir_actions_report_rel: the app must pull them from every mail_template document, or keep mail_template_ir_actions_report_rel separate
- **no_access_evidence** (mail_template): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **date_as_string** (mail_template)

## maintenanceRequest

From `maintenance_request` with `maintenance_request_res_users_rel` embedded.

```js
{
  _id: int,  // id
  companyId: int,  // company_id
  ownerUserId: int,  // owner_user_id
  categoryId: int,  // category_id
  equipmentId: int,  // equipment_id
  stageId: int,  // stage_id
  color: int,  // color
  maintenanceTeamId: int,  // maintenance_team_id
  repeatInterval: int,  // repeat_interval
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  priority: string,  // priority
  state: string,  // state
  maintenanceType: string,  // maintenance_type
  repeatUnit: string,  // repeat_unit
  repeatType: string,  // repeat_type
  closeDate: date,  // close_date
  repeatUntil: date,  // repeat_until
  equipmentReqProperties: object,  // equipment_req_properties
  description: string,  // description
  instructionText: string,  // instruction_text
  recurringMaintenance: bool,  // recurring_maintenance
  scheduleDate: date,  // schedule_date
  scheduleEnd: date,  // schedule_end
  createDate: date,  // create_date
  writeDate: date,  // write_date
  duration: double,  // duration
  employeeId: int,  // employee_id
  resUsersRel: [{  // maintenance_request_res_users_rel, 1:N derived
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- maintenance_equipment_category, res_company, res_users, hr_employee, maintenance_equipment, maintenance_team, maintenance_stage → maintenance_request: **reference**, other tables also point at it, so it keeps its own collection (derived)
- maintenance_request → maintenance_request_res_users_rel: **embed**, a link table, kept as an array on this side (derived)
- res_users → maintenance_request_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **extended_reference_candidate** (maintenance_request_res_users_rel): app reads res_users with every maintenance_request_res_users_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (maintenance_request_res_users_rel): maintenance_request_res_users_rel is embedded in maintenance_request, but deleting a res_users row cascades to its maintenance_request_res_users_rel: the app must pull them from every maintenance_request document, or keep maintenance_request_res_users_rel separate
- **lob** (maintenance_request): LOB column(s) description, instruction_text measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (maintenance_request): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (maintenance_request_res_users_rel): source index not exercised by any confirmed access pattern; keep or drop

## maintenanceStage

From `maintenance_stage` with `maintenance_stage_maintenance_team_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  fold: bool,  // fold
  createDate: date,  // create_date
  writeDate: date,  // write_date
  maintenanceTeamRel: [{  // maintenance_stage_maintenance_team_rel, 1:N derived
    maintenanceTeamId: int,  // maintenance_team_id
  }],
}
```

Why:
- maintenance_stage → maintenance_request: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_users → maintenance_stage: **reference**, other tables also point at it, so it keeps its own collection (derived)
- maintenance_stage → maintenance_stage_maintenance_team_rel: **embed**, a link table, kept as an array on this side (derived)
- maintenance_team → maintenance_stage_maintenance_team_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (maintenance_stage_maintenance_team_rel): maintenance_stage_maintenance_team_rel has no rows per maintenance_stage in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **extended_reference_candidate** (maintenance_stage_maintenance_team_rel): app reads maintenance_team with every maintenance_stage_maintenance_team_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (maintenance_stage_maintenance_team_rel): maintenance_stage_maintenance_team_rel is embedded in maintenance_stage, but deleting a maintenance_team row cascades to its maintenance_stage_maintenance_team_rel: the app must pull them from every maintenance_stage document, or keep maintenance_stage_maintenance_team_rel separate
- **source_index_not_exercised** (maintenance_stage_maintenance_team_rel): source index not exercised by any confirmed access pattern; keep or drop

## maintenanceTeam

From `maintenance_team` with `maintenance_team_users_rel` embedded.

```js
{
  _id: int,  // id
  aliasId: int,  // alias_id
  companyId: int,  // company_id
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  usersRel: [{  // maintenance_team_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- maintenance_team → maintenance_equipment, maintenance_request: **reference**, other tables also point at it, so it keeps its own collection (derived)
- maintenance_team → maintenance_stage_maintenance_team_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_alias, res_users → maintenance_team: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_company → maintenance_team: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- maintenance_team → maintenance_team_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → maintenance_team_users_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (maintenance_team_users_rel): maintenance_team_users_rel has no rows per maintenance_team in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (maintenance_team_users_rel): maintenance_team_users_rel is embedded in maintenance_team, but deleting a res_users row cascades to its maintenance_team_users_rel: the app must pull them from every maintenance_team document, or keep maintenance_team_users_rel separate
- **source_index_not_exercised** (maintenance_team): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (maintenance_team_users_rel): source index not exercised by any confirmed access pattern; keep or drop

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

Open questions (2):
- **cascade_into_embed** (onboarding_onboarding_onboarding_onboarding_step_rel): onboarding_onboarding_onboarding_onboarding_step_rel is embedded in onboarding_onboarding, but deleting a onboarding_onboarding_step row cascades to its onboarding_onboarding_onboarding_onboarding_step_rel: the app must pull them from every onboarding_onboarding document, or keep onboarding_onboarding_onboarding_onboarding_step_rel separate
- **no_access_evidence** (onboarding_onboarding): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (3):
- **fanout_unmeasured** (onboarding_progress_onboarding_progress_step_rel): onboarding_progress_onboarding_progress_step_rel has no rows per onboarding_progress in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (onboarding_progress_onboarding_progress_step_rel): onboarding_progress_onboarding_progress_step_rel is embedded in onboarding_progress, but deleting a onboarding_progress_step row cascades to its onboarding_progress_onboarding_progress_step_rel: the app must pull them from every onboarding_progress document, or keep onboarding_progress_onboarding_progress_step_rel separate
- **no_access_evidence** (onboarding_progress): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (5):
- **fanout_unmeasured** (payment_method_res_country_rel): payment_method_res_country_rel has no rows per payment_method in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (payment_method_res_currency_rel): payment_method_res_currency_rel has no rows per payment_method in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (payment_method_res_country_rel): payment_method_res_country_rel is embedded in payment_method, but deleting a res_country row cascades to its payment_method_res_country_rel: the app must pull them from every payment_method document, or keep payment_method_res_country_rel separate
- **cascade_into_embed** (payment_method_res_currency_rel): payment_method_res_currency_rel is embedded in payment_method, but deleting a res_currency row cascades to its payment_method_res_currency_rel: the app must pull them from every payment_method document, or keep payment_method_res_currency_rel separate
- **no_access_evidence** (payment_method): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (7):
- **fanout_unmeasured** (payment_country_rel): payment_country_rel has no rows per payment_provider in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (payment_currency_rel): payment_currency_rel has no rows per payment_provider in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (payment_provider_product_pricelist_rel): payment_provider_product_pricelist_rel has no rows per payment_provider in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (payment_country_rel): payment_country_rel is embedded in payment_provider, but deleting a res_country row cascades to its payment_country_rel: the app must pull them from every payment_provider document, or keep payment_country_rel separate
- **cascade_into_embed** (payment_currency_rel): payment_currency_rel is embedded in payment_provider, but deleting a res_currency row cascades to its payment_currency_rel: the app must pull them from every payment_provider document, or keep payment_currency_rel separate
- **cascade_into_embed** (payment_provider_product_pricelist_rel): payment_provider_product_pricelist_rel is embedded in payment_provider, but deleting a product_pricelist row cascades to its payment_provider_product_pricelist_rel: the app must pull them from every payment_provider document, or keep payment_provider_product_pricelist_rel separate
- **no_access_evidence** (payment_provider): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
- res_users → product_attribute: **reference**, other tables also point at it, so it keeps its own collection (assumed)
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
- product_attribute, res_users → product_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
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
- product_category → account_analytic_applicability, account_analytic_distribution_model, product_category, product_pricelist_item, product_template, stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, product_removal → product_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_type → product_category_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category → product_category_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (product_category_stock_picking_type_rel): product_category_stock_picking_type_rel has no rows per product_category in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
- res_company, res_users → product_combo: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo → product_combo_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo → product_combo_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_combo_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (product_combo_product_template_rel): product_combo_product_template_rel is embedded in product_combo, but deleting a product_template row cascades to its product_combo_product_template_rel: the app must pull them from every product_combo document, or keep product_combo_product_template_rel separate
- **no_access_evidence** (product_combo): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productDocument

From `product_document` with `product_document_sale_pdf_form_field_rel` embedded.

```js
{
  _id: int,  // id
  irAttachmentId: int,  // ir_attachment_id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  attachedOnSale: string,  // attached_on_sale
  salePdfFormFieldRel: [{  // product_document_sale_pdf_form_field_rel, 1:N assumed
    salePdfFormFieldId: int,  // sale_pdf_form_field_id
  }],
}
```

Why:
- res_users, ir_attachment → product_document: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- sale_pdf_form_field → product_document_sale_pdf_form_field_rel: **reference**, a link table, embedded on the other side (assumed)
- product_document → product_document_sale_pdf_form_field_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_document → sale_order_line_product_document_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (product_document_sale_pdf_form_field_rel): product_document_sale_pdf_form_field_rel is embedded in product_document, but deleting a sale_pdf_form_field row cascades to its product_document_sale_pdf_form_field_rel: the app must pull them from every product_document document, or keep product_document_sale_pdf_form_field_rel separate
- **no_access_evidence** (product_document): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productProduct

From `product_product` with `product_value`, `product_product_uom_uom_rel`, `product_variant_combination` embedded.

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
- product_product → account_analytic_distribution_model, account_analytic_line, account_move_line, customer_product_reference, event_event_ticket, event_type_ticket, product_combo_item, product_pricelist_item, product_supplierinfo, product_uom, project_project, purchase_order_line, res_company, sale_order_line, sale_order_template_line, stock_lot, stock_move, stock_move_line, stock_putaway_rule, stock_quant, stock_storage_category_capacity, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_product → event_event_ticket_product_product_rel, event_type_ticket_product_product_rel, product_tag_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- product_product → hr_expense, hr_expense_product_job_position_limit: **reference**, other tables also point at it, so it keeps its own collection (derived)
- product_base_unit, res_users, product_template → product_product: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_product → product_product_uom_uom_rel, product_variant_combination: **embed**, a link table, kept as an array on this side (assumed)
- uom_uom → product_product_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- account_move, res_company, res_users, stock_lot, stock_move → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_product → product_value: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- product_template_attribute_value → product_variant_combination: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (product_product_uom_uom_rel): product_product_uom_uom_rel has no rows per product_product in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
- res_users → product_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_product → product_tag_product_product_rel: **reference**, a link table, embedded on the other side (assumed)
- product_tag → product_tag_product_product_rel, product_tag_product_template_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template → product_tag_product_template_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **fanout_unmeasured** (product_tag_product_product_rel): product_tag_product_product_rel has no rows per product_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (product_tag_product_template_rel): product_tag_product_template_rel has no rows per product_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
  canBeExpensed: bool,  // can_be_expensed
  purchaseMethod: string,  // purchase_method
  purchaseLineWarnMsg: string,  // purchase_line_warn_msg
  lotValuated: bool,  // lot_valuated
  serviceType: string,  // service_type
  reinvoicePolicy: string,  // reinvoice_policy
  invoicePolicy: string,  // invoice_policy
  saleDelay: object,  // sale_delay
  saleLineWarnMsg: string,  // sale_line_warn_msg
  projectId: object,  // project_id
  projectTemplateId: object,  // project_template_id
  taskTemplateId: object,  // task_template_id
  serviceUpsellThreshold: double,  // service_upsell_threshold
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
- product_base_unit, product_category, res_company, res_users, ir_sequence, uom_uom → product_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- uom_uom → product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (product_template_uom_uom_rel): product_template_uom_uom_rel has no rows per product_template in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (product_template_uom_uom_rel): product_template_uom_uom_rel is embedded in product_template, but deleting a uom_uom row cascades to its product_template_uom_uom_rel: the app must pull them from every product_template document, or keep product_template_uom_uom_rel separate
- **no_access_evidence** (product_template): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (product_template): LOB column(s) purchase_line_warn_msg, sale_line_warn_msg measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## productTemplateAttributeValue

From `product_template_attribute_value` with `product_template_attribute_excluded_value_ids_rel`, `product_template_attribute_value_purchase_order_line_rel`, `product_template_attribute_value_sale_order_line_rel`, `product_template_attribute_value_sale_order_template_line_rel`, `template_attribute_value_stock_move_rel` embedded.

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
  saleOrderTemplateLineRel: [{  // product_template_attribute_value_sale_order_template_line_rel, 1:N assumed
    saleOrderTemplateLineId: int,  // sale_order_template_line_id
  }],
  templateAttributeValueStockMoveRel: [{  // template_attribute_value_stock_move_rel, 1:N assumed
    moveId: int,  // move_id
  }],
}
```

Why:
- product_template_attribute_value → product_attribute_custom_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel, product_template_attribute_value_purchase_order_line_rel, product_template_attribute_value_sale_order_line_rel, product_template_attribute_value_sale_order_template_line_rel, template_attribute_value_stock_move_rel: **embed**, a link table, kept as an array on this side (assumed)
- product_template_attribute_value → product_template_attribute_excluded_value_ids_rel, product_variant_combination: **reference**, a link table, embedded on the other side (assumed)
- product_attribute_value, product_attribute, product_template_attribute_line, res_users, product_template → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order_line → product_template_attribute_value_purchase_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → product_template_attribute_value_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_template_line → product_template_attribute_value_sale_order_template_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → template_attribute_value_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (9):
- **fanout_unmeasured** (product_template_attribute_value_purchase_order_line_rel): product_template_attribute_value_purchase_order_line_rel has no rows per product_template_attribute_value in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (product_template_attribute_value_sale_order_line_rel): product_template_attribute_value_sale_order_line_rel has no rows per product_template_attribute_value in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (product_template_attribute_value_sale_order_template_line_rel): product_template_attribute_value_sale_order_template_line_rel has no rows per product_template_attribute_value in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (template_attribute_value_stock_move_rel): template_attribute_value_stock_move_rel has no rows per product_template_attribute_value in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (product_template_attribute_value_purchase_order_line_rel): product_template_attribute_value_purchase_order_line_rel is embedded in product_template_attribute_value, but deleting a purchase_order_line row cascades to its product_template_attribute_value_purchase_order_line_rel: the app must pull them from every product_template_attribute_value document, or keep product_template_attribute_value_purchase_order_line_rel separate
- **cascade_into_embed** (product_template_attribute_value_sale_order_line_rel): product_template_attribute_value_sale_order_line_rel is embedded in product_template_attribute_value, but deleting a sale_order_line row cascades to its product_template_attribute_value_sale_order_line_rel: the app must pull them from every product_template_attribute_value document, or keep product_template_attribute_value_sale_order_line_rel separate
- **cascade_into_embed** (product_template_attribute_value_sale_order_template_line_rel): product_template_attribute_value_sale_order_template_line_rel is embedded in product_template_attribute_value, but deleting a sale_order_template_line row cascades to its product_template_attribute_value_sale_order_template_line_rel: the app must pull them from every product_template_attribute_value document, or keep product_template_attribute_value_sale_order_template_line_rel separate
- **cascade_into_embed** (template_attribute_value_stock_move_rel): template_attribute_value_stock_move_rel is embedded in product_template_attribute_value, but deleting a stock_move row cascades to its template_attribute_value_stock_move_rel: the app must pull them from every product_template_attribute_value document, or keep template_attribute_value_stock_move_rel separate
- **no_access_evidence** (product_template_attribute_value): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectProject

From `project_project` with `project_collaborator`, `project_sale_line_employee_map`, `project_allowed_internal_users_rel`, `project_favorite_user_rel`, `project_project_project_tags_rel` embedded.

```js
{
  _id: int,  // id
  accountId: int,  // account_id
  aliasId: int,  // alias_id
  sequence: int,  // sequence
  partnerId: int,  // partner_id
  companyId: int,  // company_id
  color: int,  // color
  userId: int,  // user_id
  stageId: int,  // stage_id
  lastUpdateId: int,  // last_update_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  accessToken: string,  // access_token
  privacyVisibility: string,  // privacy_visibility
  lastUpdateStatus: string,  // last_update_status
  dateStart: date,  // date_start
  date: date,  // date
  durationTracking: object,  // duration_tracking
  name: object,  // name
  labelTasks: object,  // label_tasks
  taskPropertiesDefinition: object,  // task_properties_definition
  description: string,  // description
  active: bool,  // active
  allowTaskDependencies: bool,  // allow_task_dependencies
  allowMilestones: bool,  // allow_milestones
  allowRecurringTasks: bool,  // allow_recurring_tasks
  isTemplate: bool,  // is_template
  dateLastStageUpdate: date,  // date_last_stage_update
  createDate: date,  // create_date
  writeDate: date,  // write_date
  xPlan2Id: int,  // x_plan2_id
  xPlan3Id: int,  // x_plan3_id
  allowTimesheets: bool,  // allow_timesheets
  allocatedHours: double,  // allocated_hours
  saleLineId: int,  // sale_line_id
  reinvoicedSaleOrderId: int,  // reinvoiced_sale_order_id
  allowBillable: bool,  // allow_billable
  leadId: int,  // lead_id
  timesheetProductId: int,  // timesheet_product_id
  billingType: string,  // billing_type
  projectCollaborator: [{  // project_collaborator, 1:N derived
    partnerId: int,  // partner_id
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    accessMode: string,  // access_mode
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  projectSaleLineEmployeeMap: [{  // project_sale_line_employee_map, 1:N derived
    employeeId: int,  // employee_id
    id: int,  // id
    saleLineId: int,  // sale_line_id
    currencyId: int,  // currency_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    cost: decimal,  // cost
    isCostChanged: bool,  // is_cost_changed
    createDate: date,  // create_date
    writeDate: date,  // write_date
    priceUnit: double,  // price_unit
  }],
  projectAllowedInternalUsersRel: [{  // project_allowed_internal_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
  projectFavoriteUserRel: [{  // project_favorite_user_rel, 1:N assumed
    userId: int,  // user_id
  }],
  projectTagsRel: [{  // project_project_project_tags_rel, 1:N assumed
    projectTagsId: int,  // project_tags_id
  }],
}
```

Why:
- project_project → account_analytic_line, project_milestone, project_task, project_update, purchase_order, res_company, sale_order, sale_order_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_project → project_allowed_internal_users_rel, project_favorite_user_rel, project_project_project_tags_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users → project_allowed_internal_users_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, res_partner → project_collaborator: **reference**, it is embedded under another parent; this one is referenced (derived)
- project_project → project_collaborator, project_sale_line_employee_map: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → project_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)
- account_analytic_account, mail_alias, res_company, res_users, project_update, crm_lead, res_partner, sale_order, sale_order_line, project_project_stage, product_product → project_project: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_tags → project_project_project_tags_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, res_currency, hr_employee, sale_order_line → project_sale_line_employee_map: **reference**, it is embedded under another parent; this one is referenced (derived)
- project_project → project_task_type_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **cascade_into_embed** (project_allowed_internal_users_rel): project_allowed_internal_users_rel is embedded in project_project, but deleting a res_users row cascades to its project_allowed_internal_users_rel: the app must pull them from every project_project document, or keep project_allowed_internal_users_rel separate
- **cascade_into_embed** (project_favorite_user_rel): project_favorite_user_rel is embedded in project_project, but deleting a res_users row cascades to its project_favorite_user_rel: the app must pull them from every project_project document, or keep project_favorite_user_rel separate
- **cascade_into_embed** (project_project_project_tags_rel): project_project_project_tags_rel is embedded in project_project, but deleting a project_tags row cascades to its project_project_project_tags_rel: the app must pull them from every project_project document, or keep project_project_project_tags_rel separate
- **no_access_evidence** (project_project): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (project_project): LOB column(s) description measured max 146 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## projectRole

From `project_role` with `project_role_project_task_rel`, `project_role_res_users_rel` embedded.

```js
{
  _id: int,  // id
  color: int,  // color
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  projectTaskRel: [{  // project_role_project_task_rel, 1:N assumed
    projectTaskId: int,  // project_task_id
  }],
  resUsersRel: [{  // project_role_res_users_rel, 1:N assumed
    resUsersId: int,  // res_users_id
  }],
}
```

Why:
- res_users → project_role: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_role → project_role_project_task_rel, project_role_res_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- project_task → project_role_project_task_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → project_role_res_users_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **fanout_unmeasured** (project_role_res_users_rel): project_role_res_users_rel has no rows per project_role in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (project_role_project_task_rel): project_role_project_task_rel is embedded in project_role, but deleting a project_task row cascades to its project_role_project_task_rel: the app must pull them from every project_role document, or keep project_role_project_task_rel separate
- **cascade_into_embed** (project_role_res_users_rel): project_role_res_users_rel is embedded in project_role, but deleting a res_users row cascades to its project_role_res_users_rel: the app must pull them from every project_role document, or keep project_role_res_users_rel separate
- **no_access_evidence** (project_role): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectTags

From `project_tags` with `project_tags_project_task_rel` embedded.

```js
{
  _id: int,  // id
  color: int,  // color
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: object,  // name
  createDate: date,  // create_date
  writeDate: date,  // write_date
  projectTaskRel: [{  // project_tags_project_task_rel, 1:N assumed
    projectTaskId: int,  // project_task_id
  }],
}
```

Why:
- project_tags → project_project_project_tags_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → project_tags: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_tags → project_tags_project_task_rel: **embed**, a link table, kept as an array on this side (assumed)
- project_task → project_tags_project_task_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (2):
- **cascade_into_embed** (project_tags_project_task_rel): project_tags_project_task_rel is embedded in project_tags, but deleting a project_task row cascades to its project_tags_project_task_rel: the app must pull them from every project_tags document, or keep project_tags_project_task_rel separate
- **no_access_evidence** (project_tags): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectTask

From `project_task` with `task_dependencies_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  stageId: int,  // stage_id
  projectId: int,  // project_id
  partnerId: int,  // partner_id
  companyId: int,  // company_id
  color: int,  // color
  displayedImageId: int,  // displayed_image_id
  parentId: int,  // parent_id
  milestoneId: int,  // milestone_id
  recurrenceId: int,  // recurrence_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  accessToken: string,  // access_token
  name: string,  // name
  priority: string,  // priority
  state: string,  // state
  partnerPhone: string,  // partner_phone
  emailFrom: string,  // email_from
  htmlFieldHistory: object,  // html_field_history
  durationTracking: object,  // duration_tracking
  taskProperties: object,  // task_properties
  description: string,  // description
  workingHoursOpen: decimal,  // working_hours_open
  workingHoursClose: decimal,  // working_hours_close
  active: bool,  // active
  displayInProject: bool,  // display_in_project
  recurringTask: bool,  // recurring_task
  isTemplate: bool,  // is_template
  hasTemplateAncestor: bool,  // has_template_ancestor
  createDate: date,  // create_date
  writeDate: date,  // write_date
  dateEnd: date,  // date_end
  dateAssign: date,  // date_assign
  dateDeadline: date,  // date_deadline
  dateLastStageUpdate: date,  // date_last_stage_update
  ratingLastValue: double,  // rating_last_value
  allocatedHours: double,  // allocated_hours
  workingDaysOpen: double,  // working_days_open
  workingDaysClose: double,  // working_days_close
  remainingHours: double,  // remaining_hours
  effectiveHours: double,  // effective_hours
  totalHoursSpent: double,  // total_hours_spent
  progress: double,  // progress
  overtime: double,  // overtime
  subtaskEffectiveHours: double,  // subtask_effective_hours
  saleOrderId: int,  // sale_order_id
  saleLineId: int,  // sale_line_id
  taskDependenciesRel: [{  // task_dependencies_rel, 1:N assumed
    taskId: int,  // task_id
  }],
}
```

Why:
- project_task → account_analytic_line, project_task, project_task_user_rel, res_company, sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_task → project_role_project_task_rel, project_tags_project_task_rel, task_dependencies_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, ir_attachment, project_milestone, res_partner, project_project, project_task_recurrence, sale_order_line, sale_order, project_task_type → project_task: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_task → task_dependencies_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (2):
- **no_access_evidence** (project_task): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (project_task): LOB column(s) description measured max 2322 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## projectTaskType

From `project_task_type` with `project_task_type_rel` embedded.

```js
{
  _id: int,  // id
  sequence: int,  // sequence
  mailTemplateId: int,  // mail_template_id
  ratingTemplateId: int,  // rating_template_id
  rottingThresholdDays: int,  // rotting_threshold_days
  userId: int,  // user_id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  ratingStatus: string,  // rating_status
  ratingStatusPeriod: string,  // rating_status_period
  name: object,  // name
  active: bool,  // active
  fold: bool,  // fold
  autoValidationState: bool,  // auto_validation_state
  ratingActive: bool,  // rating_active
  ratingRequestDeadline: date,  // rating_request_deadline
  createDate: date,  // create_date
  writeDate: date,  // write_date
  smsTemplateId: int,  // sms_template_id
  rel: [{  // project_task_type_rel, 1:N assumed
    projectId: int,  // project_id
  }],
}
```

Why:
- project_task_type → project_task, project_task_user_rel: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, mail_template, sms_template → project_task_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_project → project_task_type_rel: **reference**, a link table, embedded on the other side (assumed)
- project_task_type → project_task_type_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (2):
- **cascade_into_embed** (project_task_type_rel): project_task_type_rel is embedded in project_task_type, but deleting a project_project row cascades to its project_task_type_rel: the app must pull them from every project_task_type document, or keep project_task_type_rel separate
- **no_access_evidence** (project_task_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
  projectId: int,  // project_id
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
- res_company, res_users, res_currency, res_partner, account_fiscal_position, account_incoterms, account_payment_term, stock_picking_type, project_project → purchase_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
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
- res_company, res_users, stock_location, purchase_order, stock_warehouse_orderpoint, res_partner, product_product, sale_order_line, uom_uom → purchase_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move → purchase_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- purchase_order_line → purchase_order_line_accrual_move_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (4):
- **fanout_unmeasured** (purchase_order_line_accrual_move_rel): purchase_order_line_accrual_move_rel has no rows per purchase_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (purchase_order_line_accrual_move_rel): purchase_order_line_accrual_move_rel is embedded in purchase_order_line, but deleting a account_move row cascades to its purchase_order_line_accrual_move_rel: the app must pull them from every purchase_order_line document, or keep purchase_order_line_accrual_move_rel separate
- **no_access_evidence** (purchase_order_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (purchase_order_line): LOB column(s) name measured max 25 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## quotationDocument

From `quotation_document` with `header_footer_quotation_template_rel`, `quotation_document_sale_order_rel`, `quotation_document_sale_pdf_form_field_rel` embedded.

```js
{
  _id: int,  // id
  irAttachmentId: int,  // ir_attachment_id
  sequence: int,  // sequence
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  documentType: string,  // document_type
  active: bool,  // active
  addByDefault: bool,  // add_by_default
  createDate: date,  // create_date
  writeDate: date,  // write_date
  headerFooterQuotationTemplateRel: [{  // header_footer_quotation_template_rel, 1:N assumed
    saleOrderTemplateId: int,  // sale_order_template_id
  }],
  saleOrderRel: [{  // quotation_document_sale_order_rel, 1:N assumed
    saleOrderId: int,  // sale_order_id
  }],
  salePdfFormFieldRel: [{  // quotation_document_sale_pdf_form_field_rel, 1:N assumed
    salePdfFormFieldId: int,  // sale_pdf_form_field_id
  }],
}
```

Why:
- sale_order_template → header_footer_quotation_template_rel: **reference**, a link table, embedded on the other side (assumed)
- quotation_document → header_footer_quotation_template_rel, quotation_document_sale_order_rel, quotation_document_sale_pdf_form_field_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_users, ir_attachment → quotation_document: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- sale_order → quotation_document_sale_order_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_pdf_form_field → quotation_document_sale_pdf_form_field_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **fanout_unmeasured** (quotation_document_sale_order_rel): quotation_document_sale_order_rel has no rows per quotation_document in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (header_footer_quotation_template_rel): header_footer_quotation_template_rel is embedded in quotation_document, but deleting a sale_order_template row cascades to its header_footer_quotation_template_rel: the app must pull them from every quotation_document document, or keep header_footer_quotation_template_rel separate
- **cascade_into_embed** (quotation_document_sale_order_rel): quotation_document_sale_order_rel is embedded in quotation_document, but deleting a sale_order row cascades to its quotation_document_sale_order_rel: the app must pull them from every quotation_document document, or keep quotation_document_sale_order_rel separate
- **cascade_into_embed** (quotation_document_sale_pdf_form_field_rel): quotation_document_sale_pdf_form_field_rel is embedded in quotation_document, but deleting a sale_pdf_form_field row cascades to its quotation_document_sale_pdf_form_field_rel: the app must pull them from every quotation_document document, or keep quotation_document_sale_pdf_form_field_rel separate
- **no_access_evidence** (quotation_document): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resCompany

From `res_company` with `res_company_spreadsheet_dashboard_rel`, `res_company_users_rel` embedded.

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
  lunchNotifyMessage: object,  // lunch_notify_message
  lunchMinimumThreshold: double,  // lunch_minimum_threshold
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
  hrPresenceControlEmailAmount: int,  // hr_presence_control_email_amount
  contractExpirationNoticePeriod: int,  // contract_expiration_notice_period
  workPermitExpirationNoticePeriod: int,  // work_permit_expiration_notice_period
  hrPresenceControlIpList: array,  // hr_presence_control_ip_list
  employeePropertiesDefinition: object,  // employee_properties_definition
  hrPresenceControlLogin: bool,  // hr_presence_control_login
  hrPresenceControlEmail: bool,  // hr_presence_control_email
  hrPresenceControlIp: bool,  // hr_presence_control_ip
  hrPresenceControlAttendance: bool,  // hr_presence_control_attendance
  internalTransitLocationId: int,  // internal_transit_location_id
  stockMailConfirmationTemplateId: int,  // stock_mail_confirmation_template_id
  annualInventoryDay: int,  // annual_inventory_day
  horizonDays: int,  // horizon_days
  annualInventoryMonth: string,  // annual_inventory_month
  stockConfirmationType: string,  // stock_confirmation_type
  pickingPolicy: string,  // picking_policy
  stockMoveEmailValidation: bool,  // stock_move_email_validation
  stockTextConfirmation: bool,  // stock_text_confirmation
  expenseJournalId: int,  // expense_journal_id
  projectTimeModeId: int,  // project_time_mode_id
  timesheetEncodeUomId: int,  // timesheet_encode_uom_id
  internalProjectId: int,  // internal_project_id
  externalCode: string,  // external_code
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
  leaveTimesheetTaskId: int,  // leave_timesheet_task_id
  returnValidityDays: int,  // return_validity_days
  securityLead: int,  // security_lead
  allowSpontaneousReturns: bool,  // allow_spontaneous_returns
  spreadsheetDashboardRel: [{  // res_company_spreadsheet_dashboard_rel, 1:N assumed
    spreadsheetDashboardId: int,  // spreadsheet_dashboard_id
  }],
  usersRel: [{  // res_company_users_rel, 1:N assumed
    userId: int,  // user_id
  }],
}
```

Why:
- res_company → account_account_res_company_rel, account_payment_method_line_res_company_rel, iap_account_res_company_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company → account_analytic_account, account_analytic_applicability, account_analytic_distribution_model, account_analytic_line, account_bank_statement, account_bank_statement_line, account_cash_rounding, account_fiscal_position, account_journal, account_lock_exception, account_move, account_move_line, account_partial_reconcile, account_payment, account_payment_term, account_reconcile_model, account_reconcile_model_line, account_tax, account_tax_group, account_tax_repartition_line, crm_lead, crm_team, digest_digest, event_event, event_lead_rule, event_registration, fleet_service_type, hr_department, hr_employee, hr_employee_type, hr_job, hr_leave, hr_leave_accrual_plan, hr_leave_allocation, hr_leave_mandatory_day, hr_time_rule, hr_version, hr_work_location, ir_attachment, ir_default, ir_sequence, lunch_location, lunch_product_category, lunch_supplier, mail_activity_plan, mail_message, maintenance_equipment_category, maintenance_team, onboarding_progress, onboarding_progress_step, payment_provider, payment_token, payment_transaction, product_category, product_combo, product_combo_item, product_pricelist, product_pricelist_item, product_supplierinfo, product_template, product_uom, project_project, project_project_stage, project_task, purchase_order, purchase_order_line, res_company, res_partner, res_partner_bank, res_users, resource_calendar, resource_calendar_leaves, resource_resource, sale_order, sale_order_line, sale_order_template, sale_order_template_line, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_package_type, stock_picking, stock_picking_batch, stock_picking_type, stock_putaway_rule, stock_quant, stock_route, stock_rule, stock_storage_category, stock_warehouse, stock_warehouse_orderpoint, website: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company → account_fiscal_position_account, account_report_external_value, fleet_vehicle_log_services, product_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_company → fleet_vehicle, fleet_vehicle_log_contract, fleet_vehicle_model, hr_expense, lunch_order, lunch_product, maintenance_equipment, maintenance_request: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_company → lunch_topping, res_currency_rate: **reference**, another parent owns it; this one is referenced (derived)
- account_account, res_country, account_move, account_fiscal_position, account_tax, mail_alias_domain, account_journal, ir_sequence, res_users, res_currency, ir_ui_view, account_incoterms, project_project, stock_location, project_task, barcode_nomenclature, report_paperformat, res_partner, uom_uom, resource_calendar, product_product, mail_template, sms_template → res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company → res_company_spreadsheet_dashboard_rel, res_company_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- spreadsheet_dashboard → res_company_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → res_company_users_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **fanout_unmeasured** (res_company_spreadsheet_dashboard_rel): res_company_spreadsheet_dashboard_rel has no rows per res_company in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (res_company_spreadsheet_dashboard_rel): res_company_spreadsheet_dashboard_rel is embedded in res_company, but deleting a spreadsheet_dashboard row cascades to its res_company_spreadsheet_dashboard_rel: the app must pull them from every res_company document, or keep res_company_spreadsheet_dashboard_rel separate
- **cascade_into_embed** (res_company_users_rel): res_company_users_rel is embedded in res_company, but deleting a res_users row cascades to its res_company_users_rel: the app must pull them from every res_company document, or keep res_company_users_rel separate
- **no_access_evidence** (res_company): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **csv_list** (res_company)

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
- res_country → account_account_tag, account_fiscal_position, account_report, account_tax, account_tax_group, clearing_label, crm_lead, event_event, hr_departure_reason, hr_employee, hr_employee_type, hr_payroll_structure_type, hr_time_rule, hr_version, hr_work_entry_type, mail_guest, payment_transaction, res_city, res_company, res_country_state, res_partner, res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country → crm_iap_lead_mining_request_res_country_rel, module_country, payment_country_rel, payment_method_res_country_rel: **reference**, a link table, embedded on the other side (assumed)
- ir_ui_view, res_users, res_currency → res_country: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country_group → res_country_res_country_group_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country → res_country_res_country_group_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (3):
- **cascade_into_embed** (res_country_res_country_group_rel): res_country_res_country_group_rel is embedded in res_country, but deleting a res_country_group row cascades to its res_country_res_country_group_rel: the app must pull them from every res_country document, or keep res_country_res_country_group_rel separate
- **no_access_evidence** (res_country): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (res_country): LOB column(s) address_format measured max 87 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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

Open questions (5):
- **fanout_unmeasured** (res_country_group_pricelist_rel): res_country_group_pricelist_rel has no rows per res_country_group in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (res_country_group_pricelist_rel): res_country_group_pricelist_rel is embedded in res_country_group, but deleting a product_pricelist row cascades to its res_country_group_pricelist_rel: the app must pull them from every res_country_group document, or keep res_country_group_pricelist_rel separate
- **cascade_into_embed** (res_country_group_res_country_state_rel): res_country_group_res_country_state_rel is embedded in res_country_group, but deleting a res_country_state row cascades to its res_country_group_res_country_state_rel: the app must pull them from every res_country_group document, or keep res_country_group_res_country_state_rel separate
- **no_access_evidence** (res_country_group): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## resGroups

From `res_groups` with `res_groups_implied_rel`, `res_groups_report_rel`, `res_groups_spreadsheet_dashboard_rel`, `res_groups_users_rel` embedded.

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
  usersRel: [{  // res_groups_users_rel, 1:N assumed
    uid: int,  // uid
  }],
}
```

Why:
- res_groups → digest_tip, discuss_channel, ir_access: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_groups → discuss_channel_res_groups_rel, ir_act_server_group_rel, ir_act_window_group_rel, ir_embedded_actions_res_groups_rel, ir_model_fields_group_rel, ir_ui_menu_group_rel, ir_ui_view_group_rel, mail_canned_response_res_groups_rel, res_groups_implied_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, res_groups_privilege → res_groups: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_groups → res_groups_implied_rel, res_groups_report_rel, res_groups_spreadsheet_dashboard_rel, res_groups_users_rel: **embed**, a link table, kept as an array on this side (assumed)
- ir_act_report_xml → res_groups_report_rel: **reference**, a link table, embedded on the other side (assumed)
- spreadsheet_dashboard → res_groups_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → res_groups_users_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (4):
- **cascade_into_embed** (res_groups_report_rel): res_groups_report_rel is embedded in res_groups, but deleting a ir_act_report_xml row cascades to its res_groups_report_rel: the app must pull them from every res_groups document, or keep res_groups_report_rel separate
- **cascade_into_embed** (res_groups_spreadsheet_dashboard_rel): res_groups_spreadsheet_dashboard_rel is embedded in res_groups, but deleting a spreadsheet_dashboard row cascades to its res_groups_spreadsheet_dashboard_rel: the app must pull them from every res_groups document, or keep res_groups_spreadsheet_dashboard_rel separate
- **cascade_into_embed** (res_groups_users_rel): res_groups_users_rel is embedded in res_groups, but deleting a res_users row cascades to its res_groups_users_rel: the app must pull them from every res_groups document, or keep res_groups_users_rel separate
- **no_access_evidence** (res_groups): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resLang

From `res_lang` with `res_lang_survey_survey_rel` embedded.

```js
{
  _id: int,  // id
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  name: string,  // name
  code: string,  // code
  isoCode: string,  // iso_code
  urlCode: string,  // url_code
  direction: string,  // direction
  dateFormat: string,  // date_format
  timeFormat: string,  // time_format
  weekStart: string,  // week_start
  grouping: string,  // grouping
  decimalPoint: string,  // decimal_point
  thousandsSep: string,  // thousands_sep
  active: bool,  // active
  createDate: date,  // create_date
  writeDate: date,  // write_date
  surveySurveyRel: [{  // res_lang_survey_survey_rel, 1:N assumed
    surveySurveyId: int,  // survey_survey_id
  }],
}
```

Why:
- res_lang → crm_lead: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_lang → ir_exports_res_lang_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → res_lang: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_lang → res_lang_survey_survey_rel: **embed**, a link table, kept as an array on this side (assumed)
- survey_survey → res_lang_survey_survey_rel: **reference**, a link table, embedded on the other side (assumed)
- res_lang → survey_user_input: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (3):
- **fanout_unmeasured** (res_lang_survey_survey_rel): res_lang_survey_survey_rel has no rows per res_lang in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (res_lang_survey_survey_rel): res_lang_survey_survey_rel is embedded in res_lang, but deleting a survey_survey row cascades to its res_lang_survey_survey_rel: the app must pull them from every res_lang document, or keep res_lang_survey_survey_rel separate
- **no_access_evidence** (res_lang): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
  calendarLastNotifAck: date,  // calendar_last_notif_ack
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
- res_partner → account_analytic_account, account_analytic_distribution_model, account_analytic_line, account_bank_statement_line, account_move, account_move_line, account_payment, account_reconcile_model, account_reconcile_model_line, calendar_attendee, crm_lead, customer_product_reference, discuss_channel_member, discuss_channel_rtc_session, event_event, event_registration, hr_employee, hr_version, hr_work_location, lunch_supplier, mail_followers, mail_message, mail_message_reaction, mail_notification, mail_push_device, mail_scheduled_message, payment_token, payment_transaction, product_supplierinfo, project_project, project_task, purchase_order, purchase_order_line, rating_rating, res_company, res_partner, res_partner_bank, res_users, res_users_settings_volumes, sale_order, sale_order_line, sms_sms, stock_move, stock_move_line, stock_picking, stock_quant, stock_rule, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner → account_reconcile_model_res_partner_rel, calendar_event_res_partner_rel, fleet_vehicle_model_vendors, ir_act_server_res_partner_rel, mail_mail_res_partner_cc_rel, mail_mail_res_partner_rel, mail_message_res_partner_bookmarked_rel, mail_message_res_partner_cc_rel, mail_message_res_partner_rel, mail_scheduled_message_res_partner_cc_rel, mail_scheduled_message_res_partner_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → calendar_filters, fleet_vehicle_log_services, project_collaborator: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_partner → fleet_vehicle, fleet_vehicle_log_contract, fleet_vehicle_odometer, hr_expense, maintenance_equipment, survey_user_input: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_partner → fleet_vehicle_assignation_log: **reference**, another parent owns it; this one is referenced (derived)
- res_users, res_city, res_company, res_country, account_incoterms, res_partner_industry, ir_act_report_xml, res_country_state → res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner_category → res_partner_res_partner_category_rel: **reference**, a link table, embedded on the other side (assumed)
- res_partner → res_partner_res_partner_category_rel, res_partner_stock_lot_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_lot → res_partner_stock_lot_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **fanout_unmeasured** (res_partner_stock_lot_rel): res_partner_stock_lot_rel has no rows per res_partner in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (res_partner_res_partner_category_rel): res_partner_res_partner_category_rel is embedded in res_partner, but deleting a res_partner_category row cascades to its res_partner_res_partner_category_rel: the app must pull them from every res_partner document, or keep res_partner_res_partner_category_rel separate
- **cascade_into_embed** (res_partner_stock_lot_rel): res_partner_stock_lot_rel is embedded in res_partner, but deleting a stock_lot row cascades to its res_partner_stock_lot_rel: the app must pull them from every res_partner document, or keep res_partner_stock_lot_rel separate
- **no_access_evidence** (res_partner): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (res_partner): LOB column(s) comment, picking_warn_msg, purchase_warn_msg, sale_warn_msg measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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

Open questions (2):
- **cascade_into_embed** (res_role_res_users_rel): res_role_res_users_rel is embedded in res_role, but deleting a res_users row cascades to its res_role_res_users_rel: the app must pull them from every res_role document, or keep res_role_res_users_rel separate
- **no_access_evidence** (res_role): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resUsers

From `res_users` with `account_analytic_line_calendar_employee`, `auth_totp_device`, `calendar_filters`, `gamification_karma_tracking`, `hr_user_work_entry_employee`, `res_users_apikeys`, `picking_type_favorite_user_rel`, `res_users_spreadsheet_dashboard_favorite_filters_rel`, `res_users_spreadsheet_dashboard_rel`, `res_users_survey_survey_rel`, `res_users_web_tour_tour_rel` embedded.

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
  primaryCalendarId: int,  // primary_calendar_id
  karma: int,  // karma
  rankId: int,  // rank_id
  nextRankId: int,  // next_rank_id
  lastLunchLocationId: int,  // last_lunch_location_id
  odoobotState: string,  // odoobot_state
  odoobotFailed: bool,  // odoobot_failed
  saleTeamId: int,  // sale_team_id
  propertyWarehouseId: object,  // property_warehouse_id
  accountAnalyticLineCalendarEmployee: [{  // account_analytic_line_calendar_employee, 1:N assumed
    id: int,  // id
    employeeId: int,  // employee_id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    checked: bool,  // checked
    active: bool,  // active
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  authTotpDevice: [{  // auth_totp_device, 1:N assumed
    id: int,  // id
    name: string,  // name
    scope: string,  // scope
    expirationDate: date,  // expiration_date
    index: string,  // index
    key: string,  // key
    createDate: date,  // create_date
  }],
  calendarFilters: [{  // calendar_filters, 1:N derived
    partnerId: int,  // partner_id
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    active: bool,  // active
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  gamificationKarmaTracking: [{  // gamification_karma_tracking, 1:N derived
    id: int,  // id
    oldValue: int,  // old_value
    newValue: int,  // new_value
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    originRef: string,  // origin_ref
    originRefModelName: string,  // origin_ref_model_name
    reason: string,  // reason
    consolidated: bool,  // consolidated
    trackingDate: date,  // tracking_date
    createDate: date,  // create_date
    writeDate: date,  // write_date
  }],
  hrUserWorkEntryEmployee: [{  // hr_user_work_entry_employee, 1:N assumed
    employeeId: int,  // employee_id
    id: int,  // id
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    active: bool,  // active
    isChecked: bool,  // is_checked
    createDate: date,  // create_date
    writeDate: date,  // write_date
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
  surveySurveyRel: [{  // res_users_survey_survey_rel, 1:N assumed
    surveySurveyId: int,  // survey_survey_id
  }],
  webTourTourRel: [{  // res_users_web_tour_tour_rel, 1:N assumed
    webTourTourId: int,  // web_tour_tour_id
  }],
}
```

Why:
- res_users → account_account, account_account_tag, account_analytic_account, account_analytic_applicability, account_analytic_distribution_model, account_analytic_line, account_analytic_plan, account_bank_statement, account_bank_statement_line, account_cash_rounding, account_fiscal_position, account_full_reconcile, account_incoterms, account_journal, account_journal_group, account_lock_exception, account_move, account_move_line, account_partial_reconcile, account_payment, account_payment_method, account_payment_method_line, account_payment_term, account_reconcile_model, account_reconcile_model_line, account_report, account_report_expression, account_report_line, account_tax, account_tax_group, account_tax_repartition_line, auth_passkey_key, barcode_nomenclature, barcode_rule, base_import_mapping, bus_bus, calendar_alarm, calendar_attendee, calendar_calendar, calendar_event, calendar_event_type, calendar_recurrence, calendar_user, clearing_label, crm_iap_lead_helpers, crm_iap_lead_industry, crm_iap_lead_industry_division, crm_iap_lead_mining_request, crm_iap_lead_role, crm_iap_lead_seniority, crm_lead, crm_lost_reason, crm_recurring_plan, crm_stage, crm_tag, crm_team, crm_team_member, customer_product_reference, decimal_precision, digest_digest, digest_tip, discuss_call_history, discuss_category, discuss_channel, discuss_channel_member, discuss_channel_rtc_session, discuss_gif_favorite, event_event, event_event_ticket, event_lead_rule, event_mail, event_mail_registration, event_mail_slot, event_question, event_question_answer, event_registration, event_slot, event_stage, event_tag, event_tag_category, event_type, event_type_ticket, fetchmail_server, fleet_service_type, fleet_vehicle_model_brand, fleet_vehicle_model_category, fleet_vehicle_state, fleet_vehicle_tag, gamification_badge, gamification_badge_user, gamification_challenge, gamification_challenge_line, gamification_goal, gamification_goal_definition, gamification_karma_rank, hr_department, hr_departure_reason, hr_employee, hr_employee_category, hr_employee_departure, hr_employee_skill, hr_employee_type, hr_job, hr_job_skill, hr_leave, hr_leave_accrual_plan, hr_leave_allocation, hr_leave_mandatory_day, hr_payroll_structure_type, hr_resume_line, hr_resume_line_type, hr_skill, hr_skill_level, hr_skill_type, hr_time_rule, hr_version, hr_work_entry_type, hr_work_location, html_editor_converter_test, html_editor_converter_test_sub, iap_account, iap_service, ir_access, ir_act_report_xml, ir_act_server, ir_act_window, ir_actions_todo, ir_asset, ir_attachment, ir_config_parameter, ir_cron, ir_cron_trigger, ir_default, ir_embedded_actions, ir_exports, ir_filters, ir_mail_server, ir_model, ir_model_constraint, ir_model_data, ir_model_fields, ir_model_fields_selection, ir_model_relation, ir_module_category, ir_module_module, ir_sequence, ir_ui_menu, ir_ui_view, ir_ui_view_custom, l10n_us_res_county, lunch_alert, lunch_cashmove, lunch_location, lunch_product_category, lunch_supplier, mail_activity, mail_activity_plan, mail_activity_plan_template, mail_activity_type, mail_alias, mail_alias_domain, mail_blacklist, mail_canned_response, mail_followers, mail_gateway_allowed, mail_guest, mail_ice_server, mail_link_preview, mail_mail, mail_message, mail_message_link_preview, mail_message_subtype, mail_poll, mail_poll_option, mail_poll_vote, mail_presence, mail_push_device, mail_scheduled_message, mail_template, maintenance_equipment_category, onboarding_onboarding, onboarding_onboarding_step, onboarding_progress, onboarding_progress_step, payment_data, payment_method, payment_provider, payment_token, payment_transaction, phone_blacklist, portal_entry, privacy_log, product_attribute, product_attribute_custom_value, product_attribute_value, product_base_unit, product_category, product_combo, product_combo_item, product_document, product_pricelist, product_pricelist_item, product_product, product_removal, product_supplierinfo, product_tag, product_template, product_template_attribute_line, product_template_attribute_value, product_uom, project_milestone, project_project, project_project_stage, project_role, project_tags, project_task, project_task_recurrence, project_task_type, project_task_user_rel, project_update, purchase_order, purchase_order_line, quotation_document, rating_rating, report_layout, report_paperformat, res_city, res_company, res_country, res_country_group, res_country_state, res_currency, res_device_log, res_groups, res_groups_privilege, res_lang, res_partner, res_partner_bank, res_partner_category, res_partner_industry, res_role, res_users, res_users_deletion, res_users_log, res_users_settings, res_users_settings_embedded_action, res_users_settings_volumes, resource_calendar, resource_calendar_leaves, resource_resource, return_reason, sale_order, sale_order_line, sale_order_template, sale_order_template_line, sale_pdf_form_field, sms_sms, sms_template, spreadsheet_dashboard, spreadsheet_dashboard_favorite_filters, spreadsheet_dashboard_group, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_package_type, stock_picking, stock_picking_batch, stock_picking_type, stock_putaway_rule, stock_quant, stock_reference, stock_route, stock_rule, stock_scrap_reason_tag, stock_storage_category, stock_storage_category_capacity, stock_warehouse, stock_warehouse_orderpoint, uom_uom, utm_campaign, utm_medium, utm_source, utm_stage, utm_tag, web_tour_tour, website: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_analytic_line_calendar_employee, account_fiscal_position_account, account_payment_term_line, account_report_column, account_report_external_value, calendar_filters, crm_lead_scoring_frequency, crm_lead_scoring_frequency_field, discuss_voice_metadata, event_registration_answer, event_type_mail, fleet_vehicle_log_services, gamification_karma_tracking, hr_leave_accrual_level, hr_time_rule_allocation_log, hr_user_work_entry_employee, iap_service_pack, ir_act_client, ir_act_url, ir_act_window_view, ir_actions, ir_actions_server_history, ir_cron_progress, ir_exports_line, ir_module_module_exclusion, mail_call_artifact, mail_message_schedule, mail_message_translation, mail_push, product_value, project_collaborator, project_sale_line_employee_map, properties_base_definition, resource_calendar_attendance, sms_tracker, spreadsheet_dashboard_share, survey_question_answer, web_tour_tour_step: **reference**, it is embedded under another parent; this one is referenced (derived)
- hr_employee → account_analytic_line_calendar_employee: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → account_analytic_line_calendar_employee, auth_totp_device, hr_user_work_entry_employee, res_users_apikeys: **embed**, owned by its parent (cascade delete or ordinal key) (assumed)
- res_partner → calendar_filters: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → calendar_filters, gamification_karma_tracking: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users → digest_digest_res_users_rel, digest_tip_res_users_rel, gamification_challenge_users_rel, gamification_invited_user_ids_rel, iap_account_res_users_rel, ir_filters_res_users_rel, lunch_product_favorite_user_rel, maintenance_request_res_users_rel, maintenance_team_users_rel, project_allowed_internal_users_rel, project_favorite_user_rel, project_role_res_users_rel, rel_badge_auth_users, res_company_users_rel, res_groups_users_rel, res_role_res_users_rel, spreadsheet_dashboard_allowed_users_rel, team_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → fleet_vehicle, fleet_vehicle_log_contract, fleet_vehicle_model, fleet_vehicle_odometer, hr_expense, hr_expense_product_job_position_limit, lunch_order, lunch_product, maintenance_equipment, maintenance_request, maintenance_stage, maintenance_team, survey_survey, survey_user_input: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_users → fleet_vehicle_assignation_log, hr_employee_location, ir_sequence_date_range, lunch_topping, res_currency_rate, survey_question, survey_user_input_line: **reference**, another parent owns it; this one is referenced (derived)
- hr_employee → hr_user_work_entry_employee: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_picking_type → picking_type_favorite_user_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → picking_type_favorite_user_rel, res_users_spreadsheet_dashboard_favorite_filters_rel, res_users_spreadsheet_dashboard_rel, res_users_survey_survey_rel, res_users_web_tour_tour_rel: **embed**, a link table, kept as an array on this side (assumed)
- res_company, lunch_location, gamification_karma_rank, res_partner, calendar_calendar, crm_team → res_users: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- spreadsheet_dashboard_favorite_filters → res_users_spreadsheet_dashboard_favorite_filters_rel: **reference**, a link table, embedded on the other side (assumed)
- spreadsheet_dashboard → res_users_spreadsheet_dashboard_rel: **reference**, a link table, embedded on the other side (assumed)
- survey_survey → res_users_survey_survey_rel: **reference**, a link table, embedded on the other side (assumed)
- web_tour_tour → res_users_web_tour_tour_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (27):
- **fanout_unmeasured** (account_analytic_line_calendar_employee): account_analytic_line_calendar_employee has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (auth_totp_device): auth_totp_device has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (hr_user_work_entry_employee): hr_user_work_entry_employee has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (res_users_apikeys): res_users_apikeys has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (picking_type_favorite_user_rel): picking_type_favorite_user_rel has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (res_users_spreadsheet_dashboard_favorite_filters_rel): res_users_spreadsheet_dashboard_favorite_filters_rel has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (res_users_spreadsheet_dashboard_rel): res_users_spreadsheet_dashboard_rel has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (res_users_survey_survey_rel): res_users_survey_survey_rel has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (res_users_web_tour_tour_rel): res_users_web_tour_tour_rel has no rows per res_users in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (picking_type_favorite_user_rel): picking_type_favorite_user_rel is embedded in res_users, but deleting a stock_picking_type row cascades to its picking_type_favorite_user_rel: the app must pull them from every res_users document, or keep picking_type_favorite_user_rel separate
- **cascade_into_embed** (res_users_spreadsheet_dashboard_favorite_filters_rel): res_users_spreadsheet_dashboard_favorite_filters_rel is embedded in res_users, but deleting a spreadsheet_dashboard_favorite_filters row cascades to its res_users_spreadsheet_dashboard_favorite_filters_rel: the app must pull them from every res_users document, or keep res_users_spreadsheet_dashboard_favorite_filters_rel separate
- **cascade_into_embed** (res_users_spreadsheet_dashboard_rel): res_users_spreadsheet_dashboard_rel is embedded in res_users, but deleting a spreadsheet_dashboard row cascades to its res_users_spreadsheet_dashboard_rel: the app must pull them from every res_users document, or keep res_users_spreadsheet_dashboard_rel separate
- **cascade_into_embed** (res_users_survey_survey_rel): res_users_survey_survey_rel is embedded in res_users, but deleting a survey_survey row cascades to its res_users_survey_survey_rel: the app must pull them from every res_users document, or keep res_users_survey_survey_rel separate
- **cascade_into_embed** (res_users_web_tour_tour_rel): res_users_web_tour_tour_rel is embedded in res_users, but deleting a web_tour_tour row cascades to its res_users_web_tour_tour_rel: the app must pull them from every res_users document, or keep res_users_web_tour_tour_rel separate
- **lob** (res_users): LOB column(s) signature, out_of_office_message measured max 26 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **lob** (gamification_karma_tracking): LOB column(s) reason measured max 15 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (auth_totp_device): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (calendar_filters): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (gamification_karma_tracking): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (picking_type_favorite_user_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (res_users): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (res_users): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (res_users_apikeys): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (res_users_spreadsheet_dashboard_favorite_filters_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (res_users_spreadsheet_dashboard_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (res_users_survey_survey_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (res_users_web_tour_tour_rel): source index not exercised by any confirmed access pattern; keep or drop

## resourceCalendar

From `resource_calendar` with `resource_calendar_attendance` embedded.

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
  leaveAccrualPlanId: int,  // leave_accrual_plan_id
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
    workEntryTypeId: int,  // work_entry_type_id
  }],
}
```

Why:
- resource_calendar → hr_leave, hr_leave_mandatory_day, hr_payroll_structure_type, hr_time_rule, hr_version, res_company, resource_calendar, resource_calendar_leaves, resource_resource: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, hr_leave_accrual_plan → resource_calendar: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- resource_calendar → resource_calendar_attendance: **embed**, owned by its parent (cascade delete or ordinal key) (derived)
- res_users, hr_work_entry_type → resource_calendar_attendance: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (1):
- **no_access_evidence** (resource_calendar): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
  opportunityId: int,  // opportunity_id
  saleOrderTemplateId: int,  // sale_order_template_id
  warehouseId: int,  // warehouse_id
  pickingPolicy: string,  // picking_policy
  effectiveDate: date,  // effective_date
  margin: decimal,  // margin
  marginPercent: double,  // margin_percent
  customizablePdfFormFields: object,  // customizable_pdf_form_fields
  projectId: int,  // project_id
  tagRel: [{  // sale_order_tag_rel, 1:N assumed
    tagId: int,  // tag_id
  }],
  transactionRel: [{  // sale_order_transaction_rel, 1:N assumed
    transactionId: int,  // transaction_id
  }],
}
```

Why:
- sale_order → account_analytic_line, event_registration, project_project, project_task, sale_order_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- sale_order → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)
- sale_order → quotation_document_sale_order_rel, stock_reference_sale_rel: **reference**, a link table, embedded on the other side (assumed)
- account_analytic_account, utm_campaign, res_company, res_users, res_currency, account_fiscal_position, account_incoterms, account_journal, utm_medium, crm_lead, res_partner, account_payment_term, mail_template, account_payment_method_line, product_pricelist, project_project, sale_order_template, utm_source, crm_team, stock_warehouse → sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- sale_order → sale_order_tag_rel, sale_order_transaction_rel: **embed**, a link table, kept as an array on this side (assumed)
- crm_tag → sale_order_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- payment_transaction → sale_order_transaction_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (5):
- **fanout_unmeasured** (sale_order_transaction_rel): sale_order_transaction_rel has no rows per sale_order in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (sale_order_tag_rel): sale_order_tag_rel is embedded in sale_order, but deleting a crm_tag row cascades to its sale_order_tag_rel: the app must pull them from every sale_order document, or keep sale_order_tag_rel separate
- **cascade_into_embed** (sale_order_transaction_rel): sale_order_transaction_rel is embedded in sale_order, but deleting a payment_transaction row cascades to its sale_order_transaction_rel: the app must pull them from every sale_order document, or keep sale_order_transaction_rel separate
- **no_access_evidence** (sale_order): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (sale_order): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## saleOrderLine

From `sale_order_line` with `sale_order_line_accrual_move_rel`, `sale_order_line_invoice_rel`, `sale_order_line_product_document_rel`, `sale_order_line_stock_route_rel` embedded.

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
  isOptional: bool,  // is_optional
  warehouseId: int,  // warehouse_id
  eventId: int,  // event_id
  eventSlotId: int,  // event_slot_id
  eventTicketId: int,  // event_ticket_id
  margin: decimal,  // margin
  purchasePrice: decimal,  // purchase_price
  marginPercent: double,  // margin_percent
  isService: bool,  // is_service
  expenseId: int,  // expense_id
  projectId: int,  // project_id
  taskId: int,  // task_id
  hasDisplayedWarningUpsell: bool,  // has_displayed_warning_upsell
  remainingHours: double,  // remaining_hours
  accrualMoveRel: [{  // sale_order_line_accrual_move_rel, 1:N assumed
    moveId: int,  // move_id
  }],
  invoiceRel: [{  // sale_order_line_invoice_rel, 1:N assumed
    invoiceLineId: int,  // invoice_line_id
  }],
  productDocumentRel: [{  // sale_order_line_product_document_rel, 1:N assumed
    productDocumentId: int,  // product_document_id
  }],
  stockRouteRel: [{  // sale_order_line_stock_route_rel, 1:N assumed
    stockRouteId: int,  // stock_route_id
  }],
}
```

Why:
- sale_order_line → account_analytic_line, event_registration, product_attribute_custom_value, project_milestone, project_project, project_task, purchase_order_line, sale_order_line, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- sale_order_line → account_tax_sale_order_line_rel, product_template_attribute_value_sale_order_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)
- sale_order_line → project_sale_line_employee_map: **reference**, it is embedded under another parent; this one is referenced (derived)
- product_combo_item, res_company, res_users, res_currency, event_event, event_slot, event_event_ticket, hr_expense, sale_order, res_partner, product_product, uom_uom, project_project, project_task, stock_warehouse → sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_move → sale_order_line_accrual_move_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_line → sale_order_line_accrual_move_rel, sale_order_line_invoice_rel, sale_order_line_product_document_rel, sale_order_line_stock_route_rel: **embed**, a link table, kept as an array on this side (assumed)
- account_move_line → sale_order_line_invoice_rel: **reference**, a link table, embedded on the other side (assumed)
- product_document → sale_order_line_product_document_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → sale_order_line_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (8):
- **fanout_unmeasured** (sale_order_line_accrual_move_rel): sale_order_line_accrual_move_rel has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (sale_order_line_product_document_rel): sale_order_line_product_document_rel has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (sale_order_line_stock_route_rel): sale_order_line_stock_route_rel has no rows per sale_order_line in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (sale_order_line_accrual_move_rel): sale_order_line_accrual_move_rel is embedded in sale_order_line, but deleting a account_move row cascades to its sale_order_line_accrual_move_rel: the app must pull them from every sale_order_line document, or keep sale_order_line_accrual_move_rel separate
- **cascade_into_embed** (sale_order_line_invoice_rel): sale_order_line_invoice_rel is embedded in sale_order_line, but deleting a account_move_line row cascades to its sale_order_line_invoice_rel: the app must pull them from every sale_order_line document, or keep sale_order_line_invoice_rel separate
- **cascade_into_embed** (sale_order_line_product_document_rel): sale_order_line_product_document_rel is embedded in sale_order_line, but deleting a product_document row cascades to its sale_order_line_product_document_rel: the app must pull them from every sale_order_line document, or keep sale_order_line_product_document_rel separate
- **no_access_evidence** (sale_order_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (sale_order_line): LOB column(s) name measured max 53 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

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

Open questions (4):
- **fanout_unmeasured** (spreadsheet_dashboard_share): spreadsheet_dashboard_share has no rows per spreadsheet_dashboard in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (spreadsheet_dashboard_allowed_users_rel): spreadsheet_dashboard_allowed_users_rel has no rows per spreadsheet_dashboard in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (spreadsheet_dashboard_allowed_users_rel): spreadsheet_dashboard_allowed_users_rel is embedded in spreadsheet_dashboard, but deleting a res_users row cascades to its spreadsheet_dashboard_allowed_users_rel: the app must pull them from every spreadsheet_dashboard document, or keep spreadsheet_dashboard_allowed_users_rel separate
- **no_access_evidence** (spreadsheet_dashboard): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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
- stock_location → maintenance_equipment: **reference**, other tables also point at it, so it keeps its own collection (derived)
- stock_location → purchase_order_line, res_company, stock_location, stock_lot, stock_move, stock_move_line, stock_package, stock_package_history, stock_picking, stock_picking_type, stock_putaway_rule, stock_quant, stock_rule, stock_warehouse, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, product_removal, stock_storage_category, account_account, stock_warehouse → stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_type → stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_location → stock_location_stock_picking_type_rel: **embed**, a link table, kept as an array on this side (assumed)

Open questions (4):
- **fanout_unmeasured** (stock_location_stock_picking_type_rel): stock_location_stock_picking_type_rel has no rows per stock_location in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (stock_location_stock_picking_type_rel): stock_location_stock_picking_type_rel is embedded in stock_location, but deleting a stock_picking_type row cascades to its stock_location_stock_picking_type_rel: the app must pull them from every stock_location document, or keep stock_location_stock_picking_type_rel separate
- **no_access_evidence** (stock_location): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockMove

From `stock_move` with `stock_move_created_purchase_line_rel`, `stock_move_move_rel`, `stock_move_stock_scrap_reason_tag_rel` embedded.

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
}
```

Why:
- stock_move → account_analytic_line_stock_move_rel, stock_move_move_rel, stock_reference_move_rel, stock_route_move, template_attribute_value_stock_move_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → account_move_line, stock_move, stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_move → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- account_move, res_company, res_users, stock_location, stock_warehouse_orderpoint, uom_uom, res_partner, stock_picking, stock_picking_type, product_product, purchase_order_line, stock_rule, sale_order_line, stock_warehouse → stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- purchase_order_line → stock_move_created_purchase_line_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_move → stock_move_created_purchase_line_rel, stock_move_move_rel, stock_move_stock_scrap_reason_tag_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (7):
- **fanout_unmeasured** (stock_move_created_purchase_line_rel): stock_move_created_purchase_line_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_move_move_rel): stock_move_move_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_move_stock_scrap_reason_tag_rel): stock_move_stock_scrap_reason_tag_rel has no rows per stock_move in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
- res_company, res_users, stock_location, stock_lot, stock_move, res_partner, stock_package_history, stock_package, stock_picking, product_product, uom_uom → stock_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
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
- res_company, res_users, stock_location, stock_package → stock_package_history: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_package_history → stock_package_history_stock_picking_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_picking → stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **fanout_unmeasured** (stock_package_history_stock_picking_rel): stock_package_history_stock_picking_rel has no rows per stock_package_history in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
- res_company, res_users, ir_sequence → stock_package_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_package_type → stock_package_type_stock_putaway_rule_rel, stock_package_type_stock_route_rel: **embed**, a link table, kept as an array on this side (assumed)
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_package_type_stock_route_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (6):
- **fanout_unmeasured** (stock_package_type_stock_putaway_rule_rel): stock_package_type_stock_putaway_rule_rel has no rows per stock_package_type in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_package_type_stock_route_rel): stock_package_type_stock_route_rel has no rows per stock_package_type in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (stock_package_type_stock_putaway_rule_rel): stock_package_type_stock_putaway_rule_rel is embedded in stock_package_type, but deleting a stock_putaway_rule row cascades to its stock_package_type_stock_putaway_rule_rel: the app must pull them from every stock_package_type document, or keep stock_package_type_stock_putaway_rule_rel separate
- **cascade_into_embed** (stock_package_type_stock_route_rel): stock_package_type_stock_route_rel is embedded in stock_package_type, but deleting a stock_route row cascades to its stock_package_type_stock_route_rel: the app must pull them from every stock_package_type document, or keep stock_package_type_stock_route_rel separate
- **no_access_evidence** (stock_package_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

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
- res_company, res_users, stock_warehouse → stock_route: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_category → stock_route_categ: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_route_categ, stock_route_move, stock_route_product, stock_route_warehouse: **embed**, a link table, kept as an array on this side (assumed)
- stock_move → stock_route_move: **reference**, a link table, embedded on the other side (assumed)
- product_template → stock_route_product: **reference**, a link table, embedded on the other side (assumed)
- stock_warehouse → stock_route_warehouse: **reference**, a link table, embedded on the other side (assumed)
- stock_route → stock_rule, stock_warehouse, stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (8):
- **fanout_unmeasured** (stock_route_categ): stock_route_categ has no rows per stock_route in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_route_move): stock_route_move has no rows per stock_route in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **fanout_unmeasured** (stock_route_product): stock_route_product has no rows per stock_route in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
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
- stock_rule, res_company, res_users, stock_route, stock_picking_type, stock_location, res_partner → stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_warehouse → stock_wh_resupply_table: **embed**, a link table, kept as an array on this side (assumed)

Open questions (2):
- **fanout_unmeasured** (stock_wh_resupply_table): stock_wh_resupply_table has no rows per stock_warehouse in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (stock_warehouse): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## surveyQuestion

From `survey_question` with `survey_question_answer`, `survey_question_survey_question_answer_rel`, `survey_question_survey_user_input_rel` embedded.

```js
{
  _id: int,  // id
  surveyId: int,  // survey_id
  sequence: int,  // sequence
  randomQuestionsCount: int,  // random_questions_count
  pageId: int,  // page_id
  scaleMin: int,  // scale_min
  scaleMax: int,  // scale_max
  timeLimit: int,  // time_limit
  validationLengthMin: int,  // validation_length_min
  validationLengthMax: int,  // validation_length_max
  createUid: int,  // create_uid
  writeUid: int,  // write_uid
  questionType: string,  // question_type
  matrixSubtype: string,  // matrix_subtype
  answerDate: date,  // answer_date
  validationMinDate: date,  // validation_min_date
  validationMaxDate: date,  // validation_max_date
  title: object,  // title
  description: object,  // description
  questionPlaceholder: object,  // question_placeholder
  scaleMinLabel: object,  // scale_min_label
  scaleMaxLabel: object,  // scale_max_label
  commentsMessage: object,  // comments_message
  validationErrorMsg: object,  // validation_error_msg
  constrErrorMsg: object,  // constr_error_msg
  isPage: bool,  // is_page
  isScoredQuestion: bool,  // is_scored_question
  saveAsEmail: bool,  // save_as_email
  saveAsNickname: bool,  // save_as_nickname
  isTimeLimited: bool,  // is_time_limited
  isTimeCustomized: bool,  // is_time_customized
  commentsAllowed: bool,  // comments_allowed
  commentCountAsAnswer: bool,  // comment_count_as_answer
  validationRequired: bool,  // validation_required
  validationEmail: bool,  // validation_email
  constrMandatory: bool,  // constr_mandatory
  answerDatetime: date,  // answer_datetime
  validationMinDatetime: date,  // validation_min_datetime
  validationMaxDatetime: date,  // validation_max_datetime
  createDate: date,  // create_date
  writeDate: date,  // write_date
  answerNumericalBox: double,  // answer_numerical_box
  answerScore: double,  // answer_score
  validationMinFloatValue: double,  // validation_min_float_value
  validationMaxFloatValue: double,  // validation_max_float_value
  answer: [{  // survey_question_answer, 1:N derived
    id: int,  // id
    matrixQuestionId: int,  // matrix_question_id
    sequence: int,  // sequence
    createUid: int,  // create_uid
    writeUid: int,  // write_uid
    valueImageFilename: string,  // value_image_filename
    value: object,  // value
    isCorrect: bool,  // is_correct
    createDate: date,  // create_date
    writeDate: date,  // write_date
    answerScore: double,  // answer_score
    generateLead: bool,  // generate_lead
  }],
  surveyQuestionAnswerRel: [{  // survey_question_survey_question_answer_rel, 1:N derived
    surveyQuestionAnswerId: int,  // survey_question_answer_id
  }],
  surveyUserInputRel: [{  // survey_question_survey_user_input_rel, 1:N assumed
    surveyUserInputId: int,  // survey_user_input_id
  }],
}
```

Why:
- res_users → survey_question: **reference**, another parent owns it; this one is referenced (derived)
- survey_question → survey_question, survey_user_input_line: **reference**, another parent owns it; this one is referenced (derived)
- survey_survey → survey_question: **reference**, the app reads it on its own (derived)
- res_users → survey_question_answer: **reference**, it is embedded under another parent; this one is referenced (derived)
- survey_question → survey_question_answer: **reference**, it is embedded under another parent; this one is referenced (derived)
- survey_question → survey_question_answer: **embed**, the app reads it with its parent (derived)
- survey_question_answer → survey_question_survey_question_answer_rel: **reference**, a link table, embedded on the other side (assumed)
- survey_question → survey_question_survey_question_answer_rel: **embed**, a link table, kept as an array on this side (derived)
- survey_question → survey_question_survey_user_input_rel: **embed**, a link table, kept as an array on this side (assumed)
- survey_user_input → survey_question_survey_user_input_rel: **reference**, a link table, embedded on the other side (assumed)
- survey_question → survey_survey, survey_user_input: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (9):
- **extended_reference_candidate** (survey_question_answer): app reads survey_question with every survey_question_answer: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **extended_reference_candidate** (survey_question_survey_question_answer_rel): app reads survey_question_answer with every survey_question_survey_question_answer_rel: copy up to 5 read fields into each element (needs embed-level extended reference; record with resolve until supported) or keep the reference
- **cascade_into_embed** (survey_question_survey_question_answer_rel): survey_question_survey_question_answer_rel is embedded in survey_question, but deleting a survey_question_answer row cascades to its survey_question_survey_question_answer_rel: the app must pull them from every survey_question document, or keep survey_question_survey_question_answer_rel separate
- **cascade_into_embed** (survey_question_survey_user_input_rel): survey_question_survey_user_input_rel is embedded in survey_question, but deleting a survey_user_input row cascades to its survey_question_survey_user_input_rel: the app must pull them from every survey_question document, or keep survey_question_survey_user_input_rel separate
- **single_valued_index_key** (survey_question): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **single_valued_index_key** (survey_question_answer): profile shows one non-null value; confirm the domain on the real estate before relying on this access-index plan
- **source_index_not_exercised** (survey_question_answer): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (survey_question_survey_question_answer_rel): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (survey_question_survey_user_input_rel): source index not exercised by any confirmed access pattern; keep or drop

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

Open questions (3):
- **fanout_unmeasured** (utm_tag_rel): utm_tag_rel has no rows per utm_tag in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **cascade_into_embed** (utm_tag_rel): utm_tag_rel is embedded in utm_tag, but deleting a utm_campaign row cascades to its utm_tag_rel: the app must pull them from every utm_tag document, or keep utm_tag_rel separate
- **no_access_evidence** (utm_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

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

Open questions (2):
- **fanout_unmeasured** (web_tour_tour_step): web_tour_tour_step has no rows per web_tour_tour in the profiled source (child_rows=0); fan-out is unmeasured — profile a representative source or confirm a bound before embedding
- **no_access_evidence** (web_tour_tour): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountAnalyticAccount

From `account_analytic_account`.

Why:
- res_company, res_users, res_partner, account_analytic_plan → account_analytic_account: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_analytic_account → account_analytic_line, project_project, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_analytic_account): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountAnalyticApplicability

From `account_analytic_applicability`.

Why:
- account_analytic_plan, res_company, res_users, product_category → account_analytic_applicability: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_analytic_applicability): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountAnalyticDistributionModel

From `account_analytic_distribution_model`.

Why:
- res_company, res_users, res_partner_category, res_partner, product_category, product_product → account_analytic_distribution_model: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_analytic_distribution_model): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountAnalyticPlan

From `account_analytic_plan`.

Why:
- account_analytic_plan → account_analytic_account, account_analytic_applicability, account_analytic_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_analytic_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (account_analytic_plan): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (account_analytic_plan): LOB column(s) description measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## accountBankStatementLine

From `account_bank_statement_line`.

Why:
- res_company, res_users, res_currency, account_journal, account_move, res_partner, account_bank_statement → account_bank_statement_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_move, account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_bank_statement_line → account_payment_account_bank_statement_line_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (1):
- **no_access_evidence** (account_bank_statement_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountFullReconcile

From `account_full_reconcile`.

Why:
- res_users → account_full_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_full_reconcile → account_move_line, account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_full_reconcile): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountIncoterms

From `account_incoterms`.

Why:
- res_users → account_incoterms: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_incoterms → account_move, purchase_order, res_company, res_partner, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_incoterms): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountJournalGroup

From `account_journal_group`.

Why:
- account_journal_group → account_journal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_journal_group: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_journal_group): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountLockException

From `account_lock_exception`.

Why:
- res_company, res_users → account_lock_exception: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_lock_exception): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountPartialReconcile

From `account_partial_reconcile`.

Why:
- account_partial_reconcile → account_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_currency, account_move_line, account_move, account_full_reconcile → account_partial_reconcile: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_partial_reconcile): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountPaymentMethod

From `account_payment_method`.

Why:
- account_payment_method → account_payment, account_payment_method_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → account_payment_method: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_payment_method): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountReportLine

From `account_report_line`.

Why:
- account_report_line → account_report_expression, account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_report_line → account_report_external_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users, account_report → account_report_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (account_report_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## accountTaxGroup

From `account_tax_group`.

Why:
- account_tax_group → account_move_line, account_tax: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_country, res_users → account_tax_group: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_tax_group): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## accountTaxRepartitionLine

From `account_tax_repartition_line`.

Why:
- account_tax_repartition_line → account_account_tag_account_tax_repartition_line_rel: **reference**, a link table, embedded on the other side (assumed)
- account_tax_repartition_line → account_move_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- account_account, res_company, res_users, account_tax → account_tax_repartition_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (account_tax_repartition_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## authPasskeyKey

From `auth_passkey_key`.

Why:
- res_users → auth_passkey_key: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (auth_passkey_key): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## barcodeNomenclature

From `barcode_nomenclature`.

Why:
- res_users → barcode_nomenclature: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- barcode_nomenclature → barcode_rule, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (barcode_nomenclature): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## barcodeRule

From `barcode_rule`.

Why:
- uom_uom, barcode_nomenclature, res_users → barcode_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (barcode_rule): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## baseImportMapping

From `base_import_mapping`.

Why:
- res_users → base_import_mapping: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (base_import_mapping): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## busBus

From `bus_bus`.

Why:
- res_users → bus_bus: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (bus_bus): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## calendarAttendee

From `calendar_attendee`.

Why:
- res_users, calendar_event, res_partner → calendar_attendee: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (calendar_attendee): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## calendarCalendar

From `calendar_calendar`.

Why:
- res_users → calendar_calendar: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- calendar_calendar → calendar_event, calendar_user, res_users: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (calendar_calendar): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## calendarEventType

From `calendar_event_type`.

Why:
- res_users → calendar_event_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- calendar_event_type → meeting_category_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (1):
- **no_access_evidence** (calendar_event_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## calendarRecurrence

From `calendar_recurrence`.

Why:
- calendar_recurrence → calendar_event: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- calendar_event, res_users, ir_cron_trigger → calendar_recurrence: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (calendar_recurrence): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## calendarUser

From `calendar_user`.

Why:
- calendar_calendar, res_users → calendar_user: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (calendar_user): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## clearingLabel

From `clearing_label`.

Why:
- res_country, res_users → clearing_label: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- clearing_label → res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (clearing_label): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmIapLeadHelpers

From `crm_iap_lead_helpers`.

Why:
- res_users → crm_iap_lead_helpers: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (crm_iap_lead_helpers): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmIapLeadIndustryDivision

From `crm_iap_lead_industry_division`.

Why:
- crm_iap_lead_industry_division → crm_iap_lead_industry: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → crm_iap_lead_industry_division: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (crm_iap_lead_industry_division): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmIapLeadRole

From `crm_iap_lead_role`.

Why:
- res_users → crm_iap_lead_role: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (crm_iap_lead_role): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmIapLeadSeniority

From `crm_iap_lead_seniority`.

Why:
- res_users → crm_iap_lead_seniority: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (crm_iap_lead_seniority): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmLostReason

From `crm_lost_reason`.

Why:
- crm_lost_reason → crm_lead: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → crm_lost_reason: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (crm_lost_reason): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmRecurringPlan

From `crm_recurring_plan`.

Why:
- crm_recurring_plan → crm_lead: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → crm_recurring_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (crm_recurring_plan): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## crmTeamMember

From `crm_team_member`.

Why:
- res_users, crm_team → crm_team_member: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (crm_team_member): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## customerProductReference

From `customer_product_reference`.

Why:
- res_users, res_partner, product_product → customer_product_reference: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (customer_product_reference): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## decimalPrecision

From `decimal_precision`.

Why:
- res_users → decimal_precision: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (decimal_precision): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## discussCategory

From `discuss_category`.

Why:
- res_users → discuss_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_category → discuss_channel: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (discuss_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## discussChannelMember

From `discuss_channel_member`.

Why:
- discuss_channel, res_users, mail_guest, res_partner, discuss_channel_rtc_session, mail_message → discuss_channel_member: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_channel_member → discuss_channel_rtc_session: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (discuss_channel_member): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## discussChannelRtcSession

From `discuss_channel_rtc_session`.

Why:
- discuss_channel_rtc_session → discuss_channel_member: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- discuss_channel, discuss_channel_member, res_users, res_partner → discuss_channel_rtc_session: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (discuss_channel_rtc_session): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## discussGifFavorite

From `discuss_gif_favorite`.

Why:
- res_users → discuss_gif_favorite: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (discuss_gif_favorite): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## eventMail

From `event_mail`.

Why:
- res_users, event_event, event_registration → event_mail: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_mail → event_mail_registration, event_mail_slot: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (event_mail): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventMailRegistration

From `event_mail_registration`.

Why:
- res_users, event_registration, event_mail → event_mail_registration: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (event_mail_registration): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventMailSlot

From `event_mail_slot`.

Why:
- res_users, event_slot, event_registration, event_mail → event_mail_slot: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (event_mail_slot): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventQuestionAnswer

From `event_question_answer`.

Why:
- res_users, event_question → event_question_answer: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- event_question_answer → event_registration_answer: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (1):
- **no_access_evidence** (event_question_answer): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventSlot

From `event_slot`.

Why:
- event_slot → event_mail_slot, event_registration, sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, event_event → event_slot: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (event_slot): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventStage

From `event_stage`.

Why:
- event_stage → event_event: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → event_stage: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (event_stage): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## eventTagCategory

From `event_tag_category`.

Why:
- event_tag_category → event_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → event_tag_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (event_tag_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## fetchmailServer

From `fetchmail_server`.

Why:
- res_users, ir_model → fetchmail_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- fetchmail_server → mail_mail: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (fetchmail_server): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (fetchmail_server): LOB column(s) error_message, configuration: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## fleetVehicleAssignationLog

From `fleet_vehicle_assignation_log`.

Why:
- res_users, hr_employee, res_partner → fleet_vehicle_assignation_log: **reference**, another parent owns it; this one is referenced (derived)
- fleet_vehicle → fleet_vehicle_assignation_log: **reference**, the app reads it on its own (derived)

## fleetVehicleLogContract

From `fleet_vehicle_log_contract`.

Why:
- fleet_vehicle_log_contract → fleet_service_type_fleet_vehicle_log_contract_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, fleet_service_type, res_users, res_partner, fleet_vehicle → fleet_vehicle_log_contract: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (2):
- **lob** (fleet_vehicle_log_contract): LOB column(s) notes measured max 32 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (fleet_vehicle_log_contract): source index not exercised by any confirmed access pattern; keep or drop

## fleetVehicleModelBrand

From `fleet_vehicle_model_brand`.

Why:
- fleet_vehicle_model_brand → fleet_vehicle, fleet_vehicle_model: **reference**, other tables also point at it, so it keeps its own collection (derived)
- fleet_vehicle_model_brand → fleet_vehicle_log_services: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → fleet_vehicle_model_brand: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (fleet_vehicle_model_brand): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## fleetVehicleModelCategory

From `fleet_vehicle_model_category`.

Why:
- fleet_vehicle_model_category → fleet_vehicle, fleet_vehicle_model: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_users → fleet_vehicle_model_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (fleet_vehicle_model_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## fleetVehicleOdometer

From `fleet_vehicle_odometer`.

Why:
- fleet_vehicle_odometer → fleet_vehicle_log_services: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users, res_partner → fleet_vehicle_odometer: **reference**, other tables also point at it, so it keeps its own collection (derived)
- fleet_vehicle → fleet_vehicle_odometer: **reference**, other tables also point at it, so it keeps its own collection (assumed)

## fleetVehicleState

From `fleet_vehicle_state`.

Why:
- fleet_vehicle_state → fleet_vehicle: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_users → fleet_vehicle_state: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (fleet_vehicle_state): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## fleetVehicleTag

From `fleet_vehicle_tag`.

Why:
- res_users → fleet_vehicle_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- fleet_vehicle_tag → fleet_vehicle_vehicle_tag_rel: **reference**, a link table, embedded on the other side (assumed)

## gamificationBadgeUser

From `gamification_badge_user`.

Why:
- gamification_badge, gamification_challenge, res_users, hr_employee → gamification_badge_user: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (gamification_badge_user): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (gamification_badge_user): LOB column(s) comment: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## gamificationChallengeLine

From `gamification_challenge_line`.

Why:
- gamification_challenge, res_users, gamification_goal_definition → gamification_challenge_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- gamification_challenge_line → gamification_goal: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (gamification_challenge_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## gamificationGoal

From `gamification_goal`.

Why:
- gamification_challenge, res_users, gamification_goal_definition, gamification_challenge_line → gamification_goal: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (gamification_goal): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## gamificationGoalDefinition

From `gamification_goal_definition`.

Why:
- gamification_goal_definition → badge_unlocked_definition_rel: **reference**, a link table, embedded on the other side (assumed)
- gamification_goal_definition → gamification_challenge_line, gamification_goal: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_window, ir_model_fields, res_users, ir_model → gamification_goal_definition: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (gamification_goal_definition): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (gamification_goal_definition): LOB column(s) description, compute_code measured max 88 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## gamificationKarmaRank

From `gamification_karma_rank`.

Why:
- res_users → gamification_karma_rank: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- gamification_karma_rank → res_users: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (gamification_karma_rank): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrDepartureReason

From `hr_departure_reason`.

Why:
- res_country, res_users → hr_departure_reason: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_departure_reason → hr_employee_departure: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_departure_reason): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrEmployeeCategory

From `hr_employee_category`.

Why:
- hr_employee_category → employee_category_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → hr_employee_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_employee_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrEmployeeDeparture

From `hr_employee_departure`.

Why:
- res_users, hr_departure_reason, hr_employee → hr_employee_departure: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_employee_departure → hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (hr_employee_departure): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (hr_employee_departure): LOB column(s) departure_description: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## hrEmployeeLocation

From `hr_employee_location`.

Why:
- res_users, hr_work_location → hr_employee_location: **reference**, another parent owns it; this one is referenced (derived)
- hr_employee → hr_employee_location: **reference**, no evidence either way (assumed)

Open questions (2):
- **no_access_evidence** (hr_employee_location): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## hrEmployeeSkill

From `hr_employee_skill`.

Why:
- res_users, hr_employee, hr_skill, hr_skill_level, hr_skill_type → hr_employee_skill: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_employee_skill): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrEmployeeType

From `hr_employee_type`.

Why:
- res_company, res_country, res_users → hr_employee_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_employee_type → hr_job, hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_employee_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrExpense

From `hr_expense`.

Why:
- hr_expense → account_move_line, sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_expense → expense_tax: **reference**, a link table, embedded on the other side (assumed)
- account_account, account_move, res_company, res_users, res_currency, hr_department, hr_employee, ir_attachment, account_payment_method_line, product_product, uom_uom, sale_order, sale_order_line, res_partner → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)
- hr_expense → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (8):
- **lob** (hr_expense): LOB column(s) description measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **source_index_not_exercised** (hr_expense): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (hr_expense): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (hr_expense): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (hr_expense): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (hr_expense): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (hr_expense): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (hr_expense): source index not exercised by any confirmed access pattern; keep or drop

## hrJobSkill

From `hr_job_skill`.

Why:
- res_users, hr_job, hr_skill, hr_skill_level, hr_skill_type → hr_job_skill: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_job_skill): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrLeave

From `hr_leave`.

Why:
- hr_leave → account_analytic_line, hr_leave, resource_calendar_leaves: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, hr_department, hr_employee, calendar_event, ir_attachment, resource_calendar, hr_time_rule, hr_work_entry_type → hr_leave: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (hr_leave): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (hr_leave): LOB column(s) notes measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## hrLeaveMandatoryDay

From `hr_leave_mandatory_day`.

Why:
- hr_leave_mandatory_day → hr_department_hr_leave_mandatory_day_rel, hr_job_hr_leave_mandatory_day_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, resource_calendar → hr_leave_mandatory_day: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_leave_mandatory_day): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrPayrollStructureType

From `hr_payroll_structure_type`.

Why:
- res_country, res_users, resource_calendar → hr_payroll_structure_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_payroll_structure_type → hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_payroll_structure_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrResumeLine

From `hr_resume_line`.

Why:
- res_users, hr_department, hr_employee, event_event, hr_resume_line_type, survey_survey → hr_resume_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_resume_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrResumeLineType

From `hr_resume_line_type`.

Why:
- hr_resume_line_type → hr_resume_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → hr_resume_line_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_resume_line_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrSkill

From `hr_skill`.

Why:
- hr_skill → hr_employee_hr_skill_rel, hr_job_hr_skill_rel: **reference**, a link table, embedded on the other side (assumed)
- hr_skill → hr_employee_skill, hr_job_skill: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, hr_skill_type → hr_skill: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_skill): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrSkillLevel

From `hr_skill_level`.

Why:
- hr_skill_level → hr_employee_skill, hr_job_skill: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, hr_skill_type → hr_skill_level: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_skill_level): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrSkillType

From `hr_skill_type`.

Why:
- hr_skill_type → hr_employee_skill, hr_job_skill, hr_skill, hr_skill_level: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → hr_skill_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_skill_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrVersion

From `hr_version`.

Why:
- hr_version → hr_employee, hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner, hr_leave_allocation, res_company, res_country, res_users, hr_department, hr_employee_departure, hr_employee, hr_employee_type, hr_job, res_country_state, resource_calendar, hr_payroll_structure_type, hr_work_location → hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_version): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrWorkEntryType

From `hr_work_entry_type`.

Why:
- hr_work_entry_type → hr_leave, hr_leave_accrual_plan, hr_leave_allocation, hr_time_rule, resource_calendar_leaves: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_work_entry_type → hr_time_rule_condition_work_entry_type_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_message_subtype, res_country, res_users → hr_work_entry_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_work_entry_type → resource_calendar_attendance: **reference**, it is embedded under another parent; this one is referenced (derived)

Open questions (1):
- **no_access_evidence** (hr_work_entry_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## hrWorkLocation

From `hr_work_location`.

Why:
- hr_work_location → hr_employee, hr_version: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- hr_work_location → hr_employee_location: **reference**, another parent owns it; this one is referenced (derived)
- res_partner, res_company, res_users → hr_work_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (hr_work_location): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## htmlEditorConverterTest

From `html_editor_converter_test`.

Why:
- res_users, html_editor_converter_test_sub → html_editor_converter_test: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (html_editor_converter_test): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (html_editor_converter_test): LOB column(s) html, text: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## htmlEditorConverterTestSub

From `html_editor_converter_test_sub`.

Why:
- html_editor_converter_test_sub → html_editor_converter_test: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → html_editor_converter_test_sub: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (html_editor_converter_test_sub): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irAccess

From `ir_access`.

Why:
- res_users, res_groups, ir_model → ir_access: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (ir_access): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_access): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## irActReportXml

From `ir_act_report_xml`.

Why:
- ir_act_report_xml → account_journal, res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_model, res_users, report_paperformat → ir_act_report_xml: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_act_report_xml → mail_template_ir_actions_report_rel, res_groups_report_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (3):
- **no_access_evidence** (ir_act_report_xml): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_act_report_xml): LOB column(s) explanation measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## irActionsTodo

From `ir_actions_todo`.

Why:
- res_users → ir_actions_todo: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_actions_todo): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irAsset

From `ir_asset`.

Why:
- res_users → ir_asset: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_asset): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irConfigParameter

From `ir_config_parameter`.

Why:
- res_users → ir_config_parameter: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (ir_config_parameter): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_config_parameter): LOB column(s) value measured max 70 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## irCronTrigger

From `ir_cron_trigger`.

Why:
- ir_cron_trigger → calendar_recurrence: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_cron → ir_cron_trigger: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_cron_trigger): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irDefault

From `ir_default`.

Why:
- res_company, res_users, ir_model_fields → ir_default: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_default): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irLogging

From `ir_logging`.

Open questions (2):
- **no_access_evidence** (ir_logging): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_logging): LOB column(s) message: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## irMailServer

From `ir_mail_server`.

Why:
- res_users → ir_mail_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_mail_server → mail_message, mail_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (ir_mail_server): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## irModelConstraint

From `ir_model_constraint`.

Why:
- res_users, ir_model, ir_module_module → ir_model_constraint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_model_constraint): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irModelData

From `ir_model_data`.

Why:
- res_users → ir_model_data: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_model_data): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irModelFieldsSelection

From `ir_model_fields_selection`.

Why:
- ir_model_fields_selection → ir_act_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_model_fields → ir_model_fields_selection: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_model_fields_selection): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irModelRelation

From `ir_model_relation`.

Why:
- res_users, ir_model, ir_module_module → ir_model_relation: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_model_relation): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irModuleCategory

From `ir_module_category`.

Why:
- res_users → ir_module_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_module_category → ir_module_category, ir_module_module, res_groups_privilege: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (ir_module_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irSequence

From `ir_sequence`.

Why:
- ir_sequence → ir_act_server, product_template, res_company, stock_package_type, stock_picking_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users → ir_sequence: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_sequence → ir_sequence_date_range: **reference**, no evidence either way (assumed)

Open questions (1):
- **no_access_evidence** (ir_sequence): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irSequenceDateRange

From `ir_sequence_date_range`.

Why:
- res_users → ir_sequence_date_range: **reference**, another parent owns it; this one is referenced (derived)
- ir_sequence → ir_sequence_date_range: **reference**, no evidence either way (assumed)

Open questions (1):
- **no_access_evidence** (ir_sequence_date_range): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## irUiViewCustom

From `ir_ui_view_custom`.

Why:
- res_users, ir_ui_view → ir_ui_view_custom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (ir_ui_view_custom): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (ir_ui_view_custom): LOB column(s) arch: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## l10nUsResCounty

From `l10n_us_res_county`.

Why:
- l10n_us_res_county → account_tax, res_city: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, res_country_state → l10n_us_res_county: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (l10n_us_res_county): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## lunchCashmove

From `lunch_cashmove`.

Why:
- res_users, res_currency → lunch_cashmove: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (lunch_cashmove): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (lunch_cashmove): LOB column(s) description measured max 32 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## lunchProductCategory

From `lunch_product_category`.

Why:
- lunch_product_category → lunch_order, lunch_product: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_company, res_users → lunch_product_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (lunch_product_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## lunchSupplier

From `lunch_supplier`.

Why:
- lunch_supplier → lunch_location_lunch_supplier_rel: **reference**, a link table, embedded on the other side (assumed)
- lunch_supplier → lunch_order, lunch_product: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_company, res_users, ir_cron, res_partner → lunch_supplier: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- lunch_supplier → lunch_topping: **reference**, the app reads it on its own (derived)

Open questions (1):
- **repeating_group** (lunch_supplier): collapse each numbered series into one array field; needs app evidence, mapped 1:1 until then

## lunchTopping

From `lunch_topping`.

Why:
- lunch_topping → lunch_order_topping: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users → lunch_topping: **reference**, another parent owns it; this one is referenced (derived)
- lunch_supplier → lunch_topping: **reference**, the app reads it on its own (derived)

## mailActivity

From `mail_activity`.

Why:
- mail_activity → activity_attachment_rel: **reference**, a link table, embedded on the other side (assumed)
- mail_activity_plan, mail_activity_plan_template, mail_activity_type, calendar_event, res_users, ir_model, res_role → mail_activity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (mail_activity): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_activity): LOB column(s) note, feedback measured max 179 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## mailActivityPlan

From `mail_activity_plan`.

Why:
- mail_activity_plan → ir_act_server, mail_activity, mail_activity_plan_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, hr_department, ir_model → mail_activity_plan: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_activity_plan): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailActivityPlanTemplate

From `mail_activity_plan_template`.

Why:
- mail_activity_plan_template → mail_activity: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_activity_type, res_users, mail_activity_plan, res_role → mail_activity_plan_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (mail_activity_plan_template): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_activity_plan_template): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## mailAlias

From `mail_alias`.

Why:
- mail_alias → account_journal, crm_team, project_project: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_alias_domain, ir_model, res_users → mail_alias: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_alias → maintenance_team: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (2):
- **no_access_evidence** (mail_alias): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_alias): LOB column(s) alias_defaults measured max 63 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## mailAliasDomain

From `mail_alias_domain`.

Why:
- mail_alias_domain → mail_alias, mail_message, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → mail_alias_domain: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_alias_domain): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailBlacklist

From `mail_blacklist`.

Why:
- res_users → mail_blacklist: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_blacklist): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailGatewayAllowed

From `mail_gateway_allowed`.

Why:
- res_users → mail_gateway_allowed: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_gateway_allowed): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailGuest

From `mail_guest`.

Why:
- mail_guest → discuss_channel_member, mail_message, mail_message_reaction, mail_poll_vote, mail_presence: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country, res_users → mail_guest: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_guest): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailIceServer

From `mail_ice_server`.

Why:
- res_users → mail_ice_server: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_ice_server): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailLinkPreview

From `mail_link_preview`.

Why:
- res_users → mail_link_preview: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_link_preview → mail_message_link_preview: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (mail_link_preview): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (mail_link_preview): LOB column(s) og_description: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## mailMessageLinkPreview

From `mail_message_link_preview`.

Why:
- res_users, mail_link_preview, mail_message → mail_message_link_preview: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_message_link_preview): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailMessageReaction

From `mail_message_reaction`.

Why:
- mail_guest, mail_message, res_partner → mail_message_reaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_message_reaction): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailMessageSubtype

From `mail_message_subtype`.

Why:
- mail_message_subtype → hr_work_entry_type, mail_message, mail_message_subtype: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_message_subtype → ir_act_server_mail_message_subtype_rel, mail_followers_mail_message_subtype_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → mail_message_subtype: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_message_subtype): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailPoll

From `mail_poll`.

Why:
- res_users, mail_message → mail_poll: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_poll → mail_poll_option: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (mail_poll): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## mailPollOption

From `mail_poll_option`.

Why:
- res_users, mail_poll → mail_poll_option: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- mail_poll_option → mail_poll_vote: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_poll_option): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## mailPollVote

From `mail_poll_vote`.

Why:
- res_users, mail_guest, mail_poll_option → mail_poll_vote: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (mail_poll_vote): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## mailPresence

From `mail_presence`.

Why:
- mail_guest, res_users → mail_presence: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (mail_presence): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## maintenanceEquipment

From `maintenance_equipment`.

Why:
- maintenance_equipment_category → maintenance_equipment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, hr_department, hr_employee, stock_location, maintenance_team, res_partner, fleet_vehicle → maintenance_equipment: **reference**, other tables also point at it, so it keeps its own collection (derived)
- maintenance_equipment → maintenance_request: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (6):
- **lob** (maintenance_equipment): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (maintenance_equipment): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (maintenance_equipment): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (maintenance_equipment): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (maintenance_equipment): source index not exercised by any confirmed access pattern; keep or drop

## maintenanceEquipmentCategory

From `maintenance_equipment_category`.

Why:
- maintenance_equipment_category → maintenance_equipment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users → maintenance_equipment_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- maintenance_equipment_category → maintenance_request: **reference**, other tables also point at it, so it keeps its own collection (derived)

Open questions (1):
- **no_access_evidence** (maintenance_equipment_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## onboardingOnboardingStep

From `onboarding_onboarding_step`.

Why:
- onboarding_onboarding_step → onboarding_onboarding_onboarding_onboarding_step_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → onboarding_onboarding_step: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- onboarding_onboarding_step → onboarding_progress_step: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (onboarding_onboarding_step): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## onboardingProgressStep

From `onboarding_progress_step`.

Why:
- onboarding_progress_step → onboarding_progress_onboarding_progress_step_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, onboarding_onboarding_step → onboarding_progress_step: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (onboarding_progress_step): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## ormSignalingAssets

From `orm_signaling_assets`.

Open questions (1):
- **no_access_evidence** (orm_signaling_assets): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## ormSignalingDefault

From `orm_signaling_default`.

Open questions (1):
- **no_access_evidence** (orm_signaling_default): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## ormSignalingGroups

From `orm_signaling_groups`.

Open questions (1):
- **no_access_evidence** (orm_signaling_groups): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## ormSignalingRegistry

From `orm_signaling_registry`.

Open questions (1):
- **no_access_evidence** (orm_signaling_registry): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## ormSignalingRouting

From `orm_signaling_routing`.

Open questions (1):
- **no_access_evidence** (orm_signaling_routing): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## ormSignalingStable

From `orm_signaling_stable`.

Open questions (1):
- **no_access_evidence** (orm_signaling_stable): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## ormSignalingTemplates

From `orm_signaling_templates`.

Open questions (1):
- **no_access_evidence** (orm_signaling_templates): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## paymentData

From `payment_data`.

Why:
- res_users, payment_transaction → payment_data: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (payment_data): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (payment_data): LOB column(s) error_traceback: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## paymentToken

From `payment_token`.

Why:
- payment_token → account_payment, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_partner, payment_method, payment_provider → payment_token: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (payment_token): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## paymentTransaction

From `payment_transaction`.

Why:
- payment_transaction → account_invoice_transaction_rel, sale_order_transaction_rel: **reference**, a link table, embedded on the other side (assumed)
- payment_transaction → account_payment, payment_data, payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_currency, res_country, res_partner, res_country_state, account_payment, payment_method, payment_provider, payment_token → payment_transaction: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (payment_transaction): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (payment_transaction): LOB column(s) state_message: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## phoneBlacklist

From `phone_blacklist`.

Why:
- res_users → phone_blacklist: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (phone_blacklist): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## portalEntry

From `portal_entry`.

Why:
- res_users → portal_entry: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (portal_entry): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## privacyLog

From `privacy_log`.

Why:
- res_users → privacy_log: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (privacy_log): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (privacy_log): LOB column(s) execution_details, records_description, additional_note: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit

## productAttributeCustomValue

From `product_attribute_custom_value`.

Why:
- product_template_attribute_value, res_users, sale_order_line, sale_order_template_line → product_attribute_custom_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (product_attribute_custom_value): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## productBaseUnit

From `product_base_unit`.

Why:
- res_users → product_base_unit: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_base_unit → product_product, product_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_base_unit): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productComboItem

From `product_combo_item`.

Why:
- product_combo, res_company, res_users, product_product → product_combo_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_combo_item → sale_order_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_combo_item): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productPricelist

From `product_pricelist`.

Why:
- product_pricelist → payment_provider_product_pricelist_rel, res_country_group_pricelist_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, res_currency → product_pricelist: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_pricelist → product_pricelist_item, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_pricelist): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productPricelistItem

From `product_pricelist_item`.

Why:
- product_pricelist, product_category, res_company, res_users, res_currency, product_product, product_template, uom_uom → product_pricelist_item: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_pricelist_item): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productRemoval

From `product_removal`.

Why:
- product_removal → product_category, stock_location: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → product_removal: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_removal): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productSupplierinfo

From `product_supplierinfo`.

Why:
- res_company, res_users, res_currency, res_partner, product_product, product_template, uom_uom → product_supplierinfo: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_supplierinfo → stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_supplierinfo): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productTemplateAttributeLine

From `product_template_attribute_line`.

Why:
- product_template_attribute_line → product_attribute_value_product_template_attribute_line_rel: **reference**, a link table, embedded on the other side (assumed)
- product_attribute, res_users, product_template → product_template_attribute_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- product_template_attribute_line → product_template_attribute_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_template_attribute_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## productUom

From `product_uom`.

Why:
- res_company, res_users, product_product, uom_uom → product_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (product_uom): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectMilestone

From `project_milestone`.

Why:
- res_users, project_project, sale_order_line → project_milestone: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- project_milestone → project_task: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (project_milestone): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectProjectStage

From `project_project_stage`.

Why:
- project_project_stage → project_project: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, mail_template, sms_template → project_project_stage: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (project_project_stage): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectTaskRecurrence

From `project_task_recurrence`.

Why:
- project_task_recurrence → project_task: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → project_task_recurrence: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (project_task_recurrence): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectTaskUserRel

From `project_task_user_rel`.

Why:
- res_users, project_task_type, project_task → project_task_user_rel: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (project_task_user_rel): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## projectUpdate

From `project_update`.

Why:
- project_update → project_project: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, project_project, uom_uom → project_update: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (project_update): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (project_update): LOB column(s) description measured max 1209 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## ratingRating

From `rating_rating`.

Why:
- res_users, mail_message, ir_model, res_partner → rating_rating: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (rating_rating): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (rating_rating): LOB column(s) feedback, publisher_comment measured max 142 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## reportLayout

From `report_layout`.

Why:
- res_users, ir_ui_view → report_layout: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (report_layout): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## reportPaperformat

From `report_paperformat`.

Why:
- report_paperformat → ir_act_report_xml, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → report_paperformat: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (report_paperformat): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resCity

From `res_city`.

Why:
- res_city → account_tax, res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country, res_users, l10n_us_res_county, res_country_state → res_city: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_city): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resCountryState

From `res_country_state`.

Why:
- res_country_state → account_fiscal_position_res_country_state_rel, crm_iap_lead_mining_request_res_country_state_rel, res_country_group_res_country_state_rel: **reference**, a link table, embedded on the other side (assumed)
- res_country_state → account_tax, crm_lead, hr_version, l10n_us_res_county, payment_transaction, res_city, res_partner, res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_country, res_users → res_country_state: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_country_state): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resCurrency

From `res_currency`.

Why:
- res_currency → account_account, account_analytic_line, account_bank_statement, account_bank_statement_line, account_journal, account_move, account_move_line, account_partial_reconcile, account_payment, lunch_cashmove, payment_transaction, product_pricelist, product_pricelist_item, product_supplierinfo, purchase_order, res_company, res_country, sale_order, sale_order_line, sale_order_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_currency → account_cash_rounding_res_currency_rel, payment_currency_rel, payment_method_res_currency_rel: **reference**, a link table, embedded on the other side (assumed)
- res_currency → hr_expense, lunch_order: **reference**, other tables also point at it, so it keeps its own collection (derived)
- res_currency → project_sale_line_employee_map: **reference**, it is embedded under another parent; this one is referenced (derived)
- res_users → res_currency: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_currency → res_currency_rate: **reference**, no evidence either way (assumed)

Open questions (1):
- **no_access_evidence** (res_currency): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resCurrencyRate

From `res_currency_rate`.

Why:
- res_company, res_users → res_currency_rate: **reference**, another parent owns it; this one is referenced (derived)
- res_currency → res_currency_rate: **reference**, no evidence either way (assumed)

Open questions (2):
- **no_access_evidence** (res_currency_rate): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## resDeviceLog

From `res_device_log`.

Why:
- res_users → res_device_log: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_device_log): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resGroupsPrivilege

From `res_groups_privilege`.

Why:
- res_groups_privilege → res_groups: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- ir_module_category, res_users → res_groups_privilege: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_groups_privilege): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resPartnerBank

From `res_partner_bank`.

Why:
- res_partner_bank → account_journal, account_move, account_payment: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner_bank → employee_bank_account_rel: **reference**, a link table, embedded on the other side (assumed)
- clearing_label, res_company, res_country, res_users, res_partner, res_country_state → res_partner_bank: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (res_partner_bank): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (res_partner_bank): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## resPartnerCategory

From `res_partner_category`.

Why:
- res_partner_category → account_analytic_distribution_model, res_partner_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_partner_category → account_cash_rounding_res_partner_category_rel, res_partner_res_partner_category_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → res_partner_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_partner_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resPartnerIndustry

From `res_partner_industry`.

Why:
- res_partner_industry → res_partner: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → res_partner_industry: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_partner_industry): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resUsersDeletion

From `res_users_deletion`.

Why:
- res_users → res_users_deletion: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_users_deletion): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resUsersLog

From `res_users_log`.

Why:
- res_users → res_users_log: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_users_log): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resUsersSettings

From `res_users_settings`.

Why:
- res_users → res_users_settings: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users_settings → res_users_settings_embedded_action, res_users_settings_volumes: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_users_settings): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resUsersSettingsEmbeddedAction

From `res_users_settings_embedded_action`.

Why:
- ir_act_window, res_users, res_users_settings → res_users_settings_embedded_action: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (res_users_settings_embedded_action): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## resUsersSettingsVolumes

From `res_users_settings_volumes`.

Why:
- res_users, res_partner, res_users_settings → res_users_settings_volumes: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (res_users_settings_volumes): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resourceCalendarLeaves

From `resource_calendar_leaves`.

Why:
- resource_calendar_leaves → account_analytic_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- resource_calendar, res_company, res_users, hr_leave, resource_resource, hr_work_entry_type → resource_calendar_leaves: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (resource_calendar_leaves): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## resourceResource

From `resource_resource`.

Why:
- resource_resource → hr_employee, resource_calendar_leaves: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- resource_calendar, res_company, res_users → resource_resource: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (resource_resource): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## returnReason

From `return_reason`.

Why:
- res_users → return_reason: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- return_reason → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (return_reason): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## saleOrderTemplate

From `sale_order_template`.

Why:
- sale_order_template → crm_team_sale_order_template_rel, header_footer_quotation_template_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_template → sale_order, sale_order_template_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, res_currency, mail_template → sale_order_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (sale_order_template): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## saleOrderTemplateLine

From `sale_order_template_line`.

Why:
- sale_order_template_line → account_tax_sale_order_template_line_rel, product_template_attribute_value_sale_order_template_line_rel: **reference**, a link table, embedded on the other side (assumed)
- sale_order_template_line → product_attribute_custom_value: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, product_product, uom_uom, sale_order_template → sale_order_template_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (sale_order_template_line): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## salePdfFormField

From `sale_pdf_form_field`.

Why:
- sale_pdf_form_field → product_document_sale_pdf_form_field_rel, quotation_document_sale_pdf_form_field_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → sale_pdf_form_field: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (sale_pdf_form_field): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## smsSms

From `sms_sms`.

Why:
- res_users, mail_message, res_partner → sms_sms: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (sms_sms): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (sms_sms): LOB column(s) body: measure row_bytes/embed_bytes before embedding this table or embedding it into a parent; keep large bodies in a separate collection (or GridFS) if they approach the 16 MB document limit
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## smsTemplate

From `sms_template`.

Why:
- sms_template → calendar_alarm, ir_act_server, project_project_stage, project_task_type, res_company: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, ir_model, ir_act_window → sms_template: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (sms_template): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## spreadsheetDashboardFavoriteFilters

From `spreadsheet_dashboard_favorite_filters`.

Why:
- spreadsheet_dashboard_favorite_filters → res_users_spreadsheet_dashboard_favorite_filters_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, spreadsheet_dashboard → spreadsheet_dashboard_favorite_filters: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (spreadsheet_dashboard_favorite_filters): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## spreadsheetDashboardGroup

From `spreadsheet_dashboard_group`.

Why:
- spreadsheet_dashboard_group → spreadsheet_dashboard: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → spreadsheet_dashboard_group: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (spreadsheet_dashboard_group): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockLot

From `stock_lot`.

Why:
- stock_lot → product_value: **reference**, it is embedded under another parent; this one is referenced (derived)
- stock_lot → res_partner_stock_lot_rel: **reference**, a link table, embedded on the other side (assumed)
- res_company, res_users, stock_location, product_product → stock_lot: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_lot → stock_move_line, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (stock_lot): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (stock_lot): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## stockPackage

From `stock_package`.

Why:
- stock_package → stock_move_line, stock_package, stock_package_history, stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_location, stock_package_type → stock_package: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_package): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockPicking

From `stock_picking`.

Why:
- stock_picking → purchase_order_stock_picking_rel, stock_package_history_stock_picking_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking → stock_move, stock_move_line, stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_picking_batch, res_company, res_users, stock_location, res_partner, stock_picking_type, project_project, return_reason, sale_order → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (stock_picking): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **lob** (stock_picking): LOB column(s) note measured max 0 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockPickingBatch

From `stock_picking_batch`.

Why:
- stock_picking_batch → stock_picking: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_picking_type → stock_picking_batch: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_picking_batch): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockPickingType

From `stock_picking_type`.

Why:
- stock_picking_type → picking_type_favorite_user_rel, product_category_stock_picking_type_rel, stock_location_stock_picking_type_rel: **reference**, a link table, embedded on the other side (assumed)
- stock_picking_type → purchase_order, stock_move, stock_picking, stock_picking_batch, stock_picking_type, stock_rule, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- stock_location, res_company, res_users, ir_sequence, stock_warehouse → stock_picking_type: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_picking_type): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockPutawayRule

From `stock_putaway_rule`.

Why:
- stock_putaway_rule → stock_package_type_stock_putaway_rule_rel: **reference**, a link table, embedded on the other side (assumed)
- product_category, res_company, res_users, stock_location, product_product, stock_storage_category → stock_putaway_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_putaway_rule): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockQuant

From `stock_quant`.

Why:
- res_company, res_users, stock_location, stock_lot, res_partner, stock_package, product_product → stock_quant: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_quant): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockRule

From `stock_rule`.

Why:
- stock_rule → stock_move, stock_warehouse: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_location, res_partner, stock_picking_type, stock_route, stock_warehouse → stock_rule: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_rule): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockScrapReasonTag

From `stock_scrap_reason_tag`.

Why:
- stock_scrap_reason_tag → stock_move_stock_scrap_reason_tag_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users → stock_scrap_reason_tag: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_scrap_reason_tag): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockStorageCategory

From `stock_storage_category`.

Why:
- stock_storage_category → stock_location, stock_putaway_rule, stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users → stock_storage_category: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_storage_category): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## stockStorageCategoryCapacity

From `stock_storage_category_capacity`.

Why:
- res_users, stock_package_type, product_product, stock_storage_category → stock_storage_category_capacity: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (3):
- **no_access_evidence** (stock_storage_category_capacity): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## stockWarehouseOrderpoint

From `stock_warehouse_orderpoint`.

Why:
- stock_warehouse_orderpoint → purchase_order_line, stock_move: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_company, res_users, stock_location, product_product, uom_uom, stock_route, product_supplierinfo, stock_warehouse → stock_warehouse_orderpoint: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (stock_warehouse_orderpoint): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## surveySurvey

From `survey_survey`.

Why:
- survey_survey → gamification_badge, hr_resume_line: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- survey_survey → res_lang_survey_survey_rel, res_users_survey_survey_rel: **reference**, a link table, embedded on the other side (assumed)
- survey_survey → survey_question: **reference**, the app reads it on its own (derived)
- gamification_badge, mail_template, res_users, survey_question, crm_team → survey_survey: **reference**, other tables also point at it, so it keeps its own collection (derived)
- survey_survey → survey_user_input: **reference**, other tables also point at it, so it keeps its own collection (derived)
- survey_survey → survey_user_input_line: **reference**, another parent owns it; this one is referenced (derived)

Open questions (5):
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
- **source_index_not_exercised** (survey_survey): source index not exercised by any confirmed access pattern; keep or drop
- **source_index_not_exercised** (survey_survey): source index not exercised by any confirmed access pattern; keep or drop

## surveyUserInput

From `survey_user_input`.

Why:
- survey_user_input → survey_question_survey_user_input_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, res_lang, survey_question, crm_lead, res_partner, survey_survey → survey_user_input: **reference**, other tables also point at it, so it keeps its own collection (derived)
- survey_user_input → survey_user_input_line: **reference**, the app reads it on its own (derived)

Open questions (1):
- **source_index_not_exercised** (survey_user_input): source index not exercised by any confirmed access pattern; keep or drop

## surveyUserInputLine

From `survey_user_input_line`.

Why:
- res_users, survey_question_answer, survey_question, survey_survey → survey_user_input_line: **reference**, another parent owns it; this one is referenced (derived)
- survey_user_input → survey_user_input_line: **reference**, the app reads it on its own (derived)

Open questions (1):
- **lob** (survey_user_input_line): LOB column(s) value_text_box measured max 123 bytes on this data: size allows embedding, but confirm the bound on the real estate (profile is a sample)

## uomUom

From `uom_uom`.

Why:
- uom_uom → account_analytic_line, account_move_line, barcode_rule, product_pricelist_item, product_supplierinfo, product_template, product_uom, project_update, purchase_order_line, res_company, sale_order_line, sale_order_template_line, stock_move, stock_move_line, stock_warehouse_orderpoint, uom_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- uom_uom → hr_expense: **reference**, other tables also point at it, so it keeps its own collection (derived)
- uom_uom → product_product_uom_uom_rel, product_template_uom_uom_rel: **reference**, a link table, embedded on the other side (assumed)
- res_users, stock_package_type → uom_uom: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (uom_uom): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced

## utmCampaign

From `utm_campaign`.

Why:
- utm_campaign → account_move, crm_lead, event_registration, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users, utm_stage → utm_campaign: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- utm_campaign → utm_tag_rel: **reference**, a link table, embedded on the other side (assumed)

Open questions (1):
- **no_access_evidence** (utm_campaign): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## utmMedium

From `utm_medium`.

Why:
- utm_medium → account_move, crm_lead, event_registration, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → utm_medium: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (utm_medium): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## utmSource

From `utm_source`.

Why:
- utm_source → account_move, crm_lead, event_registration, sale_order: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → utm_source: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (utm_source): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## utmStage

From `utm_stage`.

Why:
- utm_stage → utm_campaign: **reference**, other tables also point at it, so it keeps its own collection (assumed)
- res_users → utm_stage: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (1):
- **no_access_evidence** (utm_stage): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged

## website

From `website`.

Why:
- res_company, res_users → website: **reference**, other tables also point at it, so it keeps its own collection (assumed)

Open questions (2):
- **no_access_evidence** (website): no confirmed non-deploy application pattern touches this collection or its embedded tables; review these pointer/FK columns as index candidates, but do not create indexes without workload evidence; any source_indexes listed are carried over unchanged
- **nullable_unique_key**: source UNIQUE admits repeated NULLs, a MongoDB unique index does not: confirm no NULLs and add an index decision, or keep it unenforced
