// Vida del cuarto: plantas que se mecen con el viento, lámparas que «respiran» y monitor con código
// que se escribe solo. Todo es función pura de t (la página re-arma cuadros reproduciendo desde 0 con ?t=).
// Al sorprenderse Ghosty (surpriseAt) el cuarto reacciona: las plantas dan un brinco amortiguado y las
// lámparas parpadean una vez.
const PLANTS = ["anim_plantSmall1", "anim_plantSmall2", "anim_plantSmall3", "anim_pottedPlant"];
const LAMPS = ["anim_lampRoundTable_shade", "anim_lampRoundFloor_shade"];
const SCREEN = "anim_computerScreen";
const MINT = "#85DDCB", DARK = "#3B3F4E";

// hash determinista 0..1 (para anchos de renglón y sangrías)
const rnd = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// resorte amortiguado: arranca en 0, sube y se apaga (oscilador subamortiguado clásico)
const spring = (d, freq = 3.2, decay = 4.5) => (d <= 0 ? 0 : Math.exp(-d * decay) * Math.sin(d * freq * Math.PI * 2));

// overlay(g, W, H, t): se pinta encima del código (aquí, el inicio de sesión de este short)
export function setupAmbient({ THREE, root, camera, overlay = null }) {
  const find = (n) => root.getObjectByName(n);

  // --- plantas: rotación sobre la base de la maceta (el origen ya está ahí desde Blender) ---
  const plants = PLANTS.map(find).filter(Boolean).map((o, i) => ({
    o, rx: o.rotation.x, rz: o.rotation.z,
    phase: i * 1.7 + 0.4, freq: 0.55 + i * 0.09, amp: o.name === "anim_pottedPlant" ? 0.022 : 0.035,
    delay: i * 0.06, // el «susto» las alcanza una tras otra
  }));

  // --- lámparas: el material de la pantalla se aclara (color > 1 multiplica la textura horneada) + halo aditivo ---
  const haloTex = (() => {
    const c = document.createElement("canvas"); c.width = c.height = 128;
    const g = c.getContext("2d");
    const r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    r.addColorStop(0, "rgba(255,227,163,0.9)"); r.addColorStop(0.35, "rgba(255,214,140,0.35)"); r.addColorStop(1, "rgba(255,214,140,0)");
    g.fillStyle = r; g.fillRect(0, 0, 128, 128);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  })();
  const lamps = LAMPS.map(find).filter(Boolean).map((o, i) => {
    o.updateWorldMatrix(true, false);
    const box = new THREE.Box3().setFromObject(o), size = box.getSize(new THREE.Vector3());
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, toneMapped: false }));
    halo.position.copy(box.getCenter(new THREE.Vector3()));
    halo.scale.setScalar(Math.max(size.x, size.y, size.z) * 2.6);
    halo.renderOrder = 4;
    o.parent.add(halo); // mismo espacio que la lámpara
    halo.position.applyMatrix4(o.parent.matrixWorld.clone().invert());
    const mats = [];
    o.traverse((m) => { if (m.isMesh) { m.material = m.material.clone(); mats.push(m.material); } });
    return { o, halo, mats, phase: i * 2.3 };
  });

  // --- monitor: lienzo con código que se escribe, scroll y barra de progreso ---
  let screen = null;
  const so = find(SCREEN);
  if (so) {
    so.updateWorldMatrix(true, true);
    const box = new THREE.Box3().setFromObject(so), size = box.getSize(new THREE.Vector3()), center = box.getCenter(new THREE.Vector3());
    // normal de la cara: promedio de normales en mundo (la pantalla es casi plana)
    const n = new THREE.Vector3();
    so.traverse((m) => {
      if (!m.isMesh || !m.geometry.attributes.normal) return;
      const a = m.geometry.attributes.normal, nm = new THREE.Matrix3().getNormalMatrix(m.matrixWorld), v = new THREE.Vector3();
      for (let k = 0; k < a.count; k++) n.add(v.fromBufferAttribute(a, k).applyMatrix3(nm));
    });
    // la cara de la pantalla mira hacia la silla (−z en three): el promedio de normales caía en el dorso
    // y el código salía al revés
    n.set(0, 0, -1);
    // el ancho va en el eje horizontal perpendicular a la normal
    const w = Math.abs(n.x) > Math.abs(n.z) ? size.z : size.x;
    const c = document.createElement("canvas"); c.width = 640; c.height = Math.round(640 * size.y / w); // 2× para que el texto se lea de cerca
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.88, size.y * 0.84), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
    // se despega de la cara sólo medio grosor (el grosor va a lo largo de la normal)
    const depth = Math.abs(n.x) > Math.abs(n.z) ? size.x : size.z;
    mesh.position.copy(center).addScaledVector(n, depth * 0.5 + 0.002);
    mesh.lookAt(mesh.position.clone().add(n));
    root.add(mesh);
    mesh.position.applyMatrix4(root.matrixWorld.clone().invert());
    // resplandor menta detrás/alrededor: se ve aunque la cámara mire el dorso del monitor
    const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex, color: new THREE.Color(MINT), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, toneMapped: false }));
    glow.position.copy(center).addScaledVector(n, 0.03).applyMatrix4(root.matrixWorld.clone().invert());
    glow.scale.set(w * 2.2, size.y * 2.2, 1);
    glow.renderOrder = 4;
    root.add(glow);
    screen = { c, g: c.getContext("2d"), tex, glow, last: -1 };
  }

  const drawScreen = (t, surprise) => {
    const { c, g } = screen, W = c.width / 2, H = c.height / 2;
    g.setTransform(2, 0, 0, 2, 0, 0);
    g.fillStyle = DARK; g.fillRect(0, 0, W, H);
    const LH = 22, pad = 16, rate = 2.2; // renglones por segundo
    const typed = t * rate, cur = Math.floor(typed);
    const rows = Math.floor((H - 40) / LH);
    const first = Math.max(0, cur - rows + 1); // scroll: el renglón activo se queda abajo
    g.lineCap = "round"; g.lineWidth = 8;
    for (let k = first; k <= cur; k++) {
      const y = pad + 6 + (k - first) * LH;
      const indent = [0, 1, 2, 1, 2, 3, 1][Math.floor(rnd(k + 9) * 7)] * 18;
      const full = 60 + rnd(k) * (W - 120 - indent);
      const len = k === cur ? full * (typed - cur) : full;
      // dos «tokens» por renglón: palabra clave en menta, el resto menta tenue
      const kw = Math.min(len, 22 + rnd(k + 3) * 40);
      g.strokeStyle = MINT; g.globalAlpha = 1;
      g.beginPath(); g.moveTo(pad + indent, y); g.lineTo(pad + indent + kw, y); g.stroke();
      if (len > kw + 10) { g.globalAlpha = 0.55; g.beginPath(); g.moveTo(pad + indent + kw + 12, y); g.lineTo(pad + indent + len, y); g.stroke(); }
      if (k === cur && Math.floor(t * 3) % 2 === 0) { g.globalAlpha = 1; g.fillStyle = MINT; g.fillRect(pad + indent + len + 6, y - 7, 6, 14); }
    }
    g.globalAlpha = 1;
    // barra de progreso abajo
    const p = (t * 0.11) % 1;
    g.fillStyle = "rgba(133,221,203,0.25)"; g.fillRect(pad, H - 22, W - pad * 2, 8);
    g.fillStyle = MINT; g.fillRect(pad, H - 22, (W - pad * 2) * p, 8);
    // al sorprenderse, la pantalla da un destello
    if (surprise > 0 && surprise < 0.3) { g.fillStyle = `rgba(133,221,203,${0.5 * (1 - surprise / 0.3)})`; g.fillRect(0, 0, W, H); }
    if (overlay) overlay(g, W, H, t);
    screen.tex.needsUpdate = true;
  };

  const update = (t, dt, surpriseAt = Infinity) => {
    const ds = t - surpriseAt;
    for (const p of plants) {
      // viento: suma de dos senos (rachas), poca amplitud, fase escalonada por planta
      const wind = Math.sin(t * p.freq * Math.PI * 2 + p.phase) * 0.7 + Math.sin(t * p.freq * 2.3 * Math.PI + p.phase * 1.9) * 0.3;
      const gust = Math.sin(t * p.freq * 1.3 * Math.PI + p.phase * 0.7);
      const jig = spring(ds - p.delay) * 0.16;
      p.o.rotation.x = p.rx + wind * p.amp + jig;
      p.o.rotation.z = p.rz + gust * p.amp * 0.6 - jig * 0.6;
    }
    for (const l of lamps) {
      // respiración lenta (~5 s) y cálida
      let k = 1 + 0.1 * (0.5 + 0.5 * Math.sin(t * 1.25 + l.phase));
      // parpadeo único al susto: se apaga un instante y vuelve con un golpe de luz
      if (ds > 0.04 && ds < 0.16) k = 0.55;
      else if (ds >= 0.16 && ds < 0.7) k += 0.35 * Math.exp(-(ds - 0.16) * 6);
      for (const m of l.mats) m.color.setRGB(k, k * 0.98, k * 0.93);
      l.halo.material.opacity = THREE.MathUtils.clamp((k - 0.6) * 0.9, 0, 1);
    }
    if (screen) {
      const q = Math.round(t * 30);
      if (q !== screen.last) { screen.last = q; drawScreen(t, ds); }
      screen.glow.material.opacity = 0.28 + 0.06 * Math.sin(t * 2.1) + (ds > 0 && ds < 0.3 ? 0.4 * (1 - ds / 0.3) : 0);
    }
  };
  return { update };
}
