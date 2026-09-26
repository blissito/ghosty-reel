# Arma voice/lines.json: tiempos de palabra medidos (whisper large-v3 sobre cada clip) + el texto que va en pantalla.
# Sólo se corrigen errores de oído («Kosti» → «Ghosty», «Messeñer» → «Messenger», «que» → «qué»), y las
# palabras que whisper pega («Ysi», «Ya», «Yte») o resume («31» → «treinta y uno») se reparten en partes iguales.
import json, subprocess
LINES = [
  ("hookA", "Pagas un anuncio y te escriben treinta y siete."),
  ("hookB", "¿Cuántos de verdad compran?"),
  ("contesta", "Ghosty le contesta a cada uno al instante, en Messenger, de día y de noche."),
  ("califica", "Le pregunta lo que falta, le cotiza en PDF, le agenda la cita y te lo deja en tu tablero."),
  ("filtroA", "A los curiosos los despide con amabilidad y deja de gastar en ellos."),
  ("filtroB", "Y si el correo o el teléfono es falso, te lo marca."),
  ("reporteA", "Y a las nueve de la mañana y a las nueve de la noche te manda el reporte:"),
  ("reporteB", "quién escribió, qué busca y qué sigue."),
  ("cierre", "Tú sólo hablas con los que sí compran."),
  ("ctaA", "Escríbenos por Messenger,"),
  ("ctaB", "y te armamos tu tablero gratis, con tu marca."),
  ("ctaC", "Hasta el treinta y uno de octubre."),
]
SPLIT = {"Ysi": 2, "Ya": 2, "Yte": 2, "31": 3}
out = []
for scene, text in LINES:
    shown = text.split()
    ws = json.load(open(f"voice/tr-{scene}/transcript.json"))
    split = []
    for w in ws:
        n = SPLIT.get(w["text"], 1)
        if n > 1 and len(ws) != len(shown):
            d = (w["end"] - w["start"]) / n
            split += [{"start": round(w["start"] + i * d, 3), "end": round(w["start"] + (i + 1) * d, 3)} for i in range(n)]
        else: split.append(w)
    assert len(split) == len(shown), (scene, [w.get("text") for w in ws], shown)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"voice/{scene}.wav"], capture_output=True, text=True).stdout)
    out.append({"scene": scene, "file": f"voice/{scene}.wav", "dur": round(dur, 3), "heard": " ".join(w["text"] for w in ws),
                "words": [{"w": s, "s": w["start"], "e": w["end"]} for s, w in zip(shown, split)]})
json.dump(out, open("voice/lines.json", "w"), ensure_ascii=False, indent=1)
print("ok", [(l["scene"], l["dur"], l["words"][-1]["e"]) for l in out])
