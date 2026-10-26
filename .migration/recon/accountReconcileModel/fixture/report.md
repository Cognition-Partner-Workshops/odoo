# Recon report: unit `accountReconcileModel`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `573f2cd0e8ea` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `7c85166a328a`
- Collections: `accountReconcileModel`
- Seed: `0`
- Generated: 2026-10-26T05:30:14.145586+00:00
- 18 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 8 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 3 | PASS |
| 2 | per_field_aggregates | 13 | PASS |
| 3 | keyed_diffs | 20 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountReconcileModel": 9
  },
  "embed_source_counts": {
    "accountReconcileModel.resPartnerRel": 1,
    "accountReconcileModel.line": 10
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
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
      "field": "accountReconcileModel.name",
      "key": "accountReconcileModel"
    }
  ],
  "fields_fully_deferred": 8
}
```

## Tier 3 coverage
```json
{
  "accountReconcileModel": {
    "mode": "full_diff",
    "population": 9,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountReconcileModel.resPartnerRel": 1,
    "accountReconcileModel.line": 10
  }
}
```
