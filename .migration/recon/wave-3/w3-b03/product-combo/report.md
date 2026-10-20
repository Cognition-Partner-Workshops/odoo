# Recon report: unit `product-combo`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `productCombo`, `productComboItem`
- Seed: `0`
- Generated: 2026-10-20T15:28:11.629515+00:00
- 13 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 1 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 5 | PASS |
| 2 | per_field_aggregates | 11 | PASS |
| 3 | keyed_diffs | 14 | PASS |
| 4 | app_level_parity | 3 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "productCombo": 4,
    "productComboItem": 10
  }
}
```

## Tier 2 coverage
```json
{
  "deferred_to_tier3": [
    "productCombo.sequence",
    "productCombo.companyId",
    "productCombo.createUid",
    "productCombo.writeUid",
    "productCombo.name",
    "productCombo.createDate",
    "productCombo.writeDate",
    "productComboItem.companyId",
    "productComboItem.createUid",
    "productComboItem.writeUid",
    "productComboItem.extraPrice",
    "productComboItem.createDate",
    "productComboItem.writeDate"
  ],
  "string_aggregates_deferred_to_tier3": [
    {
      "field": "productCombo.name",
      "stats": [
        "min",
        "max",
        "distinct_count"
      ]
    }
  ],
  "document_aggregates_deferred_to_tier3": [
    {
      "field": "productCombo.name",
      "key": "productCombo"
    }
  ],
  "fields_fully_deferred": 4
}
```

## Tier 3 coverage
```json
{
  "productCombo": {
    "mode": "full_diff",
    "population": 4,
    "duplicate_source_key_count": 0
  },
  "productComboItem": {
    "mode": "full_diff",
    "population": 10,
    "duplicate_source_key_count": 0
  }
}
```
