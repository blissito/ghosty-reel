// Interfaz 2D que se pinta en lienzos (pantalla del monitor y del teléfono): el formulario de inicio de
// sesión, la palomita de «sesión iniciada», el toque con onda y los botones. Todo es función de t.
export const INK = "#1B1B1F", LAV = "#8483E0", LAV_SOFT = "#EFE7FA", GREEN = "#8DCF6E", GRAY = "#C9C4DA", MUTED = "#7C7A8E";
export const FONT = '"Nunito", system-ui, sans-serif';

export const clamp01 = (x) => Math.min(Math.max(x, 0), 1);
export const easeOut = (x) => 1 - Math.pow(1 - clamp01(x), 3);
export const backOut = (x, s = 1.7) => { x = clamp01(x); return x === 0 ? 0 : 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2); };

export const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
export const text = (g, s, x, y, size, color, weight = 900, align = "center") => {
  g.font = `${weight} ${size}px ${FONT}`; g.fillStyle = color; g.textAlign = align; g.textBaseline = "middle"; g.fillText(s, x, y);
};

// candado: cuerpo redondeado + arco; `open` 0..1 levanta y gira el arco
export function padlock(g, cx, cy, s, color, open = 0) {
  g.save(); g.translate(cx, cy);
  g.strokeStyle = color; g.lineWidth = s * 0.16; g.lineCap = "round";
  g.save(); g.translate(s * 0.3 * open, -s * 0.18 * open);
  g.beginPath(); g.arc(0, -s * 0.12, s * 0.3, Math.PI, 0); g.lineTo(s * 0.3, s * 0.05); g.moveTo(-s * 0.3, -s * 0.12); g.lineTo(-s * 0.3, s * 0.05 - s * 0.2 * open); g.stroke();
  g.restore();
  g.fillStyle = color; rr(g, -s * 0.45, 0, s * 0.9, s * 0.7, s * 0.14); g.fill();
  g.restore();
}

export function check(g, cx, cy, r, k = 1) {
  g.fillStyle = GREEN; g.beginPath(); g.arc(cx, cy, r * backOut(k), 0, Math.PI * 2); g.fill();
  if (k < 0.3) return;
  const p = clamp01((k - 0.3) / 0.5);
  g.strokeStyle = "#FFFFFF"; g.lineWidth = r * 0.24; g.lineCap = "round"; g.lineJoin = "round";
  g.beginPath(); g.moveTo(cx - r * 0.45, cy + r * 0.02);
  const mid = [cx - r * 0.12, cy + r * 0.35], end = [cx + r * 0.5, cy - r * 0.35];
  if (p < 0.4) g.lineTo(cx - r * 0.45 + (mid[0] - cx + r * 0.45) * p / 0.4, cy + r * 0.02 + (mid[1] - cy - r * 0.02) * p / 0.4);
  else { g.lineTo(...mid); g.lineTo(mid[0] + (end[0] - mid[0]) * (p - 0.4) / 0.6, mid[1] + (end[1] - mid[1]) * (p - 0.4) / 0.6); }
  g.stroke();
}

// toque: un punto que baja y una onda que se abre (no hay mano: sólo la huella del dedo)
export function tap(g, x, y, dt, s = 1) {
  if (dt < -0.25 || dt > 0.6) return;
  if (dt < 0.08) { const k = clamp01((dt + 0.25) / 0.33); g.fillStyle = `rgba(27,27,31,${0.28 * k})`; g.beginPath(); g.arc(x, y, 16 * s, 0, Math.PI * 2); g.fill(); }
  if (dt > 0) { const k = clamp01(dt / 0.6); g.strokeStyle = `rgba(132,131,224,${0.9 * (1 - k)})`; g.lineWidth = 6 * s; g.beginPath(); g.arc(x, y, (16 + 70 * easeOut(k)) * s, 0, Math.PI * 2); g.stroke(); }
}

export function button(g, x, y, w, h, label, color, pressed = 0) {
  const d = pressed * 3;
  g.fillStyle = "rgba(27,27,31,0.18)"; rr(g, x, y + 6, w, h, h / 2); g.fill();
  g.fillStyle = color; rr(g, x, y + d, w, h, h / 2); g.fill();
  // la letra se encoge si la etiqueta no cabe en el botón
  g.font = `900 ${h * 0.42}px ${FONT}`;
  const size = Math.min(h * 0.42, h * 0.42 * (w - h * 0.6) / g.measureText(label).width);
  text(g, label, x + w / 2, y + h / 2 + d + 1, size, "#FFFFFF");
}

// formulario de inicio de sesión (mismo en el monitor y en el espejo del teléfono)
// st: { email 0..1 (lo escribe Ghosty), pass 0..1 (la escribes tú), pressed 0..1, keychain (chip «Llavero») }
export function loginForm(g, x, y, w, h, st) {
  g.fillStyle = "#FFFFFF"; rr(g, x, y, w, h, w * 0.06); g.fill();
  const u = w / 300;
  padlock(g, x + w / 2, y + 44 * u, 44 * u, LAV, st.lockOpen ?? 0);
  text(g, "Inicia sesión", x + w / 2, y + 112 * u, 26 * u, INK);
  const fields = [["Correo", "tu@correo.com", st.email ?? 0], ["Contraseña", "••••••••••", st.pass ?? 0]];
  fields.forEach(([ph, val, kk], i) => {
    const fy = y + (140 + i * 52) * u, k = clamp01(kk);
    const focus = i === 1 && st.focus;
    g.fillStyle = "#F3F1F8"; rr(g, x + 24 * u, fy, w - 48 * u, 40 * u, 10 * u); g.fill();
    if (focus) { g.strokeStyle = LAV; g.lineWidth = 3 * u; rr(g, x + 24 * u, fy, w - 48 * u, 40 * u, 10 * u); g.stroke(); }
    const shown = val.slice(0, Math.round(val.length * k));
    text(g, k > 0 ? shown : ph, x + 40 * u, fy + 21 * u, 17 * u, k > 0 ? INK : MUTED, 800, "left");
    if (i === 1 && st.keychain) {
      g.fillStyle = LAV_SOFT; rr(g, x + w - 112 * u, fy + 8 * u, 80 * u, 24 * u, 12 * u); g.fill();
      text(g, "Llavero", x + w - 72 * u, fy + 21 * u, 13 * u, LAV, 900);
    }
  });
  button(g, x + 24 * u, y + 252 * u, w - 48 * u, 44 * u, "Entrar", LAV, st.pressed ?? 0);
}

// barra de navegador: «Navegador de Ghosty · caja segura» con candado
export function browserBar(g, x, y, w, h) {
  g.fillStyle = "#FFFFFF"; g.fillRect(x, y, w, h);
  g.fillStyle = "#F3F1F8"; rr(g, x + h * 0.3, y + h * 0.18, w - h * 0.6, h * 0.64, h * 0.32); g.fill();
  padlock(g, x + h * 0.85, y + h * 0.47, h * 0.42, GREEN);
  text(g, "Navegador de Ghosty · caja segura", x + h * 1.3, y + h * 0.52, h * 0.36, INK, 900, "left");
}
