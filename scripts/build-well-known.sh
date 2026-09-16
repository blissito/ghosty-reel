#!/usr/bin/env bash
# Genera .well-known/skills/ a partir de skills/*/ para que `npx skills add <url>` lo encuentre.
set -euo pipefail
OUT="${1:-_site}"
rm -rf "$OUT" && mkdir -p "$OUT/.well-known/skills"
entries=""
for dir in skills/*/; do
  name=$(basename "$dir")
  cp -R "$dir" "$OUT/.well-known/skills/$name"
  desc=$(awk '/^---/{c++; next} c==1 && /^description:/{sub(/^description:[ ]*/,""); print; exit}' "$dir/SKILL.md")
  files=$(cd "$dir" && find . -type f | sed 's#^\./##' | sort | jq -R . | jq -sc .)
  entries="$entries$(jq -nc --arg n "$name" --arg d "$desc" --argjson f "$files" '{name:$n,description:$d,files:$f}'),"
done
echo "{\"skills\":[${entries%,}]}" | jq . > "$OUT/.well-known/skills/index.json"
touch "$OUT/.nojekyll"
cat > "$OUT/index.html" <<HTML
<!doctype html><meta charset="utf-8"><title>ghosty-reel skills</title>
<pre>npx skills add https://blissito.github.io/ghosty-reel</pre>
<p><a href="https://github.com/blissito/ghosty-reel">github.com/blissito/ghosty-reel</a> · <a href=".well-known/skills/index.json">index.json</a></p>
HTML
cat "$OUT/.well-known/skills/index.json"
