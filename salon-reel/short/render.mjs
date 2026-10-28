// Render mudo del short: abre la escena en modo secuencia (?seq=1), avanza cuadro por cuadro a 30 fps
// y manda cada captura a ffmpeg. Uso: node render.mjs [segundos] [salida.mp4]
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { existsSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

function findPuppeteer() {
  try { return createRequire(import.meta.url)("puppeteer-core"); } catch {}
  const npx = join(homedir(), ".npm/_npx");
  for (const d of existsSync(npx) ? readdirSync(npx) : []) {
    const p = join(npx, d, "node_modules/puppeteer-core");
    if (existsSync(p)) return createRequire(join(npx, d, "node_modules/"))("puppeteer-core");
  }
  throw new Error("no encontré puppeteer-core");
}
function findChrome() {
  const base = join(homedir(), ".cache/hyperframes/chrome/chrome-headless-shell");
  for (const v of readdirSync(base)) for (const sub of readdirSync(join(base, v))) {
    const bin = join(base, v, sub, "chrome-headless-shell"); if (existsSync(bin)) return bin;
  }
}

const [, , secs = 18, out = "renders/mudo.mp4"] = process.argv;
const FPS = 30, N = Math.round(+secs * FPS);
const browser = await findPuppeteer().launch({ executablePath: findChrome(), headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920 });
page.on("pageerror", (e) => { console.log("ERROR:", e.message); process.exit(1); });
await page.goto("http://localhost:8787/ghosty-salon-unas/escena/?seq=1", { waitUntil: "networkidle0", timeout: 300000 });
await page.waitForFunction(() => window.__ready, { timeout: 300000 });

const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow", "-r", String(FPS), out], { stdio: ["pipe", "inherit", "inherit"] });
const t0 = Date.now();
for (let i = 0; i < N; i++) {
  await page.evaluate((i) => window.__frame(i), i);
  const png = await page.screenshot({ type: "png" });
  if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once("drain", r));
  if (i % 30 === 0) console.log(`cuadro ${i}/${N} · ${((Date.now() - t0) / 1000).toFixed(0)} s`);
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await browser.close();
console.log("ok", out);
