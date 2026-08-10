# Reels generados por completo desde la terminal

Video promocional con Blender headless: guion, voz, música, efectos, render y
mezcla. Nadie abre Blender, ni un editor de video, ni un DAW. Todo el stack es
libre.

## Cómo funciona

**1. Se escribe el guion y se genera la voz.** Kokoro local, sin red. Las
duraciones reales de esos audios son las que fijan todo lo demás.

**2. Esas duraciones se vuelcan a `scene.json`,** que es la dirección completa:
beats, posiciones, cámara. Ningún número vive dentro del script de escena.

**3. El audio se deriva de ahí.** `plan.py` coloca cada efecto en el beat visual
al que responde, no en un segundo escrito a mano. `music.py` sintetiza el bed
desde cero y saca de ahí su duración. Mover un beat realinea todo.

**4. Blender renderiza sin abrirse.** `scene.py` construye la escena, la anima y
saca los frames. `PREVIEW=1` da stills en un segundo para iterar sin esperar.

**5. `mix.sh` mezcla y encodea.** Voz, música y efectos con ffmpeg, pegados a los
frames.

## Las dos técnicas

**Capturar la UI.** La interfaz no se modela: Chrome headless la dispara en capas
separadas y Blender las usa como texturas. Ese corte en capas *es* el efecto — si
el botón viviera dentro de la textura de fondo, jamás podría despegarse de ella.

**Trazar con Grease Pencil.** Cuando no hay UI que mostrar sino una idea que
explicar. El diagrama se dibuja en el espacio 3D, la cámara entra entre las capas
y el trazo se dibuja solo. Render mucho más barato.

## Producciones

- **EasyBits** — 16:9, 32s, UI capturada. Vive en la raíz: fue la primera.
- **[harness-reel](./harness-reel)** — 9:16, 31s, Grease Pencil.

```bash
./capture.sh && python3 plan.py && python3 music.py    # EasyBits
blender -b -P scene.py && ./mix.sh
```

## Stack — todo libre

Blender 5.2 (GPL) · Chrome headless (BSD) · Kokoro-82M (Apache 2.0) · ffmpeg
(LGPL/GPL) · música sintetizada propia · SFX de Pixabay.

Sin cuentas, sin API keys, sin servicios.

Los gotchas que costaron horas están en
[`skills/blender-ad`](./skills/blender-ad), con un ejemplo que corre solo.

---

Hecho por [blissito](https://github.com/blissito) · [fixter.org](https://fixter.org)
