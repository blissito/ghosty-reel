#!/usr/bin/env bash
# Arma la pista de audio (voz + SFX + música) desde audio/plan.json y la pega
# a los frames renderizados. La música es opcional: si audio/bgm.mp3 no existe,
# el resto se mezcla igual.
set -euo pipefail
cd "$(dirname "$0")"

command -v ffmpeg >/dev/null || { echo "falta ffmpeg: brew install ffmpeg"; exit 1; }
# AUDIO_ONLY=1 arma solo audio/mix.wav — útil para juzgar la pista mientras
# Blender todavía está renderizando.
[ -n "${AUDIO_ONLY:-}" ] || [ -d out/frames ] || \
  { echo "no hay frames: corre blender -b -P scene.py"; exit 1; }

python3 - "$@" <<'PY'
import json, os, shlex, subprocess, sys

plan = json.load(open("audio/plan.json"))
dur = plan["duration"]
sfx_dir = plan["sfx_dir"]

inputs, filters, mixed = [], [], []

# Adelanto global. El oído tolera muchísimo peor el audio TARDE que el audio
# temprano (ITU-R BT.1359: ~125ms tarde vs ~45ms adelantado antes de notarse),
# así que en motion graphics se sesga hacia adelante. Además el evento visual
# tiene anticipación —el cursor ya va bajando cuando "toca"— y el golpe leído
# como sincronizado cae 1-2 frames antes del contacto.
LEAD = plan.get("lead_ms", 0) / 1000.0


def add(path, at, gain, tag):
    if not os.path.exists(path):
        print(f"  [skip] {tag}: falta {path}")
        return
    at = max(0.0, at - LEAD)
    i = len(inputs)
    inputs.append(path)
    # adelay coloca el clip en su beat; sin él todo empieza en cero y el audio
    # se despega de la imagen.
    filters.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                   f"volume={gain},adelay={int(at*1000)}|{int(at*1000)}[a{i}]")
    mixed.append(f"[a{i}]")

for v in plan["voice"]:
    add(os.path.join("audio", v["file"]), v["at"], v["gain"], v["text"])
for s in plan["sfx"]:
    add(os.path.join(sfx_dir, s["file"]), s["at"], s["gain"], s["cue"])

b = plan["bgm"]
bgm_path = os.path.join("audio", b["file"])
if os.path.exists(bgm_path):
    i = len(inputs)
    inputs.append(bgm_path)
    filters.append(
        f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
        f"volume={b['gain']},afade=t=out:st={b['fade_out_at']}:d={dur-b['fade_out_at']:.2f}[a{i}]")
    mixed.append(f"[a{i}]")
else:
    print(f"  [skip] música: falta {bgm_path}")

if not mixed:
    sys.exit("no hay nada que mezclar")

# normalize=0: amix por defecto divide entre el número de entradas, lo que
# aplastaría la voz cada vez que coincide con un SFX.
# loudnorm trabaja internamente a 192 kHz y DEJA la salida ahí si no se le
# vuelve a bajar. Sin el aresample final el AAC terminaba en 96 kHz: bitrate
# desperdiciado y remuestreo en cada reproductor.
graph = ";".join(filters) + ";" + "".join(mixed) + \
    f"amix=inputs={len(mixed)}:normalize=0:dropout_transition=0," \
    f"atrim=0:{dur},alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11," \
    f"aresample=48000:resampler=soxr,aformat=sample_fmts=s16[out]"

cmd = ["ffmpeg", "-y"]
for p in inputs:
    cmd += ["-i", p]
cmd += ["-filter_complex", graph, "-map", "[out]",
        "-c:a", "pcm_s16le", "audio/mix.wav"]
subprocess.run(cmd, check=True, capture_output=True)
print(f"  audio/mix.wav  ({len(mixed)} pistas)")
PY

if [ -n "${AUDIO_ONLY:-}" ]; then
  echo "-> audio/mix.wav (solo audio)"
  exit 0
fi

FPS=$(python3 -c "import json;print(json.load(open('scene.json'))['fps'])")
ffmpeg -y -framerate "$FPS" -pattern_type glob -i 'out/frames/f*.png' -i audio/mix.wav \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 192k -ar 48000 -shortest out/ad.mp4 2>&1 | tail -1

echo "-> out/ad.mp4  ($(du -h out/ad.mp4 | cut -f1))"
