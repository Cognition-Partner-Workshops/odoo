#!/usr/bin/env bash
# s3.1 scratch probe (UNT12-9): what the pinned plugin would produce if it tolerated the
# proposer's references to excluded tables. Works on a COPY of the committed spec under
# $SCRATCH; the committed .migration/mapping_spec.json is never touched and the plugin
# is not patched. Steps: 1) copy the spec and filter out the 299 `references[].to` rows
# that name collections of excluded tables (the only edit, and it is why this is scratch),
# 2) apply .migration/answers.txt + design_decisions.json with the pinned model_patch.py,
# 3) run --check, 4) render the review page.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PLUGIN=${PLUGIN:-/home/ubuntu/plugin-9a584b4}
PY=${PY:-/home/ubuntu/.venvs/recon/bin/python}
SCRATCH=${SCRATCH:-/home/ubuntu/scratch}
M="$PLUGIN/skills/schema-modeling"
OUT="$ROOT/.migration/rehearsal"
mkdir -p "$SCRATCH"
cd "$ROOT"

python3 - "$ROOT/.migration/mapping_spec.json" "$SCRATCH/spec_nodangling.json" <<'PY'
import json, sys
spec = json.load(open(sys.argv[1]))
names = {c["collection"] for c in spec["collections"]}
dropped = 0
for c in spec["collections"]:
    refs = c["decision"]["references"]
    c["decision"]["references"] = [r for r in refs if r["to"] in names]
    dropped += len(refs) - len(c["decision"]["references"])
    for e in c["embeds"]:
        refs = e.get("child_references", [])
        e["child_references"] = [r for r in refs if r["to"] in names]
        dropped += len(refs) - len(e["child_references"])
json.dump(spec, open(sys.argv[2], "w"), indent=1)
print(f"scratch copy: {dropped} references to excluded-table collections filtered out")
PY

cp .migration/design_decisions.json "$SCRATCH/design_decisions.json"
"$PY" "$M/model_patch.py" --spec "$SCRATCH/spec_nodangling.json" \
  --answers .migration/answers.txt --decisions "$SCRATCH/design_decisions.json" \
  --out "$OUT/mapping_spec.map-draft-2.scratch.json" --version map-draft-2 \
  --data-profile .migration/data_profile.json --census .migration/census.json \
  --access-patterns .migration/access_patterns.json --workspace .

set +e
"$PY" "$M/model_patch.py" --spec "$OUT/mapping_spec.map-draft-2.scratch.json" \
  --data-profile .migration/data_profile.json --census .migration/census.json \
  --access-patterns .migration/access_patterns.json --check > "$SCRATCH/check.tmp" 2>&1
CODE=$?
set -e
{ echo "exit=$CODE"; cat "$SCRATCH/check.tmp"; } > "$OUT/check.map-draft-2.scratch.txt"
echo "--check on the scratch map-draft-2: exit $CODE ($(grep -c 'no rationale row' "$OUT/check.map-draft-2.scratch.txt") 'no rationale row' lines)"

python3 "$M/model_cards.py" --spec "$OUT/mapping_spec.map-draft-2.scratch.json" \
  --out "$OUT/model_cards.map-draft-2.scratch.md"
