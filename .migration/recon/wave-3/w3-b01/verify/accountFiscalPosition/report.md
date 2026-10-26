# Recon report: unit `accountFiscalPosition`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `f84dbc723f61` | source db `odoo_src` | source server `hmac-sha256:545efbd0aca82e45` | ops sha256 `b041d3be5d6f`
- Collections: `accountFiscalPosition`
- Seed: `0`
- Generated: 2026-10-26T15:17:43.436730+00:00
- 16 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 5 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 11 | PASS |
| 2 | per_field_aggregates | 7 | PASS |
| 3 | keyed_diffs | 57 | PASS |
| 4 | app_level_parity | 1 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "accountFiscalPosition": 4
  },
  "embed_source_counts": {
    "accountFiscalPosition.account": 1,
    "accountFiscalPosition.resCountryStateRel": 2,
    "accountFiscalPosition.accountTaxRel": 50
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "accountFiscalPosition.sequence",
    "accountFiscalPosition.countryId",
    "accountFiscalPosition.countryGroupId",
    "accountFiscalPosition.createUid",
    "accountFiscalPosition.writeUid",
    "accountFiscalPosition.zipFrom",
    "accountFiscalPosition.zipTo",
    "accountFiscalPosition.foreignVat",
    "accountFiscalPosition.name",
    "accountFiscalPosition.note",
    "accountFiscalPosition.active",
    "accountFiscalPosition.autoApply",
    "accountFiscalPosition.vatRequired",
    "accountFiscalPosition.isDomestic",
    "accountFiscalPosition.createDate",
    "accountFiscalPosition.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "accountFiscalPosition.zipFrom",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.zipTo",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.foreignVat",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "accountFiscalPosition.note",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "accountFiscalPosition.name",
      "key": "accountFiscalPosition"
    },
    {
      "field": "accountFiscalPosition.note",
      "key": "accountFiscalPosition"
    }
  ],
  "fields_fully_deferred": 10
}
```

## Tier 3 coverage
```json
{
  "accountFiscalPosition": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
  },
  "embeds_graded": {
    "accountFiscalPosition.account": 1,
    "accountFiscalPosition.resCountryStateRel": 2,
    "accountFiscalPosition.accountTaxRel": 50
  }
}
```
