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
cp assets/og.png "$OUT/og.png"; # videos de producciones: se sirven desde Pages para verlos sin salir del sitio
mkdir -p "$OUT/v"; for f in fabrica-reel/docs/fabrica-reel.mp4 partitura-reel/docs/partitura-reel.mp4 harness-reel/docs/harness-reel.mp4; do [ -f "$f" ] && cp "$f" "$OUT/v/"; done
cp assets/harness-frame.jpg assets/hero.mp4 assets/hero-poster.jpg assets/partitura.mp4 assets/partitura-poster.jpg "$OUT/"   # meta imagen y poster del reel

# Galería de motion-lab: una página con el preview en video de cada receta y link a su SKILL.md
if [ -d skills/motion-lab ]; then
  mkdir -p "$OUT/motion-lab"
  tiles=""
  for r in skills/motion-lab/*/; do
    [ -f "$r/SKILL.md" ] || continue
    n=$(basename "$r")
    # la descripción del frontmatter puede ser multilínea (description: |); se juntan las líneas indentadas
    d=$(awk '/^---/{c++; next} c==1 && /^description:/{ if ($0 ~ /\|[ ]*$/) {m=1; next} sub(/^description:[ ]*/,""); print; exit } m && /^[ ]+/{sub(/^[ ]+/,""); printf "%s ", $0; next} m{exit}' "$r/SKILL.md" | sed 's/ *$//')
    v=""; [ -f "$r/preview.mp4" ] && v="<video src=\"../.well-known/skills/motion-lab/$n/preview.mp4\" poster=\"../.well-known/skills/motion-lab/$n/preview.png\" muted loop playsinline preload=\"metadata\"></video>"
    tiles="$tiles<a class=\"tile\" href=\"../.well-known/skills/motion-lab/$n/SKILL.md\"><div class=\"media\">$v</div><div class=\"body\"><h3>$n</h3><p>$d</p></div></a>"
  done
  awk -v tiles="$tiles" '{ if (index($0,"<!--TILES-->")) print tiles; else print }' scripts/gallery-template.html > "$OUT/motion-lab/index.html"
fi

# La página: plantilla + una tarjeta por skill, con links a sus archivos
cards=$(jq -r '.skills[] as $s | ($s.files|length) as $n
  | "<div class=\"skill\"><h3>\($s.name)</h3><p>\($s.description)</p>"
  + (if $n > 12 then "<details class=\"files-wrap\"><summary>\($n) archivos</summary>" else "" end)
  + "<div class=\"files\">" + ([$s.files[] | "<a href=\".well-known/skills/\($s.name)/\(.)\">\(.)</a>"] | join(" ")) + "</div>"
  + (if $n > 12 then "</details>" else "" end) + "</div>"' "$OUT/.well-known/skills/index.json" | tr -d "\n")
awk -v cards="$cards" '{ if (index($0,"<!--SKILLS-->")) print cards; else print }' scripts/pages-template.html > "$OUT/index.html"
cat "$OUT/.well-known/skills/index.json"
