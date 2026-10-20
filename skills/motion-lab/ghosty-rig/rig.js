/* ghosty-rig — gestos de Ghosty sobre una timeline GSAP pausada (HyperFrames).
 *
 * Uso:
 *   const rig = GhostyRig.create(tl, { root: "#stage", shadow: "#gShadow", floorY: 600 });
 *   rig.place(640, 600, 1.5);          // pie (base de los olanes) en x, y; escala
 *   rig.idle(0, 6).blink(0.3).look(0.6, "left").hop(2).happy(2).proud(3).shy(4).wave(5).exit(5.5);
 *   rig.finalize(6.7);                 // agrega el driver; SIEMPRE al final
 *   window.__sfxCues = rig.cues;
 *
 * Todo es determinista: la pose del cuerpo es función pura del tiempo (un driver ease:"none" con onUpdate),
 * y ojos/accesorios son tweens dentro de la misma timeline. Nada de rAF, Date, Math.random ni repeat:-1.
 * Las piezas se buscan por id DENTRO de `root`, así que dos Ghostys en la misma página pueden convivir si cada
 * uno vive en su propio <svg> (pasa ese <svg> como root).
 */
(function (G) {
  "use strict";
  // pivotes en coordenadas del vector oficial (viewBox 48 22 160 190)
  const BASE = [128, 208], EYES = [128, 76], EYE_L = [108, 76], EYE_R = [157, 76], RIG_C = [128, 117];
  // escala alrededor de un punto, como atributo transform (no depende del <svg> que lo contiene)
  const about = ([ox, oy], sx, sy) => `translate(${ox} ${oy}) scale(${sx.toFixed(4)} ${sy.toFixed(4)}) translate(${-ox} ${-oy})`;
  const DIRS = {
    center: [0, 0], left: [-7, 0], right: [7, 0], up: [0, -6], down: [0, 7],
    upLeft: [-6, -5], upRight: [6, -5], downLeft: [-7, 6], downRight: [7, 6],
  };
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const smooth = (u) => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
  const EASES = {
    inOut: (u) => 0.5 - 0.5 * Math.cos(Math.PI * clamp(u, 0, 1)),
    in: (u) => clamp(u, 0, 1) ** 2,            // caída con gravedad
    out: (u) => 1 - (1 - clamp(u, 0, 1)) ** 2, // despegue
  };
  // envolvente: sube en a, se sostiene hasta d, baja en b
  const env = (t, t0, d, a, b) => {
    if (t < t0 || t > t0 + d + b) return 0;
    if (t < t0 + a) return smooth((t - t0) / a);
    if (t < t0 + d) return 1;
    return 1 - smooth((t - t0 - d) / b);
  };

  function create(tl, opts = {}) {
    const q = (s) => (typeof s === "string" ? document.querySelector(s) : s);
    const root = q(opts.root || document);
    const $ = (id) => root.querySelector("#" + id);
    const el = {
      hop: $("gHop"), sq: $("gSq"), rig: $("gRig"), body: $("gBody"), eyes: $("gEyes"), pup: $("gPup"),
      eyeL: $("eyeL"), eyeR: $("eyeR"), happyL: $("gHappyL"), happyR: $("gHappyR"), gl: $("gGl"),
    };
    for (const k in el) if (!el[k]) throw new Error("ghosty-rig: falta la pieza " + k);
    const shadow = opts.shadow ? q(opts.shadow) : null;
    const floorY = opts.floorY ?? null;

    const SEGS = [], HOPS = [], IMPACTS = [], CROUCH = [], FLOATS = [], ROCKS = [], POSES = [], EXCITE = [];
    const cues = [];
    let home = { x: 0, y: 0, s: 1 };
    const cue = (t, sfx, gesture) => cues.push({ t: +t.toFixed(3), sfx, gesture });

    // ---- trayectoria base (sólo SEGS + HOPS): de aquí sale la velocidad ----
    let ready = false;
    const at = (t, x, y, s) => SEGS.push({ t0: t, t1: t, to: { x, y, s }, arc: 0, ease: "inOut" });
    const resolve = () => {
      SEGS.sort((a, b) => a.t0 - b.t0);
      let prev = null;
      for (const g of SEGS) {
        if (prev && g.t0 < prev.cut) prev.cut = g.t0;
        g.cut = g.t1;
        g.from = prev ? segAt(prev, Math.min(g.t0, prev.cut)) : { ...g.to };
        prev = g;
      }
      ready = true;
    };
    const segAt = (g, t) => {
      if (g.t1 <= g.t0 || t >= g.t1) return { ...g.to };
      const u = (t - g.t0) / (g.t1 - g.t0), e = EASES[g.ease](u), f = g.from;
      return {
        x: f.x + (g.to.x - f.x) * e,
        y: f.y + (g.to.y - f.y) * e - g.arc * Math.sin(Math.PI * u),
        s: f.s + (g.to.s - f.s) * e,
      };
    };
    const motion = (t) => {
      let g = SEGS[0];
      for (const x of SEGS) { if (x.t0 <= t) g = x; else break; }
      const st = segAt(g, Math.min(t, g.cut));
      for (const h of HOPS) if (t > h.t && t < h.t + h.dur) { const v = (t - h.t) / h.dur; st.y -= h.h * 4 * v * (1 - v); }
      return st;
    };
    const vel = (t) => { const a = motion(t - 1 / 60), b = motion(t + 1 / 60); return { x: (b.x - a.x) * 30, y: (b.y - a.y) * 30 }; };

    // ---- olanes: se mecen desde su unión; la forma oficial no cambia (amp 0 = trazo oficial exacto) ----
    const D = el.body.getAttribute("d");
    const TOK = D.match(/[A-Za-z]|-?\d*\.?\d+(?:e-?\d+)?/g);
    const hem = (dx, t, amp) => {
      const out = []; let cmd = "", buf = [];
      for (const k of TOK) {
        if (/[A-Za-z]/.test(k)) { cmd = k; out.push(k); continue; }
        if (cmd === "H") { out.push((+k).toFixed(3)); continue; }
        buf.push(+k);
        if (buf.length === 2) {
          const [x, y] = buf; buf = [];
          const i = x > 156 ? 0 : x > 120 ? 1 : 2, ph = 2 * Math.PI * 0.9 * t - i * 1.15;
          const w = smooth((y - 184) / 22);
          out.push((x + dx * smooth((y - 120) / 88) + amp * Math.sin(ph) * w).toFixed(3) + " " + (y + amp * 0.45 * Math.cos(ph) * w).toFixed(3));
        }
      }
      return out.join(" ");
    };

    const render = (t) => {
      if (!ready) resolve();
      const m = motion(t), v = vel(t), lag = vel(t - 0.09);
      const sp = Math.hypot(v.x, v.y), spLag = Math.hypot(lag.x, lag.y);
      let x = m.x, y = m.y, s = m.s, r = 0, idleAmp = 0;
      // flotación finita, se apaga si vuela
      const calm = 1 - Math.min(1, sp / 500);
      for (const f of FLOATS) if (t > f.t0 && t < f.t1) {
        const e = smooth((t - f.t0) / 0.4) * smooth((f.t1 - t) / 0.4) * calm, w = (2 * Math.PI * (t - f.t0)) / f.period;
        y += f.amp * Math.sin(w) * e; x += f.amp * 0.35 * Math.sin(w / 1.5) * e; idleAmp += 0.8 * e;
      }
      for (const p of POSES) { const e = env(t, p.t, p.d, p.a, p.b); r += p.r * e; s *= 1 + (p.s - 1) * e; y += p.dy * e; }
      for (const k of ROCKS) if (t > k.t && t < k.t + k.d) { const u = (t - k.t) / k.d; r += k.deg * Math.sin(2 * Math.PI * k.times * u) * Math.sin(Math.PI * u); }
      r += clamp(lag.x * 0.006, -9, 9); // se inclina con la velocidad, con retraso
      el.hop.setAttribute("transform", `translate(${x.toFixed(2)} ${y.toFixed(2)}) rotate(${r.toFixed(2)}) scale(${s.toFixed(4)}) translate(${-BASE[0]} ${-BASE[1]})`);
      // estirón A LO LARGO del movimiento, área constante, máximo 6 %
      const k = 1 + Math.min(0.06, sp * 0.00004), a = (Math.atan2(v.y, v.x) * 180) / Math.PI;
      el.rig.setAttribute("transform", `translate(${RIG_C[0]} ${RIG_C[1]}) rotate(${a.toFixed(2)}) scale(${k.toFixed(4)} ${(1 / k).toFixed(4)}) rotate(${(-a).toFixed(2)}) translate(${-RIG_C[0]} ${-RIG_C[1]})`);
      // squash: anticipación (se agacha) + contacto (aplasta y rebota amortiguado)
      let c = 0;
      for (const cr of CROUCH) if (t > cr.t && t < cr.t + cr.d) c += cr.k * Math.sin((Math.PI / 2) * ((t - cr.t) / cr.d));
      for (const im of IMPACTS) if (t > im.t && t < im.t + 0.7) { const d = t - im.t; c += im.k * Math.exp(-d / 0.12) * Math.cos((2 * Math.PI * d) / 0.34); }
      el.sq.setAttribute("transform", `translate(${BASE[0]} ${BASE[1]}) scale(${(1 / (1 - c)).toFixed(4)} ${(1 - c).toFixed(4)}) translate(${-BASE[0]} ${-BASE[1]})`);
      // los lentes llegan tarde (follow-through vertical)
      el.gl.setAttribute("transform", `translate(0 ${(clamp(-lag.y * 0.006, -5, 5) + c * 40).toFixed(2)})`);
      // sombra del piso: se encoge con la altura
      if (shadow && floorY !== null) {
        const h = Math.max(0, floorY - y), sc = 1 - clamp(h / 420, 0, 0.6);
        shadow.setAttribute("transform", `translate(${x.toFixed(2)} ${floorY}) scale(${(sc * s * (1 / (1 - c))).toFixed(4)} ${(sc * s).toFixed(4)})`);
        shadow.setAttribute("opacity", (h > 700 ? 0 : 1).toString());
      }
      // olanes
      let ex = 0;
      for (const e of EXCITE) if (t > e.t && t < e.t + e.d) ex += e.k * Math.sin((Math.PI * (t - e.t)) / e.d);
      const drag = clamp(-lag.x * 0.007, -10, 10);
      el.body.setAttribute("d", hem(drag, t, 1.2 + idleAmp + Math.min(2, spLag * 0.0015) + ex * 1.5));
    };

    // ---- cara y accesorios: GSAP anima objetos proxy y applyFace escribe los atributos transform ----
    // (svgOrigin de GSAP se mide en el <svg> raíz: con Ghosty movido dentro de un escenario, el pivote se corre)
    const face = { blink: 1, lidL: 1, lidR: 1, px: 0, py: 0 }, acc = {};
    const applyFace = () => {
      el.eyes.setAttribute("transform", about(EYES, 1, face.blink));
      el.eyeL.setAttribute("transform", about(EYE_L, 1, face.lidL));
      el.eyeR.setAttribute("transform", about(EYE_R, 1, face.lidR));
      el.pup.setAttribute("transform", `translate(${face.px.toFixed(2)} ${face.py.toFixed(2)})`);
      for (const id in acc) acc[id].el.setAttribute("transform", about(acc[id].o, acc[id].k, acc[id].k));
    };
    const lids = (t, v, d = 0.22) => tl.to(face, { lidL: v, lidR: v, duration: d, ease: "power2.out", onUpdate: applyFace }, t);
    const gaze = (t, dir, d = 0.22) => {
      const [x, y] = Array.isArray(dir) ? dir : DIRS[dir] || DIRS.center;
      tl.to(face, { px: x, py: y, duration: d, ease: "sine.inOut", onUpdate: applyFace }, t);
    };

    const api = {
      cues,
      /** Pie de Ghosty (base de los olanes) en (x, y) del lienzo, escala s. Llamar primero. */
      place(x, y, s = 1) { home = { x, y, s }; at(0, x, y, s); return api; },
      /** Vuela a (x, y) entre t y t+dur, en arco. */
      moveTo(t, x, y, { dur = 0.6, s = home.s, arc = null, ease = "inOut" } = {}) {
        SEGS.push({ t0: t, t1: t + dur, to: { x, y, s }, arc: arc ?? 60, ease });
        IMPACTS.push({ t: t + dur, k: 0.03 }); cue(t, "whoosh", "moveTo"); return api;
      },
      /** Entra cayendo desde `from` (default: arriba) hasta `to` (default: place) y aterriza con squash. */
      enter(t, { from = null, to = null, dur = 0.42 } = {}) {
        const dst = to || home, src = from || [dst.x, -260];
        at(t, src[0], src[1], dst.s);
        SEGS.push({ t0: t + 1e-4, t1: t + dur, to: { x: dst.x, y: dst.y, s: dst.s }, arc: 0, ease: "in" });
        IMPACTS.push({ t: t + dur, k: 0.11 }); EXCITE.push({ t: t + dur, d: 0.8, k: 1 });
        cue(t, "whoosh", "enter"); cue(t + dur, "thud", "enter"); return api;
      },
      /** Se agacha (anticipación) y sale disparado hacia `to` (default: arriba). */
      exit(t, { to = null, dur = 0.4, anticip = 0.14 } = {}) {
        const dst = to || [home.x, -320];
        CROUCH.push({ t, d: anticip, k: 0.1 });
        SEGS.push({ t0: t + anticip, t1: t + anticip + dur, to: { x: dst[0], y: dst[1], s: home.s }, arc: 0, ease: "out" });
        cue(t + anticip, "whoosh", "exit"); return api;
      },
      /** Brinco: se agacha, parábola de h px y aterriza con squash amortiguado. */
      hop(t, { h = 80, dur = 0.5, anticip = 0.1 } = {}) {
        CROUCH.push({ t, d: anticip, k: 0.08 });
        HOPS.push({ t: t + anticip, h, dur });
        IMPACTS.push({ t: t + anticip + dur, k: 0.07 }); EXCITE.push({ t: t + anticip, d: 0.9, k: 1.2 });
        cue(t + anticip, "whoosh", "hop"); cue(t + anticip + dur, "thud", "hop"); return api;
      },
      /** Parpadeo: ojos completos (párpado + pupila). double = dos seguidos. */
      blink(t, { double = false } = {}) {
        tl.fromTo(face, { blink: 1 }, { blink: 0.08, duration: 0.06, yoyo: true, repeat: double ? 3 : 1, ease: "power1.inOut", immediateRender: false, onUpdate: applyFace }, t);
        cue(t, "tick", "blink");
        return api;
      },
      /** Guiño: un ojo pasa a ^ un momento. side "L" | "R" (del lienzo). */
      wink(t, { side = "R", hold = 0.4 } = {}) {
        const e = side === "L" ? el.eyeL : el.eyeR, h = side === "L" ? el.happyL : el.happyR;
        tl.set(e, { visibility: "hidden" }, t); tl.set(h, { visibility: "visible" }, t);
        tl.set(e, { visibility: "visible" }, t + hold); tl.set(h, { visibility: "hidden" }, t + hold);
        POSES.push({ t, d: hold, a: 0.1, b: 0.15, r: side === "L" ? -3 : 3, s: 1, dy: 0 });
        cue(t, "tick", "wink"); return api;
      },
      /** Mira: "left" | "right" | "up" | "down" | "upLeft" … | "center" | [x, y] (px del vector, máx ~8). */
      look(t, dir = "center", { dur = 0.22 } = {}) { gaze(t, dir, dur); return api; },
      /** Contento: ojitos ^^, olanes animados y un rebote mínimo. */
      happy(t, { hold = 0.8 } = {}) {
        [el.eyeL, el.eyeR].forEach((e) => { tl.set(e, { visibility: "hidden" }, t); tl.set(e, { visibility: "visible" }, t + hold); });
        [el.happyL, el.happyR].forEach((e) => { tl.set(e, { visibility: "visible" }, t); tl.set(e, { visibility: "hidden" }, t + hold); });
        POSES.push({ t, d: hold - 0.15, a: 0.12, b: 0.2, r: 0, s: 1.02, dy: -6 });
        EXCITE.push({ t, d: hold, k: 1 }); cue(t, "sparkle", "happy"); return api;
      },
      /** Orgulloso: se infla parejo, mira arriba con ojos entrecerrados y luego baja la vista a su gafete. */
      proud(t, { hold = 0.9 } = {}) {
        POSES.push({ t, d: hold, a: 0.25, b: 0.3, r: 0, s: 1.05, dy: -4 });
        gaze(t, [3, -5], 0.25); lids(t + 0.05, 0.72, 0.25);
        gaze(t + hold * 0.55, "down", 0.3); lids(t + hold * 0.55, 1, 0.2);
        gaze(t + hold, "center", 0.25);
        EXCITE.push({ t, d: hold, k: 0.6 }); cue(t, "swell", "proud"); return api;
      },
      /** Apenado: se ladea y se encoge, baja la mirada de lado, entrecierra, te mira un instante y vuelve a desviar. */
      shy(t, { hold = 0.9 } = {}) {
        POSES.push({ t, d: hold, a: 0.3, b: 0.3, r: -6, s: 0.96, dy: 6 });
        gaze(t + 0.05, "downLeft", 0.3); lids(t + 0.15, 0.62, 0.25);
        gaze(t + hold * 0.45, [-1, 2], 0.18); lids(t + hold * 0.45, 1, 0.15);
        gaze(t + hold * 0.7, "downLeft", 0.25); lids(t + hold * 0.72, 0.7, 0.2);
        gaze(t + hold, "center", 0.25); lids(t + hold, 1, 0.2);
        cue(t, "aww", "shy"); return api;
      },
      /** Saluda con el cuerpo (Ghosty no tiene manos): balanceo desde la base + olanes. */
      wave(t, { dur = 0.6, times = 2, deg = 7 } = {}) {
        ROCKS.push({ t, d: dur, times, deg }); EXCITE.push({ t, d: dur + 0.2, k: 1 });
        cue(t, "swish", "wave"); return api;
      },
      /** Flotación en reposo entre t0 y t1 (finita; entra y sale suave). */
      idle(t0, t1, { amp = 8, period = 1.6 } = {}) { FLOATS.push({ t0, t1, amp, period }); return api; },
      /** Accesorio (capa aparte: "gBadge", "gHat", o uno tuyo dentro de #gAcc con data-origin). */
      accessory(id, t, { show = true, dur = 0.34 } = {}) {
        const a = $(id); if (!a) throw new Error("ghosty-rig: no existe el accesorio " + id);
        const st = (acc[id] ||= { el: a, o: (a.getAttribute("data-origin") || "128 117").split(/[ ,]+/).map(Number), k: 1 });
        if (show) {
          tl.set(a, { visibility: "visible" }, t);
          tl.fromTo(st, { k: 0.2 }, { k: 1, duration: dur, ease: "back.out(2.4)", immediateRender: false, onUpdate: applyFace }, t);
          cue(t + dur / 3.4, "pop", "accessory"); // back.out(2.4): el golpe va en 1/(s+1) del tween
        } else {
          tl.to(st, { k: 0.2, duration: dur * 0.7, ease: "power2.in", onUpdate: applyFace }, t);
          tl.set(a, { visibility: "hidden" }, t + dur * 0.7);
        }
        return api;
      },
      /** Agrega el driver del cuerpo. Llamar UNA vez, después de todos los gestos. */
      finalize(duration) {
        cues.sort((a, b) => a.t - b.t);
        const drv = { t: 0 };
        tl.fromTo(drv, { t: 0 }, { t: duration, duration, ease: "none", immediateRender: false, onUpdate: () => { render(drv.t); applyFace(); } }, 0);
        render(0); applyFace();
        return tl;
      },
      render,
    };
    return api;
  }
  G.GhostyRig = { create, DIRS };
})(window);
