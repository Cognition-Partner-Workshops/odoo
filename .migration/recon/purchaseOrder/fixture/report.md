# Recon report: unit `purchaseOrder`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `f84dbc723f61` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `1e0296874331`
- Collections: `purchaseOrder`
- Seed: `0`
- Generated: 2026-10-26T16:39:09.852845+00:00
- 36 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 11 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 2 | PASS |
| 2 | per_field_aggregates | 21 | PASS |
| 3 | keyed_diffs | 27 | PASS |
| 4 | app_level_parity | 4 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "purchaseOrder": 20
  },
  "embed_source_counts": {
    "purchaseOrder.stockPickingRel": 7
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "purchaseOrder.destAddressId",
    "purchaseOrder.invoiceCount",
    "purchaseOrder.fiscalPositionId",
    "purchaseOrder.paymentTermId",
    "purchaseOrder.incotermId",
    "purchaseOrder.userId",
    "purchaseOrder.reminderDateBeforeReceipt",
    "purchaseOrder.createUid",
    "purchaseOrder.writeUid",
    "purchaseOrder.accessToken",
    "purchaseOrder.name",
    "purchaseOrder.priority",
    "purchaseOrder.origin",
    "purchaseOrder.partnerRef",
    "purchaseOrder.state",
    "purchaseOrder.invoiceStatus",
    "purchaseOrder.documentTaxMode",
    "purchaseOrder.incotermLocation",
    "purchaseOrder.receiptStatus",
    "purchaseOrder.note",
    "purchaseOrder.amountUntaxed",
    "purchaseOrder.amountTax",
    "purchaseOrder.amountTotal",
    "purchaseOrder.amountTotalCc",
    "purchaseOrder.currencyRate",
    "purchaseOrder.locked",
    "purchaseOrder.acknowledged",
    "purchaseOrder.receiptReminderEmail",
    "purchaseOrder.dateOrder",
    "purchaseOrder.dateApprove",
    "purchaseOrder.datePlanned",
    "purchaseOrder.dateCalendarStart",
    "purchaseOrder.createDate",
    "purchaseOrder.writeDate",
    "purchaseOrder.effectiveDate",
    "purchaseOrder.datePromised"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "purchaseOrder.accessToken",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.priority",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.origin",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.partnerRef",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.state",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.invoiceStatus",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.documentTaxMode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.incotermLocation",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.receiptStatus",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "purchaseOrder.note",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "fields_fully_deferred": 19
}
```

## Tier 3 coverage
```json
{
  "purchaseOrder": {
    "mode": "full_diff",
    "population": 20,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "purchaseOrder.stockPickingRel": 7
  }
}
```
