# Voz de la casa: em_santa (Kokoro) en es-419 con el léxico de la casa (réplica de apply_lexicon() de
# ~/sandbox-host/templates/kokoro-svc/server.py), speed 1.0. Una frase por archivo.
import json, re, sys
import soundfile as sf
from kokoro_onnx import Kokoro
C = "/Users/bliss/.cache/hyperframes/tts"
LEXF = "/Users/bliss/sandbox-host/templates/kokoro-svc/lexicon.es.json"
raw = json.load(open(LEXF, encoding="utf8"))
LEX = {k.lower(): v for k, v in raw.items() if not k.startswith("_") and v}
RE = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(k) for k in sorted(LEX, key=len, reverse=True)) + r")(?!\w)", re.IGNORECASE)
lex = lambda t: RE.sub(lambda m: LEX[m.group(0).lower()], t)
LINES = json.load(open("voice/script.json", encoding="utf8"))
k = Kokoro(f"{C}/models/kokoro-v1.0.onnx", f"{C}/voices/voices-v1.0.bin")
for l in LINES:
    if len(sys.argv) > 1 and l["id"] not in sys.argv[1:]: continue
    said = lex(l["text"])
    s, sr = k.create(said, voice="em_santa", speed=1.0, lang="es-419")
    sf.write(f"voice/{l['id']}.wav", s, sr)
    print(l["id"], round(len(s) / sr, 2), "s ·", said)
