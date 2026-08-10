#!/usr/bin/env python3
"""
Bed musical sintetizado desde cero — sin modelos, sin catálogo, sin licencia.

Por qué no un generador de música: los modelos abiertos (MusicGen, Stable Audio)
traen pesos con licencia no comercial o restringida, que es justo lo que rompe la
premisa de un pipeline 100% libre. Un bed de anuncio no necesita un modelo: es
una progresión corta con sub, arpegio y pad. Sintetizarlo es determinista, pesa
nada, corre en cualquier microVM sin GPU y el resultado es nuestro.

La estructura sigue los actos del anuncio (ver scene.json -> beats), no un loop
genérico: entra sobrio en el problema, abre al aparecer el producto, sube en el
clic y resuelve en la marca.

Uso:  python3 music.py [salida.wav]
"""

import json
import math
import os
import sys
import wave

import numpy as np

SR = 48_000
# La duración sale de scene.json: si la edición crece, la música crece con ella.
# Tenerla escrita aquí garantiza que se desincronicen en el primer retoque.
_scene = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "scene.json")))
DUR = _scene["duration_frames"] / _scene["fps"]
BPM = 120.0
BEAT = 60.0 / BPM

N = int(SR * DUR)
T = np.arange(N) / SR

# La menor: sobrio sin ser triste, y el acorde final (Am -> F -> C -> G) resuelve
# sin sonar a jingle.
A2, C3, E3, F3, G3, A3, C4, E4, G4, A4 = (
    110.00, 130.81, 164.81, 174.61, 196.00, 220.00, 261.63, 329.63, 392.00, 440.00)
CYCLE = [  # (raíz del bajo, notas del pad) — 4 tiempos cada uno
    (A2, (A3, C4, E4)),
    (F3, (A3, C4, F3 * 2)),
    (C3, (C4, E4, G4)),
    (G3, (G3 * 2, C4, E4)),
]
# El ciclo se repite hasta cubrir la duración: la progresión es la misma, lo que
# cambia entre secciones es la instrumentación (arpegio, ticks, swell).
PROG = [(i * 4, *CYCLE[i % 4])
        for i in range(math.ceil(DUR / BEAT / 4))]


# El groove entra en t=0: en vertical, una intro que tarda en llegar al ritmo
# mata el gancho — y el gancho son los primeros 3 segundos.
ARP_IN, ARP_OUT, TICK_IN = 0.0, DUR - 2.2, 2.0

# Instantes en que habla la voz: el bed se agacha desde la SÍNTESIS, así el
# loudnorm de la mezcla no tiene que pelear. Sale de audio/plan.py.
DUCKS = [(v["at"] - 0.15, v["dur"] + 0.3) for v in _scene["vo"]]


def env(start, dur, attack, release):
    """Envolvente trapezoidal en segundos de la línea de tiempo global."""
    e = np.zeros(N)
    a, b = int(start * SR), int((start + dur) * SR)
    b = min(b, N)
    if b <= a:
        return e
    seg = b - a
    at, rl = int(attack * SR), int(release * SR)
    at, rl = min(at, seg // 2), min(rl, seg // 2)
    ramp = np.ones(seg)
    if at:
        ramp[:at] = np.linspace(0, 1, at)
    if rl:
        ramp[-rl:] = np.linspace(1, 0, rl)
    e[a:b] = ramp
    return e


def sine(freq, phase=0.0):
    return np.sin(2 * np.pi * freq * T + phase)


def saw(freq, harmonics=8):
    """Diente de sierra por suma de armónicos: sin aliasing, a diferencia de
    generar la rampa directamente."""
    out = np.zeros(N)
    for k in range(1, harmonics + 1):
        out += np.sin(2 * np.pi * freq * k * T) / k
    return out * (2 / np.pi)


def lowpass(x, cutoff):
    """Un polo. Basta para quitar filo; no buscamos un filtro de síntesis."""
    a = math.exp(-2 * math.pi * cutoff / SR)
    out = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        out[i] = acc
    return out


def bed():
    mix = np.zeros(N)

    # --- sub: marca el pulso, entra desde el primer compás -------------------
    for bar, root, _ in PROG:
        for b in range(8):                      # corcheas del compás
            t0 = (bar + b / 2) * BEAT
            if t0 >= DUR:
                break
            amp = 0.55 if b % 2 == 0 else 0.22
            mix += sine(root) * env(t0, 0.26, 0.004, 0.20) * amp

    # --- pad: el colchón armónico, suave y siempre presente ------------------
    pad = np.zeros(N)
    for bar, _, notes in PROG:
        t0, t1 = bar * BEAT, (bar + 4) * BEAT
        e = env(t0, t1 - t0, 0.35, 0.5)
        for f in notes:
            # dos osciladores desafinados por nota: sin ese batido el pad suena
            # a sintetizador de juguete
            pad += (sine(f) + sine(f * 1.004)) * e * 0.5
    mix += lowpass(pad, 2200) * 0.11

    # --- arpegio: entra cuando aparece la UI (~3.2s) --------------------------
    arp_notes = [A3, C4, E4, C4, A3, E4, G4, E4]
    arp = np.zeros(N)
    step = BEAT / 2
    k = 0
    t0 = ARP_IN
    while t0 < ARP_OUT:
        f = arp_notes[k % len(arp_notes)]
        arp += saw(f, 6) * env(t0, step * 0.85, 0.005, step * 0.6)
        t0 += step
        k += 1
    # el arpegio abre el filtro conforme avanza el anuncio: energía creciente
    # sin subir volumen
    mix += lowpass(arp, 1400) * 0.07 * np.clip((T - ARP_IN) / 6.0, 0, 1)

    # --- ticks: aire en la parte alta, entran con el producto ----------------
    rng = np.random.default_rng(3)
    noise = rng.standard_normal(N)
    ticks = np.zeros(N)
    t0 = TICK_IN
    while t0 < ARP_OUT:
        ticks += noise * env(t0, 0.035, 0.001, 0.03)
        t0 += BEAT / 2
    mix += (ticks - lowpass(ticks, 3000)) * 0.05

    # --- swell hacia la marca ------------------------------------------------
    swell = (sine(A3) + sine(E4) + sine(A4)) * env(DUR - 3.4, 2.4, 1.7, 0.5)
    mix += lowpass(swell, 3000) * 0.05

    # --- acorde final: sostiene bajo el logo ---------------------------------
    for f in (A2, A3, C4, E4):
        mix += sine(f) * env(DUR - 2.6, 2.6, 0.25, 1.4) * 0.10

    # Respiración: baja mientras hablan las dos primeras líneas para que el
    # ducking del mix final no tenga que trabajar de más.
    duck = np.ones(N)
    for start, dur in DUCKS:
        duck -= env(start, dur, 0.25, 0.5) * 0.52
    duck = np.clip(duck, 0.25, 1.0)
    mix *= duck

    mix *= env(0.0, DUR, 0.15, 1.2)              # fade global
    peak = np.abs(mix).max()
    if peak:
        mix *= 0.82 / peak
    return mix


def write(path, mono):
    stereo = np.stack([mono, np.roll(mono, 90)], axis=1)   # ancho sutil
    data = np.clip(stereo, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"  {path}  {DUR:.1f}s  {BPM:.0f} BPM  Am-F-C-G")


if __name__ == "__main__":
    write(sys.argv[1] if len(sys.argv) > 1 else "audio/bgm.wav", bed())
