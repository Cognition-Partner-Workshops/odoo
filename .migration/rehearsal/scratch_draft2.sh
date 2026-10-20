#!/usr/bin/env bash
# s3.1 reproducible recipe (UNT12-9, plan decision d-plugin-gap = accept-scratch-draft2):
# rebuilds map-draft-2 from the map-draft-1 proposal with the pinned, unpatched plugin.
# Input is map-draft-1 as committed on the run branch (BASE_REF, default origin/mongo-run/unt12),
# never the working copy. Steps: 1) copy it and filter out the 299 `references[].to` rows that
# name collections of --exclude-table tables (the plugin gap at 9a584b4: model_proposal.py emits
# them and model_patch.py refuses every decision while they exist; see NOTES.md s3.1),
# 2) apply .migration/answers.txt + design_decisions.json with the pinned model_patch.py,
# 3) run --check, 4) render the review page. Output lands under $SCRATCH; the sha256 printed at
# the end must equal the committed .migration/mapping_spec.json for the recipe to hold.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PLUGIN=${PLUGIN:-/home/ubuntu/plugin-9a584b4}
PY=${PY:-/home/ubuntu/.venvs/recon/bin/python}
SCRATCH=${SCRATCH:-/home/ubuntu/scratch}
BASE_REF=${BASE_REF:-origin/mongo-run/unt12}
M="$PLUGIN/skills/schema-modeling"
OUT="$SCRATCH"
mkdir -p "$SCRATCH"
cd "$ROOT"
git show "$BASE_REF:.migration/mapping_spec.json" > "$SCRATCH/spec_map-draft-1.json"

python3 - "$SCRATCH/spec_map-draft-1.json" "$SCRATCH/spec_nodangling.json" <<'PY'
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
  --out "$OUT/mapping_spec.map-draft-2.json" --version map-draft-2 \
  --data-profile .migration/data_profile.json --census .migration/census.json \
  --access-patterns .migration/access_patterns.json --workspace .

set +e
"$PY" "$M/model_patch.py" --spec "$OUT/mapping_spec.map-draft-2.json" \
  --data-profile .migration/data_profile.json --census .migration/census.json \
  --access-patterns .migration/access_patterns.json --check > "$SCRATCH/check.tmp" 2>&1
CODE=$?
set -e
{ echo "exit=$CODE"; cat "$SCRATCH/check.tmp"; } > "$OUT/check.map-draft-2.txt"
echo "--check on the rebuilt map-draft-2: exit $CODE ($(grep -c 'no rationale row' "$OUT/check.map-draft-2.txt") 'no rationale row' lines)"

python3 "$M/model_cards.py" --spec "$OUT/mapping_spec.map-draft-2.json" \
  --out "$OUT/model_cards.map-draft-2.md"
echo "rebuilt map-draft-2 sha256: $(sha256sum "$OUT/mapping_spec.map-draft-2.json" | cut -c1-64) (committed: $(sha256sum .migration/mapping_spec.json | cut -c1-64))"
