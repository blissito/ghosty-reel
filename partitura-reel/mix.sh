#!/usr/bin/env bash
# Montaje: render mudo + música de la partitura (synth.py) + voz del CTA (em_santa, voice/cta.wav).
# Voz a −15 LUFS; la partitura va de pista principal (−17 LUFS) y se agacha con sidechain cuya llave es la voz sola.
# Ganancia fija medida con ebur128 + alimiter (nunca loudnorm al final), y verificación
# sobre el archivo entregado: start_time, blackdetect, SAR, tamaño, duración, LUFS.
# Uso: ./mix.sh renders/mudo.mp4 renders/factory-partitura.mp4
set -euo pipefail
cd "$(dirname "$0")"
IN=${1:-renders/mudo.mp4}
OUT=${2:-renders/factory-partitura.mp4}
TARGET=-14.5

node score.mjs
python3 synth.py music.wav

DUR=$(python3 -c "import json;print(json.load(open('score.gen.json'))['duration'])")
VS=$(python3 -c "import json;print(int(round(json.load(open('score.gen.json'))['voiceStart']*1000)))")
TMP=$(mktemp -d)
ffmpeg -v error -y -i voice/cta.wav -af "loudnorm=I=-15:TP=-1.5:LRA=11" -ar 48000 -ac 2 "$TMP/voice.wav"
MI=$(ffmpeg -hide_banner -i music.wav -af ebur128 -f null - 2>&1 | awk '/^ +I:/{print $2}' | tail -1)
MG=$(python3 -c "print(round(-17 - ($MI), 2))")
echo "música: $MI LUFS → ${MG} dB; voz en ${VS} ms"
# pre-mezcla: voz desplazada + música agachada por la voz; apad en cada entrada, sin -shortest
ffmpeg -v error -y -i "$TMP/voice.wav" -i music.wav -filter_complex "\
  [0:a]adelay=${VS}|${VS},apad=whole_dur=${DUR},asplit=2[v][key];\
  [1:a]volume=${MG}dB,aresample=48000,apad=whole_dur=${DUR}[m];\
  [m][key]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350[md];\
  [v][md]amix=inputs=2:normalize=0:duration=longest[a]" -map "[a]" -t "$DUR" "$TMP/pre.wav"
I=$(ffmpeg -hide_banner -i "$TMP/pre.wav" -af ebur128 -f null - 2>&1 | awk '/^ +I:/{print $2}' | tail -1)
GAIN=$(python3 -c "print(round($TARGET - ($I), 2))")
echo "pre-mezcla: $I LUFS → ganancia fija ${GAIN} dB"

ffmpeg -v error -y -i "$IN" -i "$TMP/pre.wav" \
  -filter_complex "[1:a]volume=${GAIN}dB,alimiter=limit=0.84:level=false,aresample=48000[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 256k -ar 48000 -movflags +faststart "$OUT"

echo "--- verificación de $OUT"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio,start_time -of compact "$OUT"
ffprobe -v error -select_streams a:0 -show_entries stream=start_time -of compact "$OUT"
ffprobe -v error -show_entries format=duration -of compact "$OUT"
ffmpeg -hide_banner -i "$OUT" -af ebur128 -f null - 2>&1 | awk '/^ +I:/{print "LUFS integrado:", $2}' | tail -1
BLACK=$(ffmpeg -hide_banner -i "$OUT" -vf "blackdetect=d=0.05:pic_th=0.98" -an -f null - 2>&1 | grep -c black_start || true)
echo "blackdetect: $BLACK tramos negros"
[ "$BLACK" = "0" ] || { echo "FALLA: hay fotogramas negros"; exit 1; }
for w in 8.3:8.9 25.3:26.3 31.5:35 35:37; do
  a=${w%:*}; b=${w#*:}
  printf "RMS %s–%s s: " "$a" "$b"
  ffmpeg -hide_banner -ss "$a" -to "$b" -i "$OUT" -af volumedetect -vn -f null - 2>&1 | awk '/mean_volume/{print $5, $6}'
done
