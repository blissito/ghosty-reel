// Partitura de «Ghosty Ads — El colador» (click-to-Messenger, vertical 1080×1920).
// La voz manda: cada escena mide lo que duran sus frases, cada animación se ancla a la palabra que la nombra
// (voice/lines.json, whisper large-v3) y toda escena, ya completa, se sostiene ≥ HOLD s antes de la cortinilla.
// La cama se alinea para que su caída (drop) caiga justo en el corte al cierre circular.
import { readFileSync, writeFileSync } from "node:fs";

const LINES = JSON.parse(readFileSync(new URL("./voice/lines.json", import.meta.url)));
const L = Object.fromEntries(LINES.map((l) => [l.scene, l]));
const HOLD = 2.1, WIPE = 0.6, R = (x) => +x.toFixed(3);
const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");

// escenas: frases [nombre, hueco] y las palabras que disparan animaciones; la escena dura lo que su voz
// o lo que su última animación + HOLD + cortinilla, lo que sea mayor
const DEF = [
  { id: "hook", lines: [["hookA", 0.3], ["hookB", 0.35]] },
  { id: "contesta", lines: [["contesta", 0.55]] },
  { id: "califica", lines: [["califica", 0.5]] },
  { id: "filtro", lines: [["filtroA", 0.5], ["filtroB", 0.3]] },
  { id: "reporte", lines: [["reporteA", 0.5], ["reporteB", 0.25]] },
  { id: "cierre", lines: [["cierre", 0.4]] },
  { id: "cta", lines: [["ctaA", 0.5], ["ctaB", 0.25], ["ctaC", 0.3]], last: true },
];
// palabra → tiempo absoluto (se resuelve durante el armado)
const VOICE = {};
const W = (line, which, edge = "s") => {
  const ws = L[line].words;
  const w = typeof which === "number" ? ws[which] : ws.find((x) => norm(x.w).startsWith(norm(which)));
  if (!w) throw new Error(`palabra «${which}» no está en ${line}`);
  return R(VOICE[line] + (edge === "s" ? w.s : w.e));
};
// animaciones por escena (se evalúan cuando la escena ya tiene sus frases colocadas)
const ANIM = {
  hook: (s) => ({ fly1: s.t0 + 0.45, fly2: s.t0 + 0.85, fly3: s.t0 + 1.25, bump1: W("hookA", "treinta"), bump2: W("hookA", 7), bump3: W("hookA", "siete"),
                  buzz: W("hookA", "siete", "e") + 0.05, ask: W("hookB", "cuantos") }),
  contesta: (s) => ({ ghostIn: s.t0 + 0.15, r1: W("contesta", "contesta"), in2: W("contesta", "cada"), r2: W("contesta", "uno", "e"),
                      watch: W("contesta", "instante"), chip: W("contesta", "instante", "e") + 0.3 }),
  califica: () => ({ ask: W("califica", "pregunta"), ans: W("califica", "falta", "e") + 0.05, pdf: W("califica", "pdf"), cal: W("califica", "cita"),
                     fold: W("califica", "deja"), drop: W("califica", "tablero") }),
  filtro: () => ({ b1: W("filtroA", "curiosos"), b2: W("filtroA", "despide"), bye: W("filtroA", "amabilidad"), stamp: W("filtroA", "gastar"),
                   gold: W("filtroA", "ellos"), beto: W("filtroB", "correo"), strike: W("filtroB", "falso"), flag: W("filtroB", "marca") }),
  reporte: () => ({ clock: W("reporteA", "nueve"), sun: W("reporteA", "manana"), moon: W("reporteA", "noche"), push: W("reporteA", "reporte"),
                    row1: W("reporteB", "quien"), row2: W("reporteB", "busca"), row3: W("reporteB", "sigue") }),
  cierre: (s) => ({ fall: s.t0 + 0.3, gold: W("cierre", "hablas"), badge: W("cierre", "compran") }),
  cta: (s) => ({ card: s.t0 + 0.1, btn: W("ctaA", "messenger"), gift: W("ctaB", "gratis"), mark: W("ctaB", "marca"), date: W("ctaC", "octubre") }),
};
let t0 = 0; const SCENES = []; const T = {};
for (const d of DEF) {
  let cur = t0;
  d.lines.forEach(([name, gap], i) => { VOICE[name] = R(cur + gap); cur = VOICE[name] + L[name].dur; });
  const a = ANIM[d.id]({ t0 });
  const lastAnim = Math.max(...Object.values(a));
  const voiceEnd = Math.max(...d.lines.map(([n]) => VOICE[n] + L[n].words.at(-1).e));
  const t1 = d.last ? R(Math.max(voiceEnd + 2.4, lastAnim + 2.6)) : R(Math.max(voiceEnd + 0.9, lastAnim + HOLD + WIPE));
  for (const [k, v] of Object.entries(a)) T[`${d.id}.${k}`] = R(v);
  SCENES.push({ id: d.id, t0, t1, hold: R(t1 - (d.last ? 0 : WIPE) - lastAnim) });
  t0 = t1;
}
const DURATION = t0;
const SC = Object.fromEntries(SCENES.map((s) => [s.id, s]));

T.words = LINES.map((l) => ({ line: l.scene, words: l.words.map((w) => ({ w: w.w, s: R(VOICE[l.scene] + w.s), e: R(VOICE[l.scene] + w.e) })) }));

// ---- efectos: uno por animación, nunca el mismo dos veces seguidas ----
const sfx = [];
const fx = (t, file, gain = 0.7) => sfx.push({ t: R(Math.max(0, t)), file, gain });
const t = (k) => T[k];
fx(t("hook.fly1"), "pop"); fx(t("hook.fly2"), "8bit-blip", 0.5); fx(t("hook.fly3"), "pop"); fx(t("hook.bump1"), "tick", 0.6); fx(t("hook.bump2"), "8bit-blip", 0.45); fx(t("hook.bump3"), "tick", 0.6);
fx(t("hook.buzz"), "hit-low", 0.6); fx(t("hook.ask"), "pin", 0.5);
fx(t("contesta.ghostIn"), "bean"); fx(t("contesta.r1"), "whoosh-short", 0.55); fx(t("contesta.in2"), "pop"); fx(t("contesta.r2"), "whoosh-short", 0.55);
fx(t("contesta.watch"), "ding"); fx(t("contesta.chip"), "tick", 0.6);
fx(t("califica.ask"), "pop"); fx(t("califica.ans"), "tick", 0.6); fx(t("califica.pdf"), "paper"); fx(t("califica.cal"), "pin"); fx(t("califica.fold"), "card"); fx(t("califica.drop") + 0.3, "land");
fx(t("filtro.b1") + 0.35, "block"); fx(t("filtro.b2") + 0.35, "bean"); fx(t("filtro.bye"), "whoosh-short", 0.55); fx(t("filtro.stamp") + 0.18, "stamp"); fx(t("filtro.gold") + 0.4, "coin", 0.6);
fx(t("filtro.beto"), "pop"); fx(t("filtro.strike"), "8bit-hack", 0.5); fx(t("filtro.flag"), "turn");
fx(t("reporte.clock"), "tick", 0.6); fx(t("reporte.sun"), "pop"); fx(t("reporte.moon"), "pin"); fx(t("reporte.push") + 0.2, "ding");
fx(t("reporte.row1"), "8bit-blip", 0.45); fx(t("reporte.row2"), "tick", 0.6); fx(t("reporte.row3"), "8bit-blip", 0.45);
fx(t("cierre.fall"), "land"); fx(t("cierre.gold"), "pop"); fx(t("cierre.badge"), "coin", 0.6);
fx(t("cta.card"), "card"); fx(t("cta.btn"), "8bit-pickup", 0.5); fx(t("cta.gift"), "pop"); fx(t("cta.mark"), "tick", 0.6); fx(t("cta.date"), "stamp");
// cortinillas: riser/whoosh mientras cierran; golpe cuando el glifo sella (back.out(1.8): impacto a 1/(s+1) del tween).
// En el cierre el sello cae EXACTO en t0: ahí va la caída de la cama y el zoom-punch.
const CUTS = { contesta: ["whoosh-fly", "hit-sub"], califica: ["riser", "hit-low"], filtro: ["whoosh-fly", "hit-sub"], reporte: ["riser", "hit-low"], cierre: ["riser", "hit-sub"], cta: ["whoosh-fly", "hit-low"] };
T.seal = {};
for (const [id, [sw, hit]] of Object.entries(CUTS)) {
  const c = SC[id].t0; const sealAt = id === "cierre" ? R(c - 0.3 / 2.8) : R(c - 0.2);
  T.seal[id] = sealAt;
  fx(c - 0.62, sw, 0.5); fx(sealAt + 0.3 / 2.8, hit, id === "cierre" ? 0.8 : 0.6);
  if (id === "cierre") fx(c + 0.02, "stamp", 0.6);
}
sfx.sort((a, b) => a.t - b.t);
for (let i = 1; i < sfx.length; i++) if (sfx[i].file === sfx[i - 1].file) throw new Error(`efecto repetido seguido: ${sfx[i].file} en ${sfx[i].t}`);

const music = { drop: SC.cierre.t0 };
const voice = LINES.map((l) => ({ t: VOICE[l.scene], file: l.file }));
writeFileSync(new URL("./score.gen.json", import.meta.url), JSON.stringify({ duration: DURATION, scenes: SCENES, T, sfx, voice, music }, null, 1));
writeFileSync(new URL("./score.gen.js", import.meta.url), `// generado por score.mjs\nwindow.SCORE = ${JSON.stringify({ duration: DURATION, scenes: SCENES, T })};\n`);
console.log(`${DURATION} s · ${sfx.length} efectos · caída de la cama en ${music.drop} s`);
console.log(SCENES.map((s) => `${s.id} ${s.t0}–${s.t1} (hold ${s.hold})`).join("\n"));
