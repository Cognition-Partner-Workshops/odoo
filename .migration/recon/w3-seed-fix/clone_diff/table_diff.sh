#!/usr/bin/env bash
# per-table row diff of two clones: sorted column-insert dumps, differing INSERT lines grouped by table
set -u
export PGHOST=/var/run/postgresql PGPORT=5433
A=$1; B=$2; OUT=$3
mkdir -p "$OUT"
for db in "$A" "$B"; do
  pg_dump --data-only --column-inserts --no-owner "$db" | grep '^INSERT INTO' | sed 's/^INSERT INTO public\.//' | LC_ALL=C sort > "$OUT/$db.sorted.sql"
done
LC_ALL=C comm -3 "$OUT/$A.sorted.sql" "$OUT/$B.sorted.sql" > "$OUT/differing_lines.txt"
echo "differing INSERT lines: $(wc -l < "$OUT/differing_lines.txt")"
sed -E 's/^\t?([a-z0-9_]+) .*/\1/' "$OUT/differing_lines.txt" | sort | uniq -c | sort -rn > "$OUT/by_table.txt"
cat "$OUT/by_table.txt"
