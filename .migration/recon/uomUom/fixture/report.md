# Recon report: unit `uomUom`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `7e53e0a39694` | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `015639493d64`
- Collections: `uomUom`
- Seed: `1`
- Generated: 2026-10-26T03:46:55.904480+00:00
- 12 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 8 | PASS |
| 3 | keyed_diffs | 30 | PASS |
| 4 | app_level_parity | 2 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "uomUom": 30
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "uomUom.sequence",
    "uomUom.relativeUomId",
    "uomUom.createUid",
    "uomUom.writeUid",
    "uomUom.parentPath",
    "uomUom.name",
    "uomUom.factor",
    "uomUom.active",
    "uomUom.createDate",
    "uomUom.writeDate",
    "uomUom.packageTypeId",
    "uomUom.uneceCode"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "uomUom.parentPath",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "uomUom.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    },
    {
      "field": "uomUom.uneceCode",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "uomUom.name",
      "key": "uomUom"
    }
  ],
  "fields_fully_deferred": 5
}
```

## Tier 3 coverage
```json
{
  "uomUom": {
    "mode": "full_diff",
    "population": 30,
    "duplicate_source_key_count": 0
  }
}
```
