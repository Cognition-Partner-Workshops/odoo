# Recon report: unit `account-journal`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-2` (sha256 `88650faf41b7`)
- Tolerance version: `unt12-3` (sha256 `7b426db21459`)
- Collections: `accountJournal`, `accountPaymentMethod`, `accountReconcileModel`, `accountReconcileModelLineAccountTaxRel`
- Seed: `0`
- Generated: 2026-10-20T21:10:52.297242+00:00
- 57 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 20 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 36 | PASS |
| 2 | per_field_aggregates | 38 | PASS |
| 3 | keyed_diffs | 41 | PASS |
| 4 | app_level_parity | 5 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountJournal": 14,
    "accountPaymentMethod": 2,
    "accountReconcileModel": 8,
    "accountReconcileModelLineAccountTaxRel": 1
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountJournal.aliasId",
    "accountJournal.defaultAccountId",
    "accountJournal.suspenseAccountId",
    "accountJournal.nonDeductibleAccountId",
    "accountJournal.sequence",
    "accountJournal.currencyId",
    "accountJournal.invoiceTemplatePdfReportId",
    "accountJournal.profitAccountId",
    "accountJournal.lossAccountId",
    "accountJournal.bankAccountId",
    "accountJournal.journalGroupId",
    "accountJournal.createUid",
    "accountJournal.writeUid",
    "accountJournal.color",
    "accountJournal.accessToken",
    "accountJournal.code",
    "accountJournal.type",
    "accountJournal.invoiceReferenceType",
    "accountJournal.invoiceReferenceModel",
    "accountJournal.bankStatementsSource",
    "accountJournal.incomingEinvoiceNotificationEmail",
    "accountJournal.name",
    "accountJournal.sequenceOverrideRegex",
    "accountJournal.active",
    "accountJournal.isSelfBilling",
    "accountJournal.restrictModeHashTable",
    "accountJournal.refundSequence",
    "accountJournal.paymentSequence",
    "accountJournal.showOnDashboard",
    "accountJournal.disableDashboardGraph",
    "accountJournal.createDate",
    "accountJournal.writeDate",
    "accountPaymentMethod.createUid",
    "accountPaymentMethod.writeUid",
    "accountPaymentMethod.code",
    "accountPaymentMethod.paymentType",
    "accountPaymentMethod.name",
    "accountPaymentMethod.createDate",
    "accountPaymentMethod.writeDate",
    "accountReconcileModel.nextActivityTypeId",
    "accountReconcileModel.mappedPartnerId",
    "accountReconcileModel.createUid",
    "accountReconcileModel.writeUid",
    "accountReconcileModel.trigger",
    "accountReconcileModel.matchAmount",
    "accountReconcileModel.matchLabel",
    "accountReconcileModel.matchLabelParam",
    "accountReconcileModel.paymentToleranceType",
    "accountReconcileModel.matchingOrder",
    "accountReconcileModel.ruleType",
    "accountReconcileModel.name",
    "accountReconcileModel.active",
    "accountReconcileModel.canBeProposed",
    "accountReconcileModel.createDate",
    "accountReconcileModel.writeDate",
    "accountReconcileModel.matchAmountMin",
    "accountReconcileModel.matchAmountMax"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountJournal.accessToken",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.type",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.invoiceReferenceType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.invoiceReferenceModel",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.bankStatementsSource",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.incomingEinvoiceNotificationEmail",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountJournal.sequenceOverrideRegex",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountPaymentMethod.code",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountPaymentMethod.paymentType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountPaymentMethod.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.trigger",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.matchAmount",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.matchLabel",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.matchLabelParam",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.paymentToleranceType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.matchingOrder",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.ruleType",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountReconcileModel.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountJournal.name",
      "key": "accountJournal"
    },
    {
      "field": "accountPaymentMethod.name",
      "key": "accountPaymentMethod"
    },
    {
      "field": "accountReconcileModel.name",
      "key": "accountReconcileModel"
    }
  ],
  "fields_fully_deferred": 23
}
```

## Tier 3 coverage
```json
{
  "accountJournal": {
    "mode": "full_diff",
    "population": 14,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountJournal.accountReconcileModelRel": 1,
    "accountPaymentMethod.line": 4,
    "accountReconcileModel.resPartnerRel": 1,
    "accountReconcileModel.line": 10
  },
  "accountPaymentMethod": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "accountReconcileModel": {
    "mode": "full_diff",
    "population": 8,
    "duplicate_source_key_count": 0
  },
  "accountReconcileModelLineAccountTaxRel": {
    "mode": "full_diff",
    "population": 1,
    "duplicate_source_key_count": 0
  }
}
```
