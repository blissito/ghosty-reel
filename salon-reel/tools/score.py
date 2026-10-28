# Arma assets/score.js: dónde entra cada frase de voz (t0) y los tiempos absolutos de cada palabra (para karaoke,
# destacados y SFX). Los momentos de la animación (T) salen de las palabras: cada cosa se enciende cuando la voz la nombra.
import json
START = {"01-cerro": 0.3, "02-escribe": 3.75, "03-ghosty": 6.45, "04-sigue": 10.2, "05-cta": 13.4}
DUR = 16.2
L = json.load(open("voice/words.json"))
lines = []
for l in L:
    t0 = START[l["id"]]
    lines.append({"id": l["id"], "t0": t0, "words": [{"w": w["w"], "s": round(t0 + w["s"], 3), "e": round(t0 + w["e"], 3)} for w in l["words"]]})
W = {l["id"]: {w["w"].strip(".,").lower(): w["s"] for w in l["words"]} for l in lines}
T = {
  "phoneIn": 3.55, "msgIn": W["02-escribe"]["escribe"], "ghostyIn": W["03-ghosty"]["ghosty"],
  "reply": W["03-ghosty"]["ghosty"] + 0.45, "card1": W["03-ghosty"]["cita"], "card2": W["03-ghosty"]["anticipo"],
  "paid": W["03-ghosty"]["anticipo"] + 0.15, "card3": W["03-ghosty"]["factura"], "thanks": START["04-sigue"] + 0.2,
  "flip": W["04-sigue"]["sigue"], "ctaIn": START["05-cta"] - 0.15, "url": W["05-cta"]["ghosty.studio"],
}
json.dump({"duration": DUR, "lines": lines, "T": T, "start": START}, open("assets/score.json", "w"), ensure_ascii=False, indent=1)
open("assets/score.js", "w").write("window.SCORE = " + json.dumps({"duration": DUR, "lines": lines, "T": T}, ensure_ascii=False) + ";\n")
print(json.dumps(T, indent=1))
