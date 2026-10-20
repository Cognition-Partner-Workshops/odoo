# Recon report: unit `uom`

- **Verdict: PASS** (values redacted)
- Mode: `live`
- Merge eligible: yes (fixture/continuous evidence never merges)
- Mapping version: `map-draft-5` (sha256 `e329b5aec09f`)
- Tolerance version: `v1` (sha256 `59f500708400`)
- Collections: `uomUom`
- Seed: `0`
- Generated: 2026-10-19T21:29:35.208517+00:00
- 12 fields: Tier 2 aggregates deferred to Tier 3 (rules change the value)
- 3 string fields: min/max/distinct deferred to Tier 3

| Tier | Name | Checks | Result |
|---|---|---|---|
| 1 | counts_through_mapping | 3 | PASS |
| 2 | per_field_aggregates | 8 | PASS |
| 3 | keyed_diffs | 30 | PASS |

## Tier 1 coverage
```json
{
  "source_counts": {
    "uomUom": 30
  }
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
