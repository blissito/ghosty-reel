#!/usr/bin/env python3
"""
Verifica la sincronía sobre el archivo entregado, con el mismo método que se usó para medir cute.mp4:
1) audio: detecta ataques en 400–4000 Hz y los cuantiza a la rejilla de 120 BPM (dieciseisavos);
   además, cada nota de la partitura debe tener un ataque detectado a ≤ 15 ms.
2) imagen: para cada evento visual de la partitura, el cuadro que empieza en su tiempo debe cambiar
   respecto al anterior (el objeto aparece a ≤ 1 cuadro de su nota).
Uso: python3 verif-sync.py renders/factory-partitura.mp4
"""
import json
import subprocess
import sys

import numpy as np

src = sys.argv[1]
score = json.load(open("score.gen.json"))
SR = 22050

a = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                   capture_output=True, check=True).stdout
x = np.frombuffer(a, np.int16) / 32768
hop, n = 64, 1024
fq = np.fft.rfftfreq(n, 1 / SR)
S = np.array([np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n))) for i in range(0, len(x) - n, hop)])
t = (np.arange(len(S)) * hop + n / 2) / SR
m = (fq >= float(sys.argv[2]) if len(sys.argv) > 2 else fq >= 400) & (fq < 4000)
L = np.log1p(S[:, m] * 20)
fl = np.maximum(np.diff(L, axis=0), 0).sum(1)
thr = np.convolve(fl, np.ones(101) / 101, "same") * 1.8 + np.median(fl)
on = [t[i + 1] for i in range(1, len(fl) - 1) if fl[i] > thr[i] and fl[i] >= fl[i - 1] and fl[i] >= fl[i + 1]]
o = []
[o.append(v) for v in on if not o or v - o[-1] > 0.06]
o = np.array(o)
err = np.abs(((o + 0.0625) % 0.125) - 0.0625)
print(f"audio: {len(o)} ataques; a ≤15 ms de la rejilla 1/16: {np.mean(err <= 0.015):.0%} (error medio {err.mean()*1000:.1f} ms)")

tonal = [e for e in score["events"] if e["inst"] in ("bell", "marimba", "pluck") and e["t"] < score["duration"] - 0.1]


def band_energy(t0, f0, win=0.03):
    """energía en ±4 % de la fundamental de la nota, en una ventana de 30 ms que empieza en t0"""
    a, b = int(t0 * SR), int((t0 + win) * SR)
    seg = x[a:b] * np.hanning(b - a)
    sp = np.abs(np.fft.rfft(seg, 8192))
    ff = np.fft.rfftfreq(8192, 1 / SR)
    return sp[(ff > f0 * 0.96) & (ff < f0 * 1.04)].max() + 1e-9


# la nota debe crecer justo en su tiempo: ventana [t, t+30ms] contra [t-35ms, t-5ms]
bad_a = []
for e in tonal:
    f0 = 440 * 2 ** ((e["note"] - 69) / 12)
    ratio = band_energy(e["t"], f0) / band_energy(e["t"] - 0.035, f0)
    if ratio < 1.5:
        bad_a.append((e["t"], e["id"], round(float(ratio), 2)))
print(f"notas de la partitura que arrancan en su tiempo (±30 ms, a su frecuencia): {len(tonal)-len(bad_a)}/{len(tonal)}")
for b in bad_a[:10]:
    print("   sin arranque:", b)

W, H = 270, 480
v = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                   capture_output=True, check=True).stdout
fr = np.frombuffer(v, np.uint8).reshape(-1, H, W).astype(np.int16)
vis = [e for e in score["events"] if e["id"] and not e["id"].startswith("wipe")]
bad = []
for e in vis:
    f = int(np.ceil(e["t"] * 30 - 1e-6))
    if f <= 0 or f >= len(fr):
        continue
    ch = (np.abs(fr[f] - fr[f - 1]) > 12).sum()
    if ch < 20:
        bad.append((e["t"], e["id"], int(ch)))
print(f"imagen: eventos visuales que cambian en su cuadro: {len(vis)-len(bad)}/{len(vis)}")
for b in bad[:15]:
    print("   sin cambio:", b)
