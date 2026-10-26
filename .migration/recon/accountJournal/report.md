# Recon report: unit `accountJournal`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `743e75613640` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `9f54225cc30e`
- Collections: `accountJournal`
- Seed: `0`
- Generated: 2026-10-26T06:03:42.820815+00:00
- 32 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 9 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 21 | PASS |
| 2 | per_field_aggregates | 20 | PASS |
| 3 | keyed_diffs | 26 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountJournal": 25
  },
  "embed_source_counts": {
    "accountJournal.accountReconcileModelRel": 1
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
    "accountJournal.writeDate"
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
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountJournal.name",
      "key": "accountJournal"
    }
  ],
  "fields_fully_deferred": 13
}
```

## Tier 3 coverage
```json
{
  "accountJournal": {
    "mode": "full_diff",
    "population": 25,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountJournal.accountReconcileModelRel": 1
  }
}
```
