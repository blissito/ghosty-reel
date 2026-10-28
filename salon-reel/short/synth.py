#!/usr/bin/env python3
"""
Música y efectos del short del salón (numpy, 48 kHz, determinista). Openverse no respondió (504), así que la
cama se sintetiza como en ghosty-3d-inicia-sesion: pista propia, sin crédito que dar.

  music.wav → noche tranquila: piano eléctrico suave en arpegios + bajo pulsado; 92 BPM, Fa–Lam–Rem–Sib.
              Intro sólo arpegio; entra el bajo con la clienta; bombo y shaker cuando Ghosty se pone a trabajar;
              acorde final que sostiene el CTA.
  sfx.wav   → efectos de la casa (docs/shorts-taller/sfx, CC0) y los de chat originales (_shared/sfx-ghosty-chat),
              cada uno en el cuadro exacto de la escena (escena/score.json).
"""
import json, os, wave
import numpy as np

SR = 48_000
HERE = os.path.dirname(os.path.abspath(__file__))
SC = json.load(open(os.path.join(HERE, "../escena/score.json")))
T, DUR = SC["T"], SC["duration"]
N = int(SR * DUR)
rng = np.random.default_rng(23)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def env(n, a=0.004, d=0.4):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1.0) * np.exp(-t / d)
def put(buf, t, sig, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf) or i < 0: return
    sig = sig[: len(buf) - i] * gain
    if sig.ndim == 1:
        buf[i:i + len(sig), 0] += sig * (1 - max(pan, 0)); buf[i:i + len(sig), 1] += sig * (1 + min(pan, 0))
    else:
        buf[i:i + len(sig)] += sig
def epiano(m, dur=0.9):
    # piano eléctrico: seno + segundo armónico con trémolo lento, ataque suave
    n = int(SR * dur); t = np.arange(n) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.25) + 0.08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / 0.08)
    return s * (1 + 0.08 * np.sin(2 * np.pi * 5 * t)) * env(n, 0.006, 0.45)
def bass(m, dur=0.5):
    n = int(SR * dur); t = np.arange(n) / SR; f = hz(m)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * env(n, 0.005, 0.22)
def kick():
    n = int(SR * 0.3); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(48 + 80 * np.exp(-t / 0.03)) / SR) * env(n, 0.001, 0.11)
def shaker():
    n = int(SR * 0.05); s = np.diff(rng.uniform(-1, 1, n), prepend=0)
    return s * env(n, 0.002, 0.015)
def load(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
        return x.reshape(-1, w.getnchannels()) if w.getnchannels() == 2 else x

# --- música ---
music = np.zeros((N, 2))
BEAT = 60 / 92
CH = [(41, [65, 69, 72, 77]), (45, [64, 69, 72, 76]), (38, [62, 65, 69, 74]), (46, [62, 65, 70, 74])]
bass_in, groove, end = T["phoneIn"], T["ghostyIn"], T["ctaIn"]
b = 0
while b * BEAT < end - 0.05:
    t = b * BEAT; root, notes = CH[(b // 4) % 4]
    for k in range(2):
        put(music, t + k * BEAT / 2, epiano(notes[(b * 2 + k * 3) % 4]), 0.2, pan=-0.35 + 0.7 * k)
    if t >= bass_in - 0.05:
        put(music, t, bass(root), 0.4); put(music, t + BEAT * 0.75, bass(root + 12, 0.25), 0.18)
    if t >= groove - 0.05:
        if b % 2 == 0: put(music, t, kick(), 0.45)
        put(music, t + BEAT / 2, shaker(), 0.1, pan=0.4)
    b += 1
# acorde final: sostiene el CTA hasta el último cuadro
fin = DUR - end
for m in (41, 53, 65, 69, 72, 77):
    s = epiano(m, fin); s *= np.linspace(1, 0.5, len(s)); put(music, end, s, 0.16)
put(music, end, kick(), 0.5)

# --- efectos (sin repetir el mismo dos veces seguidas) ---
FX = os.path.expanduser("~/fixter2025/docs/shorts-taller/sfx"); CHAT = os.path.join(HERE, "../../_shared/sfx-ghosty-chat")
IN_TO, GO_FROM, GO_TO = T["ghostyIn"] + 0.35, T["flip"] - 1.25, T["flip"] - 0.15
CUES = [
    (T["phoneIn"] - 0.1, f"{FX}/whoosh-short.wav", 0.7),   # sube el celular
    (T["msgIn"], f"{CHAT}/llega.wav", 0.9),                # llega el mensaje de Sofía
    (T["ghostyIn"] - 0.35, f"{FX}/whoosh-fly.wav", 0.7),   # Ghosty entra volando
    (IN_TO, f"{FX}/land.wav", 0.6),                        # aterriza en la recepción
    (T["reply"], f"{CHAT}/envia.wav", 0.9),                # contesta
    (T["card1"], f"{FX}/card.wav", 0.8),                   # tarjeta: cita
    (T["card2"], f"{FX}/coin.wav", 0.8),                   # tarjeta: anticipo
    (T["paid"], f"{CHAT}/envia.wav", 0.7),                 # mensaje del anticipo
    (T["card3"], f"{FX}/stamp.wav", 0.8),                  # tarjeta: factura
    (T["thanks"], f"{CHAT}/llega.wav", 0.8),               # «¡Gracias!»
    (GO_FROM, f"{FX}/whoosh-short.wav", 0.7),              # vuela a la puerta
    (GO_TO, f"{FX}/pop.wav", 0.7),                         # llega junto al letrero
    (T["flip"] - 0.05, f"{FX}/turn.wav", 0.6),             # el letrero se voltea
    (T["ctaIn"] - 0.2, f"{FX}/whoosh-fly.wav", 0.6),       # la cámara se aleja al CTA
    (T["url"], f"{CHAT}/listo.wav", 0.8),                  # ghosty.studio
    (T["url"] + 0.4, f"{FX}/pin.wav", 0.8),                # pastilla de la fecha
]
sfx = np.zeros((N, 2))
for t, path, g in CUES: put(sfx, t, load(path), g)

def save(name, buf):
    buf = buf / (np.abs(buf).max() + 1e-9) * 0.8
    with wave.open(os.path.join(HERE, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype("<i2").tobytes())
save("music.wav", music); save("sfx.wav", sfx)
print("ok", DUR, "s")
