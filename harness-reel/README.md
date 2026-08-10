# harness-reel

Reel vertical 9:16 (~31s) sobre la anatomía de un agente, para el Taller
Sistemas Agénticos. A diferencia del anuncio de la raíz, aquí **no se captura
ninguna UI**: el diagrama se traza con Grease Pencil, así que la cámara puede
entrar entre las capas.

Estructura narrativa: Open Loop — el dato contraintuitivo abre en el segundo
cero y no se resuelve hasta "todo eso es el harness".

## Construir

```bash
export HYPERFRAMES_PYTHON=~/.venvs/kokoro/bin/python3
i=0; while IFS= read -r l; do i=$((i+1)); \
  npx hyperframes tts "$l" -v em_santa -l es -s 0.96 -o audio/vo/vo$i.wav </dev/null; \
done < lines.txt                      # 1. voz  (mide las duraciones reales)

python3 plan.py                       # 2. beats -> audio/plan.json
python3 music.py                      # 3. bed sintetizado
blender -b -P scene.py                # 4. 930 frames a 1080x1920
./mix.sh                              # 5. mezcla + encode -> out/ad.mp4
```

Iterar sin esperar el render completo:

```bash
PREVIEW=1 blender -b -P scene.py              # stills al 40% en cada beat
PREVIEW=1 FRAMES=95,585,880 blender -b -P scene.py
AUDIO_ONLY=1 ./mix.sh                         # juzgar la pista aparte
```

## scene.json manda

Los beats están en SEGUNDOS y salen de las duraciones reales de la voz. `plan.py`
deriva de ahí los SFX y `music.py` los ducks del bed, así que mover un beat y
volver a correr los tres realinea todo. Ningún tiempo se escribe a mano dos veces.

Los gotchas del pipeline (Grease Pencil, formato vertical, audio) están en
`../skills/blender-ad/SKILL.md`.
