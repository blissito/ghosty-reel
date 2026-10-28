#!/usr/bin/env bash
# Pista de voz: cada frase em_santa en su tiempo (tools/score.py → START), 16.2 s.
set -euo pipefail
cd "$(dirname "$0")"
V=../voice; DUR=16.2
ffmpeg -v error -y -i $V/01-cerro.wav -i $V/02-escribe.wav -i $V/03-ghosty.wav -i $V/04-sigue.wav -i $V/05-cta.wav -filter_complex "\
[0]aresample=48000,adelay=300:all=1,apad=whole_dur=${DUR}[a];[1]aresample=48000,adelay=3750:all=1,apad=whole_dur=${DUR}[b];\
[2]aresample=48000,adelay=6450:all=1,apad=whole_dur=${DUR}[c];[3]aresample=48000,adelay=10200:all=1,apad=whole_dur=${DUR}[d];\
[4]aresample=48000,adelay=13400:all=1,apad=whole_dur=${DUR}[e];[a][b][c][d][e]amix=inputs=5:normalize=0:duration=longest" -t "$DUR" voz.wav
