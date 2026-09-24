// Partitura: la única fuente de verdad del short. De aquí salen la timeline visual
// (score.gen.js, la lee index.html) y las notas del sintetizador (score.gen.json, la lee synth.py).
// Reloj: 120 BPM → 1 dieciseisavo = 0.125 s. Cada escena mide un número entero de dieciseisavos
// y termina con una pausa ya completa antes de la cortinilla, para que se aprecie.
import { writeFileSync } from "node:fs";

export const BPM = 120;
export const S16 = 0.125;

// escenas en orden: duración en dieciseisavos, piel y glifo de la cortinilla que la abre
const SCENES = [
  { id: "s0", len: 24, skin: "thread" },
  { id: "s1", len: 40, skin: "box", glyph: "@plan", color: "#edc75a" },
  { id: "s2", len: 24, skin: "thread", glyph: "✋", color: "#f2f5f9" },
  { id: "s3", len: 56, skin: "box", glyph: "@build", color: "#7fbe60" },
  { id: "s4", len: 40, skin: "box", glyph: "@check", color: "#e4ae8e" },
  { id: "s5", len: 40, skin: "thread", glyph: "ghosty", color: "#8ad7c9" },
  { id: "s6", len: 24, skin: "thread", glyph: "7 min", color: "#edc75a" },
  { id: "s7", len: 48, skin: "thread", glyph: "ghosty", color: "#8ad7c9" },
];
let acc = 0;
const START = {};
SCENES.forEach((s) => { s.t = +(acc * S16).toFixed(4); START[s.id] = acc; acc += s.len; });
export const DURATION = acc * S16; // 37 s

// tiempo absoluto: escena + dieciseisavos + tresillos de dieciseisavo (1/12 s)
const at = (sc, s16 = 0, tri = 0) => +((START[sc] + s16) * S16 + tri / 12).toFixed(4);

// MIDI: Do mayor pentatónica para las notas de eventos
const PENTA = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 86, 88, 91];

const events = [];
// id = acción visual (null = sólo sonido); inst = instrumento (null = sólo imagen)
const ev = (t, id, inst = null, note = null, dur = 0.25, vel = 0.8) =>
  events.push({ t, id, inst, note, dur, vel });

// ---- s0: hilo #fabrica, se teclea @plan (clic por letra en tresillos) ----
"@plan".split("").forEach((_, i) => ev(at("s0", 4, i), `type:${i}`, "click", 84 + i, 0.05, 0.5));
ev(at("s0", 8), "send", "bell", 76, 0.6);
ev(at("s0", 10), "planAck", "bell", 79, 0.6, 0.6);

// ---- s1: @plan lee el repo (un archivo por dieciseisavo) y escribe el plan ----
for (let i = 0; i < 12; i++) ev(at("s1", 4 + i), `file:${i}`, "bell", PENTA[(i * 2) % 9], 0.35, 0.55 + (i % 4 === 0 ? 0.2 : 0));
[0, 1, 2].forEach((i) => ev(at("s1", 20 + i * 4), `planRow:${i}`, "bell", PENTA[4 + i * 2], 0.9, 0.9));

// ---- s2: silencio humano; firmas el plan ----
ev(at("s2", 8), "approve", "stamp", null, 0.6, 1);

// ---- s3: @build en su propia computadora ----
for (let i = 0; i < 4; i++) ev(at("s3", 4 + i * 2), `commit:${i}`, "marimba", PENTA[i], 0.4, 0.8);
for (let i = 0; i < 10; i++) ev(at("s3", 14 + i * 2), `test:${i}`, "marimba", PENTA[i % 5], 0.3, 0.6);
for (let i = 0; i < 10; i++) ev(at("s3", 32 + i), `pass:${i}`, "marimba", PENTA[i + 2], 0.35, 0.85);
ev(at("s3", 44), "draftPR", "bell", 84, 0.8, 0.8);

// ---- s4: @check revisa contra el plan, nunca edita ----
for (let i = 0; i < 3; i++) ev(at("s4", 4 + i * 4), `tick:${i}`, "pluck", PENTA[5 + i], 0.5, 0.9);
for (let i = 0; i < 4; i++) ev(at("s4", 16 + i * 2), `ci:${i}`, "kick", null, 0.4, 0.9);
for (let i = 0; i < 4; i++) ev(at("s4", 16 + i * 2), null, "pluck", PENTA[3 + i], 0.4, 0.6);
ev(at("s4", 26), "zeroLoops", "stamp", null, 0.6, 0.9);

// ---- s5: Ghosty publica el veredicto; silencio humano; Mezclar → confeti ----
["rowChanges", "rowCI", "rowReview"].forEach((k, i) => ev(at("s5", 4 + i * 2), k, "bell", PENTA[5 + i * 2], 0.6, 0.7));
ev(at("s5", 12), "buttons", "bell", 88, 0.8, 0.8);
ev(at("s5", 24), "tapMerge", "click", 72, 0.06, 0.9);
ev(at("s5", 28), "merged", "confetti", null, 1.2, 1);

// ---- s6: el dato real, cuenta 1→7 ----
for (let i = 1; i <= 7; i++) ev(at("s6", 2 + i), `count:${i}`, "bell", PENTA[i + 3], 0.4, 0.7);

// ---- s7: CTA con la voz (em_santa). «Pide» cae en el dieciseisavo 4; «factory» 1.30 s después ----
ev(at("s7", 4), "ctaVerb", "bell", 79, 1.2, 0.5);
ev(at("s7", 15), "ctaUrl", "bell", 84, 1.6, 0.55);
ev(at("s7", 34), "ctaSmall", "bell", 88, 1.8, 0.5);
export const VOICE_START = +(at("s7", 4) - 0.05).toFixed(4); // el ataque de «Pide» está a 0.05 s del inicio del wav

// ---- cama: acordes por escena ([dieciseisavo, notas]); los silencios son las firmas humanas ----
const C = [48, 55, 64], Am = [45, 52, 60], F = [41, 48, 57], G = [43, 50, 59], Em = [40, 47, 55];
const CHORDS = {
  s0: [[0, C], [16, Am]],
  s1: [[0, F], [16, Am], [32, G]],
  s2: [[8, C]], // silencio hasta que firmas
  s3: [[0, C], [16, Am], [32, F], [48, G]],
  s4: [[0, Em], [16, F], [32, G]],
  s5: [[0, F], [8, G], [16, null], [28, [48, 55, 64, 72]]], // silencio hasta Mezclar
  s6: [[0, C], [16, G]],
  s7: [[0, F], [16, C]],
};
const SILENT = { s2: [0, 8], s5: [16, 28] };
const pads = [];
SCENES.forEach((s) => {
  const list = CHORDS[s.id];
  list.forEach(([st, notes], k) => {
    if (!notes) return;
    const end = k + 1 < list.length ? list[k + 1][0] : s.len;
    pads.push({ t: at(s.id, st), notes, dur: +((end - st) * S16).toFixed(4) });
  });
  // bombo cada medio compás (menos en silencios y en el CTA con voz); hats dentro de la caja
  if (s.id !== "s7")
    for (let k = 0; k < s.len; k += 8) {
      const sil = SILENT[s.id];
      if (sil && k >= sil[0] && k < sil[1]) continue;
      ev(at(s.id, k), null, "kick", null, 0.4, k % 16 === 0 ? 0.9 : 0.7);
    }
  if (s.skin === "box") for (let k = 1; k < s.len; k += 2) ev(at(s.id, k), null, "hat", null, 0.05, 0.35);
});

// cortinillas: barrido de ruido que sube mientras cierra; el corte cae en el inicio de la escena
const cuts = SCENES.filter((s) => s.glyph).map((s) => ({ t: s.t, glyph: s.glyph, color: s.color }));
cuts.forEach((c) => ev(+(c.t - 0.3).toFixed(4), `wipe:${c.t}`, "sweep", null, 0.3, 0.7));

events.sort((a, b) => a.t - b.t);
const score = {
  bpm: BPM, duration: DURATION, voiceStart: VOICE_START,
  scenes: SCENES.map(({ id, t, skin, len }) => ({ id, t, skin, len })), cuts, events, pads,
};
writeFileSync(new URL("./score.gen.json", import.meta.url), JSON.stringify(score, null, 1));
writeFileSync(new URL("./score.gen.js", import.meta.url), `// generado por score.mjs — no editar\nwindow.SCORE = ${JSON.stringify(score)};\n`);
console.log(`${DURATION} s, ${events.length} eventos, ${pads.length} acordes, ${cuts.length} cortinillas, voz en ${VOICE_START} s`);
