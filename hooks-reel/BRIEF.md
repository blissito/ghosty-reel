---
workflow: general-video
flow: automation
storyboard: yes
message: "Los hooks son el único punto del harness donde metes control que no depende de que el modelo obedezca"
destination: youtube
aspect: 1080x1920
language: es
audience: "Desarrolladores que construyen con agentes de IA (suscriptores de FixterGeek)"
length: 120s
angle: concept
voice: em_santa
---

## Intent

Video para el correo 3 de la secuencia de preparación del taller de sistemas
agénticos. Tres escenas, ~2 minutos:

1. **El problema** — pedirle al modelo que obedezca es una apuesta, no un control.
2. **El hook** — el punto determinista del harness: corre siempre, el modelo no lo vota.
3. **Primitiva general** — no es cosa de Claude Code: LangGraph lo llama
   middleware, el OpenAI Agents SDK lo llama lifecycle hooks + guardrails.

Sin cara, sin footage. Tipografía, formas planas y diagramas animados.
Tono: español mexicano profesional, directo, sin voseo argentino.

## Customizations

- **Dirección de arte nueva: caricatura plana.** Colores sólidos saturados,
  contorno de tinta grueso, cero gradientes, cero glow, cero blur. Ver `frame.md`.
- Narración TTS local Kokoro (`em_santa`, velocidad 0.92), `[pausa]` como marca
  de corte.
- Cama musical suave sintetizada localmente con ffmpeg.
- **Style frames primero**: antes de animar, se producen diapositivas de estilo
  estáticas para que bliss apruebe la dirección visual.

## Qué mejorar respecto a `videos/contexto-escritorio`

- Menos escenas y más largas allá (10 escenas / 271s) → aquí 3 escenas densas.
- El fondo de blobs radiales con gradiente se reemplaza por campo plano de
  formas sólidas.
- Motion con más carácter: overshoot y squash-and-stretch de caricatura,
  no sólo `power3.out` limpio.

## Notes

- No tocar nada del repo `fixter2025` fuera de este directorio.
- Los nombres de framework en pantalla, no narrados letra por letra.
