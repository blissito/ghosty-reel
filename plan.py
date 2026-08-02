#!/usr/bin/env python3
"""
Genera audio/plan.json a partir de los beats de scene.json.

La gracia: los efectos NO llevan tiempos escritos a mano, se derivan del beat
visual al que responden. Mover `button_pop` en scene.json y volver a correr esto
mueve el impacto con él. Escribir los segundos a mano garantiza que imagen y
audio se separen en cuanto se retoca la edición.

Uso:  python3 plan.py
"""

import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
scene = json.load(open(os.path.join(ROOT, "scene.json")))

FPS = scene["fps"]
DUR = scene["duration_frames"] / FPS
B = scene["beats"]


def at(beat, offset=0):
    """Segundo en que cae un beat visual (+/- un ajuste en frames)."""
    return round((B[beat][0] + offset) / FPS, 2)


def end(beat, offset=0):
    return round((B[beat][1] + offset) / FPS, 2)


VOICE = [
    (0.60,  "vo1", "Tus agentes generan archivos."),
    (2.40,  "vo2", "¿Dónde los guardas?"),
    (7.30,  "vo3", "Un clic, y todo queda en su lugar."),
    (13.60, "vo5", "Tus agentes suben, buscan y comparten."),
    (19.20, "vo6", "Un solo almacén para toda tu flota."),
    (25.00, "vo7", "Comparte con un link."),
    (29.30, "vo4", "EasyBits. Almacenamiento para agentes."),
]

# (segundo, archivo, ganancia, alineación, a qué momento visual responde)
#   onset -> golpes    peak -> swells que culminan en el corte
SFX = [
    (end("titles", -18),   "whoosh-cinematic.mp3", 0.34, "peak",  "los títulos atraviesan la cámara"),
    (at("click"),          "click.mp3",            0.46, "onset", "el cursor hace clic"),
    (at("button_pop", 3),  "impact-bass-1.mp3",    0.40, "onset", "el botón se despega"),
    (at("burst", 4),       "sparkle.mp3",          0.24, "onset", "salen los archivos"),
    (end("settle", -30),   "chime.mp3",            0.20, "onset", "los archivos se ordenan"),

    (at("clear", 8),       "whoosh.mp3",           0.26, "peak",  "transición al agente"),
    (at("agent", 44),      "ping.mp3",             0.22, "onset", "upload_file()"),
    (at("agent", 64),      "ping.mp3",             0.22, "onset", "search_documents()"),
    (at("agent", 84),      "ping.mp3",             0.22, "onset", "create_share_link()"),

    (at("fleet", -6),      "whoosh.mp3",           0.26, "peak",  "transición a la flota"),
    (at("fleet", 118),     "chime.mp3",            0.20, "onset", "los archivos convergen"),

    (at("share", -6),      "whoosh.mp3",           0.26, "peak",  "transición a compartir"),
    (at("share", 50),      "sparkle.mp3",          0.24, "onset", "el link se replica"),

    (at("end_in", 8),      "riser.mp3",            0.26, "peak",  "entrada de la marca"),
]

plan = {
    "_comment": "GENERADO por plan.py desde scene.json — no editar a mano. "
                "'at' = instante en que el sonido DEBE oírse; mix.sh compensa el "
                "silencio inicial de cada archivo (ver AUDIO.md).",
    "sfx_dir": "audio/sfx",
    "lead_ms": 60,
    "duration": DUR,
    "voice": [{"at": t, "file": f"vo/{f}.wav", "gain": 1.0, "text": txt}
              for t, f, txt in VOICE],
    "sfx": [{"at": t, "file": f, "gain": g, "align": a, "cue": c}
            for t, f, g, a, c in SFX],
    "bgm": {"file": "bgm.wav", "gain": 0.14, "fade_out_at": round(DUR - 1.4, 2)},
}

with open(os.path.join(ROOT, "audio/plan.json"), "w") as fh:
    json.dump(plan, fh, indent=2, ensure_ascii=False)

print(f"  audio/plan.json  {DUR}s · {len(VOICE)} voces · {len(SFX)} efectos")
