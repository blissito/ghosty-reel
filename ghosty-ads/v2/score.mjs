// Partitura de «Ghosty Ads — El colador» v2 (click-to-Messenger, vertical 1080×1920, ≤ 62 s).
// v2: cifras dichas de corrido («treintaisiete», «treintaiuno»), acto nuevo «Ghosty te arma la campaña»
// después del hook, contesta + califica en un solo beat y CTA de «tu primera campaña».
// La voz manda: cada animación se ancla a la palabra que la nombra (voice/lines.json, whisper large-v3) y toda
// escena, ya completa, se sostiene ≥ HOLD s antes de la cortinilla. La caída de la cama cae en el corte al cierre.
import { readFileSync, writeFileSync } from "node:fs";

const LINES = JSON.parse(readFileSync(new URL("./voice/lines.json", import.meta.url)));
const L = Object.fromEntries(LINES.map((l) => [l.scene, l]));
const HOLD = 2.05, WIPE = 0.6, R = (x) => +x.toFixed(3);
const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");

const DEF = [
  { id: "hook", lines: [["hookA", 0.3], ["hookB", 0.3]] },
  { id: "cmp", lines: [["cmpA", 0.45], ["cmpB", 0.35], ["cmpC", 0.35], ["cmpD", 0.45]] },
  { id: "atiende", lines: [["atiende", 0.45]] },
  { id: "filtro", lines: [["filtroA", 0.45], ["filtroB", 0.25]] },
  { id: "reporte", lines: [["reporteA", 0.45], ["reporteB", 0.2]] },
  { id: "cierre", lines: [["cierre", 0.35]] },
  { id: "cta", lines: [["ctaA", 0.45], ["ctaB", 0.2], ["ctaC", 0.3]], last: true },
];
const VOICE = {};
const W = (line, which, edge = "s") => {
  const ws = L[line].words;
  const w = typeof which === "number" ? ws[which] : ws.find((x) => norm(x.w).startsWith(norm(which)));
  if (!w) throw new Error(`palabra «${which}» no está en ${line}`);
  return R(VOICE[line] + (edge === "s" ? w.s : w.e));
};
const ANIM = {
  hook: (s) => ({ fly1: s.t0 + 0.45, fly2: s.t0 + 0.85, fly3: s.t0 + 1.25, bump: W("hookA", "37"), buzz: W("hookA", "37", "e") + 0.05, ask: W("hookB", "cuantos") }),
  cmp: (s) => ({
    ghostIn: s.t0 + 0.15, print: W("cmpA", "campana"), chipCre: W("cmpA", "creativo"), chipVid: W("cmpA", "creativo", "e") + 0.15, chipCol: W("cmpA", "marca"),
    toCopy: VOICE.cmpB - 0.3, typeA: VOICE.cmpB, typeB: W("cmpB", "anuncio", "e"), send: W("cmpB", "anuncio", "e") + 0.1,
    target: W("cmpC", "segmentacion"), c1: W("cmpC", "intereses"), c2: W("cmpC", "intereses", "e") + 0.12, c3: W("cmpC", "edad"), c4: W("cmpC", "zona"), c5: W("cmpC", "zona", "e") + 0.2,
    g1: W("cmpC", "curiosos"), g2: W("cmpC", "curiosos") + 0.3,
    toPause: VOICE.cmpD - 0.3, budget: VOICE.cmpD - 0.1, paused: W("cmpD", "pausa"), push: W("cmpD", "prendes"), tap: W("cmpD", "celular"), active: W("cmpD", "celular") + 0.25,
  }),
  atiende: () => ({ reply: W("atiende", "contesta"), watch: W("atiende", "instante"), pdf: W("atiende", "cotiza"), cal: W("atiende", "agenda"), drop: W("atiende", "agenda", "e") + 0.35 }),
  filtro: () => ({ b1: W("filtroA", "curiosos"), b2: W("filtroA", "despide"), bye: W("filtroA", "amabilidad"), stamp: W("filtroA", "gastar"),
                   gold: W("filtroA", "ellos"), beto: W("filtroB", "correo"), strike: W("filtroB", "falso"), flag: W("filtroB", "marca") }),
  reporte: () => ({ clock: W("reporteA", "nueve"), sun: W("reporteA", "manana"), moon: W("reporteA", "noche"), push: W("reporteA", "reporte"),
                    row1: W("reporteB", "quien"), row2: W("reporteB", "busca"), row3: W("reporteB", "sigue") }),
  cierre: (s) => ({ fall: s.t0 + 0.3, gold: W("cierre", "hablas"), badge: W("cierre", "compran") }),
  cta: (s) => ({ card: s.t0 + 0.1, btn: W("ctaA", "messenger"), gift: W("ctaB", "campana"), mark: W("ctaB", "campana", "e") + 0.3, date: W("ctaC", "octubre") }),
};
let t0 = 0; const SCENES = []; const T = {};
for (const d of DEF) {
  let cur = t0;
  d.lines.forEach(([name, gap]) => { VOICE[name] = R(cur + gap); cur = VOICE[name] + L[name].dur; });
  const a = ANIM[d.id]({ t0 });
  const lastAnim = Math.max(...Object.values(a));
  const voiceEnd = Math.max(...d.lines.map(([n]) => VOICE[n] + L[n].words.at(-1).e));
  const t1 = d.last ? R(Math.max(voiceEnd + 2.3, lastAnim + 2.5)) : R(Math.max(voiceEnd + 0.9, lastAnim + HOLD + WIPE));
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
fx(t("hook.fly1"), "pop"); fx(t("hook.fly2"), "8bit-blip", 0.5); fx(t("hook.fly3"), "pop"); fx(t("hook.bump"), "tick", 0.6); fx(t("hook.buzz"), "hit-low", 0.6); fx(t("hook.ask"), "pin", 0.5);
// acto de la campaña
fx(t("cmp.ghostIn"), "bean"); fx(t("cmp.print"), "paper"); fx(t("cmp.print") + 0.5, "whoosh-short", 0.45); fx(t("cmp.chipCre"), "pop"); fx(t("cmp.chipVid"), "tick", 0.55); fx(t("cmp.chipCol"), "pop");
fx(t("cmp.toCopy"), "whoosh-fly", 0.45);
for (let k = 0, tt = t("cmp.typeA"); tt < t("cmp.typeB") - 0.05; tt += 0.16, k++) fx(tt, k % 2 ? "tick" : "8bit-blip", 0.3);  // tecleo
fx(t("cmp.send"), "pop"); fx(t("cmp.target"), "card");
["c1", "c2", "c3", "c4", "c5"].map((k) => t("cmp." + k)).sort((x, y) => x - y).forEach((tt, i) => fx(tt, i % 2 ? "pop" : "pin", 0.6));
fx(t("cmp.g1") + 0.3, "block"); fx(t("cmp.g2") + 0.3, "bean");
fx(t("cmp.toPause"), "whoosh-short", 0.5); fx(t("cmp.budget"), "coin", 0.55); fx(t("cmp.paused"), "tick", 0.6); fx(t("cmp.push"), "ding"); fx(t("cmp.tap"), "block"); fx(t("cmp.active"), "stamp");
// atiende
fx(t("atiende.reply"), "whoosh-short", 0.55); fx(t("atiende.watch"), "ding"); fx(t("atiende.pdf"), "paper"); fx(t("atiende.cal"), "pin"); fx(t("atiende.drop"), "land");
// colador
fx(t("filtro.b1") + 0.35, "block"); fx(t("filtro.b2") + 0.35, "bean"); fx(t("filtro.bye"), "whoosh-short", 0.55); fx(t("filtro.stamp") + 0.18, "stamp"); fx(t("filtro.gold") + 0.4, "coin", 0.6);
fx(t("filtro.beto"), "pop"); fx(t("filtro.strike"), "8bit-hack", 0.5); fx(t("filtro.flag"), "turn");
fx(t("reporte.clock"), "tick", 0.6); fx(t("reporte.sun"), "pop"); fx(t("reporte.moon"), "pin"); fx(t("reporte.push") + 0.2, "ding");
fx(t("reporte.row1"), "8bit-blip", 0.45); fx(t("reporte.row2"), "tick", 0.6); fx(t("reporte.row3"), "8bit-blip", 0.45);
fx(t("cierre.fall"), "land"); fx(t("cierre.gold"), "pop"); fx(t("cierre.badge"), "coin", 0.6);
fx(t("cta.card"), "card"); fx(t("cta.btn"), "8bit-pickup", 0.5); fx(t("cta.gift"), "pop"); fx(t("cta.mark"), "tick", 0.6); fx(t("cta.date"), "stamp");
const CUTS = { cmp: ["whoosh-fly", "hit-sub"], atiende: ["riser", "hit-low"], filtro: ["whoosh-fly", "hit-sub"], reporte: ["riser", "hit-low"], cierre: ["riser", "hit-sub"], cta: ["whoosh-fly", "hit-low"] };
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
