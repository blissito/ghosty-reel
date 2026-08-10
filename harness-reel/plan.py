#!/usr/bin/env python3
"""
Genera audio/plan.json a partir de scene.json.

Los efectos NO llevan segundos escritos a mano: se derivan del beat visual al
que responden. Mueve un beat en scene.json, corre esto, y el sonido se mueve con
él. En un pipeline donde el render tarda, un desfase por retimeo manual se
descubre demasiado tarde.

Uso:  python3 plan.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
scene = json.load(open(os.path.join(ROOT, "scene.json")))
B = scene["beats"]
VO = scene["vo"]
DUR = B["end"]


def at(beat, off=0.0):
    """Segundo de un beat visual, con ajuste opcional."""
    return round(B[beat] + off, 2)


# (segundo, archivo, ganancia, alineación, a qué momento visual responde)
#   onset -> golpes secos     peak -> swells que culminan en el corte
SFX = [
    (at("hook", 0.05),      "click-soft.mp3",       0.30, "onset", "aparece 'medio millón'"),
    (at("hook", 1.30),      "impact-bass-1.mp3",    0.38, "onset", "el giro: 'ninguna es el modelo'"),
    (at("hook_out", -0.15), "whoosh-cinematic.mp3", 0.30, "peak",  "el texto sale, entra el diagrama"),

    (at("nucleo", 0.05),    "pop.mp3",              0.30, "onset", "nace el núcleo"),
    (at("tools", 0.05),     "click.mp3",            0.26, "onset", "se traza tools"),
    (at("skills", 0.05),    "click.mp3",            0.26, "onset", "se traza skills"),
    (at("mcp", 0.05),       "click.mp3",            0.26, "onset", "se traza mcp"),
    (at("subs", 0.05),      "click.mp3",            0.26, "onset", "se traza subagentes"),

    (at("harness", 0.10),   "chime.mp3",            0.24, "onset", "se cierra el loop: 'el harness'"),
    (at("cta", -0.30),      "riser.mp3",            0.26, "peak",  "entrada del CTA"),
    (at("cta", 0.10),       "sparkle.mp3",          0.20, "onset", "aparece el taller"),
]

plan = {
    "_comment": "GENERADO por plan.py desde scene.json — no editar a mano. "
                "'at' = instante en que el sonido DEBE oírse; mix.sh compensa el "
                "silencio inicial de cada archivo (ver AUDIO.md).",
    "sfx_dir": "../audio/sfx",
    "lead_ms": 60,
    "duration": DUR,
    "voice": [{"at": v["at"], "file": f"vo/{v['file']}", "gain": 1.0, "text": v["text"]}
              for v in VO],
    "sfx": [{"at": t, "file": f, "gain": g, "align": a, "cue": c}
            for t, f, g, a, c in SFX],
    "bgm": {"file": "bgm.wav", "gain": 0.13, "fade_out_at": round(DUR - 1.4, 2)},
}

with open(os.path.join(ROOT, "audio/plan.json"), "w") as fh:
    json.dump(plan, fh, indent=2, ensure_ascii=False)

print(f"  audio/plan.json  {DUR}s · {len(plan['voice'])} voces · {len(SFX)} efectos")
