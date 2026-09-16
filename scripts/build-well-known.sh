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
# La página: plantilla + una tarjeta por skill, con links a sus archivos
cards=$(jq -r '.skills[] as $s | "<div class=\"skill\"><h3>\($s.name)</h3><p>\($s.description)</p><div class=\"files\">" + ([$s.files[] | "<a href=\".well-known/skills/\($s.name)/\(.)\">\(.)</a>"] | join(" ")) + "</div></div>"' "$OUT/.well-known/skills/index.json")
awk -v cards="$cards" '{ if ($0=="<!--SKILLS-->") print cards; else print }' scripts/pages-template.html > "$OUT/index.html"
cat "$OUT/.well-known/skills/index.json"
