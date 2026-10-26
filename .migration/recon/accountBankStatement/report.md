# Recon report: unit `accountBankStatement`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `1ddf4b2fbd61` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `f81806ba06b2`
- Collections: `accountBankStatement`
- Seed: `0`
- Generated: 2026-10-26T17:25:03.920300+00:00
- 16 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 9 | PASS |
| 2 | per_field_aggregates | 8 | PASS |
| 3 | keyed_diffs | 4 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountBankStatement": 2
  },
  "embed_source_counts": {
    "accountBankStatement.irAttachmentRel": 2
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountBankStatement.companyId",
    "accountBankStatement.currencyId",
    "accountBankStatement.journalId",
    "accountBankStatement.createUid",
    "accountBankStatement.writeUid",
    "accountBankStatement.name",
    "accountBankStatement.reference",
    "accountBankStatement.firstLineIndex",
    "accountBankStatement.date",
    "accountBankStatement.balanceStart",
    "accountBankStatement.balanceEnd",
    "accountBankStatement.balanceEndReal",
    "accountBankStatement.isComplete",
    "accountBankStatement.isStatementPosted",
    "accountBankStatement.createDate",
    "accountBankStatement.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountBankStatement.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountBankStatement.reference",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountBankStatement.firstLineIndex",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "fields_fully_deferred": 8
}
```

## Tier 3 coverage
```json
{
  "accountBankStatement": {
    "mode": "full_diff",
    "population": 2,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountBankStatement.irAttachmentRel": 2
  }
}
```
