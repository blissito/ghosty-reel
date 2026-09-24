// Partitura de «Un pedido cruza la fábrica» con narración (vertical 1080×1920, estilo oficial de ghosty.studio).
// La voz manda: cada escena mide lo que dura su frase + un respiro, y cada efecto se ancla a la palabra que lo nombra
// (tiempos de palabra medidos con `hyperframes transcribe -m large-v3 -l es`, en voice/lines.json).
// Todo se cuantiza a dieciseisavos de 120 BPM (0.125 s) para que música y efectos caigan en la rejilla.
import { readFileSync, writeFileSync } from "node:fs";

const S16 = 0.125;
const q = (x) => +(Math.round(x / S16) * S16).toFixed(4);          // al dieciseisavo más cercano
const qUp = (x) => +(Math.ceil(x / S16 - 1e-9) * S16).toFixed(4);  // hacia arriba
const LINES = JSON.parse(readFileSync(new URL("./voice/lines.json", import.meta.url)));
const L = Object.fromEntries(LINES.map((l) => [l.scene, l]));
const VO = { tablero: 0.35, listo: 1.75 }; // en «listo» la voz espera a que el contador llegue a 7           // la voz entra 0.5 s después del corte (la cortinilla ya salió); en la primera, casi de inmediato
const TAIL = { tablero: 0.9, plan: 1.2, firma: 1.4, aBuild: 0.9, sandbox: 1.3, check: 1.4, aPR: 0.9, veredicto: 2.7, listo: 1.2, cta: 2.2 };
const ORDER = ["tablero", "plan", "firma", "aBuild", "sandbox", "check", "aPR", "veredicto", "listo", "cta"];
const GLYPH = { plan: "plan", firma: "firma", aBuild: "tablero", sandbox: "build", check: "check", aPR: "tablero", veredicto: "ghosty", listo: "tablero", cta: "ghosty" };
const STAGE = { tablero: 0, plan: 0, firma: 1, aBuild: 2, sandbox: 2, check: 3, aPR: 4, veredicto: 4, listo: 5, cta: 5 };

let t0 = 0; const SCENES = [];
for (const id of ORDER) {
  const vo = VO[id] ?? 0.5, dur = L[id].dur;
  const len = qUp(vo + dur + TAIL[id]);
  SCENES.push({ id, t0, t1: +(t0 + len).toFixed(4), voice: +(t0 + vo).toFixed(4), glyph: GLYPH[id], stage: STAGE[id] });
  t0 = +(t0 + len).toFixed(4);
}
const DURATION = t0;
const SC = Object.fromEntries(SCENES.map((s) => [s.id, s]));
// tiempo absoluto de una palabra de la frase de la escena (por índice o por inicio de texto), inicio o fin
const W = (scene, which, edge = "s") => {
  const ws = L[scene].words;
  const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");
  const w = typeof which === "number" ? ws[which] : ws.find((x) => norm(x.w).startsWith(norm(which)));
  if (!w) throw new Error(`palabra «${which}» no está en ${scene}`);
  return SC[scene].voice + (edge === "s" ? w.s : w.e);
};

// ---- momentos visuales, anclados a la voz ----
const lerp = (a, b, p) => a + (b - a) * p;
const T = {
  cardGlow: q(W("tablero", "pedido")),
  files: [...Array(8)].map((_, i) => q(lerp(W("plan", "lee"), W("plan", "nada", "e"), i / 7))),
  planRows: [q(W("plan", "historia")), q(W("plan", "brief")), q(W("plan", "riesgos"))],
  planDone: q(W("plan", "riesgos", "e") + 0.15),
  handIn: q(SC.firma.voice + 0.2), approve: q(W("firma", "apruebas", "e") + 0.1), stamp: q(W("firma", "apruebas", "e") + 0.85),
  hopBuild: q(W("aBuild", "pasa")),
  boxClose: q(W("sandbox", "trabaja")),
  term: [q(W("sandbox", "abre")), q(W("sandbox", "rama")), q(W("sandbox", "escribe")), q(W("sandbox", "10")), q(W("sandbox", "corre")), q(W("sandbox", "pasan")), q(W("sandbox", "pasan", "e") + 0.4)],
  gearsOn: q(W("sandbox", "corre")), gearsOff: q(W("sandbox", "pasan")),
  tests: q(W("sandbox", "pasan")), pill: q(W("sandbox", "pasan")),
  ticks: [q(W("check", "trabajo")), q(W("check", "contra")), q(W("check", "plan"))],
  ci: [q(W("check", "esta")), q(W("check", "vez")), q(W("check", "aprobo") - 0.12), q(W("check", "aprobo"))],
  zero: q(W("check", "primera")),
  hopPR: q(W("aPR", "listo")),
  vrows: [q(W("veredicto", "dif")), q(W("veredicto", "pruebas")), q(W("veredicto", "ci"))],
  vbtns: q(W("veredicto", "verde", "e")), preview: q(W("veredicto", "preview")),
  handIn2: q(W("veredicto", "segunda")), merge: q(W("veredicto", "tuya", "e") + 0.15),
  hopListo: q(SC.listo.t0 + 0.25),
  ctaVerb: q(W("cta", "pide")), ctaUrl: q(W("cta", "factory")), ctaSmall: q(SC.cta.voice + L.cta.dur + 0.3),
};
T.merged = +(T.merge + 0.25).toFixed(4);
// el conteo llega a 7 justo cuando la voz dice «siete»
const siete = q(W("listo", 0));
T.count = [...Array(7)].map((_, i) => +(siete - (6 - i) * S16).toFixed(4));
if (T.count[0] < T.hopListo + 0.7) { const d = T.hopListo + 0.7 - T.count[0]; T.count = T.count.map((x) => +(x + d).toFixed(4)); }

// ---- efectos (pista sfx, no se agacha con la voz): uno por momento, el sonido de lo que pasa en pantalla ----
const sfx = [];
const fx = (t, inst, note = null, dur = 0.3, vel = 0.7) => sfx.push({ t: +t.toFixed(4), inst, note, dur, vel });
fx(T.cardGlow, "pop", null, 0.09, 0.9);
T.planRows.forEach((k, i) => fx(k, "marimba", [67, 72, 76][i], 0.45, 0.6)); // un renglón, una nota que sube
[67, 72, 76, 79].forEach((n) => fx(T.planDone, "marimba", n, 0.7, 0.5));     // y el acorde que los resuelve
fx(T.approve, "click", 72, 0.06, 0.8); fx(T.approve, "marimba", 79, 0.35, 0.9); // el clic lleva cuerpo para oírse sobre la voz
fx(T.stamp, "knock", null, 0.35, 0.9); // el sello baja 0.75 s después del clic
fx(T.hopBuild + 0.5, "marimba", 60, 0.35, 0.7); fx(T.boxClose + 0.25, "knock", null, 0.35, 0.55);
[72, 76, 79].forEach((n) => fx(T.tests, "marimba", n, 0.6, 0.6));
T.ticks.forEach((k, i) => { fx(k, "pluck", [69, 72, 76][i], 0.4, 0.65); fx(k, "marimba", [81, 84, 88][i], 0.3, 0.45); });
T.ci.forEach((k, i) => fx(k, "marimba", [67, 69, 72, 74][i], 0.3, 0.55));
[67, 72, 76, 79].forEach((n, i) => fx(T.zero + i * 0.03, "pluck", n, 0.7, 0.6));
fx(T.hopPR + 0.5, "marimba", 62, 0.35, 0.7);
fx(T.preview, "marimba", 76, 0.35, 0.5); fx(T.merge, "click", 72, 0.06, 0.8); fx(T.merged, "confetti", null, 1.2, 0.55);
fx(T.hopListo + 0.5, "marimba", 64, 0.35, 0.7);
[60, 64, 67, 72, 76].forEach((n, i) => fx(T.count[6] + i * 0.035, "pluck", n, 0.8, 0.6));
SCENES.slice(1).forEach((s) => fx(s.t0 - 0.3, "sweep", null, 0.3, 0.3)); // el viento, sólo en las cortinillas
T.logo = +(T.ctaSmall + 0.3).toFixed(4);
[84, 88, 91, 96].forEach((n, i) => fx(T.logo + i * 0.09, "bell", n, 1.6, 0.22)); // brillo suave al aparecer el logo

// ---- cama (pista bed, se agacha con la voz): acordes cada 2 compases, bombo suave, melodía discreta ----
const bed = [], pads = [];
const PROG = [[48, 55, 64], [45, 52, 60], [41, 48, 57], [43, 50, 59]];
const WAIT = [[T.handIn, T.approve], [T.handIn2, T.merge]]; // esperas de firma: acorde suspendido, sin bombo ni melodía
const inWait = (x) => WAIT.some(([a, b]) => x >= a && x < b);
for (let st = 0; st < DURATION; st += 4) {
  const en = Math.min(DURATION, st + 4);
  let segs = [[st, en]];
  for (const [a, z] of WAIT) segs = segs.flatMap(([x, y]) => (z <= x || a >= y ? [[x, y]] : [[x, a], [z, y]].filter(([p, r]) => r - p > 0.05)));
  const notes = st >= SC.cta.t0 - 0.01 ? [48, 55, 64, 72] : PROG[(st / 4) % 4];
  segs.forEach(([x, y]) => pads.push({ t: +x.toFixed(4), notes, dur: +(y - x).toFixed(4) }));
}
WAIT.forEach(([a, z]) => pads.push({ t: +a.toFixed(4), notes: [50, 55, 60, 67], dur: +(z - a + 0.25).toFixed(4), gain: 0.55, release: 0.35 }));
for (let x = 0; x < SC.cta.t0; x += 1) if (!inWait(x)) bed.push({ t: x, inst: "kick", note: null, dur: 0.3, vel: x % 2 === 0 ? 0.4 : 0.28 });
const PHRASE = [67, null, 72, 74, 76, null, 74, 72, 69, null, 72, null, 67, 69, 72, null];
for (let k = 0; k * 0.5 < SC.cta.t0; k++) {
  const x = k * 0.5, n = PHRASE[k % PHRASE.length];
  const near = sfx.some((e) => e.inst !== "sweep" && Math.abs(e.t - x) < 0.3);
  if (n && !near && !inWait(x) && !inWait(x + 0.4)) bed.push({ t: x, inst: "marimba", note: n, dur: 0.4, vel: 0.16 });
}

// los efectos que caen mientras habla la voz suben para no quedar tapados
const speaking = (x) => LINES.some((l) => { const v = SC[l.scene].voice; return l.words.some((w) => x >= v + w.s - 0.05 && x <= v + w.e + 0.05); });
sfx.forEach((e) => { if (e.inst !== "sweep" && speaking(e.t)) e.vel = +Math.min(2.4, e.vel * 2.6).toFixed(2); });
sfx.sort((a, b) => a.t - b.t); bed.sort((a, b) => a.t - b.t);
const voice = SCENES.map((s) => ({ t: s.voice, file: L[s.id].file }));
writeFileSync(new URL("./score.gen.json", import.meta.url), JSON.stringify({ duration: DURATION, scenes: SCENES, T, sfx, bed, pads, voice }, null, 1));
writeFileSync(new URL("./score.gen.js", import.meta.url), `// generado por score.mjs\nwindow.SCORE = ${JSON.stringify({ duration: DURATION, scenes: SCENES, T })};\n`);
console.log(`${DURATION} s · ${sfx.length} efectos · ${bed.length} notas de cama`);
console.log(SCENES.map((s) => `${s.id} ${s.t0}–${s.t1}`).join(" · "));
