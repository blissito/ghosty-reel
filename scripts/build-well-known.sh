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
cp assets/og.png "$OUT/og.png"; cp assets/harness-frame.jpg assets/hero.mp4 assets/hero-poster.jpg "$OUT/"   # meta imagen y poster del reel
# La página: plantilla + una tarjeta por skill, con links a sus archivos
cards=$(jq -r '.skills[] as $s | ($s.files|length) as $n
  | "<div class=\"skill\"><h3>\($s.name)</h3><p>\($s.description)</p>"
  + (if $n > 12 then "<details class=\"files-wrap\"><summary>\($n) archivos</summary>" else "" end)
  + "<div class=\"files\">" + ([$s.files[] | "<a href=\".well-known/skills/\($s.name)/\(.)\">\(.)</a>"] | join(" ")) + "</div>"
  + (if $n > 12 then "</details>" else "" end) + "</div>"' "$OUT/.well-known/skills/index.json" | tr -d "\n")
awk -v cards="$cards" '{ if (index($0,"<!--SKILLS-->")) print cards; else print }' scripts/pages-template.html > "$OUT/index.html"
cat "$OUT/.well-known/skills/index.json"
