#!/usr/bin/env bash
# Voz del CTA con em_santa (Kokoro, local). Anglicismos escritos como se pronuncian.
# Después medir con: npx hyperframes transcribe voice/cta.wav -m large-v3 -l es --json
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p voice
npx hyperframes@0.8.44 tts -v em_santa -l es -o voice/cta.wav "Pide tu primer pi ar en fáctori, punto gósti, punto estudio."
