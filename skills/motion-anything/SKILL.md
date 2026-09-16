---
name: motion-anything
description: Biblioteca de 85 recetas web (texto cinético, entradas, fondos, shaders), 20 efectos para tarjetas y 94 clases CSS tipo animate.css, dependency-free (Apache-2.0, ports de react-bits con permiso). Úsala ANTES de escribir un efecto a mano en cualquier reel, short o tarjeta HTML/HyperFrames — revisa si ya existe la receta. Cada receta trae SKILL.md (cuándo usarla), preview.html y el .css/.js que se copia. Lo que anima con CSS keyframes o WAAPI es seek-safe y entra directo a HyperFrames; canvas/WebGL con reloj propio sólo en grabación en tiempo real.
---

# Recetas de motion-anything

Copiadas de `nexu-io/motion-anything` (Apache-2.0). Créditos de terceros en `ATTRIBUTION.md`;
contrato de cada receta en `MOTION-SPEC.md`.

- `web/` — 85 efectos dependency-free. Texto cinético: `kinetic-headline`, `text-scramble`,
  `decrypted-text`, `falling-text`, `count-up`, `glitch-text`, `rotating-text`, `shuffle-text`.
  Entradas: `bounce-cards`, `stagger-list`, `fade-in-up`, `scroll-reveal`. Fondos: `dot-grid`,
  `pixel-transition`, `aurora`, `silk`, `waves`, `particles`. Cada carpeta: `SKILL.md`,
  `preview.html` y el archivo que se copia.
- `slides/` — 20 efectos para tarjetas y títulos: `fx-word-cascade`, `fx-letter-explode`,
  `fx-confetti`, `fx-shockwave`, `fx-typewriter-multi`, `fx-counter-explosion`.
- `css/` — 94 clases estilo animate.css (`anim-bouncein`, `anim-backinup`…).

## Cómo usarlas

1. Antes de animar a mano, busca la receta: `ls web slides css | grep <palabra>` y lee su `SKILL.md`.
2. Abre `preview.html` en el navegador para ver el efecto antes de copiarlo.
3. Copia el `.css`/`.js` al proyecto e inicialízalo como indica su `SKILL.md`.

## Reglas para video (HyperFrames)

- CSS keyframes y WAAPI son seek-safe y deterministas: entran directo.
- `requestAnimationFrame` o WebGL con reloj propio (shaders, canvas: `aurora`, `silk`, `plasma`,
  `liquid-chrome`, `galaxy`…) NO es determinista frame a frame: úsalo sólo en grabaciones de
  pantalla en tiempo real, o exponle un `seek(t)`.
- Bucles finitos (nunca `repeat: -1`), paleta por marca, y un SFX por cada animación montado con
  ffmpeg fuera del render.
