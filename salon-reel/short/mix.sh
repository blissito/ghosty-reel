#!/usr/bin/env bash
# Montaje: render mudo + voz em_santa (voz.wav, −15 LUFS) + música sintetizada (music.wav, −26 LUFS,
# agachada con sidechain cuya llave es la voz sola) + efectos (sfx.wav, al 0.7).
# Ganancia fija medida con ebur128 + alimiter (nunca loudnorm al final) y verificación sobre el entregado.
# Uso: ./mix.sh [renders/mudo.mp4] [renders/ghosty-inicia-sesion.mp4]
set -euo pipefail
cd "$(dirname "$0")"
IN=${1:-renders/mudo.mp4}
OUT=${2:-renders/ghosty-salon-unas.mp4}
TARGET=-14.5
DUR=16.2

./voz.sh
python3 synth.py
lufs() { ffmpeg -hide_banner -i "$1" -af ebur128 -f null - 2>&1 | awk '/^ +I:/{print $2}' | tail -1; }
VG=$(python3 -c "print(round(-15 - ($(lufs voz.wav)), 2))")
MG=$(python3 -c "print(round(-26 - ($(lufs music.wav)), 2))")
echo "voz ${VG} dB · música ${MG} dB"
TMP=$(mktemp -d)
ffmpeg -v error -y -i voz.wav -i music.wav -i sfx.wav -filter_complex "\
  [0:a]volume=${VG}dB,aresample=48000,apad=whole_dur=${DUR},asplit=2[v][key];\
  [1:a]volume=${MG}dB,aresample=48000,apad=whole_dur=${DUR}[m];\
  [m][key]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[md];\
  [2:a]volume=0.7,aresample=48000,apad=whole_dur=${DUR}[s];\
  [v][md][s]amix=inputs=3:normalize=0:duration=longest[a]" -map "[a]" -t "$DUR" "$TMP/pre.wav"
I=$(lufs "$TMP/pre.wav")
GAIN=$(python3 -c "print(round($TARGET - ($I), 2))")
echo "pre-mezcla: $I LUFS → ganancia fija ${GAIN} dB"
ffmpeg -v error -y -i "$IN" -i "$TMP/pre.wav" \
  -filter_complex "[1:a]volume=${GAIN}dB,alimiter=limit=0.84:level=false,aresample=48000[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 256k -ar 48000 -movflags +faststart "$OUT"

echo "--- verificación de $OUT"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio,start_time -of compact "$OUT"
ffprobe -v error -select_streams a:0 -show_entries stream=start_time -of compact "$OUT"
ffprobe -v error -show_entries format=duration -of compact "$OUT"
echo "LUFS integrado: $(lufs "$OUT")"
BLACK=$(ffmpeg -hide_banner -i "$OUT" -vf "blackdetect=d=0.05:pic_th=0.98" -an -f null - 2>&1 | grep -c black_start || true)
echo "blackdetect: $BLACK tramos negros"
[ "$BLACK" = "0" ] || { echo "FALLA: hay fotogramas negros"; exit 1; }
for w in 0:3.5 6.4:10 13.2:16.2; do
  a=${w%:*}; b=${w#*:}
  printf "RMS %s–%s s: " "$a" "$b"
  ffmpeg -hide_banner -ss "$a" -to "$b" -i "$OUT" -af volumedetect -vn -f null - 2>&1 | awk '/mean_volume/{print $5, $6}'
done
