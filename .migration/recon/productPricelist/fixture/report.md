# Recon report: unit `productPricelist`

- **Verdict: PASS** (values redacted)
- Mode: `fixture` (fixture data: NOT a merge verdict, run live once before merging)
- Merge eligible: no (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `c0b93dad9526`)
- Tolerance version: `1` (sha256 `8c9b9e4cf438`)
- Evidence: git `2f68f2104eda` (dirty) | source db `odoo_fixture` | source server `hmac-sha256:993afb77f5d4f38d` | ops sha256 `4230b7ba77ba`
- Collections: `productPricelist`
- Seed: `1`
- Generated: 2026-10-26T03:33:24.968127+00:00
- 8 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 1 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 1 | PASS |
| 2 | per_field_aggregates | 6 | PASS |
| 3 | keyed_diffs | 9 | PASS |
| 4 | app_level_parity | 1 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productPricelist": 9
  },
  "embed_source_counts": {}
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productPricelist.sequence",
    "productPricelist.companyId",
    "productPricelist.createUid",
    "productPricelist.writeUid",
    "productPricelist.name",
    "productPricelist.active",
    "productPricelist.createDate",
    "productPricelist.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productPricelist.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productPricelist.name",
      "key": "productPricelist"
    }
  ],
  "fields_fully_deferred": 3
}
```

## Tier 3 coverage
```json
{
  "productPricelist": {
    "mode": "full_diff",
    "population": 9,
    "duplicate_source_key_count": 0
  }
}
```
